"""The Iman Cut catalog core. Standard library only (sqlite3).

Principles enforced here:
- Immutable UUID + readable display ID per record; display IDs never reused; merges keep redirects.
- Every change writes a full revision snapshot; blank incoming values never erase known values
  unless explicitly requested.
- Reviews/approvals bind to an exact revision; a later edit invalidates them.
- Upstream changes flag dependent records (scripts, timelines, exports, posts) as stale; nothing
  downstream is modified automatically.
- Timing is integer ticks at 1/240000 s, intervals [start, end).
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
import unicodedata
import uuid as uuidlib
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = ROOT / "catalog" / "migrations"
TICKS_PER_SECOND = 240000          # divisible by 24000/1001-frame, 30000/1001-frame, 25, 50, 60 fps and 48 kHz audio
TB = Fraction(1, TICKS_PER_SECOND)

PREFIX = {
    "work": "WRK", "season": "SEA", "installment": "INS", "edition": "EDT", "person": "PER",
    "character": "CHR", "portrayal": "POR", "relationship": "REL", "asset": "AST", "ingestion": "ING",
    "transcript": "TRN", "segment": "SEG", "scene": "SCN", "shot": "SHT", "appearance": "APP",
    "source": "SRC", "claim": "CLM", "rights": "RGT", "concept": "CON", "project": "PRJ",
    "timeline": "TML", "timeline_item": "TMI", "script": "SCR", "voice": "VOC", "take": "TAK",
    "export": "EXP", "review": "REV", "account": "ACC", "post": "PST", "metric": "MET",
    "packaging": "PKG", "annotation_set": "ANN", "historical_link": "HLK", "reference_image": "IMG",
}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def norm(s: str) -> str:
    """Normalisation for matching only (never for display)."""
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    s = re.sub(r"[\"'“”‘’]", "", s.lower())
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- timing
def to_ticks(value) -> int:
    """Seconds (int/float/str/Fraction) or 'HH:MM:SS.mmm' → exact ticks. Rejects inexact rounding."""
    if isinstance(value, str) and ":" in value:
        parts = value.split(":")
        secs = Fraction(0)
        for p in parts:
            secs = secs * 60 + Fraction(p)
    else:
        secs = Fraction(str(value)) if isinstance(value, (float, str)) else Fraction(value)
    t = secs * TICKS_PER_SECOND
    if t.denominator != 1:
        raise ValueError(f"{value!r} is not representable exactly at 1/{TICKS_PER_SECOND}")
    return int(t)


def frames_to_ticks(frames: int, fps_num: int, fps_den: int) -> int:
    t = Fraction(frames * fps_den, fps_num) * TICKS_PER_SECOND
    if t.denominator != 1:
        raise ValueError("frame rate not representable at canonical time base")
    return int(t)


def fmt_ticks(t: int) -> str:
    ms = Fraction(t, TICKS_PER_SECOND) * 1000
    ms = int(ms)  # display only; truncation documented
    h, ms = divmod(ms, 3_600_000); m, ms = divmod(ms, 60_000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def union_length(intervals) -> int:
    """Total length of the union of half-open [start, end) intervals (no double counting)."""
    total, cur_s, cur_e = 0, None, None
    for s, e in sorted(intervals):
        if cur_e is None or s > cur_e:
            if cur_e is not None:
                total += cur_e - cur_s
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    if cur_e is not None:
        total += cur_e - cur_s
    return total


# ---------------------------------------------------------------- database
class Catalog:
    def __init__(self, path: Path | str, actor: str = "system"):
        self.path = Path(path)
        self.actor = actor
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.migrate()

    # -- migrations
    def migrate(self):
        self.db.execute("CREATE TABLE IF NOT EXISTS schema_migration (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
        done = {r[0] for r in self.db.execute("SELECT version FROM schema_migration")}
        for f in sorted(MIGRATIONS.glob("*.sql")):
            if f.stem not in done:
                with self.db:
                    self.db.executescript(f.read_text())
                    self.db.execute("INSERT INTO schema_migration VALUES (?,?)", (f.stem, now()))

    def q(self, sql, *a):
        return self.db.execute(sql, a).fetchall()

    def one(self, sql, *a):
        return self.db.execute(sql, a).fetchone()

    # -- identities
    def _new_entity(self, etype: str) -> tuple[str, str]:
        prefix = PREFIX[etype]
        row = self.one("SELECT next_value FROM id_counter WHERE prefix=?", prefix)
        n = row[0] if row else 1
        self.db.execute("INSERT INTO id_counter VALUES (?,?) ON CONFLICT(prefix) DO UPDATE SET next_value=excluded.next_value", (prefix, n + 1))
        u, did, t = str(uuidlib.uuid4()), f"{prefix}-{n:06d}", now()
        self.db.execute("INSERT INTO entity (uuid, display_id, type, rev, created_at, updated_at) VALUES (?,?,?,1,?,?)", (u, did, etype, t, t))
        return u, did

    def create(self, etype: str, fields: dict, ingestion: str | None = None, note: str | None = None) -> str:
        u, _ = self._new_entity(etype)
        cols = ["uuid"] + list(fields)
        self.db.execute(f"INSERT INTO {etype} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", [u, *fields.values()])
        self._snapshot(etype, u, 1, sorted(fields), ingestion, note or "created")
        for k, v in fields.items():
            if ingestion and v not in (None, ""):
                self.db.execute("INSERT INTO provenance VALUES (?,?,?,?,NULL,?)", (u, k, str(v), ingestion, now()))
        return u

    def _snapshot(self, etype, u, rev, changed, ingestion, note):
        row = self.one(f"SELECT * FROM {etype} WHERE uuid=?", u)
        self.db.execute("INSERT INTO revision VALUES (?,?,?,?,?,?,?,?)",
                        (u, rev, json.dumps(dict(row), default=str, sort_keys=True), json.dumps(changed), ingestion, self.actor, note, now()))

    def update(self, u: str, fields: dict, ingestion: str | None = None, note: str | None = None,
               overwrite_blank: bool = False) -> list[str]:
        """Field-level update. Returns the list of fields that actually changed."""
        etype = self.type_of(u)
        cur = dict(self.one(f"SELECT * FROM {etype} WHERE uuid=?", u))
        changed = {}
        for k, v in fields.items():
            if v in (None, "") and not overwrite_blank:
                continue                      # blank import never erases a known value
            if cur.get(k) != v:
                changed[k] = v
        if not changed:
            return []
        sets = ",".join(f"{k}=?" for k in changed)
        self.db.execute(f"UPDATE {etype} SET {sets} WHERE uuid=?", [*changed.values(), u])
        rev = self.one("SELECT rev FROM entity WHERE uuid=?", u)[0] + 1
        self.db.execute("UPDATE entity SET rev=?, updated_at=? WHERE uuid=?", (rev, now(), u))
        self._snapshot(etype, u, rev, sorted(changed), ingestion, note)
        for k, v in changed.items():
            self.db.execute("INSERT INTO provenance VALUES (?,?,?,?,NULL,?)", (u, k, None if v is None else str(v), ingestion, now()))
        desc = f"{self.did(u)} rev {rev}: changed {', '.join(sorted(changed))}" + (f" ({note})" if note else "")
        self._invalidate_reviews(u, rev, desc)
        self._propagate(u, rev, desc)
        self.log("update", u, desc)
        return sorted(changed)

    def type_of(self, u):
        return self.one("SELECT type FROM entity WHERE uuid=?", u)[0]

    def did(self, u):
        return self.one("SELECT display_id FROM entity WHERE uuid=?", u)[0]

    def rev(self, u):
        return self.one("SELECT rev FROM entity WHERE uuid=?", u)[0]

    def resolve(self, display_id: str) -> str:
        """Display ID → current uuid, following merge redirects."""
        row = self.one("SELECT uuid, retired_to FROM entity WHERE display_id=?", display_id)
        if not row:
            raise KeyError(display_id)
        u, to = row
        seen = {u}
        while to:
            u = to
            to = self.one("SELECT retired_to FROM entity WHERE uuid=?", u)[0]
            if to in seen:
                raise RuntimeError("redirect loop")
            seen.add(u)
        return u

    def merge(self, duplicate: str, keep: str, reason: str):
        """Retire a duplicate. Its ID is never reused and keeps redirecting to the survivor."""
        self.db.execute("UPDATE entity SET retired_to=?, retired_reason=?, updated_at=? WHERE uuid=?", (keep, reason, now(), duplicate))
        self.db.execute("INSERT OR IGNORE INTO dependency VALUES (?,?,?)", (keep, duplicate, "merged_into"))
        self._propagate(duplicate, self.rev(duplicate), f"{self.did(duplicate)} merged into {self.did(keep)}: {reason}")
        self.log("merge", duplicate, f"→ {self.did(keep)}: {reason}")

    def log(self, action, u, detail):
        self.db.execute("INSERT INTO audit_log (at, actor, action, entity_uuid, detail) VALUES (?,?,?,?,?)", (now(), self.actor, action, u, detail))

    # -- dependencies, staleness, approvals
    def depends(self, downstream: str, *upstreams: str, kind: str | None = None):
        for up in upstreams:
            if up:
                self.db.execute("INSERT OR IGNORE INTO dependency VALUES (?,?,?)", (up, downstream, kind))

    def _propagate(self, up: str, rev: int, change: str):
        frontier, seen = [up], {up}
        while frontier:
            nxt = []
            for node in frontier:
                for (down,) in self.q("SELECT downstream_uuid FROM dependency WHERE upstream_uuid=?", node):
                    if down in seen:
                        continue
                    seen.add(down)
                    self.db.execute("INSERT INTO stale_flag (downstream_uuid, upstream_uuid, upstream_rev, change, at) VALUES (?,?,?,?,?)",
                                    (down, up, rev, change, now()))
                    nxt.append(down)
            frontier = nxt

    def _invalidate_reviews(self, u, new_rev, why):
        self.db.execute("UPDATE review SET valid=0, invalidated_reason=? WHERE target_uuid=? AND valid=1 AND target_rev<?", (why, u, new_rev))

    def review(self, target: str, kind: str, decision: str, reviewer: str, notes: str = "") -> str:
        return self.create("review", dict(target_uuid=target, target_rev=self.rev(target), kind=kind, decision=decision,
                                          reviewer=reviewer, notes=notes, at=now(), valid=1, invalidated_reason=None))

    def is_approved(self, target: str, kind: str) -> bool:
        r = self.one("SELECT 1 FROM review WHERE target_uuid=? AND kind=? AND decision='approved' AND valid=1 AND target_rev=?",
                     target, kind, self.rev(target))
        return r is not None

    def stale(self, u: str):
        return self.q("SELECT * FROM stale_flag WHERE downstream_uuid=? AND resolved=0", u)

    # -- backup / restore
    def backup(self, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        b = sqlite3.connect(dest)
        with b:
            self.db.backup(b)
        b.close()
        return dest

    def verify_restore(self, backup_path: Path, scratch: Path) -> dict:
        """Restore a backup into a scratch file and compare integrity + per-table row counts."""
        shutil.copyfile(backup_path, scratch)
        r = sqlite3.connect(scratch)
        integrity = r.execute("PRAGMA integrity_check").fetchone()[0]
        fk = r.execute("PRAGMA foreign_key_check").fetchall()
        tables = [t[0] for t in self.q("SELECT name FROM sqlite_master WHERE type='table'")]
        mism = {t: (self.one(f"SELECT count(*) FROM {t}")[0], r.execute(f"SELECT count(*) FROM {t}").fetchone()[0])
                for t in tables}
        mism = {t: v for t, v in mism.items() if v[0] != v[1]}
        r.close()
        return {"integrity": integrity, "foreign_key_violations": len(fk), "table_count_mismatches": mism,
                "ok": integrity == "ok" and not fk and not mism}

    def commit(self):
        self.db.commit()

    # -- convenience finders
    def find_person(self, name: str):
        n = norm(name)
        return self.q("SELECT DISTINCT p.uuid FROM person p LEFT JOIN person_name pn ON pn.person_uuid=p.uuid "
                      "WHERE p.norm_name=? OR pn.norm_name=?", n, n)

    def find_character(self, work: str, name: str):
        n = norm(name)
        return self.q("SELECT DISTINCT c.uuid FROM character c LEFT JOIN character_name cn ON cn.character_uuid=c.uuid "
                      "WHERE c.work_uuid=? AND (c.norm_name=? OR cn.norm_name=?)", work, n, n)

    def screen_time(self, character: str, modes=("visible", "speaking_on_screen")) -> dict:
        """Union of confirmed intervals per annotation set (active sets only) + coverage label."""
        out = {}
        for (ann,) in self.q("SELECT uuid FROM annotation_set WHERE status='active'"):
            rows = self.q(f"SELECT start_ticks, end_ticks, scene_uuid, shot_uuid FROM appearance WHERE character_uuid=? AND annotation_set_uuid=? "
                          f"AND review_status='human_confirmed' AND identity_status='Confirmed' AND mode IN ({','.join('?' * len(modes))})",
                          character, ann, *modes)
            cov = self.q("SELECT start_ticks, end_ticks FROM coverage WHERE annotation_set_uuid=?", ann)
            asset = self.one("SELECT a.duration_ticks FROM annotation_set s JOIN asset a ON a.uuid=s.asset_uuid WHERE s.uuid=?", ann)[0]
            covered = union_length([(c[0], c[1]) for c in cov])
            out[self.did(ann)] = {
                "visible_ticks": union_length([(r[0], r[1]) for r in rows]),
                "scenes": len({r[2] for r in rows if r[2]}),
                "shots": len({r[3] for r in rows if r[3]}),
                "coverage_fraction": float(Fraction(covered, asset)) if asset else None,
                "provisional": covered < (asset or 0),
            }
        return out

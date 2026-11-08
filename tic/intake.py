"""Incremental intake. Every input becomes an ING record; re-ingesting identical bytes is a no-op.

Matching rules (documented in docs/ARCHITECTURE.md §Intake):
- Person: IMDb name ID → exact normalised name/alias. One hit = match; several = review queue.
- Character (within a work): exact normalised credited name or alias.
  * Same name, different primary performer → conflict queue (often distinct background roles).
  * Name whose tokens are a strict subset of another character's name ("Howard" vs "Howard Cosell")
    → ambiguous queue; nothing created.
  * "Young X" → linked as a young portrayal of X only when exactly one character matches X.
  * Multi-name credits ("A / B") → one character keeping the exact credited string, names as aliases,
    plus a queue item asking whether they are aliases or separate roles (unless an existing
    character already carries those names, as with Cassius Clay / Muhammad Ali).
- Blank values never erase known values. Nothing is deleted.
"""
from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path

from .core import Catalog, norm, now, sha256_file, ROOT

INTAKE_DIR = ROOT / "intake"


def _rows(path: Path):
    lines = [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    return list(csv.reader(lines, delimiter="\t"))


def start_ingestion(cat: Catalog, path: Path, kind: str, provenance: str):
    """Returns (ingestion_uuid, already_done_report_or_None)."""
    digest = sha256_file(path)
    row = cat.one("SELECT uuid, report_json FROM ingestion WHERE kind=? AND sha256=?", kind, digest)
    if row:
        return row[0], json.loads(row[1] or "{}")
    u, did = cat._new_entity("ingestion")
    dest_dir = INTAKE_DIR / did
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / path.name
    shutil.copy2(path, dest)
    dest.chmod(0o444)  # preserved original, read-only
    cat.db.execute("INSERT INTO ingestion VALUES (?,?,?,?,?,?,?,NULL)",
                   (u, kind, path.name, str(dest.relative_to(ROOT)) if dest.is_relative_to(ROOT) else str(dest), digest, provenance, now()))
    cat._snapshot("ingestion", u, 1, ["created"], None, "ingestion started")
    return u, None


def finish_ingestion(cat: Catalog, ing: str, report: dict):
    cat.db.execute("UPDATE ingestion SET report_json=? WHERE uuid=?", (json.dumps(report, indent=1), ing))
    cat.commit()
    return report


def queue(cat: Catalog, ing: str, kind: str, payload: dict, candidates=None, report=None):
    cur = cat.db.execute("INSERT OR IGNORE INTO review_queue (ingestion_uuid, kind, payload_json, candidates_json) VALUES (?,?,?,?)",
                         (ing, kind, json.dumps(payload, sort_keys=True, ensure_ascii=False), json.dumps(candidates or [])))
    if report is not None:
        report["unresolved"].append({"kind": kind, **payload, "candidates": [cat.did(c) for c in (candidates or [])]})


def _char_names(cat, work):
    out = {}
    for u, n in cat.q("SELECT uuid, norm_name FROM character WHERE work_uuid=?", work):
        out.setdefault(u, set()).add(n)
    for u, n in cat.q("SELECT cn.character_uuid, cn.norm_name FROM character_name cn JOIN character c ON c.uuid=cn.character_uuid WHERE c.work_uuid=?", work):
        out.setdefault(u, set()).add(n)
    return out


def _subset_candidates(name_norm, names_by_char, exclude=()):
    toks = set(name_norm.split())
    hits = []
    for u, names in names_by_char.items():
        if u in exclude:
            continue
        if any(toks < set(n.split()) for n in names):
            hits.append(u)
    return hits


def _ensure_person(cat, ing, actor, nm, report):
    if nm:
        r = cat.one("SELECT entity_uuid FROM external_id WHERE provider='imdb' AND value=?", nm)
        if r:
            report["matched"].append(f"{cat.did(r[0])} {actor} (IMDb {nm})")
            return r[0]
    hits = [h[0] for h in cat.find_person(actor)]
    if len(hits) > 1:
        queue(cat, ing, "ambiguous_match", {"person": actor, "imdb": nm}, hits, report)
        return None
    if hits:
        p = hits[0]
        report["matched"].append(f"{cat.did(p)} {actor}")
    else:
        p = cat.create("person", dict(name=actor, norm_name=norm(actor)), ing)
        report["added"].append(f"{cat.did(p)} person {actor}")
    if nm and not cat.one("SELECT 1 FROM external_id WHERE provider='imdb' AND value=?", nm):
        cat.db.execute("INSERT INTO external_id VALUES (?,?,?)", (p, "imdb", nm))
        report["updated"].append(f"{cat.did(p)} + IMDb ID {nm}")
    return p


def _add_name(cat, char, name, kind, verification, source):
    cat.db.execute("INSERT OR IGNORE INTO character_name VALUES (?,?,?,?,?,?)", (char, name, norm(name), kind, verification, source))


def ingest_legacy(cat: Catalog, path: Path, work: str, provenance: str) -> dict:
    ing, done = start_ingestion(cat, path, "legacy_ids", provenance)
    if done is not None:
        return {"idempotent_noop": True, **done}
    report = {k: [] for k in ("added", "matched", "updated", "conflicting", "unresolved", "affected_outputs")}
    for legacy_id, credited, aliases, actor, cstatus, rel, ver in _rows(path):
        p = _ensure_person(cat, ing, actor, None, report)
        c = cat.create("character", dict(work_uuid=work, credited_name=credited, norm_name=norm(credited),
                                         counterpart_status=cstatus, relationship_to_subject=rel), ing, note=f"legacy {legacy_id}")
        cat.db.execute("INSERT INTO external_id VALUES (?,?,?)", (c, "tic-v0", legacy_id))
        for a in filter(None, aliases.split(";")):
            _add_name(cat, c, a, "alias_or_historical", "v0_search_snippets", "legacy v0 sheet")
        pr = cat.create("portrayal", dict(character_uuid=c, person_uuid=p, credit_verification=ver), ing)
        report["added"].append(f"{cat.did(c)} {credited} (was {legacy_id}) · {cat.did(pr)} {actor}")
    return finish_ingestion(cat, ing, report)


def ingest_cast(cat: Catalog, path: Path, work: str, provenance: str, verification: str,
                authoritative_names: bool = False) -> dict:
    """Cast-credit list (TSV: order, imdb_nm, actor, characters, note, episodes)."""
    ing, done = start_ingestion(cat, path, "cast_list", provenance)
    if done is not None:
        return {"idempotent_noop": True, **done}
    report = {k: [] for k in ("added", "matched", "updated", "conflicting", "unresolved", "affected_outputs")}
    rows = _rows(path)
    batch_names = {}
    for r in rows:
        for n in re.split(r"\s*/\s*", r[3]):
            if n and n != "...":
                batch_names.setdefault(f"batch:{r[0]}", set()).add(norm(n))

    for order, nm, actor, chars_raw, note, eps in rows:
        nm = nm.strip() or None
        person = _ensure_person(cat, ing, actor, nm, report)
        if person is None:
            continue
        credited_as = None
        m = re.search(r"\(as ([^)]+)\)", note or "")
        if m:
            credited_as = m.group(1)
            cat.db.execute("INSERT OR IGNORE INTO person_name VALUES (?,?,?,?,NULL)", (person, credited_as, norm(credited_as), "credited_as"))
        uncredited = "uncredited" in (note or "")
        if not chars_raw.strip():
            queue(cat, ing, "unresolved_reference", {"row": order, "actor": actor, "issue": "credit lists no character name"}, [], report)
            continue
        names = [n for n in re.split(r"\s*/\s*", chars_raw) if n and n != "..."]
        truncated = "..." in chars_raw
        names_by_char = _char_names(cat, work)
        age = "primary"

        # 1) exact match on any listed name
        exact = sorted({u for u, ns in names_by_char.items() for n in names if norm(n) in ns})
        char = None
        if len(exact) > 1:
            queue(cat, ing, "ambiguous_match", {"row": order, "credit": chars_raw, "actor": actor}, exact, report)
            continue
        if exact:
            char = exact[0]
            other = cat.one("SELECT p.uuid, pe.name FROM portrayal p JOIN person pe ON pe.uuid=p.person_uuid "
                            "WHERE p.character_uuid=? AND p.age_portrayal='primary' AND p.person_uuid<>?", char, person)
            if other:
                queue(cat, ing, "conflict", {"row": order, "credit": chars_raw, "actor": actor,
                                             "issue": f"{cat.did(char)} already credited to {other[1]}; likely a distinct role with the same generic name"},
                      [char], report)
                report["conflicting"].append(f"row {order}: '{chars_raw}' ({actor}) vs {cat.did(char)} ({other[1]})")
                continue
            if authoritative_names and cat.one("SELECT credited_name FROM character WHERE uuid=?", char)[0] != chars_raw:
                old = cat.one("SELECT credited_name FROM character WHERE uuid=?", char)[0]
                _add_name(cat, char, old, "previous_label", "superseded_by_credits", "earlier label")
                cat.update(char, {"credited_name": chars_raw, "norm_name": norm(chars_raw)}, ing, note=f"credited name per {provenance}")
                report["updated"].append(f"{cat.did(char)} credited name '{old}' → '{chars_raw}' (old kept as previous_label)")
            else:
                report["matched"].append(f"{cat.did(char)} '{chars_raw}'")
        # 2) "Young X"
        elif len(names) == 1 and names[0].lower().startswith("young "):
            base = norm(names[0][6:])
            cands = sorted({u for u, ns in names_by_char.items() if any(set(base.split()) <= set(n.split()) for n in ns)})
            known = set().union(*(names_by_char[c] for c in cands)) if cands else set()
            batch_hits = [k.split(":")[1] for k, v in batch_names.items() if k != f"batch:{order}"
                          and any(set(base.split()) <= set(x.split()) and x not in known and not x.startswith("young ") for x in v)]
            if batch_hits:
                queue(cat, ing, "ambiguous_match", {"row": order, "credit": names[0], "actor": actor,
                                                    "issue": "young portrayal could match several credited names", "batch_rows": batch_hits}, cands, report)
                continue
            if len(cands) == 1:
                char, age = cands[0], "young"
                _add_name(cat, char, names[0], "credited_young_portrayal", verification, provenance)
                report["matched"].append(f"'{names[0]}' → young portrayal of {cat.did(char)} (name rule; confirm on screen)")
            elif len(cands) > 1:
                queue(cat, ing, "ambiguous_match", {"row": order, "credit": names[0], "actor": actor,
                                                    "issue": "young portrayal matches several characters"}, cands, report)
                continue
        # 3) strict-subset ambiguity ("Howard" vs "Howard Cosell")
        if char is None:
            own = batch_names[f"batch:{order}"]
            others = {k: v for k, v in batch_names.items() if k != f"batch:{order}"}
            amb_db = sorted({c for n in own for c in _subset_candidates(n, names_by_char)})
            amb_batch = sorted({k for n in own for k, v in others.items() if any(set(n.split()) < set(x.split()) for x in v)})
            if len(names) == 1 and (amb_db or amb_batch):
                queue(cat, ing, "ambiguous_match", {"row": order, "credit": chars_raw, "actor": actor,
                                                    "issue": "name is a less specific form of another credited name",
                                                    "batch_rows": [k.split(':')[1] for k in amb_batch]}, amb_db, report)
                continue
            char = cat.create("character", dict(work_uuid=work, credited_name=chars_raw, norm_name=norm(chars_raw)), ing)
            report["added"].append(f"{cat.did(char)} character '{chars_raw}'")
            if len(names) > 1 or truncated:
                for n in names:
                    _add_name(cat, char, n, "listed_in_multi_credit", verification, provenance)
                contains = len(names) == 2 and (norm(names[0]) in norm(names[1]) or norm(names[1]) in norm(names[0]))
                if not contains:
                    queue(cat, ing, "multi_name_credit", {"row": order, "credit": chars_raw, "actor": actor,
                                                          "issue": "aliases of one character, or separate roles?" + (" (list truncated with '...')" if truncated else "")},
                          [char], report)
        # portrayal
        pr = cat.one("SELECT uuid FROM portrayal WHERE character_uuid=? AND person_uuid=? AND age_portrayal=?", char, person, age)
        fields = dict(credit_status="uncredited" if uncredited else "credited",
                      credited_episode_count=int(eps) if eps.strip() else None)
        if pr:
            pr = pr[0]
            changed = cat.update(pr, {**fields, "credit_verification": verification if verification in ("V2", "VC") else None}, ing, note=provenance)
            if changed:
                report["updated"].append(f"{cat.did(pr)} {', '.join(changed)}")
        else:
            pr = cat.create("portrayal", dict(character_uuid=char, person_uuid=person, age_portrayal=age, credit_verification=verification, **fields), ing)
            report["added"].append(f"{cat.did(pr)} {actor} as '{chars_raw}'" + (" (young)" if age == "young" else "") + (" (uncredited)" if uncredited else ""))
        cat.db.execute("INSERT OR IGNORE INTO portrayal_credit_name VALUES (?,?,?,?)", (pr, chars_raw, credited_as or actor, ing))
        for (down,) in cat.q("SELECT downstream_uuid FROM dependency WHERE upstream_uuid IN (?,?)", char, pr):
            report["affected_outputs"].append(cat.did(down))
    report["affected_outputs"] = sorted(set(report["affected_outputs"]))
    return finish_ingestion(cat, ing, report)


def summary(report: dict) -> str:
    keys = ("added", "matched", "updated", "conflicting", "unresolved", "affected_outputs")
    return " | ".join(f"{k.replace('_', ' ').title()}: {len(report.get(k, []))}" for k in keys)


def ingest_crew(cat: Catalog, path: Path, work: str, provenance: str) -> dict:
    """Crew TSV: imdb_nm, person, department, role_verbatim, episodes. Detects 'stunt double: <performer>'."""
    ing, done = start_ingestion(cat, path, "crew_list", provenance)
    if done is not None:
        return {"idempotent_noop": True, **done}
    report = {k: [] for k in ("added", "matched", "updated", "conflicting", "unresolved", "affected_outputs")}
    for nm, person, dept, role, eps in _rows(path):
        p = _ensure_person(cat, ing, person, nm or None, report)
        doubles = re.findall(r"stunt double: ([A-Z][\w.' -]+?)(?: /|$)", role)
        targets = []
        for d in doubles:
            hits = [h[0] for h in cat.find_person(d.strip())]
            if len(hits) == 1:
                targets.append(hits[0])
            else:
                queue(cat, ing, "unresolved_reference", {"crew": person, "role": role, "doubles_for": d}, hits, report)
        cat.db.execute("INSERT OR IGNORE INTO crew_credit VALUES (?,?,?,?,?,?,?)",
                       (work, p, dept, role, int(eps) if eps else None, targets[0] if targets else None, ing))
        for t in targets[1:]:
            cat.db.execute("INSERT OR IGNORE INTO crew_credit VALUES (?,?,?,?,?,?,?)", (work, p, dept, role + f" [double #{targets.index(t)+1}]", int(eps) if eps else None, t, ing))
        report["added"].append(f"crew: {person} — {role}" + (f" (doubles: {', '.join(cat.did(t) for t in targets)})" if targets else ""))
    return finish_ingestion(cat, ing, report)


def ingest_research(cat: Catalog, path: Path, provenance_default: str = "research note") -> dict:
    """Research note (JSON): new sources, claim status updates (old status kept in revisions), new claims."""
    ing, done = start_ingestion(cat, path, "research", provenance_default)
    if done is not None:
        return {"idempotent_noop": True, **done}
    data = json.loads(path.read_text(encoding="utf-8"))
    report = {k: [] for k in ("added", "matched", "updated", "conflicting", "unresolved", "affected_outputs")}
    src = {}
    for key, (title, author, url, stype, note) in data.get("sources", {}).items():
        r = cat.one("SELECT uuid FROM source WHERE title=?", title)
        if r:
            src[key] = r[0]; report["matched"].append(f"{cat.did(r[0])} {title}")
        else:
            src[key] = cat.create("source", dict(title=title, author=author, url=url, source_type=stype, access_date=now()[:10], reliability_note=note), ing)
            report["added"].append(f"{cat.did(src[key])} source {title}")
    for u in data.get("updates", []):
        r = cat.one("SELECT uuid FROM claim WHERE text=?", u["claim"])
        if not r:
            queue(cat, ing, "unresolved_reference", {"claim": u["claim"], "issue": "claim text not found"}, [], report); continue
        for k in u["sources"]:
            cat.db.execute("INSERT OR IGNORE INTO claim_evidence VALUES (?,?,?,NULL,?)", (r[0], src[k], "supports", now()))
        ch = cat.update(r[0], {"status": u["new_status"], "notes": u.get("note"), "checked_at": now()[:10]}, ing, note="research update")
        report["updated"].append(f"{cat.did(r[0])} → {u['new_status']} ({', '.join(ch)})")
        for (d,) in cat.q("SELECT downstream_uuid FROM dependency WHERE upstream_uuid=?", r[0]):
            report["affected_outputs"].append(cat.did(d))
    for c in data.get("new_claims", []):
        subj = cat.one("SELECT entity_uuid FROM external_id WHERE provider='tic-v0' AND value=?", c["subject"])[0]
        if cat.one("SELECT 1 FROM claim WHERE subject_uuid=? AND text=?", subj, c["text"]):
            report["matched"].append(c["text"]); continue
        cu = cat.create("claim", dict(text=c["text"], subject_uuid=subj, domain=c["domain"], claim_class=c["class"], status=c["status"],
                                      notes=c.get("note"), checked_at=now()[:10]), ing)
        for k in c["sources"]:
            cat.db.execute("INSERT OR IGNORE INTO claim_evidence VALUES (?,?,?,NULL,?)", (cu, src[k], "supports", now()))
        report["added"].append(f"{cat.did(cu)} {c['text']} [{c['status']}]")
    report["affected_outputs"] = sorted(set(report["affected_outputs"]))
    return finish_ingestion(cat, ing, report)

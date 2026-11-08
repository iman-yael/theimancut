"""Generate readable documents FROM the database. Documents are outputs, never sources of truth:
corrections go back into the catalog, then documents are regenerated."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .core import Catalog, now, fmt_ticks

PENDING = "Pending footage review"


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48]


def header(cat: Catalog, title: str, uuids: list[str]) -> str:
    revs = ", ".join(f"{cat.did(u)} r{cat.rev(u)}" for u in uuids)
    return f"# {title}\n\n> Generated {now()} from catalog `{cat.path.name}` · records: {revs}\n> Do not edit by hand. Route corrections through intake; regenerate.\n"


def _claims(cat, subject):
    rows = cat.q("SELECT c.uuid, c.text, c.domain, c.claim_class, c.status, c.notes FROM claim c WHERE c.subject_uuid=? ORDER BY c.domain", subject)
    out = []
    for u, text, dom, cls, st, notes in rows:
        srcs = cat.q("SELECT s.title, s.url, ce.stance, ce.locator FROM claim_evidence ce JOIN source s ON s.uuid=ce.source_uuid WHERE ce.claim_uuid=?", u)
        s = "; ".join(f"[{t}]({url}) ({stance}{', ' + loc if loc else ''})" if url else f"{t} ({stance})" for t, url, stance, loc in srcs) or "—"
        out.append(f"| {cat.did(u)} | {text} | {dom} | {cls} | **{st}** | {s} | {notes or ''} |")
    return out


def character_sheet(cat: Catalog, char: str) -> str:
    c = dict(cat.one("SELECT * FROM character WHERE uuid=?", char))
    prof = json.loads(c["profile_json"] or "{}")
    did = cat.did(char)
    legacy = cat.one("SELECT value FROM external_id WHERE entity_uuid=? AND provider='tic-v0'", char)
    L = [header(cat, f"{did} · {c['credited_name']}", [char])]
    L.append("## 1. Identity")
    L.append("| Field | Value |\n|---|---|")
    L.append(f"| Character ID | **{did}**" + (f" (legacy {legacy[0]})" if legacy else "") + f" · uuid `{char}` |")
    L.append(f"| Exact credited name | `{c['credited_name']}` |")
    names = cat.q("SELECT name, kind, verification, source FROM character_name WHERE character_uuid=? ORDER BY kind", char)
    L.append("| Names / aliases on file | " + ("; ".join(f"{n} *({k}, {v})*" for n, k, v, _ in names) or "—") + " |")
    L.append(f"| Historical counterpart status | {c['counterpart_status']} (a credit is not evidence of a real-person link) |")
    L.append(f"| Relationship to Muhammad Ali | {c['relationship_to_subject'] or 'Not established'} — see claims table for sourcing |")
    L.append("\n## 2. Performers (portrayals)")
    L.append("| Portrayal | Actor | Age portrayal | Credit | Credit verification | IMDb credited episodes* | Credited names | Actor IMDb page (pointer, not an image) |\n|---|---|---|---|---|---|---|---|")
    for p in cat.q("SELECT p.uuid, pe.uuid, pe.name, p.age_portrayal, p.credit_status, p.credit_verification, p.credited_episode_count "
                   "FROM portrayal p JOIN person pe ON pe.uuid=p.person_uuid WHERE p.character_uuid=? ORDER BY p.age_portrayal", char):
        cn = "; ".join(f"{a} as {b}" for b, a in cat.q("SELECT credited_character_name, credited_actor_name FROM portrayal_credit_name WHERE portrayal_uuid=?", p[0]))
        nm = cat.one("SELECT value FROM external_id WHERE entity_uuid=? AND provider='imdb'", p[1])
        url = f"https://www.imdb.com/name/{nm[0]}/" if nm else "—"
        L.append(f"| {cat.did(p[0])} | {p[2]} ({cat.did(p[1])}) | {p[3]} | {p[4]} | {p[5]} | {p[6] if p[6] is not None else '—'} | {cn} | {url} |")
    L.append("\n\\*IMDb episode totals are credited counts only. They do not establish appearances, scene counts or screen time.")
    doubles = cat.q("SELECT pe.name, cc.role_verbatim FROM crew_credit cc JOIN person pe ON pe.uuid=cc.person_uuid "
                    "WHERE cc.doubles_for_person IN (SELECT person_uuid FROM portrayal WHERE character_uuid=?)", char)
    if doubles:
        L.append("\n**Stunt doubles on file (affects on-screen identification in fight/action shots):** " +
                 "; ".join(f"{n} — {r}" for n, r in doubles))
    L.append("\n## 3. Visual reference")
    L.append("| Reference | Status |\n|---|---|")
    L.append("| Actor headshot | **MISSING.** The pasted credits contained no images, and automated access to IMDb returns 403. To add: supply image files with source and licence, kept as an internal reference only. |")
    L.append(f"| In-character frames | {PENDING}: no authorized footage supplied |")
    L.append("| On-screen identification | **Unresolved:** nothing has been observed. Credits establish casting, not which face appears in a given shot. |")
    L.append(f"| Hair / wardrobe / makeup / continuity | {PENDING} |")
    L.append("\n## 4. Appearances and statistics")
    st = cat.screen_time(char)
    if any(v["visible_ticks"] for v in st.values()):
        for k, v in st.items():
            L.append(f"- {k}: visible {fmt_ticks(v['visible_ticks'])}, scenes {v['scenes']}, shots {v['shots']}, coverage {v['coverage_fraction']:.0%}" + (" — PROVISIONAL" if v["provisional"] else ""))
    else:
        L.append(f"Scene count / shot count / visible screen time / voice-only / mentions: **{PENDING}** (0 of 8 episodes indexed; counting method CM-1).")
    rels = cat.q("SELECT e.display_id, c2.credited_name, r.rel_type, r.description FROM relationship r JOIN character c2 ON c2.uuid=r.to_character "
                 "JOIN entity e ON e.uuid=r.to_character WHERE r.from_character=?", char)
    L.append("\n## 5. Key relationships")
    L.append("\n".join(f"- {d} {n}: {t}" + (f" ({desc})" if desc else "") for d, n, t, desc in rels) or "- None recorded yet")
    if prof:
        for sec, title in (("role_reported", "6. Role in the series (as reported by reviews; not yet seen)"),
                           ("arc", "7. Arc evidence"), ("standout", "8. Standout moments"),
                           ("angles", "9. Proposed montage angles"), ("posts", "10. Proposed posts, credit lines and hashtags"),
                           ("actor_bio", "11. Actor biography (separate from the character)"),
                           ("historical_bio", "12. Historical-person biography (separate from the character)"),
                           ("show_vs_history", "13. Show vs. history"), ("sensitive", "14. Spoiler and sensitive-content flags"),
                           ("open_questions", "15. Unresolved questions")):
            if sec in prof:
                L.append(f"\n## {title}\n" + (prof[sec] if isinstance(prof[sec], str) else "\n".join(f"- {x}" for x in prof[sec])))
    else:
        L.append("\n## 6–15. Role, arc, moments, angles, bios, sensitivity\nNot yet researched. The credit alone does not establish a historical counterpart. "
                 f"Arc, moments and continuity: {PENDING}. Spoiler level: unknown.")
    cl = _claims(cat, char)
    L.append("\n## Sources, claims and confidence")
    if cl:
        L.append("| Claim | Text | Domain | Class | Status | Sources | Notes |\n|---|---|---|---|---|---|---|")
        L.extend(cl)
    else:
        L.append("Only the casting credit (see ingestion records) is on file.")
    q = cat.q("SELECT kind, payload_json FROM review_queue WHERE status='open' AND candidates_json LIKE ?", f"%{char}%")
    if q:
        L.append("\n## Open review items touching this character")
        L.extend(f"- **{k}**: {json.loads(p).get('credit', '')} — {json.loads(p).get('issue', '')}" for k, p in q)
    return "\n".join(L) + "\n"


def directory(cat: Catalog, work: str) -> str:
    title = cat.one("SELECT title FROM work WHERE uuid=?", work)[0]
    L = [header(cat, f"Character directory: {title}", [work])]
    L.append("Identification of who appears on screen: **Unresolved for every character** until authorized footage is reviewed. "
             "\"Credit verification\" describes the casting credit only.\n")
    L.append("| CHR | Exact credited name | Performer (POR) | Age | Credit | Credit verif. | IMDb ep. credits | Counterpart status | Sheet |\n|---|---|---|---|---|---|---|---|---|")
    for (u,) in cat.q("SELECT c.uuid FROM character c JOIN entity e ON e.uuid=c.uuid WHERE c.work_uuid=? ORDER BY e.display_id", work):
        c = cat.one("SELECT credited_name, counterpart_status FROM character WHERE uuid=?", u)
        ps = cat.q("SELECT p.uuid, pe.name, p.age_portrayal, p.credit_status, p.credit_verification, p.credited_episode_count FROM portrayal p "
                   "JOIN person pe ON pe.uuid=p.person_uuid WHERE p.character_uuid=? ORDER BY p.age_portrayal", u)
        for i, p in enumerate(ps or [(None, "—", "", "", "", None)]):
            L.append(f"| {cat.did(u) if i == 0 else '↳'} | {c[0] if i == 0 else ''} | {p[1]}" + (f" ({cat.did(p[0])})" if p[0] else "") +
                     f" | {p[2]} | {p[3]} | {p[4]} | {p[5] if p[5] is not None else '—'} | {c[1] if i == 0 else ''} | " +
                     (f"[sheet](characters/{cat.did(u)}_{slug(c[0])}.md)" if i == 0 else "") + " |")
    return "\n".join(L) + "\n"


def installment_doc(cat: Catalog, inst: str) -> str:
    i = dict(cat.one("SELECT * FROM installment WHERE uuid=?", inst))
    nums = cat.q("SELECT scheme, label FROM installment_number WHERE installment_uuid=?", inst)
    eds = cat.q("SELECT uuid, name FROM edition WHERE installment_uuid=?", inst)
    label = ", ".join(f"{s}: {l}" for s, l in nums)
    L = [header(cat, f"{cat.did(inst)} · {i['title'] or '(title unconfirmed)'}", [inst] + [e[0] for e in eds])]
    season = cat.one("SELECT label FROM season WHERE uuid=?", i["season_uuid"]) if i["season_uuid"] else None
    L.append("| Field | Value |\n|---|---|")
    L.append(f"| Work / season / installment | {cat.did(i['work_uuid'])} / {season[0] + ' (' + cat.did(i['season_uuid']) + ')' if season else 'n/a'} / {cat.did(inst)} ({i['kind']}) |")
    L.append(f"| Numbering labels | {label or '—'} |")
    L.append("| Editions | " + (", ".join(f"{cat.did(e[0])} {e[1]}" for e in eds) or "—") + " |")
    assets = cat.q("SELECT a.uuid, a.original_filename FROM asset a WHERE a.edition_uuid IN (SELECT uuid FROM edition WHERE installment_uuid=?)", inst)
    L.append("| Source assets | " + (", ".join(f"{cat.did(a[0])} {a[1]}" for a in assets) or "**None supplied**") + " |")
    L.append(f"| Reviewed coverage | {'0%' if not assets else 'see annotation sets'} |")
    L.append(f"| Synopsis / spoiler level | {i['synopsis'] or 'Pending review'} / {i['spoiler_level'] or 'Pending review'} |")
    for f in ("Scene list", "Character appearances", "Transcript links", "Narrative chronology", "Sensitive-content flags", "Candidate clips / montage contributions"):
        L.append(f"| {f} | Pending review |")
    L.append("| Rights status | Footage: **Unknown** (no permission document on file) |")
    cl = _claims(cat, inst)
    if cl:
        L.append("\n## Claims\n| Claim | Text | Domain | Class | Status | Sources | Notes |\n|---|---|---|---|---|---|---|")
        L.extend(cl)
    L.append("\n## Missing\n- Authorized source file, transcript/subtitles, permission document.")
    return "\n".join(L) + "\n"


def review_queue_doc(cat: Catalog) -> str:
    L = [header(cat, "Open review queue", [])]
    L.append("| # | Kind | Credit / item | Actor | Issue | Candidates | From |\n|---|---|---|---|---|---|---|")
    for rid, ing, kind, payload, cands in cat.q("SELECT id, ingestion_uuid, kind, payload_json, candidates_json FROM review_queue WHERE status='open' ORDER BY id"):
        p = json.loads(payload)
        cs = ", ".join(cat.did(c) + " " + (cat.one("SELECT credited_name FROM character WHERE uuid=?", c) or cat.one("SELECT name FROM person WHERE uuid=?", c) or [""])[0]
                       for c in json.loads(cands or "[]"))
        extra = f" (also rows {', '.join(p['batch_rows'])})" if p.get("batch_rows") else ""
        L.append(f"| {rid} | {kind} | {p.get('credit') or p.get('doubles_for') or p.get('person') or p.get('phrase', '')} | {p.get('actor') or p.get('crew', '')} | {p.get('issue', '')}{extra} | {cs or '—'} | {cat.did(ing) if ing else '—'} |")
    return "\n".join(L) + "\n"


def rights_doc(cat: Catalog) -> str:
    L = [header(cat, "Rights register", [])]
    L.append("| RGT | Asset | Class | Holder | Permission/licence evidence | Platforms | Monetization | Restrictions / conditions | Status |\n|---|---|---|---|---|---|---|---|---|")
    for r in cat.q("SELECT * FROM rights r JOIN entity e ON e.uuid=r.uuid ORDER BY e.display_id"):
        r = dict(r)
        L.append(f"| {cat.did(r['uuid'])} | {r['asset_description']} | {r['asset_class']} | {r['holder'] or 'Unknown'} | {r['evidence'] or 'None on file'} | "
                 f"{', '.join(json.loads(r['platforms_json'] or '[]')) or '—'} | {r['monetization'] or 'Unknown'} | {r['conditions'] or ''} | **{r['status']}** |")
    return "\n".join(L) + "\n"


def data_dictionary(cat: Catalog) -> str:
    L = [f"# Data dictionary\n\n> Generated {now()} from the live schema (migrations: "
         + ", ".join(r[0] for r in cat.q("SELECT version FROM schema_migration ORDER BY version")) + ").\n"]
    for (t,) in cat.q("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        L.append(f"\n## `{t}`\n| Column | Type | Required | Default | Key / reference |\n|---|---|---|---|---|")
        fks = {f[3]: f"→ {f[2]}.{f[4]}" for f in cat.q(f"PRAGMA foreign_key_list({t})")}
        for col in cat.q(f"PRAGMA table_info({t})"):
            L.append(f"| {col[1]} | {col[2]} | {'yes' if col[3] or col[5] else ''} | {col[4] if col[4] is not None else ''} | {'PK ' if col[5] else ''}{fks.get(col[1], '')} |")
        sql = cat.one("SELECT sql FROM sqlite_master WHERE name=?", t)[0]
        checks = re.findall(r"CHECK \(([^)]*\([^)]*\)[^)]*|[^)]*)\)", sql)
        uniq = re.findall(r"UNIQUE \(([^)]*)\)", sql)
        if checks or uniq:
            L.append("\nConstraints: " + "; ".join([f"CHECK {c}" for c in checks] + [f"UNIQUE ({u})" for u in uniq]))
    return "\n".join(L) + "\n"


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path

"""Review-queue resolutions, 2026-11-09 (Iman's instruction #8). Idempotent: only acts on items still open."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent; sys.path.insert(0, str(ROOT))
from tic.core import Catalog, norm, now
cat = Catalog(ROOT / "catalog" / "catalog.sqlite", actor="claude-producer (per Iman 2026-11-09)")
W = cat.q("SELECT uuid FROM work")[0][0]
def item(i): return cat.one("SELECT status, payload_json, candidates_json FROM review_queue WHERE id=?", i)
def person(actor): return cat.find_person(actor)[0][0]
def close(i, text): cat.db.execute("UPDATE review_queue SET status='resolved', resolution=? WHERE id=?", (f"{now()} {text}", i))
out = []
# 1. Young Cassius → proposed young portrayal of CHR-000001 (Iman's direction), pending episode credits
st, p, c = item(1)
if st == "open":
    ali = cat.resolve("CHR-000001"); pe = person("Elias Leacock")
    por = cat.create("portrayal", dict(character_uuid=ali, person_uuid=pe, age_portrayal="young", credit_status="credited",
                                       credit_verification="V1-IMDb", credited_episode_count=2,
                                       notes="PROPOSED by Iman 2026-11-09: younger Cassius Clay/Muhammad Ali. Credited separately from Jaalen Best. Verify against episode end credits."))
    cat.db.execute("INSERT OR IGNORE INTO portrayal_credit_name VALUES (?,?,?,NULL)", (por, "Young Cassius", "Elias Leacock"))
    cat.db.execute("INSERT OR IGNORE INTO character_name VALUES (?,?,?,?,?,?)", (ali, "Young Cassius", norm("Young Cassius"), "credited_young_portrayal", "proposed", "IMDb paste + Iman"))
    close(1, f"Proposed young portrayal of CHR-000001 ({cat.did(por)}, Elias Leacock); pending episode credits")
    out.append(f"#1 Young Cassius → {cat.did(por)} young portrayal of CHR-000001 (proposed)")
# Generic roles with a different credited performer → distinct characters (relation to similar names unverified)
for i in (7, 8, 9, 10, 13, 15, 16, 17, 18):
    st, p, c = item(i)
    if st != "open": continue
    p = json.loads(p); cands = [cat.did(x) for x in json.loads(c or "[]")]
    name = p["credit"]; actor = p["actor"]
    label = name if not cat.find_character(W, name) else f"{name} ({actor})"   # same generic name, different performer
    ch = cat.create("character", dict(work_uuid=W, credited_name=label, norm_name=norm(label), counterpart_status="unconfirmed",
                                      notes=f"IMDb credit '{name}' ({actor}). Distinct credited performer; any relation to {', '.join(cands) or 'similar names'} unverified."))
    if label != name:
        cat.db.execute("INSERT OR IGNORE INTO character_name VALUES (?,?,?,?,?,?)", (ch, name, norm(name), "credited_generic_name", "imdb", "IMDb paste"))
    note = "uncredited" if p.get("row") and int(p["row"]) >= 125 else "credited"
    por = cat.create("portrayal", dict(character_uuid=ch, person_uuid=person(actor), credit_status=note, credit_verification="V1-IMDb", credited_episode_count=1))
    cat.db.execute("INSERT OR IGNORE INTO portrayal_credit_name VALUES (?,?,?,NULL)", (por, name, actor))
    close(i, f"Created {cat.did(ch)} as a distinct role (different performer); relation to {', '.join(cands) or '—'} unverified; not used in any current edit")
    out.append(f"#{i} {name} ({actor}) → {cat.did(ch)}")
for i in (2, 11, 19):  # announcer credits: affect the Bird Clay cut (announcer audio) → keep open for Iman
    cat.db.execute("UPDATE review_queue SET resolution=? WHERE id=? AND status='open'", ("AFFECTS EDIT (Bird Clay announcer) — needs Iman/episode credits", i))
cat.commit(); print("\n".join(out) or "nothing open to resolve")

"""Command line: python3 -m tic.cli <command>
  docs     regenerate all documents for every work
  backup   write a timestamped backup and verify that it restores
  status   counts, open review items, stale flags
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .core import Catalog, ROOT
from . import docs

DB = ROOT / "catalog" / "catalog.sqlite"


def cmd_docs(cat):
    for (w,) in cat.q("SELECT uuid FROM work"):
        title = cat.one("SELECT title FROM work WHERE uuid=?", w)[0]
        base = ROOT / "works" / f"{cat.did(w)}_{docs.slug(title)}"
        docs.write(base / "CHARACTER_DIRECTORY.md", docs.directory(cat, w))
        n = 0
        for (c,) in cat.q("SELECT uuid FROM character WHERE work_uuid=?", w):
            name = cat.one("SELECT credited_name FROM character WHERE uuid=?", c)[0]
            docs.write(base / "characters" / f"{cat.did(c)}_{docs.slug(name)}.md", docs.character_sheet(cat, c)); n += 1
        for (i,) in cat.q("SELECT uuid FROM installment WHERE work_uuid=?", w):
            lab = cat.one("SELECT label FROM installment_number WHERE installment_uuid=? ORDER BY scheme LIMIT 1", i)
            docs.write(base / "installments" / f"{cat.did(i)}_{lab[0] if lab else 'feature'}.md", docs.installment_doc(cat, i))
        print(f"{cat.did(w)}: directory + {n} character sheets + installment docs → {base.relative_to(ROOT)}")
    docs.write(ROOT / "docs" / "generated" / "REVIEW_QUEUE.md", docs.review_queue_doc(cat))
    docs.write(ROOT / "docs" / "generated" / "RIGHTS_REGISTER.md", docs.rights_doc(cat))
    docs.write(ROOT / "docs" / "generated" / "DATA_DICTIONARY.md", docs.data_dictionary(cat))
    for (u, did, rep) in cat.q("SELECT i.uuid, e.display_id, i.report_json FROM ingestion i JOIN entity e ON e.uuid=i.uuid"):
        r = json.loads(rep or "{}")
        body = [f"# Intake report {did}\n", "| Added | Matched | Updated | Conflicting | Unresolved | Affected outputs |", "|---|---|---|---|---|---|",
                "| " + " | ".join(str(len(r.get(k, []))) for k in ("added", "matched", "updated", "conflicting", "unresolved", "affected_outputs")) + " |"]
        for k in ("conflicting", "unresolved", "updated", "added", "matched"):
            if r.get(k):
                body.append(f"\n## {k.title()}\n" + "\n".join(f"- {x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)}" for x in r[k]))
        docs.write(ROOT / "intake" / did / "INTAKE_REPORT.md", "\n".join(body) + "\n")


def cmd_backup(cat):
    cat.commit()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bk = cat.backup(ROOT / "catalog" / "backups" / f"catalog_{stamp}.sqlite")
    res = cat.verify_restore(bk, ROOT / "catalog" / "backups" / ".restore_check.sqlite")
    (ROOT / "catalog" / "backups" / ".restore_check.sqlite").unlink()
    print(bk.name, json.dumps(res))


def cmd_status(cat):
    for t in ("work", "installment", "person", "character", "portrayal", "asset", "scene", "appearance", "claim", "project", "export", "post"):
        print(f"{t:12s} {cat.one(f'SELECT count(*) FROM {t}')[0]}")
    print("open review items", cat.one("SELECT count(*) FROM review_queue WHERE status='open'")[0])
    print("open stale flags ", cat.one("SELECT count(*) FROM stale_flag WHERE resolved=0")[0])


if __name__ == "__main__":
    c = Catalog(DB, actor="cli")
    {"docs": cmd_docs, "backup": cmd_backup, "status": cmd_status}[sys.argv[1]](c)

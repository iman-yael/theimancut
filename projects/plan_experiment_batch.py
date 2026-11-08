"""Initial experiment batch as CONCEPT records (idempotent): 6 character edits, 3 narrated breakdowns, 1 channel intro.
All footage-dependent fields stay pending; nothing here asserts what a scene contains."""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tic.core import Catalog  # noqa: E402
from tic.docs import header, write  # noqa: E402

cat = Catalog(ROOT / "catalog" / "catalog.sqlite", actor="claude-producer")
W = cat.one("SELECT entity_uuid FROM external_id WHERE provider='imdb' AND value='tt15715850'")[0]
v0 = lambda n: cat.one("SELECT entity_uuid FROM external_id WHERE provider='tic-v0' AND value=?", f"CHR-{n:03d}")[0]  # noqa: E731
byname = lambda n: cat.find_character(W, n)[0][0]  # noqa: E731

BATCH = [
 # (key, title, format tag, characters, premise (proposed), hypothesis, spoiler, sensitivity, research status)
 ("E1", "Bird Clay character portrait", "format:character_portrait", [v0(3)], "See PRJ-000001.", "Quiet-performance opening holds attention comparably to a conflict-led opening.", "S1", "DV-adjacent: non-graphic only", "Casting supported; history unchecked"),
 ("E2", "The Clay Brothers", "format:relationship_montage", [v0(1), v0(4)], "Before he was the champion, he was someone's big brother: the scene suggests Rudy is his first audience.", "Relationship framing earns more shares than single-character framing (compare with E1 on the same platform).", "S1–S2", "Low; young portrayals labelled with the correct performers", "Casting supported; Young Cassius queued"),
 ("E3", "Sonny & Geraldine", "format:relationship_montage", [v0(5), v0(6)], "The champion the papers called a menace, seen through the person who read the papers to him.", "A 'villain's tenderness' angle drives comments that discuss the character rather than the outcome.", "S1", "Period-press stereotyping; contested allegations kept out", "Scene lead from a review only (CLM-000016)"),
 ("E4", "Jaalen Best: range reel", "format:actor_spotlight", [v0(1)], "Proposed: Best's performance lives in the shift from showman to listener.", "Performance-led spotlights retain better than narrated ones (A/B across E4 and E1).", "S1–S2", "Racism context; check fight shots for stunt double (Daniel Lavigne)", "Pending footage"),
 ("E5", "In the corner: Dundee & Bundini", "format:thematic_study", [v0(7), v0(9)], "Two very different voices in one corner; what each gives the fighter.", "Thematic studies attract follows from boxing audiences (watch the follow rate).", "S2–S3", "Fight violence: no injury close-ups on the cover", "Bundini quote attribution disputed; check before use"),
 ("E6", "Cassius & Malcolm", "format:relationship_montage", [v0(1), v0(8)], "Proposed: the series frames Malcolm X as both mentor and mirror; the scene evidence must confirm this.", "History-adjacent relationship edits prompt 'what really happened' questions → feeds breakdowns.", "S2–S3", "Religion and political violence; neutral framing", "History unchecked"),
 ("B1", "Who was Alberta Jones?", "format:historical_breakdown", [byname("Alberta Jones")], "The Louisville lawyer behind Cassius Clay's first pro contract (single independent source; needs a second).", "Little-known-history breakdowns earn saves.", "S0", "Violent death (1965, unsolved): factual, no speculation", "CLM-000017 single source; CLM-000018/19 conflicting"),
 ("B2", "Who bankrolled Cassius Clay?", "format:historical_breakdown", [v0(10)], "The Louisville Sponsoring Group and William Faversham Jr.: how the deal was structured (research needed).", "Business-history angle broadens the audience (track new-follower share).", "S0", "Low; race and money framed with care", "Unchecked; Filson Historical Society archive is a lead"),
 ("B3", "Sonny Liston beyond the headlines", "format:historical_breakdown", [v0(5)], "What's documented, what's alleged, and what's still unknown about Liston.", "A claim-status framing (documented/alleged/unknown) builds trust (watch comment sentiment by sample review).", "S3 if fight results are discussed", "Contested allegations; incarceration; avoid 'menace' stereotyping", "Unchecked; birth year disputed (CLM-000015)"),
 ("I1", "I'm Iman Yael, and this is The Iman Cut", "format:channel_intro", [], "What viewers get here: performance, character and history, through one consistent point of view.", "An intro pinned on the profile converts profile visits to follows.", "S0", "None", "Uses only facts Iman supplies about herself"),
]

INTRO_SCRIPT = [
 ("0:00–0:03", "Iman on camera or a voice-over on a branded card (Iman's choice)", "I'm Iman Yael, and this is The Iman Cut.", "Editorial (Iman)"),
 ("0:03–0:12", "Quick textless cards: CHARACTER · PERFORMANCE · HISTORY", "I watch film and TV for the choices people make: the actors, the characters, and the real history underneath.", "Editorial (Iman)"),
 ("0:12–0:22", "Cards only, no show footage until rights are documented", "I'll tell you what I notice, what the scene suggests, and what the record actually shows, and I'll keep those three things separate.", "Editorial (Iman)"),
 ("0:22–0:28", "End card: THE IMAN CUT · By Iman Yael", "First up: The Greatest. Who should I cover first?", "Editorial (Iman)"),
 ("—", "—", "[OPTIONAL LINE, IMAN SUPPLIES: one true sentence about her own background. Not written for her.]", "Placeholder"),
]

made = []
for key, title, fmt, chars, premise, hyp, spoiler, sens, research in BATCH:
    r = cat.one("SELECT uuid FROM concept WHERE title=?", title)
    if not r:
        u = cat.create("concept", dict(title=title, premise=premise, format=fmt.split(":")[1], hypothesis=hyp,
                                       audience="See packaging", focus_json=json.dumps([cat.did(c) for c in chars])))
        cat.depends(u, *chars)
        cat.db.execute("INSERT OR IGNORE INTO entity_tag VALUES (?,?)", (u, fmt))
        for s in spoiler.replace("–", " ").split():
            if s in ("S0", "S1", "S2", "S3"):
                cat.db.execute("INSERT OR IGNORE INTO entity_tag VALUES (?,?)", (u, f"spoiler:{s}"))
        r = (u,)
    made.append((key, r[0], title, fmt, chars, premise, hyp, spoiler, sens, research))
cat.commit()

L = [header(cat, "Experiment batch v1: 6 edits · 3 narrated breakdowns · 1 intro (PROPOSED)", [m[1] for m in made]),
     "Proposals only. No footage has been reviewed, so every premise is a hypothesis to test against the scenes. Order of work: E1 → E2 → B1 → E3 → I1 → others, depending on approvals and footage.\n",
     "| # | CON | Title | Format | Characters | Proposed premise | Packaging hypothesis | Spoiler | Sensitivity | Research status |",
     "|---|---|---|---|---|---|---|---|---|---|"]
for key, u, title, fmt, chars, premise, hyp, spoiler, sens, research in made:
    L.append(f"| {key} | {cat.did(u)} | {title} | {fmt.split(':')[1]} | {', '.join(cat.did(c) for c in chars) or '—'} | {premise} | {hyp} | {spoiler} | {sens} | {research} |")
L += ["\n**Follow-ups:** any post that reaches 1,000,000 views on a single platform is flagged for a substantial narrated deep dive on its character, actor or history. Shorter explainers are tested before that milestone whenever comments ask for them.",
      "\n## I1 channel intro: draft script (≈28 s; no claims about Iman beyond what she supplies)",
      "| Timeline | Visual | Line | Line type |\n|---|---|---|---|"]
L += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in INTRO_SCRIPT]
L.append("\nDisclosure if delivered by the digital presenter or digital voice: \"AI presenter based on my likeness\" on screen, plus the platform AI label.")
write(ROOT / "projects" / "EXPERIMENT_BATCH_v1.md", "\n".join(L) + "\n")

# Hook library (proposed AND, later, published/tested — unsuccessful tests are kept)
with open(ROOT / "analytics" / "TIC_HOOK_LIBRARY.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["pkg_id", "project_id", "platform", "format", "character_ids", "hook_style", "hook_text", "recommended", "status", "result_note"])
    for pk, prj, plat, hooks, rec in cat.q("SELECT p.uuid, p.project_uuid, p.platform, p.hooks_json, p.recommended_hook FROM packaging p"):
        con = cat.one("SELECT c.format, c.focus_json FROM project pr JOIN concept c ON c.uuid=pr.concept_uuid WHERE pr.uuid=?", prj)
        for style, text in json.loads(hooks).items():
            w.writerow([cat.did(pk), cat.did(prj), plat, con[0], " ".join(json.loads(con[1])), style, text, "yes" if text == rec else "",
                        "proposed (untested)", ""])
print("concepts:", len(made), "→ projects/EXPERIMENT_BATCH_v1.md, analytics/TIC_HOOK_LIBRARY.csv")

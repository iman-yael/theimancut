"""Pilot: CHR-000003 Odessa 'Bird' Clay character portrait. Writes concept/project/scripts/packaging to the
catalog (idempotent) and generates the proposal documents from those records."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tic.core import Catalog, now  # noqa: E402
from tic.docs import header, write  # noqa: E402

cat = Catalog(ROOT / "catalog" / "catalog.sqlite", actor="claude-producer")
BIRD = cat.one("SELECT entity_uuid FROM external_id WHERE provider='tic-v0' AND value='CHR-003'")[0]
ALI = cat.one("SELECT entity_uuid FROM external_id WHERE provider='tic-v0' AND value='CHR-001'")[0]
RUDY = cat.one("SELECT entity_uuid FROM external_id WHERE provider='tic-v0' AND value='CHR-004'")[0]
CLM = {t: u for u, t in cat.q("SELECT uuid, text FROM claim WHERE subject_uuid=?", BIRD)}
HIST = [u for t, u in CLM.items() if t.startswith("Odessa Grady Clay was")][0]

PREMISE = ("PROPOSED (to be tested against the footage): In *The Greatest*, the first person in Cassius Clay's corner "
           "is not a trainer but his mother. This portrait shows how Dana Gourrier plays Bird's steadiness as a choice "
           "she keeps making, not just warmth.")

# Timed narrated script. Every footage slot is a SELECTION CRITERION, not a scene: no timestamps exist yet.
NARRATED = [
 dict(t="0:00–0:04", src="SLOT-1 · PENDING", visual="Bird, close, a quiet reaction that reads without context", dlg="—", vo="—", label="—",
      text="DANA GOURRIER / as ODESSA 'BIRD' CLAY (label 0.3–4 s)", audio="Scene audio only; let the face land"),
 dict(t="0:04–0:11", src="SLOT-2 · PENDING", visual="Bird with Cassius and/or Rudy (Ep1–2 preferred; any young portrayal labelled with the correct performer)",
      dlg="PENDING: verbatim, keep if it carries the moment", vo="In The Greatest, the first person in Cassius Clay's corner isn't a trainer. It's his mother.",
      label="Editorial interpretation · confirm after viewing", text="—", audio="Duck scene under VO −12 dB; no VO over dialogue"),
 dict(t="0:11–0:21", src="SLOT-3 · PENDING", visual="Her strongest line in a warm/humorous register", dlg="PENDING: original dialogue, verbatim", vo="—", label="Original dialogue",
      text="—", audio="Full scene audio; preserve pauses"),
 dict(t="0:21–0:29", src="SLOT-4 · PENDING", visual="Pressure on the household, from Bird's perspective. NON-GRAPHIC: no violence shown; reaction or aftermath only, if used at all",
      dlg="PENDING", vo="The series doesn't make her life easy. Watch what Gourrier does with the moments after: [REWRITE AFTER VIEWING: one specific, observable acting choice].",
      label="Editorial interpretation · BLOCKED until viewed", text="Content note at 0:21 only if this slot depicts or references abuse", audio="No dramatic stingers"),
 dict(t="0:29–0:39", src="SLOT-5 · PENDING", visual="A decision or stand she takes (turning point ONLY if the footage supports one; otherwise a second 'resolve' beat)",
      dlg="PENDING: verbatim", vo="—", label="Original dialogue", text="—", audio="Full scene audio"),
 dict(t="0:39–0:46", src="Archival/graphic card (rights needed) or plain text card", visual="Text card or licensed photo",
      dlg="—", vo="The real Odessa Grady Clay raised two sons in segregated Louisville.", label="Verified historical information · BLOCKED: claims unchecked",
      text="Odessa Grady Clay · Louisville, KY", audio="Soft bed, licensed only"),
 dict(t="0:46–0:52", src="SLOT-6 · PENDING", visual="Closing beat: a callback to SLOT-1 or a final look", dlg="PENDING", vo="—", label="Original dialogue / silence",
      text="Which moment of hers stayed with you?", audio="Let silence finish; hard out"),
]
PERFORMANCE = [
 ("0:00–0:04", "SLOT-1", "Quiet reaction; ID label"), ("0:04–0:14", "SLOT-2", "With her sons; one context card if needed: 'Louisville, KY · late 1950s' (verify the period the scene depicts)"),
 ("0:14–0:24", "SLOT-3", "Warm/humorous line"), ("0:24–0:32", "SLOT-4", "Pressure, non-graphic, her perspective"),
 ("0:32–0:42", "SLOT-5", "Decision or resolve"), ("0:42–0:48", "SLOT-6", "Closing look / callback; end card 'THE IMAN CUT · By Iman Yael'"),
]
HOOKS = {
 "search-led": "Dana Gourrier as Bird Clay in The Greatest",
 "curiosity-led": "Ali's first corner wasn't in a gym",
 "performance-led": "Watch what Dana Gourrier does when nobody's talking",
 "emotional": "Before the world believed in him, she did",
 "character-contrast": "Everyone remembers the fighter. This is the woman who raised him.",
 "historical-context": "Who was the real Odessa 'Bird' Clay?  [BLOCKED until CLM-000010 is sourced]",
}
PLATFORM_COPY = {
 "IG": "Ali's first corner wasn't in a gym.\n\nIn Prime Video's The Greatest, Dana Gourrier plays Odessa 'Bird' Clay, Cassius Clay's mother. [ONE OBSERVATION AFTER VIEWING]\n\nWhich moment of hers stayed with you?\n\nDana Gourrier as Odessa 'Bird' Clay · The Greatest (Prime Video) · The Iman Cut, by Iman Yael\n#TheGreatest #MuhammadAli #CharacterStudy #DanaGourrier",
 "TT": "Dana Gourrier as Bird Clay, Muhammad Ali's mom in The Greatest on Prime Video. [ONE OBSERVATION]. Which moment stayed with you?\n#TheGreatest #MuhammadAli #DanaGourrier #CharacterStudy",
 "FB": "Haven't started The Greatest yet? Prime Video's eight-episode series follows a young Cassius Clay in Louisville before the world knew him as Muhammad Ali. At the centre of his home is his mother, Odessa 'Bird' Clay, played by Dana Gourrier. [ONE OBSERVATION]\n\nWhich moment of hers stayed with you?\n\nThe Iman Cut, by Iman Yael. Not affiliated with Prime Video or the production.\n#TheGreatest #MuhammadAli #CharacterStudy",
 "YT": "TITLE: Dana Gourrier as Bird Clay | The Greatest (Prime Video) | The Iman Cut\nDESCRIPTION: A character portrait of Odessa 'Bird' Clay, Muhammad Ali's mother, as played by Dana Gourrier in Prime Video's The Greatest. Commentary by Iman Yael. [AI-narration disclosure if a digital voice is used.] Not affiliated with Prime Video or the production.\nSources for historical lines: [from SOURCES once CLM-000010 is sourced]\n#TheGreatest #MuhammadAli #CharacterStudy",
}

con = cat.one("SELECT uuid FROM concept WHERE title=?", "Bird Clay character portrait")
if not con:
    con = cat.create("concept", dict(title="Bird Clay character portrait", premise=PREMISE, format="Character portrait (narrated recommended; performance-led fallback)",
                                     hypothesis="A portrait led by a quiet performance beat holds attention as well as a confrontation-led clip, measured by average watch % (per platform, same elapsed time).",
                                     audience="Viewers of The Greatest; people searching the actor/character; Ali-history audience", focus_json=json.dumps(["CHR-000003"])))
    cat.depends(con, BIRD)
    prj = cat.create("project", dict(concept_uuid=con, title="Bird Clay: character portrait", slug="BirdClay", status="Proposed",
                                     cost_estimate="$0 render (local ffmpeg); voice service cost unknown until you name the service", cost_actual="$0"))
    cat.depends(prj, con)
    s1 = cat.create("script", dict(project_uuid=prj, approach="narrated", body_json=json.dumps(NARRATED, ensure_ascii=False), status="draft"))
    s2 = cat.create("script", dict(project_uuid=prj, approach="performance_led", body_json=json.dumps(PERFORMANCE, ensure_ascii=False), status="draft"))
    cat.depends(s1, BIRD, HIST, prj); cat.depends(s2, BIRD, prj)
    for plat, copy in PLATFORM_COPY.items():
        pk = cat.create("packaging", dict(project_uuid=prj, platform=plat, language="EN", primary_phrase="Dana Gourrier Bird Clay The Greatest",
                                          related_json=json.dumps(["Odessa Clay The Greatest", "Muhammad Ali mother", "The Greatest Prime Video cast"]),
                                          intent="Viewers who just watched the show and are searching the actor/character", hooks_json=json.dumps(HOOKS, ensure_ascii=False),
                                          recommended_hook=HOOKS["curiosity-led"], cover_headline="Ali's first corner",
                                          title="Dana Gourrier as Bird Clay | The Greatest" if plat == "YT" else None, caption=copy,
                                          hashtags_json=json.dumps(["#TheGreatest", "#MuhammadAli", "#CharacterStudy", "#DanaGourrier"]), mentions_json="[]",
                                          pinned_comment="Dana Gourrier plays Odessa 'Bird' Clay in The Greatest (Prime Video). Scenes are dramatized; historical notes and sources are in the description. Which character should The Iman Cut cover next?",
                                          sources_json=json.dumps(["CLM-000004", "CLM-000010", "CLM-000011"]),
                                          hypothesis="Curiosity hook vs. search hook: compare 3-s hold and average watch % on the same platform at 48 h", provisional=1))
        cat.depends(pk, prj, s1)
    cat.commit()
prj = cat.one("SELECT uuid FROM project WHERE slug='BirdClay'")[0]
s1 = cat.one("SELECT uuid FROM script WHERE project_uuid=? AND approach='narrated'", prj)[0]
s2 = cat.one("SELECT uuid FROM script WHERE project_uuid=? AND approach='performance_led'", prj)[0]
P = cat.did(prj)
base = ROOT / "projects" / f"{P}_BirdClay"
pre = f"TIC_{P}_BirdClay_CharacterPortrait"

rows = json.loads(cat.one("SELECT body_json FROM script WHERE uuid=?", s1)[0])
vo_words = sum(len(r["vo"].split()) for r in rows if r["vo"] != "—")
L = [header(cat, f"{P} · Bird Clay: character portrait (PROPOSAL, for review)", [prj, s1, s2]),
     "**Status:** Proposed. Nothing selected from footage, because none is available. Every footage slot below is a selection criterion, not a scene. No timestamps have been invented.",
     f"\n## One-sentence premise\n{PREMISE}",
     "\n## Why Bird first\n- Your priority list puts her first, and reviews single her out most consistently among supporting performers (CLM-000011, opinion, single source).\n- A portrait angle can be built from non-graphic material, which lowers the domestic-violence risk compared with the Cash Clay storyline.\n- Low spoiler level (S1).",
     "\n## Angles (from CHR-000003 sheet)\n1. **Character portrait: 'The corner before the corner' (recommended)**\n2. Relationship montage: Bird & Cassius\n3. Performance showcase: Gourrier's range (only if the footage shows that range)",
     "\n## Arc evidence\nBeginning, wants, obstacles, choices, turning point, consequences, where the footage leaves her: **Pending footage review.** It will be labelled *character portrait* unless the footage shows a real turning point.",
     "\n## Recommended approach: **B. Narrated** (perspective from day one), with **A. Performance-led** as the fallback if no voice asset is approved.",
     "\n## A. Performance-led outline (≈48 s)\n| Timeline | Slot | Intent |\n|---|---|---|"]
L += [f"| {a} | {b} | {c} |" for a, b, c in json.loads(cat.one("SELECT body_json FROM script WHERE uuid=?", s2)[0])]
L += ["\n## B. Narrated: timed voice-over script (≈52 s)",
      "| Timeline | Source episode/timecode | Visual | Original dialogue | Voice-over (Iman) | Line type | On-screen text | Audio/edit notes |\n|---|---|---|---|---|---|---|---|"]
L += [f"| {r['t']} | {r['src']} | {r['visual']} | {r['dlg']} | {r['vo']} | {r['label']} | {r['text']} | {r['audio']} |" for r in rows]
L += [f"\n**Timing check:** {vo_words} narration words across about 20 s of VO windows. Read aloud, this sits near the upper limit for a calm pace. **Not yet tested aloud or with your voice:** no voice asset was supplied, and I did not substitute a synthetic voice. Next step: you record a phone read of the three VO lines, and I time them against the slots.",
      "\n**Pronunciation:** Odessa = oh-DESS-uh (standard English; confirm). *Gourrier*: **unverified**. Use the actor's own pronunciation from an interview before recording.",
      "\n**Delivery:** calm and observant; no rising 'trailer' energy. Slot 4 is respectful and unhurried. No accent changes.",
      "\n## Sensitive-content review\n| Content flags | Context preserved | Content note | Resource decision | Historical verification | Platform concerns | Status |\n|---|---|---|---|---|---|---|",
      "| Possible DV-adjacent material (SLOT-4) | Bird's perspective only; no depiction of violence | Only if SLOT-4 depicts or references abuse | If a note is used: a discreet end card with a **verified** resource (placeholder `VERIFY BEFORE PUBLICATION`; none verified yet) | CLM-000010 unchecked → historical VO line blocked | None expected for a non-graphic portrait; re-check once footage is chosen | **Needs review** |",
      "\n## Packaging (provisional: footage not reviewed)\nPrimary search phrase: *Dana Gourrier Bird Clay The Greatest* (editorial choice; no search-volume data).\n\n| Style | Hook |\n|---|---|"]
L += [f"| {k} | {v} |" for k, v in HOOKS.items()]
L += ["\n**Recommended hook:** curiosity-led, 'Ali's first corner wasn't in a gym.' It is specific, truthful if the footage supports the premise, and it doesn't lean on abuse.",
      "**Cover headline:** `Ali's first` / `corner` (2 lines; THE IMAN CUT watermark top-right).",
      "**Hypothesis:** the curiosity hook vs. the search hook, compared on 3-s hold and average watch % on the same platform at 48 h. Correlation only.",
      "\n### Platform copy (drafts; placeholders block publication)"]
for plat in ("IG", "TT", "FB", "YT"):
    L.append(f"\n**{plat}**\n```\n{PLATFORM_COPY[plat]}\n```")
L += ["\n**Pinned comment draft:** Dana Gourrier plays Odessa 'Bird' Clay in The Greatest (Prime Video). Scenes are dramatized; historical notes and sources are in the description. Which character should The Iman Cut cover next?",
      "\n## Deliverable filenames (once rendered)\n" + "\n".join(f"- `{pre}_{p}_1080x1920_EN_v01{s}`" for p in ("IG", "TT", "FB", "YT") for s in (".mp4", "_CLEAN.mp4", "_SUBTITLES.srt")) +
      f"\n- `{pre}_VO.wav` · `{pre}_COVER.jpg` · `{pre}_POST_COPY.md` · `{pre}_SOURCES.md`",
      "\n## To render this pilot I need\n1. An authorized, unencrypted source file for the episodes Bird appears in, with written permission (see RGT-000001).\n2. Your voice: a recorded read, or an authorized digital-voice service you name, with consent on file (RGT-000003).\n3. Your approval of the premise, the recommended approach, and watermark placement A or B."]
write(base / f"{pre}_PROPOSAL.md", "\n".join(L) + "\n")
write(base / f"{pre}_SOURCES.md", header(cat, f"{P} sources", [prj]) + "\n| Claim | Status | Used in |\n|---|---|---|\n" +
      "\n".join(f"| {cat.did(u)} {t} | {cat.one('SELECT status FROM claim WHERE uuid=?', u)[0]} | {'VO 0:39 (blocked)' if u == HIST else 'packaging/credits'} |" for t, u in CLM.items()))
print("wrote", base.relative_to(ROOT))

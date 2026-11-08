"""PRJ-000002: in-app remixes of the OFFICIAL The Greatest trailer (option 2). Nothing is downloaded or re-uploaded;
Iman records inside each app using its own remix tool. Idempotent."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tic.core import Catalog, now  # noqa: E402
from tic.docs import header, write  # noqa: E402

cat = Catalog(ROOT / "catalog" / "catalog.sqlite", actor="claude-producer")
W = cat.one("SELECT entity_uuid FROM external_id WHERE provider='imdb' AND value='tt15715850'")[0]
v0 = lambda n: cat.one("SELECT entity_uuid FROM external_id WHERE provider='tic-v0' AND value=?", f"CHR-{n:03d}")[0]  # noqa: E731
BIRD, SR, RUDY, ALI = v0(3), v0(2), v0(4), v0(1)
did = cat.did

# sources + claims used by the scripts
def source(title, author, url, stype, note):
    r = cat.one("SELECT uuid FROM source WHERE title=?", title)
    return r[0] if r else cat.create("source", dict(title=title, author=author, url=url, source_type=stype, access_date=now()[:10], reliability_note=note))
AMZ = source("Watch the trailer for 'The Greatest,' the Muhammad Ali series coming to Prime Video November 4", "About Amazon (official)",
             "https://www.aboutamazon.com/news/entertainment/the-greatest-muhammad-ali-prime-video", "official_press", "Official Amazon page; embeds the trailer. Seen via snippet.")
HYPE = source("Prime Video Explores Muhammad Ali's Formative Years in Official 'The Greatest' Trailer", "Hypebeast",
              "https://hypebeast.com/2026/10/prime-video-explores-muhammad-ali-formative-years-official-the-greatest-trailer-release-info", "entertainment_press", "Seen via snippet.")
IMDB = cat.one("SELECT uuid FROM source WHERE title LIKE 'IMDb full credits%'")[0]
def claim(subject, text, domain, status, evid, notes=None):
    r = cat.one("SELECT uuid FROM claim WHERE text=?", text)
    if r:
        return r[0]
    u = cat.create("claim", dict(text=text, subject_uuid=subject, domain=domain, claim_class="fact", status=status, notes=notes, checked_at=now()[:10]))
    for s in evid:
        cat.db.execute("INSERT OR IGNORE INTO claim_evidence VALUES (?,?,?,NULL,?)", (u, s, "supports", now()))
    return u
C_AUTH = claim(W, "The Greatest is the first authorized scripted series about Muhammad Ali", "production", "supported", [AMZ, HYPE],
               "'Authorized' per Amazon's own press; attribute it: 'Prime Video calls it…'.")
C_LONNIE = claim(W, "Lonnie Ali, Muhammad Ali's widow, is an executive producer", "production", "supported", [IMDB, AMZ])
C_TRAILER = claim(W, "Official trailer released mid-October 2026 (teaser July 2026)", "production", "supported_single_source", [HYPE])
CL = {t: u for u, t in cat.q("SELECT uuid, text FROM claim")}

R1 = [  # "Meet the Clay family": background remix (YT Green Screen / IG-FB Remix / TT Duet)
 dict(t="0:00–0:03", visual="Iman to camera, trailer in background (any opening shot)", line="Before he was Muhammad Ali, he was Bird Clay's son.",
      kind="Editorial framing (credit-based: the series credits 'Odessa \"Bird\" Clay')", claims=[did(CL["Dana Gourrier is credited as Odessa 'Bird' Clay"])], text="THE CLAY FAMILY in The Greatest"),
 dict(t="0:03–0:09", visual="Trailer background: [IMAN PICKS a moment where Bird is clearly identifiable from context]", line="In The Greatest on Prime Video, Dana Gourrier plays his mother, Odessa.",
      kind="Verified casting", claims=[did(CL["Dana Gourrier is credited as Odessa 'Bird' Clay"])], text="Dana Gourrier / as Odessa 'Bird' Clay (only if she is on screen)"),
 dict(t="0:09–0:14", visual="Trailer background: [moment with Cash Sr., if identifiable]", line="Omari Hardwick plays his father, Cassius Clay Senior.",
      kind="Verified casting", claims=[did(CL["Omari Hardwick is credited as Cassius Clay Sr."])], text="Omari Hardwick / as Cassius Clay Sr."),
 dict(t="0:14–0:19", visual="Trailer background: [moment with Rudy, if identifiable]", line="And Kai Parham plays his younger brother, Rudy.",
      kind="Verified casting", claims=[did(CL["Kai Parham is credited as Rudy Clay"])], text="Kai Parham / as Rudy Clay"),
 dict(t="0:19–0:27", visual="Iman to camera (full frame or large inset)", line="The real Odessa Grady Clay raised both boys in Louisville. Rudy boxed too, and later became Rahaman Ali.",
      kind="Verified history", claims=[did(CL["Odessa Grady Clay was Muhammad Ali's mother"]), did(CL["Rudy Clay later took the name Rahman Ali (spelling also given as Rahaman)"])], text="Historical note"),
 dict(t="0:27–0:31", visual="Iman to camera", line="He died last year, in 2025.", kind="Verified history (calm, respectful delivery)",
      claims=[did(CL["Rahaman Ali (born Rudolph Clay, 1943) died on 1 August 2025 in Louisville, aged 82"])], text="Rahaman Ali, 1943–2025"),
 dict(t="0:31–0:35", visual="Iman to camera, end beat", line="Which Clay do you want me to break down first?", kind="Engagement question", claims=[], text="THE IMAN CUT"),
]
R2 = [  # 5-second Cut/Stitch, then Iman's take
 dict(t="0:00–0:05", visual="Trailer CUT/STITCH: [IMAN PICKS ≤5 s that reads on its own: a line or image from the trailer, not a fight result]", line="(original trailer audio)", kind="Official trailer excerpt via the platform tool", claims=[], text="—"),
 dict(t="0:05–0:12", visual="Iman to camera", line="Prime Video calls this the first authorized scripted series about Muhammad Ali, and his widow, Lonnie Ali, is an executive producer.",
      kind="Verified production fact (attributed)", claims=[did(C_AUTH), did(C_LONNIE)], text="First authorized scripted Ali series (per Prime Video)"),
 dict(t="0:12–0:24", visual="Iman to camera", line="[IMAN'S POINT: choose one of three stances below, or write your own]", kind="Editorial (Iman, to approve)", claims=[], text="—"),
 dict(t="0:24–0:28", visual="Iman to camera", line="Are you watching it? Who's the performance to beat so far?", kind="Engagement question", claims=[], text="THE IMAN CUT"),
]
STANCES = ["(a) 'An authorized story raises a fair question: how honestly will it show the hard parts of his family life? I'll be watching how it treats his mother, Bird.'",
           "(b) 'What I want to see is how it separates the legend from the record, because Ali's life comes with both.'",
           "(c) 'For me, the test is everyone around Ali: his family, his trainers, and his rivals. Great biopics live in the supporting roles.'"]
HOOKS1 = {"search-led": "The Clay family in The Greatest, explained", "curiosity-led": "Before he was Muhammad Ali, he was Bird Clay's son",
          "performance-led": "Dana Gourrier, Omari Hardwick and Kai Parham are the Clays", "emotional": "The family that made Muhammad Ali",
          "character-contrast": "Everyone knows the champion. Meet the people at his kitchen table.", "historical-context": "Who were the real Clays behind The Greatest?"}
HOOKS2 = {"search-led": "The Greatest on Prime Video: first authorized Ali series", "curiosity-led": "Why 'authorized' matters for The Greatest",
          "performance-led": "The performance to beat in The Greatest", "emotional": "Lonnie Ali helped bring this story to the screen",
          "character-contrast": "The legend vs. the record: what to watch for in The Greatest", "historical-context": "What makes The Greatest different from other Ali stories"}
CAPS1 = {
 "IG": "Before he was Muhammad Ali, he was Bird Clay's son.\n\nIn Prime Video's The Greatest: Dana Gourrier as Odessa 'Bird' Clay, Omari Hardwick as Cassius Clay Sr., Kai Parham as Rudy Clay. The real Rudy, later Rahaman Ali, died in 2025.\n\nWhich Clay should I break down first?\n\nThe Iman Cut, by Iman Yael · Not affiliated with Prime Video\n#TheGreatest #MuhammadAli #CharacterStudy #BoxingHistory",
 "TT": "Meet the Clays from The Greatest on Prime Video 👊 Dana Gourrier (Bird), Omari Hardwick (Cassius Clay Sr.), Kai Parham (Rudy). Which Clay should I break down first?\n#TheGreatest #MuhammadAli #PrimeVideo #CharacterStudy",
 "FB": "New to The Greatest? Prime Video's eight-episode series follows young Cassius Clay in Louisville, and his family is at the centre of it. Dana Gourrier plays his mother Odessa 'Bird' Clay, Omari Hardwick his father, and Kai Parham his younger brother Rudy, who in real life boxed too and later became Rahaman Ali (1943–2025).\n\nWhich Clay should I break down first?\n\nThe Iman Cut, by Iman Yael · Not affiliated with Prime Video or the production.\n#TheGreatest #MuhammadAli #BoxingHistory",
 "YT": "TITLE: Meet the Clay Family in The Greatest (Prime Video) | The Iman Cut\nDESCRIPTION: Who's who in Muhammad Ali's family in Prime Video's The Greatest: Dana Gourrier as Odessa 'Bird' Clay, Omari Hardwick as Cassius Clay Sr., Kai Parham as Rudy Clay. Commentary by Iman Yael; remixed from the official trailer using YouTube's Remix tool. Not affiliated with Prime Video.\nSources: Odessa Grady Clay (en.wikipedia.org/wiki/Odessa_Grady_Clay); Rahaman Ali obituary (boxingscene.com); cast: IMDb, Deadline.\n#TheGreatest #MuhammadAli #BoxingHistory"}
CAPS2 = {
 "IG": "Prime Video calls The Greatest the first authorized scripted series about Muhammad Ali, and Lonnie Ali is an executive producer.\n\n[IMAN'S POINT, one line]\n\nWho's the performance to beat so far?\n\nThe Iman Cut, by Iman Yael · Not affiliated with Prime Video\n#TheGreatest #MuhammadAli #FilmAnalysis",
 "TT": "The Greatest on Prime Video is the first authorized Ali series (per Prime Video). Here's what I'm watching for 👀 Who's the performance to beat?\n#TheGreatest #MuhammadAli #PrimeVideo",
 "FB": "Prime Video's The Greatest is billed as the first authorized scripted series about Muhammad Ali; his widow Lonnie Ali is an executive producer. [IMAN'S POINT]. Who's the performance to beat so far?\n\nThe Iman Cut, by Iman Yael · Not affiliated with Prime Video.\n#TheGreatest #MuhammadAli",
 "YT": "TITLE: The Greatest (Prime Video): What 'Authorized' Means | The Iman Cut\nDESCRIPTION: Commentary by Iman Yael on Prime Video's The Greatest, remixed from the official trailer with YouTube's Remix tool. Source: aboutamazon.com press page. Not affiliated with Prime Video.\n#TheGreatest #MuhammadAli"}

r = cat.one("SELECT uuid FROM project WHERE slug='TrailerRemix'")
if not r:
    con = cat.create("concept", dict(title="Official-trailer in-app remixes", premise="Iman's on-camera commentary over Prime Video's official trailer using each platform's own remix tool.",
                                     format="native_remix", hypothesis="Family-explainer remix (R1) earns more follows than the opinion remix (R2), same platform at 48 h.",
                                     audience="People who saw the trailer or the series and want who's-who context", focus_json=json.dumps([did(BIRD), did(SR), did(RUDY)])))
    cat.depends(con, BIRD, SR, RUDY)
    prj = cat.create("project", dict(concept_uuid=con, title="Official-trailer remixes (R1 Clay family, R2 'authorized')", slug="TrailerRemix", status="Proposed",
                                     cost_estimate="$0 (recorded in-app on Iman's phone)", cost_actual="$0"))
    cat.depends(prj, con)
    for name, rows in (("R1", R1), ("R2", R2)):
        s = cat.create("script", dict(project_uuid=prj, approach="narrated", body_json=json.dumps({"remix": name, "rows": rows, "stances": STANCES if name == "R2" else []}, ensure_ascii=False), status="draft"))
        cat.depends(s, prj, *[cat.resolve(c) for row in rows for c in row["claims"]])
        for plat, cap in (CAPS1 if name == "R1" else CAPS2).items():
            pk = cat.create("packaging", dict(project_uuid=prj, platform=plat, language="EN",
                primary_phrase="The Greatest Clay family cast" if name == "R1" else "The Greatest Prime Video authorized Ali series",
                related_json=json.dumps(["The Greatest cast", "Muhammad Ali family", "Dana Gourrier Omari Hardwick Kai Parham"] if name == "R1" else ["Lonnie Ali The Greatest", "The Greatest trailer"]),
                intent="Trailer viewers wanting who's-who" if name == "R1" else "Trailer viewers deciding whether to watch",
                hooks_json=json.dumps(HOOKS1 if name == "R1" else HOOKS2), recommended_hook=(HOOKS1 if name == "R1" else HOOKS2)["curiosity-led"],
                cover_headline="Meet the Clays" if name == "R1" else "'Authorized' Ali", title=cap.split("\n")[0].replace("TITLE: ", "") if plat == "YT" else None,
                caption=cap, hashtags_json=json.dumps([t for t in cap.split() if t.startswith("#")]), mentions_json="[]",
                pinned_comment=("Cast per the series credits. Historical notes: Odessa Grady Clay was Ali's mother; Rudy Clay later became Rahaman Ali (1943–2025). Sources are in the description where links work. Which Clay next?"
                                if name == "R1" else "Prime Video describes The Greatest as the first authorized scripted Ali series; Lonnie Ali is an executive producer. Which performance should I break down first?"),
                sources_json=json.dumps([c for row in rows for c in row["claims"]]),
                hypothesis="Curiosity hook vs. search hook on the same platform: 3-s hold and follows at 48 h", provisional=1))
            cat.depends(pk, s)
    cat.create("rights", dict(covers_uuid=prj, asset_description="Official The Greatest trailer, used ONLY through each platform's in-app remix tool (no download/re-upload)",
                              asset_class="footage", holder="Amazon MGM Studios / Prime Video (uploader)",
                              evidence="Platform terms + uploader's remix setting; confirm the remix button is available on the official post at recording time",
                              platforms_json=json.dumps(["YT", "TT", "IG", "FB"]), monetization="Unknown; remixes may be ineligible or limited",
                              status="Under review", conditions="Only inside the platform where remixed; never cross-post the file (other platforms' watermarks and permissions don't travel); the remix can disappear if the source is removed or remixing is disabled."))
    cat.commit()

prj = cat.one("SELECT uuid FROM project WHERE slug='TrailerRemix'")[0]
P = did(prj)
pre = f"TIC_{P}_TrailerRemix"
L = [header(cat, f"{P} · Official-trailer in-app remix kit (option 2): FOR REVIEW", [prj]),
     "**Status: Proposed.** I have **not** watched the trailer. Moments marked [IMAN PICKS] are chosen by you, in the app, while recording. Every spoken fact below is tied to a sourced claim; cast names are credit-verified.",
     "\n## How it works on each platform (rules from third-party guides; **confirm in the app** before recording)",
     "| Platform | Tool | What you get (per guides) | Use for |\n|---|---|---|---|",
     "| YouTube Shorts | Remix → **Green Screen** (trailer as background, up to ~60 s) or **Cut** (1–5 s clip, then you) | Auto-links to the original. Unavailable if the uploader disabled remixing or Content ID restricts it. | R1 Green Screen · R2 Cut |",
     "| TikTok | **Stitch** (up to 5 s, then you) or **Duet** (side by side) | Works only if Prime Video's post allows reuse of content. | R2 Stitch · R1 Duet |",
     "| Instagram Reels | **Remix** (side by side, green screen, or after the original) | Allowed only if the official reel permits remixing. Automatic 'Remix with' credit. | R1 or R2 |",
     "| Facebook Reels | **Remix** where offered | Availability varies; check the official Prime Video post. | R1 or R2 |",
     "\n**Rules for this format:**\n- Start from the **official verified Prime Video post** on each platform.\n- Never download, screen-record, or re-upload.\n- Record a remix **inside each app separately**. A remix made on one platform can't be cross-posted, because it carries that platform's mark and permission.\n- Add **THE IMAN CUT** as small in-app text, top-right.\n- If the remix button is missing, that post isn't available for remixing: stop there.\n- Rights: RGT record status **Under review**. Monetization is unknown.",
     "\n## R1 · 'Meet the Clay family' (≈35 s) · Green Screen / Duet / Remix\n**Premise:** the series' family, made easy to follow, with the real history in two sentences.",
     "| Timeline | Visual | Iman says | Line type | Claim(s) | On-screen text |\n|---|---|---|---|---|---|"]
L += [f"| {r['t']} | {r['visual']} | {r['line']} | {r['kind']} | {', '.join(r['claims']) or '—'} | {r['text']} |" for r in R1]
L += ["\n**Labels rule:** put an actor label over the trailer **only** when that character is identifiable from the trailer's own context. Otherwise keep the label on your talking shot (\"Dana Gourrier plays Odessa\"). Never identify anyone by facial resemblance alone.",
      "**Delivery:** warm and conversational. Slow down slightly for 'He died last year, in 2025.' Pronunciation: Odessa = oh-DESS-uh; Rahaman = rah-HAH-mahn (**confirm**); Gourrier = **unverified**, so avoid saying it until confirmed, or use the on-screen text only.",
      "\n## R2 · 'Why authorized matters' (≈28 s) · Cut / Stitch / Remix",
      "| Timeline | Visual | Iman says | Line type | Claim(s) | On-screen text |\n|---|---|---|---|---|---|"]
L += [f"| {r['t']} | {r['visual']} | {r['line']} | {r['kind']} | {', '.join(r['claims']) or '—'} | {r['text']} |" for r in R2]
L += ["\n**Pick your stance for 0:12–0:24** (proposed, not your words until you approve them):"] + [f"- {s}" for s in STANCES]
L += ["\n## Packaging (provisional)", "### R1 hooks"] + [f"- **{k}:** {v}" for k, v in HOOKS1.items()] + \
     ["Recommended: curiosity-led. It's specific, credit-true, and doesn't depend on any particular trailer frame.", "Cover headline: `Meet the Clays`", "\n### R2 hooks"] + \
     [f"- **{k}:** {v}" for k, v in HOOKS2.items()] + ["Recommended: curiosity-led. Cover headline: `'Authorized' Ali`"]
for name, caps in (("R1", CAPS1), ("R2", CAPS2)):
    L.append(f"\n### {name} captions")
    L += [f"**{p}**\n```\n{c}\n```" for p, c in caps.items()]
L += ["\n## Accuracy and sensitivity review",
      "| Item | Flags | Context | Content note | Resources | History | Platform concerns | Status |\n|---|---|---|---|---|---|---|---|",
      "| R1 | Death of a real person (2025) | Stated factually | None | n/a | CLM-000010, 000014, 000023 supported | Remix availability | **Ready for your review** |",
      "| R2 | None | 'Authorized' attributed to Prime Video | None | n/a | Production claims supported | Monetization may be limited | **Needs your stance** |",
      "\n**Disclosures:** if you record with your own voice and face, no AI label is needed. If your digital presenter or voice is used, add 'AI presenter based on my likeness' and turn on the platform AI label. Always: 'Not affiliated with Prime Video'.",
      f"\n## Tracking\nLog each live post in `analytics/TIC_Performance_Tracker_TEMPLATE.csv`, with the packaging ID and the hook used. Files: none to render. These are recorded in-app, so the deliverables are this kit, `{pre}_POST_COPY` (above) and `{pre}_SOURCES` (claims listed)."]
write(ROOT / "projects" / f"{P}_TrailerRemix" / f"{pre}_REMIX_KIT.md", "\n".join(L) + "\n")
print("wrote", P)

# The Iman Cut: Bird Clay pilot proposal (v0.1, November 8, 2026)

Status: **ready for your review, not for publication.** The voice track, subtitles, identity confirmation and clearance are still open.

## 1. Deliverables in this package
| Item | File |
|---|---|
| Review video, vertical (Reels / TikTok / Shorts) | `previews/IMAN-CUT_bird-clay-pilot_9x16_review_v0.1.mp4` (1:13, −14 LUFS) |
| Review video, horizontal (YouTube) | `previews/IMAN-CUT_bird-clay-pilot_16x9_review_v0.1.mp4` |
| Watermark motion tests | `previews/watermark-motion-test-9x16.mp4`, `…16x9.mp4` |
| Cover, draft | `cover/IMAN-CUT_bird-clay-pilot_cover_9x16_DRAFT_v0.1.png`, crop check: `cover/cover-crop-check.jpg` |
| Watermark audit images | `watermark/` |
| Footage index (real timestamps) | `index/footage-index.md`, `index/R2-shot-cuts.txt` |
| Research and credits (claim-level citations) | `research/sources-and-characters.md` |
| Rebuild script (configurable layout, variant and watermark position) | `build_pilot.sh` |

## 2. Watermark verification
- **Text:** all three files read exactly THE IMAN CUT, with a red slash through IMAN.
- **The Iman Cut Editorial Logo.png:** ❌ **not usable as a watermark.** It has no transparency: it's a 1254×1254 image on a solid black square, so it would burn a black box into the footage. It's fine as a profile avatar or end card.
- **editorial watermark-1.png and Serif Watermark-2.png:** ✅ real transparency. The lettering is opaque (alpha 253–254), and the edges are anti-aliased in matching cream, so there are no dark halos and no glow. The two files are almost identical (they differ in about 3,100 pixels, mostly around the slash). **Please say which one is the master.**
- **Padding:** ⚠️ both files are 1536×1024, and about 70–75% of that is empty. The lettering only fills 220 px in from the sides, 180 px from the top and 110 px from the bottom. I made `watermark/iman-cut-watermark-trimmed-PROPOSED.png` by cropping to the lettering plus 12 px. That's a crop only, with no redesign. **I need your approval to make it the working asset.**
- **Readability at small size:**
  - On dark footage, ✅ clear.
  - On light footage (a cream wall), ⚠️ low contrast: THE and CUT stay readable but faint.
  - On busy footage, ⚠️ it's readable but sits over a head in the cropped vertical layout.
  - At watermark size (190–230 px wide), the red slash is a hairline. It survives on dark footage and nearly disappears on light footage.
- **Option for light scenes:** a soft drop shadow. This is a render treatment, the asset itself is unchanged, and it needs your approval. See `watermark/test-9x16-light-SHADOW-option-zoom.jpg`.

## 3. Placement and size
- **Top-right in both layouts:**
  - 16:9: 190 px wide, 77 px from the right, 43 px from the top.
  - 9:16: 230 px wide, 64 px from the right, 250 px from the top, which keeps it below the top band where the TikTok/Reels interface sits.
  - You can change this per project in `build_pilot.sh` (`WMW`, `WMX`, `WMY`).
- **Vertical layout:** I recommend the **framed layout** (Option B): the full 16:9 picture centered on a dark background.
  - A center crop of this footage cut through faces and put the watermark on top of heads.
  - The framed layout keeps the watermark on the dark band, clear of faces, action and the series' own graphics.
  - Downside: at phone size the picture is small, about a quarter of the screen height. **Decision needed: framed layout, or a 1.3× zoom-crop?**
- **Interface check** (approximate TikTok/Reels zones):
  - The watermark stays clear of the top bar.
  - The right-hand button column overlaps the right ~14% of the picture band. Nothing essential is there in this cut, but check it per scene.
  - Captions belong above the bottom 360 px.

## 4. The edit
All source times are from **R2** (Screen Recording 2026-11-08 at 11.44.17 AM).
| Pilot time | Source | Content | Audio |
|---|---|---|---|
| 0:00–0:10 | R2 3:48.4–3:58.7 | Ring → hands clasped → man at the radio → announcer: "The winner by unanimous decision… Cassius Clay" | Original |
| 0:07–0:15 | card | **Narration 1** (context) | Your voice, pending |
| 0:15–0:29 | R2 3:58.7–4:12.8 | Decision in the ring → the home erupts → a woman in the kitchen | Original |
| 0:29–0:39 | card | **Narration 2** (the performance) | Your voice, pending |
| 0:39–0:56 | R2 4:12.8–4:29.5 | **The embrace: 16.7 s held uncut** (the meaningful pause) | Original |
| 0:56–1:04 | card | **Narration 3** (close) | Your voice, pending |
| 1:04–1:07 | R2 4:29.5–4:32.5 | Medal podium | Original |
| 1:07–1:10 | end card | THE IMAN CUT logo | Silent |

The narration sits on its own cards and never plays over the show's dialogue, so the original dialogue and pauses stay intact. I've checked the cuts against a Whisper transcript (`index/transcript-R2/`). v0.1 had started in the middle of "The winner by unanimous decision", so I moved the opening cut back to the shot boundary at 3:48.4. No other cut lands mid-line. **The transcript is a machine draft with errors** ("Cassius play" for "Cassius Clay", "Dolph medal" for "gold medal"), so subtitles need a corrected pass before Publish. The dialogue never says "Bird" or "Odessa", so it doesn't settle B1.

## 5. Script: your voice vs. my suggestions
> **Rule:** nothing below is your opinion until you write or approve it. ✍️ = your words needed. 💡 = my suggestion, for you to accept, edit or reject.

**Narration 1, context (~8 s)**
- 💡 Factual suggestion: "Rome, 1960. An eighteen-year-old Cassius Clay is fighting for Olympic gold, and back home in Louisville, the show puts his family around the radio."
- Sources: H8 for the bout. The radio scene is the series' staging (§ Series vs. history), which is why the line says "the show puts".

**Narration 2, the performance (~10 s)**
- ✍️ **Your reaction:** in a sentence or two, what do you see Dana Gourrier doing in this scene?
- 💡 A proposed reading to react to (it's mine, not yours): "Watch how the scene holds back from her: we see the room before we see Bird, so when the camera finally finds her, the release lands harder."
- This reading depends on confirming that the woman at 4:10–4:20 is Bird. See blocker B1.

**Narration 3, close (~8 s)**
- ✍️ Your closing thought.
- 💡 Factual option: "Odessa Clay lived until 1994 and appeared as herself in *When We Were Kings*." (H6, H7)

## 6. Caption and hashtags (draft)
> **Caption, draft:** The win happens in Rome. The show lets you feel it in a Louisville living room. ✍️[your one-line take]. *The Greatest* (Prime Video): Dana Gourrier as Odessa "Bird" Clay. Commentary by The Iman Cut.
>
> **Hashtags:** #TheGreatest #MuhammadAli #PrimeVideo #DanaGourrier #TVCommentary #FilmAnalysis #TheImanCut
>
> **Handle:** pending. I won't invent it.

## 7. Cover
- The cover is designed separately from the video frames. The background comes from R2 4:19, darkened at the bottom.
- The headline, face and brand mark all sit inside the **central 1:1 crop** and the 3:4 grid crop (see `cover/cover-crop-check.jpg`).
- The logo is centered, not top-right, as you specified.
- The headline line is a placeholder.

## 8. Experiment order: recommended substitutions
The footage on hand is **one 4:52 sequence (R2)** plus a making-of documentary (R3). Experiments 2–4 would all have to reuse R2, which would make the batch mostly overlapping excerpts. My recommendation:
- **Pilot:** as planned (R2, home-reaction sequence).
- **#2 Bird, performance-led:** needs **a different Bird scene from another episode**. Blocked on footage.
- **#3 Ali standout scene:** possible from R2 (the bout itself, about 0:25–3:15, which barely overlaps the pilot). It's the best candidate to do next.
- **#4 Rudy Clay spotlight:** blocked. I haven't identified Rudy in R2 from context yet; the transcript may help.
- **Substitute candidate:** a "how they built Ali" piece from R3 (training, acting coach, the Louisville visit). It's a different source, so there's no overlap. Clearance is separate, and R3 contains third-party archival photos.

## 9. Production preset (draft; it gets locked as v1.0 only after you approve)
`preset-v0.1.json`. I'll fill it in once you've made the decisions in §10.

## 10. Decisions I need from you
1. **Master watermark file:** "editorial watermark-1" or "Serif Watermark-2". And do you approve the padding-trimmed version?
2. **Vertical layout:** framed (recommended) or 1.3× zoom-crop?
3. **Drop shadow on light scenes:** yes or no?
4. **Narration 2 and 3:** your own reaction lines, or edits to my 💡 suggestions.
5. **Cover headline.**

## 11. Remaining blockers
| # | Blocker | Why it matters | My recommendation |
|---|---|---|---|
| B1 | **Which on-screen woman is Bird.** Three different women appear in R2: one in black against a dark wall (0:10–0:25), one in the kitchen in a house dress (4:02 and 4:10), and one wearing pearls in the embrace (4:16–4:20). From context alone I can't tell whether these are one performer in different scenes or different characters. | The pilot's narration and cover both depend on it | Most likely the woman in the embrace (4:16–4:20), because the scene is the family home during the broadcast. The evidence is weak. I'll check the transcript for names like "Bird" or "Odessa"; otherwise one line from you confirming it settles it |
| B2 | **Voice track** | Narrations 1–3 are placeholders | Your recorded narration, or an approved voice service (a paid one needs a cost estimate first). No clone will be made |
| B3 | **Footage for experiments #2, #4, #5 and #6** | R2 alone would make the batch overlap | Recordings of other episodes, taken from your legitimate access |
| B4 | **Publication clearance** | Not done | Commentary use of short excerpts may qualify as fair use, but that isn't guaranteed. Two things are open: Prime Video's terms on screen recording, and the third-party archival photos in R3. **I'm not marking this cleared** |
| B5 | **Instagram handle** | Needed for the caption and end card | Send me the exact spelling |
| B6 | **Primary sources** for H2 and H5 (the Olympic date is now confirmed: September 5, 1960, H8) | Narration accuracy | I'll look for Olympic records and the AP obituary text. Eig's book only if you can give me legitimate access |

# CLAUDE.md: The Iman Cut

Standing instructions for every Claude session that opens this repo (Mac or cloud). Read this first. Details live in the linked files.

## Who and what
- **Brand:** The Iman Cut. **Creator:** Iman Yael. Film, character, performance and history commentary.
- **First project:** Prime Video's *The Greatest* (2026, Muhammad Ali; IMDb tt15715850).
- **Handles (reported, verify before @-mentioning):** Instagram `theimancut` · TikTok `@beeiman` · YouTube `@ImanYael`.

## Session routine
1. **Start:** `git pull` (fast-forward) from `main`.
2. **Finish:** commit and **push to `main`**. Use only the `main` branch; never create branches.
3. Don't change the same files as another active session. The main editing chat is **"File and folder organization"** (Claude Code on Iman's Mac). Cloud sessions handle research and docs.

## Brand rules (decided; don't re-ask)
- Watermark text: exactly **THE IMAN CUT**, never "The Yael Cut". Asset: `brand/watermark/iman-cut-watermark-trimmed.png`, 230 px wide, 64 px from the right edge, 250 px from the top on 1080×1920.
- Watermark **ON** for TikTok and Snapchat; **OFF** for Instagram (Iman, 2026-11-09) and all YouTube (Shorts and landscape).
- Vertical layout is **option B (fit-blurred)**: the whole frame, no crop, centred on a blurred, darkened copy of itself (270×480 boxblur 12:2, brightness −0.10, saturation 0.85). No black bars, no stretching.
- Sizes: 1080×1920 for IG, TikTok, Snapchat and YouTube Shorts; 1920×1080 for YouTube landscape.
- Current cuts: **original scene audio only**. No narration cards, placeholders, added music, or generated voices unless Iman asks.

## Rights (hard rules)
- Footage licence requested from Amazon MGM Media Licensing (clipstill@mgm.com): **pending** (RGT-000001). Until it's granted, **screen recordings are review-only**, never published.
- **Never** bypass DRM or HDCP, use pirated sites, or download platform videos for re-upload.
- In-app remixes (YouTube Remix, TikTok Stitch/Duet, Instagram/Facebook Remix) are separate versions. Propose one only after confirming that specific official source offers remix on that platform.
- Music is cleared separately from footage. **Never transcribe song lyrics**: mark them `♪ [music]` and flag the track for Iman.
- Nothing is published, scheduled, bought or sent without Iman's explicit approval.

## Accuracy rules
- **Actor ≠ character ≠ historical person.** Credit only actors confirmed as visible in the finished cut. Never identify anyone by face alone; use credits, dialogue and scene context. Identity labels: Confirmed / Probable / Unresolved.
- Use exact credited names from the IMDb paste, e.g. **"Cassius Clay Sr."** (not "Cash"), **"Odessa 'Bird' Clay"**.
- "Young Cassius" (Elias Leacock) is a *proposed* younger portrayal of CHR-000001, pending the episode credits.
- **"Connie lesson"**: unresolved (Sonny Liston or Sonny Banks). Do not resolve it without Iman.
- Never invent timestamps, quotes, appearances or history. Interpretation is labelled as interpretation; history needs a supported claim (`catalog`, CLM records).
- Subtitles are machine drafts until Iman approves them. Nothing is burned in before that.

## Where things are
| What | Where |
|---|---|
| Decisions, brief, task board, handoff | `PROJECT_BRIEF.md`, `DECISION_LOG.md`, `TASK_BOARD.md`, `HANDOFF.md` |
| Latest open questions for Iman | `projects/REVIEW_PACKET_2026-11-09.md` |
| Cast and character sheets (generated) | `works/WRK-000001_the-greatest/` (135+ characters, IDs `CHR-000001`…) |
| Catalog (source of truth) | `catalog/catalog.sqlite`; regenerate docs with `python3 -m tic.cli docs`, tests with `python3 -m unittest tests.test_core tests.test_search_and_takes` |
| Film & TV library (all full-length sources) | `~/Movies/The Iman Cut/Sources/`: the one folder the Clipper lists (from 2026-11-08 on) and the auto-export's `IMPORTS` points to. Random screen recordings stay out of it |
| Clipper (split long videos into clips) | `tools/clipper/`; start with `Start Clipper.command`; output in `~/Movies/The Iman Cut/Clips/` |
| Desktop auto-export | `tools/autoexport/` (install: `bash tools/autoexport/install.sh`) → `~/Movies/The Iman Cut/Export/the-greatest/` (Desktop shortcut `theimancut`; background helpers can't read the Desktop) |
| Desktop folders | `IMPORTS/` (shortcut to `~/Movies/The Iman Cut/Sources`; never exported; `_SOURCE_MAP.md` lists them, UNVERIFIED until matched to official uploads) · `_drop-finished-clips-here/` · `instagram/ tiktok/ snapchat/ youtube/` · `_subtitles-to-review/` · `_subtitles-approved/` · `_originals/` |
| Bird Clay cut (Mac) | `projects/PRJ-000001_BirdClay/local_cut/` (edit list, subtitles, render scripts; no video in git) |
| Trailer remix kit | `projects/PRJ-000002_TrailerRemix/` |
| Policies | `policies/` (sensitivity, moderation, corrections, QC checklist) |

## Covers and quote carousels
- For every finished clip, use the existing `tools/autoexport/tic_cover.py` workflow and apply [the thumbnail selection and review rules](docs/THUMBNAIL_WORKFLOW.md).
- When finished clips are available, update the clip-derived knowledge base and prepare platform carousel packages using [the quote carousel workflow](carousels/README.md). Start with Bird Clay. Use the existing catalog IDs and verify every real-life quote before export. Write reviewed clip and quote JSON into the carousel workspace (`~/Movies/The Iman Cut/Export/the-greatest/carousels/`, copies in `carousels/knowledge-base/`) documented there. The Mac auto-export agent renders the platform packages and records missing evidence.

## Repo hygiene
- No video, audio or images from the show in git (`.gitignore`). Brand assets are the exception.
- Large media stays on the Mac, referenced by checksum.
- Commit messages end with the session's attribution lines.

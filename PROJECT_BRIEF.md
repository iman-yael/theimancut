# PROJECT_BRIEF: The Iman Cut

> **Current rules are summarised in `CLAUDE.md`. Latest status: `HANDOFF.md`.** Where this brief and the update table at the bottom disagree, the update table wins.

*Single consolidated brief. Updated 2026-11-08. Supersedes `legacy/v0_the-greatest/README.md`.*

## Identity (definitive)
| | |
|---|---|
| Brand / series | **The Iman Cut** (ordinary text) |
| Watermark (exact) | **THE IMAN CUT**. Never "The Yael Cut". |
| Creator | Iman Yael · credit line "By Iman Yael" |
| Positioning | Film, character, performance and history through Iman's perspective |
| Optional intro | "I'm Iman Yael, and this is The Iman Cut." Only in the channel intro or longer pieces, never as a preamble to every short. |
| Channel handles | IG `theimancut` · TikTok `@beeiman` · YouTube `@ImanYael` (reported by Iman; verify before @-mentions) |
| Founder content | Later and gradual, labelled "Building with Iman". One relevant CTA at most. |

## Audience and editorial voice
- People who just watched a title and want to understand the performances, characters and history.
- The voice is human, confident, observant and conversational. Interpretation is framed as interpretation ("The scene suggests…"); history appears only when it is sourced.
- Iman's opinions about footage are **proposed for approval**, never invented as hers.

## First project: *The Greatest* (WRK-000001, IMDb tt15715850)
8-episode limited series, Prime Video, released 2026-11-04. The catalog holds 135 characters, 161 people and 136 portrayals from the pasted IMDb credits (ING-000002), plus the v0 legacy IDs (ING-000001), identity-relevant crew and stunt doubles (ING-000003), and your typed mappings (ING-000004, all matched, no duplicates).

**Priority characters:** CHR-000003 Bird · CHR-000004 Rudy · CHR-000001 Cassius/Ali · CHR-000002 Cash Sr. · CHR-000005 Sonny Liston · CHR-000006 Geraldine Liston.
**Pilot:** PRJ-000001 Bird Clay character portrait. Status **Proposed**.
**Experiment batch v1:** 10 concept records (CON) for 6 edits, 3 narrated breakdowns and 1 channel intro. See `projects/EXPERIMENT_BATCH_v1.md`.

## Assets and tools (audited 2026-11-08)
| Item | Status |
|---|---|
| Episode footage | **None.** The Prime desktop download is not reachable from this cloud session, and it is DRM-protected in any case (see below). |
| Rights documentation | None (RGT-000001…000005 Unknown) |
| Transcripts/subtitles | None |
| Actor headshots | **None.** The IMDb paste had no images; IMDb returns 403 to automated access. |
| Voice / digital presenter | None supplied (VOC-000001 `not_supplied`). No substitute voice will be used. |
| Analytics | No integration. Tracking template only; **no monitoring active**. |
| Tools available | ffmpeg 6.1 (libx264, AAC, zscale/tonemap, libass), Python 3 + SQLite 3.53, web search. No speech-to-text installed yet. |
| Network | www.imdb.com and m.media-amazon.com added to the environment allowlist (approved), but IMDb blocks automated requests (403). |

## Output settings (house defaults; re-check the actual upload method before delivery)
- 9:16 1080×1920 for IG Reels / TikTok / FB Reels / YT Shorts; optional 4:5 1080×1350 for IG/FB feed.
- MP4, H.264 High, CRF 16 capped at 20 Mbps; AAC 256 kbps 48 kHz; −14 LUFS; 30 fps CFR (frame duplication, never interpolation) plus a source-frame-rate master; SDR Rec.709 with hable tone-mapping for PQ/HLG.
- Layouts: crop / `fit` (blurred canvas) / `split`. No stretching.
- Text layers: dialogue subtitles (white bold) · narration subtitles (warm italic) · editorial text (upper third) · ID labels (top-left) · **THE IMAN CUT** watermark (A top-right or B top-centre: **your choice pending**).
- Files: `TIC_PRJ-######_Slug_Format_PLAT_WxH_EN_v##` + `_CLEAN.mp4`, `_SUBTITLES.srt`, `_VO.wav`, `_COVER.jpg`, `_POST_COPY.md`, `_SOURCES.md`.

## Budget
**Not set.** Current spend $0. Nothing will be bought (voice service, stock, transcription credits) without your approval.

## Conflicts found across your instructions, and how they are handled
| # | Conflict | Current handling | Needs you? |
|---|---|---|---|
| 1 | Filenames: `TG_S01E##_SC###…` (brief 1) vs `TG_S01_MULTI_CHAR###…` (brief 2) vs `TIC_PRJ-000001_…` (brand brief) | Latest brand rule `TIC_PRJ-…`; exact sources live in the manifest | No |
| 2 | Character IDs `CHR-001` (v0) vs `CHR-000001` | Six-digit IDs; v0 IDs kept as redirects (`external_id` provider `tic-v0`) | No |
| 3 | `.srt` vs `_SUBTITLES.srt` | `_SUBTITLES.srt` | No |
| 4 | "Clean export" content: no subtitles only, or also no labels/watermark? | Clean = no burned subtitles; ID labels and watermark kept | **Yes** |
| 5 | "No third-party watermark" vs a brand watermark | Not a real conflict: only the THE IMAN CUT mark, and it never implies ownership or affiliation | No |
| 6 | Narrated vs. performance-led first render | **Decided:** original scene audio only for now; optional commentary is drafted separately | No |

## Unresolved questions
1. "Connie lesson": possible matches CHR-000005 Sonny Liston or CHR-000084 Sonny Banks. **Awaiting your confirmation.**
2. 19 other review-queue items from the IMDb import (`docs/generated/REVIEW_QUEUE.md`), e.g. whether "Young Cassius" is the young Cassius Jr. (recommended) or Sr.
3. Betty Shabazz (CHR-000028) / Cesili Williams: only your mapping and IMDb support this credit.
4. Watermark placement A or B; the clean-export definition; the budget; channel handles.
5. Cover watermark: at y=250 it is cropped out of the 1:1 profile-grid preview and sits at the edge of 3:4. Keep it (the headline survives all crops), or move it to the centre band on covers only?

## Update: merged from the local Mac session (see `docs/LOCAL_SESSION_HANDOFF_2026-11-08.md`)
| Topic | Decision (Iman, via local session) | Supersedes |
|---|---|---|
| Watermark placement | **A: top-right**, small; master PNG asset on the Mac | "A or B pending" |
| Watermark by platform | ON for IG/TikTok vertical; **OFF for all YouTube** (Shorts and landscape) | "Watermark on all" |
| Vertical layout | No crop: full frame over a blurred, darkened copy (`fit`) | crop default |
| Narration | Not for now: original audio only, no cards, music or generated voice | narrated recommended |
| Handles | IG `theimancut`, TikTok `@beeiman`, YouTube `@ImanYael` (reported; verify before @-mentions) | "not supplied" |
| Experiment order | Bird pilot → Bird scene → Ali standout → Rudy → contrast → themed montage | EXPERIMENT_BATCH_v1 order |

**Still blocking publication:** the Mac cuts come from a screen recording of a promo. Footage rights are Unknown, and the cast identity of everyone except Cassius is Unresolved.

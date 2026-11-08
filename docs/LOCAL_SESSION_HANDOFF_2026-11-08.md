# Handoff from the local Mac session ("File and folder organization"), 2026-11-08

> Merged into this project at Iman's request. **Reported state.** The files live on Iman's Mac under `~/Projects/personal/iman-cut/` and have **not** been seen or checked by the cloud session. Items marked ⚠️ are flagged by the cloud session.

## Decisions Iman made in that session
- **Watermark:** exact text `THE IMAN CUT`, small, **top-right** (placement A). Master asset: `watermark/iman-cut-watermark-trimmed-PROPOSED.png`, a crop-only trim of the transparent "editorial watermark-1". "The Iman Cut Editorial Logo.png" has no transparency and is **not** usable as a watermark.
- **Watermark ON** for Instagram and TikTok verticals. **OFF for all YouTube uploads** (landscape and Shorts).
- **Vertical layout:** no cropping. The whole 16:9 frame is scaled to 1080 wide and centred on a blurred, darkened copy of itself (layout "B" there = `fit` here). No black bars, no stretching.
- **For now:** scene clips with original audio only. No narration cards, placeholders, added music, or generated voices.
- **Handles (reported):** Instagram `instagram.com/theimancut` · TikTok `@beeiman` · YouTube `@ImanYael`. ⚠️ The cloud session hasn't verified them; confirm before using them in captions.
- No paid spending. Nothing published or uploaded.

## Source used there (measured on the Mac)
- `Screen Recording 2026-11-08 at 11.44.17 AM.mov`: a macOS **screen recording** of an official promo/extended clip of *The Greatest* (ends on the "New series Nov 4" card and the Prime logo). 1966×1106 (active 1962×1106), H.264 ~18.3 Mbps, VFR ~32.6 fps container with ~24 unique fps, 4:52, SDR BT.709. Not the studio original.
- `5:min clip.mov`: the same promo at a lower bitrate.
- The 11.51 recording / `15minMAclip.mov`: the *Becoming the Greatest* making-of documentary, which contains **third-party archival Ali photos** (separate rights).
- ⚠️ **Rights:** a screen recording of a promotional video is not an authorized editing source, and posting from it is not permitted by default. The local session lists clearance as **not done**. These cuts stay **review-only**: do not publish until permission is documented (see `policies/EDITORIAL_SENSITIVITY_MODERATION.md`). The in-app remix route (PRJ-000002) remains the cleared-by-design option.

## Bird Clay cut (on the Mac, `iman-cut/v03/`)
- **Edit:** source 3:48.35–4:06.12 + 4:09.75–4:46.20 (opponent and ring cutaways removed). 54.2 s, 23.976 fps CFR, H.264 CRF 16, AAC 48 kHz, −14 LUFS.
- **Content:** opens on the announcer, "The winner, by unanimous decision… Cassius Clay", then the reaction at home, the uncut embrace and the medal ceremony; ends on Cassius looking up with the medal.
- **Files:**
  - `TIC_BirdClay_Vertical_1080x1920_v05.mp4` (IG/TikTok; watermark, subtitles)
  - `TIC_BirdClay_YouTubeShorts_1080x1920_v05.mp4` (no watermark)
  - `TIC_BirdClay_YouTube_1920x1080_v04.mp4` (no watermark)
  - CLEAN versions (vertical v05, landscape v03)
  - `TIC_BirdClay_v03.srt`, `EDIT-LIST_v03.md`, `SOURCE-QUALITY-REPORT.md`, `RIGHTS-AND-CREDITS_v03.md`, `POST-DESCRIPTION_v03.md`, `cast_labels.json`, `render_v03.py`, `make_subs.py`, `edl_v03.json`
- **Subtitles:** 3 cues. "Congratulations, congratulations" is low-confidence and needs Iman's ear. The ceremony announcement (~0:43–0:53) is deliberately not subtitled, because two Whisper models disagree.
- ⚠️ **Scene-integrity note:** removing the cutaways joins two source ranges. Check that the reaction still responds to the same announcement it follows in the source (it should, per the edit list).

## Open items reported
1. **Cast identity:** only Jaalen Best as Cassius Clay is strongly supported (press, and the announcer names Cassius Clay). The man at the radio (Cash / Omari Hardwick?) and the woman in pearls (Bird / Dana Gourrier?) are **Unresolved**; no face-based identification. The kitchen woman, announcer, referee and the Pietrzykowski actor are unknown. Labels burn in only when `confirmed=true`.
   - Catalog note: IMDb credits list **Michael Simpson as Zbigniew 'Ziggy' Pietrzykowski** (2 credited episodes) and Alexandre Cadieux as the Olympic Referee. These are **candidates only**; not confirmed on screen.
2. **Music** not verified by ear; cue M-01 unresolved. The series score is by Stanley A. Smith (also in the IMDb paste). "Gladiator" (Wyclef Jean & Kofi Black) is not heard in this cut.
3. **Episode:** likely S1E1 "Fool's Gold". Unconfirmed for this promo; the title is also unconfirmed in the catalog.
4. **Commentary:** opinion lines in the post description are left for Iman. With no commentary in the cut, the fair-use position is weak until narration or analysis is added.
5. **Clearance:** not done; Prime Video's terms on screen capture are unresolved.

## Facts reported with citations there
- Rome 1960 light-heavyweight final, 5 September 1960: Clay beat Zbigniew Pietrzykowski 5–0 (Olympics.com, Olympedia). *Logged as a claim to add to the catalog on the next research intake.*
- Odessa Grady Clay, 1917–1994. Her marriage year (1933/1934) and occupation conflict across sources.

## Tooling there
- "Clipper", a local web app (`iman-cut/clipper/`, start with `Start Clipper.command`, http://127.0.0.1:8765). It splits a long video at shot cuts that fall in audio pauses, renders 9:16 (no-crop blurred background by default; face-tracked crop opt-in) and 16:9, and has a gallery. Tested: the promo produced 8 clips.

## Agreed experiment order (local session)
1. Narrated Bird Clay pilot
2. Bird performance scene
3. Ali standout
4. Rudy spotlight
5. Contrasting character
6. Themed montage (needs footage from other episodes)

The cloud session's EXPERIMENT_BATCH_v1 covers the same ground. Where they differ, this order (Iman's) wins.

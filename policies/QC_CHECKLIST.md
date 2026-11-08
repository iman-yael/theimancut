# Final QC Checklist (per video, per platform)

A video is **READY** only when every box is ticked and signed. It is **POSTED** only after you explicitly authorize posting. Nothing is published automatically.

**File:** ______________________ **Reviewer:** ______ **Date:** ______

## A. Automated (`Edit_Projects/pipeline/qc_probe.sh FILE [SRT]`)
- [ ] All PASS: dimensions, H.264, yuv420p, Rec.709 tags, constant fps, AAC 48 kHz, audio bitrate, loudness about -14 LUFS, SRT free of placeholders, ≤ 2 lines per event
- [ ] Frame grid (`*_QC_FRAMES.jpg`) inspected for softness, banding, blocking, crop errors

## B. Human: watch the whole export with sound
- [ ] Watched start to finish, on a phone and on headphones
- [ ] Dialogue intelligible; music sits under dialogue; music cleared for this platform and use
- [ ] Motion: no 24→30 judder that distracts on pans or punches (if it does, try the SRCFPS master on platforms that accept it, or re-time the cut)
- [ ] Color/skin tones natural; HDR sources tone-mapped without clipped highlights or washed blacks
- [ ] No stretching, no artificial sharpening, no fake 60 fps, no "4K" claim on upscaled material
- [ ] Meaningful pauses and reactions preserved

## C. Framing and overlays
- [ ] Faces, reactions, and essential action visible in every shot (layout per shot: crop / fit / split)
- [ ] Previewed each platform's **real draft/preview screen** (upload as draft, private, or "only me"; do not publish). Captions, labels, and faces clear of buttons, the handle, caption text, and progress bars on **IG, TT, FB, YT** separately.
- [ ] Cover: main face and headline central; checked in each app's feed and profile grid (approximations in `Covers/*_PREVIEW-1x1/3x4/4x5.jpg`)

## D. Accuracy and ethics
- [ ] Subtitles match the audio word for word; names spelled correctly; `[?]` markers resolved
- [ ] Actor/character credits are V2 or better (VC preferred); historical names checked
- [ ] Edit preserves meaning; no line attributed to the wrong speaker; context card present where needed
- [ ] Dramatized vs. documented clearly distinguished; contested claims labelled as such
- [ ] Domestic violence / racism: content note present; not used as the hook; not sensationalized
- [ ] Spoiler label correct
- [ ] AI-presenter disclosure on screen and spoken (presenter videos only)

## E. Copy and delivery
- [ ] Post captions, hook, cover headline, and hashtags describe **this** export (same scene, same names)
- [ ] Hashtags checked in-app for meaning; 3–5 used
- [ ] No placeholder text anywhere (video, SRT, cover, copy)
- [ ] Current upload specs re-checked for the actual upload method (app, Creator Studio/Business Suite, YouTube Studio, scheduler/API limits on duration, size, cover format)
- [ ] Permission status = CLEARED in the manifest, with document ref; no unresolved factual issue
- [ ] Manifest updated: approval_status, qc_status = HUMAN_PASS

**Unresolved issues (must be empty for READY):** __________________________

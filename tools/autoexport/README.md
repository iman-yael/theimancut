# Auto-export: Desktop folders for The Greatest

Drop a finished clip into a Desktop folder, and platform-ready versions appear automatically in **option B** (`B_fit-blurred`): the whole frame, no crop, centred over a blurred, darkened copy of itself. No black bars, no stretching.

## One-time install (on your Mac, from this repo folder)
```bash
brew install ffmpeg        # skip if already installed
bash tools/autoexport/install.sh
```
If macOS asks whether this may access your Desktop, click **Allow**.

## Folders it creates
```
~/Desktop/theimancut/the-greatest/
  IMPORTS → ~/Movies/The Iman Cut/Sources   ← shortcut to the shared Film & TV library (also what the Clipper lists); never auto-exported
  _drop-finished-clips-here/   ← put finished clips here (+ optional same-name .srt)
  instagram/   NAME_IG_1080x1920.mp4          9:16 · THE IMAN CUT watermark
  tiktok/      NAME_TT_1080x1920.mp4          9:16 · watermark
  snapchat/    NAME_SC_1080x1920.mp4          9:16 · watermark
  youtube/     NAME_YT-Shorts_1080x1920.mp4   9:16 · no watermark (YouTube adds its own branding)
               NAME_YT_1920x1080.mp4          16:9 · no watermark
  _originals/  sources move here after a successful export
  _subtitles-to-review/  NAME.DRAFT.srt + NAME.REVIEW.md (machine draft, never burned in)
  _subtitles-approved/   put your corrected NAME.srt here → *_CAPTIONED.mp4 versions are made
  IMPORTS/_SOURCE_MAP.md  inventory of raw recordings to match to official uploads (UNVERIFIED until filled in)
  _export-log.txt · _export-manifest.csv · Export Now.command · READ ME.txt
```

## Subtitles (draft → your review → captioned)
1. Once per Mac: `pip3 install -U openai-whisper`. It runs locally; nothing is uploaded.
2. Each finished clip gets `_subtitles-to-review/NAME.DRAFT.srt` and `NAME.REVIEW.md`. Flagged lines start with `[?]`: uncertain wording, cast and character names to check against the IMDb list, capitalised words, very short cues. **Songs are never transcribed.** They appear as `♪ [music]` and are flagged so you can identify the track and check its rights.
3. Fix the wording and timing, remove every `[?]`, and save the file as `NAME.srt` in `_subtitles-approved/`. Files that still contain `[?]` are refused.
4. Captioned versions (`…_CAPTIONED.mp4`) are rendered from the original. The clean exports stay untouched.

## Encoding
- **Video:** H.264 High, CRF 16 (max 20 Mbps), Rec.709, faststart. Uses the **same detection as Clipper**: black bars are trimmed (cropdetect on a mid-clip sample), and the output frame rate comes from how many frames actually change, so a film-cadence screen recording stays 23.976 and nothing is interpolated.
- **Matches Clipper and Bird Clay v05:** the option B background (270×480 blur, −10% brightness, 85% saturation), 1080×1920 / 1920×1080, and the watermark (230 px, 64 px from the right, 250 px from the top). One intentional difference: audio is 256 kbps, as your brief asks, where Clipper uses 192.
- **Audio:** AAC 256 kbps, 48 kHz, normalised to −14 LUFS.
- **Watermark:** the approved PNG, 230 px wide, 64 px from the right edge, 250 px from the top. These are the v05 settings.

## Notes
- **IMPORTS:** a shortcut to `~/Movies/The Iman Cut/Sources`, the one Film & TV library shared with the Clipper (set `TIC_SOURCES` to use another folder). Put full-length sources there, cut clips from them with the Clipper (saved to `~/Movies/The Iman Cut/Clips`), then drop the finished clips you choose into the drop folder. Recordings in IMPORTS are not cleared for posting by being there; log their source and permission first.
- **Trigger:** the agent runs when the drop folder changes, and every 60 s as a backstop. It waits until a file has stopped growing, so half-copied exports are skipped until complete. It never overwrites an existing export.
- **Snapchat watermark:** on by default. To turn it off, run with `TIC_SNAP_WATERMARK=0`.
- **Nothing is uploaded or posted.** Every export is logged with rights status `UNKNOWN-check-before-posting`.
- **If nothing happens:** double-click `Export Now.command`, then check `~/Library/Application Support/theimancut/agent.log`.
- **To stop:** `bash tools/autoexport/uninstall.sh`. Your folders and clips are left alone.

**Testing:** run end to end on Linux with synthetic clips (16:9 with subtitles, and a silent vertical clip). The macOS-specific parts (the launchd agent, the Desktop permission prompt, notifications) have **not** been tested on a Mac.

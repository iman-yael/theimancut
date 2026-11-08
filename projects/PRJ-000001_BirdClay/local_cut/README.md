# Bird Clay cut (made on Iman's Mac): review only

**Status:** review only. Nothing is published, and clearance is not done (see [RIGHTS-AND-CREDITS_v03.md](RIGHTS-AND-CREDITS_v03.md)). The source is a screen recording of an official promo, and **no video is stored in this repo.**

## What's here
| File | What it is |
|---|---|
| [EDIT-LIST_v03.md](EDIT-LIST_v03.md) | Every shot with source and output timestamps, and why the 3.6-second cutaway section was removed |
| [SOURCE-QUALITY-REPORT.md](SOURCE-QUALITY-REPORT.md) | Measured source specs (screen recording, film-rate content) and the export settings |
| [RIGHTS-AND-CREDITS_v03.md](RIGHTS-AND-CREDITS_v03.md) | Rights summary, featured cast (with verification status), people mentioned, music cue sheet, third-party assets |
| [POST-DESCRIPTION_v03.md](POST-DESCRIPTION_v03.md) | Post description draft from Iman's template; her opinion lines are left blank |
| `edl_v03.json` | The edit decision list the renderer reads |
| `lines_verified.json` → `TIC_BirdClay_v03.srt` | Subtitle lines with the basis for each one (one line is low-confidence) |
| `cast_labels.json` | On-screen "Name / as Character" labels. A label is burned in **only** when its `confirmed` is `true` |
| `render_v03.py`, `make_subs.py` | Rebuild every deliverable in a single encode pass straight from the source |
| `history/` | The superseded v0.1 pilot proposal, with narration cards and a draft preset |

## Rebuild
```bash
export BIRDCLAY_SOURCE="/path/to/Screen Recording 2026-11-08 at 11.44.17 AM.mov"   # not in the repo
python3 -E make_subs.py
python3 -E render_v03.py vertical publish            # TIC_BirdClay_Vertical_1080x1920_v05.mp4 (IG/TikTok, watermark)
python3 -E render_v03.py vertical publish --shorts   # TIC_BirdClay_YouTubeShorts_1080x1920_v05.mp4 (no watermark)
python3 -E render_v03.py landscape publish           # TIC_BirdClay_YouTube_1920x1080_v04.mp4 (no watermark)
python3 -E render_v03.py vertical clean              # no subtitles, labels or watermark
python3 -E render_v03.py landscape clean
```
- **ffmpeg:** needs libx264 and libass. Homebrew's `ffmpeg` works, or `python3 -m pip install --user imageio-ffmpeg`.
- **Rendered `.mp4` files are ignored by git.**

## Decisions encoded here
- **Vertical:** no cropping. The whole frame is shown at 1080 wide on a blurred, darkened copy of itself; subtitles sit below the picture.
- **Watermark:** `THE IMAN CUT`, top-right, on IG/TikTok verticals only; never on YouTube or Shorts.
- **Original audio only.** Audio is cut only where the edit actually skips source time, with 12 ms fades there. Loudness is −14 LUFS.
- **Frame rate:** 23.976 fps constant, which matches the source's real cadence.

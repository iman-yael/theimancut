# Source Acquisition: Viewing Copy vs. Editing Source

## A. Your personal viewing download (Prime Video app)

These steps come from third-party guides found by web search. I have not tested them in the app, and menu names vary by device and app version.

1. Open the official **Prime Video app** on a device that supports downloads (phone, tablet, or the Windows/Mac app where available; browsers do not offer downloads).
2. Go to **My Stuff → Settings (gear) → Stream & Download** (some versions say "Streaming & Downloading").
3. Tap **Download Quality** and choose **Best**. The other options are usually Better, Good, Data Saver, and *Always Ask*.
4. Optional: turn on *Download on Wi-Fi only*.
5. Download episodes from the series page.

What "Best" does **not** guarantee:
- It is the highest tier the app offers on **your** device for **that** title. It is not a promise of 1080p, 4K, or HDR, and sources disagree on file sizes, which suggests it varies.
- Downloads are **DRM-protected** and play only inside the app. They are not editable files.
- **A download, however good, is not an editing source or a publishing permission.** I won't help extract, decrypt, screen-record, or otherwise work around protection.

Use the viewing copy to **watch, take notes, and log candidate timestamps** in `Scene_Index/`. Those notes become the shopping list for the authorized request below.

## B. The editing source (only with permission to publish)

Request from the rights holder (Amazon MGM Studios / the series' publicity or licensing contact), or use an expressly cleared press asset. Ask for:

| Item | Ask for |
|---|---|
| Format | Unencrypted ProRes 422 HQ (preferred) or high-bitrate H.264/H.265 mezzanine |
| Picture | Native resolution and frame rate (expected 23.976). Specify SDR Rec.709, or HDR plus an SDR trim if available. |
| Audio | Stereo mix at 48 kHz. Ideally separate dialogue/music/effects stems, so music can be removed if it isn't cleared for social use. |
| Coverage | Episode + timecode ranges from your scene log, with 2–3 s handles |
| Paperwork | Written licence naming: platforms (IG, TT, FB, YT), uses (clips, AI-presenter commentary, covers), duration, territory, credit line, music restrictions, and approval requirements |
| Delivery | Direct download or drive link. **No** messaging apps, social re-downloads, or screen captures. |

Log every asset in `Source_Reports/TG_Rights_Log_TEMPLATE.csv`. `render.sh` refuses to run without `-p CLEARED:<rights-log ID>`.

Press clips and trailers are **not** assumed cleared just because they're promotional.

## C. On arrival

1. Run `Edit_Projects/pipeline/source_report.sh <file>`. This writes `Source_Reports/<file>_SOURCE_REPORT.md` with resolution, codec, frame rate/VFR, bitrate, color, HDR, audio channels, a SHA-256 checksum, and the crop budget.
2. Store the original read-only (`chmod a-w`) and never re-save over it. Re-check the checksum before final export.
3. Edit from the original or a ProRes intermediate. Proxies are for playback speed only; relink to the original before export (`render.sh` always reads the source you pass it).
4. One encode per deliverable. Clean platform copies are byte-identical copies, not re-encodes.
5. Never upscale-and-relabel. A 1920×1080 source cropped to 9:16 keeps about 608×1080 px (scaled 1.78× to fill 1080×1920). If it looks soft, use the `fit` or `split` layout instead of forcing a tight crop.

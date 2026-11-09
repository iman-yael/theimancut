# The Iman Cut: Clipper

A local web app that turns a long video into draft clips you can browse, play and download. It runs only on your Mac, at http://127.0.0.1:8765, and nothing is uploaded to the internet.

## Start it
Double-click **`Start Clipper.command`**. The first time, macOS may ask to let Terminal access your Desktop, Documents or Downloads; allow it so the app can list those videos. The browser opens automatically.

## Use it
1. Choose a video in one of three ways:
   - drop it onto the page,
   - paste its path (for example `~/Desktop/long video.mov`), or
   - pick it from the list of videos in Desktop, Movies, Documents, Downloads and earlier uploads. Each video shows its length.
2. Set options:
   - **Show** and **Episode** (for example `The Greatest`, `S01E01`). They go into every file name
   - clip length: minimum and maximum seconds (default 8–30)
   - vertical 9:16 and/or landscape 16:9
   - vertical shows the **whole picture on a blurred background**; tick "Crop vertical to fill" only if you want face-tracked cropping
   - THE IMAN CUT watermark on vertical (off by default; YouTube adds its own branding)
   - transcription (on by default; it names clips by what's said, and is a machine draft)
   - high-quality encoding
3. Press **Make clips**. Runs wait in line and are made **one at a time**, so they don't slow each other down. You can cancel a run.
   - The progress bar shows each step live: finding shot cuts, finding pauses, transcribing, then rendering each clip.
   - The clip list appears as soon as the cuts are found. Each card shows its thumbnail, then a progress bar while it renders, then a player.
   - Refreshing the page keeps your place (the run is in the address), and a video you're playing is never reset.
   - Switch between 9:16 and 16:9 at any time.
4. Every clip shows its length. To change what a clip's name says it shows, edit the box on its card and press **Rename**; its files are renamed to match.

## Where the clips go
Finished clips are saved to **`~/Movies/The Iman Cut/Clips/<Show - Episode - date>/`**, already under their final names. **Open in Finder** on a run opens that folder. Removing a run from the list keeps the clips.

Output is high quality by default (H.264 CRF 17). Tick *Draft quality* for faster previews.

## File names
`<show>_<episode>_clipNNN_<seconds>s_<what-happens>_<9x16|16x9>.mp4`, for example
`the-greatest_s01e01_clip004_9s_winner-unanimous-decision-cassius-clay_9x16.mp4`.

*What happens* comes from the clip's dialogue when transcription is on. Otherwise it comes from macOS scene recognition plus a face count (close-up / two people / group). These are machine guesses, so rename anything that's off.

## How it decides clips
1. Finds every shot cut.
2. Finds pauses in the audio.
3. Makes **as many clips as possible**: each clip ends at the first shot cut after the minimum length that falls in a pause, so dialogue isn't chopped. If none falls in a pause, it uses the first cut after the minimum.
4. For vertical, resizes the whole frame onto a blurred copy of itself (no cropping). If you turn on cropping, it frames each shot on the largest face, or the most eye-catching area, or the center.
5. Converts screen recordings to their real frame rate, which removes duplicate frames.

## Limits
- These are **drafts**. Check the crops, cuts and any transcript before posting.
- In crop mode, vertical crops from 1080p-ish sources are upscaled, so they're a little soft.
- Title cards and logos at the end of the source (for example a network end card) can end up inside the last clip.
- It doesn't check music, rights or who is on screen. That's what the rights log and credits steps are for.

Files: `jobs/<run>/clipNNN_9x16.mp4`, `clipNNN_16x9.mp4`, `clipNNN.jpg`, `job.json`.

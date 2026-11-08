# The Iman Cut: Clipper

A local web app that turns a long video into draft clips you can browse, play and download. It runs only on your Mac, at http://127.0.0.1:8765, and nothing is uploaded to the internet.

## Start it
Double-click **`Start Clipper.command`**. The first time, macOS may ask to let Terminal access your Desktop, Documents or Downloads; allow it so the app can list those videos. The browser opens automatically.

## Use it
1. Choose a video in one of three ways:
   - drop it onto the page,
   - paste its path (for example `~/Desktop/long video.mov`), or
   - pick it from the list of videos in Desktop, Movies, Documents, Downloads and earlier uploads.
2. Set options:
   - clip length (minimum and maximum seconds)
   - vertical 9:16 and/or landscape 16:9
   - vertical shows the **whole picture on a blurred background**; tick "Crop vertical to fill" only if you want face-tracked cropping
   - THE IMAN CUT watermark on vertical (off by default; YouTube adds its own branding)
   - transcription (slower, and a machine draft)
   - high-quality encoding
3. Press **Make clips**. Each clip appears in the gallery as soon as it's rendered, and you can switch between 9:16 and 16:9.

## How it decides clips
1. Finds every shot cut.
2. Finds pauses in the audio.
3. Groups shots into clips of your target length, ending each clip at a cut that falls in a pause, so dialogue isn't chopped.
4. For vertical, resizes the whole frame onto a blurred copy of itself (no cropping). If you turn on cropping, it frames each shot on the largest face, or the most eye-catching area, or the center.
5. Converts screen recordings to their real frame rate, which removes duplicate frames.

## Limits
- These are **drafts**. Check the crops, cuts and any transcript before posting.
- In crop mode, vertical crops from 1080p-ish sources are upscaled, so they're a little soft.
- Title cards and logos at the end of the source (for example a network end card) can end up inside the last clip.
- It doesn't check music, rights or who is on screen. That's what the rights log and credits steps are for.

Files: `jobs/<run>/clipNNN_9x16.mp4`, `clipNNN_16x9.mp4`, `clipNNN.jpg`, `job.json`.

#!/bin/bash
# One-time setup on your Mac:  bash tools/autoexport/install.sh   (run from the theimancut repo folder)
# Creates ~/Desktop/theimancut/the-greatest/{instagram,tiktok,youtube,snapchat,_drop-finished-clips-here,_originals,_subtitles-to-review,_subtitles-approved}
# plus IMPORTS as a shortcut to the shared Film & TV library (~/Movies/The Iman Cut/Sources),
# and a background agent that exports anything dropped into _drop-finished-clips-here (option B layout).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$(cd "$HERE/../.." && pwd)"
APP="$HOME/Library/Application Support/theimancut"
SHOW="$HOME/Desktop/theimancut/the-greatest"
PLIST="$HOME/Library/LaunchAgents/com.theimancut.autoexport.plist"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
command -v ffmpeg >/dev/null || { echo "ffmpeg is missing. Install it first:  brew install ffmpeg"; exit 1; }
mkdir -p "$APP" "$SHOW"/{_covers,instagram,tiktok,youtube,snapchat,_drop-finished-clips-here,_originals,_subtitles-to-review,_subtitles-approved} "$HOME/Library/LaunchAgents"
# IMPORTS is a shortcut to the shared Film & TV library, the same folder the Clipper lists
# (default ~/Movies/The Iman Cut/Sources; override with TIC_SOURCES). Anything already in a real IMPORTS folder moves there.
SOURCES="${TIC_SOURCES:-$HOME/Movies/The Iman Cut/Sources}"
mkdir -p "$SOURCES"
if [[ -d "$SHOW/IMPORTS" && ! -L "$SHOW/IMPORTS" ]]; then
  find "$SHOW/IMPORTS" -mindepth 1 -maxdepth 1 -exec mv -n {} "$SOURCES/" \;
  rmdir "$SHOW/IMPORTS" 2>/dev/null || { echo "IMPORTS still has files that clash with names in $SOURCES; left in place."; }
fi
[[ -e "$SHOW/IMPORTS" ]] || ln -s "$SOURCES" "$SHOW/IMPORTS"
cp "$HERE/tic_autoexport.sh" "$HERE/tic_subdraft.py" "$HERE/tic_cover.py" "$HERE/tic_carousel.py" "$HERE/characters.json" "$HERE/cast_names.txt" "$APP/"; chmod +x "$APP/tic_autoexport.sh"
# covers: on-device face/eye/saliency helper (macOS Vision) + Pillow for drawing
command -v swiftc >/dev/null && swiftc -O "$HERE/ticvision.swift" -o "$APP/ticvision" 2>/dev/null || echo "Note: couldn't build the cover helper (needs Xcode command line tools); covers will be flagged for review."
# Keep Pillow separate from Homebrew's managed Python packages.
command -v python3 >/dev/null || { echo "Python 3 is required. Install it first: brew install python"; exit 1; }
if [[ ! -x "$APP/.render-venv/bin/python3" ]]; then
  python3 -m venv "$APP/.render-venv"
fi
"$APP/.render-venv/bin/python3" -c "import PIL" 2>/dev/null ||
  "$APP/.render-venv/bin/python3" -m pip install -q Pillow
cp "$REPO/brand/watermark/iman-cut-watermark-trimmed.png" "$APP/"
cp "$HERE/Export Now.command" "$SHOW/"; chmod +x "$SHOW/Export Now.command"
cat > "$SHOW/READ ME.txt" <<TXT
THE IMAN CUT: The Greatest exports
0. IMPORTS = shortcut to your Film & TV library (Movies/The Iman Cut/Sources), shared with the Clipper. Full-length sources only; nothing here is exported automatically.
1. Drop a finished clip (and optionally a same-named .srt) into _drop-finished-clips-here
2. Within a minute it appears in instagram / tiktok / snapchat (1080x1920, watermark)
   and youtube (Shorts 1080x1920 + landscape 1920x1080, no watermark).
3. Draft subtitles appear in _subtitles-to-review (NAME.DRAFT.srt + NAME.REVIEW.md). Fix them, remove [?] markers, save as NAME.srt in _subtitles-approved → captioned versions (_CAPTIONED) are made.
4. The original moves to _originals. Progress: _export-log.txt. List of exports: _export-manifest.csv
5. Quote carousels and their review status appear under carousels/. See carousels/README.md in the repo for source inputs.
Nothing is uploaded or posted. Check rights and cast labels before posting.
If nothing happens, double-click "Export Now.command".
TXT
sed -e "s#__SCRIPT__#$APP/tic_autoexport.sh#" -e "s#__DROP__#$SHOW/_drop-finished-clips-here#" -e "s#__APP__#$APP#" "$HERE/com.theimancut.autoexport.plist" > "$PLIST"
launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed. Folders: $SHOW"
echo "Test: drop a clip into _drop-finished-clips-here. If macOS asks for access to the Desktop, click Allow."

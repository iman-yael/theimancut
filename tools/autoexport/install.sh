#!/bin/bash
# One-time setup on your Mac:  bash tools/autoexport/install.sh   (run from the theimancut repo folder)
# Creates ~/Desktop/theimancut/the-greatest/{IMPORTS,instagram,tiktok,youtube,snapchat,_drop-finished-clips-here,_originals}
# and a background agent that exports anything dropped into _drop-finished-clips-here (option B layout).
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$(cd "$HERE/../.." && pwd)"
APP="$HOME/Library/Application Support/theimancut"
SHOW="$HOME/Desktop/theimancut/the-greatest"
PLIST="$HOME/Library/LaunchAgents/com.theimancut.autoexport.plist"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
command -v ffmpeg >/dev/null || { echo "ffmpeg is missing. Install it first:  brew install ffmpeg"; exit 1; }
mkdir -p "$APP" "$SHOW"/{IMPORTS,instagram,tiktok,youtube,snapchat,_drop-finished-clips-here,_originals} "$HOME/Library/LaunchAgents"
cp "$HERE/tic_autoexport.sh" "$APP/"; chmod +x "$APP/tic_autoexport.sh"
cp "$REPO/brand/watermark/iman-cut-watermark-trimmed.png" "$APP/"
cp "$HERE/Export Now.command" "$SHOW/"; chmod +x "$SHOW/Export Now.command"
cat > "$SHOW/READ ME.txt" <<TXT
THE IMAN CUT: The Greatest exports
0. IMPORTS = raw screen recordings / source files (storage only; nothing here is exported automatically).
1. Drop a finished clip (and optionally a same-named .srt) into _drop-finished-clips-here
2. Within a minute it appears in instagram / tiktok / snapchat (1080x1920, watermark)
   and youtube (Shorts 1080x1920 + landscape 1920x1080, no watermark).
3. The original moves to _originals. Progress: _export-log.txt. List of exports: _export-manifest.csv
Nothing is uploaded or posted. Check rights and cast labels before posting.
If nothing happens, double-click "Export Now.command".
TXT
sed -e "s#__SCRIPT__#$APP/tic_autoexport.sh#" -e "s#__DROP__#$SHOW/_drop-finished-clips-here#" -e "s#__APP__#$APP#" "$HERE/com.theimancut.autoexport.plist" > "$PLIST"
launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed. Folders: $SHOW"
echo "Test: drop a clip into _drop-finished-clips-here. If macOS asks for access to the Desktop, click Allow."

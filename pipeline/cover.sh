#!/usr/bin/env bash
# 1080x1920 cover master + crop previews (center 1:1, 3:4, 4:5) for feed/profile-grid checks.
# Usage: cover.sh SOURCE TIME "Headline text" BASENAME [XCENTER=0.5]
# Headline: ≤2 lines, ≤20 chars/line; put a real line break in the text to wrap.
# The headline sits in the central band so it survives the square/3:4/4:5 center crops.
# Crop previews are approximations of grid/feed crops — confirm in each app before delivery.
set -euo pipefail
SRC=$1; T=$2; HEAD=$3; BASE=$4; X=${5:-0.5}
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; OD="$ROOT/projects/_renders/covers"; mkdir -p "$OD"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT; printf '%s' "$HEAD" > "$TMP/h.txt"
TRC=$(ffprobe -v error -select_streams v:0 -show_entries stream=color_transfer -of default=nw=1:nk=1 "$SRC")
PRE=""; [[ "$TRC" == smpte2084 || "$TRC" == arib-std-b67 ]] && PRE="zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,"
ffmpeg -v error -y -ss "$T" -i "$SRC" -frames:v 1 -vf "${PRE}crop=w=trunc(ih*9/32)*2:h=ih:x=max(0\,min(iw-ih*9/16\,iw*$X-ih*9/32)):y=0,scale=1080:1920:flags=lanczos,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile=$TMP/h.txt:fontsize=68:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=24:x=(w-text_w)/2:y=1080,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text=THE IMAN CUT:fontsize=30:fontcolor=white@0.78:shadowcolor=black@0.55:shadowx=2:shadowy=2:x=w-text_w-70:y=250" -q:v 2 "$OD/${BASE}_COVER.jpg"
for r in "1x1:1080:1080" "3x4:1080:1440" "4x5:1080:1350"; do IFS=: read -r n w h <<<"$r"
  ffmpeg -v error -y -i "$OD/${BASE}_COVER.jpg" -vf "crop=$w:$h:(iw-$w)/2:(ih-$h)/2,scale=360:-2" "$OD/${BASE}_COVER_PREVIEW-${n}.jpg"; done
echo "$OD/${BASE}_COVER.jpg"

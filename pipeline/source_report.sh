#!/usr/bin/env bash
# Source-quality report. Reads only; never modifies the original.
# Usage: source_report.sh SOURCE_FILE [OUT_DIR]   (default OUT_DIR = Source_Reports next to this repo)
set -euo pipefail
SRC="$1"; ROOT="$(cd "$(dirname "$0")/.." && pwd)"; OUTDIR="${2:-$ROOT/media/source_reports}"
B="$(basename "${SRC%.*}")"; R="$OUTDIR/${B}_SOURCE_REPORT.md"
v(){ ffprobe -v error -select_streams v:0 -show_entries stream="$1" -of default=nw=1:nk=1 "$SRC" | head -1; }
W=$(v width); H=$(v height); RFR=$(v r_frame_rate); AFR=$(v avg_frame_rate)
TRC=$(v color_transfer); PRI=$(v color_primaries); SPC=$(v color_space)
HDR="SDR (no HDR transfer tagged)"; case "$TRC" in smpte2084) HDR="HDR10/PQ — tone-map required";; arib-std-b67) HDR="HLG — tone-map required";; esac
[[ "$PRI" == "unknown" || -z "$PRI" ]] && HDR="$HDR; WARNING color primaries untagged — confirm with rights holder"
VFR="CFR (r_frame_rate = avg_frame_rate)"; [[ "$RFR" != "$AFR" ]] && VFR="POSSIBLE VFR (r=$RFR avg=$AFR) — inspect"
CROPW=$(( H*9/16 )); CROP45=$(( H*4/5 ))
{
echo "# Source-quality report: $(basename "$SRC")"
echo "Generated $(date -u +%FT%TZ) by source_report.sh (ffprobe). Values are measured from the file, not assumed."
echo; echo "| Property | Value |"; echo "|---|---|"
echo "| SHA-256 (original, unchanged) | \`$(sha256sum "$SRC" | cut -d' ' -f1)\` |"
echo "| Container / size | $(ffprobe -v error -show_entries format=format_long_name -of default=nw=1:nk=1 "$SRC") / $(du -h "$SRC" | cut -f1) |"
echo "| Duration (s) | $(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$SRC") |"
echo "| Resolution | ${W}×${H} (SAR $(v sample_aspect_ratio)) |"
echo "| Video codec / profile | $(v codec_name) / $(v profile) |"
echo "| Pixel format / bit depth | $(v pix_fmt) |"
echo "| Frame rate | $RFR — $VFR |"
echo "| Video bitrate | $(v bit_rate) bps (overall $(ffprobe -v error -show_entries format=bit_rate -of default=nw=1:nk=1 "$SRC") bps) |"
echo "| Color primaries / transfer / matrix / range | $PRI / $TRC / $SPC / $(v color_range) |"
echo "| HDR status | $HDR |"
echo "| Field order | $(v field_order) |"
echo "| Timecode start (file→episode offset needed) | $(ffprobe -v error -show_entries format_tags=timecode:stream_tags=timecode -of default=nw=1:nk=1 "$SRC" | head -1) |"
echo; echo "## Audio streams"; echo "| # | Codec | Channels | Layout | Sample rate | Bitrate | Language |"; echo "|---|---|---|---|---|---|---|"
ffprobe -v error -select_streams a -show_entries stream=index,codec_name,channels,channel_layout,sample_rate,bit_rate:stream_tags=language -of csv=p=0 "$SRC" | awk -F, '{print "| "$1" | "$2" | "$4" | "$5" | "$3" | "$6" | "$7" |"}'
echo; echo "## Crop budget (measured source)"
echo "- 9:16 full-height crop keeps **${CROPW}×${H}** px of ${W}×${H}, scaled to 1080×1920 (factor $(awk "BEGIN{printf \"%.2f\",1920/$H}")× — above 1.00 means upscaling; inspect softness)."
echo "- 4:5 full-height crop keeps **${CROP45}×${H}** px, scaled to 1080×1350 (factor $(awk "BEGIN{printf \"%.2f\",1350/$H}")×)."
echo "- If a 9:16 crop looks soft or drops an actor, use the \`fit\` or \`split\` layouts."
echo; echo "## Reviewer notes"; echo "- Rights doc ref: ____  ·  Received via: ____ (not a messaging app / social download)  ·  Visual check by: ____"
} > "$R"
echo "$R"

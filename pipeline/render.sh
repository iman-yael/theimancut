#!/usr/bin/env bash
# Platform renderer for AUTHORIZED footage only. Reproducible edit instructions: every export's
# exact command is logged next to it. Originals are only read, never modified.
#
# Usage:
#   render.sh -s SOURCE -i IN -o OUT -b BASE -p PERMISSION [-l LAYOUT] [-c CAPTIONS.srt]
#             [-a "Actor Name" -n "Character Name" [-t LABEL_SECONDS]] [-N NARRATION.srt] [-w A|B|none] [-v v01] [-f] [-T]
#   BASE       TIC_PRJ-000001_CharacterSlug_Format   (platform/size/lang/version are appended)
#   -N         narration subtitles (rendered in a distinct italic warm style; dialogue SRT stays white bold)
#   -w         THE IMAN CUT watermark placement: A = top-right (default), B = top-centre, none
#   PERMISSION must start with "CLEARED:" plus the rights-log asset ID, e.g. CLEARED:RL-004.
#              -T (test mode) skips the check and is ONLY for synthetic test material.
#   LAYOUT     x=0.50 (9:16 crop centred at 50% of width) | fit (whole frame on a restrained
#              blurred canvas) | split:0.30:0.70 (two stacked panels, crop centres at 30%/70%)
#   IN/OUT     file timecodes. Caption times in the SRT are RELATIVE TO IN.
#   -f         also make 4:5 1080x1350 feed adaptations for IG and FB
#
# Outputs (projects/_renders/BASE/):
#   BASE_MASTER-SRCFPS_1080x1920_EN_vNN.mp4   clean, source frame rate (archive/re-edit master)
#   BASE_{IG,TT,FB,YT}_1080x1920_EN_vNN.mp4   burned subtitles + ID labels, 30 fps
#   ..._CLEAN.mp4                             no burned subtitles (ID labels kept) — for
#                                             platform-native captions; one encode, copied per platform
#   Subtitles/BASE_{PLAT}_..._vNN_SUBTITLES.srt sidecar subtitles (dialogue + narration merged), same basename
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LAYOUT="x=0.50"; SRT=""; NSRT=""; WM="A"; ACTOR=""; CHAR=""; LSEC=4; VER=v01; FEED=0; TEST=0; PERM=""
while getopts "s:i:o:b:p:l:c:N:w:a:n:t:v:fT" o; do case $o in
  s) SRC=$OPTARG;; i) IN=$OPTARG;; o) OUT=$OPTARG;; b) BASE=$OPTARG;; p) PERM=$OPTARG;;
  l) LAYOUT=$OPTARG;; c) SRT=$OPTARG;; N) NSRT=$OPTARG;; w) WM=$OPTARG;; a) ACTOR=$OPTARG;; n) CHAR=$OPTARG;; t) LSEC=$OPTARG;;
  v) VER=$OPTARG;; f) FEED=1;; T) TEST=1;; *) exit 2;; esac; done
if [[ $TEST -eq 0 && "$PERM" != CLEARED:* ]]; then
  echo "ABORT: footage permission not cleared (-p CLEARED:<rights-log ID> required)." >&2; exit 3; fi
[[ $TEST -eq 1 ]] && PERM="TEST-SYNTHETIC-ONLY"
OD="$ROOT/projects/_renders/$BASE"; SD="$OD"; mkdir -p "$OD" "$SD"
LOG="$OD/${BASE}_EXPORT_LOG_${VER}.txt"; : > "$LOG"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
[[ -n "$SRT" ]] && cp "$SRT" "$TMP/subs.srt"
[[ -n "$NSRT" ]] && cp "$NSRT" "$TMP/narr.srt"
printf "THE IMAN CUT" > "$TMP/wm.txt"
printf '%s' "$ACTOR" > "$TMP/actor.txt"; printf 'as %s' "$CHAR" > "$TMP/char.txt"

# --- HDR → SDR Rec.709 tone-map (only if the source is tagged PQ/HLG) ---
TRC=$(ffprobe -v error -select_streams v:0 -show_entries stream=color_transfer -of default=nw=1:nk=1 "$SRC")
PRE=""
if [[ "$TRC" == smpte2084 || "$TRC" == arib-std-b67 ]]; then
  PRE="zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,"
  echo "HDR source ($TRC): tone-mapped to SDR Rec.709 (hable). Inspect skin tones and highlights." | tee -a "$LOG"
fi

# layout W H → filtergraph from [0:v] to [base]
layout() { local W=$1 H=$2 A
  A=$(awk "BEGIN{print $W/$H}")
  case "$LAYOUT" in
    x=*) local X=${LAYOUT#x=}
      echo "[0:v]${PRE}crop=w=trunc(ih*$A/2)*2:h=ih:x=max(0\,min(iw-ih*$A\,iw*$X-ih*$A/2)):y=0,scale=$W:$H:flags=lanczos[base]";;
    fit)
      echo "[0:v]${PRE}split[a][b];[a]scale=$W:$H:force_original_aspect_ratio=increase,crop=$W:$H,gblur=sigma=40,eq=brightness=-0.22:saturation=0.6[bg];[b]scale=$W:-2:flags=lanczos[fg];[bg][fg]overlay=0:(H-h)/2[base]";;
    split:*) IFS=: read -r _ X1 X2 <<<"$LAYOUT"; local PH=$((H/2)) PA
      PA=$(awk "BEGIN{print $W/($H/2)}")
      echo "[0:v]${PRE}split[a][b];[a]crop=w=trunc(ih*$PA/2)*2:h=ih:x=max(0\,min(iw-ih*$PA\,iw*$X1-ih*$PA/2)):y=0,scale=$W:$PH:flags=lanczos[t];[b]crop=w=trunc(ih*$PA/2)*2:h=ih:x=max(0\,min(iw-ih*$PA\,iw*$X2-ih*$PA/2)):y=0,scale=$W:$PH:flags=lanczos[u];[t][u]vstack[base]";;
    *) echo "bad layout" >&2; exit 2;; esac; }

# ID label (top-left, below top UI); FONT sizes fixed for consistency
labels() { local LY=$1
  [[ -z "$ACTOR" ]] && { echo "null"; return; }
  echo "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile=$TMP/actor.txt:fontsize=50:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=14:x=80:y=$LY:enable='between(t,0.3,$LSEC)',drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:textfile=$TMP/char.txt:fontsize=40:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=12:x=80:y=$((LY+82)):enable='between(t,0.3,$LSEC)'"; }

# Per-platform subtitle margins (px on the real canvas). APPROXIMATE house defaults —
# must be confirmed in each app's draft/preview before delivery (see QC checklist).
declare -A MV=( [IG]=560 [TT]=600 [FB]=560 [YT]=520 [IG45]=150 [FB45]=150 )
declare -A MR=( [IG]=170 [TT]=190 [FB]=170 [YT]=170 [IG45]=90  [FB45]=90 )
watermark() { local W=$1 H=$2
  [[ "$WM" == none ]] && { echo "null"; return; }
  local X="w-text_w-70" Y=250; [[ $H -eq 1350 ]] && Y=60
  [[ "$WM" == B ]] && X="(w-text_w)/2"
  echo "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:textfile=$TMP/wm.txt:fontsize=30:fontcolor=white@0.78:shadowcolor=black@0.55:shadowx=2:shadowy=2:x=$X:y=$Y"; }
narr() { local W=$1 H=$2 K=$3
  [[ -z "$NSRT" || -z "$K" ]] && { echo "null"; return; }
  echo "subtitles=$TMP/narr.srt:original_size=${W}x${H}:force_style='PlayResX=$W,PlayResY=$H,FontName=DejaVu Sans,FontSize=52,Italic=1,Bold=0,PrimaryColour=&H00C9E6F2,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,Alignment=2,MarginL=120,MarginR=${MR[$K]},MarginV=${MV[$K]},WrapStyle=0'"; }
subs() { local W=$1 H=$2 K=$3
  [[ -z "$SRT" ]] && { echo "null"; return; }
  echo "subtitles=$TMP/subs.srt:original_size=${W}x${H}:force_style='PlayResX=$W,PlayResY=$H,FontName=DejaVu Sans,FontSize=56,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=4,Shadow=0,Alignment=2,MarginL=120,MarginR=${MR[$K]},MarginV=${MV[$K]},WrapStyle=0'"; }

VENC=(-c:v libx264 -preset slow -profile:v high -level:v 4.2 -crf 16 -maxrate 20M -bufsize 40M
      -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv
      -fps_mode cfr -movflags +faststart)
AENC=(-af "loudnorm=I=-14:TP=-1.5:LRA=11" -ac 2 -ar 48000 -c:a aac -b:a 256k)

enc() { # out W H fpsfilter labelY subsKey
  local OUTF=$1 W=$2 H=$3 FPS=$4 LY=$5 K=$6
  local G="$(layout "$W" "$H");[base]$FPS,$(labels "$LY"),$(watermark "$W" "$H"),$( [[ -n "$K" ]] && subs "$W" "$H" "$K" || echo null),$(narr "$W" "$H" "$K"),setsar=1,format=yuv420p[v]"
  local GOP=60; [[ "$FPS" == "null" ]] && GOP=48
  local CMD=(ffmpeg -v error -y -ss "$IN" -to "$OUT" -i "$SRC" -filter_complex "$G" -map "[v]" -map 0:a:0
             "${VENC[@]}" -g $GOP "${AENC[@]}" "$OUTF")
  printf '%q ' "${CMD[@]}" >> "$LOG"; echo >> "$LOG"
  "${CMD[@]}"
}

S="EN_${VER}"
# 1) Source-frame-rate clean master (no fps conversion)
enc "$OD/${BASE}_MASTER-SRCFPS_1080x1920_${S}.mp4" 1080 1920 null 300 ""
# 2) Shared 30 fps clean (frame duplication only — no interpolation; check 24→30 cadence judder)
enc "$TMP/clean.mp4" 1080 1920 fps=30 300 ""
for P in IG TT FB YT; do
  N="${BASE}_${P}_1080x1920_${S}"
  cp "$TMP/clean.mp4" "$OD/${N}_CLEAN.mp4"
  if [[ -n "$SRT$NSRT" ]]; then enc "$OD/${N}.mp4" 1080 1920 fps=30 300 "$P"; "$(dirname "$0")/merge_srt.py" "$SD/${N}_SUBTITLES.srt" "$SRT" "$NSRT"; fi
done
if [[ $FEED -eq 1 ]]; then
  enc "$TMP/clean45.mp4" 1080 1350 fps=30 70 ""
  for P in IG FB; do N="${BASE}_${P}_1080x1350_${S}"; cp "$TMP/clean45.mp4" "$OD/${N}_CLEAN.mp4"
    if [[ -n "$SRT$NSRT" ]]; then enc "$OD/${N}.mp4" 1080 1350 fps=30 70 "${P}45"; "$(dirname "$0")/merge_srt.py" "$SD/${N}_SUBTITLES.srt" "$SRT" "$NSRT"; fi; done
fi

# Manifest rows (status REVIEW — nothing is approved by rendering)
MAN="$ROOT/projects/_renders/RENDER_MANIFEST.csv"; [[ -f "$MAN" ]] || echo "filename,label1,label2,character_ids,source_file,source_in,source_out,permission_status,export_settings,layout,approval_status,qc_status,date" > "$MAN"
for f in "$OD"/*.mp4; do
  n=$(basename "$f"); sid=$(cut -d_ -f3 <<<"$n"); ep=$(cut -d_ -f2 <<<"$n")
  probe=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height,avg_frame_rate,bit_rate -of csv=p=0 "$f" | tr , ' ')
  echo "$n,$ep,$sid,,$(basename "$SRC"),$IN,$OUT,$PERM,\"$probe | h264 high | aac 256k 48k | bt709 | loudnorm -14\",$LAYOUT,REVIEW,NOT_CHECKED,$(date -u +%F)" >> "$MAN"
done
echo "Done → $OD"; ls -1 "$OD"

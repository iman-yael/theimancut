#!/bin/zsh
# HISTORY ONLY (v0.1 pilot with narration cards, superseded by ../render_v03.py). Paths are from the original Mac.
# Build the Bird Clay pilot rough cut from the preset.
# Usage: build_pilot.sh <layout: 9x16|16x9> <variant: review|publish|textless-branded|textless-unbranded>
set -e
FF=/Users/imanyael/Library/Python/3.9/lib/python/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1
P=${0:A:h}
LAYOUT=${1:-9x16}; VARIANT=${2:-review}
SRC=$(ls ~/Desktop/Screen\ Recording\ 2026-11-08*11.44*.mov)
WM=$P/watermark/iman-cut-watermark-trimmed-PROPOSED.png
FONT=/System/Library/Fonts/Supplemental/Arial\ Bold.ttf
SERIF=/System/Library/Fonts/NewYork.ttf
OUT=$P/previews; mkdir -p $OUT/tmp

if [[ $LAYOUT == 9x16 ]]; then W=1080 H=1920 WMW=230 WMX=64 WMY=250; FIT="scale=1080:-2,pad=1080:1920:0:(oh-ih)/2:color=0x0d0b09"
else W=1920 H=1080 WMW=190 WMX=77 WMY=43; FIT="scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:color=0x0d0b09"; fi

# Edit decision list: source in/out (seconds in R2) or narration card (duration + label)
EDL=(
  "clip 228.35 238.70"
  "card 8 NARRATION 1 — context: Rome 1960, the final"
  "clip 238.70 252.84"
  "card 10 NARRATION 2 — your read on the performance"
  "clip 252.84 269.53"
  "card 8 NARRATION 3 — close"
  "clip 269.53 272.50"
  "end 3"
)
i=0; LIST=$OUT/tmp/list.txt; : > $LIST
for e in "${EDL[@]}"; do
  set -- ${(z)e}; kind=$1; f=$OUT/tmp/seg$i.ts
  case $kind in
    clip) $FF -v error -ss $2 -to $3 -i "$SRC" -vf "$FIT,fps=30,format=yuv420p" -af "aresample=48000" -c:v libx264 -crf 18 -preset veryfast -c:a aac -b:a 192k -ar 48000 -ac 2 -y $f ;;
    card) dur=$2; shift 2; label="$*"
      print -r -- "$label" > $OUT/tmp/label$i.txt; print -r -- "(placeholder — voice track pending)" > $OUT/tmp/sub$i.txt
      if [[ $VARIANT == review ]]; then TXT="drawtext=fontfile='$FONT':textfile='$OUT/tmp/label$i.txt':fontcolor=0xF6EBD3:fontsize=$((W/30)):x=(w-tw)/2:y=(h-th)/2,drawtext=fontfile='$FONT':textfile='$OUT/tmp/sub$i.txt':fontcolor=0xF6EBD3@0.6:fontsize=$((W/40)):x=(w-tw)/2:y=(h/2)+$((W/18))"; else TXT="null"; fi
      $FF -v error -f lavfi -i "color=c=0x0d0b09:s=${W}x${H}:d=${dur}:r=30" -f lavfi -i "anullsrc=r=48000:cl=stereo" -t $dur -vf "$TXT,format=yuv420p" -c:v libx264 -crf 18 -preset veryfast -c:a aac -b:a 192k -y $f ;;
    end) $FF -v error -f lavfi -i "color=c=0x0d0b09:s=${W}x${H}:d=${2}:r=30" -f lavfi -i "anullsrc=r=48000:cl=stereo" -i $WM -t $2 -filter_complex "[2]scale=$((W*45/100)):-1[l];[0][l]overlay=(W-w)/2:(H-h)/2,format=yuv420p" -map 1:a -c:v libx264 -crf 18 -preset veryfast -c:a aac -b:a 192k -y $f ;;
  esac
  echo "file '$f'" >> $LIST; i=$((i+1))
done
NAME=$OUT/IMAN-CUT_bird-clay-pilot_${LAYOUT}_${VARIANT}_v0.1.mp4
if [[ $VARIANT == textless-unbranded ]]; then FC="[0:v]format=yuv420p[v]"; else FC="[1]scale=$WMW:-1[wm];[0:v][wm]overlay=W-w-$WMX:$WMY,format=yuv420p[v]"; fi
$FF -v error -f concat -safe 0 -i $LIST -i $WM -filter_complex "$FC" -map "[v]" -map 0:a -af "loudnorm=I=-14:TP=-1.5:LRA=11" -c:v libx264 -crf 20 -preset medium -movflags +faststart -c:a aac -b:a 192k -y $NAME
rm -rf $OUT/tmp; echo $NAME

#!/bin/bash
# The Iman Cut: automatic platform export ("option B": whole frame, no crop, on a blurred, darkened copy of itself).
#
# Drop a finished clip into   ~/Desktop/theimancut/the-greatest/_drop-finished-clips-here/
# and it is rendered to:
#   instagram/  NAME_IG_1080x1920.mp4          9:16, watermark ON
#   tiktok/     NAME_TT_1080x1920.mp4          9:16, watermark ON
#   snapchat/   NAME_SC_1080x1920.mp4          9:16, watermark ON
#   youtube/    NAME_YT-Shorts_1080x1920.mp4   9:16, NO watermark (YouTube adds its own branding)
#               NAME_YT_1920x1080.mp4          16:9, NO watermark
# If NAME.srt sits next to the clip, subtitles are burned in and the .srt is copied into every folder.
# The original moves to _originals/ when every export has succeeded. Nothing is uploaded or posted.
#
# Settings can be overridden with env vars: TIC_ROOT, TIC_FPS (e.g. 24000/1001), TIC_SNAP_WATERMARK=0.
set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
ROOT="${TIC_ROOT:-$HOME/Desktop/theimancut}"
SHOW="$ROOT/the-greatest"
DROP="$SHOW/_drop-finished-clips-here"
DONE="$SHOW/_originals"
APP="${TIC_APP:-$HOME/Library/Application Support/theimancut}"
WM="$APP/iman-cut-watermark-trimmed.png"
LOG="$SHOW/_export-log.txt"
MAN="$SHOW/_export-manifest.csv"
LOCK="$APP/.export.lock"
mkdir -p "$SHOW"/{instagram,tiktok,youtube,snapchat} "$DROP" "$DONE" "$APP"
[[ -f "$MAN" ]] || echo "date,source,output,platform,size,fps,watermark,subtitles,rights_status" > "$MAN"
log() { echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" >> "$LOG"; }

command -v ffmpeg >/dev/null || { log "ERROR: ffmpeg not found (install with: brew install ffmpeg)"; exit 1; }
# one run at a time (launchd can fire again while we render)
if ! mkdir "$LOCK" 2>/dev/null; then
  if [[ -n "$(find "$LOCK" -maxdepth 0 -mmin +120 2>/dev/null)" ]]; then rmdir "$LOCK"; mkdir "$LOCK" || exit 0; else exit 0; fi
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

pick_fps() {  # source rate snapped to the nearest standard rate (keeps film at 23.976; no interpolation)
  [[ -n "${TIC_FPS:-}" ]] && { echo "$TIC_FPS"; return; }
  local r; r=$(ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate -of default=nw=1:nk=1 "$1")
  awk -v r="$r" 'BEGIN{ split(r,a,"/"); f=(a[2]>0)?a[1]/a[2]:24; n=split("24000/1001 24 25 30000/1001 30 50 60000/1001 60",s," ");
    best=s[1]; bd=1e9; for(i=1;i<=n;i++){ split(s[i],b,"/"); v=(b[2]>0)?b[1]/b[2]:b[1]; d=(v>f)?v-f:f-v; if(d<bd){bd=d;best=s[i]} } print best }'
}

render() {  # src out W H watermark(0/1) srt fps
  local src="$1" out="$2" W="$3" H="$4" wmk="$5" srt="$6" fps="$7" bw bh tmp
  bw=$((W/4)); bh=$((H/4)); tmp="${out%.mp4}.part.mp4"
  local g="[0:v]fps=$fps,split[a][b];[a]scale=$bw:$bh:force_original_aspect_ratio=increase,crop=$bw:$bh,boxblur=12:2,eq=brightness=-0.10:saturation=0.85,scale=$W:$H[bg];"
  g+="[b]scale=$W:$H:force_original_aspect_ratio=decrease:flags=lanczos,setsar=1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2[v0]"
  local last="v0"
  if [[ -n "$srt" ]]; then
    local mv=$(( H==1920 ? 560 : 70 )) fs=$(( H==1920 ? 58 : 46 ))
    cp "$srt" "$APP/.subs.srt"
    g+=";[$last]subtitles='$APP/.subs.srt':original_size=${W}x${H}:force_style='PlayResX=$W,PlayResY=$H,FontName=Helvetica Neue,FontSize=$fs,Bold=1,Outline=4,Shadow=0,Alignment=2,MarginL=120,MarginR=120,MarginV=$mv'[vs]"; last="vs"
  fi
  local inputs=(-i "$src")
  if [[ "$wmk" == 1 && -f "$WM" ]]; then
    inputs+=(-i "$WM"); g+=";[1:v]scale=230:-1[wm];[$last][wm]overlay=W-w-64:250:format=auto[vw]"; last="vw"
  elif [[ "$wmk" == 1 ]]; then
    g+=";[$last]drawtext=text='THE IMAN CUT':fontsize=30:fontcolor=white@0.8:shadowcolor=black@0.5:shadowx=2:shadowy=2:x=w-text_w-64:y=250[vw]"; last="vw"
  fi
  g+=";[$last]format=yuv420p[vout]"
  local has_audio; has_audio=$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$src" | head -1)
  local amap=() aenc=()
  if [[ -n "$has_audio" ]]; then amap=(-map 0:a:0); aenc=(-af "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000" -c:a aac -b:a 256k -ar 48000 -ac 2); fi
  ffmpeg -nostdin -v error -y "${inputs[@]}" -filter_complex "$g" -map "[vout]" "${amap[@]}" \
    -c:v libx264 -preset medium -crf 16 -maxrate 20M -bufsize 40M -profile:v high -level 4.2 -pix_fmt yuv420p \
    -colorspace bt709 -color_primaries bt709 -color_trc bt709 -r "$fps" -fps_mode cfr "${aenc[@]}" -movflags +faststart "$tmp" \
    && mv "$tmp" "$out"
}

stable() {  # wait until the file stops growing (a copy or export may still be in progress)
  local a b; a=$(wc -c < "$1" | tr -d ' '); sleep "${TIC_SETTLE:-3}"; b=$(wc -c < "$1" | tr -d ' '); [[ "$a" == "$b" && "$a" -gt 0 ]]
}

shopt -s nullglob nocaseglob
for src in "$DROP"/*.mp4 "$DROP"/*.mov "$DROP"/*.m4v; do
  stable "$src" || { log "waiting: $(basename "$src") is still being copied"; continue; }
  name="$(basename "${src%.*}")"; srt="${src%.*}.srt"; [[ -f "$srt" ]] || srt=""
  fps="$(pick_fps "$src")"; snapwm="${TIC_SNAP_WATERMARK:-1}"
  log "start: $(basename "$src") (fps $fps, subtitles: ${srt:+yes}${srt:-no})"
  ok=1
  while IFS='|' read -r dir tag W H wmk; do
    out="$SHOW/$dir/${name}_${tag}_${W}x${H}.mp4"
    [[ -f "$out" ]] && { log "  exists, skipped: $dir/$(basename "$out")"; continue; }
    if render "$src" "$out" "$W" "$H" "$wmk" "$srt" "$fps" 2>>"$LOG"; then
      [[ -n "$srt" ]] && cp "$srt" "$SHOW/$dir/${name}_${tag}_${W}x${H}.srt"
      echo "$(date '+%F %T'),\"$(basename "$src")\",\"$dir/$(basename "$out")\",$dir,${W}x${H},$fps,$([[ $wmk == 1 ]] && echo on || echo off),$([[ -n $srt ]] && echo burned || echo none),UNKNOWN-check-before-posting" >> "$MAN"
      log "  done: $dir/$(basename "$out")"
    else
      ok=0; log "  FAILED: $dir/${name}_${tag}_${W}x${H}.mp4"; rm -f "${out%.mp4}.part.mp4"
    fi
  done <<EOF
instagram|IG|1080|1920|1
tiktok|TT|1080|1920|1
snapchat|SC|1080|1920|$snapwm
youtube|YT-Shorts|1080|1920|0
youtube|YT|1920|1080|0
EOF
  if [[ $ok == 1 ]]; then
    mv "$src" "$DONE/"; [[ -n "$srt" ]] && mv "$srt" "$DONE/"
    log "finished: $(basename "$src") → moved to _originals"
    command -v osascript >/dev/null && osascript -e "display notification \"$name exported to Instagram, TikTok, Snapchat, YouTube\" with title \"The Iman Cut\"" 2>/dev/null || true
  else
    log "kept in drop folder because an export failed: $(basename "$src")"
  fi
done
true

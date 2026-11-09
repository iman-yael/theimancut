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
RENDER_PYTHON="$APP/.render-venv/bin/python3"
[[ -x "$RENDER_PYTHON" ]] || RENDER_PYTHON=python3
LOG="$SHOW/_export-log.txt"
MAN="$SHOW/_export-manifest.csv"
LOCK="$APP/.export.lock"
REVIEW="$SHOW/_subtitles-to-review"; APPROVED="$SHOW/_subtitles-approved"
mkdir -p "$SHOW"/{instagram,tiktok,youtube,snapchat,_covers} "$DROP" "$DONE" "$APP" "$REVIEW" "$APPROVED"
# IMPORTS is a shortcut to the shared Film & TV library, the same folder the Clipper lists
# (default ~/Movies/The Iman Cut/Sources; override with TIC_SOURCES). Anything already in a real IMPORTS folder moves there.
SOURCES="${TIC_SOURCES:-$HOME/Movies/The Iman Cut/Sources}"
mkdir -p "$SOURCES"
if [[ -d "$SHOW/IMPORTS" && ! -L "$SHOW/IMPORTS" ]]; then
  find "$SHOW/IMPORTS" -mindepth 1 -maxdepth 1 -exec mv -n {} "$SOURCES/" \;
  rmdir "$SHOW/IMPORTS" 2>/dev/null || { echo "IMPORTS still has files that clash with names in $SOURCES; left in place."; }
fi
[[ -e "$SHOW/IMPORTS" ]] || ln -s "$SOURCES" "$SHOW/IMPORTS"
[[ -f "$MAN" ]] || echo "date,source,output,platform,size,fps,watermark,subtitles,rights_status" > "$MAN"
log() { echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" >> "$LOG"; }

command -v ffmpeg >/dev/null || { log "ERROR: ffmpeg not found (install with: brew install ffmpeg)"; exit 1; }
# Homebrew's standard ffmpeg has no `subtitles`/`drawtext` filters (libass/freetype), so captioned exports
# would fail. Render with an ffmpeg that has them: $TIC_FFMPEG, PATH's ffmpeg if capable, else the
# full-featured build pip's imageio-ffmpeg installs (the one the Clipper uses). ffprobe still comes from PATH.
has_subs() { "$1" -hide_banner -filters 2>/dev/null | grep -q ' subtitles '; }
FFMPEG="${TIC_FFMPEG:-ffmpeg}"
if ! has_subs "$FFMPEG"; then
  for c in "$HOME"/Library/Python/*/lib/python/site-packages/imageio_ffmpeg/binaries/ffmpeg-*; do
    if [[ -x "$c" ]] && has_subs "$c"; then FFMPEG="$c"; break; fi
  done
fi
has_subs "$FFMPEG" || log "WARNING: no ffmpeg with the subtitles filter; captioned (_CAPTIONED) exports will fail. Fix: python3 -m pip install --user imageio-ffmpeg"
# one run at a time (launchd can fire again while we render)
if ! mkdir "$LOCK" 2>/dev/null; then
  if [[ -n "$(find "$LOCK" -maxdepth 0 -mmin +120 2>/dev/null)" ]]; then rmdir "$LOCK"; mkdir "$LOCK" || exit 0; else exit 0; fi
fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

probe_source() {  # same method as Clipper: active picture (strip black bars) + real frame cadence, sampled mid-clip
  local src="$1" dur mid cd
  dur=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$src" | awk '{print int($1)}')
  mid=$(( dur > 12 ? dur/2 - 5 : 0 )); local span=$(( dur < 10 ? (dur>0?dur:1) : 10 ))
  cd=$(ffmpeg -nostdin -hide_banner -ss "$mid" -t "$span" -i "$src" -vf cropdetect=24:2:0 -an -f null - 2>&1 | grep -o 'crop=[0-9:]*' | sort | uniq -c | sort -rn | head -1 | awk '{print $2}')
  ACTIVE_CROP="${cd:-}"
  if [[ -n "${TIC_FPS:-}" ]]; then OUT_FPS="$TIC_FPS"; return; fi
  local frames; frames=$(ffmpeg -nostdin -hide_banner -ss "$mid" -t "$span" -i "$src" -vf "mpdecimate=hi=256:lo=128:frac=0.1,showinfo" -an -f null - 2>&1 | grep -c pts_time)
  OUT_FPS=$(awk -v n="$frames" -v t="$span" 'BEGIN{u=n/t; if(u>=20 && u<=25.5) print "24000/1001"; else if(u<=26.5 && u>25.5) print "25"; else if(u<=31 && u>26.5) print "30000/1001"; else if(u<20) print "24000/1001"; else print "30"}')
}
pick_fps() { probe_source "$1"; echo "$OUT_FPS"; }   # kept for callers; also sets ACTIVE_CROP

render() {  # src out W H watermark(0/1) srt fps
  local src="$1" out="$2" W="$3" H="$4" wmk="$5" srt="$6" fps="$7" bw bh tmp
  bw=$((W/4)); bh=$((H/4)); tmp="${out%.mp4}.part.mp4"
  local g="[0:v]${ACTIVE_CROP:+$ACTIVE_CROP,}fps=$fps,split[a][b];[a]scale=$bw:$bh:force_original_aspect_ratio=increase,crop=$bw:$bh,boxblur=12:2,eq=brightness=-0.10:saturation=0.85,scale=$W:$H[bg];"
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
  if [[ -n "${TITLE_PNG:-}" && -f "${TITLE_PNG:-}" ]]; then   # cover title over moving footage (frame-select-only platforms)
    local ti=$(( ${#inputs[@]} / 2 )); inputs+=(-i "$TITLE_PNG")
    g+=";[$last][$ti:v]overlay=0:0:format=auto:enable='between(t,${TITLE_A},${TITLE_B})'[vt]"; last="vt"
  fi
  g+=";[$last]format=yuv420p[vout]"
  local has_audio; has_audio=$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$src" | head -1)
  local amap=() aenc=()
  if [[ -n "$has_audio" ]]; then amap=(-map 0:a:0); aenc=(-af "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000" -c:a aac -b:a 256k -ar 48000 -ac 2); fi
  "$FFMPEG" -nostdin -v error -y "${inputs[@]}" -filter_complex "$g" -map "[vout]" "${amap[@]}" \
    -c:v libx264 -preset medium -crf 16 -maxrate 20M -bufsize 40M -profile:v high -level 4.2 -pix_fmt yuv420p \
    -colorspace bt709 -color_primaries bt709 -color_trc bt709 -r "$fps" -fps_mode cfr "${aenc[@]}" -movflags +faststart "$tmp" \
    && mv "$tmp" "$out"
}

stable() {  # wait until the file stops growing (a copy or export may still be in progress)
  local a b; a=$(wc -c < "$1" | tr -d ' '); sleep "${TIC_SETTLE:-3}"; b=$(wc -c < "$1" | tr -d ' '); [[ "$a" == "$b" && "$a" -gt 0 ]]
}

shopt -s nullglob nocaseglob

draft_subs() {  # local Whisper transcript → DRAFT .srt + REVIEW.md (never burned in automatically)
  local src="$1" name="$2" py; py="$(command -v python3)"
  if ! "$py" -c "import whisper" 2>/dev/null; then
    printf '# Subtitle review: %s\n\nNo draft made: the local transcription tool is not installed.\nInstall once in Terminal:  pip3 install -U openai-whisper\nThen drop the clip again, or write NAME.srt yourself and put it in _subtitles-approved/.\n' "$name" > "$REVIEW/$name.REVIEW.md"
    log "  subtitles: Whisper not installed, wrote instructions to _subtitles-to-review"; return
  fi
  local wd="$APP/whisper/$name"; mkdir -p "$wd"
  "$py" -m whisper "$src" --model "${TIC_WHISPER_MODEL:-small}" --language en --task transcribe --word_timestamps True \
     --output_format json --output_dir "$wd" --fp16 False >>"$LOG" 2>&1 \
  && "$py" "$APP/tic_subdraft.py" "$wd/$(basename "${src%.*}").json" "$REVIEW" "$name" "$APP/cast_names.txt" >>"$LOG" 2>&1 \
  && log "  subtitles: draft ready for review → _subtitles-to-review/$name.DRAFT.srt" \
  || log "  subtitles: transcription FAILED for $name (see log)"
}

make_covers() {  # src name transcript fps snap-watermark → covers per platform + _TITLED exports (see tic_cover.py)
  local src="$1" name="$2" text="$3" fps="$4" snapwm="$5" res j
  [[ "${TIC_COVERS:-1}" == 1 && -f "$APP/tic_cover.py" ]] || return 0
  if [[ -z "$text" ]]; then j=("$APP/whisper/$name/"*.json); [[ -f "${j[0]:-}" ]] && text="${j[0]}"; fi
  res=$("$RENDER_PYTHON" "$APP/tic_cover.py" "$src" "$name" "$SHOW" "$APP" --cast "$APP/cast_names.txt" ${text:+--text "$text"} 2>>"$LOG" | tail -1)
  log "  covers: ${res:-FAILED (see log)} → _covers/$name""_COVERS.md"
  local envf="$SHOW/_covers/$name.title.env"
  [[ -f "$envf" ]] || return 0
  (
    TITLE_SC=""; TITLE_YT_Shorts=""; TITLE_TIME=""
    # shellcheck disable=SC1090
    source "$envf"
    [[ -n "$TITLE_TIME" ]] || exit 0
    TITLE_A=$(awk -v t="$TITLE_TIME" 'BEGIN{a=t-0.6; if(a<0)a=0; printf "%.3f", a}'); TITLE_B=$(awk -v t="$TITLE_TIME" 'BEGIN{printf "%.3f", t+1.0}')
    export TITLE_A TITLE_B
    probe_source "$src"
    [[ -n "$TITLE_SC" ]] && TITLE_PNG="$TITLE_SC" render "$src" "$SHOW/snapchat/${name}_SC_1080x1920_TITLED.mp4" 1080 1920 "$snapwm" "" "$fps" 2>>"$LOG" \
      && log "  titled: snapchat/${name}_SC_1080x1920_TITLED.mp4 (title at ${TITLE_TIME}s)"
    [[ -n "$TITLE_YT_Shorts" ]] && TITLE_PNG="$TITLE_YT_Shorts" render "$src" "$SHOW/youtube/${name}_YT-Shorts_1080x1920_TITLED.mp4" 1080 1920 0 "" "$fps" 2>>"$LOG" \
      && log "  titled: youtube/${name}_YT-Shorts_1080x1920_TITLED.mp4 (title at ${TITLE_TIME}s)"
  )
  [[ "$res" == REVIEW* ]] && command -v osascript >/dev/null && osascript -e "display notification \"$name: cover needs a quick check (see _covers)\" with title \"The Iman Cut\"" 2>/dev/null
  return 0
}

captioned_from_approved() {  # NAME.srt approved by Iman → captioned versions, from the original in _originals
  local srt name src
  for srt in "$APPROVED"/*.srt; do
    name="$(basename "${srt%.srt}")"; src=""
    for e in mp4 mov m4v MP4 MOV M4V; do [[ -f "$DONE/$name.$e" ]] && src="$DONE/$name.$e" && break; done
    [[ -z "$src" ]] && { log "approved subtitles waiting: no original found for $name in _originals"; continue; }
    if grep -q '^\[?\]' "$srt"; then log "approved subtitles NOT used: $name.srt still contains [?] markers"; continue; fi
    probe_source "$src"; local fps="$OUT_FPS"; local ok=1
    while IFS='|' read -r dir tag W H wmk; do
      out="$SHOW/$dir/${name}_${tag}_${W}x${H}_CAPTIONED.mp4"; [[ -f "$out" ]] && continue
      if render "$src" "$out" "$W" "$H" "$wmk" "$srt" "$fps" 2>>"$LOG"; then
        cp "$srt" "$SHOW/$dir/${name}_${tag}_${W}x${H}.srt"
        echo "$(date '+%F %T'),\"$(basename "$src")\",\"$dir/$(basename "$out")\",$dir,${W}x${H},$fps,$([[ $wmk == 1 ]] && echo on || echo off),burned-approved,UNKNOWN-check-before-posting" >> "$MAN"
        log "  captioned: $dir/$(basename "$out")"
      else ok=0; log "  FAILED captioned: $dir/$(basename "$out")"; fi
    done <<EOT
instagram|IG|1080|1920|1
tiktok|TT|1080|1920|1
snapchat|SC|1080|1920|${TIC_SNAP_WATERMARK:-1}
youtube|YT-Shorts|1080|1920|0
youtube|YT|1920|1080|0
EOT
    [[ $ok == 1 ]] && mv "$srt" "$DONE/$name.APPROVED.srt" && log "finished captioned versions: $name"
  done
}

map_imports() {  # inventory of raw recordings in IMPORTS; matching to official uploads is filled in by hand
  local map="$SHOW/IMPORTS/_SOURCE_MAP.md" f
  [[ -f "$map" ]] || printf '# IMPORTS source map\n\nMatch each recording to its OFFICIAL upload. Leave Match = UNVERIFIED until the URL, uploader and title are confirmed on the page itself.\nKnown official releases (from press coverage): teaser, July 2026, on Prime Video'"'"'s YouTube channel · official trailer, 14 Oct 2026. "Becoming the Greatest": no official release found yet; do not use that label until a source supports it.\n\n| File | Length | Picture | fps | Recorded | SHA-256 (first 12) | Official URL | Uploader | Video title | Source in–out | Match | Notes |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n' > "$map"
  mkdir -p "$SHOW/IMPORTS/_thumbs"
  for f in "$SHOW"/IMPORTS/*.mov "$SHOW"/IMPORTS/*.mp4 "$SHOW"/IMPORTS/*.m4v; do
    local b; b="$(basename "$f")"; grep -qF "| $b |" "$map" && continue
    local d wh fr sha made
    d=$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$f" | awk '{printf "%d:%02d", $1/60, $1%60}')
    wh=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$f")
    fr=$(ffprobe -v error -select_streams v:0 -show_entries stream=avg_frame_rate -of default=nw=1:nk=1 "$f" | awk -F/ '{if($2>0) printf "%.2f",$1/$2; else print $1}')
    sha=$(shasum -a 256 "$f" 2>/dev/null || sha256sum "$f"); sha=${sha:0:12}
    made=$(date -r "$f" '+%Y-%m-%d %H:%M' 2>/dev/null)
    ffmpeg -nostdin -v error -y -ss 2 -i "$f" -frames:v 1 -vf scale=480:-2 "$SHOW/IMPORTS/_thumbs/${b%.*}_start.jpg" 2>/dev/null
    ffmpeg -nostdin -v error -y -sseof -3 -i "$f" -frames:v 1 -vf scale=480:-2 "$SHOW/IMPORTS/_thumbs/${b%.*}_end.jpg" 2>/dev/null
    echo "| $b | $d | $wh | $fr | $made | $sha |  |  |  |  | UNVERIFIED | thumbs: _thumbs/${b%.*}_start.jpg, _end.jpg |" >> "$map"
    log "IMPORTS: added $b to _SOURCE_MAP.md (UNVERIFIED)"
  done
}

map_imports
captioned_from_approved
for src in "$DROP"/*.mp4 "$DROP"/*.mov "$DROP"/*.m4v; do
  stable "$src" || { log "waiting: $(basename "$src") is still being copied"; continue; }
  name="$(basename "${src%.*}")"; srt="${src%.*}.srt"; [[ -f "$srt" ]] || srt=""
  # Export and research filenames are keyed by stem.
  collision=0
  for prior in "$DONE/$name".{mp4,mov,m4v}; do
    [[ -f "$prior" ]] && collision=1
  done
  if [[ $collision == 1 ]]; then
    log "  name already exported: $(basename "$src"); rename it to a unique stem before retrying"
    continue
  fi
  probe_source "$src"; fps="$OUT_FPS"; snapwm="${TIC_SNAP_WATERMARK:-1}"
  log "start: $(basename "$src") (fps $fps, picture ${ACTIVE_CROP:-full frame}, subtitles: ${srt:+yes}${srt:-no})"
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
    [[ -z "$srt" && "${TIC_TRANSCRIBE:-1}" == 1 ]] && draft_subs "$DONE/$(basename "$src")" "$name"
    make_covers "$DONE/$(basename "$src")" "$name" "${srt:+$DONE/$(basename "$srt")}" "$fps" "$snapwm"
    log "finished: $(basename "$src") → moved to _originals"
    command -v osascript >/dev/null && osascript -e "display notification \"$name exported to Instagram, TikTok, Snapchat, YouTube\" with title \"The Iman Cut\"" 2>/dev/null || true
  else
    log "kept in drop folder because an export failed: $(basename "$src")"
  fi
done
if [[ -f "$APP/tic_carousel.py" ]]; then
  "$RENDER_PYTHON" "$APP/tic_carousel.py" "$SHOW" >>"$LOG" 2>&1 || log "  carousels: check carousels/run-status.json and the clip review records"
fi
true

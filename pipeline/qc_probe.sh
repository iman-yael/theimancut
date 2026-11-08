#!/usr/bin/env bash
# Automated technical QC for one export. It does NOT replace the human checks in
# policies/QC_CHECKLIST.md (full watch with sound, meaning, names, framing).
# Usage: qc_probe.sh EXPORT.mp4 [SIDECAR.srt]   → prints PASS/FAIL lines; also writes a frame grid.
set -uo pipefail
F=$1; SRT=${2:-}; fail=0
p(){ ffprobe -v error -select_streams "$1" -show_entries stream="$2" -of default=nw=1:nk=1 "$F" | head -1; }
chk(){ if [[ "${2:-}" == "1" ]]; then echo "PASS  $1"; else echo "FAIL  $1"; fail=1; fi; }
W=$(p v:0 width); H=$(p v:0 height); R=$(p v:0 r_frame_rate); AR=$(p v:0 avg_frame_rate)
chk "dimensions ${W}x${H} in {1080x1920,1080x1350}" $([[ "${W}x${H}" == 1080x1920 || "${W}x${H}" == 1080x1350 ]] && echo 1)
chk "video codec $(p v:0 codec_name) = h264" $([[ $(p v:0 codec_name) == h264 ]] && echo 1)
chk "pix_fmt $(p v:0 pix_fmt) = yuv420p" $([[ $(p v:0 pix_fmt) == yuv420p ]] && echo 1)
chk "color tags $(p v:0 color_primaries)/$(p v:0 color_transfer)/$(p v:0 color_space) = bt709" $([[ $(p v:0 color_transfer) == bt709 ]] && echo 1)
chk "constant frame rate r=$R avg=$AR" $([[ "$R" == "$AR" ]] && echo 1)
BR=$(ffprobe -v error -show_entries format=bit_rate -of default=nw=1:nk=1 "$F")
echo "INFO  overall bitrate $((BR/1000)) kbps (CRF 16, capped at 20 Mbps: simple content lands lower, busy content near the cap. Under 8 Mbps on live-action footage → inspect closely. Bitrate is not proof of quality — inspect the frame grid)"
chk "audio $(p a:0 codec_name) $(p a:0 sample_rate)Hz = aac 48000" $([[ $(p a:0 codec_name) == aac && $(p a:0 sample_rate) == 48000 ]] && echo 1)
ABR=$(p a:0 bit_rate); chk "audio bitrate $((ABR/1000)) kbps (target 256k, ≥230k measured allowed)" $([[ $ABR -ge 230000 ]] && echo 1)
L=$(ffmpeg -nostats -i "$F" -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
echo "INFO  integrated loudness ${L} LUFS (house target -14)"
if [[ -n "$SRT" ]]; then
  if grep -nE '\[(ACTOR|CHARACTER|NAME|TBD|SCENE)|TODO|TBD|___|PLACEHOLDER|\[(TEST|SAMPLE)\]' "$SRT"; then chk "no placeholder text in SRT" 0; else chk "no placeholder text in SRT" 1; fi
  LONG=$(awk 'length($0)>42 && $0 !~ /-->/' "$SRT" | wc -l); echo "INFO  subtitle lines >42 chars: $LONG (review for readability)"
  ML=$(awk 'BEGIN{RS="";n=0} {c=split($0,a,"\n"); if(c-2>2) n++} END{print n}' "$SRT"); chk "max 2 lines per subtitle event ($ML violations)" $([[ $ML -eq 0 ]] && echo 1)
fi
G="${F%.mp4}_QC_FRAMES.jpg"
ffmpeg -v error -y -i "$F" -vf "fps=1/2,scale=270:-2,tile=6x2" -frames:v 1 "$G" && echo "INFO  frame grid → $G"
[[ $fail -eq 0 ]] && echo "AUTOMATED QC: PASS (human QC still required)" || echo "AUTOMATED QC: FAIL"
exit $fail

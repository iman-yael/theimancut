"""Render the Bird Clay cut (vertical = v05 no-crop, YouTube = v04) in one encode pass straight from the source recording.

usage: python3 -E render_v03.py <vertical|landscape> <publish|clean> [--shorts]
  vertical publish           -> IG/TikTok (watermark)
  vertical publish --shorts  -> YouTube Shorts (no watermark)
  landscape publish          -> YouTube (no watermark)
  * clean                    -> no subtitles, labels or watermark
Run make_subs.py first.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
WM = f"{REPO}/brand/watermark/iman-cut-watermark-trimmed.png"


def find_ffmpeg():
    """ffmpeg with libx264 + libass: $FFMPEG, then PATH (e.g. brew install ffmpeg), then pip's imageio-ffmpeg."""
    import shutil
    p = os.environ.get("FFMPEG") or shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise SystemExit("ffmpeg not found: brew install ffmpeg, or python3 -m pip install --user imageio-ffmpeg")


FF = find_ffmpeg()
layout, variant = sys.argv[1], sys.argv[2]

edl = json.load(open(f"{HERE}/edl_v03.json"))
import glob
# Source video is NOT in the repo. Point BIRDCLAY_SOURCE at it; by default it's looked up in the Film & TV library
# (~/Movies/The Iman Cut/Sources, renamed 2026-11-08), then at its original Desktop name
# (the macOS name contains a narrow no-break space before "AM", hence the glob).
_cands = [os.environ["BIRDCLAY_SOURCE"]] if os.environ.get("BIRDCLAY_SOURCE") else (glob.glob(os.path.expanduser("~/Movies/The Iman Cut/Sources/The Greatest - Promo - Rome Olympic Final*.mov")) or glob.glob(os.path.expanduser("~/Desktop/Screen Recording 2026-11-08 at 11.44.17*.mov")))
if not _cands or not os.path.exists(_cands[0]):
    raise SystemExit("Source not found. Set BIRDCLAY_SOURCE=/path/to/source.mov")
src = _cands[0]
shots = [s for s in edl["shots"] if "in" in s]
SEEK = 225.0  # input seek; all trims are relative to this

# Source picture: 1966x1106 with 2 px black columns each side -> active 1962x1106.
SW, SH, SX = 1962, 1106, 2
FPS = "24000/1001"   # measured: ~24 unique frames/s inside a ~32.6 fps variable-rate capture
FADE = 0.012         # 12 ms audio fades at every cut to prevent clicks

# Cut picture and sound only where the edit actually skips source time ("runs" of contiguous shots);
# inside a run the per-shot crop is switched by time, so sync never drifts and audio is never chopped.
runs = []
for s in shots:
    if runs and abs(runs[-1][-1]["out"] - s["in"]) < 1e-6:
        runs[-1].append(s)
    else:
        runs.append([s])

cw = round(SH * 9 / 16 / 2) * 2              # 622 px wide crop, full 1106 height
def crop_x(run):
    t0, expr = run[0]["in"], f"{(SW - cw) / 2:.1f}"
    for s in reversed(run):
        a, b = s["in"] - t0, s["out"] - t0
        x0 = s["cx"] * SW - cw / 2
        x1 = s.get("cx_end", s["cx"]) * SW - cw / 2
        x = f"({x0:.1f}+({x1 - x0:.1f})*(t-{a:.3f})/{b - a:.3f})" if "cx_end" in s else f"{x0:.1f}"
        expr = f"if(lt(t\\,{b:.3f})*gte(t\\,{a:.3f})\\,{x}\\,{expr})"
    return f"max(0\\,min({SW - cw}\\,{expr}))"

n = len(runs)
parts, labels = [f"[0:v]split={n}" + "".join(f"[sv{i}]" for i in range(n)), f"[0:a]asplit={n}" + "".join(f"[sa{i}]" for i in range(n))], []
for i, run in enumerate(runs):
    a, b = run[0]["in"] - SEEK, run[-1]["out"] - SEEK
    d = b - a
    head = f"[sv{i}]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS,fps={FPS},crop={SW}:{SH}:{SX}:0"   # drops only the 2-px black side bars
    if layout == "vertical":
        # No crop: the whole frame is resized to 1080 wide and centred; the space above/below is a
        # blurred, darkened copy of the same frame (blurred at low resolution for speed).
        parts.append(f"{head},split[fg{i}][bgs{i}]")
        parts.append(f"[bgs{i}]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=12:2,eq=brightness=-0.10:saturation=0.85,scale=1080:1920[bg{i}]")
        parts.append(f"[fg{i}]scale=1080:-2:flags=lanczos[fgs{i}]")
        parts.append(f"[bg{i}][fgs{i}]overlay=0:(H-h)/2,setsar=1[v{i}]")
    else:
        parts.append(f"{head},scale=1920:1080:flags=lanczos,setsar=1[v{i}]")
    end_fade = 0.04 if i == n - 1 else FADE
    parts.append(f"[sa{i}]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d={FADE},afade=t=out:st={d - end_fade:.3f}:d={end_fade}[a{i}]")
    labels.append(f"[v{i}][a{i}]")
parts.append(f"{''.join(labels)}concat=n={n}:v=1:a=1[vc][ac]")

W, H = (1080, 1920) if layout == "vertical" else (1920, 1080)
WMW, WMX, WMY = (230, 64, 250) if layout == "vertical" else (190, 77, 43)
last = "[vc]"
SHORTS = "--shorts" in sys.argv     # vertical copy for YouTube Shorts
WATERMARK = layout == "vertical" and not SHORTS   # YouTube adds its own branding, so YouTube uploads get subtitles only (v04)
if variant == "publish":
    ass = f"{HERE}/subs_{layout}.ass"
    if WATERMARK:
        parts.append(f"[vc]ass='{ass}'[vs]")
        parts.append(f"movie='{WM}',scale={WMW}:-1[wm]")
        parts.append(f"[vs][wm]overlay={W}-w-{WMX}:{WMY}:format=auto,format=yuv420p[vo]")
    else:
        parts.append(f"[vc]ass='{ass}',format=yuv420p[vo]")
    last = "[vo]"
else:
    parts.append("[vc]format=yuv420p[vo]"); last = "[vo]"
parts.append("[ac]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[ao]")

name = "YouTubeShorts_1080x1920" if SHORTS else {"vertical": "Vertical_1080x1920", "landscape": "YouTube_1920x1080"}[layout]
tag = "" if variant == "publish" else "_CLEAN"
ver = "v05" if layout == "vertical" else ("v04" if variant == "publish" else "v03")   # v05: vertical without cropping
out = f"{HERE}/TIC_BirdClay_{name}{tag}_{ver}.mp4"
cmd = [FF, "-v", "error", "-y", "-ss", str(SEEK), "-i", src, "-filter_complex", ";".join(parts), "-map", last, "-map", "[ao]",
       "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-tune", "film", "-profile:v", "high", "-level", "4.2",
       "-r", FPS, "-fps_mode", "cfr",
       "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
print(out)

"""Version B of a batch clip: option B layout, picture zoomed on the speaking character, jump cuts over pauses.

usage: python3 variant_zoom_jump.py SOURCE WORK_DIR CLIP_NUMBER OUT.mp4 [ZOOM=1.35]
Reads parts.json / analysis.json from WORK_DIR (written by batch_review.py). Pauses longer than 0.35 s inside
the clip are removed (0.12 s of air kept each side), so the cut jumps from line to line. Original audio, -14 LUFS.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as P

SRC, WORK, N, OUT = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
ZOOM = float(sys.argv[5]) if len(sys.argv) > 5 else 1.35
a, b = json.load(open(os.path.join(WORK, "parts.json")))[N - 1]
cuts, quiet = json.load(open(os.path.join(WORK, "analysis.json")))
info = P.probe(SRC); act = info["active"]

# keep-segments: the clip minus inner pauses
keep, t = [], a
for qa, qb in sorted(quiet):
    if qb - qa < 0.35 or qb <= a + 0.3 or qa >= b - 0.3:
        continue
    s0, s1 = max(a, qa + 0.12), min(b, qb - 0.12)
    if s1 - s0 > 0.2 and s0 > t:
        keep.append((t, s0)); t = s1
keep.append((t, b))
keep = [(x, y) for x, y in keep if y - x > 0.25]

# face centre for each segment (frame at its midpoint)
cw = int(act["w"] / ZOOM) // 2 * 2
ph = int(1080 * act["h"] / cw) // 2 * 2
frames = []
for i, (x, y) in enumerate(keep):
    p = os.path.join(WORK, f"v_{N:02d}_{i:03d}.jpg")
    P.run([P.FF, "-v", "error", "-ss", f"{(x + y) / 2:.3f}", "-i", SRC, "-frames:v", "1",
           "-vf", f"crop={act['w']}:{act['h']}:{act['x']}:{act['y']},scale=640:-2", "-y", p])
    frames.append(p)
cx = {}
for line in P.run([P.FACECX, *frames]).stdout.splitlines():
    p, v, kind = line.split("\t"); cx[p] = float(v) if v != "none" else 0.5

# seek once, then work in clip-relative time; split the streams for each segment
rel = [(x - a, y - a) for x, y in keep]
n = len(keep)
parts = [f"[0:v]split={2 * n}" + "".join(f"[s{i}]" for i in range(2 * n)), f"[0:a]asplit={n}" + "".join(f"[t{i}]" for i in range(n))]
base = f"crop={act['w']}:{act['h']}:{act['x']}:{act['y']}"
for i, ((x, y), p) in enumerate(zip(rel, frames)):
    x0 = int(min(max(0, cx.get(p, 0.5) * act["w"] - cw / 2), act["w"] - cw))
    parts.append(f"[s{2 * i}]trim={x:.3f}:{y:.3f},setpts=PTS-STARTPTS,fps={info['out_fps']},{base},crop={cw}:{act['h']}:{x0}:0,"
                 f"scale=1080:{ph}:flags=lanczos,setsar=1[v{i}];"
                 f"[s{2 * i + 1}]trim={x:.3f}:{y:.3f},setpts=PTS-STARTPTS,fps={info['out_fps']},{base},scale=270:480:force_original_aspect_ratio=increase,"
                 f"crop=270:480,boxblur=12:2,eq=brightness=-0.10:saturation=0.85,scale=1080:1920,setsar=1[g{i}];"
                 f"[t{i}]atrim={x:.3f}:{y:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={max(0, y - x - 0.01):.3f}:d=0.01[a{i}]")
g = ";".join(parts) + ";" + "".join(f"[g{i}][v{i}]" for i in range(n)) + f"concat=n={n}:v=2:a=0[bg][fg];" + \
    "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[ac];" + \
    "[bg][fg]overlay=0:(H-h)/2,format=yuv420p[v];[ac]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[ao]"
r = P.run([P.FF, "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a + 0.5:.3f}", "-i", SRC, "-filter_complex", g, "-map", "[v]", "-map", "[ao]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", info["out_fps"], "-fps_mode", "cfr",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", OUT])
print("ok" if r.returncode == 0 else r.stderr[-600:], f"{len(keep)} segments, {sum(y - x for x, y in keep):.1f}s of {b - a:.1f}s")

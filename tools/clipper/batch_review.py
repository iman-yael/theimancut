"""Cut one long source into N standalone 1080x1920 review clips + an index.

usage: python3 batch_review.py SOURCE OUT_DIR PREFIX [N=30]
Boundaries fall at the end of a spoken sentence that coincides with a shot cut or pause, so every clip starts with
context and ends after the line lands. Title cards / black frames are skipped. Layout: the brand's option B
(whole frame over a blurred copy) with a modest punch-in centred on the face of each shot.
"""
import csv, glob, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as P

SRC, OUT, PREFIX = sys.argv[1], sys.argv[2], sys.argv[3]
N = int(sys.argv[4]) if len(sys.argv) > 4 else 30
PUNCH = 1.0           # no zoom: the WHOLE frame, resized into option B (brand rule)
# archival material spotted when indexing this source (black-and-white Ali stills / footage): separate rights review
ARCHIVAL = [(410, 425), (655, 665), (775, 785), (778, 790)]
os.makedirs(OUT, exist_ok=True)
work = os.path.join(OUT, "_work"); os.makedirs(work, exist_ok=True)
log = lambda *a: print(*a, flush=True)

info = P.probe(SRC); D = info["duration"]; act = info["active"]
log("probe", info)
cache = os.path.join(work, "analysis.json")
if os.path.exists(cache):
    cuts, quiet = json.load(open(cache))
else:
    cuts = P.shot_cuts(SRC, D)
    quiet = P.pauses(SRC, True, D)
    json.dump([cuts, quiet], open(cache, "w"))
tj = os.path.join(work, "transcript.json")
if not os.path.exists(tj):
    segs = P.transcribe(SRC, work, D)
    json.dump(segs, open(tj, "w"))
segs = json.load(open(tj))
log("cuts", len(cuts), "pauses", len(quiet), "segments", len(segs))

# filler: black / near-white frames (title cards, flashes, end card)
out = subprocess.run([P.FF, "-hide_banner", "-i", SRC, "-vf", "blackdetect=d=0.4:pix_th=0.10", "-an", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
black = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", out)]
filler = black + [(D - 6.0, D)]                     # Prime end card

def in_filler(t):
    return any(a - 0.3 <= t <= b + 0.3 for a, b in filler)

# candidate boundaries: sentence ends that sit near a cut or pause
ends = [s["end"] for s in segs if s["text"].strip()[-1:] in ".!?\"'"] + [s["end"] for s in segs]
def strength(t):
    near_cut = min((abs(t - c) for c in cuts), default=9) < 0.6
    return (2 if near_cut else 0) + (1 if P.in_pause(t, quiet, 0.3) else 0)
cands = sorted(set(round(t, 2) for t in ends if 3 < t < D - 6 and not in_filler(t)))

def snap(t):
    """Move a boundary onto the nearest shot cut within 0.6 s so clips don't start mid-shot."""
    c = min(cuts, key=lambda c: abs(c - t)) if cuts else t
    return c if abs(c - t) < 0.6 else t

def partition(L):
    start = next((s["start"] for s in segs if not in_filler(s["start"])), 0.0)
    res = []
    while start < D - 10:
        window = [t for t in cands if start + 0.6 * L <= t <= start + 1.7 * L]
        if not window:
            nxt = [t for t in cands if t > start + 0.6 * L]
            if not nxt:
                break
            window = nxt[:1]
        end = max(window, key=lambda t: (strength(t), -abs(t - (start + L))))
        res.append((start, end))
        nxt_start = [s["start"] for s in segs if s["start"] >= end - 0.05 and not in_filler(s["start"])]
        start = min(nxt_start) if nxt_start else end
        start = max(end, start - 0.4)               # a breath of lead-in before the next line
    return res

lo, hi = 8.0, 80.0
for _ in range(30):
    L = (lo + hi) / 2; parts = partition(L)
    if len(parts) > N: lo = L
    elif len(parts) < N: hi = L
    else: break
parts = parts[:N]
parts = [(snap(a) if abs(snap(a) - a) < 0.6 else a, snap(b)) for a, b in parts]
log("clips", len(parts), "target length", round(L, 1))

json.dump(parts, open(os.path.join(work, "parts.json"), "w"))
if "--plan" in sys.argv:
    log("plan written", os.path.join(work, "parts.json")); sys.exit(0)

# framing: face centre per shot
shot_bounds = [0.0] + cuts + [D]
frames = []
for k in range(len(shot_bounds) - 1):
    a, b = shot_bounds[k], shot_bounds[k + 1]
    p = os.path.join(work, f"s{k:04d}.jpg")
    if not os.path.exists(p):
        P.run([P.FF, "-v", "error", "-ss", f"{(a + b) / 2:.3f}", "-i", SRC, "-frames:v", "1",
               "-vf", f"crop={act['w']}:{act['h']}:{act['x']}:{act['y']},scale=640:-2", "-y", p])
    frames.append((a, b, p))
cx = {}
paths = [p for _, _, p in frames]
for i in range(0, len(paths), 150):
    for line in P.run([P.FACECX, *paths[i:i + 150]]).stdout.splitlines():
        p, v, kind = line.split("\t")
        cx[p] = (float(v) if v != "none" else 0.5, kind)
shots = [dict(start=a, end=b, cx=cx.get(p, (0.5, "none"))[0], kind=cx.get(p, (0.5, "none"))[1]) for a, b, p in frames]

def crop_x(a, b, cw):
    expr = f"{(act['w'] - cw) / 2:.1f}"
    for s in reversed([s for s in shots if s["end"] > a and s["start"] < b]):
        x = s["cx"] * act["w"] - cw / 2
        expr = f"if(lt(t\\,{s['end'] - a:.3f})*gte(t\\,{s['start'] - a:.3f})\\,{x:.1f}\\,{expr})"
    return f"max(0\\,min({act['w'] - cw}\\,{expr}))"

STOP = P.STOP
rows = []
for n, (a, b) in enumerate(parts, 1):
    text = " ".join(s["text"].strip() for s in segs if s["start"] < b - 0.2 and s["end"] > a + 0.2)
    words = [w for w in re.findall(r"[A-Za-z']+", text) if w.lower() not in STOP and len(w) > 2]
    title = " ".join(words[:6]).title() if words else "Untitled moment"
    slug = P.slug(" ".join(words[:5])) if words else "moment"
    name = f"{PREFIX}_{n:02d}_{slug}_{round(b - a)}s_1080x1920.mp4"
    cw = int(act["w"] * PUNCH) // 2 * 2
    ph = int(1080 * act["h"] / cw) // 2 * 2
    g = (f"[0:v]fps={info['out_fps']},crop={act['w']}:{act['h']}:{act['x']}:{act['y']},split[f][g];"
         f"[g]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=12:2,eq=brightness=-0.10:saturation=0.85,scale=1080:1920[bg];"
         f"[f]crop={cw}:{act['h']}:{crop_x(a, b, cw)}:0,scale=1080:{ph}:flags=lanczos[fg];[bg][fg]overlay=0:(H-h)/2,setsar=1,format=yuv420p[v]")
    d = b - a
    r = P.run([P.FF, "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", SRC, "-filter_complex", g, "-map", "[v]",
               "-map", "0:a", "-af", f"afade=t=in:d=0.012,afade=t=out:st={max(0, d - 0.05):.3f}:d=0.05,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000",
               "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high", "-r", info["out_fps"], "-fps_mode", "cfr",
               "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", os.path.join(OUT, name)])
    # thumbnail frame: the shot inside the clip with the largest, sharpest face (by detector kind), mid-shot
    inside = [s for s in shots if s["start"] >= a and s["end"] <= b] or [s for s in shots if s["end"] > a and s["start"] < b]
    best = max(inside, key=lambda s: (s["kind"] == "face", s["end"] - s["start"]))
    thumb_t = round(max(a, min(b, (best["start"] + best["end"]) / 2)) - a, 2)
    arch = any(a < y and b > x for x, y in ARCHIVAL)
    rows.append(dict(n=n, file=name, title=title, source_in=round(a, 2), source_out=round(b, 2), duration=round(d, 2),
                     confirmed_subjects="", thumbnail_time_in_clip=thumb_t,
                     archival_flag="ARCHIVAL - separate rights review" if arch else "", dialogue=text[:240],
                     render="ok" if r.returncode == 0 else ("FAILED: " + r.stderr[-200:])))
    log(n, name, rows[-1]["render"])

def tc(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"
with open(os.path.join(OUT, "INDEX.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
md = [f"# Review batch: {os.path.basename(SRC)}", "", f"{len(rows)} clips · 1080×1920 · original audio · option B layout, whole frame (no zoom). "
      "Review only; footage licence pending.", "", "| # | Title | Source in–out | Dur | Subjects (confirmed) | Thumb @ | Flags | File |", "|---|---|---|---|---|---|---|---|"]
for r in rows:
    md.append(f"| {r['n']} | {r['title']} | {tc(r['source_in'])}–{tc(r['source_out'])} | {r['duration']:.0f}s | {r['confirmed_subjects'] or 'to confirm'} | "
              f"{r['thumbnail_time_in_clip']}s | {r['archival_flag']} | {r['file']} |")
open(os.path.join(OUT, "INDEX.md"), "w").write("\n".join(md) + "\n")
log("done", OUT)

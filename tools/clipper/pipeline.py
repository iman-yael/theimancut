"""Turn one long video into a set of draft clips.

Steps: probe -> shot cuts -> pauses -> group shots into clips -> frame each shot for 9:16 -> render -> thumbnails.
Optional: Whisper transcript (machine draft, never burned in automatically).
Every step writes progress into job.json so the web app can show it.
"""
import glob, json, math, os, re, statistics, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))


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
FACECX = f"{HERE}/facecx"
WM = os.path.join(HERE, "..", "..", "brand", "watermark", "iman-cut-watermark-trimmed.png")


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


class Job:
    def __init__(self, job_dir):
        self.dir = job_dir
        self.path = f"{job_dir}/job.json"
        self.data = json.load(open(self.path))

    def save(self, **kw):
        self.data.update(kw)
        tmp = self.path + ".tmp"
        json.dump(self.data, open(tmp, "w"), indent=2)
        os.replace(tmp, self.path)

    def step(self, name, pct):
        self.save(step=name, progress=round(pct, 3))


def probe(src):
    out = run([FF, "-hide_banner", "-i", src]).stderr
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    duration = int(dur[1]) * 3600 + int(dur[2]) * 60 + float(dur[3])
    v = re.search(r"Video: (\w+).*?, (\d{2,5})x(\d{2,5})", out)
    br = re.search(r"bitrate: (\d+) kb/s", out)
    has_audio = "Audio:" in out
    # active picture (strip black bars) from a sample in the middle
    mid = max(0, duration / 2 - 5)
    cd = run([FF, "-hide_banner", "-ss", f"{mid}", "-t", "10", "-i", src, "-vf", "cropdetect=24:2:0", "-an", "-f", "null", "-"]).stderr
    crops = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", cd)
    w, h = int(v[2]), int(v[3])
    cw, ch, cx, cy = (map(int, max(set(crops), key=crops.count)) if crops else (w, h, 0, 0))
    # real frame cadence: count frames that actually change over 10 s
    sample = run([FF, "-hide_banner", "-ss", f"{mid}", "-t", "10", "-i", src, "-vf", "mpdecimate=hi=256:lo=128:frac=0.1,showinfo", "-an", "-f", "null", "-"]).stderr
    unique = len(re.findall(r"pts_time", sample)) / 10.0
    fps = "24000/1001" if 20 <= unique <= 25.5 else ("25" if unique <= 26.5 else ("30000/1001" if unique <= 31 else "30"))
    return dict(duration=duration, codec=v[1], width=w, height=h, bitrate_kbps=int(br[1]) if br else None,
                active=dict(w=cw, h=ch, x=cx, y=cy), unique_fps=round(unique, 2), out_fps=fps, has_audio=has_audio)


def shot_cuts(src, duration, threshold=0.30):
    out = run([FF, "-hide_banner", "-i", src, "-vf", f"scale=320:-2,select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-"]).stderr
    cuts = sorted(float(t) for t in re.findall(r"pts_time:([\d.]+)", out))
    clean, last = [], 0.0
    for c in cuts:                       # ignore flicker: shots shorter than 0.4 s
        if c - last >= 0.4 and duration - c >= 0.4:
            clean.append(c); last = c
    return [0.0] + clean + [duration]


def pauses(src, has_audio):
    if not has_audio:
        return []
    out = run([FF, "-hide_banner", "-i", src, "-af", "silencedetect=noise=-32dB:d=0.35", "-vn", "-f", "null", "-"]).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    return list(zip(starts, ends))


def in_pause(t, quiet, slack=0.25):
    return any(a - slack <= t <= b + slack for a, b in quiet)


def group(bounds, quiet, min_len, max_len):
    """Greedy: grow a clip shot by shot; close it at the first cut after min_len that falls in a pause,
    or force-close before max_len at the cut nearest a pause (else the last cut that fits)."""
    clips, start, i = [], bounds[0], 1
    while i < len(bounds):
        end = bounds[i]
        length = end - start
        if length >= min_len and (in_pause(end, quiet) or i == len(bounds) - 1):
            clips.append((start, end)); start = end
        elif length > max_len:
            # walk back to the best earlier cut inside the window
            cands = [b for b in bounds if start + min_len * 0.5 <= b < end]
            best = next((b for b in reversed(cands) if in_pause(b, quiet)), cands[-1] if cands else end)
            clips.append((start, best)); start = best
            i = bounds.index(best)
        i += 1
    if bounds[-1] - start > 1.0:
        if clips and bounds[-1] - start < min_len * 0.5:      # short tail joins the previous clip
            clips[-1] = (clips[-1][0], bounds[-1])
        else:
            clips.append((start, bounds[-1]))
    return clips


def frame_shots(src, bounds, active, tmp):
    """Return per-shot crop centre (0-1 of active width) using faces, then saliency, else centre."""
    os.makedirs(tmp, exist_ok=True)
    jobs = []
    for k in range(len(bounds) - 1):
        a, b = bounds[k], bounds[k + 1]
        for j, f in enumerate((0.25, 0.5, 0.75)):
            t = a + (b - a) * f
            p = f"{tmp}/s{k:04d}_{j}.jpg"
            jobs.append((k, p))
            run([FF, "-v", "error", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1",
                 "-vf", f"crop={active['w']}:{active['h']}:{active['x']}:{active['y']},scale=640:-2", "-y", p])
    res = {}
    paths = [p for _, p in jobs]
    for chunk in range(0, len(paths), 200):
        for line in run([FACECX, *paths[chunk:chunk + 200]]).stdout.splitlines():
            p, cx, kind = line.split("\t")
            res[p] = (None if cx == "none" else float(cx), kind)
    shots = []
    for k in range(len(bounds) - 1):
        vals = [res.get(p, (None, "none")) for kk, p in jobs if kk == k]
        faces = [v for v, kind in vals if kind == "face"]
        sal = [v for v, kind in vals if kind == "salient"]
        pick = faces or sal
        shots.append(dict(start=bounds[k], end=bounds[k + 1], cx=round(statistics.median(pick), 3) if pick else 0.5,
                          basis="face" if faces else ("salient" if sal else "centre")))
    return shots


def crop_expr(shots, t0, aw, cw):
    expr = f"{(aw - cw) / 2:.1f}"
    for s in reversed(shots):
        a, b = s["start"] - t0, s["end"] - t0
        x = s["cx"] * aw - cw / 2
        expr = f"if(lt(t\\,{b:.3f})*gte(t\\,{a:.3f})\\,{x:.1f}\\,{expr})"
    return f"max(0\\,min({aw - cw}\\,{expr}))"


def render(src, info, clip, shots, out, layout, watermark, quality, vertical_mode="fit"):
    a, b = clip["start"], clip["end"]
    act = info["active"]
    base = f"crop={act['w']}:{act['h']}:{act['x']}:{act['y']}"
    fps = f"fps={info['out_fps']}"
    if layout == "vertical" and vertical_mode == "crop":
        cw = round(act["h"] * 9 / 16 / 2) * 2
        mine = [s for s in shots if s["end"] > a and s["start"] < b]
        chain = f"[0:v]{fps},{base},crop={cw}:{act['h']}:{crop_expr(mine, a, act['w'], cw)}:0,scale=1080:1920:flags=lanczos,setsar=1[v]"
    elif layout == "vertical":
        # default: no crop. Whole frame resized to fit 1080 wide (or 1920 tall), centred on a blurred copy of itself.
        chain = (f"[0:v]{fps},{base},split[f][g];"
                 f"[g]scale=270:480:force_original_aspect_ratio=increase,crop=270:480,boxblur=12:2,eq=brightness=-0.10:saturation=0.85,scale=1080:1920[bg];"
                 f"[f]scale=1080:1920:force_original_aspect_ratio=decrease:flags=lanczos,scale=trunc(iw/2)*2:trunc(ih/2)*2[fg];"
                 f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[v]")
    else:
        chain = f"[0:v]{fps},{base},scale=w=1920:h=1080:force_original_aspect_ratio=decrease:flags=lanczos,scale=trunc(iw/2)*2:trunc(ih/2)*2,setsar=1[v]"
    wm = (230, 64, 250) if layout == "vertical" else (190, 77, 43)
    args = [FF, "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", src]
    if watermark and os.path.exists(WM):
        args += ["-i", WM, "-filter_complex", f"{chain};[1]scale={wm[0]}:-1[w];[v][w]overlay=main_w-w-{wm[1]}:{wm[2]},format=yuv420p[o]", "-map", "[o]"]
    else:
        args += ["-filter_complex", f"{chain};[v]format=yuv420p[o]", "-map", "[o]"]
    if info["has_audio"]:
        d = b - a
        args += ["-map", "0:a", "-af", f"afade=t=in:d=0.012,afade=t=out:st={max(0, d - 0.04):.3f}:d=0.04,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000",
                 "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
    crf, preset = {"draft": ("21", "veryfast"), "high": ("16", "slow")}[quality]
    args += ["-c:v", "libx264", "-preset", preset, "-crf", crf, "-profile:v", "high", "-r", info["out_fps"], "-fps_mode", "cfr",
             "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart", out]
    r = run(args)
    if r.returncode:
        raise RuntimeError(r.stderr[-800:])


def transcribe(src, job_dir):
    ffbin = f"{job_dir}/_bin"
    os.makedirs(ffbin, exist_ok=True)
    link = f"{ffbin}/ffmpeg"
    if not os.path.exists(link):
        os.symlink(FF, link)
    env = dict(os.environ, PATH=f"{ffbin}:{os.environ['PATH']}")
    r = run(["python3", "-E", "-m", "whisper", src, "--model", "small", "--language", "en", "--output_format", "json",
             "--output_dir", f"{job_dir}/transcript", "--fp16", "False"], env=env)
    files = glob.glob(f"{job_dir}/transcript/*.json")
    return json.load(open(files[0]))["segments"] if files else []


def main(job_dir):
    job = Job(job_dir)
    o = job.data["options"]
    src = job.data["source"]
    try:
        job.step("Reading the video", 0.02)
        info = probe(src)
        job.save(info=info)
        job.step("Finding shot cuts", 0.08)
        bounds = shot_cuts(src, info["duration"])
        job.step("Finding pauses in the audio", 0.20)
        quiet = pauses(src, info["has_audio"])
        segs = []
        if o.get("transcribe"):
            job.step("Transcribing dialogue (Whisper, machine draft)", 0.25)
            segs = transcribe(src, job_dir)
        if o.get("vertical_mode") == "crop":
            job.step("Framing every shot for vertical", 0.35)
            shots = frame_shots(src, bounds, info["active"], f"{job_dir}/_frames")
        else:   # no-crop mode doesn't need per-shot framing
            shots = [dict(start=bounds[k], end=bounds[k + 1], cx=0.5, basis="none") for k in range(len(bounds) - 1)]
        clips = group(bounds, quiet, o.get("min_len", 20), o.get("max_len", 60))
        rows = []
        for n, (a, b) in enumerate(clips, 1):
            text = " ".join(s["text"].strip() for s in segs if s["start"] < b and s["end"] > a)
            rows.append(dict(n=n, start=round(a, 3), end=round(b, 3), duration=round(b - a, 2), shots=sum(1 for s in shots if s["start"] < b and s["end"] > a),
                             text=text, files={}, status="queued"))
        job.save(clips=rows, shots=shots)
        layouts = [l for l in ("vertical", "landscape") if o.get(l, True)]
        total = len(rows) * max(1, len(layouts))
        done = 0
        for c in rows:
            c["status"] = "rendering"; job.save(clips=rows)
            thumb = f"{job_dir}/clip{c['n']:03d}.jpg"
            run([FF, "-v", "error", "-ss", f"{c['start'] + min(1.0, c['duration'] / 3):.3f}", "-i", src, "-frames:v", "1",
                 "-vf", f"crop={info['active']['w']}:{info['active']['h']}:{info['active']['x']}:{info['active']['y']},scale=480:-2", "-y", thumb])
            c["thumb"] = os.path.basename(thumb)
            for lay in layouts:
                job.step(f"Rendering clip {c['n']} of {len(rows)} ({lay})", 0.4 + 0.6 * done / total)
                name = f"clip{c['n']:03d}_{'9x16' if lay == 'vertical' else '16x9'}.mp4"
                render(src, info, c, shots, f"{job_dir}/{name}", lay, o.get("watermark", False) and lay == "vertical", o.get("quality", "draft"),
                       o.get("vertical_mode", "fit"))
                c["files"][lay] = name
                done += 1
                job.save(clips=rows)
            c["status"] = "done"; job.save(clips=rows)
        job.save(status="done", step="Done", progress=1.0, finished=time.time())
    except Exception as e:
        job.save(status="error", step="Failed", error=str(e)[-1500:])


if __name__ == "__main__":
    import sys
    main(sys.argv[1])

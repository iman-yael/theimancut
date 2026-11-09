"""Turn one long video into a set of draft clips.

Steps: probe -> shot cuts -> pauses -> group shots into clips -> frame each shot for 9:16 -> render -> thumbnails.
Optional: Whisper transcript (machine draft, never burned in automatically).
Every step writes progress into job.json so the web app can show it.
"""
import glob, json, math, os, re, shutil, statistics, subprocess, time

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


class Cancelled(Exception):
    pass


class Job:
    def __init__(self, job_dir):
        self.dir = job_dir
        self.path = f"{job_dir}/job.json"
        self.data = json.load(open(self.path))
        self.save(status="running", pid=os.getpid(), step="Starting")

    def save(self, **kw):
        try:                                   # the app may have cancelled this run meanwhile
            if json.load(open(self.path)).get("status") == "cancelled":
                raise Cancelled()
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        self.data.update(kw)
        tmp = self.path + ".tmp"
        json.dump(self.data, open(tmp, "w"), indent=2)
        os.replace(tmp, self.path)

    def step(self, name, pct):
        self.save(step=name, progress=round(pct, 3))


def run_live(args, duration, on_progress, every=1.0):
    """Run ffmpeg, calling on_progress(fraction) as it works; returns its log (stderr) text.
    Progress comes from `-progress pipe:1` (flushed key=value lines on stdout); the log is read on a thread."""
    import threading
    p = subprocess.Popen(args[:1] + ["-progress", "pipe:1", "-nostats"] + args[1:],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
    log = []
    reader = threading.Thread(target=lambda: log.append(p.stderr.read()), daemon=True)
    reader.start()
    last, pending = 0.0, b""
    while True:
        chunk = os.read(p.stdout.fileno(), 4096)      # unbuffered: progress arrives as ffmpeg writes it
        if not chunk:
            break
        lines = (pending + chunk).split(b"\n")
        pending = lines.pop()
        for line in lines:
            if line.startswith(b"out_time_us=") and duration and time.time() - last > every:
                try:
                    t = int(line.split(b"=", 1)[1]) / 1e6
                except ValueError:
                    continue
                on_progress(max(0.0, min(1.0, t / duration))); last = time.time()
    p.wait(); reader.join(5)
    text = b"".join(log).decode("utf-8", "replace")
    if p.returncode:
        raise RuntimeError(text[-1500:])
    return text


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


def run_scan(args, duration, on_progress, every=1.0):
    """Run an ffmpeg analysis pass whose filter graph emits one `showinfo@tick` line per source second;
    report progress from those lines as they appear on stderr. Returns the full log."""
    p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, bufsize=0)
    log, last, pending = [], 0.0, b""
    while True:
        chunk = os.read(p.stderr.fileno(), 65536)
        if not chunk:
            break
        lines = (pending + chunk).split(b"\n")
        pending = lines.pop()
        for raw in lines:
            line = raw.decode("utf-8", "replace")
            if "showinfo@tick" in line:
                if duration and time.time() - last > every:
                    m = re.search(r"pts_time:([\d.]+)", line)
                    if m:
                        on_progress(min(1.0, float(m[1]) / duration)); last = time.time()
            else:
                log.append(line)
    p.wait()
    if p.returncode:
        raise RuntimeError("\n".join(log[-12:]))
    return "\n".join(log)


def shot_cuts(src, duration, threshold=0.30, on_progress=lambda f: None):
    graph = (f"[0:v]scale=320:-2,split[a][b];[a]select='gt(scene,{threshold})',showinfo@cut[c];"
             f"[b]fps=1,showinfo@tick[t]")
    out = run_scan([FF, "-hide_banner", "-nostats", "-hwaccel", "videotoolbox", "-i", src, "-filter_complex", graph,
                    "-map", "[c]", "-f", "null", "-", "-map", "[t]", "-f", "null", "-"], duration, on_progress)
    cuts = sorted(float(t) for t in re.findall(r"showinfo@cut.*?pts_time:([\d.]+)", out))
    clean, last = [], 0.0
    for c in cuts:                       # ignore flicker: shots shorter than 0.4 s
        if c - last >= 0.4 and duration - c >= 0.4:
            clean.append(c); last = c
    return [0.0] + clean + [duration]


def pauses(src, has_audio, duration=None, on_progress=lambda f: None):
    if not has_audio:
        return []
    out = run_live([FF, "-hide_banner", "-i", src, "-af", "silencedetect=noise=-32dB:d=0.35", "-vn", "-f", "null", "-"], duration, on_progress)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    return list(zip(starts, ends))


def in_pause(t, quiet, slack=0.25):
    return any(a - slack <= t <= b + slack for a, b in quiet)


def group(bounds, quiet, min_len, max_len):
    """Most clips: close each clip at the EARLIEST shot cut past min_len that falls in an audio pause;
    if no cut in [min_len, max_len] is in a pause, use the earliest cut in that window.
    A single shot longer than max_len becomes its own clip. A short tail joins the previous clip."""
    clips, start, end_all = [], bounds[0], bounds[-1]
    while end_all - start > 0.5:
        window = [b for b in bounds if start + min_len <= b <= start + max_len]
        if window:
            end = next((b for b in window if in_pause(b, quiet)), window[0])
        else:
            later = [b for b in bounds if b > start + min_len]
            end = later[0] if later else end_all
        if end_all - end < min_len * 0.5:
            end = end_all
        clips.append((start, end))
        start = end
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


def render(src, info, clip, shots, out, layout, watermark, quality, vertical_mode="fit", on_progress=lambda f: None):
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
    crf, preset = {"draft": ("21", "veryfast"), "high": ("17", "medium")}[quality]
    args += ["-c:v", "libx264", "-preset", preset, "-crf", crf, "-profile:v", "high", "-r", info["out_fps"], "-fps_mode", "cfr",
             "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-movflags", "+faststart", out + ".part.mp4"]
    run_live(args, b - a, on_progress)
    os.replace(out + ".part.mp4", out)           # a clip only appears under its real name once it's complete


def transcribe(src, job_dir, duration, on_progress=lambda f: None):
    """Whisper (small, English) on the soundtrack; reports progress from the timestamps it prints."""
    ffbin = f"{job_dir}/_bin"
    os.makedirs(ffbin, exist_ok=True)
    link = f"{ffbin}/ffmpeg"
    if not os.path.exists(link):
        os.symlink(FF, link)
    wav = f"{job_dir}/audio16k.wav"
    run([FF, "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", wav])
    env = dict(os.environ, PATH=f"{ffbin}:{os.environ['PATH']}", PYTHONUNBUFFERED="1")
    p = subprocess.Popen(["python3", "-E", "-m", "whisper", wav, "--model", "small", "--language", "en", "--output_format", "json",
                          "--output_dir", f"{job_dir}/transcript", "--fp16", "False", "--verbose", "True"],
                         env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    for line in p.stdout:
        m = re.match(r"\[(?:(\d+):)?(\d+):([\d.]+) -->", line)
        if m and duration:
            on_progress(min(1.0, (int(m[1] or 0) * 3600 + int(m[2]) * 60 + float(m[3])) / duration))
    p.wait()
    files = glob.glob(f"{job_dir}/transcript/*.json")
    return json.load(open(files[0]))["segments"] if files else []


SCENELABEL = f"{HERE}/scenelabel"
# Vision labels too generic to say anything about the scene
GENERIC = {"people", "adult", "structure", "material", "document", "printed_page", "screenshot", "clothing", "wood_processed",
           "conveyance", "portal", "furniture", "textile", "child", "headgear", "jacket", "shirt", "blue_sky", "sky", "light",
           "art", "illustrations", "machine", "cord", "rope", "liquid", "water_body", "plant", "wood_natural", "consumables"}
STOP = set("a an the and or but so to of in on at for with is are was were be been it its i you he she we they me my your his her our their "
           "this that these those just oh uh um yeah okay ok well now then there here what who do does did not no yes".split())


def slug(s, n=48):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:n].rstrip("-") or "untitled"


def describe(src, info, rows, tmp):
    """Fill c['what']: dialogue keywords if transcribed, else Vision scene labels + how many faces."""
    os.makedirs(tmp, exist_ok=True)
    act = info["active"]
    frames = []
    for c in rows:
        for j, f in enumerate((0.2, 0.5, 0.8)):
            p = f"{tmp}/c{c['n']:03d}_{j}.jpg"
            run([FF, "-v", "error", "-ss", f"{c['start'] + c['duration'] * f:.3f}", "-i", src, "-frames:v", "1",
                 "-vf", f"crop={act['w']}:{act['h']}:{act['x']}:{act['y']},scale=640:-2", "-y", p])
            frames.append((c["n"], p))
    out = {}
    if os.path.exists(SCENELABEL):
        paths = [p for _, p in frames]
        for k in range(0, len(paths), 150):
            for line in run([SCENELABEL, *paths[k:k + 150]]).stdout.splitlines():
                parts = line.split("\t")
                if len(parts) == 3:
                    out[parts[0]] = (int(parts[1]), [x.split(":") for x in parts[2].split(",") if ":" in x])
    for c in rows:
        faces, labels = 0, {}
        for n, p in frames:
            if n != c["n"] or p not in out:
                continue
            fc, ls = out[p]
            faces = max(faces, fc)
            for name, conf in ls:
                if name not in GENERIC:
                    labels[name] = max(labels.get(name, 0), float(conf))
        scene = [k.replace("_", "-") for k, _ in sorted(labels.items(), key=lambda kv: -kv[1])[:2]]
        who = {0: [], 1: ["close-up"], 2: ["two-people"]}.get(faces, ["group"])
        words = [w for w in re.findall(r"[a-zA-Z']+", c.get("text", "").lower()) if w not in STOP and len(w) > 2]
        c["labels"] = scene + who
        c["what"] = slug(" ".join(words[:5])) if words else slug(" ".join(scene + who) or "scene")


def clip_base(o, c):
    """<show>_<episode>_clipNNN_<secs>s_<what> — the same stem for every file of the clip."""
    parts = [slug(o.get("show") or "", 30), slug(o.get("episode") or "", 20)]
    parts = [p for p in parts if p != "untitled"]
    return "_".join(parts + [f"clip{c['n']:03d}", f"{round(c['duration'])}s", c["what"]])


def main(job_dir):
    job = Job(job_dir)
    o = job.data["options"]
    src = job.data["source"]
    out_dir = job.data.get("out_dir") or job_dir
    os.makedirs(out_dir, exist_ok=True)
    try:
        # progress budget: probe 2% · cuts 15% · pauses 5% · transcript 25% · describe 3% · render 50%
        job.step("Reading the video", 0.01)
        info = probe(src)
        job.save(info=info)
        D = info["duration"]
        bounds = shot_cuts(src, D, on_progress=lambda f: job.step(f"Finding shot cuts · {int(f * 100)}%", 0.02 + 0.15 * f))
        quiet = pauses(src, info["has_audio"], D, on_progress=lambda f: job.step(f"Finding pauses · {int(f * 100)}%", 0.17 + 0.05 * f))
        if o.get("vertical_mode") == "crop":
            job.step("Framing every shot for vertical", 0.22)
            shots = frame_shots(src, bounds, info["active"], f"{job_dir}/_frames")
        else:   # no-crop mode doesn't need per-shot framing
            shots = [dict(start=bounds[k], end=bounds[k + 1], cx=0.5, basis="none") for k in range(len(bounds) - 1)]

        # the clip list exists now — show it straight away, with a thumbnail each
        rows = []
        for n, (a, b) in enumerate(group(bounds, quiet, o.get("min_len", 8), o.get("max_len", 30)), 1):
            rows.append(dict(n=n, start=round(a, 3), end=round(b, 3), duration=round(b - a, 2), text="", what="", files={},
                             shots=sum(1 for s in shots if s["start"] < b and s["end"] > a), status="queued", pct=0))
        act = info["active"]
        for c in rows:
            c["thumb"] = f"_thumb_{c['n']:03d}.jpg"
            run([FF, "-v", "error", "-ss", f"{c['start'] + c['duration'] / 2:.3f}", "-i", src, "-frames:v", "1",
                 "-vf", f"crop={act['w']}:{act['h']}:{act['x']}:{act['y']},scale=480:-2", "-y", f"{job_dir}/{c['thumb']}"])
        job.save(clips=rows, shots=shots, step=f"Found {len(rows)} clips", progress=0.23)

        segs = []
        if o.get("transcribe", True) and info["has_audio"]:
            segs = transcribe(src, job_dir, D, on_progress=lambda f: job.step(f"Transcribing dialogue · {int(f * 100)}%", 0.23 + 0.25 * f))
            for c in rows:
                c["text"] = " ".join(s["text"].strip() for s in segs if s["start"] < c["end"] and s["end"] > c["start"])
        job.step("Naming each clip", 0.48)
        describe(src, info, rows, f"{job_dir}/_desc")
        for c in rows:
            c["base"] = clip_base(o, c)
        job.save(clips=rows)

        layouts = [l for l in ("vertical", "landscape") if o.get(l, True)]
        total = len(rows) * max(1, len(layouts))
        done = 0
        for c in rows:
            c["status"] = "rendering"
            # final thumbnail under the clip's real name, in the visible folder
            final_thumb = f"{c['base']}.jpg"
            shutil.copyfile(f"{job_dir}/{c['thumb']}", os.path.join(out_dir, final_thumb))
            c["thumb"] = final_thumb
            for k, lay in enumerate(layouts):
                name = f"{c['base']}_{'9x16' if lay == 'vertical' else '16x9'}.mp4"

                def prog(f, k=k):
                    c["pct"] = int(100 * (k + f) / len(layouts))
                    job.step(f"Rendering clip {c['n']} of {len(rows)} ({lay}) · {int(f * 100)}%", 0.5 + 0.5 * (done + f) / total)
                render(src, info, c, shots, os.path.join(out_dir, name), lay, o.get("watermark", False) and lay == "vertical",
                       o.get("quality", "high"), o.get("vertical_mode", "fit"), on_progress=prog)
                c["files"][lay] = name
                done += 1
                job.save(clips=rows)
            c["status"] = "done"; c["pct"] = 100
            job.save(clips=rows)
        job.save(status="done", step=f"Done · {len(rows)} clips saved", progress=1.0, finished=time.time())
    except Cancelled:
        pass
    except Exception as e:
        try:
            job.save(status="error", step="Failed", error=str(e)[-1500:])
        except Cancelled:
            pass


if __name__ == "__main__":
    import sys
    main(sys.argv[1])

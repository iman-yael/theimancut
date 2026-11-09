"""The Iman Cut — Clipper. Local-only web app: pick or upload a long video, get clips.

Run:  python3 -E server.py   then open http://127.0.0.1:8765
Runs are queued and processed one at a time. Finished clips are written to
~/Movies/The Iman Cut/Clips/<show - episode - date>/ with descriptive names.
"""
import json, mimetypes, os, re, shutil, signal, subprocess, sys, threading, time, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
JOBS = f"{HERE}/jobs"
UPLOADS = f"{HERE}/uploads"
HOME = os.path.expanduser("~")
CLIPS_ROOT = os.environ.get("CLIPS_DIR", os.path.join(HOME, "Movies", "The Iman Cut", "Clips"))
# Film & TV library: the ONLY place the picker lists videos from (random screen recordings never show up).
SOURCES = os.environ.get("SOURCES_DIR", os.path.join(HOME, "Movies", "The Iman Cut", "Sources"))
LIBRARY_SINCE = time.mktime(time.strptime(os.environ.get("LIBRARY_SINCE", "2026-11-08"), "%Y-%m-%d"))
VIDEO_EXT = (".mov", ".mp4", ".m4v", ".mkv", ".webm")
SCAN_DIRS = ["Desktop", "Movies", "Documents", "Downloads"]
PORT = int(os.environ.get("PORT", 8765))
for d in (JOBS, UPLOADS, CLIPS_ROOT, SOURCES):
    os.makedirs(d, exist_ok=True)
LOCK = threading.Lock()          # guards job.json writes made by the server
HIDDEN = f"{HERE}/hidden_videos.json"     # videos you chose to hide from the picker (files are untouched)


def hidden():
    try:
        return set(json.load(open(HIDDEN)))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


# ---------- source videos ----------
_durations = {}


def duration_of(p, st):
    """Source length in seconds, read from the file header with ffmpeg (cached by size + mtime)."""
    key = (p, st.st_size, st.st_mtime)
    if key not in _durations:
        from pipeline import FF
        out = subprocess.run([FF, "-hide_banner", "-i", p], capture_output=True, text=True).stderr
        m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
        _durations[key] = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else None
    return _durations[key]


def list_videos():
    """Film & TV library only: videos in SOURCES (and one level of sub-folders) dated LIBRARY_SINCE or later."""
    out = []
    for root, dirs, files in os.walk(SOURCES):
        if root.count(os.sep) - SOURCES.count(os.sep) >= 1:
            dirs[:] = []
        dirs[:] = [x for x in dirs if not x.startswith(".")]
        for f in files:
            if f.lower().endswith(VIDEO_EXT) and not f.startswith("."):
                p = os.path.join(root, f)
                st = os.stat(p)
                added = max(st.st_mtime, st.st_birthtime if hasattr(st, "st_birthtime") else 0)
                if added < LIBRARY_SINCE:
                    continue
                out.append(dict(path=p, name=f, folder=os.path.relpath(root, os.path.dirname(SOURCES)), size=st.st_size,
                                modified=st.st_mtime, duration=duration_of(p, st)))
    hide = hidden()
    out = [v for v in out if v["path"] not in hide]
    return dict(videos=sorted(out, key=lambda v: -v["modified"]), hidden=len(hide), library=SOURCES)


def allowed_source(p):
    p = os.path.realpath(os.path.expanduser(p.strip().strip("'\"")))
    if not (p.startswith(HOME + os.sep) and p.lower().endswith(VIDEO_EXT)):
        return None, "Pick a video file (.mov .mp4 .m4v .mkv .webm) inside your home folder."
    try:
        open(p, "rb").close()
    except PermissionError:
        return None, "macOS is blocking this folder for the Clipper. Start it with 'Start Clipper.command' and allow access, or upload the file instead."
    except FileNotFoundError:
        return None, "That file doesn't exist."
    return p, None


# ---------- runs ----------
def read_job(jid):
    p = f"{JOBS}/{jid}/job.json"
    if not (re.fullmatch(r"[\w-]+", jid) and os.path.exists(p)):
        return None
    for _ in range(5):                      # the pipeline replaces the file atomically; retry a torn read
        try:
            return json.load(open(p))
        except (json.JSONDecodeError, FileNotFoundError):
            time.sleep(0.05)
    return None


def write_job(job):
    p = f"{JOBS}/{job['id']}/job.json"
    with LOCK:
        json.dump(job, open(p + ".srv", "w"), indent=2); os.replace(p + ".srv", p)


def run_folder(src, options, created):
    from pipeline import slug
    label = " - ".join(x for x in (options.get("show"), options.get("episode")) if x) or os.path.splitext(os.path.basename(src))[0]
    label = re.sub(r"[/:\\]", "-", label).strip()[:80]
    return os.path.join(CLIPS_ROOT, f"{label} - {time.strftime('%Y-%m-%d %H.%M', time.localtime(created))}")


def start_job(src, options):
    jid = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
    os.makedirs(f"{JOBS}/{jid}")
    name = os.path.basename(src)
    if src.startswith(UPLOADS + os.sep):
        name = name.split("_", 1)[-1]          # drop the upload timestamp prefix
    now = time.time()
    job = dict(id=jid, source=src, name=name, options=options, status="queued", step="Waiting in line",
               progress=0, created=now, clips=[], out_dir=run_folder(src, options, now))
    write_job(job)
    return jid


def pid_alive(pid):
    try:
        os.kill(pid, 0); return True
    except (OSError, TypeError):
        return False


def all_jobs():
    return [j for j in (read_job(x) for x in sorted(os.listdir(JOBS))) if j]


def worker():
    """Run one job at a time, oldest first."""
    while True:
        jobs = all_jobs()
        for j in jobs:          # a run whose process died without reporting goes back in line
            if j["status"] == "running" and not pid_alive(j.get("pid")):
                j.update(status="queued", step="Waiting in line (restarted)", progress=0, clips=[]); write_job(j)
        busy = [j for j in jobs if (j["status"] == "running" and pid_alive(j.get("pid")))
                or (j["status"] == "starting" and time.time() - j.get("started", 0) < 60)]
        if not busy:
            nxt = next((j for j in sorted(jobs, key=lambda j: j["created"]) if j["status"] == "queued"), None)
            if nxt:
                d = f"{JOBS}/{nxt['id']}"
                nxt.update(status="starting", step="Starting", started=time.time())
                write_job(nxt)                       # the pipeline itself then marks it running with its pid
                subprocess.Popen([sys.executable, "-E", f"{HERE}/pipeline.py", d], stdout=open(f"{d}/log.txt", "w"),
                                 stderr=subprocess.STDOUT, start_new_session=True)
        time.sleep(1.5)


def recover():
    """On start: a run that was 'running' when the app stopped goes back in the queue."""
    for j in all_jobs():
        if j["status"] in ("running", "starting") and not pid_alive(j.get("pid")):
            j.update(status="queued", step="Waiting in line (restarted)", progress=0, clips=[])
            j.setdefault("out_dir", run_folder(j["source"], j["options"], j["created"]))
            write_job(j)


# ---------- HTTP ----------
class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def send_file(self, path, download=False):
        size = os.path.getsize(path)
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        rng = self.headers.get("Range")
        start, end = 0, size - 1
        if rng and (m := re.match(r"bytes=(\d*)-(\d*)", rng)):
            if m[1]: start = int(m[1])
            if m[2]: end = min(int(m[2]), size - 1)
            if not m[1] and m[2]: start, end = size - int(m[2]), size - 1
            self.send_response(206); self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        else:
            self.send_response(200)
        self.send_header("Content-Type", ctype); self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        if download:
            self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(path)}"')
        self.end_headers()
        with open(path, "rb") as f:
            f.seek(start); left = end - start + 1
            while left > 0:
                chunk = f.read(min(1 << 20, left))
                if not chunk: break
                try: self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError): return
                left -= len(chunk)

    def do_GET(self):
        u = urlparse(self.path); p = unquote(u.path)
        if p == "/":
            return self.send_file(f"{HERE}/index.html")
        if p == "/api/videos":
            return self.send_json(list_videos())
        if p == "/api/jobs":
            jobs = sorted(all_jobs(), key=lambda j: -j["created"])
            queued = [j["id"] for j in sorted(jobs, key=lambda j: j["created"]) if j["status"] == "queued"]
            for j in jobs:
                if j["id"] in queued:
                    j["queue_pos"] = queued.index(j["id"]) + 1
            return self.send_json(jobs)
        if m := re.fullmatch(r"/api/jobs/([\w-]+)", p):
            j = read_job(m[1]); return self.send_json(j) if j else self.send_json({"error": "not found"}, 404)
        if m := re.fullmatch(r"/media/([\w-]+)/([^/]+)", p):
            j = read_job(m[1])
            if j:
                for base in (j.get("out_dir"), f"{JOBS}/{m[1]}"):
                    if not base:
                        continue
                    f = os.path.realpath(os.path.join(base, m[2]))
                    if f.startswith(os.path.realpath(base) + os.sep) and os.path.isfile(f):
                        return self.send_file(f, download="dl=1" in (u.query or ""))
        self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        p = urlparse(self.path).path
        n = int(self.headers.get("Content-Length", 0))
        if p == "/api/upload":
            name = os.path.basename(unquote(self.headers.get("X-Filename", "upload.mp4")))
            if not name.lower().endswith(VIDEO_EXT):
                return self.send_json({"error": "Only video files (.mov .mp4 .m4v .mkv .webm)"}, 400)
            safe = re.sub(r"[/:\\]", "-", name).strip() or "upload.mp4"
            dest = os.path.join(SOURCES, safe)            # uploads join the Film & TV library under their own name
            stem, ext = os.path.splitext(dest); k = 2
            while os.path.exists(dest):
                dest = f"{stem} ({k}){ext}"; k += 1
            with open(dest, "wb") as f:
                left = n
                while left > 0:
                    chunk = self.rfile.read(min(1 << 20, left))
                    if not chunk: break
                    f.write(chunk); left -= len(chunk)
            return self.send_json({"path": dest, "duration": duration_of(dest, os.stat(dest))})
        if m := re.fullmatch(r"/api/jobs/([\w-]+)/clips/(\d+)", p):
            body = json.loads(self.rfile.read(n) or b"{}")
            return self.rename_clip(m[1], int(m[2]), str(body.get("what", "")))
        if m := re.fullmatch(r"/api/jobs/([\w-]+)/cancel", p):
            j = read_job(m[1])
            if not j:
                return self.send_json({"error": "not found"}, 404)
            if j["status"] == "running" and pid_alive(j.get("pid")):
                try: os.killpg(j["pid"], signal.SIGTERM)       # pipeline + its ffmpeg/whisper children
                except OSError: pass
            if j["status"] in ("running", "queued"):
                j.update(status="cancelled", step="Cancelled"); write_job(j)
            return self.send_json(j)
        if m := re.fullmatch(r"/api/jobs/([\w-]+)/reveal", p):
            j = read_job(m[1])
            if j and j.get("out_dir"):
                os.makedirs(j["out_dir"], exist_ok=True)
                subprocess.run(["open", j["out_dir"]])
                return self.send_json({"ok": True, "folder": j["out_dir"]})
            return self.send_json({"error": "not found"}, 404)
        if p in ("/api/hide", "/api/unhide-all"):
            body = json.loads(self.rfile.read(n) or b"{}")
            h = hidden() if p == "/api/hide" else set()
            if p == "/api/hide" and body.get("path"):
                h.add(body["path"])
            json.dump(sorted(h), open(HIDDEN, "w"), indent=2)
            return self.send_json({"hidden": len(h)})
        if p == "/api/jobs":
            body = json.loads(self.rfile.read(n) or b"{}")
            src, err = allowed_source(body.get("path", ""))
            if err:
                return self.send_json({"error": err}, 400)
            opts = body.get("options", {})
            clean = dict(min_len=max(3, min(120, float(opts.get("min_len", 8)))), max_len=max(6, min(180, float(opts.get("max_len", 30)))),
                         vertical=bool(opts.get("vertical", True)), landscape=bool(opts.get("landscape", True)),
                         watermark=bool(opts.get("watermark", False)), transcribe=bool(opts.get("transcribe", True)),
                         show=str(opts.get("show", ""))[:60], episode=str(opts.get("episode", ""))[:40],
                         quality="draft" if opts.get("quality") == "draft" else "high",
                         vertical_mode="crop" if opts.get("vertical_mode") == "crop" else "fit")
            if clean["max_len"] < clean["min_len"]:
                clean["max_len"] = clean["min_len"] * 2
            return self.send_json({"id": start_job(src, clean)})
        self.send_json({"error": "not found"}, 404)

    def rename_clip(self, jid, n, what):
        """Rename every file of one clip to <show>_<episode>_clipNNN_<secs>s_<what>."""
        from pipeline import clip_base, slug
        job = read_job(jid)
        if not job or job["status"] in ("running", "queued"):
            return self.send_json({"error": "Rename after the run has finished."}, 400)
        c = next((c for c in job["clips"] if c["n"] == n), None)
        if not c or c.get("status") != "done":
            return self.send_json({"error": "Clip not found."}, 400)
        d = job.get("out_dir") or f"{JOBS}/{jid}"
        c["what"] = slug(what)
        new = clip_base(job["options"], c)
        old = c.get("base")
        if old and old != new:
            for k, f in list(c["files"].items()):
                nf = f.replace(old, new, 1)
                os.rename(os.path.join(d, f), os.path.join(d, nf)); c["files"][k] = nf
            if c.get("thumb"):
                nt = c["thumb"].replace(old, new, 1)
                os.rename(os.path.join(d, c["thumb"]), os.path.join(d, nt)); c["thumb"] = nt
        c["base"] = new
        write_job(job)
        return self.send_json(c)

    def do_DELETE(self):
        if m := re.fullmatch(r"/api/jobs/([\w-]+)", urlparse(self.path).path):
            j = read_job(m[1])
            if j:
                if j["status"] == "running" and pid_alive(j.get("pid")):
                    try: os.killpg(j["pid"], signal.SIGTERM)
                    except OSError: pass
                shutil.rmtree(f"{JOBS}/{m[1]}")       # the clips folder in Movies is kept
                return self.send_json({"ok": True})
        self.send_json({"error": "not found"}, 404)


if __name__ == "__main__":
    recover()
    threading.Thread(target=worker, daemon=True).start()
    print(f"The Iman Cut — Clipper on http://127.0.0.1:{PORT}  ·  clips are saved in {CLIPS_ROOT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()

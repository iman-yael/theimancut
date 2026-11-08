"""The Iman Cut — Clipper. Local-only web app: pick or upload a long video, get draft clips.

Run:  python3 -E server.py   then open http://127.0.0.1:8765
"""
import json, mimetypes, os, re, shutil, subprocess, sys, threading, time, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
JOBS = f"{HERE}/jobs"
UPLOADS = f"{HERE}/uploads"
HOME = os.path.expanduser("~")
VIDEO_EXT = (".mov", ".mp4", ".m4v", ".mkv", ".webm")
SCAN_DIRS = ["Desktop", "Movies", "Documents", "Downloads"]
PORT = int(os.environ.get("PORT", 8765))
os.makedirs(JOBS, exist_ok=True); os.makedirs(UPLOADS, exist_ok=True)


def list_videos():
    out, blocked = [], []
    for d in SCAN_DIRS:
        base = os.path.join(HOME, d)
        try:
            os.listdir(base)
        except PermissionError:          # macOS privacy (TCC) has not granted this app the folder
            blocked.append(d); continue
        except FileNotFoundError:
            continue
        for root, dirs, files in os.walk(base):
            if root.count(os.sep) - base.count(os.sep) >= 2:
                dirs[:] = []
            dirs[:] = [x for x in dirs if not x.startswith(".")]
            for f in files:
                if f.lower().endswith(VIDEO_EXT) and not f.startswith("."):
                    p = os.path.join(root, f)
                    st = os.stat(p)
                    out.append(dict(path=p, name=f, folder=os.path.relpath(root, HOME), size=st.st_size, modified=st.st_mtime))
    for f in os.listdir(UPLOADS):
        if f.lower().endswith(VIDEO_EXT):
            st = os.stat(f"{UPLOADS}/{f}")
            out.append(dict(path=f"{UPLOADS}/{f}", name=f.split("_", 1)[-1], folder="Clipper uploads", size=st.st_size, modified=st.st_mtime))
    return dict(videos=sorted(out, key=lambda v: -v["modified"]), blocked=blocked)


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


def start_job(src, options):
    jid = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
    d = f"{JOBS}/{jid}"; os.makedirs(d)
    name = os.path.basename(src)
    if src.startswith(UPLOADS + os.sep):
        name = name.split("_", 1)[-1]          # drop the upload timestamp prefix
    job = dict(id=jid, source=src, name=name, options=options, status="running", step="Queued",
               progress=0, created=time.time(), clips=[])
    json.dump(job, open(f"{d}/job.json", "w"), indent=2)
    subprocess.Popen([sys.executable, "-E", f"{HERE}/pipeline.py", d], stdout=open(f"{d}/log.txt", "w"), stderr=subprocess.STDOUT)
    return jid


def read_job(jid):
    p = f"{JOBS}/{jid}/job.json"
    return json.load(open(p)) if re.fullmatch(r"[\w-]+", jid) and os.path.exists(p) else None


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
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
            jobs = [read_job(j) for j in sorted(os.listdir(JOBS), reverse=True)]
            return self.send_json([j for j in jobs if j])
        if m := re.fullmatch(r"/api/jobs/([\w-]+)", p):
            j = read_job(m[1]); return self.send_json(j) if j else self.send_json({"error": "not found"}, 404)
        if m := re.fullmatch(r"/media/([\w-]+)/([\w.-]+)", p):
            f = os.path.realpath(f"{JOBS}/{m[1]}/{m[2]}")
            if f.startswith(JOBS + os.sep) and os.path.isfile(f):
                return self.send_file(f, download="dl=1" in (u.query or ""))
        self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        p = urlparse(self.path).path
        n = int(self.headers.get("Content-Length", 0))
        if p == "/api/upload":
            name = os.path.basename(unquote(self.headers.get("X-Filename", "upload.mp4")))
            if not name.lower().endswith(VIDEO_EXT):
                return self.send_json({"error": "Only video files (.mov .mp4 .m4v .mkv .webm)"}, 400)
            safe = re.sub(r"[^\w. -]", "_", name)
            dest = f"{UPLOADS}/{int(time.time())}_{safe}"
            with open(dest, "wb") as f:
                left = n
                while left > 0:
                    chunk = self.rfile.read(min(1 << 20, left))
                    if not chunk: break
                    f.write(chunk); left -= len(chunk)
            return self.send_json({"path": dest})
        if p == "/api/jobs":
            body = json.loads(self.rfile.read(n) or b"{}")
            src, err = allowed_source(body.get("path", ""))
            if err:
                return self.send_json({"error": err}, 400)
            opts = body.get("options", {})
            clean = dict(min_len=max(5, min(120, float(opts.get("min_len", 20)))), max_len=max(10, min(180, float(opts.get("max_len", 60)))),
                         vertical=bool(opts.get("vertical", True)), landscape=bool(opts.get("landscape", True)),
                         watermark=bool(opts.get("watermark", False)), transcribe=bool(opts.get("transcribe", False)),
                         quality="high" if opts.get("quality") == "high" else "draft",
                         vertical_mode="crop" if opts.get("vertical_mode") == "crop" else "fit")
            if clean["max_len"] < clean["min_len"]:
                clean["max_len"] = clean["min_len"] * 2
            return self.send_json({"id": start_job(src, clean)})
        self.send_json({"error": "not found"}, 404)

    def do_DELETE(self):
        if m := re.fullmatch(r"/api/jobs/([\w-]+)", urlparse(self.path).path):
            if read_job(m[1]):
                shutil.rmtree(f"{JOBS}/{m[1]}"); return self.send_json({"ok": True})
        self.send_json({"error": "not found"}, 404)


if __name__ == "__main__":
    print(f"The Iman Cut — Clipper on http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()

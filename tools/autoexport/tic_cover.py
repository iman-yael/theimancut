#!/usr/bin/env python3
"""The Iman Cut: automatic covers for one finished clip.

usage: tic_cover.py SRC NAME SHOW_DIR APP_DIR [--text TRANSCRIPT.json|.srt] [--cast cast_names.txt]

For every finished clip it:
  1. scans the CLEAN final cut (no burned captions) for candidate frames across opening, middle and payoff,
     skipping blinks, blur, blank frames and frames next to a cut (transitions);
  2. writes three short headlines (2-5 words) and keeps the clearest one;
  3. picks the best frame PER PLATFORM (vertical crop fit, YouTube side-by-side layout), renders the cover with
     large ivory lettering, a dark backing where contrast needs it, and the small THE IMAN CUT mark;
  4. checks each cover against the platform's visible area (Instagram grid 3:4 + 1:1, TikTok/Snapchat/Shorts
     interface zones, YouTube duration badge), shrinking/shortening or moving to the next frame if it fails;
  5. writes a title overlay for platforms that only let you pick a frame (Snapchat, YouTube Shorts), and logs
     timestamp, headline, size, filename and how to apply it.

Identity: names come only from your file name, a NAME.headline.txt you provide, or the clip's dialogue, never
from faces. A name heard only in dialogue is logged as "Probable".
Output: <platform>/<NAME>_<Platform>_Cover_<W>x<H>.jpg, _covers/<NAME>_COVERS.md, _covers/<NAME>_checks.jpg,
        and _covers/<NAME>.title.env (read by tic_autoexport.sh for the TITLED video exports).
"""
import glob, json, os, re, shutil, statistics, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = ("/System/Library/Fonts/Supplemental/Futura.ttc", 4)          # Futura Condensed ExtraBold
IVORY = (246, 235, 211)
FF = os.environ.get("TIC_FFMPEG") or shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"

# Platform canvases and how a cover is applied (as checked Nov 2026; options differ by account, so verify in-app)
PLATFORMS = [
    # key, folder, label, W, H, kind, how to apply
    ("instagram", "instagram", "Instagram", 1080, 1920, "vertical",
     "Reels → Edit cover → Add from camera roll → choose this JPG. Check the profile-grid preview."),
    ("tiktok", "tiktok", "TikTok", 1080, 1920, "vertical",
     "Select cover → Upload (if your account offers it) → choose this JPG; otherwise pick the frame at the logged time."),
    ("shorts", "youtube", "YouTubeShorts", 1080, 1920, "vertical",
     "YouTube app → Shorts → Thumbnail: pick the frame at the logged time in the _TITLED export. "
     "If your channel shows 'Upload thumbnail' for Shorts, use this JPG instead."),
    ("snapchat", "snapchat", "Snapchat", 1080, 1920, "vertical",
     "Spotlight has no custom covers: post the _TITLED export; its title is on screen at the logged time. "
     "This JPG is a preview only."),
    ("youtube", "youtube", "YouTube", 1280, 720, "wide",
     "YouTube Studio → Details → Thumbnail → Upload file → choose this JPG (needs a verified channel; max 2 MB)."),
]
FRAME_ONLY = {"snapchat", "shorts"}      # also get a _TITLED video export


def run(a, **k):
    return subprocess.run(a, capture_output=True, text=True, **k)


def duration(src):
    try:
        return float(run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", src]).stdout.strip())
    except ValueError:
        out = run([FF, "-hide_banner", "-i", src]).stderr
        m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
        return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])


def active_crop(src, dur):
    mid = max(0.0, dur / 2 - 2)
    out = run([FF, "-hide_banner", "-ss", f"{mid}", "-t", "4", "-i", src, "-vf", "cropdetect=24:2:0", "-an", "-f", "null", "-"]).stderr
    c = re.findall(r"crop=\d+:\d+:\d+:\d+", out)
    return max(set(c), key=c.count) if c else None


def cut_times(src):
    out = run([FF, "-hide_banner", "-i", src, "-vf", "scale=320:-2,select='gt(scene,0.30)',showinfo", "-an", "-f", "null", "-"]).stderr
    return [float(t) for t in re.findall(r"pts_time:([\d.]+)", out)]


def grab(src, t, crop, out, width=None):
    vf = ",".join(x for x in (crop, f"scale={width}:-2" if width else None) if x) or "null"
    run([FF, "-v", "error", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1", "-vf", vf, "-q:v", "2", "-y", out])
    return os.path.exists(out)


def vision(paths, app):
    exe = os.path.join(app, "ticvision")
    if not os.path.exists(exe):
        return {p: {"faces": [], "salient": None} for p in paths}
    res = {}
    for line in run([exe, *paths]).stdout.splitlines():
        try:
            d = json.loads(line); res[d["path"]] = d
        except ValueError:
            pass
    return res


def sharpness(img):
    g = img.convert("L").resize((480, int(480 * img.height / img.width)))
    return ImageStat.Stat(g.filter(ImageFilter.FIND_EDGES)).var[0]


# ---------------------------------------------------------------- headlines
def load_names(cast_file):
    names = []
    if cast_file and os.path.exists(cast_file):
        for line in open(cast_file, encoding="utf-8", errors="replace"):
            s = line.strip()
            if s and not s.startswith("#") and not re.search(r"\d|#|Patron|Reporter|Member|Man |Woman|Guard|Fan|Officer|Announcer|Referee", s):
                names.append(s)
    return names


def display_name(full):
    """'Odessa "Bird" Clay' -> 'BIRD CLAY'; 'Cassius Clay Sr.' -> 'CASSIUS CLAY SR.'"""
    m = re.search(r"[\"'“‘](\w+)[\"'”’]", full)
    parts = re.sub(r"[\"'“”‘’]\w+[\"'“”‘’]", "", full).split()
    if m and parts:
        return f"{m[1]} {parts[-1]}".upper()
    words = full.split()
    return " ".join(words[:3] if words[-1].rstrip(".") in ("Sr", "Jr") else words[:2]).upper()


def find_names(text, names):
    found = []
    low = " " + re.sub(r"[^a-z0-9' ]", " ", text.lower()) + " "
    for n in names:
        nick = re.search(r"[\"'“‘](\w+)[\"'”’]", n)
        keys = [re.sub(r"[\"'“”‘’]", "", n).lower()]
        if nick:
            keys.append(f"{nick[1].lower()} {n.split()[-1].lower()}")
            keys.append(nick[1].lower())
        if any(f" {k} " in low for k in keys if len(k) > 3):
            found.append(n)
    found.sort(key=lambda n: -len(n))
    return found


def transcript_text(path):
    if not path or not os.path.exists(path):
        return ""
    if path.endswith(".json"):
        d = json.load(open(path))
        return " ".join(s.get("text", "") for s in d.get("segments", []))
    return " ".join(l for l in open(path, encoding="utf-8", errors="replace").read().splitlines()
                    if l.strip() and not re.match(r"^\d+$|^\d\d:\d\d", l.strip()) and "♪" not in l)


STOP = set("a an the and or but so to of in on at for with is are was were be been it its i you he she we they me my your his "
           "her our their this that these those just oh uh um yeah okay ok well now then there here what who do does did not no "
           "yes gonna got get go going know like right come can will would could should all one up out".split())
FILLER = {"clip", "close", "up", "two", "people", "group", "scene", "s01e01", "s01e02", "s01e03", "s01e04", "s01e05",
          "s01e06", "s01e07", "s01e08", "the", "greatest", "9x16", "16x9", "mp4", "mov"}


def phrase_from(text, maxw=4):
    # prefer a short spoken line (2-5 words) that reads as a headline
    sents = [s.strip(" .,!?-–—\"'") for s in re.split(r"[.!?]+", text) if s.strip()]
    short = [s for s in sents if 2 <= len(s.split()) <= 5 and sum(w.lower() not in STOP for w in s.split()) >= 1]
    if short:
        return max(short, key=lambda s: sum(w.lower() not in STOP for w in s.split())).upper()
    words = [w for w in re.findall(r"[A-Za-z']+", text) if w.lower() not in STOP and len(w) > 2]
    return " ".join(words[:maxw]).upper() if len(words) >= 2 else ""


def headlines(name, text, names, override):
    """Three candidates; returns (chosen, candidates, subject, identity_status, needs_review)."""
    if override:
        h = override.strip().upper()
        return h, [h], None, "Given by you", False
    slug_words = [w for w in re.split(r"[_\-\s]+", name) if w and not re.match(r"^clip\d+$|^\d+s$", w.lower())]
    from_file = find_names(" ".join(slug_words) + " " + re.sub(r"([a-z])([A-Z])", r"\1 \2", name), names)
    from_dialog = find_names(text, names)
    subject, status = (from_file[0], "Confirmed (named in the file name you gave)") if from_file else \
                      ((from_dialog[0], "Probable (named in the clip's dialogue, not checked on screen)") if from_dialog else (None, "Unresolved"))
    cands = []
    lowname = name.lower()
    if subject:
        dn = display_name(subject)
        surname = dn.split()[-1]
        if "family" in lowname:
            cands.append(f"MEET THE {surname} FAMILY")
        if "cast" in lowname:
            cands.append("MEET THE CAST")
        cands.append(f"MEET {dn}")
        cands.append(f"{dn}'S REACTION" if not dn.endswith("S") else f"{dn}' REACTION")
    ph = phrase_from(text)
    if ph:
        cands.append(ph)
    what = [w for w in slug_words if w.lower() not in FILLER and not re.match(r"^\d", w)]
    if len(what) >= 2:
        cands.append(" ".join(what[-4:]).upper())
    cands = [c for i, c in enumerate(cands) if c and c not in cands[:i]][:3]
    if not cands:
        return "", [], None, status, True

    def clarity(h):
        n = len(h.split())
        s = 2.0 if subject and display_name(subject) in h else 0.0
        s += 1.0 if 2 <= n <= 5 else -1.0
        s += 0.5 if h.startswith("MEET") and "family" not in lowname and "cast" not in lowname else 0
        s += 1.0 if ("family" in lowname and "FAMILY" in h) or ("cast" in lowname and "CAST" in h) else 0
        return s - 0.05 * len(h)
    chosen = max(cands, key=clarity)
    review = subject is None and not ph
    return chosen, cands, subject, status, review


# ---------------------------------------------------------------- layout helpers
def font(size):
    return ImageFont.truetype(FONT[0], size, index=FONT[1])


def wrap(text, size, maxw):
    """Split into 1-2 lines that fit maxw at this size; None if it can't."""
    f = font(size); words = text.split()
    if f.getlength(text) <= maxw:
        return [text]
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        w = max(f.getlength(a), f.getlength(b))
        if w <= maxw and (best is None or w < best[0]):
            best = (w, [a, b])
    return best[1] if best else None


def fit_text(text, maxw, start, minimum):
    for size in range(start, minimum - 1, -4):
        lines = wrap(text, size, maxw)
        if lines:
            return size, lines
    return None, None


def text_block(lines, size):
    f = font(size); lh = int(size * 0.98)
    return max(int(f.getlength(l)) for l in lines), lh * len(lines), lh


def draw_text(img, lines, size, cx, top, align="center", left=None):
    d = ImageDraw.Draw(img); f = font(size); lh = int(size * 0.98)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for i, l in enumerate(lines):
        w = f.getlength(l)
        x = (cx - w / 2) if align == "center" else left
        for dx, dy in ((0, 6),):
            sd.text((x + dx, top + i * lh + dy - size * 0.12), l, font=f, fill=(0, 0, 0, 170))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    for i, l in enumerate(lines):
        w = f.getlength(l)
        x = (cx - w / 2) if align == "center" else left
        d.text((x, top + i * lh - size * 0.12), l, font=f, fill=IVORY + (255,))


def backing(img, box, strength=150):
    """Soft dark band behind text when the area is bright or busy."""
    x0, y0, x1, y1 = [int(v) for v in box]
    region = img.crop((max(0, x0), max(0, y0), min(img.width, x1), min(img.height, y1))).convert("L")
    st = ImageStat.Stat(region)
    if st.mean[0] < 70 and st.stddev[0] < 45:
        return False                                   # already dark and calm: no backing needed
    pad = 40
    band = Image.new("L", img.size, 0); bd = ImageDraw.Draw(band)
    bd.rounded_rectangle((x0 - pad, y0 - pad, x1 + pad, y1 + pad), radius=40, fill=strength)
    band = band.filter(ImageFilter.GaussianBlur(36))
    img.alpha_composite(Image.merge("RGBA", (Image.new("L", img.size, 0),) * 3 + (band,)))
    return True


def mark(width):
    p = os.environ.get("TIC_MARK") or os.path.join(os.path.dirname(os.path.dirname(HERE)), "brand", "watermark", "iman-cut-watermark-trimmed.png")
    for c in (p, os.path.join(os.environ.get("TIC_APP", ""), "iman-cut-watermark-trimmed.png")):
        if c and os.path.exists(c):
            m = Image.open(c).convert("RGBA"); return m.resize((width, int(width * m.height / m.width)), Image.LANCZOS)
    return None


def overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def inside(a, b):
    return a[0] >= b[0] and a[1] >= b[1] and a[2] <= b[2] and a[3] <= b[3]


# vertical (1080x1920) visible areas
V_GRID_11 = (0, 420, 1080, 1500)        # Instagram 1:1 profile crop
V_GRID_34 = (0, 240, 1080, 1680)        # Instagram 3:4 profile grid
V_UI = [(0, 0, 1080, 230), (930, 820, 1080, 1580), (0, 1560, 1080, 1920)]   # TikTok/Snap/Shorts top bar, right rail, caption
YT_BADGE = (1080, 630, 1280, 720)       # YouTube duration badge


# ---------------------------------------------------------------- cover builders
def vertical_cover(frame, faces, headline, out):
    """Crop the frame to 9:16 around the subject, place headline + mark in the safe band. Returns (ok, info)."""
    W, H = 1080, 1920
    fw, fh = frame.size
    cw = int(fh * 9 / 16)
    if cw > fw:                                       # source already narrower than 9:16: crop height instead
        ch = int(fw * 16 / 9); y0 = max(0, (fh - ch) // 2); src = frame.crop((0, y0, fw, y0 + ch)); x0 = 0
    else:
        key = [f for f in faces if f["w"] * f["h"] >= 0.35 * max(g["w"] * g["h"] for g in faces)] if faces else []
        if key:
            lo, hi = min(f["x"] for f in key) * fw, max(f["x"] + f["w"] for f in key) * fw
            if hi - lo > cw * 0.92:
                return False, "important faces don't fit a vertical crop"
            cx = (lo + hi) / 2
        else:
            cx = fw / 2
        x0 = int(min(max(0, cx - cw / 2), fw - cw)); src = frame.crop((x0, 0, x0 + cw, fh)); y0 = 0
    s = W / src.width
    img = src.resize((W, int(src.height * s)), Image.LANCZOS).crop((0, 0, W, H)).convert("RGBA")
    fboxes = []
    for f in faces:
        bx = ((f["x"] * fw - x0) * s, (f["y"] * fh - y0) * s, ((f["x"] + f["w"]) * fw - x0) * s, ((f["y"] + f["h"]) * fh - y0) * s)
        if bx[2] > 0 and bx[0] < W:
            fboxes.append(bx)
    main = max(fboxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1])) if fboxes else None
    if main and not inside(main, V_GRID_11):
        # face must survive the 1:1 profile crop; allow a little forehead loss
        if not (main[1] >= V_GRID_11[1] - (main[3] - main[1]) * 0.25 and main[3] <= V_GRID_11[3]):
            return False, "face falls outside the Instagram 1:1 profile crop"
    m = mark(210)
    for size in range(190, 103, -6):
        lines = wrap(headline, size, 800)
        if not lines:
            continue
        tw, th, lh = text_block(lines, size)
        for mark_below in (True, False):
            total = th + (m.height + 24 if (m and mark_below) else 0)
            slots = []
            if main:
                slots += [main[3] + 40, main[1] - 40 - total]
            slots += [V_GRID_11[3] - 30 - total, V_GRID_11[1] + 30]
            for top in slots:
                box = (W / 2 - tw / 2, top, W / 2 + tw / 2, top + total)
                if not inside(box, (60, V_GRID_11[1] + 10, W - 60, V_GRID_11[3] - 10)):
                    continue
                if any(overlap(box, fb) for fb in fboxes) or any(overlap(box, z) for z in V_UI):
                    continue
                mark_pos = None
                if m and not mark_below:      # mark at the top of the Instagram 3:4 area, clear of the face and the app bar
                    mb = (W / 2 - m.width / 2, 262, W / 2 + m.width / 2, 262 + m.height)
                    if any(overlap(mb, fb) for fb in fboxes):
                        mb = (64, 262, 64 + m.width, 262 + m.height)
                        if any(overlap(mb, fb) for fb in fboxes):
                            continue
                    mark_pos = (int(mb[0]), int(mb[1]))
                backed = backing(img, (box[0], box[1], box[2], box[3]))
                draw_text(img, lines, size, W / 2, top)
                if m:
                    img.alpha_composite(m, mark_pos or (int(W / 2 - m.width / 2), int(top + th + 24)))
                img.convert("RGB").save(out, quality=92)
                return True, dict(size=size, lines=lines, text_box=[int(v) for v in box], face_box=[int(v) for v in main] if main else None,
                                  backing=backed, crop_x=x0, mark="under headline" if mark_below else "top")
    return False, "no place for the headline that avoids the face and the app's buttons"



# ---------------------------------------------------------------- v2 look (matches the approved example)
WORD_FONT = "/System/Library/Fonts/Supplemental/Futura.ttc"     # 0 Medium, 2 Bold
RED = (200, 16, 46)


def wordmark(width=560):
    """'THE IMAN CUT' set as spaced caps (THE in medium, IMAN CUT in bold) with a thin red slash beneath."""
    size = 54
    fm, fb = ImageFont.truetype(WORD_FONT, size, index=0), ImageFont.truetype(WORD_FONT, size, index=2)
    track = size * 0.22
    def run_w(txt, f):
        return sum(f.getlength(c) + track for c in txt) - track
    w = run_w("THE ", fm) + track + run_w("IMAN CUT", fb)
    img = Image.new("RGBA", (int(w + 40), int(size * 2.1)), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    x = 20
    for txt, f in (("THE ", fm), ("IMAN CUT", fb)):
        for c in txt:
            sd.text((x, 6 + 3), c, font=f, fill=(0, 0, 0, 160)); d.text((x, 6), c, font=f, fill=(255, 255, 255, 255))
            x += f.getlength(c) + track
        x += track
    x0 = 20 + run_w("THE ", fm) + track
    y = size * 1.45
    d.line((x0 - 10, y + 10, x0 + run_w("IMAN", fb) * 1.25, y - 4), fill=RED + (255,), width=7)
    out = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)), img)
    return out.resize((width, int(width * out.height / out.width)), Image.LANCZOS)


def platform_headline(key, entry, chosen):
    """Per-platform variety from the character file (relationship, pronoun); falls back to the chosen headline."""
    if not entry:
        return chosen
    short = entry["short"]
    poss = "'" if short.endswith("S") else "'S"
    return {
        "instagram": f"MEET {short}",
        "shorts": entry.get("relation") or f"MEET {short}",
        "snapchat": f"WATCH {entry.get('poss', 'THEIR')} FACE",
        "tiktok": f"{short}{poss} REACTION",
        "youtube": f"MEET {short}",
    }.get(key, chosen)


def vertical_cover_v2(frame, faces, headline, out, key="instagram"):
    """Full-bleed 9:16 crop around the subject; huge ivory headline in the lower half (never on the face);
    dark fade behind it; wordmark at the top. Checks: face and headline inside Instagram's 3:4 grid,
    headline clear of the app's buttons for TikTok/Snapchat/Shorts."""
    W, H = 1080, 1920
    fw, fh = frame.size
    cw = int(fh * 9 / 16)
    if cw > fw:
        ch = int(fw * 16 / 9); y0 = max(0, (fh - ch) // 2); src = frame.crop((0, y0, fw, y0 + ch)); x0 = 0
    else:
        big = max((f["w"] * f["h"] for f in faces), default=0)
        key_faces = [f for f in faces if f["w"] * f["h"] >= 0.35 * big]
        if key_faces:
            lo, hi = min(f["x"] for f in key_faces) * fw, max(f["x"] + f["w"] for f in key_faces) * fw
            if hi - lo > cw * 0.92:
                return False, "important faces don't fit a vertical crop"
            cx = (lo + hi) / 2
        else:
            cx = fw / 2
        x0 = int(min(max(0, cx - cw / 2), fw - cw)); src = frame.crop((x0, 0, x0 + cw, fh)); y0 = 0
    s = W / src.width
    img = src.resize((W, int(src.height * s)), Image.LANCZOS).crop((0, 0, W, H)).convert("RGBA")
    fboxes = [((f["x"] * fw - x0) * s, (f["y"] * fh - y0) * s, ((f["x"] + f["w"]) * fw - x0) * s, ((f["y"] + f["h"]) * fh - y0) * s)
              for f in faces if ((f["x"] + f["w"]) * fw - x0) > 0 and (f["x"] * fw - x0) < cw]
    main = max(fboxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1])) if fboxes else None
    if main and not (main[1] >= V_GRID_34[1] - 0.2 * (main[3] - main[1]) and main[3] <= V_GRID_34[3]):
        return False, "face falls outside the Instagram profile-grid crop"
    ui_safe = key in ("tiktok", "snapchat", "shorts")
    maxw = 790 if ui_safe else 900
    bottom_limit = (V_GRID_34[3] - 30) if key == "instagram" else 1540     # above captions/app bar
    text_top_min = (main[3] + 30) if main else 900
    for size in range(300, 139, -8):
        f = font(size); words = headline.split()
        # up to 3 lines, balanced
        best = None
        for n in (1, 2, 3):
            if n > len(words):
                break
            import itertools
            for cuts in itertools.combinations(range(1, len(words)), n - 1):
                parts = [" ".join(words[a:b]) for a, b in zip((0,) + cuts, cuts + (len(words),))]
                wmax = max(f.getlength(p) for p in parts)
                if wmax <= maxw and (best is None or (n, wmax) < (best[0], best[1])):
                    best = (n, wmax, parts)
            if best:
                break
        if not best:
            continue
        lines = best[2]; lh = int(size * 0.92); th = lh * len(lines)
        top = bottom_limit - th
        if top < text_top_min:
            continue
        cxt = (W / 2) if not ui_safe else (W / 2 - 40)        # nudge left of TikTok/Snap buttons
        box = (cxt - best[1] / 2, top, cxt + best[1] / 2, top + th)
        if any(overlap(box, fb) for fb in fboxes):
            continue
        if ui_safe and any(overlap(box, z) for z in V_UI):
            continue
        # dark fade from just below the face to the bottom
        fade_from = int(max(text_top_min - 120, H * 0.45))
        a = Image.new("L", (1, H), 0)
        for y in range(H):
            a.putpixel((0, y), int(215 * max(0.0, min(1.0, (y - fade_from) / max(1, (top + th * 0.5) - fade_from)))))
        img.alpha_composite(Image.merge("RGBA", (Image.new("L", (W, H), 0),) * 3 + (a.resize((W, H)),)))
        d = ImageDraw.Draw(img)
        for i, l in enumerate(lines):
            w = f.getlength(l)
            d.text((cxt - w / 2 + 3, top + i * lh - size * 0.1 + 5), l, font=f, fill=(0, 0, 0, 150))
            d.text((cxt - w / 2, top + i * lh - size * 0.1), l, font=f, fill=IVORY + (255,))
        wm = wordmark(470)
        img.alpha_composite(wm, (int(W / 2 - wm.width / 2), 255))
        img.convert("RGB").save(out, quality=92)
        return True, dict(size=size, lines=lines, text_box=[int(v) for v in box], face_box=[int(v) for v in main] if main else None, crop_x=x0)
    return False, "headline can't be large (≥140 px) without covering the face"


def wide_cover(frame, faces, headline, out):
    W, H = 1280, 720
    fw, fh = frame.size
    if fw / fh > W / H:                               # wider than 16:9 (e.g. scope): crop sides around the subject
        cw = int(fh * W / H)
        cx = (statistics.mean(f["x"] + f["w"] / 2 for f in faces) * fw) if faces else fw / 2
        x0 = int(min(max(0, cx - cw / 2), fw - cw)); frame = frame.crop((x0, 0, x0 + cw, fh))
        faces = [dict(f, x=(f["x"] * fw - x0) / cw, w=f["w"] * fw / cw) for f in faces]
    img = frame.resize((W, H), Image.LANCZOS).convert("RGBA")
    fboxes = [(f["x"] * W, f["y"] * H, (f["x"] + f["w"]) * W, (f["y"] + f["h"]) * H) for f in faces]
    main = max(fboxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1])) if fboxes else None
    mcx = ((main[0] + main[2]) / 2 / W) if main else 0.5
    side = "right" if mcx < 0.45 else ("left" if mcx > 0.55 else None)
    if side is None:
        # centred subject: headline across the top, else bottom-left (the duration badge sits bottom-right)
        m = mark(130)
        for size in range(120, 69, -6):
            lines = wrap(headline, size, W - 140)
            if not lines:
                continue
            tw, th, lh = text_block(lines, size)
            for top in (40, H - 40 - th):
                box = (60, top, 60 + tw, top + th)
                if any(overlap(box, fb) for fb in fboxes) or overlap(box, YT_BADGE):
                    continue
                band = Image.new("L", (1, H))
                for y in range(H):
                    t = (1 - y / (th + 120)) if top < H / 2 else ((y - (H - th - 140)) / (th + 140))
                    band.putpixel((0, y), int(190 * max(0.0, min(1.0, t))))
                img.alpha_composite(Image.merge("RGBA", (Image.new("L", (W, H), 0),) * 3 + (band.resize((W, H)),)))
                draw_text(img, lines, size, None, top, align="left", left=60)
                if m:
                    mx = W - 60 - m.width
                    my = 40 if top > H / 2 else top + (th - m.height) // 2
                    if top < H / 2 and mx < 60 + tw + 30:
                        my = top + th + 16
                    img.alpha_composite(m, (int(mx), int(my)))
                img.convert("RGB").save(out, quality=92)
                return True, dict(size=size, lines=lines, text_box=[int(v) for v in box], face_box=[int(v) for v in main] if main else None,
                                  side="top" if top < H / 2 else "bottom-left")
        return False, "subject is centred and the headline can't avoid the face"
    area = (W * 0.52, 50, W - 50, 600) if side == "right" else (50, 50, W * 0.48, 600)
    size, lines = fit_text(headline, area[2] - area[0], 132, 70)
    if not size:
        return False, "headline needs text smaller than 70 px to fit"
    tw, th, lh = text_block(lines, size)
    m = mark(150); mh = m.height + 18 if m else 0
    top = max(area[1], (H - th - mh) / 2 - 40)
    left = area[0] if side == "right" else area[0]
    box = (left, top, left + tw, top + th + mh)
    if any(overlap(box, fb) for fb in fboxes) or overlap(box, YT_BADGE) or box[3] > H - 40:
        return False, "headline would cover the face or the duration badge"
    # darken the text side
    grad = Image.new("L", (W, 1));
    for x in range(W):
        t = (x / W) if side == "right" else (1 - x / W)
        grad.putpixel((x, 0), int(200 * max(0.0, (t - 0.35) / 0.65)))
    img.alpha_composite(Image.merge("RGBA", (Image.new("L", (W, H), 0),) * 3 + (grad.resize((W, H)),)))
    draw_text(img, lines, size, None, top, align="left", left=left)
    if m:
        img.alpha_composite(m, (int(left), int(top + th + 18)))
    img.convert("RGB").save(out, quality=92)
    if os.path.getsize(out) > 2_000_000:
        img.convert("RGB").save(out, quality=82)
    return True, dict(size=size, lines=lines, text_box=[int(v) for v in box], face_box=[int(v) for v in main] if main else None, side=side)


def title_overlay(headline, out, picture_h, with_mark, below=False):
    """Transparent 1080x1920 title for the option-B layout (whole frame centred).
    Videos: text in the blurred band above the picture. Covers (below=True): under the picture, inside the
    Instagram 1:1 profile crop so the whole headline survives the grid."""
    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if below:
        band_top, band_bottom = (H + picture_h) / 2 + 24, V_GRID_11[3] - 16
    else:
        band_top, band_bottom = 260, (H - picture_h) / 2 - 30      # between the app's top bar and the picture
    size, lines = None, None
    for sz in range(150, 71, -4):
        ln = wrap(headline, sz, 760 if below else 820)   # stays left of TikTok's right-hand buttons
        if ln and text_block(ln, sz)[1] + (0 if below else 0) <= band_bottom - band_top:
            size, lines = sz, ln; break
    if not size:
        return None
    tw, th, lh = text_block(lines, size)
    m = mark(190) if with_mark else None
    total = th + (m.height + 20 if m else 0)
    if below and m and total > band_bottom - band_top:
        img.alpha_composite(m, (int(W / 2 - m.width / 2), 262)); m = None; total = th   # mark to the top instead
    top = max(band_top, band_top + (band_bottom - band_top - total) / 2)
    backing(img, (W / 2 - tw / 2, top, W / 2 + tw / 2, top + total), strength=110) if False else None
    draw_text(img, lines, size, W / 2, top)
    if m:
        img.alpha_composite(m, (int(W / 2 - m.width / 2), int(top + th + 20)))
    img.save(out)
    return dict(size=size, lines=lines, top=int(top))


def check_sheet(covers, out):
    """Phone-size previews with the platform's visible-area guides."""
    tiles = []
    for key, path, W, H in covers:
        im = Image.open(path).convert("RGBA")
        g = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(g)
        if H == 1920:
            d.rectangle(V_GRID_34, outline=(80, 200, 255, 255), width=8)
            d.rectangle(V_GRID_11, outline=(255, 60, 60, 255), width=8)
            for z in V_UI:
                d.rectangle(z, fill=(255, 0, 0, 70))
        else:
            d.rectangle(YT_BADGE, fill=(255, 0, 0, 90))
        im.alpha_composite(g)
        t = im.convert("RGB"); t.thumbnail((270, 480))
        lab = Image.new("RGB", (t.width, t.height + 26), "white"); lab.paste(t, (0, 26))
        ImageDraw.Draw(lab).text((4, 4), key, fill="black", font=font(18))
        tiles.append(lab)
    sheet = Image.new("RGB", (sum(t.width + 10 for t in tiles), max(t.height for t in tiles)), "white")
    x = 0
    for t in tiles:
        sheet.paste(t, (x, 0)); x += t.width + 10
    sheet.save(out, quality=88)


# ---------------------------------------------------------------- main
def main():
    a = sys.argv[1:]
    src, name, show, app = a[:4]
    opt = dict(zip(a[4::2], a[5::2]))
    os.environ["TIC_APP"] = app
    covdir = os.path.join(show, "_covers"); os.makedirs(covdir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="tic_cover_")
    dur = duration(src)
    crop = active_crop(src, dur)
    cuts = cut_times(src)

    # 1 · candidate frames from the clean final cut
    n = int(min(40, max(12, dur * 2)))
    lo, hi = min(0.4, dur * 0.1), max(dur - 0.4, dur * 0.9)
    times = [lo + (hi - lo) * i / (n - 1) for i in range(n)]
    times = [t for t in times if all(abs(t - c) > 0.25 for c in cuts)] or times
    paths = []
    for i, t in enumerate(times):
        p = os.path.join(tmp, f"c{i:03d}.jpg")
        if grab(src, t, crop, p, 960):
            paths.append((t, p))
    vis = vision([p for _, p in paths], app)
    cands = []
    for t, p in paths:
        im = Image.open(p)
        st = ImageStat.Stat(im.convert("L"))
        if st.stddev[0] < 14:                       # blank / card / fade
            continue
        v = vis.get(p, {"faces": [], "salient": None})
        faces = [f for f in v.get("faces", []) if f.get("conf", 1) > 0.5 and f["w"] > 0.04]
        cands.append(dict(t=t, path=p, sharp=sharpness(im), bright=st.mean[0] / 255, faces=faces, salient=v.get("salient")))
    if not cands:
        print("REVIEW: no usable frame (all blank or unreadable)"); return 2
    sharp_sorted = sorted(c["sharp"] for c in cands)
    for c in cands:
        c["clarity"] = sharp_sorted.index(c["sharp"]) / max(1, len(sharp_sorted) - 1) * (1.0 if 0.12 < c["bright"] < 0.85 else 0.6)

    # 2 · headline
    override, pinned = None, []
    for d in (os.path.dirname(src), os.path.join(show, "_drop-finished-clips-here"), covdir):
        p = os.path.join(d, name + ".headline.txt")
        if os.path.exists(p):
            override = open(p).read()
        p = os.path.join(d, name + ".cover.txt")          # one or more times (seconds) where the subject is clearly on screen
        if os.path.exists(p):
            pinned = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", open(p).read())]
    text = transcript_text(opt.get("--text"))
    names = load_names(opt.get("--cast"))
    headline, options, subject, status, review = headlines(name, text, names, override)
    if not headline:
        headline = "THE GREATEST"; review = True
    entry = None
    try:
        chars = json.load(open(os.path.join(app, "characters.json")))["characters"]
    except (OSError, ValueError, KeyError):
        chars = json.load(open(os.path.join(HERE, "characters.json")))["characters"] if os.path.exists(os.path.join(HERE, "characters.json")) else []
    hay = (" " + re.sub(r"([a-z])([A-Z])", r"\1 \2", name) + " " + name + " " + (subject or "")).lower()
    for ch in chars:
        if any(m in hay for m in ch["match"]):
            entry = ch; break
    if override:
        entry = None                                   # your own headline wins on every platform
    lowname = name.lower(); group = "family" in lowname or "cast" in lowname or "FAMILY" in headline or "CAST" in headline
    reaction = "REACTION" in headline

    # 3 · score frames for this clip's subject
    def score(c):
        f = c["faces"]
        if f:
            big = max(x["w"] * x["h"] for x in f)
            others = len([x for x in f if x["w"] * x["h"] > 0.35 * big]) - 1
            rel = (min(1.0, big / 0.06) * (1.0 if others == 0 else 0.7)) if not group else min(1.0, 0.35 * len([x for x in f if x["w"] * x["h"] > 0.15 * big]) + 0.3)
            eyes = [x.get("eyes") for x in f if x["w"] * x["h"] >= 0.5 * big and x.get("eyes") is not None]
            blink = any(e < 0.13 for e in eyes)
            expr = (0.4 if blink else 0.8) + (0.2 if any(x.get("mouth", 0) > 0.25 for x in f) else 0) + (0.2 if reaction and any(x.get("mouth", 0) > 0.4 for x in f) else 0)
        else:
            rel, expr = (0.3 if c["salient"] else 0.1), 0.4
        return 0.35 * rel + 0.25 * c["clarity"] + 0.20 * min(1.0, expr) + 0.20 * (1.0 if f else 0.4)
    ranked = sorted(cands, key=score, reverse=True)
    if not any(c["faces"] for c in ranked[:5]):
        review = True
    subject_note = ""
    if pinned:                                          # your pinned moments go first, in your order
        pin = []
        for i, t in enumerate(pinned):
            pth = os.path.join(tmp, f"pin{i}.jpg")
            if grab(src, t, crop, pth, 960):
                v = vision([pth], app).get(pth, {"faces": []})
                pin.append(dict(t=t, path=pth, faces=[f for f in v.get("faces", []) if f.get("conf", 1) > 0.5], sharp=1, clarity=1, bright=0.5, salient=None))
        ranked = pin or ranked
        subject_note = "frame pinned by you (NAME.cover.txt)"
    elif subject:
        # faces are never matched to names, so a named cover needs a human check that this person is in the frame
        review = True
        subject_note = (f"check that {display_name(subject)} is the person in the chosen frame; if not, put the right time(s) "
                        f"in _covers/{name}.cover.txt (e.g. 24.5) and drop the clip again")

    # 4 · per platform: best frame that passes its checks
    log, made, chosen_vertical = [], [], None
    for key, folder, label, W, H, kind, how in PLATFORMS:
        out = os.path.join(show, folder, f"{name}_{label}_Cover_{W}x{H}.jpg")
        result, why = None, []
        tries = ranked[:8]
        if kind == "vertical" and chosen_vertical:
            tries = [chosen_vertical] + [c for c in tries if c is not chosen_vertical]   # reuse the frame across vertical platforms
        for c in tries:
            full = os.path.join(tmp, f"full_{c['t']:.3f}.png")
            if not os.path.exists(full):
                grab(src, c["t"], crop, full)
            frame = Image.open(full).convert("RGB")
            ph = platform_headline(key, entry, headline)
            for h in [ph] + ([headline] if headline != ph else []) + [o for o in options if o not in (headline, ph) and len(o) < len(ph)]:
                ok, info = (vertical_cover_v2(frame, c["faces"], h, out, key) if kind == "vertical" else wide_cover(frame, c["faces"], h, out))
                if ok:
                    result = (c, h, info); break
                why.append(f"{c['t']:.2f}s: {info}")
            if result:
                break
        if not result and kind == "vertical":
            # last resort, same as the videos: whole frame on a blurred copy, headline above the picture
            c = ranked[0]; full = os.path.join(tmp, f"full_{c['t']:.3f}.png")
            if not os.path.exists(full):
                grab(src, c["t"], crop, full)
            frame = Image.open(full).convert("RGB")
            bg = frame.resize((270, 480)).filter(ImageFilter.BoxBlur(12)).resize((W, H)).convert("RGBA")
            fg = frame.resize((W, int(W * frame.height / frame.width)), Image.LANCZOS)
            bg.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 40)))
            bg.paste(fg, (0, (H - fg.height) // 2))
            bg.convert("RGB").save(out); t_info = title_overlay(headline, os.path.join(tmp, "o.png"), fg.height, True, below=True)
            if t_info:
                bg.alpha_composite(Image.open(os.path.join(tmp, "o.png"))); bg.convert("RGB").save(out, quality=92)
            result = (c, headline, {"fallback": "whole frame on blurred background (no crop fit)"}); review = True
        if not result:
            log.append(dict(platform=label, status="REVIEW", reason="; ".join(why[-3:]))); review = True
            continue
        c, h, info = result
        if kind == "vertical" and not chosen_vertical:
            chosen_vertical = c
        made.append((label, out, W, H))
        log.append(dict(platform=label, status="ready" if key not in FRAME_ONLY else "preview + titled export",
                        time=round(c["t"], 2), headline=h, size=f"{W}x{H}", file=os.path.relpath(out, show), how=how, info=info))

    # 5 · title overlay for frame-only platforms (rendered into _TITLED videos by tic_autoexport.sh)
    env = {}
    if chosen_vertical:
        full = Image.open(os.path.join(tmp, f"full_{chosen_vertical['t']:.3f}.png"))
        pic_h = int(1080 * full.height / full.width)
        for key, with_mark in (("SC", False), ("YT-Shorts", True)):       # Snapchat export already carries the watermark
            p = os.path.join(covdir, f"{name}_{key}_title.png")
            if title_overlay(headline, p, pic_h, with_mark):
                env[f"TITLE_{key.replace('-', '_')}"] = p
        env["TITLE_TIME"] = f"{chosen_vertical['t']:.3f}"
    with open(os.path.join(covdir, f"{name}.title.env"), "w") as f:
        for k, v in env.items():
            f.write(f'{k}="{v}"\n')

    if made:
        check_sheet(made, os.path.join(covdir, f"{name}_checks.jpg"))
    md = [f"# Covers: {name}", "",
          f"- **Headline:** {headline}  (candidates: {' · '.join(options) or '-'})",
          f"- **Subject:** {display_name(subject) if subject else 'not named'} · identity: {status}" + (f" · **{subject_note}**" if subject_note else ""),
          f"- **Frames:** scanned {len(paths)} from the clean final cut ({dur:.1f}s), skipped {len(paths) - len(cands)} blank, "
          f"{len(cuts)} cut points avoided",
          f"- **Check sheet:** _covers/{name}_checks.jpg (blue = Instagram 3:4 grid, red box = 1:1 profile crop, red fill = app buttons/badge)",
          "", "| Platform | Status | Frame time | Headline | Size | File | How to apply |", "|---|---|---|---|---|---|---|"]
    for e in log:
        md.append(f"| {e['platform']} | {e['status']} | {e.get('time', '-')}s | {e.get('headline', '-')} | {e.get('size', '-')} | "
                  f"{e.get('file', '-')} | {e.get('how', e.get('reason', ''))} |")
    if env.get("TITLE_TIME"):
        md += ["", f"**Titled exports** (title on screen from {max(0, float(env['TITLE_TIME']) - 0.6):.2f}s to {float(env['TITLE_TIME']) + 1.0:.2f}s): "
               f"pick the frame at **{float(env['TITLE_TIME']):.2f}s** in `snapchat/{name}_SC_1080x1920_TITLED.mp4` and "
               f"`youtube/{name}_YT-Shorts_1080x1920_TITLED.mp4`. The clean exports stay untouched."]
    if review:
        md += ["", "**⚠ FLAGGED FOR REVIEW:** " + (subject_note or "subject unclear, no face in the strongest frames, or a platform cover failed its checks.")]
    md += ["", "Platform cover options differ by account and change over time: confirm in each app before relying on them. "
           "Nothing has been uploaded."]
    open(os.path.join(covdir, f"{name}_COVERS.md"), "w").write("\n".join(md) + "\n")
    shutil.rmtree(tmp, ignore_errors=True)
    print(("REVIEW " if review else "OK ") + f"{headline} · {len(made)} covers · " + os.path.join(covdir, f"{name}_COVERS.md"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

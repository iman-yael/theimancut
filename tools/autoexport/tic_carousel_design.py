"""The Iman Cut carousel design system (slides only; evidence checks stay in tic_carousel.py).

Fonts: Barlow Condensed ExtraBold (cover/headings), Inter SemiBold/Regular/Medium (quote/context/attribution),
Fraunces Bold (alternate quote-led cover). Installed fallbacks are used when a family is missing and the font
actually used is reported back for the manifest.
Colours: near-black #101010, ivory #F6EBD3, crimson #C52738 (accents and the slash only), muted gray #B8B0A4.
"""
import os, re, subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageStat

BG, IVORY, CRIMSON, GRAY = (16, 16, 16), (246, 235, 211), (197, 39, 56), (184, 176, 164)
FONT_DIRS = [os.path.expanduser("~/Library/Fonts"), "/Library/Fonts", "/System/Library/Fonts/Supplemental", "/System/Library/Fonts"]

# role -> (wanted family, candidates [(file, index or variation name, label)])
ROLES = {
    "display": ("Barlow Condensed ExtraBold", [("BarlowCondensed-ExtraBold.ttf", None, "Barlow Condensed ExtraBold"),
                                              ("Futura.ttc", 4, "Futura Condensed ExtraBold (fallback)")]),
    "serif":   ("Fraunces Bold", [("Fraunces-Bold.ttf", None, "Fraunces Bold"), ("Fraunces[SOFT,WONK,opsz,wght].ttf", "Bold", "Fraunces Bold"),
                                  ("Georgia Bold.ttf", None, "Georgia Bold (fallback)")]),
    "quote":   ("Inter SemiBold", [("Inter-SemiBold.ttf", None, "Inter SemiBold"), ("Inter[opsz,wght].ttf", "SemiBold", "Inter SemiBold"),
                                   ("SFNS.ttf", "Semibold", "SF Pro Semibold (fallback)"), ("HelveticaNeue.ttc", 10, "Helvetica Neue Medium (fallback)")]),
    "body":    ("Inter Regular", [("Inter-Regular.ttf", None, "Inter Regular"), ("Inter[opsz,wght].ttf", "Regular", "Inter Regular"),
                                  ("SFNS.ttf", "Regular", "SF Pro Regular (fallback)"), ("HelveticaNeue.ttc", 0, "Helvetica Neue (fallback)")]),
    "attrib":  ("Inter Medium", [("Inter-Medium.ttf", None, "Inter Medium"), ("Inter[opsz,wght].ttf", "Medium", "Inter Medium"),
                                 ("SFNS.ttf", "Medium", "SF Pro Medium (fallback)"), ("HelveticaNeue.ttc", 10, "Helvetica Neue Medium (fallback)")]),
}
USED = {}


def face(role, size):
    for fname, sel, label in ROLES[role][1]:
        for d in FONT_DIRS:
            p = os.path.join(d, fname)
            if not os.path.exists(p):
                continue
            try:
                f = ImageFont.truetype(p, size, index=sel if isinstance(sel, int) else 0)
                if isinstance(sel, str):
                    try:
                        f.set_variation_by_name(sel)
                    except (OSError, ValueError):
                        continue
                USED[role] = label
                return f
            except OSError:
                continue
    USED[role] = "PIL default (no suitable font found)"
    return ImageFont.load_default(size=size)


def fonts_used():
    return {ROLES[r][0]: USED.get(r, "not used") for r in ROLES}


def wrap(draw, text, f, width, natural=False):
    """Greedy wrap; with natural=True prefer breaking after commas/dashes so quotes break at pauses."""
    out = []
    for para in text.split("\n"):
        words, line = para.split(), ""
        for i, w in enumerate(words):
            cand = f"{line} {w}".strip()
            if line and draw.textlength(cand, font=f) > width:
                if natural:
                    # move back to the last natural pause on this line if it isn't too early
                    m = max(line.rfind(", "), line.rfind("; "), line.rfind(" — "))
                    if m > len(line) * 0.55:
                        out.append(line[:m + 1]); line = f"{line[m + 2:]} {w}".strip(); continue
                out.append(line); line = w
            else:
                line = cand
        out.append(line)
    return out


def text_block(draw, lines, f, x, y, fill, spacing=1.18, anchor_center=False, width=None):
    lh = int(f.size * spacing)
    for i, l in enumerate(lines):
        lx = x + (width - draw.textlength(l, font=f)) / 2 if anchor_center and width else x
        draw.text((lx, y + i * lh), l, font=f, fill=fill)
    return y + lh * len(lines)


def block_h(lines, f, spacing=1.18):
    return int(f.size * spacing) * len(lines)


def slash(draw, x, y, w=150):
    draw.line((x, y + 12, x + w, y - 4), fill=CRIMSON, width=8)


def brand(draw, W, H, safe, n=None, total=None):
    f = face("attrib", 30)
    draw.text((safe[0], safe[1]), "THE IMAN CUT", font=f, fill=IVORY)
    slash(draw, safe[0], safe[1] + 46, 150)
    if n:
        draw.text((safe[0], safe[3] - 34), f"{n:02d} / {total:02d}", font=face("attrib", 28), fill=GRAY)


def safe_area(W, H):
    """Instagram 4:5 uses generous margins; vertical keeps clear of the app's top bar, caption and right-hand buttons."""
    return (90, 100, W - 90, H - 100) if H <= 1350 else (90, 250, W - 170, H - 400)


def fit(draw, text, role, size_hi, size_lo, width, height, natural=False):
    for s in range(size_hi, size_lo - 1, -2):
        f = face(role, s); lines = wrap(draw, text, f, width, natural)
        if block_h(lines, f) <= height and all(draw.textlength(l, font=f) <= width for l in lines):
            return f, lines
    raise ValueError(f"Text doesn't fit at {size_lo}px ({role}). Shorten the copy or split the slide.")


def cover_photo(still, W, H, focus_x=0.5):
    """Crop a still to the canvas around the subject and darken the lower part for type."""
    sw, sh = still.size
    tw = sh * W / H
    if tw <= sw:
        x0 = int(min(max(0, focus_x * sw - tw / 2), sw - tw)); im = still.crop((x0, 0, int(x0 + tw), sh))
    else:
        th = sw * H / W; y0 = int(max(0, (sh - th) * 0.3)); im = still.crop((0, y0, sw, int(y0 + th)))
    im = im.resize((W, H), Image.LANCZOS).convert("RGB")
    grad = Image.new("L", (1, H))
    for y in range(H):
        grad.putpixel((0, y), int(235 * max(0.0, min(1.0, (y - H * 0.38) / (H * 0.45)))))
    im.paste(Image.new("RGB", (W, H), BG), (0, 0), grad.resize((W, H)))
    return im


def slide_cover(W, H, headline, kicker, still=None, focus_x=0.5, treatment="image"):
    safe = safe_area(W, H)
    if treatment == "image" and still is not None:
        im = cover_photo(still, W, H, focus_x)
    else:
        im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    width = safe[2] - safe[0]
    if treatment == "image":
        f, lines = fit(d, headline, "display", 140, 104, width, int(H * 0.30))
        y = safe[3] - 60 - block_h(lines, f, 0.98)
        if kicker:
            kf = face("attrib", 34); d.text((safe[0], y - 62), kicker, font=kf, fill=GRAY)
        text_block(d, lines, f, safe[0], y, IVORY, 0.98)
        slash(d, safe[0], y + block_h(lines, f, 0.98) + 34, 220)
    else:   # typography-led, Fraunces
        f, lines = fit(d, headline, "serif", 132, 88, width, int(H * 0.42))
        y = (safe[1] + safe[3]) / 2 - block_h(lines, f, 1.05) / 2
        if kicker:
            kf = face("attrib", 34); d.text((safe[0], y - 70), kicker, font=kf, fill=GRAY)
        text_block(d, lines, f, safe[0], y, IVORY, 1.05)
        slash(d, safe[0], y + block_h(lines, f, 1.05) + 24, 260)
    brand(d, W, H, safe)
    return im


def backdrop(W, H, bg=None, focus_x=0.5, dark=0.58):
    """Full-bleed scene still, darkened (and lightly softened) so ivory text stays readable."""
    if bg is None:
        return Image.new("RGB", (W, H), BG)
    sw, sh = bg.size; tw = sh * W / H
    if tw <= sw:
        x0 = int(min(max(0, focus_x * sw - tw / 2), sw - tw)); im = bg.crop((x0, 0, int(x0 + tw), sh))
    else:
        th = sw * H / W; y0 = int(max(0, (sh - th) / 2)); im = bg.crop((0, y0, sw, int(y0 + th)))
    im = im.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3)).convert("RGB")
    return Image.blend(im, Image.new("RGB", (W, H), BG), dark)


def slide_text(W, H, heading, body, n, total, sub=None, still=None, focus_x=0.5, bg=None, bg_focus=0.5):
    im = backdrop(W, H, bg, bg_focus); d = ImageDraw.Draw(im); safe = safe_area(W, H)
    width = safe[2] - safe[0]; y = safe[1] + 110
    if still is not None:
        ph = int((safe[3] - safe[1]) * 0.42)
        s = cover_photo(still, W, ph, focus_x).crop((0, 0, W, ph))
        im.paste(s, (0, y - 20)); y += ph + 10
    hf, hl = fit(d, heading, "display", 96, 64, width, 240)
    y = text_block(d, hl, hf, safe[0], y, IVORY, 1.0) + 26
    room = safe[3] - 70 - y - (90 if sub else 0)
    bf, bl = fit(d, body, "body", 48, 34, width, room)
    y = text_block(d, bl, bf, safe[0], y, IVORY, 1.3) + 24
    if sub:
        sf, sl = fit(d, sub, "attrib", 34, 26, width, 120)
        text_block(d, sl, sf, safe[0], y, GRAY, 1.25)
    brand(d, W, H, safe, n, total)
    return im


def slide_quote(W, H, quote, speaker, credit, n, total, bg=None, bg_focus=0.5):
    im = backdrop(W, H, bg, bg_focus, dark=0.66); d = ImageDraw.Draw(im); safe = safe_area(W, H)
    width = safe[2] - safe[0]
    qf, ql = fit(d, f"“{quote}”", "quote", 72, 44, width, int((safe[3] - safe[1]) * 0.62), natural=True)
    af, al = fit(d, f"— {speaker}\n{credit}", "attrib", 34, 26, width, 160)
    total_h = block_h(ql, qf, 1.22) + 60 + block_h(al, af, 1.3)
    y = (safe[1] + safe[3]) / 2 - total_h / 2 + 20
    y = text_block(d, ql, qf, safe[0], y, IVORY, 1.22) + 30
    d.line((safe[0], y, safe[0] + 120, y), fill=CRIMSON, width=6); y += 30
    text_block(d, al, af, safe[0], y, GRAY, 1.3)
    brand(d, W, H, safe, n, total)
    return im


def grab_still(clip_path, t, ff="ffmpeg"):
    import tempfile
    fd, tmp = tempfile.mkstemp(suffix=".png"); os.close(fd)
    r = subprocess.run([ff, "-v", "error", "-ss", f"{t:.3f}", "-i", str(clip_path), "-frames:v", "1", "-y", tmp], capture_output=True)
    try:
        if r.returncode == 0 and os.path.getsize(tmp) > 0:
            im = Image.open(tmp); im.load(); return im.convert("RGB")
        return None
    finally:
        os.remove(tmp)


def phone_preview(paths, out, label=None):
    ims = []
    for p in paths:
        im = Image.open(p).convert("RGB"); im.thumbnail((300, 534)); ims.append(im)
    sheet = Image.new("RGB", (sum(i.width + 16 for i in ims) + 16, max(i.height for i in ims) + 60), (235, 235, 235))
    d = ImageDraw.Draw(sheet); x = 16
    if label:
        d.text((16, 14), label, font=face("attrib", 24), fill=(20, 20, 20))
    for i in ims:
        sheet.paste(i, (x, 48)); x += i.width + 16
    sheet.save(out, quality=90)

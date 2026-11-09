#!/usr/bin/env python3
"""Build local, review-ready quote carousel packages from finished clips."""
import argparse
import csv
import io
import hashlib
import json
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont

PLATFORMS = {
    "instagram": (1350, "carousel"),
    "tiktok": (1920, "photo-post"),
    "youtube": (1350, "community-images"),
    "snapchat": (1920, "story-sequence"),
}
IVORY = "#f6ebd3"


def read_json(path):
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def write_json(path, value):
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def write_csv(path, records, fields):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(records)
    write_text(path, buffer.getvalue())


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False
    ) as output:
        output.write(text)
    Path(output.name).replace(path)


def present(record, fields):
    return all(isinstance(record.get(key), str) and record[key].strip() for key in fields)


def font(size):
    for path in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "DejaVuSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def wrap(draw, text, face, width):
    lines = []
    for paragraph in text.splitlines():
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}".strip()
            if line and draw.textlength(candidate, font=face) > width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return "\n".join(lines)


def render(path, height, title, body, number, total):
    image = Image.new("RGB", (1080, height), "#101010")
    draw = ImageDraw.Draw(image)
    draw.text((100, 125), "THE IMAN CUT", font=font(32), fill=IVORY)
    draw.line((100, 189, 255, 174), fill="#c52738", width=8)
    draw.text((100, height - 160), f"{number:02d} / {total:02d}", font=font(29), fill=IVORY)
    for size in range(88, 33, -3):
        face = font(size)
        heading = wrap(draw, title, face, 880)
        detail = wrap(draw, body, font(max(34, size - 19)), 880)
        detail_font = font(max(34, size - 19))
        a = draw.multiline_textbbox((0, 0), heading, font=face, spacing=12)
        b = draw.multiline_textbbox((0, 0), detail, font=detail_font, spacing=14)
        if max(a[2], b[2]) <= 880 and a[3] + b[3] + 60 <= height - 480:
            y = max(265, (height - a[3] - b[3] - 60) // 2)
            draw.multiline_text((100, y), heading, font=face, fill=IVORY, spacing=12)
            draw.multiline_text((100, y + a[3] + 60), detail,
                                font=detail_font, fill=IVORY, spacing=14)
            image.save(path)
            return
    raise ValueError(f"Slide {number} exceeds the readable text area. Shorten the copy.")


def build(clip, root):
    clip_id = clip.stem
    if clip_id.endswith("."):
        raise ValueError("Clip name cannot end with a dot")
    profile = read_json(root / "inputs" / f"{clip_id}.json")
    if "approved_take" in profile and not isinstance(profile["approved_take"], str):
        raise ValueError("approved_take must be text")
    quote_id = profile.get("quote_id")
    quote = {}
    if isinstance(quote_id, str) and re.fullmatch(r"[A-Za-z0-9_-]+", quote_id):
        quote = read_json(root / "knowledge-base" / "quotes" / f"{quote_id}.json")

    record = {**profile, "clip_id": clip_id, "filename": clip.name, "packages": []}
    index_path = root / "knowledge-base" / "clips" / f"{clip_id}.json"
    if not present(profile, ("character", "performer", "person_id", "real_person",
                             "scene_context", "clip_connection")):
        record.update(status="NEEDS_CLIP_REVIEW", action="Complete the clip input record.")
    elif (
        quote.get("status") != "VERIFIED"
        or quote.get("reuse_status") != "APPROVED"
        or quote.get("attribution_type") != "FIRST_PERSON"
        or quote.get("person_id") != profile["person_id"]
        or quote.get("speaker") != profile["real_person"]
        or not present(quote, ("text", "speaker", "source_title", "source_url",
                               "source_location", "context", "verified_by"))
        or urlparse(quote["source_url"]).scheme not in {"http", "https"}
        or not urlparse(quote["source_url"]).hostname
    ):
        record.update(status="NEEDS_VERIFIED_QUOTE",
                      action="Supply a verified first-person quote with source and reuse approval.")
    else:
        try:
            record["packages"] = packages(root, clip_id, profile, quote_id, quote)
        except ValueError as error:
            record.update(status="NEEDS_LAYOUT_REVIEW", action=str(error))
        else:
            record.update(status="READY_FOR_REVIEW", action="Review slides and verify upload route.")
    write_json(index_path, record)
    return record["status"]


def packages(root, clip_id, profile, quote_id, quote):
    """Design-system decks (tic_carousel_design.py). Same evidence rules; one job per slide."""
    import os, sys
    sys.path.insert(0, str(Path(__file__).parent))
    import tic_carousel_design as TD
    person, character = profile["real_person"], profile["character"]
    show_dir = root.parent
    # who the deck is about: pronoun + relationship from the character file (credits/history, never faces)
    poss, relation, real_full = "THEIR", "", person
    try:
        for ch in json.loads((Path(__file__).parent / "characters.json").read_text())["characters"]:
            if ch["credited"].lower() == character.lower() or character.lower() in ch["match"]:
                poss, relation, real_full = ch.get("poss", poss), ch.get("relation", ""), ch.get("real_person", person)
    except (OSError, ValueError, KeyError):
        pass
    headline = profile.get("deck_headline") or f"IN {poss} OWN WORDS"
    kicker = person.upper()
    credit = quote.get("short_credit") or re.sub(r"^.*?,\s*", "", quote["source_title"]).split(",")[0] + \
        (f", {m.group(0)}" if (m := re.search(r"\b(1[89]\d\d|20\d\d)\b", quote["source_title"])) else "")
    # cover still: the approved cover moment of the finished clip, framed on the largest face
    clip_path = next((p for p in (show_dir / "_originals").glob(f"{clip_id}.*")), None)
    t = profile.get("cover_time")
    envf = show_dir / "_covers" / f"{clip_id}.title.env"
    if t is None and envf.exists():
        m = re.search(r'TITLE_TIME="([\d.]+)"', envf.read_text())
        t = float(m.group(1)) if m else None
    still, focus = None, 0.5
    if clip_path and t is not None:
        still = TD.grab_still(clip_path, float(t), os.environ.get("TIC_FFMPEG", "ffmpeg"))
        try:
            import tic_cover
            still.save("/tmp/_tic_still_v.jpg")
            faces = tic_cover.vision(["/tmp/_tic_still_v.jpg"], str(Path(__file__).parent)).get("/tmp/_tic_still_v.jpg", {}).get("faces", [])
            if faces:
                f = max(faces, key=lambda f: f["w"] * f["h"]); focus = f["x"] + f["w"] / 2
        except Exception:
            pass
    scene = []          # (still, focus_x) for slide backgrounds
    if clip_path:
        try:
            import subprocess as sp, tic_cover
            dur = float(sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(clip_path)],
                               capture_output=True, text=True).stdout.strip() or 0)
            for k, frac in enumerate((0.12, 0.3, 0.48, 0.66, 0.84, 0.95)):
                im_k = TD.grab_still(clip_path, dur * frac, os.environ.get("TIC_FFMPEG", "ffmpeg"))
                if im_k is None:
                    continue
                pth = f"/tmp/_tic_bg_{k}.jpg"; im_k.save(pth)
                fs = tic_cover.vision([pth], str(Path(__file__).parent)).get(pth, {}).get("faces", [])
                fx = (max(fs, key=lambda f: f["w"] * f["h"])["x"] + max(fs, key=lambda f: f["w"] * f["h"])["w"] / 2) if fs else 0.5
                scene.append((im_k, fx, bool(fs)))
            scene.sort(key=lambda x: not x[2])           # frames with faces first
        except Exception:
            scene = []
    who_body = real_full + (f". {relation[0] + relation[1:].lower()}." if relation else ".")
    slides = [
        ("cover", None),
        ("text", (person.upper(), who_body, f"In The Greatest: {profile['performer']} plays {character}.", None)),
        ("quote", None),
        ("text", ("WHAT WAS HAPPENING", quote["context"], None, None)),
        ("text", ("IN THE CLIP", f'{profile["scene_context"]} {profile["clip_connection"]}', "The series dramatizes this scene; the quote is from the historical record.", still)),
    ]
    if profile.get("approved_take"):
        slides.append(("text", ("THE IMAN CUT'S TAKE", profile["approved_take"], None, None)))
    slides.append(("text", (profile.get("close_heading", "YOUR TAKE"), profile.get("close_question", "What did you notice in her face when the news came?"),
                            f"Source: {quote['source_title']} · {quote['source_location']}", None)))
    slug = re.sub(r"[^a-z0-9]+", "-", character.lower()).strip("-") or "character"
    key = json.dumps([clip_id, profile, quote, PLATFORMS, 5, headline], sort_keys=True)
    deck_id = hashlib.sha256(key.encode()).hexdigest()[:16]
    # human-friendly, stable folder names: carousel-1, carousel-2, … (one number per deck, kept forever)
    numbers_path = root / "deck-numbers.json"
    numbers = read_json(numbers_path)
    if deck_id not in numbers:
        numbers[deck_id] = f"carousel-{len(numbers) + 1}"
        write_json(numbers_path, numbers)
    deck_name = numbers[deck_id]
    outputs = []
    for platform, (height, kind) in PLATFORMS.items():
        H = 1350 if platform in ("instagram", "youtube") else 1920
        directory = root / platform / slug / deck_name
        names = ["01_cover.png"] + [f"{n:02d}_slide.png" for n in range(2, len(slides) + 1)]
        directory.mkdir(parents=True, exist_ok=True)
        total = len(slides)
        for n, ((kind_s, data), filename) in enumerate(zip(slides, names), 1):
            if kind_s == "cover":
                im = TD.slide_cover(1080, H, headline, kicker, still, focus, "image" if still is not None else "type")
                TD.slide_cover(1080, H, headline, kicker, None, focus, "type").save(directory / "01_cover_alt-typographic.png")
            elif kind_s == "quote":
                bgi = scene[(n - 2) % len(scene)] if scene else (None, 0.5, False)
                im = TD.slide_quote(1080, H, quote["text"], quote["speaker"], credit, n, total, bgi[0], bgi[1])
            else:
                heading, body, sub, img = data
                bgi = scene[(n - 2) % len(scene)] if (scene and img is None) else (None, 0.5, False)
                im = TD.slide_text(1080, H, heading, body, n, total, sub, img, focus, bgi[0], bgi[1])
            im.save(directory / filename)
        TD.phone_preview([directory / "01_cover.png", directory / "01_cover_alt-typographic.png"],
                         directory / "_cover_comparison_phone.jpg", "Cover A: image-led (display)   ·   Cover B: typography-led (serif)")
        TD.phone_preview([directory / n for n in names], directory / "_deck_phone_preview.jpg", f"{platform} · {kind} · 1080x{H}")
        caption = (f"{headline.title()}: {person} — {credit}.\n"
                   f"{profile['performer']} plays {character} in The Greatest. Swipe for the context and the clip.\n"
                   f"Source: {quote['source_url']}\n{profile.get('close_question', 'What did you notice in her face when the news came?')}")
        (directory / "caption.txt").write_text(caption + "\n", encoding="utf-8")
        alts = ["Cover: " + (f"still from The Greatest of {character}, " if still is not None else "") + f"headline '{headline}', name {person}."] + \
               [f"Slide {i}: " + (f"quote from {person}: “{quote['text']}” — {credit}." if k == "quote" else f"{d[0].title()}. {d[1]}") for i, (k, d) in enumerate(slides[1:], 2)]
        (directory / "alt-text.txt").write_text("\n".join(alts) + "\n", encoding="utf-8")
        (directory / "sources.md").write_text(
            f'# Sources\n\n- Quote ({quote.get("attribution_type", "")}): “{quote["text"]}”\n- Speaker: {quote["speaker"]}\n'
            f'- Source: {quote["source_title"]}\n- Location: {quote["source_location"]}\n- URL: {quote["source_url"]}\n'
            f'- Verified by: {quote["verified_by"]} · reuse: {quote.get("reuse_status")}\n- Clip: {clip_id} · {profile.get("clip_source", "")}\n'
            f'- Performer credit: {profile["performer"]} as {character} (The Greatest, Prime Video)\n', encoding="utf-8")
        write_json(directory / "manifest.json", {
            "clip_id": clip_id, "quote_id": quote_id, "deck": deck_name, "deck_id": deck_id, "design": "tic-design-v1",
            "format": kind, "dimensions": [1080, H], "slides": names, "alt_cover": "01_cover_alt-typographic.png",
            "cover_treatment": "image-led" if still is not None else "typographic", "cover_time": t,
            "headline": headline, "fonts": TD.fonts_used(), "status": "READY_FOR_REVIEW", "platform": platform,
            "upload_route_check": "confirm the destination's current format and crop before posting",
        })
        outputs.append(str(directory.relative_to(root)))
    return outputs


def publish_indexes(base, records):
    write_csv(base / "clip-index.csv", records, (
        "clip_id", "filename", "character", "performer", "person_id", "real_person",
        "clip_source", "scene_context", "clip_connection", "quote_id", "status",
    ))
    profiles = {}
    for clip in records:
        person_id = clip.get("person_id")
        if isinstance(person_id, str) and re.fullmatch(r"[A-Za-z0-9_-]+", person_id):
            profiles.setdefault(person_id, []).append(clip)
    for person_id, clips in profiles.items():
        write_json(base / "character-profiles" / f"{person_id}.json",
                   {"person_id": person_id, "clips": clips})

    quotes = []
    for path in sorted((base / "quotes").glob("*.json")):
        try:
            quotes.append({**read_json(path), "quote_id": path.stem})
        except (OSError, ValueError):
            continue
    write_csv(base / "quote-bank.csv", quotes, (
        "quote_id", "person_id", "speaker", "text", "context", "source_title",
        "source_url", "source_location", "status", "reuse_status", "verified_by",
    ))
    write_csv(base / "source-register.csv", quotes, (
        "quote_id", "source_title", "publisher", "source_url", "source_location",
        "source_date", "source_type", "verified_by",
    ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("show_dir", type=Path)
    args = parser.parse_args()
    root = args.show_dir / "carousels"
    originals = args.show_dir / "_originals"
    (root / "inputs").mkdir(parents=True, exist_ok=True)
    (root / "knowledge-base" / "quotes").mkdir(parents=True, exist_ok=True)
    counts = {}
    records = []
    failed = False
    clips = {}
    for path in sorted(originals.iterdir()) if originals.is_dir() else []:
        if path.is_file() and path.suffix.lower() in {".mp4", ".mov", ".m4v"}:
            clips.setdefault(path.stem, []).append(path)
    for matching in clips.values():
        clip = matching[0]
        try:
            if len(matching) > 1:
                raise ValueError("Multiple originals share this filename stem. Rename to unique stems.")
            status = build(clip, root)
        except (OSError, ValueError, TypeError) as error:
            status = "INVALID_INPUT"
            failed = True
            write_json(root / "knowledge-base" / "clips" / f"{clip.stem}.json",
                       {"clip_id": clip.stem, "filename": clip.name, "status": status,
                        "action": str(error), "packages": []})
        counts[status] = counts.get(status, 0) + 1
        records.append(read_json(root / "knowledge-base" / "clips" / f"{clip.stem}.json"))
    publish_indexes(root / "knowledge-base", records)
    write_json(root / "run-status.json", counts)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())

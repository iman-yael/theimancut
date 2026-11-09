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
    person = profile["real_person"]
    character = profile["character"]
    source = f'{quote["source_title"]} · {quote["source_location"]}'
    slides = [
        (f"{person}\nIN THEIR OWN WORDS", ""),
        ("THE PERSON AND THE ROLE",
         f'{person} is the historical subject.\n{profile["performer"]} plays {character} in The Greatest.'),
        ("IN THEIR OWN WORDS", f'“{quote["text"]}”\n{quote["speaker"]}\n{source}'),
        ("THE CONTEXT", quote["context"]),
        ("THE SCENE", f'{profile["scene_context"]}\n{profile["clip_connection"]}'),
    ]
    if profile.get("approved_take"):
        slides.append(("THE IMAN CUT'S TAKE", profile["approved_take"]))
    slides.append(("THE SOURCE", f"{source}\nWhat detail stood out to you?"))
    slug = re.sub(r"[^a-z0-9]+", "-", character.lower()).strip("-") or "character"
    key = json.dumps([clip_id, profile, quote, PLATFORMS, 1], sort_keys=True)
    deck_id = hashlib.sha256(key.encode()).hexdigest()[:16]
    outputs = []
    for platform, (height, kind) in PLATFORMS.items():
        directory = root / platform / slug / deck_id
        names = ["01_cover.png"] + [f"{n:02d}_slide.png" for n in range(2, len(slides) + 1)]
        sidecars = ("caption.txt", "alt-text.txt", "sources.md", "manifest.json")
        if not all((directory / name).is_file() for name in [*names, *sidecars]):
            directory.mkdir(parents=True, exist_ok=True)
            for i, ((title, body), filename) in enumerate(zip(slides, names), 1):
                render(directory / filename, height, title, body, i, len(slides))
            caption = (f"{person} in their own words. Swipe for the context and how it connects "
                       f"to The Greatest.\n{profile['performer']} as {character}.\n"
                       f"Quote source: {source} — {quote['source_url']}\nWhat detail stood out to you?")
            (directory / "caption.txt").write_text(caption + "\n", encoding="utf-8")
            (directory / "alt-text.txt").write_text(
                "\n".join(f"{i}. {title} — {body}".replace("\n", " ")
                          for i, (title, body) in enumerate(slides, 1)) + "\n", encoding="utf-8"
            )
            (directory / "sources.md").write_text(
                f'# Sources\n\n- Quote: {source}\n- URL: {quote["source_url"]}\n'
                f'- Speaker: {person}\n- Verified by: {quote["verified_by"]}\n'
                f'- Clip: {clip_id}\n- Cast and clip references: '
                f'{profile.get("clip_source", "See clip record")}\n', encoding="utf-8"
            )
            write_json(directory / "manifest.json", {
                "clip_id": clip_id, "quote_id": quote_id, "deck_id": deck_id,
                "format": kind, "dimensions": [1080, height], "slides": names,
                "status": "READY_FOR_REVIEW", "platform": platform,
                "layout": [{"title": title, "body": body} for title, body in slides],
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

"""Footage registration, indexing, timelines and exports."""
from __future__ import annotations

import json
import subprocess
from fractions import Fraction
from pathlib import Path

from .core import Catalog, sha256_file, to_ticks, TICKS_PER_SECOND, union_length


def ffprobe(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def register_asset(cat: Catalog, path: Path, role: str = "original", edition: str | None = None,
                   parent: str | None = None, transform_note: str | None = None, ingestion: str | None = None) -> str:
    """Idempotent by checksum. Never modifies the file."""
    digest = sha256_file(path)
    hit = cat.one("SELECT uuid FROM asset WHERE sha256=?", digest)
    if hit:
        return hit[0]
    info = ffprobe(path)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), {})
    fr = v.get("r_frame_rate", "0/1").split("/")
    afr = v.get("avg_frame_rate", "0/1")
    dur = Fraction(info["format"].get("duration", "0"))
    audio = [{"index": s["index"], "codec": s.get("codec_name"), "channels": s.get("channels"), "layout": s.get("channel_layout"),
              "sample_rate": s.get("sample_rate"), "language": s.get("tags", {}).get("language")}
             for s in info["streams"] if s["codec_type"] == "audio"]
    subs = [{"index": s["index"], "codec": s.get("codec_name"), "language": s.get("tags", {}).get("language")}
            for s in info["streams"] if s["codec_type"] == "subtitle"]
    trc = v.get("color_transfer")
    u = cat.create("asset", dict(
        original_filename=path.name, storage_uri=str(path.resolve()), sha256=digest, size_bytes=path.stat().st_size,
        media_type=info["format"].get("format_name"),
        duration_ticks=int(dur * TICKS_PER_SECOND),   # container duration; display/coverage only
        width=v.get("width"), height=v.get("height"), video_codec=v.get("codec_name"),
        bitrate=int(info["format"].get("bit_rate", 0)) or None,
        fps_num=int(fr[0]) if v else None, fps_den=int(fr[1]) if v else None,
        is_vfr=int(v.get("r_frame_rate") != afr) if v else None,
        color_primaries=v.get("color_primaries"), color_transfer=trc, color_matrix=v.get("color_space"),
        hdr={"smpte2084": "PQ", "arib-std-b67": "HLG"}.get(trc, "SDR" if trc else "untagged"),
        audio_json=json.dumps(audio), subtitle_json=json.dumps(subs), edition_uuid=edition,
        parent_asset_uuid=parent, transform_note=transform_note, asset_role=role), ingestion)
    if parent:
        cat.depends(u, parent, kind="derived_from")
    return u


def new_annotation_set(cat, asset, counting_method="CM-1"):
    prev = cat.q("SELECT uuid, version FROM annotation_set WHERE asset_uuid=? ORDER BY version DESC", asset)
    version = (prev[0][1] + 1) if prev else 1
    for (u, _) in prev:
        if cat.one("SELECT status FROM annotation_set WHERE uuid=?", u)[0] == "active":
            cat.update(u, {"status": "superseded"}, note="new annotation version")
    return cat.create("annotation_set", dict(asset_uuid=asset, version=version, status="active", counting_method=counting_method))


def add_scene(cat, ann, start, end, **kw) -> str:
    return cat.create("scene", dict(annotation_set_uuid=ann, start_ticks=to_ticks(start), end_ticks=to_ticks(end), **kw))


def add_appearance(cat, character, ann, start, end, mode, identity_status, scene=None, shot=None, portrayal=None,
                   review_status="proposed", evidence=None) -> str:
    u = cat.create("appearance", dict(character_uuid=character, portrayal_uuid=portrayal, annotation_set_uuid=ann,
                                      scene_uuid=scene, shot_uuid=shot, start_ticks=to_ticks(start), end_ticks=to_ticks(end),
                                      mode=mode, identity_status=identity_status, review_status=review_status, evidence=evidence))
    cat.depends(u, character, portrayal)
    return u


def add_timeline_item(cat, timeline, seq, track, kind, tl_start, tl_end, source=None, src_start=None, src_end=None, **kw) -> str:
    u = cat.create("timeline_item", dict(timeline_uuid=timeline, seq=seq, track=track, kind=kind, source_uuid=source,
                                         src_start=None if src_start is None else to_ticks(src_start),
                                         src_end=None if src_end is None else to_ticks(src_end),
                                         tl_start=to_ticks(tl_start), tl_end=to_ticks(tl_end), **kw))
    cat.depends(timeline, u, kind="contains")
    if source:
        cat.depends(u, source, kind="uses_source")
    return u


def used_intervals(cat, asset) -> list[tuple]:
    """All source intervals of an asset already used in any timeline (direct asset refs or via scenes)."""
    rows = cat.q("SELECT ti.src_start, ti.src_end, e.display_id FROM timeline_item ti JOIN entity e ON e.uuid=ti.timeline_uuid "
                 "WHERE ti.source_uuid=? AND ti.src_start IS NOT NULL", asset)
    return [(r[0], r[1], r[2]) for r in rows]


def reuse_fraction(cat, asset) -> float:
    a = cat.one("SELECT duration_ticks FROM asset WHERE uuid=?", asset)[0]
    return union_length([(s, e) for s, e, _ in used_intervals(cat, asset)]) / a if a else 0.0


def record_export(cat, project, timeline, path: Path, platform, variant, language="EN", take=None, subtitle_ref=None, settings=None) -> str:
    info = ffprobe(path)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    u = cat.create("export", dict(project_uuid=project, timeline_uuid=timeline, timeline_rev=cat.rev(timeline) if timeline else None,
                                  take_uuid=take, platform=platform, width=v["width"], height=v["height"], variant=variant,
                                  language=language, subtitle_ref=subtitle_ref, settings_json=json.dumps(settings or {}),
                                  file_uri=str(path.resolve()), sha256=sha256_file(path)))
    cat.depends(u, timeline, take, kind="rendered_from")
    return u


def record_take(cat, script, voice, audio_path: Path | None, origin: str, settings: dict | None = None) -> str:
    """A narration take pinned to the exact script revision. Never overwrites: each take is a new record.
    Refuses unless the voice profile is approved (consent on file)."""
    status = cat.one("SELECT status FROM voice WHERE uuid=?", voice)[0]
    if status != "approved":
        raise PermissionError(f"voice {cat.did(voice)} status is '{status}', not 'approved'")
    audio = register_asset(cat, audio_path, role="audio") if audio_path else None
    dur = cat.one("SELECT duration_ticks FROM asset WHERE uuid=?", audio)[0] if audio else None
    u = cat.create("take", dict(script_uuid=script, script_rev=cat.rev(script), voice_uuid=voice, origin=origin,
                                settings_json=json.dumps(settings or {}), audio_asset_uuid=audio, duration_ticks=dur))
    cat.depends(u, script, voice, audio)
    return u


def take_is_current(cat, take) -> bool:
    script, rev = cat.one("SELECT script_uuid, script_rev FROM take WHERE uuid=?", take)
    return cat.rev(script) == rev

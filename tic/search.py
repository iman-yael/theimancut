"""Retrieval queries over the authoritative records (no index required; any future search index
must link back to these UUIDs)."""
from __future__ import annotations

from datetime import date

from .core import Catalog


def confirmed_appearances(cat: Catalog, character: str):
    return cat.q("SELECT a.*, e.display_id FROM appearance a JOIN entity e ON e.uuid=a.uuid WHERE a.character_uuid=? "
                 "AND a.identity_status='Confirmed' AND a.review_status='human_confirmed' ORDER BY a.annotation_set_uuid, a.start_ticks", character)


def portrayals_of_historical_person(cat: Catalog, person: str):
    """Every character (any work) linked to a real person, with its performers."""
    return cat.q("SELECT w.title, c.credited_name, hl.link_type, pe.name AS performer FROM historical_link hl "
                 "JOIN character c ON c.uuid=hl.character_uuid JOIN work w ON w.uuid=c.work_uuid "
                 "LEFT JOIN portrayal p ON p.character_uuid=c.uuid LEFT JOIN person pe ON pe.uuid=p.person_uuid WHERE hl.person_uuid=?", person)


def scenes_with_both(cat: Catalog, a: str, b: str, confirmed_only=True):
    cond = "AND x.identity_status='Confirmed' AND x.review_status='human_confirmed'" if confirmed_only else ""
    return cat.q(f"SELECT DISTINCT s.uuid FROM scene s JOIN appearance x ON x.scene_uuid=s.uuid AND x.character_uuid=? {cond} "
                 f"JOIN appearance y ON y.scene_uuid=s.uuid AND y.character_uuid=? "
                 f"{cond.replace('x.', 'y.')}", a, b)


def unused_scenes_for_pair(cat: Catalog, a: str, b: str):
    """Scenes with both characters whose interval has not been used in any timeline."""
    out = []
    for (s,) in scenes_with_both(cat, a, b):
        sc = cat.one("SELECT s.start_ticks, s.end_ticks, an.asset_uuid FROM scene s JOIN annotation_set an ON an.uuid=s.annotation_set_uuid WHERE s.uuid=?", s)
        used = cat.one("SELECT 1 FROM timeline_item WHERE (source_uuid=? OR source_uuid=?) AND src_start < ? AND src_end > ?",
                       s, sc[2], sc[1], sc[0])
        if not used:
            out.append(s)
    return out


def assets_with_permission(cat: Catalog, platform: str | None = None, on: str | None = None):
    on = on or date.today().isoformat()
    rows = cat.q("SELECT r.covers_uuid, r.platforms_json, r.expires FROM rights r WHERE r.status='Documented permission' AND r.asset_class='footage' "
                 "AND (r.starts IS NULL OR r.starts<=?) AND (r.expires IS NULL OR r.expires>=?)", on, on)
    return [r[0] for r in rows if platform is None or platform in (r[1] or "")]


def projects_affected_by(cat: Catalog, upstream: str):
    """All downstream records (transitively) of a corrected record, grouped by type."""
    seen, frontier = set(), [upstream]
    while frontier:
        nxt = []
        for n in frontier:
            for (d,) in cat.q("SELECT downstream_uuid FROM dependency WHERE upstream_uuid=?", n):
                if d not in seen:
                    seen.add(d); nxt.append(d)
        frontier = nxt
    out = {}
    for u in seen:
        out.setdefault(cat.type_of(u), []).append(cat.did(u))
    return out


def exports_with_expired_rights(cat: Catalog, asset_class="music", on: str | None = None):
    """Exports depending (transitively) on anything covered by an expired rights record of this class."""
    on = on or date.today().isoformat()
    hits = {}
    for rid, covers in cat.q("SELECT uuid, covers_uuid FROM rights WHERE asset_class=? AND expires IS NOT NULL AND expires<?", asset_class, on):
        if covers:
            for e in projects_affected_by(cat, covers).get("export", []):
                hits.setdefault(e, []).append(cat.did(rid))
    return hits


def posts_about_actor(cat: Catalog, person: str):
    """Posts whose project focuses on any character this person portrays, across all works."""
    return cat.q("SELECT DISTINCT po.uuid, w.title FROM post po JOIN export ex ON ex.uuid=po.export_uuid JOIN project pr ON pr.uuid=ex.project_uuid "
                 "JOIN concept co ON co.uuid=pr.concept_uuid JOIN dependency d ON d.downstream_uuid=co.uuid "
                 "JOIN portrayal p ON p.character_uuid=d.upstream_uuid JOIN character c ON c.uuid=p.character_uuid JOIN work w ON w.uuid=c.work_uuid "
                 "WHERE p.person_uuid=?", person)


def counts_fully_reviewed_only(cat: Catalog, character: str):
    """Statistics only from annotation sets whose coverage spans the whole asset."""
    return {k: v for k, v in cat.screen_time(character).items() if not v["provisional"]}


def post_lineage(cat: Catalog, post: str):
    """A post and everything it was built from (walks dependencies upstream)."""
    seen, frontier = set(), [cat.one("SELECT export_uuid FROM post WHERE uuid=?", post)[0]]
    while frontier:
        nxt = []
        for n in frontier:
            for (u,) in cat.q("SELECT upstream_uuid FROM dependency WHERE downstream_uuid=?", n):
                if u not in seen:
                    seen.add(u); nxt.append(u)
        frontier = nxt
    out = {}
    for u in seen:
        out.setdefault(cat.type_of(u), []).append(cat.did(u))
    return out


def top_posts(cat: Catalog, metric="views", platform=None, limit=10):
    """Latest observed value per post (observed metrics only; nulls stay null)."""
    sql = ("SELECT p.uuid, m.value, m.observed_at FROM metric m JOIN post p ON p.uuid=m.post_uuid JOIN account a ON a.uuid=p.account_uuid "
           "WHERE m.name=? AND m.kind='observed' AND m.value IS NOT NULL " + ("AND a.platform=? " if platform else "") +
           "AND m.observed_at=(SELECT max(observed_at) FROM metric WHERE post_uuid=m.post_uuid AND name=m.name AND kind='observed') "
           "ORDER BY m.value DESC LIMIT ?")
    return cat.q(sql, metric, *([platform] if platform else []), limit)

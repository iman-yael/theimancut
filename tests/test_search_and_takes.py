"""Search/retrieval queries, narration takes, packaging lineage."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.test_core import Base  # noqa: E402
from tic import production, search  # noqa: E402
from tic.core import to_ticks  # noqa: E402


class TestSearch(Base):
    def setUp(self):
        super().setUp()
        c = self.cat
        self.a = c.create("character", dict(work_uuid=self.work, credited_name="Mother", norm_name="mother"))
        self.b = c.create("character", dict(work_uuid=self.work, credited_name="Son", norm_name="son"))
        self.actor = c.create("person", dict(name="Actor A", norm_name="actor a"))
        self.real = c.create("person", dict(name="Real Mother", norm_name="real mother"))
        c.create("portrayal", dict(character_uuid=self.a, person_uuid=self.actor))
        c.create("historical_link", dict(character_uuid=self.a, person_uuid=self.real, link_type="depicts"))
        self.asset = c.create("asset", dict(original_filename="e1.mov", storage_uri="/m", sha256="s1", size_bytes=1, duration_ticks=to_ticks(60)))
        self.ann = production.new_annotation_set(c, self.asset)
        self.s1 = production.add_scene(c, self.ann, 0, 10)
        self.s2 = production.add_scene(c, self.ann, 10, 20)
        for s, (st, en) in ((self.s1, (0, 10)), (self.s2, (10, 20))):
            production.add_appearance(c, self.a, self.ann, st, en, "visible", "Confirmed", scene=s, review_status="human_confirmed")
            production.add_appearance(c, self.b, self.ann, st, en, "visible", "Confirmed", scene=s, review_status="human_confirmed")

    def test_queries(self):
        c = self.cat
        self.assertEqual(len(search.confirmed_appearances(c, self.a)), 2)
        self.assertEqual(len(search.portrayals_of_historical_person(c, self.real)), 1)
        self.assertEqual(len(search.scenes_with_both(c, self.a, self.b)), 2)
        proj = c.create("project", dict(title="P", slug="p"))
        tl = c.create("timeline", dict(project_uuid=proj, approach="performance_led"))
        production.add_timeline_item(c, tl, 1, "V1", "source", 0, 5, source=self.asset, src_start=2, src_end=7)
        self.assertEqual(search.unused_scenes_for_pair(c, self.a, self.b), [self.s2])   # s1 interval already used
        self.assertEqual(search.counts_fully_reviewed_only(c, self.a), {})            # no full coverage → nothing citable
        c.db.execute("INSERT INTO coverage VALUES (?,?,?,?,?)", (self.ann, 0, to_ticks(60), "t", "now"))
        self.assertEqual(list(search.counts_fully_reviewed_only(c, self.a).values())[0]["visible_ticks"], to_ticks(20))
        # rights: expired music on an asset used by an export
        music = c.create("asset", dict(original_filename="m.wav", storage_uri="/m2", sha256="s2", size_bytes=1))
        production.add_timeline_item(c, tl, 2, "A2", "music", 0, 5, source=music)
        exp = c.create("export", dict(project_uuid=proj, platform="IG", width=1080, height=1920, variant="captioned", language="EN", file_uri="/e", sha256="e"))
        c.depends(exp, tl)
        c.create("rights", dict(covers_uuid=music, asset_description="track", asset_class="music", status="Documented permission", expires="2020-01-01"))
        self.assertIn(c.did(exp), search.exports_with_expired_rights(c, "music"))
        self.assertIn("export", search.projects_affected_by(c, music))
        # post lineage + metrics (null stays null)
        acc = c.create("account", dict(platform="IG", handle=None))
        rev = c.review(exp, "publication", "approved", "iman")
        post = c.create("post", dict(account_uuid=acc, export_uuid=exp, approval_review_uuid=rev))
        c.create("metric", dict(post_uuid=post, observed_at="2026-01-02T00:00:00Z", name="views", value=None, kind="observed"))
        c.create("metric", dict(post_uuid=post, observed_at="2026-01-01T00:00:00Z", name="views", value=100, kind="observed"))
        self.assertEqual(search.top_posts(c), [])          # latest observation is unknown (null), not zero, not stale 100
        self.assertIn("timeline", search.post_lineage(c, post))


class TestTakes(Base):
    def test_take_pinned_to_script_rev(self):
        c = self.cat
        proj = c.create("project", dict(title="P", slug="p"))
        scr = c.create("script", dict(project_uuid=proj, approach="narrated", body_json="[]"))
        voice = c.create("voice", dict(owner="Owner", kind="recorded"))          # default status not_supplied
        with self.assertRaises(PermissionError):
            production.record_take(c, scr, voice, None, "recording")
        c.update(voice, {"status": "approved", "consent_ref": "doc-1"})
        wav = self.d / "vo.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", "1", str(wav)], check=True)
        t1 = production.record_take(c, scr, voice, wav, "recording")
        self.assertTrue(production.take_is_current(c, t1))
        c.update(scr, {"body_json": '["edited"]'})
        self.assertFalse(production.take_is_current(c, t1))             # script changed → take outdated
        self.assertTrue(c.stale(t1))
        t2 = production.record_take(c, scr, voice, None, "recording")
        self.assertNotEqual(t1, t2)                                     # new version, old take kept
        self.assertEqual(c.one("SELECT count(*) FROM take")[0], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)

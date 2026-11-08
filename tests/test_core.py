"""Validation suite: duplicate ingestion, referential integrity, exact timing, versioned approvals,
change propagation, blank-field protection, merge redirects, backup/restore. Uses a temporary DB and
synthetic media only."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tic.core import Catalog, to_ticks, frames_to_ticks, union_length, fmt_ticks  # noqa: E402
from tic import intake, production  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        intake.INTAKE_DIR = self.d / "intake"
        self.cat = Catalog(self.d / "t.sqlite", actor="test")
        self.work = self.cat.create("work", dict(title="Test Work", work_type="limited_series"))

    def tearDown(self):
        self.cat.db.close()
        self.tmp.cleanup()

    def tsv(self, name, rows):
        p = self.d / name
        p.write_text("#order\tnm\tactor\tcharacters\tnote\teps\n" + "\n".join("\t".join(r) for r in rows) + "\n")
        return p


class TestTiming(Base):
    def test_exact_ticks(self):
        self.assertEqual(to_ticks("00:00:01.5"), 360000)
        self.assertEqual(frames_to_ticks(1, 24000, 1001), 10010)       # 23.976 fps frame
        self.assertEqual(frames_to_ticks(1, 30000, 1001), 8008)        # 29.97 fps frame
        self.assertEqual(to_ticks("1/48000"), 5)                        # one 48 kHz sample
        with self.assertRaises(ValueError):
            to_ticks("0.0000001")                                       # refuses silent rounding
        self.assertEqual(fmt_ticks(to_ticks("01:02:03.250")), "01:02:03.250")

    def test_union_no_double_count(self):
        self.assertEqual(union_length([(0, 10), (5, 15), (20, 30), (30, 35)]), 30)  # half-open, touching merges

    def test_interval_constraint(self):
        ann = self._ann()
        with self.assertRaises(Exception):
            production.add_scene(self.cat, ann, 5, 5)                  # empty interval rejected

    def _ann(self):
        a = self.cat.create("asset", dict(original_filename="x.mp4", storage_uri="/x", sha256="abc", size_bytes=1, duration_ticks=to_ticks(100)))
        return production.new_annotation_set(self.cat, a)


class TestIntake(Base):
    def test_idempotent_and_matching(self):
        p = self.tsv("cast.tsv", [["1", "nm1", "Actor One", "Hero / Alias Name", "", "8"],
                                  ["2", "nm2", "Actor Two", "Howard Smith", "", "1"],
                                  ["3", "nm3", "Actor Three", "Howard", "", "1"],
                                  ["4", "nm4", "Kid Actor", "Young Hero", "", "1"]])
        r1 = intake.ingest_cast(self.cat, p, self.work, "test", "V1")
        n_people = self.cat.one("SELECT count(*) FROM person")[0]
        r2 = intake.ingest_cast(self.cat, p, self.work, "test", "V1")
        self.assertTrue(r2.get("idempotent_noop"))
        self.assertEqual(n_people, self.cat.one("SELECT count(*) FROM person")[0])
        kinds = [u["kind"] for u in r1["unresolved"]]
        self.assertIn("ambiguous_match", kinds)                         # "Howard" queued, not created
        self.assertIsNone(self.cat.one("SELECT 1 FROM character WHERE norm_name='howard'"))
        young = self.cat.one("SELECT age_portrayal FROM portrayal p JOIN person pe ON pe.uuid=p.person_uuid WHERE pe.name='Kid Actor'")
        self.assertEqual(young[0], "young")                             # linked to same character identity

    def test_blank_does_not_erase_and_revisions_kept(self):
        p = self.cat.create("person", dict(name="A", norm_name="a", born="1950"))
        self.cat.update(p, {"born": ""})
        self.assertEqual(self.cat.one("SELECT born FROM person WHERE uuid=?", p)[0], "1950")
        self.cat.update(p, {"born": "1951"}, note="correction")
        revs = self.cat.q("SELECT rev FROM revision WHERE entity_uuid=? ORDER BY rev", p)
        self.assertEqual([r[0] for r in revs], [1, 2])


class TestApprovalsAndPropagation(Base):
    def test_versioned_approval_and_stale(self):
        c = self.cat.create("character", dict(work_uuid=self.work, credited_name="X", norm_name="x"))
        proj = self.cat.create("project", dict(title="P", slug="p"))
        scr = self.cat.create("script", dict(project_uuid=proj, approach="narrated", body_json="{}"))
        self.cat.depends(scr, c)
        exp = self.cat.create("export", dict(project_uuid=proj, platform="IG", width=1080, height=1920, variant="captioned",
                                             language="EN", file_uri="/e", sha256="e1"))
        self.cat.depends(exp, scr)
        self.cat.review(scr, "editorial", "approved", "iman")
        self.assertTrue(self.cat.is_approved(scr, "editorial"))
        self.cat.update(scr, {"body_json": '{"v":2}'})
        self.assertFalse(self.cat.is_approved(scr, "editorial"))       # edit invalidates approval
        self.cat.update(c, {"credited_name": "X2", "norm_name": "x2"}, note="name correction")
        self.assertTrue(self.cat.stale(exp))                           # flagged two levels down
        self.assertEqual(self.cat.one("SELECT sha256 FROM export WHERE uuid=?", exp)[0], "e1")  # not modified

    def test_merge_redirect(self):
        a = self.cat.create("person", dict(name="Dup", norm_name="dup"))
        b = self.cat.create("person", dict(name="Keep", norm_name="keep"))
        self.cat.merge(a, b, "duplicate")
        self.assertEqual(self.cat.resolve(self.cat.did(a)), b)
        self.assertIsNotNone(self.cat.one("SELECT 1 FROM entity WHERE uuid=?", a))   # never deleted


class TestIntegrityAndBackup(Base):
    def test_fk_enforced(self):
        with self.assertRaises(Exception):
            self.cat.create("portrayal", dict(character_uuid="nope", person_uuid="nope"))

    def test_backup_restore(self):
        self.cat.create("person", dict(name="B", norm_name="b"))
        self.cat.commit()
        bk = self.cat.backup(self.d / "bk.sqlite")
        res = self.cat.verify_restore(bk, self.d / "restored.sqlite")
        self.assertTrue(res["ok"], res)


class TestMediaWorkflow(Base):
    def test_asset_scene_appearance_timeline_export(self):
        src = self.d / "synthetic.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=24000/1001:duration=4",
                        "-f", "lavfi", "-i", "sine=duration=4", "-c:v", "libx264", "-c:a", "aac", "-shortest", str(src)], check=True)
        a = production.register_asset(self.cat, src, role="test")
        self.assertEqual(a, production.register_asset(self.cat, src, role="test"))   # checksum idempotent
        row = self.cat.one("SELECT fps_num, fps_den, is_vfr FROM asset WHERE uuid=?", a)
        self.assertEqual((row[0], row[1], row[2]), (24000, 1001, 0))
        c = self.cat.create("character", dict(work_uuid=self.work, credited_name="Hero", norm_name="hero"))
        ann = production.new_annotation_set(self.cat, a)
        sc = production.add_scene(self.cat, ann, 0, 3)
        production.add_appearance(self.cat, c, ann, "0.5", "2", "visible", "Confirmed", scene=sc, review_status="human_confirmed")
        production.add_appearance(self.cat, c, ann, "1.5", "3", "visible", "Confirmed", scene=sc, review_status="human_confirmed")
        production.add_appearance(self.cat, c, ann, "3", "3.5", "mention", "Confirmed", review_status="human_confirmed")
        self.cat.db.execute("INSERT INTO coverage VALUES (?,?,?,?,?)", (ann, 0, to_ticks(2), "test", "now"))
        st = list(self.cat.screen_time(c).values())[0]
        self.assertEqual(st["visible_ticks"], to_ticks("2.5"))         # union of 0.5–2 and 1.5–3; mention excluded
        self.assertTrue(st["provisional"])                             # coverage incomplete
        proj = self.cat.create("project", dict(title="P", slug="p"))
        tl = self.cat.create("timeline", dict(project_uuid=proj, approach="performance_led"))
        production.add_timeline_item(self.cat, tl, 1, "V1", "source", 0, 1, source=a, src_start="0.5", src_end="1.5", chrono_order=1)
        self.assertAlmostEqual(production.reuse_fraction(self.cat, a), 0.25, places=3)
        exp = production.record_export(self.cat, proj, tl, src, "IG", "clean")
        self.assertEqual(self.cat.one("SELECT timeline_rev FROM export WHERE uuid=?", exp)[0], self.cat.rev(tl))


if __name__ == "__main__":
    unittest.main(verbosity=2)

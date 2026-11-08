# Handoff / checkpoint (2026-11-08, stage: Pilot proposed)

**Complete and verified**
- Catalog system: `python3 -m unittest tests.test_core tests.test_search_and_takes` → 12/12 pass. Search queries (§16), controlled tags (migration 004), and narration takes pinned to script revisions are also covered. Covers duplicate ingestion, foreign keys, exact ticks, union screen time, versioned approvals, stale propagation, merges, blank-safe updates and backup/restore.
- Live catalog: 4 intake batches · 135 characters · 161 people · 136 portrayals · 20 claims · 18 sources · 20 open review items. A verified backup is in `catalog/backups/`.
- Generated documents: `works/WRK-000001_the-greatest/` (directory, 135 character sheets, 8 installment docs) and `docs/generated/` (review queue, rights register, data dictionary).
- Brand style sample, rendered on a **synthetic test pattern** (not show footage): `brand/style_sample/`. Watermark A and B; dialogue, narration and label styles. QC fails only on the deliberate [SAMPLE] markers.
- Pilot proposal: `projects/PRJ-000001_BirdClay/`. Experiment batch v1: `projects/EXPERIMENT_BATCH_v1.md`. Worked example: `docs/WORKED_EXAMPLE.md`. Hook library: `analytics/TIC_HOOK_LIBRARY.csv`.

**Not done (and not claimed)**
- No footage watched, indexed, or edited. No headshots obtained. No identity confirmed on screen. No narration generated or timed aloud. No post published, scheduled, or monitored.

**Next executable task**
On Iman's reply: record approvals (`cat.review(...)`), resolve the queue items she decides, then re-run `python3 -m tic.cli docs`. When an authorized source file arrives: `pipeline/source_report.sh FILE`, then `production.register_asset`, then index.

**Commands**
`python3 works/seed_the_greatest.py` (idempotent) · `python3 projects/pilot_PRJ-000001_bird_clay.py` · `python3 -m tic.cli docs|backup|status`

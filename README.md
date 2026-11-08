# The Iman Cut (theimancut)

Film & TV. **Film, character, performance and history, by Iman Yael.** Watermark text: `THE IMAN CUT`.

This repository holds the research, editorial plans, policies and the small production system behind The Iman Cut. The first project is Prime Video's *The Greatest* (2026, about Muhammad Ali). The system is title-agnostic: shows, movies and documentaries can be added later without starting over.

> **No show footage, audio or headshots are stored here.** Media lives outside the repository and is referenced by checksum. Nothing in this repo has been published.

## Start here
| File | What it is |
|---|---|
| [PROJECT_BRIEF.md](PROJECT_BRIEF.md) | Current decisions, assets, settings, conflicts, open questions |
| [HANDOFF.md](HANDOFF.md) · [TASK_BOARD.md](TASK_BOARD.md) | What's done, what's blocked, next executable task |
| [DECISION_LOG.md](DECISION_LOG.md) · [CORRECTIONS_LOG.md](CORRECTIONS_LOG.md) | Why things are the way they are |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | Consolidated brief: everything Iman asked for |
| [docs/LOCAL_SESSION_HANDOFF_2026-11-08.md](docs/LOCAL_SESSION_HANDOFF_2026-11-08.md) | State of the work done on Iman's Mac (Bird Clay cut v03/v05, Clipper app) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [docs/WORKED_EXAMPLE.md](docs/WORKED_EXAMPLE.md) | Data model, ID/versioning policy, intake workflow |
| [docs/generated/](docs/generated/) | Review queue, rights register, data dictionary (generated from the DB) |

## The Greatest (WRK-000001)
- [Character directory](works/WRK-000001_the-greatest/CHARACTER_DIRECTORY.md): 135 credited characters with a sheet each in [characters/](works/WRK-000001_the-greatest/characters/); priority sheets are CHR-000001 to CHR-000006.
- [Installment docs](works/WRK-000001_the-greatest/installments/) for the 8 episodes (footage review pending).
- Projects: [PRJ-000001 Bird Clay portrait](projects/PRJ-000001_BirdClay/) · [PRJ-000002 official-trailer in-app remixes](projects/PRJ-000002_TrailerRemix/) · [Experiment batch v1](projects/EXPERIMENT_BATCH_v1.md)

## Policies
[Editorial, sensitivity, moderation and corrections](policies/EDITORIAL_SENSITIVITY_MODERATION.md) · [QC checklist](policies/QC_CHECKLIST.md)

## System (optional; Python 3 + SQLite + ffmpeg)
```
python3 -m unittest tests.test_core tests.test_search_and_takes   # validation suite
python3 works/seed_the_greatest.py                                # idempotent seed
python3 -m tic.cli docs | backup | status                         # regenerate docs, verified backup, counts
pipeline/render.sh -h                                             # 9:16 / 4:5 renders with captions, labels, watermark
```
`catalog/catalog.sqlite` is the source of truth; every `.md` under `works/`, `docs/generated/` and `intake/ING-*` is generated from it. CSV/TSV data files have Markdown twins for reading.

## Ground rules
Footage only from authorized, unencrypted sources with documented permission. No DRM/HDCP circumvention, no pirated or screen-captured sources for publication. Actor ≠ character ≠ historical person. Interpretation is labelled as interpretation; history is cited. Nothing is published, scheduled or bought without Iman's approval.

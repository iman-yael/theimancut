# Worked example: Odessa 'Bird' Clay through every layer

> Generated 2026-11-08T19:21:42Z from the live catalog. **Known** = stored, sourced data. **Placeholder / pending** = deliberately empty; never filled with guesses.

| Layer | Record | Display ID(s) | Known | Placeholder / pending |
|---|---|---|---|---|
| WRK | Work | WRK-000001 | The Greatest · limited_series · IMDb tt15715850 | — |
| SEA/INS | Season 1 + 8 episodes | SEA-000001, INS-000001…000008 | Labels S01E01…S01E08 (labels, not keys) | Episode titles (claims conflicting/single-source), synopses |
| EDT/AST | Edition / source asset | — | — | **No edition or asset registered:** no authorized file exists |
| ING | Ingestion batches | ING-000001 (legacy_ids), ING-000002 (cast_list), ING-000003 (crew_list), ING-000004 (cast_list) | Originals preserved read-only in intake/ING-*/ | — |
| PER | Actor | PER-000003 | Dana Gourrier · IMDb nm4158239 | Headshot (none); actor biography (unsourced) |
| CHR | Character | CHR-000003 | Exact credit `Odessa 'Bird' Clay`; aliases Odessa Grady Clay, Bird (v0, unchecked) | Wardrobe/continuity, arc, moments |
| POR | Portrayal | POR-000003 | primary · credited · V2 · 8 IMDb credited episodes (not appearances) | On-screen identity: Unresolved |
| REL | Relationships | REL-000001, REL-000002, REL-000003 | mother of CHR-000001, CHR-000004; wife of CHR-000002 | Source claims for history |
| CLM/SRC | Claims | CLM-000004, 000010, 000011 | Casting supported (IMDb + Deadline); praise = critics' opinion | CLM-000010 historical fact UNCHECKED |
| SCN/APP | Scenes/appearances | — | — | **Pending footage review** |
| CON/PRJ | Concept/project | CON-000001 / PRJ-000001 | Character portrait, status Proposed | Approval (none yet) |
| SCR | Narrated script | SCR-000001 r1 | 7 timed rows, line types labelled | All footage slots, the acting observation, the history line (blocked) |
| PKG | Packaging (IG) | PKG-000001 | 6 hooks, recommended hook, cover headline, caption draft, hypothesis | provisional=1; [ONE OBSERVATION] placeholder |
| VOC/TAK | Voice / take | VOC-000001 not_supplied / — | — | Voice asset + consent; `record_take` refuses until approved |
| EXP/PST/MET | Export / post / metrics | — | — | Nothing rendered from footage; nothing published |
| RGT | Rights | RGT-000001…000006 | Font licence documented | Footage, photos, voice, likeness, music: Unknown |

## Revision history of CHR-000003 (nothing overwritten without a snapshot)
| Rev | Changed fields | Note |
|---|---|---|
| 1 | counterpart_status, credited_name, norm_name, relationship_to_subject, work_uuid | legacy CHR-003 |
| 2 | profile_json | research profile |

## How a correction would flow (tested in `tests/`)
1. A new intake (e.g. on-screen end credits) updates POR credit_verification V2 → VC: new revision, provenance → ING.
2. `dependency` edges flag SCR, PKG and any EXP built on CHR-000003 as stale; approvals bound to older revisions become invalid.
3. Docs regenerate; approved exports and posts are **not** modified. A corrected version is prepared for approval.

# *The Greatest* Social Series: Production Package

Updated 2026-11-08. Nothing has been published or scheduled, and nothing will be until you explicitly authorize posting.

## Folders
| Folder | Contents now |
|---|---|
| `Character_Sheets/` | Master cast table, template, 12 sheets, counting rules |
| `Source_Reports/` | Prime viewing vs. editing-source guide · rights-log template · (per-file source reports once footage exists) |
| `Scene_Index/` | Scene-index and character-appearance templates |
| `Edit_Projects/` | Batch plan, presenter script, clip-candidate template, `pipeline/` scripts |
| `Review_Exports/` | QC checklist (exports land here, one subfolder per post) |
| `Approved_Exports/` | Empty. Files move here only after your approval and a passed QC. |
| `Covers/` · `Subtitles/` | Empty (filled by the scripts) |
| `Post_Copy/` | Text/caption/hashtag standards · PRES-01 copy draft |
| `Historical_Sources/` | Claim checklist template · PRES-01 sources |
| `Analytics/` | Performance tracker template (no analytics connected, no monitoring active) |
| `TG_Delivery_Manifest.csv` | One row per exported file: source TC, scene/character IDs, permission, settings, approval, QC |

## Pipeline (`Edit_Projects/pipeline/`): tested on synthetic test patterns only
| Script | Does |
|---|---|
| `source_report.sh FILE` | Measures resolution, codec, fps/VFR, bitrate, color, HDR, audio, SHA-256, and crop budget. Read-only. |
| `render.sh …` | **Refuses to run without `-p CLEARED:<rights ID>`.** HDR→SDR Rec.709 tone-map when tagged. Layouts: `x=` crop, `fit`, `split`. ID labels. Per-platform subtitle margins. H.264 High, CRF 16 capped at 20 Mbps, 30 fps CFR (duplication, no interpolation), AAC 256k/48 kHz, -14 LUFS. Outputs IG/TT/FB/YT captioned + `_CLEAN` + `.srt`, optional 4:5, a source-fps master, the logged ffmpeg commands, and manifest rows. |
| `cover.sh` | 1080×1920 cover + 1:1, 3:4, and 4:5 crop previews |
| `qc_probe.sh FILE [SRT]` | Automated technical checks + frame grid (human QC still required) |

**Test results:** 23.976 fps SDR → 30 fps CFR and a 23.976 master ✔ · PQ/BT.2020 4K test → tagged bt709 ✔ · crop, fit, split, and 4:5 rendered and visually checked ✔ · permission gate aborts ✔ · placeholder detection ✔ · `_CLEAN` copies byte-identical across platforms ✔.

**Not done:** No show footage has been edited, exported, or checked. Per-platform caption margins are **approximate house defaults**; confirm them in each app's real draft preview.

## Production tracker
| Item | Researched | Selected | Approved | Edited | Checked | Ready | Blocker |
|---|---|---|---|---|---|---|---|
| Cast verification (12) | ✅ V2 | — | — | — | ⏳ | — | End credits need footage |
| Character sheets | 🟡 | — | ⏳ you | — | — | — | Footage; history not source-checked |
| "Connie lesson" | ❌ | — | — | — | — | — | **Your answer** |
| Footage index | ❌ | — | — | — | — | — | Authorized footage |
| P1–P3 scene clips | 🟡 leads | ❌ | ❌ | ❌ | ❌ | ❌ | Footage + rights |
| P4 Gourrier / P5 Best spotlights | 🟡 | ❌ | ❌ | ❌ | ❌ | ❌ | Footage + rights |
| P6 Clay Brothers mashup | 🟡 | ❌ | ❌ | ❌ | ❌ | ❌ | Footage + rights |
| PRES-01 Bird Clay | 🟡 script + copy | ✅ | ⏳ you | ❌ | ❌ | ❌ | Presenter tool/consent; C1–C3, C5 unchecked; scene placeholders |
| Pipeline + standards | ✅ | — | ⏳ you | ✅ test | ✅ test | ✅ | — |

## Access notes
- Google Drive connector: auth failed.
- Wikipedia/TMDB/IMDb page fetches: blocked by this session's network policy.
- No avatar/voice tool, no analytics, and no verified official social handles.

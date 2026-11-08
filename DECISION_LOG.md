# Decision log

| Date | Decision | By | Why |
|---|---|---|---|
| 2026-11-08 | Brand = The Iman Cut; watermark text exactly THE IMAN CUT | Iman | Definitive brand brief |
| 2026-11-08 | SQLite + stdlib Python + ffmpeg as first stack; documents generated from the DB | Producer | Smallest working system; open formats |
| 2026-11-08 | Canonical time base 1/240000 s, [start,end) intervals | Producer | Exact for all common frame rates and 48 kHz |
| 2026-11-08 | v0 IDs CHR-001…012 preserved as CHR-000001…000012 with redirects | Producer | IDs never reused or reordered |
| 2026-11-08 | IMDb credited names adopted as `credited_name`; earlier labels kept as `previous_label` | Producer | Exact credits requested; history preserved |
| 2026-11-08 | Ambiguous credits queued, not created (e.g. "Howard", "Young Cassius") | Producer | Never guess identities |
| 2026-11-08 | Filenames `TIC_PRJ-######_…`; subtitles `_SUBTITLES.srt` | Producer | Latest brief; see PROJECT_BRIEF conflicts table |
| 2026-11-08 | Encoding: CRF 16 capped at 20 Mbps rather than fixed 16 Mbps | Producer | Fixed-bitrate undershoots on simple content; capped CRF keeps quality on busy footage |
| 2026-11-08 | IMDb allowlisted in the environment (approved); requests still 403 → no circumvention | Iman / Producer | Site blocks automated access |
| 2026-11-08 | Pilot = Bird Clay character portrait; narrated recommended | Proposed (awaits Iman) | Priority #1; strongest review consensus; can avoid graphic material |
| 2026-11-08 | Covers keep the watermark top-right; flagged because the 1:1 grid crop removes it | Proposed (awaits Iman) | Headline and face take priority in thumbnails |
| 2026-11-08 | Footage from unlicensed streaming sites (e.g. YesMovies) will not be used, indexed, or edited | Producer | Pirated source: no permission; channel strike/legal risk; malware risk |
| 2026-11-08 | Option 2 adopted: in-app remixes of the official trailer (PRJ-000002) | Iman | No download; platform-native tools only |
| 2026-11-08 | Watermark top-right (A); ON for IG/TikTok, OFF for YouTube | Iman (local session) | YouTube adds its own branding |
| 2026-11-08 | Vertical = no-crop blurred-background layout | Iman (local session) | Keep the whole frame |
| 2026-11-08 | No narration, music or generated voice for now; original audio only | Iman (local session) | Simplicity; avoids voice/music clearance |
| 2026-11-08 | Mac screen-recording cuts kept review-only until clearance is documented | Producer | Screen recording ≠ authorized source |

# Consolidated requirements (Iman Yael's briefs, 2026-11-08)

A summary, in our own words, of every instruction given across the session. Where later instructions changed earlier ones, the latest wins (see `PROJECT_BRIEF.md` → conflicts).

## Brand
- **Name:** The Iman Cut. **Creator:** Iman Yael. **Watermark text:** `THE IMAN CUT`; never "The Yael Cut".
- **Watermark:** small, restrained, top-right, ON for IG/TikTok and OFF for YouTube. It must never imply ownership or affiliation.
- **Intro line:** "I'm Iman Yael, and this is The Iman Cut." Use it sparingly.
- **Founder content:** later, labelled "Building with Iman". One relevant call to action at most.

## Content priorities
1. Standout scene clips
2. Actor spotlights
3. Character portraits, arc montages and mashups
4. Narrated breakdowns (Iman's recorded voice, or an authorized digital voice)
5. Historical deep dives on the real people

A post that reaches **1,000,000 views on one platform** triggers a proposal for a substantial deep dive. Short explainers are tested earlier.

## Honesty rules
- Never claim footage was watched, an identity confirmed, history verified, audio generated, a file rendered, or monitoring active unless it actually was.
- Never invent timestamps, quotes, appearances, search data, trends or reactions.
- Mark anything not yet checked: "Pending footage review", "provisional", "UNCHECKED".

## Characters and identity
- Stable IDs (`CHR-000001` …). Exact credited names, kept with their variations and "uncredited" labels.
- Young and adult portrayals stay on one character identity, but each performer is named separately.
- Never identify a person by face alone: use credits, dialogue, context and confirmed frames. Every on-screen match is labelled **Confirmed / Probable / Unresolved**.
- Not every character is a real person. Actor bio, character and historical bio are kept separate.
- IMDb episode counts are credited counts, not appearances.
- "Connie lesson" stays unresolved: Sonny Liston and Sonny Banks are possible matches, never auto-resolved.

## Footage index and counts
- Exact in/out times, marked file-relative or episode-relative.
- Visible appearances, voice-only appearances and mentions are recorded separately.
- Shot count, scene count and screen time are computed separately under a documented method (CM-1), and labelled provisional until coverage is complete.

## Story and editing
- Write a premise first ("What does this reveal?") and an evidence-backed arc. Don't force a redemption or a downfall; call it a portrait when that's what it is.
- Up to three angles per character, with one recommended.
- Two approaches: **performance-led** and **narrated**. Render only the selected one. (Current choice: original audio only, no narration.)
- Watch the surrounding scene before cutting. Never splice unrelated dialogue or reactions. Chronological by default.
- Timed voice-over table, with every line labelled as original dialogue, editorial interpretation, or verified history. Include pronunciation notes and a timing test aloud.

## Sensitive material
- Flag domestic violence, sexual assault, coercive control, racism and slurs, child abuse, self-harm and graphic injury, noting whether each is depicted, implied or historically documented.
- Content notes; no sensational hooks; no victim-blaming. No looped assaults, and no injury in thumbnails.
- Support resources only once verified (country, contact, hours); otherwise a VERIFY placeholder.
- Comment-moderation plan; a pinned-comment draft; compassionate replies to personal disclosures. Nothing posted or replied to without approval.

## Rights and sources
- Footage only when authorized and unencrypted. A Prime download is not an edit source.
- No DRM/HDCP circumvention and no pirated sites.
- Rights register covering footage, photos, music, voice and likeness: platforms, territories, dates, monetization and restrictions. Music permission is separate from footage permission.
- Track used source intervals so clips don't collectively reconstruct an episode.

## Exports
- Formats: 1080×1920 for IG/TT/FB/YT, optional 1080×1350 for feeds.
- Encoding: MP4 H.264, AAC 48 kHz at 256 kbps or more, 30 fps CFR plus a source-fps master, SDR Rec.709 with HDR tone-mapped.
- No stretching, interpolation or sharpening. Check safe areas per platform.
- Deliverables: captioned export, CLEAN export, `_SUBTITLES.srt`, `_COVER.jpg`, `_POST_COPY.md`, `_SOURCES.md`, plus `_VO.wav` when narration exists.
- Filenames: `TIC_PRJ-######_Slug_Format_PLAT_WxH_EN_v##`.

## Packaging and discovery
- One primary search phrase.
- Six hook styles: search, curiosity, performance, emotional, contrast, history. Recommend one.
- Cover headline, a title for each platform, captions, 3–5 relevant hashtags, verified mentions only, one discussion question, a pinned comment, and one measurable hypothesis.
- Copy is provisional until the footage is reviewed.

## System
- Relational database (SQLite) as the source of truth, with migrations, backups and a verified restore.
- Immutable UUIDs plus display IDs. Redirects on merge; IDs never reused.
- Revisions on every change. A blank import never erases a known value.
- Exact timing: integer ticks, [start, end).
- Idempotent intake with a review queue. Approvals are bound to versions, and changes propagate as stale flags.
- Documents are generated from the records. Large media is kept out of the database.

## Analytics and operations
- Per-platform metric observations with timestamps; unknown values stay null.
- Test one variable at a time; no causal claims.
- Task board, decision log, manifest, checkpoints and handoff.
- No publishing, scheduling, spending or contacting anyone without Iman's authorization.

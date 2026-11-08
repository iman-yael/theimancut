# Initial Six-Post Batch: Selection Plan (FOR YOUR REVIEW, NOT RENDERED)

**Honest status:** No footage has been reviewed, so **no clip has been selected.** This document fixes the slots, the choice of subject, and the selection criteria. "Leads" are scenes that published reviews say exist. They have **not** been seen, timed, or transcribed, and none may be quoted until verified against the footage.

Editorial scores are hypotheses about appeal, not predictions of views. They are kept separate from performance data (see `templates/performance_tracker.csv`).

## Scoring rubric (1–5 each, max 30)

| Criterion | 1 | 3 | 5 |
|---|---|---|---|
| Opening hook | Slow build, no clear first beat | Interesting first line | Arresting line, look, or action in the first 1–2 s |
| Standalone clarity | Needs an episode of setup | Needs one card of context | Self-explanatory |
| Emotional payoff | Flat | Clear beat | Lands hard, earned |
| Performance strength | Functional | Strong | Showcases range or a distinctive choice |
| Discussion potential | Nothing to say | Opinion-worthy | Invites a debate, a history question, or a "was this real?" |
| Spotlight fit | Ensemble moment | Character featured | Pure showcase for one actor or character |

Hard gates, which apply regardless of score: rights cleared · dialogue not cut to change meaning · DV/racism context present · spoiler label set.

## Batch slots

| Slot | Format | Subject | Why this subject (hypothesis) | Lead to look for in footage (unverified) | Spoiler | Sensitivity |
|---|---|---|---|---|---|---|
| P1 | Standout scene | Jaalen Best as Cassius (CHR-001) | Reviews center the series on his performance, and a lead-actor clip introduces the show | A boastful, funny, or self-promoting moment in an early episode. Prefer Ep1–2. | S0–S1 | Low |
| P2 | Standout scene | Geraldine & Sonny Liston (CHR-006/005) | Unexpected tenderness from the "villain" side is likely to start discussion | A review says Geraldine reads a newspaper profile aloud and softens the harsh parts for him | S1 | Low–Med (period press stereotyping) |
| P3 | Standout scene | Rudy & Cassius (CHR-004/001) **or** Dundee in the corner (CHR-007) | Brotherhood and loyalty are a warm, shareable theme | Any confidant scene between the brothers; a corner scene if the fight is depicted | S1 / S3 if fight | Low |
| P4 | Actor spotlight | **Dana Gourrier** as Bird (CHR-003) | She is the most consistently praised supporting performer across reviews | 3–4 moments showing warmth, humor, and anger "with a reason" | S1–S2 | **Med–High** if any DV-adjacent moment is used. Prefer non-violent beats. |
| P5 | Actor spotlight | **Jaalen Best** (CHR-001) | A range reel from swagger to vulnerability | Moments across 3+ episodes | S2 (avoid finale result unless labeled) | Low |
| P6 | Character mashup | "The Clay Brothers" (CHR-001 + CHR-004) | A relationship mashup has low risk and a strong emotional throughline | All shared scenes, ordered chronologically | S2 | Low |

**Held for later:** Omari Hardwick spotlight (CHR-002). The performance is strong, but most standout material is likely to involve domestic violence. It needs a reviewed approach: content note, no abuse as the hook, survivor-centered framing, and a historical/dramatized label.

## Per-clip spec sheet (to be filled at selection)

```
POST ID:            P1 … P6
SCENE ID(S):        SCN-
SOURCE TC:          file_tc in/out | episode_tc in/out
DURATION:           target set by the scene's needs (expected ~25–75 s; mashups 45–90 s)
HEADLINE (≤ 8 words, truthful):
LABELS:             "Jaalen Best as Cassius Clay" (lower-third, first 3 s)
CONTEXT CARD:       one line, only if needed
CAPTION DRAFT:      exact transcript — verified manually against audio
CROP/REFRAME:       per shot: center / tracked / split-screen / letterbox-with-blur
COMMENTARY:         optional on-screen text or VO line
WHY WATCH/SHARE:    hypothesis
CONTENT NOTE:       if any
UNRESOLVED:         rights / fact / context
SCORES:             hook _ clarity _ payoff _ performance _ discussion _ spotlight _ = /30
```

## Draft headline bank (truthful; final choice depends on the actual scene)

- P1: "The Louisville kid who told the world first"
- P2: "She edited the headlines so he didn't have to read them" *(only if the scene matches the review's description)*
- P4: "Dana Gourrier is the heartbeat of *The Greatest*" *(sourced as critics' opinion, not ours)*
- P6: "Before Muhammad Ali, there were the Clay brothers"

Avoid "the scene everyone's talking about" or "viral" unless real data supports it.

## Added requirements (2026-11-08): per-post deliverables

Each approved post gets the following, using the naming pattern `TG_S01E##_SC###_Slug_Format_PLAT_WxH_EN_v##`:

- **Video:** IG / TT / FB / YT 1080×1920 captioned + `_CLEAN`. Optional IG/FB 1080×1350 feed adaptation. A source-fps master.
- **`.srt`** per platform, in `Subtitles/`.
- **`_COVER.jpg`** 1080×1920 + crop previews, in `Covers/`.
- **`_POST_COPY.md`:** 3 hook options, cover headline, 4 platform captions, verified credits, 3–5 hashtags, discussion question, spoiler/content notes. Standards in `Post_Copy/TG_Post_Copy_Standards.md`.
- **`_SOURCES.md`** for any historical claim.
- A row in the manifest, plus a signed `Review_Exports/TG_QC_Checklist.md`.

**Layout rule:** a 1920×1080 source keeps only about 608×1080 px in a 9:16 crop. For two-person scenes (likely P2 Geraldine/Sonny and P6 Clay Brothers), plan on `split` or `fit` layouts rather than forcing a tight crop.

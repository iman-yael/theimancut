# On-Screen Text, Post Copy & Hashtag Standards

## 1. Three kinds of on-screen text (never mixed)

| Element | What it is | Style | Position (1080×1920) |
|---|---|---|---|
| **Subtitles** | Exactly what is said, plus meaningful sounds in brackets: `[crowd roaring]`, `[door slams]` | DejaVu Sans Bold 56 px, white, 4 px black outline, 1–2 lines, ≤ 42 chars/line, no animation | Bottom-centre band, ~71% down. Side margins clear right-rail buttons. Per-platform margin set in `render.sh`. |
| **Editorial text** | Your hook, context card, analysis | Distinct from subtitles: sentence case, box background, never in quotation marks unless it is a verified verbatim quote | Upper third (y ≈ 420–700) or a dedicated card |
| **ID labels** | Who is on screen | Two lines: **ACTOR NAME** / *as Character Name*. Shown 0.3 s to ~4 s on the character's first clear appearance. | Top-left, y ≈ 300 (below top UI) |

Historical explainers add a separate, third line or card: **Real person: Odessa Grady Clay (1917–1994)**. Never phrase a label or caption so the actor seems to have committed the character's actions (✗ "Omari Hardwick's abuse"; ✓ "Cash Clay, played by Omari Hardwick").

### Subtitle rules
- Transcribe from the authorized source, then **check every line by ear**, especially names (Odessa, Liston, Dundee, Faversham, Bundini) and uncertain words. Mark lines you're unsure of `[?]` until resolved; `qc_probe.sh` fails any SRT containing placeholders.
- Subtitles are verbatim. Where speech is trimmed for length, cut whole lines at a natural pause, never inside a sentence in a way that changes meaning. A paraphrase is never presented as dialogue.
- Timing: on screen at least 1 s and no more than about 6 s per event, synced to speech onset. Don't carry text across a shot change when avoidable.
- Two deliverables per post: **captioned** (burned in) and **_CLEAN** (no subtitles, ID labels kept) + `.srt`. When you use a platform's native auto-captions, upload the _CLEAN file, so viewers never see doubled subtitles.
- Don't cover faces, mouths, or key action. Use the overlay preview (QC checklist §C) and move or shorten text per shot when needed.

### AI-presenter disclosure
On screen for the whole video: **"AI presenter based on my likeness."** Also spoken in the first 3 s, and the platform AI-content label is switched on at upload.

## 2. Per-video copy package (`*_POST_COPY.md`)

1. Three truthful opening-hook options
2. One cover headline: ≤ 2 lines, ≤ 20 characters per line (line break in the text file)
3. Separate captions for IG / TT / FB / YT
4. Verified credits: **Actor as Character** (status V2 or VC only)
5. 3–5 hashtags
6. One natural discussion question
7. Spoiler / content notes

**Caption structure:** why this moment matters → series + actor/character → one original observation (acting, storytelling, or history) → question → credits + hashtags.

| Platform | Adaptation |
|---|---|
| Instagram | Strong first sentence (it shows before "more"), performance-focused, question last |
| TikTok | Short and conversational. Spell out searchable words: "The Greatest", "Prime Video", actor name, character name, "Muhammad Ali". |
| Facebook | 1–2 extra sentences of context for people who haven't seen the series |
| YouTube | Clear title (≤ 70 chars); description with credits; **sources listed for any historical claim**; disclosure toggle for AI presenter |

**Always**
- Credit line: *"Clip from The Greatest (Prime Video). Used with permission."* Use it only when a permission document exists. Credit does not replace permission.
- No @mentions until an official account has been verified (blue badge checked in-app and linked from an official source). As of 2026-11-08 **no handle has been verified**.
- No implied affiliation: never "official", "Prime Video presents", or the show's logo unless the licence allows it.
- Spoiler tag in the first line when the clip reveals a plot point beyond the premise (S2+), e.g. "⚠️ Spoilers for Episode 6".
- Content note for domestic violence, racism, or slurs, e.g. "Content note: this scene depicts domestic violence."

## 3. Hashtags

Start with **3–5**. Choose from the pools below, check each one in-app before use, and adjust based on results.

| Pool | Options | Status / caution |
|---|---|---|
| Series | #TheGreatest | **Ambiguous.** A generic phrase used for unrelated content. Always pair with "The Greatest on Prime Video" in caption text. Check the tag page in each app. |
| Subject | #MuhammadAli | Relevant on every post |
| Angle | #ActingAnalysis · #CharacterStudy · #FilmAnalysis | Pick one |
| History | #BoxingHistory · #BlackHistory | Only when the post actually covers that history |
| Name | e.g. #JaalenBest, #DanaGourrier | Check the tag refers to the actor before use |

Never: unrelated trending tags; #TrueStory on dramatized scenes; abuse- or racism-as-bait framing; tagging an actor as the perpetrator of their character's actions; promises of reach.

## 4. Filenames

```
TG_S01E##_SC###_CharacterSlug_Format_PLAT_WxH_EN_v##.mp4
  PLAT = IG | TT | FB | YT     WxH = 1080x1920 | 1080x1350     Format = SceneClip | ActorSpotlight | Mashup | PresenterBreakdown | DeepDive
Siblings: _CLEAN.mp4 · .srt (Subtitles/) · _COVER.jpg (Covers/) · _POST_COPY.md (Post_Copy/) · _SOURCES.md (Historical_Sources/)
Mashups spanning episodes: S01EMX_SCMIX and list every scene ID in the manifest.
```

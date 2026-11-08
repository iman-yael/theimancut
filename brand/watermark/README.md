# THE IMAN CUT watermark

| File | Use |
|---|---|
| `iman-cut-watermark-trimmed.png` | **Working asset.** A crop-only trim of the original: 1120×758, the lettering plus 12 px, with the transparency untouched |
| `iman-cut-watermark-original.png` | The supplied master ("The Iman Cut editorial watermark-1"): 1536×1024, transparent, about 70% empty padding |
| `audit-on-grey.png` | The original on a grey background, for inspection |

## Audit (November 8, 2026)
- **Text:** exactly `THE IMAN CUT`, cream lettering with a red slash through IMAN.
- **Transparency:** real alpha. The lettering is opaque (alpha 253–254), and the edges are anti-aliased in matching cream, so there are no dark halos and no glow.
- **Not usable as a watermark:** "The Iman Cut Editorial Logo.png" (not stored here). It has no alpha (a black square), so it would burn a black box into the footage. Use it only as an avatar or end card.
- **Readability:** clear on dark footage. On bright footage, THE and CUT stay readable but faint, and the red slash nearly disappears at watermark size. A soft drop shadow was proposed for light scenes but **not approved**.

## Placement used
| Format | Width | From right | From top | Platforms |
|---|---|---|---|---|
| 9:16 | 230 px | 64 px | 250 px (below the app interface band) | Instagram, TikTok |
| 16:9 | 190 px | 77 px | 43 px | Not used. YouTube gets no watermark |

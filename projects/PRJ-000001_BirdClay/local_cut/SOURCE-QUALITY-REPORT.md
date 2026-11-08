# Source-quality report: Bird Clay v03

## The source I used
| Field | Value (measured with ffmpeg) |
|---|---|
| File | `~/Desktop/Screen Recording 2026-11-08 at 11.44.17 AM.mov` (the name contains a narrow no-break space before "AM") |
| What it is | **A macOS screen recording** of a video playing in a browser or player. It is **not** the studio original, and it is not one of my exports |
| Dimensions | 1966 × 1106 file; **active picture 1962 × 1106**, with 2-px black columns on the left and right. There's no letterbox: the picture fills the full height |
| Codec / bitrate | H.264 Main, yuv420p, BT.709 SDR, ~18.3 Mbps video; AAC-LC stereo 48 kHz, ~102 kbps |
| Frame rate | Variable: 32.6 fps average in a 59.94 timebase. I counted about 24 unique frames per second in the scene window (959 unique frames out of 1,304 in 40 s), so the content is **film rate, and the capture added duplicate frames** |
| Duration | 4:52.11 |
| HDR | No, SDR BT.709, so no tone-mapping was needed |
| Content | It appears to be an **official extended promo clip** for *The Greatest*: it ends on a "THE GREATEST — New series, November 4" card and a Prime Original logo. It is not a full episode |

## Other files I checked
| File | Finding |
|---|---|
| `Desktop/5:min clip.mov` | The same promo, captured earlier in a separate screen recording (finished 11:44 local). Same 1966 × 1106 frame, **lower bitrate (16.2 Mbps)**, so I didn't use it |
| `Screen Recording … 11.51.39 AM.mov` and `Documents/15minMAclip.mov` | The "Becoming the Greatest" making-of documentary, 1968 × 880. **Not used in v03** |
| The v0.1 pilot exports | **Not used as a source.** As you noted, they used only ~1080 × 608 of the frame at ~1 Mbps |

**The true original (the studio master or the streaming service's file) is not available.** The screen recording above is the best source on this computer, and I describe it honestly as a screen capture.

## Source resolution vs. export resolution
| Export | Export size | Source pixels actually used | Scaling |
|---|---|---|---|
| Vertical | 1080 × 1920 | **622 × 1106** crop per shot | **1.74× upscale (Lanczos).** No detail is added. Expect a slightly soft picture on close-ups |
| Landscape | 1920 × 1080 | 1962 × 1106 (full active frame) | 0.98× downscale, so effectively full source quality |

## Export settings (both versions)
- H.264 High profile, level 4.2, CRF 16, preset slow, tuned for film; square pixels (SAR 1:1); yuv420p BT.709 (tv range); **constant 23.976 fps**, which matches the source's real frame cadence and removes the capture's duplicate frames.
- AAC-LC 192 kbps at 48 kHz stereo, loudness-normalized to −14 LUFS with a −1.5 dBTP peak limit.
- Fast-start metadata enabled.
- **One encode pass from the screen recording** to the deliverable: no intermediate re-encodes, no sharpening, no frame interpolation.

# Handoff / checkpoint (2026-11-09)

**Stage:** tools built; footage licence pending; nothing published.
**Main editing chat:** "File and folder organization" (Claude Code on Iman's Mac). Read `CLAUDE.md` first.

## Done and verified
- **Catalog:** `catalog/catalog.sqlite`: 144 characters, 161 people, 146 portrayals, 27 claims, 10 open review items. Tests: `python3 -m unittest tests.test_core tests.test_search_and_takes` (12/12 pass).
- **Cast:** the full IMDb paste is imported. Young Rudy is linked. Young Cassius (Elias Leacock) is a *proposed* younger CHR-000001, pending the episode credits. Credited stunt doubles are recorded for Jaalen Best and Amin Joseph.
- **Desktop auto-export** (`tools/autoexport/`):
  - Option B layout; Instagram, TikTok and Snapchat at 1080×1920 with the watermark; YouTube Shorts 1080×1920 and landscape 1920×1080 without it.
  - Same black-bar trim and frame-rate detection as Clipper.
  - Local Whisper draft subtitles go to review; captioned versions are made only from approved `.srt` files. Lyrics are never transcribed.
  - Tested on Linux with synthetic clips. **Not yet installed or tested on the Mac.**
- **Clipper** (`tools/clipper/`, pushed from the Mac): queue, library, live progress; output in `~/Movies/The Iman Cut/Clips/`.
- **Bird Clay cut v03/v05**: on the Mac. Edit files are in `projects/PRJ-000001_BirdClay/local_cut/`. Review-only.
- **Trailer remix kit** (R1/R2): `projects/PRJ-000002_TrailerRemix/`.
- **Review packet** for Iman: `projects/REVIEW_PACKET_2026-11-09.md`.

## Waiting on Iman
1. Amazon MGM licence reply (RGT-000001, *Under review*).
2. Two timestamped stills plus context to confirm the woman in pearls and the man at the radio in the Bird Clay cut.
3. The official source upload for R1 (channel, title, date, remix available?) per platform, and an R2 choice (a/b/c).
4. "Connie lesson" (Sonny Liston or Sonny Banks).
5. Deleting the extra branches `the-iman-cut-initial` and `local-mac-production-files` (both fully contained in `main`).

## Next executable task (Mac chat)
```
git pull
bash tools/autoexport/install.sh
pip3 install -U openai-whisper    # once, for draft subtitles
```
Then drop one finished Clipper clip into `~/Desktop/theimancut/the-greatest/_drop-finished-clips-here/` and check the five exports and the draft subtitles.

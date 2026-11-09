# The Greatest quote carousel workflow

Review finished clips, subtitles, edit notes, and credits. For each clip, record its ID, filename, source episode or promo if known, timestamps, character, credited performer, verified historical counterpart, scene context, themes, and research questions. Keep the series portrayal, documented history, and editorial interpretation separate. Reuse existing catalog IDs and claim records. Update profiles as new clips arrive.

## Quote evidence

Find the real person's documented spoken or written words. Prefer original interviews, speeches, transcripts, letters, books they wrote, and reputable archives. Label secondary sources, translations, and paraphrases. Record exact wording, speaker, source title, publisher or archive, direct link, date and setting if known, page or timestamp, surrounding context, verification and reuse status, and linked clip and character IDs. Inspect the source and preserve meaning when excerpting. Use brief excerpts and track reuse per source across the deck.

A Bird Clay quote deck requires documented words from Odessa Clay herself. A scripted line, unverified attribution, or someone else's recollection cannot fill that slot. Mark the deck `NEEDS_VERIFIED_QUOTE` when evidence is missing. A separately framed “What Ali said about his mother” deck may use verified words attributed to Ali. Skip first-person quote decks for fictional or composite characters without a verified historical subject.

## Deck and exports

Build five to seven slides around one theme: a cover hook, the historical subject and separate performer credit, the verified quote with a readable source credit, context, connection to the scene, The Iman Cut's take, and sources with a relevant close. Combine slides when the material supports a tighter deck. Label proposed editorial opinions pending approval. Only say a quote appears in the series if verified. Use large ivory headlines, a restrained red slash, and approved branding. Use approved stills or a typographic layout.

Create the shared knowledge base and each supported package as work is produced:

```text
carousels/
  knowledge-base/
    character-profiles/
    clip-index.csv
    quote-bank.csv
    source-register.csv
  instagram/<character>/<deck-id>/
  tiktok/<character>/<deck-id>/
  youtube/<character>/<deck-id>/
  snapchat/<character>/<deck-id>/
```

Use 1080 × 1350 as the Instagram design default and 1080 × 1920 for vertical adaptations. Verify posting format and crop for the destination. Label YouTube and Snapchat packages with the actual format, such as Community images, Shorts slideshow, or Story sequence. Keep unsupported formats in draft.

Each package includes numbered slides beginning with `01_cover.png`, `caption.txt`, `alt-text.txt` where supported, `sources.md`, and `manifest.json` with clip and quote IDs, dimensions, format, slide order, and review status. Include an editable layout or reproducible design instructions when supported. Keep media local according to repo rules.

Start with the Bird Clay pilot. Report clips reviewed, characters indexed, quotes verified, decks exported, and evidence gaps. Track previously used quotes and themes. Prepare packages for Iman's review under the repo's publication rules.

## Automatic Mac workflow

After pulling this update, rerun `bash tools/autoexport/install.sh` on the Mac. The agent scans completed clips in `_originals/` on each export run. It stores the live knowledge base and rendered decks in `~/Desktop/theimancut/the-greatest/carousels/`. Run `Export Now.command` after updating research inputs to rebuild immediately. Check `run-status.json` for counts and `knowledge-base/clips/` for the action needed per clip. The Mac workflow uses individual JSON records as inputs and writes the CSV indexes and character profiles from them.

Create `inputs/<clip-basename>.json` using the finished clip's filename stem:
```json
{
  "character": "Odessa ‘Bird’ Clay",
  "performer": "Dana Gourrier",
  "person_id": "REPLACE_WITH_CATALOG_PERSON_ID",
  "real_person": "Odessa Clay",
  "clip_source": "Episode or promo, direct source link, and time range",
  "scene_context": "Describe what the clip shows.",
  "clip_connection": "Explain how it relates to the documented quote.",
  "quote_id": "REPLACE_WITH_QUOTE_ID"
}
```

Claude researches the primary source during a session and records the evidence in `knowledge-base/quotes/<quote-id>.json`. The renderer trusts these review fields, so set them only after the underlying checks are complete:
```json
{
  "person_id": "SAME_CATALOG_PERSON_ID",
  "speaker": "Odessa Clay",
  "text": "REPLACE_WITH_THE_EXACT_VERIFIED_QUOTE",
  "source_title": "REPLACE_WITH_SOURCE_TITLE",
  "source_url": "https://example.org/replace-with-original-source",
  "source_location": "Timestamp or page",
  "context": "Brief historical context.",
  "attribution_type": "FIRST_PERSON",
  "status": "NEEDS_VERIFICATION",
  "reuse_status": "PENDING",
  "verified_by": ""
}
```

Use `VERIFIED` after checking the source and `APPROVED` after reviewing reuse. Record the reviewer in `verified_by`. The renderer holds missing or mismatched evidence and makes no network requests. Output packages use a content-derived deck ID, so reruns reuse existing renders and changed inputs create a new deck. Follow the active package links in the clip record. Treat older packages as archived drafts. Every package is for review, including confirmation of the destination's upload format.

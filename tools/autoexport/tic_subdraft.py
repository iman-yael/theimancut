#!/usr/bin/env python3
"""Draft subtitles for review. Turns a Whisper JSON transcript into:
  NAME.DRAFT.srt   editable subtitles (flagged lines start with "[?]"; music is never transcribed)
  NAME.REVIEW.md   what to check: uncertain wording, names, music/songs, timing
Nothing here is burned into video. After review, save the file as NAME.srt in _subtitles-approved/.

Usage: tic_subdraft.py WHISPER.json OUT_DIR NAME [CAST_NAMES.txt]
"""
import json
import re
import sys
from pathlib import Path

LOW_LOGPROB = -0.8      # segment average log-probability below this → uncertain wording
LOW_WORD_P = 0.5        # any word probability below this → uncertain word
HALLUCINATION_CR = 2.4  # Whisper compression ratio above this → possible repeated/invented text
MUSIC = re.compile(r"♪|♫|\[(music|singing|song)[^\]]*\]|\((music|singing)\)", re.I)
MAX_LINE, MAX_LINES, MIN_DUR = 42, 2, 1.0


def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def wrap(text):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= MAX_LINE:
            cur = f"{cur} {w}".strip()
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    chunks = [lines[i:i + MAX_LINES] for i in range(0, len(lines), MAX_LINES)]
    return ["\n".join(c) for c in chunks] or [""]


def load_names(path):
    if not path or not Path(path).exists():
        return set()
    toks = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        for t in re.findall(r"[A-Za-z][A-Za-z'\-]+", line):
            if t[0].isupper() and len(t) > 2:
                toks.add(t.lower().strip("'"))
    return toks


def main(src, out_dir, name, names_file=None):
    data = json.loads(Path(src).read_text(encoding="utf-8"))
    names = load_names(names_file)
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    cues, review = [], []
    for seg in data.get("segments", []):
        start, end, text = float(seg["start"]), float(seg["end"]), seg.get("text", "").strip()
        if not text:
            continue
        flags = []
        if MUSIC.search(text) or seg.get("no_speech_prob", 0) > 0.6 and len(text.split()) > 3:
            text, flags = "♪ [music]", ["MUSIC/SONG: identify the track and check its rights; lyrics are not transcribed"]
        else:
            if seg.get("avg_logprob", 0) < LOW_LOGPROB:
                flags.append(f"uncertain wording (confidence {seg.get('avg_logprob'):.2f})")
            weak = [w["word"].strip() for w in seg.get("words", []) if w.get("probability", 1) < LOW_WORD_P]
            if weak:
                flags.append("uncertain words: " + ", ".join(weak))
            if seg.get("compression_ratio", 0) > HALLUCINATION_CR:
                flags.append("possible repeated/invented text, check against the audio")
            words = re.findall(r"[A-Za-z][A-Za-z'\-]+", text)
            cast_hits = sorted({w for w in words if w.lower().strip("'") in names})
            proper = sorted({w for i, w in enumerate(words) if i > 0 and w[0].isupper() and w.lower() not in names and w not in ("I", "I'm", "I'll", "I've")})
            if cast_hits:
                flags.append("name(s): check spelling: " + ", ".join(cast_hits))
            if proper:
                flags.append("capitalised word(s), possibly a name: " + ", ".join(proper))
        if end - start < MIN_DUR:
            end = start + MIN_DUR
            flags.append("shorter than 1 s: timing extended, check")
        parts = wrap(text)
        step = (end - start) / len(parts)
        for k, p in enumerate(parts):
            s, e = start + k * step, start + (k + 1) * step
            cue_text = ("[?] " + p) if flags and not p.startswith("♪") else p
            cues.append((s, e, cue_text))
            if flags:
                review.append((len(cues), s, e, p.replace("\n", " / "), flags))
    cues.sort(key=lambda c: c[0])
    for k in range(len(cues) - 1):        # never overlap the next line (a 1-s minimum must not cover new speech)
        s0, e0, t0 = cues[k]
        nxt = cues[k + 1][0]
        if e0 > nxt - 0.04:
            cues[k] = (s0, max(s0 + 0.3, nxt - 0.04), t0)
    srt = "\n".join(f"{i}\n{ts(s)} --> {ts(e)}\n{t}\n" for i, (s, e, t) in enumerate(cues, 1))
    (out / f"{name}.DRAFT.srt").write_text(srt, encoding="utf-8")
    L = [f"# Subtitle review: {name}", "",
         "**DRAFT, not burned in.** Machine transcript. Check every line against the audio, especially the flagged ones below.",
         "When it's right: remove the `[?] ` markers, then save the file as **`" + name + ".srt`** in `_subtitles-approved/`. Captioned versions are then made automatically.", "",
         f"- Cues: {len(cues)} · flagged: {len(review)} · model: {data.get('model', 'whisper (local)')}", "",
         "| Cue | Time | Text | Check |", "|---|---|---|---|"]
    L += [f"| {i} | {ts(s)}–{ts(e)} | {t} | {'; '.join(f)} |" for i, s, e, t, f in review] or ["| — | — | — | Nothing flagged; still listen once end to end |"]
    L += ["", "Also check: speaker changes, meaningful sounds worth marking (e.g. `[crowd cheering]`), and that no line is cut mid-sentence."]
    (out / f"{name}.REVIEW.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"{len(cues)} cues, {len(review)} flagged")


if __name__ == "__main__":
    main(*sys.argv[1:])

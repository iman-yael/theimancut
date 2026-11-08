#!/usr/bin/env python3
"""Merge SRT files (dialogue + narration) into one valid sidecar: parse, sort by start time, renumber.
Usage: merge_srt.py OUT.srt IN1.srt [IN2.srt ...]   Narration cues are prefixed with nothing; styles live only in burned versions."""
import re, sys
def cues(p):
    blocks = re.split(r"\n\s*\n", open(p, encoding="utf-8-sig").read().strip().replace("\r\n", "\n"))
    for b in blocks:
        lines = b.strip().split("\n")
        if len(lines) >= 2 and "-->" in lines[1]:
            yield lines[1].strip(), lines[2:]
def key(t):
    h, m, s = t.split(" --> ")[0].replace(",", ".").split(":"); return int(h) * 3600 + int(m) * 60 + float(s)
allc = sorted((c for p in sys.argv[2:] if p for c in cues(p)), key=lambda c: key(c[0]))
with open(sys.argv[1], "w", encoding="utf-8") as f:
    f.write("\n".join(f"{i}\n{t}\n" + "\n".join(txt) + "\n" for i, (t, txt) in enumerate(allc, 1)))

"""Build SRT + ASS subtitles on the v03 timeline from a verified line list.

lines_verified.json: [{"src_in": <source s>, "src_out": <source s>, "text": "...", "status": "verified|uncertain"}]
Source times are mapped through edl_v03.json; lines inside removed sections are dropped.
"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
shots = [s for s in json.load(open(f"{HERE}/edl_v03.json"))["shots"] if "in" in s]
lines = json.load(open(f"{HERE}/lines_verified.json"))
labels = json.load(open(f"{HERE}/cast_labels.json")) if os.path.exists(f"{HERE}/cast_labels.json") else []

def to_out(t):
    off = 0.0
    for s in shots:
        if s["in"] - 0.05 <= t <= s["out"] + 0.05:
            return off + min(max(t, s["in"]), s["out"]) - s["in"]
        off += s["out"] - s["in"]
    return None

def ts(t, sep=","):
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h):02}:{int(m):02}:{s:06.3f}".replace(".", sep)

cues = []
for l in lines:
    a, b = to_out(l["src_in"]), to_out(l["src_out"])
    if a is None or b is None or b - a < 0.3:
        continue
    cues.append((a, max(b, a + 1.0), l["text"]))

with open(f"{HERE}/TIC_BirdClay_v03.srt", "w") as f:
    for i, (a, b, t) in enumerate(cues, 1):
        f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{t}\n\n")

for layout, (w, h, size, mv) in {"vertical": (1080, 1920, 58, 500), "landscape": (1920, 1080, 46, 64)}.items():
    with open(f"{HERE}/subs_{layout}.ass", "w") as f:
        f.write(f"[Script Info]\nScriptType: v4.00+\nPlayResX: {w}\nPlayResY: {h}\nWrapStyle: 0\n\n"
                "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
                f"Style: Default,Arial,{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,{3 if layout=='vertical' else 2.5},0,2,90,90,{mv},1\n"
                # cast labels: top-left, opposite the watermark; name over "as Character"
                f"Style: Name,New York,{54 if layout=='vertical' else 44},&H00D3EBF6,&H00FFFFFF,&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,2.5,1,7,64,64,{265 if layout=='vertical' else 48},1\n"
                f"Style: Role,Arial,{36 if layout=='vertical' else 30},&H00D3EBF6,&H00FFFFFF,&H00000000,&H78000000,0,1,0,0,100,100,0,0,1,2,1,7,66,64,{330 if layout=='vertical' else 102},1\n\n"
                "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        for a, b, t in cues:
            f.write(f"Dialogue: 0,{ts(a,'.')[1:-1]},{ts(b,'.')[1:-1]},Default,,0,0,0,,{t}\n")
        # only labels you have confirmed are ever burned in
        for lab in labels:
            if lab.get("confirmed"):
                a, b = lab["edit_in"], lab["edit_in"] + lab["duration"]
                fade = "{\\fad(250,250)}"
                f.write(f"Dialogue: 1,{ts(a,'.')[1:-1]},{ts(b,'.')[1:-1]},Name,,0,0,0,,{fade}{lab['performer']}\n")
                f.write(f"Dialogue: 1,{ts(a,'.')[1:-1]},{ts(b,'.')[1:-1]},Role,,0,0,0,,{fade}as {lab['character']}\n")
print(len(cues), "cues,", sum(1 for l in labels if l.get("confirmed")), "confirmed cast labels")

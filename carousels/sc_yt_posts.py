"""Snapchat + YouTube Shorts post folders, mirroring ~/Movies/The Iman Cut/Instagram Posts."""
import os, re, glob, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

FF = "/Users/imanyael/Library/Python/3.9/lib/python/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"
M = os.path.expanduser("~/Movies/The Iman Cut")
IG = f"{M}/Instagram Posts"
B1 = f"{M}/Clips/The Greatest - Becoming the Greatest - 30-clip review batch"
B2 = f"{M}/Clips/The Greatest - Becoming the Greatest - batch 2 (45 short clips)"
PR = f"{M}/Clips/The Greatest - Promo Rome Final - 12-clip review batch"
WM = os.path.expanduser("~/Projects/personal/theimancut-repo/brand/watermark/iman-cut-watermark-trimmed.png")
SC, YT = f"{M}/Snapchat Posts", f"{M}/YouTube Shorts Posts"

def cover_dir(num):
    n = int(num)
    if n <= 10:
        return f"{B1}/_covers_clip{n:02d}", f"TIC_BTG_{n:02d}"
    if n in (11, 12):
        k = {11: "02", 12: "05"}[n]
        return f"{B2}/_covers_clip{k}", f"TIC_BTG2_{k}"
    k = {13: "01", 14: "06", 15: "08", 16: "09", 17: "10", 18: "11"}[n]
    return f"{PR}/_covers_clip{k}", f"TIC_PROMO_{k}"

def render(src, out, title_png, t, wm):
    a, b = max(0, t - 0.6), t + 1.0
    inputs = ["-i", src]; g = "[0:v]null[v0]"; last = "v0"
    if wm:
        inputs += ["-i", WM]; g += ";[1:v]scale=230:-1[wm];[v0][wm]overlay=W-w-64:250[vw]"; last = "vw"
    if title_png and os.path.exists(title_png):
        i = len(inputs) // 2; inputs += ["-i", title_png]
        g += f";[{last}][{i}:v]overlay=0:0:enable='between(t,{a:.2f},{b:.2f})'[vt]"; last = "vt"
    g += f";[{last}]format=yuv420p[vout]"
    r = subprocess.run([FF, "-v", "error", "-y", *inputs, "-filter_complex", g, "-map", "[vout]", "-map", "0:a?",
                        "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "copy", "-movflags", "+faststart", out],
                       capture_output=True, text=True)
    return r.returncode == 0 or print(r.stderr[-400:])

def job(post):
    name = os.path.basename(post); num, title = name[5:7], name[10:]
    cdir, base = cover_dir(num)
    env = open(f"{cdir}/_covers/{base}.title.env").read()
    t = float(re.search(r'TITLE_TIME="([\d.]+)"', env).group(1))
    src = glob.glob(f"{post}/1_REEL_*.mp4")[0]
    cap = [l for l in open(f"{post}/3_REEL_CAPTION.txt").read().split("\n")]
    body = "\n".join(cap).strip()
    hook = cap[0].strip()
    q = next((l for l in cap if l.strip().endswith("👇")), "").strip()
    tags = next((l for l in cap if l.startswith("#")), "#TheGreatest #TheImanCut")
    head = open(f"{cdir}/_covers/{base}.headline.txt").read().strip()

    # Snapchat: watermark ON, title on screen around the cover moment (Spotlight has no custom covers)
    d = f"{SC}/{name}"; os.makedirs(d, exist_ok=True)
    render(src, f"{d}/1_SPOTLIGHT_{base}_SC_1080x1920_TITLED.mp4", f"{cdir}/_covers/{base}_SC_title.png", t, True)
    subprocess.run(["cp", f"{cdir}/snapchat/{base}_Snapchat_Cover_1080x1920.jpg", f"{d}/2_COVER_PREVIEW_1080x1920.jpg"])
    sc_tags = " ".join(tags.split()[:3] + ["#TheImanCut"]) if "#TheImanCut" not in tags.split()[:3] else " ".join(tags.split()[:3])
    open(f"{d}/3_SNAPCHAT_CAPTION.txt", "w").write(
        f"{hook}\n{q}\n{sc_tags}\n\n"
        f"(Spotlight has no custom covers: the title \"{head}\" shows on screen at {t:.1f}s.)\n")

    # YouTube Shorts: no watermark, titled export + clean export, thumbnail JPG
    d = f"{YT}/{name}"; os.makedirs(d, exist_ok=True)
    render(src, f"{d}/1_SHORT_{base}_YT-Shorts_1080x1920_TITLED.mp4", f"{cdir}/_covers/{base}_YT-Shorts_title.png", t, False)
    subprocess.run(["cp", src, f"{d}/1b_SHORT_{base}_YT-Shorts_1080x1920_CLEAN.mp4"])
    subprocess.run(["cp", f"{cdir}/youtube/{base}_YouTubeShorts_Cover_1080x1920.jpg", f"{d}/2_THUMBNAIL_1080x1920.jpg"])
    yt_title = f"{head.title().replace(chr(39)+'S', chr(39)+'s')} | The Greatest (Prime Video) #Shorts"[:100]
    open(f"{d}/3_YOUTUBE_TITLE_AND_DESCRIPTION.txt", "w").write(
        f"TITLE (max 100 characters):\n{yt_title}\n\nDESCRIPTION:\n{body}\n\n#Shorts\n\n"
        f"THUMBNAIL: in the YouTube app, pick the frame at {t:.1f}s in the TITLED video (the title is on screen there). "
        f"If your channel offers 'Upload thumbnail' for Shorts, post the CLEAN video and upload 2_THUMBNAIL instead.\n")
    return name

posts = sorted(glob.glob(f"{IG}/Post *"))
if sys.argv[1:]: posts = [p for p in posts if os.path.basename(p)[5:7] in sys.argv[1:]]
with ThreadPoolExecutor(3) as ex:
    for n in ex.map(job, posts):
        print("ok", n)

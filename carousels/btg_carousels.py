import os, sys, json
sys.path.insert(0, os.path.expanduser("~/Projects/personal/theimancut-repo/tools/autoexport"))
import tic_carousel_design as T

FF = "/Users/imanyael/Library/Python/3.9/lib/python/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"
B = os.path.expanduser("~/Movies/The Iman Cut/Clips/The Greatest - Becoming the Greatest - 30-clip review batch")
OUT = os.path.expanduser("~/Movies/The Iman Cut/Export/the-greatest/carousels/instagram/becoming-the-greatest")
SRC = {n: f"{B}/_covers_clip{n:02d}/TIC_BTG_{n:02d}.mov" for n in (1, 3, 4)}
W, H = 1080, 1350
KICK = "THE GREATEST · PRIME VIDEO"

# ("cover", headline, t, focus) | ("text", heading, body, sub, t, focus) | ("quote", quote, speaker, credit, t, focus)
DECKS = {
 "carousel-2": dict(clip=1, title="First, He Was Clay", slides=[
  ("cover", "FIRST, HE WAS CLAY", 30.6, 0.5),
  ("text", "BEFORE THE NAME", "Prime Video's The Greatest doesn't open on the legend. It opens on a young man from Louisville named Cassius Clay, played by Jaalen Best.", "THE FILM", 26.0, 0.5),
  ("text", "LOUISVILLE, 1942", "Cassius Marcellus Clay Jr. was born on January 17, 1942, in Louisville, Kentucky, the son of Odessa Grady Clay and Cassius Clay Sr.", "THE HISTORY", 37.5, 0.5),
  ("text", "A STOLEN BIKE", "At 12, he reported his stolen bicycle to a police officer, Joe Martin, who also coached young boxers. That's how it started.", "THE HISTORY", 15.0, 0.5),
  ("text", "ROME TO LISTON", "He won Olympic gold in Rome in 1960, at 18. In 1964 he beat Sonny Liston for the heavyweight title, and soon after he announced his new name: Muhammad Ali.", "THE HISTORY", 22.0, 0.5),
  ("quote", "First, he was Clay.", "Michael B. Jordan, Executive Producer", "Becoming the Greatest (Prime Video featurette)", 23.2, 0.5),
 ]),
 "carousel-3": dict(clip=3, title="No Backup Plan", slides=[
  ("cover", "NO BACKUP PLAN", 12.4, 0.5),
  ("text", "GOING HOME", "In Becoming the Greatest, Jaalen Best, who plays Cassius Clay, drives home to see his mother, Vanessa Canady.", "THE FILM", 1.5, 0.45),
  ("quote", "I don't need no backup plan, I got this.", "Jaalen Best, as remembered by his mother, Vanessa Canady", "Becoming the Greatest (Prime Video featurette)", 19.0, 0.5),
  ("quote", "He's not cocky, but he's very confident.", "Vanessa Canady, Jaalen's mother", "Becoming the Greatest (Prime Video featurette)", 21.0, 0.5),
  ("text", "SOUND FAMILIAR?", "Long before he held a title, young Cassius Clay was telling anyone who'd listen that he would be the greatest. Confidence was part of the story from the start.", "THE HISTORY", 10.5, 0.5),
  ("quote", "Cassius Jr.'s life to me was an unusual one from other Children, and he is still Unusual to day", "Odessa Clay, Ali's mother", "handwritten sketch, quoted in Sports Illustrated, 1966", 12.9, 0.5),
 ]),
 "carousel-4": dict(clip=4, title="Who Could Play Clay?", slides=[
  ("cover", "WHO COULD PLAY CLAY?", 38.6, 0.5),
  ("quote", "If we don't find the right person, then we can't make the show.", "From the production", "Becoming the Greatest (Prime Video featurette)", 10.0, 0.5),
  ("text", "IT WASN'T JUST A READ", "The search for Cassius Clay ran through audition tapes and boxing-gym sessions. As one voice in the featurette puts it: \"It was a process.\"", "THE FILM", 41.0, 0.5),
  ("quote", "I knew that Ben would take care of that.", "Lonnie Ali, Executive Producer · Ali's widow, on creator Ben Watkins", "Becoming the Greatest (Prime Video featurette)", 34.0, 0.5),
  ("text", "THE DUNDEE LINK", "Trainer Angelo Dundee worked Ali's corner through most of his pro career. In the featurette, his son Jim Dundee goes through the archive with the team.", "THE HISTORY", 17.5, 0.5),
  ("text", "YOUR CALL", "Finding someone to play the young Clay meant capturing the speed, the mouth and the conviction. Who would you have cast?", "COMMENT BELOW", 39.5, 0.5),
 ]),
}

def caption(d):
    return (f"{d['title']}. Swipe for the film and the history behind it.\n\n"
            "🎬 The Greatest (Prime Video), from the featurette Becoming the Greatest\n"
            "✍️ Commentary and editing: Iman Yael | The Iman Cut\n\n"
            "This post includes excerpts discussed through original criticism and commentary. Fair use under 17 U.S.C. § 107 is determined case by case; "
            "this notice does not establish permission or guarantee fair use. The Iman Cut is an independent commentary platform and is not affiliated with the productions discussed.\n\n"
            "#TheGreatest #MuhammadAli #CassiusClay #JaalenBest #PrimeVideo #BoxingHistory #TheImanCut\n")

for deck, d in DECKS.items():
    od = os.path.join(OUT, deck); os.makedirs(od, exist_ok=True)
    src = SRC[d["clip"]]; total = len(d["slides"]); files = []
    for i, s in enumerate(d["slides"], 1):
        if s[0] == "cover":
            st = T.grab_still(src, s[2], FF)
            if d["clip"] == 1: st = st.crop((0, 0, st.width, int(st.height * 0.76)))   # drop the burned-in name strap
            im = T.slide_cover(W, H, s[1], KICK, st, s[3])
            fn = "01_cover.png"
        elif s[0] == "text":
            im = T.slide_text(W, H, s[1], s[2], i, total, sub=s[3], bg=T.grab_still(src, s[4], FF), bg_focus=s[5])
            fn = f"{i:02d}_slide.png"
        else:
            im = T.slide_quote(W, H, s[1], s[2], s[3], i, total, bg=T.grab_still(src, s[4], FF), bg_focus=s[5])
            fn = f"{i:02d}_slide.png"
        p = os.path.join(od, fn); im.save(p); files.append(p)
    open(os.path.join(od, "caption.txt"), "w").write(caption(d))
    T.phone_preview(files, os.path.join(od, "_preview.jpg"), f"{deck} · {d['title']}")
    print("ok", deck, len(files))
print(json.dumps(T.fonts_used()))

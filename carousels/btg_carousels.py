import os, sys, json
sys.path.insert(0, os.path.expanduser("~/Projects/personal/theimancut-repo/tools/autoexport"))
import tic_carousel_design as T

FF = "/Users/imanyael/Library/Python/3.9/lib/python/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"
B = os.path.expanduser("~/Movies/The Iman Cut/Clips/The Greatest - Becoming the Greatest - 30-clip review batch")
OUT = os.path.expanduser("~/Movies/The Iman Cut/Export/the-greatest/carousels/instagram/becoming-the-greatest")
SRC = {n: f"{B}/_covers_clip{n:02d}/TIC_BTG_{n:02d}.mov" for n in range(1, 11)}
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


DECKS.update({
 "carousel-5": dict(clip=5, title="Down to Four", slides=[
  ("cover", "DOWN TO FOUR", 15.4, 0.5),
  ("text", "SIX MONTHS OF AUDITIONS", "Over about six months, the production narrowed its search for Cassius Clay down to four actors, based on auditions alone.", "THE FILM", 1.5, 0.5),
  ("text", "THEN CAME THE GYM", "The next test was physical: a boxing evaluation over several days, with all four contenders in the same place at the same time.", "THE FILM", 12.5, 0.5),
  ("quote", "This is a completely different animal.", "Robert Sale, Boxing Instructor", "Becoming the Greatest (Prime Video featurette)", 23.6, 0.5),
  ("text", "THE REAL TRYOUT", "Young Cassius Clay learned the game as an amateur in Louisville gyms, winning Golden Gloves titles before he was old enough to turn pro.", "THE HISTORY", 3.5, 0.5),
  ("text", "AROUND 100 WINS", "His amateur record is usually given as about 100 wins and 5 losses, and it ended with Olympic gold in Rome in 1960. Could you have made the final four?", "THE HISTORY", 17.0, 0.5),
 ]),
 "carousel-6": dict(clip=6, title="A Different Animal", slides=[
  ("cover", "A DIFFERENT ANIMAL", 14.5, 0.5),
  ("quote", "His legend lives forever.", "Robert Sale, Boxing Instructor", "Becoming the Greatest (Prime Video featurette)", 11.5, 0.5),
  ("quote", "Any one of us can get it.", "A contender for the role", "Becoming the Greatest (Prime Video featurette)", 20.5, 0.5),
  ("text", "PUT THROUGH THEIR PACES", "Veteran trainer Robert Sale ran the contenders through drills, counts and pad work, testing how they moved as well as how they hit.", "THE FILM", 16.0, 0.5),
  ("text", "HANDS LOW, FEET FAST", "Clay often fought with his hands low and relied on speed and footwork, which was rare for a heavyweight. Any actor would have to move like that.", "THE HISTORY", 2.0, 0.5),
  ("text", "BUTTERFLY, BEE", "\"Float like a butterfly, sting like a bee\" came from Drew \"Bundini\" Brown, Ali's cornerman, in 1964. Which Ali line is your favourite?", "THE HISTORY", 26.0, 0.5),
 ]),
 "carousel-7": dict(clip=7, title="Faster, Faster", slides=[
  ("cover", "FASTER. FASTER.", 4.4, 0.5),
  ("quote", "Keep doing it faster, faster, faster.", "In the gym", "Becoming the Greatest (Prime Video featurette)", 1.0, 0.5),
  ("quote", "As long as you give it your all, the decision doesn't ultimately come down to you.", "A contender for the role", "Becoming the Greatest (Prime Video featurette)", 9.5, 0.5),
  ("quote", "I needed somebody to add that undefinable magic element.", "From the production", "Becoming the Greatest (Prime Video featurette)", 14.0, 0.5),
  ("text", "HE CALLED HIS SHOTS", "Young Clay was known for his speed and his mouth. He'd predict the round he'd win in, and back it up often enough to make people listen.", "THE HISTORY", 4.4, 0.5),
  ("text", "THE MAGIC PART", "Speed can be trained. Magic can't. What's the thing that makes a performance work for you?", "COMMENT BELOW", 17.5, 0.5),
 ]),
 "carousel-8": dict(clip=8, title="Top of Every List", slides=[
  ("cover", "TOP OF EVERY LIST", 13.0, 0.5),
  ("text", "THREE TESTS", "The read. The overall impression. The physical boxing evaluation. The team was asked who was at the top of their list for each one.", "THE FILM", 3.0, 0.5),
  ("quote", "Jaalen Best was the answer in all the categories.", "From the production", "Becoming the Greatest (Prime Video featurette)", 16.0, 0.5),
  ("text", "APRIL 18, 2024", "A date card marks the next scene: Los Angeles, April 18, 2024.", "THE FILM", 23.0, 0.5),
  ("text", "OCTOBER 29, 1960", "Weeks after Rome, Clay had his first pro fight back in Louisville and beat Tunney Hunsaker on points. Another first day.", "THE HISTORY", 9.0, 0.5),
  ("text", "YOUR VOTE", "Read, presence, boxing. Which matters most when you cast a legend?", "COMMENT BELOW", 13.0, 0.5),
 ]),
 "carousel-9": dict(clip=9, title="Get Here Fast", slides=[
  ("cover", "GET HERE FAST", 21.0, 0.5),
  ("quote", "I'm going to tell him congratulations.", "From the production", "Becoming the Greatest (Prime Video featurette)", 3.0, 0.5),
  ("text", "HEADED TO THE AIRPORT", "Jaalen Best was on his way to the airport when the call came: the showrunner wanted him back at the office. \"Just get there as fast as you can.\"", "THE FILM", 9.0, 0.5),
  ("quote", "I could be there in 30 minutes.", "Jaalen Best", "Becoming the Greatest (Prime Video featurette)", 18.0, 0.5),
  ("text", "HIS FIRST CALL", "At 12, Cassius Clay walked into Joe Martin's gym after his bike was stolen. One chance meeting started everything.", "THE HISTORY", 13.6, 0.5),
  ("text", "YOUR CALL", "Ever get a phone call that changed everything?", "COMMENT BELOW", 20.0, 0.5),
 ]),
 "carousel-10": dict(clip=10, title="The Role Is His", slides=[
  ("cover", "THE ROLE IS HIS", 10.5, 0.5),
  ("quote", "It was time to make the decision and anoint Jaalen Best as Cassius Clay.", "From the production", "Becoming the Greatest (Prime Video featurette)", 1.0, 0.5),
  ("quote", "It was a really emotional time for me.", "From the production", "Becoming the Greatest (Prime Video featurette)", 13.0, 0.5),
  ("text", "WHAT COMES NEXT", "\"I also was thinking about everything I'm going to need him to do.\" Playing Clay means the boxing, the voice and years of a life.", "THE FILM", 9.5, 0.5),
  ("text", "CHAMPION AT 22", "Clay was 22 when he beat Sonny Liston in February 1964 to become heavyweight champion of the world.", "THE HISTORY", 11.0, 0.5),
  ("text", "RATE IT", "Jaalen Best as Cassius Clay. Rate the casting from 1 to 10.", "COMMENT BELOW", 4.0, 0.5),
 ]),
})
ONLY = [a for a in sys.argv[1:]]

def caption(d):
    return (f"{d['title']}. Swipe for the film and the history behind it.\n\n"
            "🎬 The Greatest (Prime Video), from the featurette Becoming the Greatest\n"
            "✍️ Commentary and editing: Iman Yael | The Iman Cut\n\n"
            "This post includes excerpts discussed through original criticism and commentary. Fair use under 17 U.S.C. § 107 is determined case by case; "
            "this notice does not establish permission or guarantee fair use. The Iman Cut is an independent commentary platform and is not affiliated with the productions discussed.\n\n"
            "#TheGreatest #MuhammadAli #CassiusClay #JaalenBest #PrimeVideo #BoxingHistory #TheImanCut\n")

for deck, d in DECKS.items():
    if ONLY and deck not in ONLY: continue
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

"""Seed data for WRK: The Greatest. Data only — the catalog code is title-agnostic.
Run once; every step is idempotent (ingestions by checksum, lookups before creation)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tic.core import Catalog, norm, now  # noqa: E402
from tic import intake  # noqa: E402

cat = Catalog(ROOT / "catalog" / "catalog.sqlite", actor="claude-producer")
INC = ROOT / "intake" / "incoming"
TODAY = "2026-11-08"


def get_or_create_work():
    r = cat.one("SELECT entity_uuid FROM external_id WHERE provider='imdb' AND value='tt15715850'")
    if r:
        return r[0]
    w = cat.create("work", dict(title="The Greatest", work_type="limited_series", first_release="2026-11-04",
                                notes="Prime Video limited series about Muhammad Ali (1960–64 period per reviews)."))
    cat.db.execute("INSERT INTO external_id VALUES (?,?,?)", (w, "imdb", "tt15715850"))
    cat.db.execute("INSERT INTO work_title VALUES (?,?,?,?,?)", (w, "The Greatest", "en", "US", "original"))
    cat.db.execute("INSERT INTO release_date VALUES (?,?,?,?)", (w, "WW", "2026-11-04", "Prime Video"))
    s = cat.create("season", dict(work_uuid=w, label="Season 1", ordinal=1))
    for n in range(1, 9):
        i = cat.create("installment", dict(work_uuid=w, season_uuid=s, kind="episode", title=None))
        cat.db.execute("INSERT INTO installment_number VALUES (?,?,?,?)", (i, "release_order", f"S01E{n:02d}", n))
    return w


work = get_or_create_work()
reports = {}
reports["legacy"] = intake.ingest_legacy(cat, INC / "legacy_v0_character_ids_2026-11-08.tsv", work,
                                         "v0 package built from web-search snippets, 2026-11-08")
reports["imdb_cast"] = intake.ingest_cast(cat, INC / "imdb_tt15715850_fullcredits_cast_2026-11-08.tsv", work,
                                          "IMDb full credits as pasted by Iman Yael 2026-11-08", "V1-IMDb", authoritative_names=True)
reports["imdb_crew"] = intake.ingest_crew(cat, INC / "imdb_tt15715850_fullcredits_identity_crew_2026-11-08.tsv", work,
                                          "IMDb full credits as pasted by Iman Yael 2026-11-08")
reports["user_mappings"] = intake.ingest_cast(cat, INC / "user_supplied_mappings_2026-11-08.tsv", work,
                                              "Mappings typed by Iman Yael in brief 2026-11-08", "supplied")

C = lambda legacy: cat.one("SELECT entity_uuid FROM external_id WHERE provider='tic-v0' AND value=?", legacy)[0]  # noqa: E731


def char_by_name(name):
    r = cat.find_character(work, name)
    assert len(r) == 1, (name, r)
    return r[0][0]


ALI, SR, BIRD, RUDY, LISTON, GERALDINE = (C(f"CHR-00{i}") for i in range(1, 7))
ALBERTA, BETTY = char_by_name("Alberta Jones"), char_by_name("Betty Shabazz")

# Credit verification upgrade: IMDb + independent trade/outlet report = V2 (end credits still pending → VC).
if not cat.one("SELECT 1 FROM meta WHERE key='seed_v2_done'"):
    for ch in (ALI, SR, BIRD, RUDY, LISTON, GERALDINE, C("CHR-007"), C("CHR-008"), C("CHR-009"), C("CHR-010"), C("CHR-011"), C("CHR-012"), ALBERTA):
        for (p,) in cat.q("SELECT uuid FROM portrayal WHERE character_uuid=? AND age_portrayal='primary'", ch):
            cat.update(p, {"credit_verification": "V2"}, note="IMDb credit + independent outlet report agree")
    cat.db.execute("INSERT INTO meta VALUES ('seed_v2_done', ?)", (now(),))

# ---------------- sources
SOURCES = {
    "imdb": ("IMDb full credits, The Greatest (tt15715850), as pasted by user", "IMDb", "https://www.imdb.com/title/tt15715850/fullcredits/", "credits_database", "User-supplied paste; crowd-maintained database; casting only."),
    "deadline": ("Muhammad Ali series casts Omari Hardwick, Dana Gourrier", "Deadline", "https://deadline.com/2025/02/the-greatest-omari-hardwick-dana-gourrier-muhammad-ali-series-1236279151", "trade_press", None),
    "aol_joseph": ("Amazon series casts Amin Joseph as Sonny Liston", "AOL / Deadline syndication", "https://www.aol.com/entertainment/muhammad-ali-amazon-series-greatest-190000700.html", "trade_press", None),
    "mxdwn": ("Michael Ealy and Kai Parham cast in The Greatest", "mxdwn Television", "https://television.mxdwn.com/news/michael-ealy-and-kai-parham-cast-in-prime-videos-the-greatest/amp", "entertainment_press", None),
    "blex": ("Reno Wilson and Erica Tazel join The Greatest", "Blex Media", "https://blexmedia.com/reno-wilson-and-erica-tazel-the-greatest", "entertainment_press", None),
    "njunkie": ("Who plays who in The Greatest", "Netflix Junkie", "https://www.netflixjunkie.com/hollywood-news-who-plays-who-in-the-greatest-on-prime-video-meet-the-cast-of-the-muhammad-ali-inspired-series/", "entertainment_press", "Seen via search snippet only."),
    "ebert": ("The Greatest review", "RogerEbert.com", "https://www.rogerebert.com/reviews/the-greatest-muhammad-ali-prime-video-tv-review-2026", "review", "Seen via search snippet only."),
    "wil": ("The Greatest season 1 review", "Wherever I Look", "https://wherever-i-look.com/tv-shows/season-review/the-greatest-season-1-review-muhammad-ali-as-a-trojan-horse", "review", "Seen via search snippet only."),
    "revolt": ("First opponent yourself: Omari Hardwick as Cassius Clay Sr.", "Revolt", "https://www.revolt.tv/article/first-opponent-yourself-omari-hardwick-as-cassius-clay-sr-the-greatest", "entertainment_press", "Seen via search snippet only."),
    "thewrap": ("The Greatest review", "TheWrap", "https://thewrap.com/creative-content/reviews/the-greatest-amazon-review-prime-video/", "review", "Seen via search snippet only."),
    "variety": ("The Greatest review", "Variety", "https://variety.com/2026/tv/reviews/the-greatest-review-prime-video-muhammad-ali-1236935457/", "review", "Seen via search snippet only."),
    "blackpast": ("Alberta Odell Jones (1930-1965)", "BlackPast", "https://new.blackpast.org/?p=38409", "reference", "Seen via search snippet only."),
    "wfpl": ("Louisville trailblazer's murder unsolved 51 years later", "WFPL", "https://wfpl.org/louisville-trailblazer-murder-unsolved-51-years-later/", "news", "Seen via search snippet only."),
    "uofl_law": ("Alumna pushes for more investigation into death of civil rights leader", "University of Louisville Law", "https://law.louisville.edu/news/alumna-pushes-more-investigation-death-civil-rights-leader", "institutional", "Seen via search snippet only."),
    "jfaj": ("Alberta Jones biography", "Justice for Alberta Jones (family-run site)", "https://justiceforalbertajones.squarespace.com/bio", "family_account", "Not independent."),
    "sothebys": ("Lot 292 catalogue note (Louisville Sponsoring Group)", "Sotheby's", "https://www.sothebys.com/en/auctions/ecatalogue/2017/fine-books-manuscripts-n09658/lot.292.html", "auction_catalogue", "Secondary; seen via snippet."),
    "wiki_mirror_sr": ("Cassius Marcellus Clay Sr. (Wikipedia mirror)", "Wikipedia (IPFS mirror)", "https://en.wikipedia-on-ipfs.org/wiki/Cassius_Marcellus_Clay_Sr.", "tertiary", "Low reliability for allegations; needs primary/biography check."),
    "npr_eig": ("Fresh Air: Jonathan Eig on Ali: A Life", "NPR", "https://www.npr.org/transcripts/555301222", "interview", "Not yet read in full."),
    "eig_book": ("Ali: A Life (2017)", "Jonathan Eig", None, "biography", "NOT YET CONSULTED — needed for family claims."),
    "tvmaze": ("The Greatest episode list", "TVMaze", "https://www.tvmaze.com/shows/78326/the-greatest", "listings", "Seen via snippet only."),
}
src = {}
for k, (title, author, url, stype, note) in SOURCES.items():
    r = cat.one("SELECT uuid FROM source WHERE title=?", title)
    src[k] = r[0] if r else cat.create("source", dict(title=title, author=author, url=url, source_type=stype, access_date=TODAY, reliability_note=note))


def claim(subject, text, domain, cls, status, evidence, notes=None):
    r = cat.one("SELECT uuid FROM claim WHERE subject_uuid=? AND text=?", subject, text)
    if r:
        return r[0]
    u = cat.create("claim", dict(text=text, subject_uuid=subject, domain=domain, claim_class=cls, status=status, notes=notes, checked_at=TODAY))
    for key, stance in evidence:
        cat.db.execute("INSERT OR IGNORE INTO claim_evidence VALUES (?,?,?,NULL,?)", (u, src[key], stance, now()))
    return u


claim(work, "Eight-episode limited series released in full on Prime Video on 2026-11-04", "production", "fact", "supported", [("tvmaze", "supports"), ("variety", "context")])
claim(ALI, "Jaalen Best is credited as Cassius Clay / Muhammad Ali", "casting", "fact", "supported", [("imdb", "supports"), ("variety", "supports")])
claim(SR, "Omari Hardwick is credited as Cassius Clay Sr.", "casting", "fact", "supported", [("imdb", "supports"), ("deadline", "supports")])
claim(BIRD, "Dana Gourrier is credited as Odessa 'Bird' Clay", "casting", "fact", "supported", [("imdb", "supports"), ("deadline", "supports")])
claim(RUDY, "Kai Parham is credited as Rudy Clay", "casting", "fact", "supported", [("imdb", "supports"), ("mxdwn", "supports")])
claim(LISTON, "Amin Joseph is credited as Sonny Liston", "casting", "fact", "supported", [("imdb", "supports"), ("aol_joseph", "supports")])
claim(GERALDINE, "Erica Tazel is credited as Geraldine Liston", "casting", "fact", "supported", [("imdb", "supports"), ("blex", "supports")])
claim(ALBERTA, "Aimé Donna Kelly is credited as Alberta Jones", "casting", "fact", "supported", [("imdb", "supports"), ("njunkie", "supports")])
claim(BETTY, "Cesili Williams is credited as Betty Shabazz", "casting", "fact", "supported_single_source", [("imdb", "supports")],
      "User mapping and IMDb agree, but a web search found no independent outlet. Discrepancy kept open.")
claim(BIRD, "Odessa Grady Clay was Muhammad Ali's mother", "history", "fact", "unchecked", [("eig_book", "context")], "Widely reported; not yet checked against a cited source.")
claim(BIRD, "Reviews praise Gourrier's performance (e.g. 'an absolute force'; gives the series 'much of its warmth')", "series", "opinion", "supported_single_source", [("wil", "supports")], "Critics' opinions, quoted from snippets; verify wording on the page before quoting.")
claim(SR, "Reviews describe the series' Cash Clay as a hard-drinking, unfaithful, abusive father who also loves his family", "series", "dramatization", "supported_single_source", [("wil", "supports"), ("revolt", "context")], "Describes the dramatization only.")
claim(SR, "The historical Cassius Clay Sr. was taken to court by Odessa for physical abuse and arrested for assault and battery", "history", "allegation", "unchecked",
      [("wiki_mirror_sr", "context"), ("eig_book", "context"), ("npr_eig", "context")], "DO NOT PUBLISH until checked against Eig and, ideally, Louisville court records.")
claim(RUDY, "Rudy Clay later took the name Rahman Ali (spelling also given as Rahaman)", "history", "fact", "unchecked", [("eig_book", "context")], "Spelling conflict between sources.")
claim(LISTON, "Sonny Liston's birth year is uncertain (records vary, c.1930–1932)", "history", "fact", "unchecked", [], "Needs a biography/archival source.")
claim(GERALDINE, "In the series, Geraldine reads a newspaper profile of Liston aloud and softens its harsher passages", "series", "dramatization", "supported_single_source", [("ebert", "supports")], "Described by a review; not yet seen in footage.")
claim(ALBERTA, "Alberta O. Jones negotiated Cassius Clay's first professional contract (1960)", "history", "fact", "supported_single_source", [("blackpast", "supports"), ("jfaj", "supports")], "The family site is not independent. Find a second independent source.")
claim(ALBERTA, "Jones organised the Louisville Sponsoring Group (vs. negotiated with it)", "history", "fact", "conflicting", [("sothebys", "supports"), ("blackpast", "conflicts")], "Sources describe her role differently.")
claim(ALBERTA, "Alberta Jones's birth year: 1930 vs 1931", "history", "fact", "conflicting", [("blackpast", "context")], "Sources disagree.")
claim(ALBERTA, "Jones was killed in 1965 and the case remains unsolved", "history", "fact", "supported", [("wfpl", "supports"), ("uofl_law", "supports")], "Sensitive: violent death.")

# relationships (character-level, as credited/described; scoped to series)
def rel(a, b, t, d=None):
    if not cat.one("SELECT 1 FROM relationship WHERE from_character=? AND to_character=? AND rel_type=?", a, b, t):
        cat.create("relationship", dict(from_character=a, to_character=b, rel_type=t, description=d, scope_note="as depicted/credited; series period 1960–64"))
for a, b, t in [(BIRD, ALI, "mother of"), (BIRD, RUDY, "mother of"), (BIRD, SR, "wife of"), (SR, ALI, "father of"), (SR, RUDY, "father of"),
                (RUDY, ALI, "younger brother of"), (LISTON, ALI, "opponent of"), (GERALDINE, LISTON, "wife of"), (ALBERTA, ALI, "attorney for")]:
    rel(a, b, t)

# ---------------- profiles for the six priority characters (+ two added)
P = {
 BIRD: dict(
  role_reported="(S1) The emotional centre of the Clay household. Critics single out Gourrier's warmth and say she gives Bird's anger a clear reason. One critique: Bird gets too little time away from Cash and the boys. *Reported by reviews; not seen.*",
  arc=["Beginning / turning points / where the footage leaves her: **Pending footage review.** No timestamps exist."],
  standout=["Pending footage review. Leads to check: moments of warmth with her sons, and any scene where her anger is given a clear reason (per reviews)."],
  angles=["**A. Character portrait (recommended): 'The corner before the corner.'** Bird as her sons' first protector and believer. Warmth plus resolve; low spoiler risk.",
          "B. Relationship montage: Bird & Cassius, mother and son across the series.",
          "C. Performance showcase: Dana Gourrier's range, from humour to warmth to anger. Use only if the footage shows that range."],
  posts=["Credit line: `Dana Gourrier as Odessa 'Bird' Clay · The Greatest (Prime Video)`. No @mention: handle not verified.",
         "Hashtags (to check in-app): #TheGreatest #MuhammadAli #CharacterStudy #DanaGourrier"],
  actor_bio="Not yet researched from a reliable source. Do not use until sourced.",
  historical_bio="Odessa Grady Clay, Muhammad Ali's mother (CLM unchecked). Dates and details are pending a source check (Eig, *Ali: A Life*; Muhammad Ali Center).",
  show_vs_history="Unknown until the footage is reviewed and the sources are checked.",
  sensitive=["Depicted as the spouse of an abusive husband (per reviews). Centre her agency, never use abuse as the hook, add a content note where depicted.", "Spoilers: S1 for the portrait angle."],
  open_questions=["Historical attestation of the nickname 'Bird' (credited; history unchecked).", "Pronunciation of 'Gourrier': verify from an interview or the actor's own usage."]),
 RUDY: dict(
  role_reported="(S1) Cassius's younger brother and close confidant (per reviews). A separately credited young portrayal exists (Lennox Leacock, 'Young Rudy').",
  arc=["Pending footage review."], standout=["Pending footage review."],
  angles=["A. Relationship montage: 'The Clay Brothers' (with CHR-000001), chronological; young and adult portrayals kept separately labelled.",
          "B. Character portrait: Rudy in his brother's shadow. Only if the footage supports it."],
  posts=["Credit line: `Kai Parham as Rudy Clay · The Greatest (Prime Video)`. Young portrayal: `Lennox Leacock as Young Rudy`. No @mentions (unverified)."],
  historical_bio="Rudolph Clay, later Rahman/Rahaman Ali (spelling conflict; unchecked). Check his current living status before choosing tense.",
  sensitive=["Low. Religion/NOI context requires neutral framing."], open_questions=["Preferred spelling: Rahman vs Rahaman."]),
 ALI: dict(
  role_reported="(S1) The lead: Cassius Clay's path from Louisville to the 1964 title fight. (S3) The finale centres on the Liston fight (per episode guides). Young portrayal 'Young Cassius' (Elias Leacock) is queued for review: the name rule matches both Cassius Jr. and Sr.",
  arc=["Pending footage review."], standout=["Pending footage review."],
  angles=["A. Performance showcase: Jaalen Best's range.", "B. Character arc (S3 if the fight result is shown; spoiler card required)."],
  posts=["Credit line: `Jaalen Best as Cassius Clay / Muhammad Ali`. Fight shots may show stunt double Daniel Lavigne (credited): confirm per shot before labelling."],
  sensitive=["Racism (Jim Crow Louisville), religion, possible period slurs."]),
 SR: dict(
  role_reported="(S1) Head of the household; reviews describe drinking, infidelity and violence at home, alongside love for his family and conflict over his son's success. *Dramatization as reported.*",
  arc=["Pending footage review."], standout=["Pending footage review."],
  angles=["A. Performance showcase (hold): Omari Hardwick's range. Requires survivor-centred framing.", "B. Thematic study: fathers and sons in The Greatest, with Bird's perspective preserved."],
  posts=["Credit line: `Omari Hardwick as Cassius Clay Sr.`. Never phrase the character's abuse as the actor's."],
  show_vs_history="The historical abuse allegation (CLM, unchecked) must not be stated as fact until verified. Use 'In the series, this scene depicts…'.",
  sensitive=["**HIGH:** domestic violence, alcoholism. Content note required. Resource card considered (verified details only). Flag for review before render."]),
 LISTON: dict(
  role_reported="(S1) Heavyweight champion and Ali's rival; (S3) the title fight. Young portrayal 'Young Sonny' (Jed Strathum Kirunda, credited as Jed Stathum Kirunda) is queued: 'Sonny' also matches Sonny Banks. Fight doubles credited: Aaron D. Alexander, Tommy Europe.",
  arc=["Pending footage review."], standout=["Pending footage review."],
  angles=["A. Relationship portrait: Sonny & Geraldine (tenderness vs. public image).", "B. Character portrait: the man behind the 'menace' headlines. Avoid repeating period stereotypes."],
  posts=["Credit line: `Amin Joseph as Sonny Liston`."],
  sensitive=["Incarceration and alleged mob ties are **contested allegations**: present them as disputed. Fight violence."],
  open_questions=["Possible match for your phrase 'Connie lesson' (unconfirmed)."]),
 GERALDINE: dict(
  role_reported="(S1) A review describes her reading a newspaper profile of Sonny aloud and softening its harsher passages. *Reported; not seen.*",
  arc=["Pending footage review."], standout=["Lead to verify: the newspaper-reading scene."],
  angles=["A. Relationship montage with CHR-000005 (recommended for her).", "B. Character portrait: only if she has enough material across her 5 credited episodes."],
  posts=["Credit line: `Erica Tazel as Geraldine Liston`."],
  historical_bio="The documented record is thin; high risk of overstatement. Research needed.", sensitive=["Low–medium (period press stereotyping)."]),
 ALBERTA: dict(
  role_reported="Credited in 3 episodes (IMDb). Series role: pending footage review.",
  historical_bio="Alberta O. Jones, Louisville attorney: negotiated Clay's first professional contract (1960; single independent source). Her role with the Louisville Sponsoring Group is described inconsistently. Birth year 1930 or 1931 (conflict). Killed in 1965; the case is unsolved (two sources).",
  angles=["Historical-context breakdown: 'The lawyer who signed Cassius Clay'. Strong deep-dive candidate once claims are second-sourced."],
  sensitive=["Violent death (1965), unsolved: describe factually, with no speculation about perpetrators."]),
 BETTY: dict(
  role_reported="Credited in 2 episodes (IMDb). **Discrepancy:** the credit is supported by your mapping and the IMDb paste only; no independent outlet found.",
  open_questions=["Find an independent confirmation (end credits or press)."]),
}
for ch, prof in P.items():
    cat.update(ch, {"profile_json": json.dumps(prof, ensure_ascii=False)}, note="research profile")

# 'Connie lesson' — unresolved reference, never auto-resolved
intake.queue(cat, None, "unresolved_reference", {"phrase": "Connie lesson", "issue": "user's earlier phrase; possible matches only — awaiting confirmation"},
             [LISTON, char_by_name("Sonny Banks")])

# ---------------- rights register seeds
RIGHTS = [
    ("Episode footage, The Greatest S1 (any source)", "footage", None, "Unknown", "No permission document. A Prime subscription or offline download is not a licence."),
    ("Actor headshots (IMDb-linked)", "photo", None, "Unknown", "Not supplied. Internal reference only, even once obtained."),
    ("Iman Yael recorded voice / authorized digital voice", "voice", "Iman Yael", "Unknown", "No sample or service connection supplied; consent document needed."),
    ("Iman Yael likeness (digital presenter)", "likeness", "Iman Yael", "Unknown", "Not supplied."),
    ("Series score / music in clips", "music", None, "Unknown", "Footage permission does not imply music permission; keep a clean audio version."),
    ("Watermark font: DejaVu Sans (Bitstream Vera derivative)", "font", "DejaVu fonts project", "Documented permission", "Free licence permits embedding in rendered video."),
]
for desc, cls, holder, status, cond in RIGHTS:
    if not cat.one("SELECT 1 FROM rights WHERE asset_description=?", desc):
        cat.create("rights", dict(asset_description=desc, asset_class=cls, holder=holder, status=status, conditions=cond, platforms_json="[]"))
if not cat.one("SELECT 1 FROM voice"):
    cat.create("voice", dict(owner="Iman Yael", kind="recorded", status="not_supplied"))

cat.commit()
from tic.intake import summary  # noqa: E402
for k, r in reports.items():
    print(f"{k:14s} {'(no-op: already ingested) ' if r.get('idempotent_noop') else ''}{summary(r)}")

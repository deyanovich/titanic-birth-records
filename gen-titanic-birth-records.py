#!/usr/bin/env python3
"""Generate titanic-birth-records.json — fictional birth records for the
passengers of the RMS Titanic, kept as historically plausible as a
synthetic dataset can be.

Inputs (all in this directory):

  titanic.csv   the classic Kaggle training table (891 passengers,
                PassengerId 1-891)
  test.csv      the Kaggle evaluation table (418 passengers,
                PassengerId 892-1309) — used so that records citing
                a passenger the training table has never heard of
                cite a *real* one
  titanic3.csv  Thomas Cason's full 1309-passenger compilation
                (Vanderbilt); its home.dest column anchors each
                passenger's origin

Output:

  titanic-birth-records.json   one JSON document, eight archives, each with
                        the structure its real-world counterpart had
                        in 1912. Nothing in it reveals survival.

The world of 1912 is taken seriously: Lebanon and Syria are Ottoman
(nüfus registers, Rumi years), Croatia and Hungary are one empire
(Latin parish matricula), the Russian Empire keeps metrical books on
the Julian calendar, Sweden keeps church books with patronymics, the
English GRO index gives only a registration quarter, and married
women appear in their birth records under their maiden names.

Everything is seeded — same inputs, same output, byte for byte.
"""

import csv
import json
import random
import re
from datetime import date, timedelta

rng = random.Random(48)

SAIL = date(1912, 4, 10)  # Southampton departure

# ----------------------------------------------------------------- #
# Load the three tables and stitch them into one 1309-passenger list #
# ----------------------------------------------------------------- #

def norm_name(s):
    return re.sub(r'["\s]+', " ", s).strip().lower()

def load():
    train = list(csv.DictReader(open("titanic.csv")))
    test = list(csv.DictReader(open("test.csv")))
    t3 = list(csv.DictReader(open("titanic3.csv")))
    t3k = {}
    for r in t3:
        t3k[(norm_name(r["name"]), r["ticket"].strip())] = r
    people = []
    for r in train + test:
        m = t3k.get((norm_name(r["Name"]), r["Ticket"].strip()))
        people.append({
            "pid": int(r["PassengerId"]),
            "name": r["Name"],
            "sex": r["Sex"],
            "age": float(r["Age"]) if r["Age"] else None,
            "sibsp": int(r["SibSp"]),
            "parch": int(r["Parch"]),
            "ticket": r["Ticket"].strip(),
            "pclass": r["Pclass"],
            "embarked": r["Embarked"],
            "home": (m or {}).get("home.dest", "") or "",
        })
    return people

# ----------------------------------------------------------------- #
# Name parsing                                                       #
# ----------------------------------------------------------------- #

TITLES = ("Mr", "Mrs", "Miss", "Master", "Don", "Rev", "Dr", "Mme",
          "Ms", "Major", "Lady", "Sir", "Mlle", "Col", "Capt",
          "the Countess", "Jonkheer", "Dona")

def parse_name(raw):
    """'Cumings, Mrs. John Bradley (Florence Briggs Thayer)' ->
    surname, title, given (his), maiden ('Florence Briggs Thayer')."""
    m = re.match(r"^(.*?),\s*([A-Za-z ]+)\.\s*(.*)$", raw)
    if not m:
        return raw.strip(), "", "", None
    surname, title, rest = m.group(1).strip(), m.group(2).strip(), m.group(3)
    maiden = None
    pm = re.search(r"\(([^)]*)\)", rest)
    if pm:
        maiden = re.sub(r'"[^"]*"', "", pm.group(1)).strip()
        rest = rest[:pm.start()].strip()
    given = re.sub(r'"[^"]*"', "", rest).strip().strip('"')
    return surname, title, given, maiden

def recorded_identity(p):
    """The name a birth record would carry: married women under
    their maiden names, everyone else as on the manifest. A man
    whose manifest entry keeps his original name in parentheses
    ('Pickard, Mr. Berk (Berk Trembisky)') is recorded under that
    original; parentheses that *give* the alias ('(Mr E Haven)')
    leave the manifest name as the real one."""
    surname, title, given, maiden = parse_name(p["name"])
    if p["sex"] == "female" and maiden:
        toks = maiden.split()
        if len(toks) >= 2:
            return toks[-1], " ".join(toks[:-1])
        # '(Sultana)' — a given name alone; keep the married surname
        return surname, maiden
    if p["sex"] == "male" and maiden and not maiden.startswith("Mr"):
        toks = maiden.split()
        if len(toks) >= 2:
            return toks[-1], " ".join(toks[:-1])
    return surname, given or ("Unknown" if not given else given)

# ----------------------------------------------------------------- #
# Origin classification: home.dest first, then names, then priors    #
# ----------------------------------------------------------------- #

UK_SIGNALS = (
    "England", "London", "Cornwall", "Devon", "Somerset", "Kent",
    "Surrey", "Hants", "Wilts", "Essex", "Sussex", "Yorks", "Lancashire",
    "Middlesex", "Bristol", "Liverpool", "Southampton", "Plymouth",
    "West Bromwich", "Birmingham", "Manchester", "Leeds", "Sheffield",
    "Cheshire", "Staffordshire", "Suffolk", "Norfolk", "Notts",
    "Warwickshire", "Worcester", "Gloucester", "Durham", "Northumberland",
    "Wales", "Glamorgan", "Monmouth", "Scotland", "Glasgow", "Edinburgh",
    "Aberdeen", "Jersey", "Guernsey", "Isle of Wight", "St Ives",
    "Penzance", "Bournemouth", "Portsmouth", "Rochester", "Ilford",
    "Harrow", "Ealing", "Bath", "Truro", "Helston", "St Austell",
)

IRISH_SURNAMES = set("""
Moran McCarthy OBrien OConnor ODriscoll ODwyer OLeary OSullivan
OConnell ODonoghue Murphy Kelly Kiernan Lennon Madigan Mangan
McCormack McCoy McDermott McEvoy McGowan McGovern McMahon Mernagh
Mockler Mulvihill Naughton Rice Ryan Scanlan Buckley Bourke Burke
Burns Canavan Carr Connaghton Connolly Conlon Daly Devaney Dooley
Doyle Driscoll Farrell Flynn Foley Gallagher Gilnagh Glynn Hart
Healy Hegarty Henry Horgan Jermyn Keane Kilgannon Duane Connors
Sadlier Morrow Tobin Mullens Mannion Peters Charters Smyth Dewan
Kennedy Hagardon Barry Shaughnessy Delia Emmeth Nemagh Lemon Colbert
McNamee Dodge Sage Sweeney? Moraw
""".split())

ARABIC_SURNAMES = set("""
Attalah Ayoub Baclini Barah Barbara Betros Boulos Caram Chehab Dibo
Doharr Elias Hanna Hassab Hassan Kassem Khalil Lahoud Mamee
Masselmani Moubarek Moussa Najib Nakid Nasser Nicola-Yarred Novel
Peter Razi Saad Samaan Seman Shawah Sleiman Thomas Touma Toufik
Yasbeck Youseff Yousif Yousseff Zabour Emir Albimona Badt Karun
Leeni Jerwan Assaf Banoura Daher Gerios Ibrahim Kalil Khalib Malool
Saade Sarkis Shedid Tannous Torfa Wazli Zakarian Vartanian Sirayanian
""".split())

ARABIC_GIVEN = set("""
Hanna Mansour Mansouer Youssef Yousseff Gerious Gerios Tannous Assad
Fahim Halim Amin Khalil Sleiman Fared Farred Sahid Nassef Fatima
Sultana Malake Jamila Thamine Hileni Banoura Adele Latifa Mantoura
Saiide Nourelain Selini Darwis Sarkis Nakli Wazli Dibo Betros Bertha?
Houssein Hammad Raihed Orsen Mohamed
""".split())

NORDIC_SUFFIXES = ("sson", "ssen", "berg", "gren", "strom", "lund",
                   "qvist", "quist", "dahl", "holm", "stedt", "blom",
                   "sten", "man", "wall", "skog")
FINNISH_SUFFIXES = ("nen", "maki", "niemi", "koski", "jarvi", "kangas",
                    "salo", "aho", "la")
FINNISH_SURNAMES = set("""
Heikkinen Hirvonen Honkanen Hakkarainen Jussila Kallio Nieminen
Panula Pekoniemi Turja Salonen Rintamaki Ilmakangas Riihivouri
Peltomaki Sivola Lahtinen Laitinen Nirva Tikkanen Vanninen Wiklund?
""".split())

SLAVIC_AH_SUFFIXES = ("ic", "vic", "cic", "sic")
AH_SURNAMES = set("""
Stankovic Jalsevac Drazenoic Cacic Culumovic Oreskovic Pavlovic
Hendekovic Calic Coric Turcin Karajic Strilic Pecruic Smiljanic
Turkula? Balkic Dimic Dika Cor Hampe? Vovk Pokrnic Petranec Osman?
""".split())

BULGARIAN_SUFFIXES = ("off", "eff", "ov", "ev")
CHINESE_NAMES = {"Lang", "Ling", "Foo", "Lam", "Chip", "Hee", "Bing"}

RUSSIAN_PIDS_HINTS = set("""
Paulner Sirota Trembisky Wizosky Abelson Willer Aks? Polner
""".split())

def strip_o(s):
    return s.replace("'", "").replace("’", "")

def classify(p):
    """Return an archive key, or None for 'no record recovered'."""
    surname, title, given, maiden = parse_name(p["name"])
    s = strip_o(surname)
    home = p["home"]
    h = home.split("/")[0].strip() if home else ""

    # -- home.dest, the strongest signal ---------------------------- #
    if home:
        if "Syria" in home or "Lebanon" in home:
            return "ottoman"
        if "Ireland" in home:
            return "irish"
        if "Sweden" in home:
            return "swedish"
        if "Finland" in home:
            return "finnish"
        if "Norway" in home:
            return "norwegian"
        if "Denmark" in home:
            return "danish"
        if "Bulgaria" in home or "Greece" in home:
            return None
        if ("Croatia" in home or "Austria" in home or "Hungary" in home
                or "Bosnia" in home or "Slavonia" in home):
            return "austro_hungarian"
        if "Russia" in home:
            return "russian"
        if "France" in home or h.startswith("Paris"):
            return "french"
        if ("Belgium" in home or "Italy" in home or "Switzerland" in home
                or "Germany" in home or "Spain" in home or "Portugal" in home
                or "Holland" in home or "Netherlands" in home
                or "Mexico" in home or "Uruguay" in home or "Argentina" in home
                or "South Africa" in home or "Australia" in home
                or "India" in home or "Siam" in home or "China" in home
                or "Japan" in home or "Egypt" in home or "Cuba" in home
                or "Peru" in home or "Nicaragua" in home
                or "Greece" in home or "Turkey" in home):
            return None
        if any(sig in h for sig in UK_SIGNALS):
            return "gro"
        st = re.search(r",\s*([A-Z]{2})$", h)
        if (st and st.group(1) not in ("ON", "PQ", "MB", "BC", "NS",
                                       "NB", "SK", "AB", "PE", "NF")) \
                or "New York" in h:
            return "us"
        # Canadian or unparsable destination: fall through to names

    # -- name-shape signals ----------------------------------------- #
    if title in ("Mme", "Mlle"):
        return "french"
    if title in ("Don", "Dona") or " y " in surname:
        return None                       # Spain / Latin America
    if s in CHINESE_NAMES:
        return None
    if s in ARABIC_SURNAMES or (given and given.split()[0] in ARABIC_GIVEN):
        return "ottoman"
    if s in RUSSIAN_PIDS_HINTS or (maiden and
            strip_o(maiden.split()[-1]) in RUSSIAN_PIDS_HINTS):
        return "russian"
    if s in FINNISH_SURNAMES or (s.lower().endswith(FINNISH_SUFFIXES)
                                 and len(s) > 4):
        return "finnish"
    if s.lower().endswith("sson") or s.lower().endswith("dotter"):
        return "swedish"
    if s.lower().endswith("sen") and len(s) > 5:
        return "norwegian"
    if s.lower().endswith(NORDIC_SUFFIXES):
        return "swedish"
    if s in AH_SURNAMES or s.lower().endswith(SLAVIC_AH_SUFFIXES):
        return "austro_hungarian"
    if s.lower().endswith(BULGARIAN_SUFFIXES) and len(s) > 4:
        return None                       # Bulgaria — not recovered
    if s.lower().startswith(("van ", "vande", "vander", "de pels")):
        return None                       # Belgium — not recovered
    if p["embarked"] == "Q" or s in IRISH_SURNAMES:
        return "irish"

    # -- priors ------------------------------------------------------ #
    r = rng.random()
    if p["pclass"] == "1":
        return "us" if r < 0.50 else "gro"
    if p["pclass"] == "2":
        return "us" if r < 0.30 else "gro"
    return "us" if r < 0.06 else "gro"

# ----------------------------------------------------------------- #
# Birth dates                                                        #
# ----------------------------------------------------------------- #

def synth_age(p):
    """A plausible age for the 263 passengers the tables leave blank."""
    t = parse_name(p["name"])[1]
    if t == "Master":
        return round(rng.uniform(0.5, 12.5), 1)
    if t == "Miss":
        return round(rng.triangular(1, 39, 21), 1)
    if t == "Mrs":
        return round(rng.triangular(17, 60, 31), 1)
    if t in ("Dr", "Rev", "Major", "Col", "Capt"):
        return round(rng.triangular(30, 62, 45), 1)
    return round(rng.triangular(16, 64, 27), 1)

def birth_date(age):
    """A birth date consistent with 'age at sailing' (floor years)."""
    a = int(age)
    hi = SAIL - timedelta(days=int(age * 365.2425) + 1)
    lo = SAIL - timedelta(days=int((a + 1) * 365.2425) - 1)
    if lo >= hi:
        return hi
    return lo + timedelta(days=rng.randint(0, (hi - lo).days))

def to_julian(d):
    """Gregorian -> Julian calendar date (12 days in the 1800s,
    13 from 1900-03-13 on)."""
    off = 13 if d >= date(1900, 3, 13) else 12
    return d - timedelta(days=off)

MONTHS_EN = ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November",
             "December"]

def prose_date(d):
    return f"{d.day} {MONTHS_EN[d.month - 1]} {d.year}"

def quarter(d):
    # GRO registration ran a few weeks behind the birth
    reg = d + timedelta(days=rng.randint(7, 49))
    return f"{reg.year} Q{(reg.month - 1) // 3 + 1}"

# ----------------------------------------------------------------- #
# Cultural furniture                                                 #
# ----------------------------------------------------------------- #

GRO_DISTRICTS = [
    ("St Pancras", "1b"), ("Islington", "1b"), ("West Ham", "4a"),
    ("Southampton", "2c"), ("Portsea Island", "2b"), ("West Derby", "8b"),
    ("Birkenhead", "8a"), ("Bradford", "9b"), ("Leeds", "9b"),
    ("Bristol", "6a"), ("Guildford", "2a"), ("Basingstoke", "2c"),
    ("Croydon", "2a"), ("Marylebone", "1a"), ("Kensington", "1a"),
    ("Wandsworth", "1d"), ("Redruth", "5c"), ("Penzance", "5c"),
    ("St Austell", "5c"), ("Truro", "5c"), ("Helston", "5c"),
    ("Epsom", "2a"), ("Barton Regis", "6a"), ("Glasgow", "644"),
    ("Edinburgh", "685"), ("Cardiff", "11a"), ("Pontypridd", "11a"),
]
ENGLISH_MAIDEN = """Cox Turner Webb Hall Fletcher Payne Wood Harris
Clarke Baker Palmer Reed Mills Gray Holmes Chapman Pearce Norris Dean
Berry Hunt Rowe Trevaskis Pascoe Hicks Eddy Odgers Tremayne""".split()

IRISH_PARISHES = [
    ("Addergoole", "Mayo"), ("Lackagh", "Galway"), ("Kilcummin", "Kerry"),
    ("Kilglass", "Sligo"), ("Clonbur", "Galway"), ("Athlone", "Westmeath"),
    ("Ballysadare", "Sligo"), ("Aglish", "Waterford"),
    ("Kilfree", "Sligo"), ("Cahersiveen", "Kerry"),
    ("Mostrim", "Longford"), ("Kiltoghert", "Leitrim"),
]
IRISH_M = "Patrick John Michael Thomas James Martin Denis William Daniel Edward".split()
IRISH_F = "Mary Bridget Margaret Catherine Ellen Nora Hanora Johanna Annie Delia".split()
IRISH_MAIDEN = """Gallagher Flaherty Kennedy Duffy Costello Higgins
Walsh Byrne Nolan Quinn Brennan Corcoran Devine Loftus""".split()
TOWNLANDS = """Knockfarnaught Derrymore Carrowskeheen Ballydavid
Gortnasillagh Cloonkeen Lisheen Tullynahaia Cummeen Ardagh""".split()

SWE_PARISHES = [
    ("Vissefjärda", "Kronobergs län"), ("Alseda", "Jönköpings län"),
    ("Örkened", "Kristianstads län"), ("Gunnarskog", "Värmlands län"),
    ("Kila", "Södermanlands län"), ("Bjuv", "Malmöhus län"),
    ("Torhamn", "Blekinge län"), ("Hudiksvall", "Gävleborgs län"),
]
FIN_PARISHES = [
    ("Kestilä", "Uleåborgs län"), ("Ilmajoki", "Vasa län"),
    ("Karvia", "Åbo och Björneborgs län"), ("Elimäki", "Viborgs län"),
    ("Kuopio", "Kuopio län"),
]
NOR_PARISHES = [("Ål", "Buskerud"), ("Trondenes", "Troms"),
                ("Sandar", "Vestfold"), ("Skudenes", "Rogaland")]
DAN_PARISHES = [("Vejstrup", "Svendborg"), ("Sæby", "Hjørring")]
SWE_M = "Johan Anders Erik Karl Nils Per Gustaf Olof Lars Sven August Axel".split()

def patro_son(name):
    return name + ("son" if name.endswith("s") else "sson")

def patro_dotter(name):
    return name + ("dotter" if name.endswith("s") else "sdotter")
SWE_F = "Anna Maria Karin Ingrid Elin Hulda Emma Ida Selma Alma Hilda".split()
FIN_M = "Juho Matti Antti Heikki Mikko Tuomas Erkki Jussi".split()
FIN_F = "Maria Aino Helmi Hilja Sanna Liisa Anna Eeva".split()
FIN_MAIDEN = """Korhonen Virtanen Mäkinen Järvinen Laine Heikkilä
Koskinen Aaltonen""".split()
FARMS = """Norra Bäckebo Stensjö Långasjö Hultet Ekeberga Björkelund
Sjöatorp Kvarnamåla Gäddeviksås Fagerhult""".split()

FR_COMMUNES = [
    ("Paris 9e", "Seine"), ("Paris 17e", "Seine"), ("Le Havre",
     "Seine-Inférieure"), ("Cherbourg", "Manche"), ("Rouen",
     "Seine-Inférieure"), ("Lyon 2e", "Rhône"), ("Nantes",
     "Loire-Inférieure"), ("Bordeaux", "Gironde"),
]
FR_PROF = ("négociant cultivateur charpentier employé_de_commerce "
           "instituteur coiffeur mécanicien boulanger").replace("_", " ").split()
FR_M = "Émile Albert Henri Louis Georges Jean Pierre Marcel Auguste".split()
FR_F = "Marie Jeanne Louise Berthe Marguerite Hélène Augustine".split()
FR_MAIDEN = """Lefèvre Moreau Dubois Fournier Garnier Rousseau Mercier
Blanchard Chevalier Lambert""".split()

US_PLACES = [
    ("New York", "New York"), ("Pennsylvania", "Philadelphia"),
    ("Pennsylvania", "Allegheny"), ("Illinois", "Cook"),
    ("Ohio", "Cuyahoga"), ("Massachusetts", "Suffolk"),
    ("Minnesota", "Hennepin"), ("Michigan", "Wayne"),
    ("Wisconsin", "Milwaukee"), ("Missouri", "St. Louis"),
    ("New Jersey", "Essex"), ("Connecticut", "Hartford"),
]
US_M = "William John George Charles Frank Joseph Henry Robert Edward Walter".split()
US_F = "Mary Anna Emma Elizabeth Margaret Minnie Ida Clara Bertha Alice".split()
US_MAIDEN = """Miller Smith Brown Davis Wilson Moore Taylor Anderson
Thomas Jackson Harris Martin""".split()
INFORMANTS = ["attending physician", "midwife", "father", "registrar of the town"]

OTTOMAN_VILLAGES = [
    ("Hardin", "Batroun"), ("Kfar Mishki", "Rashaya"),
    ("Zgharta", "Tripoli"), ("Tula", "Batroun"), ("Bsharri", "Tripoli"),
    ("Zahlé", "Zahlé"), ("Douma", "Batroun"), ("Shweir", "Metn"),
    ("Tibnin", "Tyre"), ("Kfar Kila", "Marjeyoun"),
]
ARMENIAN_VILLAGES = [("Keghi", "Erzurum"), ("Hüseynig", "Harput"),
                     ("Palu", "Harput")]
OTT_M = ("Yousseff Ibrahim Boutros Tannous Gerios Hanna Elias Assad "
         "Khalil Nassif Mansour Selim Faris Habib").split()
OTT_F = ("Mariam Katrin Sultana Zahra Nazira Wardeh Jamileh Hasna "
         "Saada Latifeh").split()

AH_PARISHES = [
    ("Vagovina", "Zagrabiensis"), ("Bukovlje", "Bosniensis et Sirmiensis"),
    ("Podgorač", "Bosniensis et Sirmiensis"), ("Široka Kula", "Segniensis"),
    ("Batina", "Quinque Ecclesiensis"), ("Nagykanizsa", "Sabariensis"),
]
AH_M = "Ivan Josip Mato Stjepan Franjo Marko Ilija Petar János Mihály".split()
AH_F = "Ana Marija Kata Jela Bara Manda Ivka Terézia Rozália".split()
AH_MAIDEN = """Horvat Kovačević Babić Novak Marić Jurić Vuković Tóth
Szabó Varga""".split()

RU_GUB = [("Ковенская", "Kovno"), ("Виленская", "Vilna"),
          ("Гродненская", "Grodno"), ("Минская", "Minsk"),
          ("Волынская", "Volhynia"), ("Херсонская", "Kherson")]
RU_M = "Shmuel Avrum Berk Duvid Itsko Leyb Movsha Usher Yankel Gersh".split()
RU_F = "Khana Rivka Sora Feiga Gitel Malka Ester Leya".split()

# ----------------------------------------------------------------- #
# Family structure: shared parents where the manifest implies them    #
# ----------------------------------------------------------------- #

def couple_parents(group):
    """If a 'Mrs. <Husband>' travels in the group, the on-board (or
    implied) couple names the children's parents exactly."""
    surname = group[0]["surname"]
    wife = next((g for g in group if g["title"] == "Mrs"), None)
    if wife:
        _, _, husband_given, maiden = parse_name(wife["p"]["name"])
        # 'Mrs. Catherine (Catherine Rizk)' — a widow travels under her
        # own given name, not her late husband's; no father name there
        if (husband_given and maiden
                and husband_given.split()[0] == maiden.split()[0]):
            husband_given = None
        father = f"{husband_given} {surname}".strip() if husband_given else None
        mother = maiden if maiden else None
        return father, mother
    return None, None

# ----------------------------------------------------------------- #
# The generator proper                                               #
# ----------------------------------------------------------------- #

def main():
    people = load()

    # classify everyone (rng order matters: keep pid order)
    for p in people:
        p["archive"] = classify(p)
        surname, title, given, maiden = parse_name(p["name"])
        p["surname"], p["title"], p["given"], p["maiden"] = \
            surname, title, given, maiden

    # --- name reveals: Westernized manifest, original in the record --
    # (similar roots; the Syrian and Russian-Jewish Anglicizations are
    # the documented pattern)
    REVEAL_SURNAME = {
        "Peter": "Boutros",       # 'Peter' family — Boutros
        "Novel": "Nawfal",
        "Thomas": "Tuma",
        "Leeni": "Zenni",         # manifest itself notes 'Philip Zenni'
        "Abelson": "Abelzon",
        "Paulner": "Polner",
        "Willer": "Veller",
        "Seman": "Suleiman",
    }
    REVEAL_GIVEN = {
        "Samuel": "Shmuel", "Michael J": "Mikhail", "Maurice": "Movsha",
        "Uscher": "Usher", "Aaron": "Arn", "Betros": "Boutros",
        "Novel": "Nawfal",
    }

    # --- lost records / uncovered origins ---------------------------
    # a seeded ~6% of otherwise-covered records simply did not survive
    for p in people:
        p["lost"] = False
        if p["archive"] is not None:
            drop = 0.03 if p["age"] is None else 0.06
            if rng.random() < drop:
                p["lost"] = True

    # --- ages and birth dates ---------------------------------------
    for p in people:
        true_age = p["age"] if p["age"] is not None else synth_age(p)
        p["true_age"] = true_age
        p["birth"] = birth_date(true_age)

    # --- deliberate contradictions (~5% of covered, age known) ------
    # people lied about their ages; the records did not
    contradicted = []
    candidates = [p for p in people
                  if p["archive"] and not p["lost"] and p["age"] is not None]
    for p in candidates:
        if rng.random() < 0.05:
            shift = rng.choice([-6, -5, -4, -3, -2, 2, 3, 4, 5, 6])
            try:
                p["birth"] = p["birth"].replace(year=p["birth"].year - shift)
            except ValueError:            # Feb 29
                p["birth"] = p["birth"].replace(year=p["birth"].year - shift,
                                                day=28)
            contradicted.append((p["pid"], shift))
    # --- the calendar witness ---------------------------------------
    # One metrical-book passenger is pinned to a birth just after
    # New Year, so his Julian-labeled date crosses back into the
    # previous December (1882-01-06 Gregorian = 1881-12-25 Julian):
    # naive year extraction gets his birth year wrong by one, and
    # only a calendar-aware reading recovers it. Samuel Abelson's
    # manifest age (30) admits the date exactly.
    for p in people:
        if p["name"].startswith("Abelson, Mr. Samuel"):
            p["birth"] = date(1882, 1, 6)
    contradicted = [(pid, sh) for (pid, sh) in contradicted
                    if not any(x["pid"] == pid and
                               x["name"].startswith("Abelson, Mr. Samuel")
                               for x in people)]

    # --- family groups: shared parents ------------------------------
    groups = {}
    for p in people:
        if p["sibsp"] > 0 or p["parch"] > 0:
            groups.setdefault((p["ticket"], p["surname"]), []).append(
                {"p": p, "surname": p["surname"], "title": p["title"]})
    parent_assign = {}                    # pid -> (father, mother)
    for key, group in groups.items():
        if len(group) < 2:
            continue
        arch = group[0]["p"]["archive"]
        father, mother = couple_parents(group)
        gen_parents = None
        for g in group:
            p = g["p"]
            # the husband: his given name starts with the father-name the
            # wife's manifest entry implies ('Mrs. Carl Oscar (…)')
            fg = father.split()[:-1] if father else []
            is_husband = (p["title"] == "Mr" and p["sibsp"] > 0 and fg
                          and p["given"].split()[:len(fg)] == fg
                          and not p["given"].endswith("Jr"))
            if p["title"] == "Mrs" or is_husband:
                continue                  # the couple keeps its own parents
            if p["parch"] > 0 and (father or mother):
                # complete a half-known couple (widow aboard, husband
                # not) with a generated other half, shared family-wide
                parent_assign[p["pid"]] = ("__HALF__", key, father, mother)
            else:
                if gen_parents is None:
                    gen_parents = ("__GEN__", key)  # filled per-archive later
                parent_assign[p["pid"]] = gen_parents

    # --- hidden sibling pairs: maiden name == another surname -------
    hidden = []
    by_surname = {}
    for p in people:
        by_surname.setdefault(p["surname"], []).append(p)
    for p in people:
        if len(hidden) >= 3:
            break
        if p["maiden"] and p["archive"] and not p["lost"] \
                and p["pclass"] != "1":
            mtoks = p["maiden"].split()
            if len(mtoks) < 2:
                continue
            msur = mtoks[-1]
            for q in by_surname.get(msur, []):
                # the sibling's *birth* surname must be the maiden name:
                # a married woman whose manifest surname merely matches
                # does not qualify
                if (q["ticket"] != p["ticket"] and q["archive"]
                        and not q["lost"] and q["pid"] != p["pid"]
                        and q["pclass"] != "1"
                        and recorded_identity(q)[0] == msur
                        and q["pid"] not in parent_assign
                        and p["pid"] not in parent_assign):
                    hidden.append((p, q))
                    break

    # generated parent pools per archive, deduplicated
    used_parent_pairs = set()

    def gen_parent_pair(arch, surname, patronym_stem=None):
        for _ in range(40):
            if arch == "swedish":
                f = (f"{patronym_stem or rng.choice(SWE_M)} "
                     f"{patro_son(rng.choice(SWE_M))}")
                m = f"{rng.choice(SWE_F)} {patro_dotter(rng.choice(SWE_M))}"
            elif arch == "finnish":
                f = f"{rng.choice(FIN_M)} {surname}"
                m = f"{rng.choice(FIN_F)} {rng.choice(FIN_MAIDEN)}"
            elif arch in ("norwegian", "danish"):
                f = f"{rng.choice(SWE_M)} {surname}"
                stem = rng.choice(SWE_M)
                m = (f"{rng.choice(SWE_F)} "
                     f"{stem}{'datter' if stem.endswith('s') else 'sdatter'}")
            elif arch == "irish":
                f = f"{rng.choice(IRISH_M)} {surname}"
                m = f"{rng.choice(IRISH_F)} {rng.choice(IRISH_MAIDEN)}"
            elif arch == "french":
                f = f"{rng.choice(FR_M)} {surname}"
                m = f"{rng.choice(FR_F)} {rng.choice(FR_MAIDEN)}"
            elif arch == "us":
                f = f"{rng.choice(US_M)} {surname}"
                m = f"{rng.choice(US_F)} {rng.choice(US_MAIDEN)}"
            elif arch == "ottoman":
                f = f"{rng.choice(OTT_M)} {surname}"
                m = f"{rng.choice(OTT_F)} {rng.choice(OTT_M)}"
            elif arch == "austro_hungarian":
                f = f"{rng.choice(AH_M)} {surname}"
                m = f"{rng.choice(AH_F)} {rng.choice(AH_MAIDEN)}"
            elif arch == "russian":
                f = f"{rng.choice(RU_M)} {surname}"
                m = f"{rng.choice(RU_F)} {rng.choice(RU_M)}"
            else:                          # gro
                f = f"{rng.choice(US_M)} {surname}"
                m = f"{rng.choice(US_F)} {rng.choice(ENGLISH_MAIDEN)}"
            if f.split()[0] == f.split()[-1]:
                continue                  # 'Khalil Khalil' — try again
            if (f, m) not in used_parent_pairs:
                used_parent_pairs.add((f, m))
                return f, m
        return f, m

    # resolve generated family parents (one pair per family, shared)
    family_parents = {}
    for pid, val in list(parent_assign.items()):
        if isinstance(val, tuple) and val[0] in ("__GEN__", "__HALF__"):
            key = val[1]
            if key not in family_parents:
                p = next(x for x in people if x["pid"] == pid)
                stem = None
                if p["surname"].endswith("sson"):
                    stem = p["surname"][:-4]
                f, m = gen_parent_pair(p["archive"] or "gro",
                                       p["surname"], stem)
                if val[0] == "__HALF__":
                    f, m = val[2] or f, val[3] or m
                family_parents[key] = (f, m)
            parent_assign[pid] = family_parents[key]

    # hidden pairs: force same archive + same parents
    for p, q in hidden:
        arch = q["archive"]
        p["archive"] = arch
        msur = p["maiden"].split()[-1]
        pair = gen_parent_pair(arch, msur)
        parent_assign[p["pid"]] = pair
        parent_assign[q["pid"]] = pair

    # --- emit certificates per archive ------------------------------
    def parents_for(p, arch):
        if p["pid"] in parent_assign:
            return parent_assign[p["pid"]]
        stem = p["surname"][:-4] if p["surname"].endswith("sson") else None
        rec_sur = recorded_identity(p)[0]
        return gen_parent_pair(arch, rec_sur, stem)

    gro_entries, irish, swe, actes, us, ottoman, matricula, metrical = \
        [], {}, {}, [], {}, [], {}, []

    # a family registers its births in one place, not five
    family_place = {}

    def place_for(p, poolkey, pool):
        if p["sibsp"] > 0 or p["parch"] > 0:
            key = (p["ticket"], p["surname"], poolkey)
            if key not in family_place:
                family_place[key] = rng.choice(pool)
            return family_place[key]
        return rng.choice(pool)

    emitted = 0
    for p in sorted(people, key=lambda x: x["pid"]):
        arch = p["archive"]
        if arch is None or p["lost"]:
            continue
        emitted += 1
        rec_sur, rec_given = recorded_identity(p)
        # apply the reveal layer — only where the manifest name was the
        # Westernized one (Ottoman and Russian subjects)
        if arch in ("ottoman", "russian"):
            if p["surname"] in REVEAL_SURNAME and (p["sex"] == "male"
                                                   or not p["maiden"]):
                rec_sur = REVEAL_SURNAME[p["surname"]]
            if rec_given in REVEAL_GIVEN:
                rec_given = REVEAL_GIVEN[rec_given]
        father, mother = parents_for(p, arch)
        # the record keeps the original family name on the parents too
        if arch in ("ottoman", "russian") and p["surname"] in REVEAL_SURNAME:
            def _orig(nm):
                toks = nm.split()
                if toks and toks[-1] == p["surname"]:
                    toks[-1] = REVEAL_SURNAME[p["surname"]]
                return " ".join(toks)
            father, mother = _orig(father), _orig(mother)
        first_given = rec_given.split()[0] if rec_given else rec_sur
        b = p["birth"]
        pid = p["pid"]

        if arch == "gro":
            district, vol = place_for(p, "gro", GRO_DISTRICTS)
            gro_entries.append({
                "surname": rec_sur, "given": rec_given,
                "mother_maiden": mother.split()[-1],
                "district": district, "quarter": quarter(b),
                "volume": vol, "page": rng.randint(1, 620),
                "passenger_id": pid,
            })
        elif arch == "irish":
            parish, county = place_for(p, "ir", IRISH_PARISHES)
            irish.setdefault((parish, county), []).append({
                "child": f"{rec_given} {rec_sur}".strip(),
                "date": prose_date(b),
                "father": father, "mother": mother,
                "sponsors": [f"{rng.choice(IRISH_M)} {rng.choice(IRISH_MAIDEN)}",
                             f"{rng.choice(IRISH_F)} {rng.choice(IRISH_MAIDEN)}"],
                "townland": place_for(p, "tl", TOWNLANDS),
                "passenger_id": pid,
            })
        elif arch in ("swedish", "finnish", "norwegian", "danish"):
            pool = {"swedish": SWE_PARISHES, "finnish": FIN_PARISHES,
                    "norwegian": NOR_PARISHES, "danish": DAN_PARISHES}[arch]
            parish, lan = place_for(p, "ky", pool)
            swe.setdefault((parish, lan), {}).setdefault(
                place_for(p, "farm", FARMS), []).append({
                    "namn": f"{rec_given} {rec_sur}".strip(),
                    "född": b.isoformat(),
                    "fader": father, "moder": mother,
                    "passenger_id": pid,
                })
        elif arch == "french":
            commune, dept = place_for(p, "fr", FR_COMMUNES)
            actes.append({
                "numéro": rng.randint(1, 980),
                "commune": commune, "département": dept,
                "prénoms": rec_given or first_given, "nom": rec_sur,
                "né_le": b.isoformat(),
                "père": {"nom": father, "profession": rng.choice(FR_PROF)},
                "mère": {"nom": f"{mother.split()[0]} {rec_sur}",
                         "nom_de_jeune_fille": mother.split()[-1]},
                "témoins": [f"{rng.choice(FR_M)} {rng.choice(FR_MAIDEN)}",
                            f"{rng.choice(FR_M)} {rng.choice(FR_MAIDEN)}"],
                "passenger_id": pid,
            })
        elif arch == "us":
            state, county = place_for(p, "us", US_PLACES)
            us.setdefault(state, {}).setdefault(county, []).append({
                "name": f"{rec_given} {rec_sur}".strip(),
                "date_of_birth": b.isoformat(),
                "father": father, "mother": mother,
                "informant": rng.choice(INFORMANTS),
                "file_no": f"{b.year}-{rng.randint(100, 99999):05d}",
                "passenger_id": pid,
            })
        elif arch == "ottoman":
            if p["surname"] in ("Sirayanian", "Zakarian", "Vartanian"):
                village, kaza = place_for(p, "arm", ARMENIAN_VILLAGES)
            else:
                village, kaza = place_for(p, "ott", OTTOMAN_VILLAGES)
            entry = {
                "name": f"{first_given} {rec_sur}".strip(),
                "father": father,
                "village": village, "kaza": kaza,
                "year_rumi": b.year - 584,
                "passenger_id": pid,
            }
            if rng.random() < 0.6:
                entry["mother"] = mother
            ottoman.append(entry)
        elif arch == "austro_hungarian":
            parish, dio = place_for(p, "ah", AH_PARISHES)
            matricula.setdefault((parish, dio), []).append({
                "nomen": f"{first_given} {rec_sur}".strip(),
                "natus" if p["sex"] == "male" else "nata": b.isoformat(),
                "pater": father, "mater": mother,
                "patrini": [f"{rng.choice(AH_M)} {rng.choice(AH_MAIDEN)}"],
                "passenger_id": pid,
            })
        elif arch == "russian":
            gub, gub_lat = place_for(p, "ru", RU_GUB)
            metrical.append({
                "familiya": rec_sur,
                "imya": first_given,
                "otchestvo": father.split()[0] + ("ovna" if p["sex"] == "female"
                                                  else "ovich"),
                "data_rozhdeniya": to_julian(b).isoformat(),
                "kalendar": "julian",
                "guberniya": gub_lat,
                "passenger_id": pid,
            })

    # --- assemble ----------------------------------------------------
    doc = {
        "title": "Birth records recovered for passengers of the RMS Titanic",
        "note": ("A fictional reconstruction. Eight registration systems, "
                 "each with the structure its real counterpart had in "
                 "1912. passenger_id refers to the Kaggle Titanic tables."),
        "archives": {
            "gro": {
                "source": "General Register Office, England and Wales — "
                          "index of births",
                "entries": sorted(gro_entries,
                                  key=lambda e: (e["district"], e["surname"])),
            },
            "irish_parishes": [
                {"parish": k[0], "county": k[1],
                 "baptisms": sorted(v, key=lambda e: e["child"])}
                for k, v in sorted(irish.items())
            ],
            "kyrkobocker": {
                parish: {
                    "län": lan,
                    "households": [
                        {"gård": farm,
                         "födda": sorted(entries, key=lambda e: e["född"])}
                        for farm, entries in sorted(farms.items())
                    ],
                }
                for (parish, lan), farms in sorted(swe.items())
            },
            "actes_de_naissance": sorted(actes, key=lambda a: (a["commune"],
                                                               a["numéro"])),
            "us_state_records": {
                state: {county: sorted(recs, key=lambda r: r["name"])
                        for county, recs in sorted(counties.items())}
                for state, counties in sorted(us.items())
            },
            "ottoman_nufus": {
                "source": "Nüfus registers, Mount Lebanon Mutasarrifate "
                          "and the Vilayet of Beirut",
                "note": "year_rumi is a Rumi (Ottoman fiscal) year",
                "records": sorted(ottoman, key=lambda r: (r["village"],
                                                          r["name"])),
            },
            "matricula_baptizatorum": [
                {"parochia": k[0], "dioecesis": k[1],
                 "baptizati": sorted(v, key=lambda e: e["nomen"])}
                for k, v in sorted(matricula.items())
            ],
            "metricheskie_knigi": sorted(metrical,
                                         key=lambda r: (r["guberniya"],
                                                        r["familiya"])),
        },
    }

    with open("titanic-birth-records.json", "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # --- ground truth to stdout (not part of the dataset) ------------
    train = [p for p in people if p["pid"] <= 891]
    covered_train = [p for p in train if p["archive"] and not p["lost"]]
    ageless = [p for p in train if p["age"] is None]
    ageless_covered = [p for p in ageless if p["archive"] and not p["lost"]]
    print(f"records emitted: {emitted} of {len(people)} passengers")
    print(f"  train (1-891): {len(covered_train)} covered, "
          f"{len(train) - len(covered_train)} without a record")
    print(f"  test (892-1309): {emitted - len(covered_train)}")
    print(f"  age-missing train rows covered: {len(ageless_covered)} of "
          f"{len(ageless)}")
    from collections import Counter
    print("  by archive:", dict(Counter(p['archive'] for p in people
                                        if p['archive'] and not p['lost'])))
    print(f"  age contradictions planted: {len(contradicted)}")
    for pid, shift in contradicted[:10]:
        print(f"    pid {pid}: record is {abs(shift)}y "
              f"{'older' if shift > 0 else 'younger'}")
    print("  hidden sibling pairs:")
    for p, q in hidden:
        print(f"    {p['pid']} {p['name']!r}  <->  {q['pid']} {q['name']!r}")

if __name__ == "__main__":
    main()

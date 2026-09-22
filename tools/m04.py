from nb import md, code, ex, SETUP, FOOTER, colab_badge

PATH = "notebooks/phase1_onboarding/M04_popia_governance_deidentification.ipynb"

CELLS = [
md(f"""
# Module 04 · POPIA on day one — governance, de-identification and a research extract
**BioCollaborator Health Informatics Programme** · Phase 1: Onboarding · *Innovate Naturally*

{colab_badge(PATH)}

> **File → Save a copy in Drive**, then run cells top to bottom with **Shift + Enter**.

> ⚖️ *This module teaches data-protection concepts for learning purposes. It is not legal advice. Real projects
> need your organisation's information officer, legal counsel and the relevant ethics approvals.*
"""),
code(SETUP),
code('''
ilanga.brand.banner(4, "POPIA on day one: governance & de-identification", "Phase 1 · Onboarding", minutes=150)
ilanga.brand.ticket(
    "NQ-004", "Sipho Ngcobo", "District Information Manager, Ilanga District Health Services",
    "De-identified ART extract for an approved research study",
    "A university team studying ART outcomes has research ethics approval (ref SYN-HREC-2026-014) and district "
    "permission. We've agreed to share a de-identified extract of adults who have started ART. Only the approved "
    "variables, no way back to a patient, and a summary table we can publish without exposing small groups. "
    "Please also log the access - the Information Regulator could ask us about it one day.",
    ["You can name every direct identifier in the patient register",
     "Extract with exactly: study_id, age_band, sex, subdistrict, art_start_year, latest_vl_suppressed",
     "Keyed pseudonymous study IDs, k-anonymity of at least 5, and at least 90% of eligible patients kept",
     "Published summary table with small cells (1-4) suppressed, plus an access-log entry"],
    priority="High - external data sharing")
'''),
md("""
## Part 1 · POPIA in plain language

The *Protection of Personal Information Act, 2013 (POPIA)* governs how organisations in South Africa process
personal information. For health informaticians, four ideas matter most.

**1. Health information is "special personal information".** Processing it is prohibited unless an exception
applies. Key exceptions include consent, and a specific authorisation for healthcare providers and institutions to
process health information where it's necessary for proper treatment, care and administration — with a duty of
confidentiality. Research can be permitted too, when it serves a public interest, consent is impossible or
disproportionate to obtain, and privacy is protected by sufficient safeguards.

**2. Eight conditions for lawful processing.** Think of them as the "rules of the road":

| Condition | What it looks like in a clinic or data team |
|---|---|
| **Accountability** | Someone is answerable for compliance — usually the information officer |
| **Processing limitation** | Collect only what you need, lawfully and minimally |
| **Purpose specification** | Collect for a specific, defined reason |
| **Further processing limitation** | New uses must be compatible with the original purpose |
| **Information quality** | Keep records accurate and up to date (hello, Module 5) |
| **Openness** | People know their data is being collected and why |
| **Security safeguards** | Protect data technically and organisationally; report breaches |
| **Data subject participation** | People can access and correct their information |

**3. Borders matter.** Sending personal information to another country is restricted unless the recipient offers
adequate protection or another condition applies. Cloud tools — including Colab — make this a daily question.

**4. Breaches must be reported.** If personal information is compromised, the Information Regulator and affected
people must be notified.

Alongside POPIA, the *National Health Act* gives every patient a right to confidentiality of their health
information. Research in public health facilities also needs **research ethics committee approval** and
**provincial approval**, usually through the **National Health Research Database (NHRD)**.

*Dig deeper:* [Information Regulator (South Africa)](https://inforegulator.org.za/)
"""),
md("""
## Part 2 · Classify before you share

Every column you might share falls into one of four classes:

| Class | Meaning | Examples |
|---|---|---|
| **Direct identifier** | Identifies a person on its own | Name, ID number, phone number |
| **Quasi-identifier** | Identifies a person *in combination* | Date of birth, sex, ward, home language |
| **Sensitive** | Harmful if linked to a person | HIV status, viral load, TB outcome |
| **Operational** | Describes the system, not the person | Facility type, lab turnaround time |

> 🩺 **Clinic Corner — why quasi-identifiers are sneaky**
>
> In a small rural ward, "woman, 71, speaks Afrikaans, attends KwaNtaba Clinic" might describe exactly one person.
> No name needed. Attacks that re-identify people from "anonymous" data almost always use quasi-identifiers.

Our data team keeps a **data catalogue** with a signed-off classification for each column. Real teams consult it
before every data share. But first, think for yourself.

### 🌱 Seedling — list the direct identifiers
Look at the patient register's columns and put every **direct identifier** in the list `my_direct_identifiers`.
Decide *before* you peek at the catalogue — the quality gate will tell you what you missed.
"""),
code('''
district = ilanga.load_district()
list(district.patients.columns)
'''),
ex('''
my_direct_identifiers = []   # 👈 e.g. ["first_name", ...]
''', '''
my_direct_identifiers = ["first_name", "surname", "sa_id_number", "passport_number", "phone", "address"]
'''),
code('''
# Now compare with the catalogue
ilanga.data_dictionary("patients")[["column", "privacy_class", "description"]]
'''),
md("""
## Part 3 · The de-identification toolkit

We'll practise each technique on a tiny table first. Here are six people:
"""),
code('''
toy = district.patients.head(6)[["patient_id", "first_name", "surname", "sa_id_number", "date_of_birth",
                                 "sex", "ward", "subdistrict"]].copy()
toy
'''),
md("""
| Technique | What it does | Example |
|---|---|---|
| **Remove** | Drop the column | Remove `first_name` |
| **Pseudonymise** | Replace an ID with a consistent code only the data owner can reverse or reproduce | `ILN-P-000123` → `S-8f3a…` |
| **Generalise** | Make values coarser | Date of birth → age band; ward → sub-district |
| **Suppress** | Hide values that are too rare | A count of 3 → "<5" |
| **Perturb** | Shift values slightly | Move all of one person's dates by the same random number of days |

### Pseudonymisation — why a plain hash is not enough

It's tempting to "anonymise" an ID number by hashing it. But there are only so many possible SA ID numbers — and
you can generate them all from dates of birth, exactly like Module 3 did. An attacker can hash every possible ID and
match. That's called a **dictionary attack**.

The fix is a **keyed hash (HMAC)**: the hash mixes in a secret key that only the data owner holds. No key, no match.
"""),
code('''
import hashlib, hmac

def plain_hash(value):
    return hashlib.sha256(str(value).encode()).hexdigest()[:12]

# In Colab, store real keys in the Secrets panel (the 🔑 icon on the left), never in the notebook.
try:
    from google.colab import userdata
    SECRET_KEY = userdata.get("ILANGA_PSEUDO_KEY").encode()
    print("🔑 Using the key from Colab Secrets.")
except Exception:
    SECRET_KEY = b"demo-key-for-learning-only"
    print("⚠️ Using a demo key. In real work, keys live in a secrets manager - never in code or Git.")

def pseudonymise(value, key=SECRET_KEY):
    return "S-" + hmac.new(key, str(value).encode(), hashlib.sha256).hexdigest()[:12]

toy["plain_hash"] = toy["patient_id"].apply(plain_hash)
toy["study_id"] = toy["patient_id"].apply(pseudonymise)
toy[["patient_id", "plain_hash", "study_id"]]
'''),
md("""
> 💻 **Code Corner — consistent but unlinkable**
>
> Run `pseudonymise("ILN-P-000001")` twice and you get the same answer both times — so researchers can still link
> a patient's records *within* the extract. Change the key and every code changes, so a different project can't
> link its extract to this one. That's why each data release gets its own key.

### Generalisation
"""),
code('''
toy["age"] = ilanga.age_years(toy["date_of_birth"], ilanga.REFERENCE_DATE)
toy["age_band"] = ilanga.age_band(toy["age"], scheme="dhis")
toy[["date_of_birth", "age", "age_band", "ward", "subdistrict"]]
'''),
md("""
## Part 4 · k-anonymity: is anyone alone in the crowd?

A dataset is **k-anonymous** if every combination of quasi-identifiers is shared by at least **k** people.
If k = 1, somebody is unique — and potentially re-identifiable. Many data-sharing agreements ask for k ≥ 5.

Let's measure k for the adult patient register using detailed quasi-identifiers, then generalise.
"""),
code('''
p = district.patients.copy()
p["age"] = ilanga.age_years(p["date_of_birth"], ilanga.REFERENCE_DATE)
adults = p[p["age"] >= 18]

def k_anonymity(df, quasi_identifiers):
    return int(df.groupby(quasi_identifiers, observed=True).size().min())

detailed = ["age", "sex", "ward", "home_language"]
print("Detailed quasi-identifiers  -> k =", k_anonymity(adults, detailed))

sizes = adults.groupby(detailed, observed=True).size()
print(f"{(sizes == 1).sum():,} people are completely unique on these four columns.")
'''),
code('''
adults = adults.assign(age_band=ilanga.age_band(adults["age"], scheme="research"))
coarse = ["age_band", "sex", "subdistrict"]
print("Generalised quasi-identifiers -> k =", k_anonymity(adults, coarse))
adults.groupby(coarse, observed=True).size().describe().round(0)
'''),
md("""
Generalising age into bands and ward into sub-district took us from thousands of unique people to a large, safe
crowd. **But every bit of generalisation costs the researchers some detail.** The craft is finding the least
generalisation that achieves the protection you need.

> 🤝 **Ubuntu Moment — the patient who never signed up for this**
>
> The people in this extract came to a clinic for care, not to be studied. Research on routine data can save lives —
> and it's only legitimate if we honour the trust they placed in the health system. De-identification isn't
> paperwork. It's how we keep that promise.

## Part 5 · Small-cell suppression

Even aggregate tables can leak. If a published table says *"HIV, male, 50+, Ntaba: 2"*, someone in a small community
may know who those two people are. The standard practice is to **suppress counts from 1 to 4** (show "<5").
"""),
code('''
demo = pd.crosstab(adults["subdistrict"], adults["home_language"])
print("Raw counts:")
display(demo)

suppress = lambda v: "<5" if 0 < v < 5 else v
safe = demo.map(suppress) if hasattr(demo, "map") else demo.applymap(suppress)
print("Safe to publish:")
safe
'''),
md("""
> 💻 **Code Corner — one catch**
>
> If you also publish row totals, someone can sometimes subtract the visible cells from the total and recover a
> suppressed value. Professional statisticians apply **secondary suppression** to stop this. Keep it in mind whenever
> you publish totals alongside suppressed cells.

## Part 6 · Access logging and role-based views

Accountability means being able to answer: *who accessed what, when, and why?*
"""),
code('''
access_log = []

def log_access(user, role, dataset, purpose, rows):
    access_log.append({"timestamp": pd.Timestamp.now().floor("s"), "user": user, "role": role,
                       "dataset": dataset, "purpose": purpose, "rows_released": rows})

ROLE_VIEWS = {
    "clinician":   ["patient_id", "first_name", "surname", "date_of_birth", "sex", "phone"],
    "district_analyst": ["patient_id", "sex", "subdistrict", "home_facility_id"],
    "researcher":  [],   # researchers never see the patient register - only approved extracts
}

def view_for(role, df=district.patients):
    return df[ROLE_VIEWS[role]]

view_for("district_analyst").head(3)
'''),
md("""
---
## 🎯 Your turn — build the research extract
Hints: `ilanga.hint("NQ-004.2")` and `ilanga.hint("NQ-004.3")`, levels 1 to 3.

**Eligible patients:** adults (**18+ on 31 December 2025**) who have an HIV record **with an ART start date**.

**Approved variables:**
- `study_id` — keyed pseudonym of `patient_id` (use `pseudonymise`)
- `age_band` — `ilanga.age_band(age, scheme="research")`
- `sex`, `subdistrict`
- `art_start_year` — the year ART started, **generalised as much as needed** for k ≥ 5
- `latest_vl_suppressed` — from each patient's most recent viral load in the data: `True` if below 1,000 copies/mL
  (count `<50` results as suppressed), `False` if not, and empty if they have no viral load result

> 🩺 **Clinic Corner — two thresholds**
>
> Global targets count **<1,000 copies/mL** as virally suppressed. South African clinical guidelines aim lower:
> **<50** is fully suppressed, and **50–999** is low-level viraemia that needs attention. Always state which
> threshold you used — two reports with different thresholds can both be "right" and still disagree.

### 🌿 Sapling — `research_extract`
"""),
ex('''
research_extract = None   # 👈 your code here
''', '''
cond = district.conditions
hiv = cond[(cond["condition"] == "HIV") & cond["art_start_date"].notna()][["patient_id", "art_start_date"]]
x = hiv.merge(district.patients[["patient_id", "date_of_birth", "sex", "subdistrict"]], on="patient_id")
x["age"] = ilanga.age_years(x["date_of_birth"], ilanga.REFERENCE_DATE)
x = x[x["age"] >= 18].copy()

labs = district.lab_results
vl = labs[labs["test_code"] == "VL"].sort_values("collected_at").groupby("patient_id").tail(1)
vl = vl.assign(latest_vl_suppressed=vl["below_detection_limit"] | (vl["result_numeric"] < 1000))
x = x.merge(vl[["patient_id", "latest_vl_suppressed"]], on="patient_id", how="left")

x["study_id"] = x["patient_id"].apply(pseudonymise)
x["age_band"] = ilanga.age_band(x["age"], scheme="research")
year = x["art_start_date"].dt.year
x["art_start_year"] = np.select([year <= 2015, year <= 2020], ["2004-2015", "2016-2020"], "2021-2025")

qi = ["age_band", "sex", "subdistrict", "art_start_year"]
group_size = x.groupby(qi, observed=True)["study_id"].transform("size")
research_extract = x.loc[group_size >= 5, ["study_id"] + qi + ["latest_vl_suppressed"]].reset_index(drop=True)

print(f"Kept {len(research_extract):,} of {len(x):,} eligible patients; k = {k_anonymity(research_extract, qi)}")
log_access("analyst@nqaba", "district_analyst", "ART research extract v1", "SYN-HREC-2026-014",
           len(research_extract))
research_extract.head()
'''),
md("""
### 🌳 Baobab — the publishable summary table
Build `suppressed_table`: the number of **virally suppressed** patients in your extract by `subdistrict` (rows) and
`age_band` (columns), with every count from 1 to 4 replaced by `"<5"`. Then show your access log as a DataFrame.
"""),
ex('''
suppressed_table = None   # 👈 your code here
''', '''
supp = research_extract[research_extract["latest_vl_suppressed"] == True]
counts = pd.crosstab(supp["subdistrict"], supp["age_band"])
suppressed_table = counts.map(suppress) if hasattr(counts, "map") else counts.applymap(suppress)
display(suppressed_table)
pd.DataFrame(access_log)
'''),
md("""
## 🚦 Quality gate
"""),
code('''
passed = ilanga.tickets.check_nq004(my_direct_identifiers, research_extract, suppressed_table)
'''),
md("""
## 📝 Handover note
> **NQ-004 — done. For: Sipho Ngcobo.**
> *The extract contains … patients (… % of eligible). To reach k ≥ 5 I generalised … and suppressed … rows.*
> *Viral suppression was defined as … The pseudonymisation key is held by … and is not shared with the researchers.*
> *Residual risk I'd flag: …*

## 🧭 Career Lens
Data-protection skills are in demand everywhere health data moves: **information officers and deputy information
officers**, **data governance analysts**, **research data managers** at universities and research units, and
**privacy engineers** at health tech companies. Being the analyst who "gets POPIA" makes you the person teams trust
with their most sensitive work.

## 📚 Glossary
**POPIA** – Protection of Personal Information Act · **Special personal information** – categories like health
that get extra protection · **Information Regulator** – POPIA's enforcement body · **Pseudonymisation** – replacing
identifiers with consistent codes · **HMAC** – keyed hash · **Quasi-identifier** – identifies in combination ·
**k-anonymity** – every combination shared by at least k people · **Small-cell suppression** – hiding counts of 1–4 ·
**NHRD** – National Health Research Database

## ✅ Checkpoint
<details><summary>1. Why is SHA-256 of an SA ID number not safe as a pseudonym?</summary>The space of possible ID numbers is small enough to hash them all (a dictionary attack). A keyed hash (HMAC) prevents this.</details>
<details><summary>2. Your extract has k = 1. Name two things you could do.</summary>Generalise a quasi-identifier (e.g. years → periods, ward → sub-district) and/or suppress the rare rows.</details>
<details><summary>3. Name three of POPIA's eight conditions for lawful processing.</summary>Any three of: accountability, processing limitation, purpose specification, further processing limitation, information quality, openness, security safeguards, data subject participation.</details>

---
### 🎓 Phase 1 complete
You now know where South African health data lives, how to query it with Python and pandas, how synthetic data is
built and validated, and how to share data without betraying the people in it. **Phase 2 — Data Engineering** starts
with a shock: the *raw* Ilanga data, straight from the source systems, with every mess real data has.
"""),
md(FOOTER),
]

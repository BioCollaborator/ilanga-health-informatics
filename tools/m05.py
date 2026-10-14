from nb import md, code, ex, SETUP, FOOTER, colab_badge

PATH = "notebooks/phase2_data_engineering/M05_data_quality_patient_matching.ipynb"

CELLS = [
md(f"""
# Module 05 · Meet the raw layer — data quality and patient matching
**BioCollaborator Health Informatics Programme** · Phase 2: Data Engineering · *Innovate Naturally*

{colab_badge(PATH)}

> **File → Save a copy in Drive**, then run cells top to bottom with **Shift + Enter**.
"""),
code(SETUP),
code('''
ilanga.brand.banner(5, "Meet the raw layer: data quality & patient matching", "Phase 2 · Data Engineering", minutes=150)
ilanga.brand.ticket(
    "NQ-005", "Lerato Mokoena", "e-Impilo Implementation Lead, Ilanga District Health Services",
    "Clean and de-duplicate registrations before the e-Impilo migration",
    "We're about to migrate years of registrations into e-Impilo. If we move duplicates across, clinicians "
    "will see half a patient's history in one record and half in another - and miss results. Before migration I "
    "need the sex field standardised, viral load results made machine-readable, and a list of likely duplicate "
    "registrations for our clerks to review.",
    ["A function that standardises sex values to F / M / U",
     "A function that turns every viral load text into a number or a 'below detection limit' flag",
     "A list of candidate duplicate pairs with at least 90% precision and 95% recall",
     "A data quality scorecard and a handover note for the migration team"],
    priority="High - blocks migration")
'''),
md("""
## A note from Ayanda

For four modules you've been working on the **curated** layer — data our team had already cleaned. From today,
you're on the team that does the cleaning. The **raw** layer is Ilanga's data as it arrives from source systems:
typos, blanks, duplicates, six ways of writing the same lab result.

This is where most health data work actually happens. Industry folklore says analysts spend most of their time
preparing data, and in health it's often more. It's not glamorous, but **every indicator, dashboard and model you
will ever build is only as trustworthy as this step.**

— *Ayanda*

## Part 1 · The six dimensions of data quality

| Dimension | Question it asks | An Ilanga example |
|---|---|---|
| **Completeness** | Is the value there? | Home language left blank |
| **Validity** | Is it in the allowed format or range? | An SA ID number whose check digit fails |
| **Consistency** | Do systems and fields agree? | Sex captured as `F`, `f` and `Female` |
| **Uniqueness** | Is each real-world thing recorded once? | The same patient registered twice |
| **Timeliness** | Is it available when needed, and are times sensible? | A lab result "reported" before the specimen arrived |
| **Accuracy** | Does it match reality? | The hardest one: often only checkable against another source |
"""),
md("""
## Part 2 · Profile before you clean

Never start fixing data you haven't looked at. **Profiling** means measuring what's there.
"""),
code('''
raw = ilanga.load_district(layer="raw")
curated = ilanga.load_district()

print("Raw:    ", raw)
print("Curated:", curated)
print(f"\\nThe raw register has {len(raw.patients) - len(curated.patients):,} more patient rows than the curated one. Why might that be?")
'''),
code('''
# Completeness: share of missing values per column
missing = raw.patients.isna().mean().mul(100).round(1).sort_values(ascending=False)
missing[missing > 0]
'''),
md("""
> 🩺 **Clinic Corner — not all blanks are errors**
>
> `passport_number` is blank for most people because most people have an SA ID instead. `sa_id_number` is blank for
> many children. Completeness only means something when you know **which fields should be filled for whom**. Always
> ask a clinician or a registration clerk before you call a blank a defect.
"""),
code('''
# Consistency: how many different ways is "sex" written?
raw.patients["sex"].value_counts(dropna=False)
'''),
md("""
## Part 3 · Validity checks and a data quality scorecard

Enterprise data teams turn checks into a **scorecard**: one row per rule, the number of failing records, and the
failure rate. Run it before and after cleaning, and after every future data load.
"""),
code('''
p, e, l = raw.patients, raw.encounters, raw.lab_results

id_rows = p[p["id_type"] == "SA_ID"]
checks = {
    "SA ID number missing or invalid": (~id_rows["sa_id_number"].apply(ilanga.sa_id.is_valid), len(id_rows)),
    "Visit dated after 31 Dec 2025": (e["encounter_date"] > ilanga.REFERENCE_DATE, len(e)),
    "Lab reported before received": (l["reported_at"] < l["received_at"], len(l)),
    "Creatinine not in umol/L": ((l["test_code"] == "CREAT") & (l["unit"] != "umol/L"), (l["test_code"] == "CREAT").sum()),
    "Home language missing": (p["home_language"].isna(), len(p)),
}
scorecard = pd.DataFrame([
    {"rule": rule, "failing": int(mask.sum()), "checked": int(n), "fail_rate_%": round(100 * mask.sum() / n, 2)}
    for rule, (mask, n) in checks.items()
])
scorecard
'''),
md("""
### Fixing units: creatinine

Most South African labs report creatinine in **µmol/L**, but some systems (and older reports) use **mg/dL**.
The conversion is **1 mg/dL = 88.4 µmol/L**.
"""),
code('''
cr = l[l["test_code"] == "CREAT"].copy()
print(cr["unit"].value_counts(), "\\n")

cr["value"] = pd.to_numeric(cr["result_text"], errors="coerce")
cr["value_umol"] = np.where(cr["unit"] == "mg/dL", (cr["value"] * 88.4).round(0), cr["value"])
cr.loc[cr["unit"] == "mg/dL", ["specimen_id", "result_text", "unit", "value_umol"]].head()
'''),
md("""
> 🩺 **Clinic Corner — why units can hurt people**
>
> A creatinine of **1.1 mg/dL** is normal. A system that silently assumes µmol/L would read that as **1.1 µmol/L** —
> an impossible value that could corrupt kidney-function calculations used to dose medicines like tenofovir.
> Unit mismatches have caused real clinical incidents worldwide. **Never assume a unit; always carry it with the number.**

## Part 4 · Standardising messy values

### 🌱 Seedling — standardise sex
Write `clean_sex_values(series)` that returns a Series where every value is `"F"`, `"M"` or `"U"` (unknown).
Hints: `ilanga.hint("NQ-005.1")`.
"""),
ex('''
def clean_sex_values(series):
    # 👈 your code here
    return series

clean_sex_values(raw.patients["sex"]).value_counts()
''', '''
def clean_sex_values(series):
    mapping = {"f": "F", "female": "F", "m": "M", "male": "M"}
    return series.astype(str).str.strip().str.lower().map(mapping).fillna("U")

clean_sex_values(raw.patients["sex"]).value_counts()
'''),
md("""
### Viral load: six ways to say "undetectable"
"""),
code('''
vl_raw = l[l["test_code"] == "VL"]
vl_raw["result_text"].value_counts().head(10)
'''),
md("""
> 🩺 **Clinic Corner — censored results**
>
> Viral load assays can't measure below a **lower limit of detection**. The lab reports "<50" (or "LDL", "TND" —
> *target not detected*). That isn't a number, and it certainly isn't zero. Analysts call it a **censored** value.
> The honest way to store it is: *no number*, plus a flag saying *below the limit*.

### 🌿 Sapling — parse every viral load result
Write `parse_vl(text)` that returns a tuple `(value, below_limit)`:
- below-limit texts → `(np.nan, True)`
- numbers such as `"12364"` → `(12364.0, False)`

Hints: `ilanga.hint("NQ-005.2")`.
"""),
ex('''
def parse_vl(text):
    # 👈 your code here
    return (np.nan, False)

for t in ["<50", "TND", "12364", "< 50", "LDL"]:
    print(repr(t), "->", parse_vl(t))
''', '''
BELOW = {"<50", "< 50", "<50 copies/ml", "ldl", "tnd", "target not detected"}

def parse_vl(text):
    t = str(text).strip().lower()
    if t in BELOW:
        return (np.nan, True)
    return (float(t), False)

for t in ["<50", "TND", "12364", "< 50", "LDL"]:
    print(repr(t), "->", parse_vl(t))
'''),
md("""
## Part 5 · Patient matching: finding the same person twice

People register again when they move, visit another clinic, lose their card, or when a clerk can't find their
folder. Each time, a **new record** may be created. Across a province, that adds up to a huge number of split
histories. Solving this at national scale is exactly what the **HPRS** unique identifier is for — and patient matching
is how you clean up the past.

> 🤝 **Ubuntu Moment — two ways to get it wrong**
>
> - **Missed duplicate** (false negative): Zanele's viral load results live in a record the clinician never opens.
>   Her unsuppressed result goes unnoticed.
> - **Wrong merge** (false positive): Zanele's record is merged with a different Zanele's. Now one woman's HIV
>   status sits in another woman's file. That's a clinical risk *and* a serious privacy breach.
>
> That's why real teams send uncertain matches to a **human review queue** instead of merging automatically.

### How matching works

1. **Blocking.** Comparing everyone with everyone is `20,500 × 20,499 / 2 ≈ 210 million` pairs. Instead, only compare
   people who share something that rarely changes, like **date of birth**.
2. **Comparing.** Score how similar the names are.
3. **Deciding.** Above a threshold → candidate duplicate.
4. **Measuring.** **Precision** = of the pairs you flagged, how many were real duplicates? **Recall** = of the real
   duplicates, how many did you find?

Let's see name similarity first.
"""),
code('''
from difflib import SequenceMatcher

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

for a, b in [("Nomvula", "Nomvulo"), ("Nomvula", "NOMVULA"), ("Dlamini", "Dlamni"), ("Nomvula", "Thandeka"), ("Sipho", "Siphoh")]:
    print(f"{a:<10} vs {b:<10} similarity = {similarity(a, b):.2f}")
'''),
md("""
Now let's block on date of birth, but only for people born in **1985**, so we can see the idea working.
"""),
code('''
p85 = raw.patients[raw.patients["date_of_birth"].dt.year == 1985]
pairs = p85.merge(p85, on="date_of_birth", suffixes=("_a", "_b"))
pairs = pairs[pairs["patient_id_a"] < pairs["patient_id_b"]]      # each pair once, no self-pairs
print(f"{len(p85):,} people born in 1985 -> {len(pairs):,} candidate pairs after blocking on date of birth")

pairs["first_sim"] = [similarity(a, b) for a, b in zip(pairs["first_name_a"], pairs["first_name_b"])]
pairs["surname_sim"] = [similarity(a, b) for a, b in zip(pairs["surname_a"], pairs["surname_b"])]
pairs["name_score"] = (pairs["first_sim"] + pairs["surname_sim"]) / 2

pairs.sort_values("name_score", ascending=False)[
    ["patient_id_a", "patient_id_b", "first_name_a", "first_name_b", "surname_a", "surname_b", "name_score"]].head(10)
'''),
md("""
> 💻 **Code Corner — a self-merge**
>
> `p85.merge(p85, on="date_of_birth")` joins the table **to itself**: every person is paired with everyone who shares
> their birthday. The line `patient_id_a < patient_id_b` removes self-pairs (Sipho with Sipho) and mirror pairs (A–B and B–A).

Look closely at the top of that list. Some pairs have high scores. Some real duplicates might have **low** scores —
what if the clerk typed the surname in the first-name box? And some duplicates won't be in the same block at all:
what if the day and month of birth were swapped?

### 🌳 Baobab — find the duplicates across the whole district
Build `duplicate_pairs`: a DataFrame with columns `patient_id_a` and `patient_id_b`, one row per pair you believe is
the same person. The quality gate scores you against the migration team's reviewed answer key.

Targets: **precision ≥ 90%** and **recall ≥ 95%**. Hints: `ilanga.hint("NQ-005.3")`, levels 1 to 3.
"""),
ex('''
duplicate_pairs = pd.DataFrame(columns=["patient_id_a", "patient_id_b"])   # 👈 your code here
''', '''
pt = raw.patients.copy()
pt["fn"] = pt["first_name"].str.strip().str.lower()
pt["sn"] = pt["surname"].str.strip().str.lower()

# Pass 1: block on date of birth; score names straight AND swapped
m = pt.merge(pt, on="date_of_birth", suffixes=("_a", "_b"))
m = m[m["patient_id_a"] < m["patient_id_b"]].copy()
straight = [(similarity(a, b) + similarity(c, d)) / 2 for a, b, c, d in zip(m.fn_a, m.fn_b, m.sn_a, m.sn_b)]
swapped = [(similarity(a, d) + similarity(c, b)) / 2 for a, b, c, d in zip(m.fn_a, m.fn_b, m.sn_a, m.sn_b)]
m["name_score"] = np.maximum(straight, swapped)
same_id = m["sa_id_number_a"].notna() & (m["sa_id_number_a"] == m["sa_id_number_b"])
same_sex = clean_sex_values(m["sex_a"]) == clean_sex_values(m["sex_b"])
pass1 = m[((m["name_score"] >= 0.85) & same_sex) | same_id]

# Pass 2: exact names, but day and month of birth swapped
dob = pt["date_of_birth"]
pt["dob_swapped"] = pd.to_datetime(dict(year=dob.dt.year, month=dob.dt.day.clip(upper=12), day=dob.dt.month), errors="coerce")
m2 = pt[dob.dt.day <= 12].merge(pt, left_on=["fn", "sn", "dob_swapped"], right_on=["fn", "sn", "date_of_birth"],
                                  suffixes=("_a", "_b"))
m2 = m2[m2["patient_id_a"] != m2["patient_id_b"]]

found = pd.concat([pass1[["patient_id_a", "patient_id_b"]], m2[["patient_id_a", "patient_id_b"]]])
duplicate_pairs = pd.DataFrame(np.sort(found.values, axis=1), columns=["patient_id_a", "patient_id_b"]).drop_duplicates()
print(f"{len(duplicate_pairs):,} candidate duplicate pairs")
duplicate_pairs.head()
'''),
md("""
## 🚦 Quality gate
"""),
code('''
passed = ilanga.tickets.check_nq005(clean_sex_values, parse_vl, duplicate_pairs)
'''),
md("""
## 📝 Handover note
> **NQ-005 — done. For: Lerato Mokoena and the migration team.**
> *Scorecard summary: …*
> *I found … candidate duplicate pairs using … Precision was … and recall …*
> *Recommendation: pairs scoring below … should go to clerk review rather than automatic merge because …*

## 🧭 Career Lens
**Data quality analysts**, **master data / MPI specialists** and **data engineers** do this work every day, and EMR
migrations like e-Impilo's can't happen without them. Record linkage is also a research specialty: linking
registries, lab data and mortality records is how many South African epidemiological studies are built.

## 📚 Glossary
**Raw vs curated layer** – data as received vs cleaned and conformed · **Profiling** – measuring data before changing
it · **Scorecard** – a table of data quality rules and failure rates · **Censored value** – a result known only to be
below (or above) a limit · **MPI** – master patient index · **Blocking** – only comparing records that share a key ·
**Precision / recall** – how many flagged matches are right / how many true matches were found

## ✅ Checkpoint
<details><summary>1. Which is usually worse in a clinical record: a missed duplicate or a wrong merge? Why?</summary>A wrong merge — it puts another person's clinical information in someone's file (safety risk and privacy breach). That's why uncertain matches go to human review.</details>
<details><summary>2. Why block on date of birth before comparing names?</summary>To avoid comparing hundreds of millions of pairs. Blocking reduces comparisons to people who share a stable attribute.</details>
<details><summary>3. How should "<50 copies/mL" be stored?</summary>As no numeric value plus a flag that it's below the detection limit — not as 0 and not as 50.</details>

**Next up → Module 06:** Codes, codes, codes. ICD-10, LOINC, SNOMED CT and ATC — the languages that let systems
agree on what a diagnosis, test or medicine *is*.
"""),
md(FOOTER),
]

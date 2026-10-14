from nb import md, code, ex, SETUP, FOOTER, colab_badge

PATH = "notebooks/phase2_data_engineering/M06_clinical_terminologies.ipynb"

CELLS = [
md(f"""
# Module 06 · Speaking the same language — ICD-10, LOINC, SNOMED CT and ATC
**BioCollaborator Health Informatics Programme** · Phase 2: Data Engineering · *Innovate Naturally*

{colab_badge(PATH)}

> **File → Save a copy in Drive**, then run cells top to bottom with **Shift + Enter**.
"""),
code(SETUP),
code('''
from ilanga import terminology as term

ilanga.brand.banner(6, "Speaking the same language: clinical terminologies", "Phase 2 · Data Engineering", minutes=150)
ilanga.brand.ticket(
    "NQ-006", "Dr Priya Naidoo", "Clinical Governance Lead, Ilanga District Health Services",
    "Code our data consistently for the chronic-care clinical audit",
    "Next quarter we audit chronic care across the district. I need diagnoses grouped the way the audit "
    "framework groups them, our programme conditions coded in SNOMED CT so they line up with e-Impilo, and - "
    "the painful one - the dispensing data from the paper-era pharmacy system mapped to proper medicine codes. "
    "Right now 'TLD', 'TDF/3TC/DTG' and 'tld 1 tab daily' are three different medicines as far as a computer knows.",
    ["A function that returns the ICD-10 chapter for any code",
     "Every programme condition coded in SNOMED CT, with no rows lost or duplicated",
     "Free-text dispensing records mapped to WHO ATC codes, at least 98% accurate",
     "A mapping note explaining any codes you could not map with confidence"],
    priority="Normal")
'''),
md("""
## Part 1 · Why codes?

To a human, "HTN", "high blood pressure", "hypertension" and "BP ↑" mean the same thing. To a computer they're
four unrelated strings. A **terminology** gives each concept one agreed code, so systems — and the people who
analyse their data — can agree on meaning. This is called **semantic interoperability**.

| Terminology | What it codes | Who uses it in SA | Example |
|---|---|---|---|
| **ICD-10** (WHO) | Diagnoses, for classification and reporting | Mandatory on medical scheme claims; used across public-sector reporting | `I10` Essential hypertension |
| **LOINC** | Laboratory tests and clinical measurements | Lab systems and interfaces | `20447-9` HIV-1 viral load |
| **SNOMED CT** | Detailed clinical concepts in the record | EMRs; increasingly central in digital health strategies | `38341003` Hypertensive disorder |
| **ATC** (WHO) | Medicines by anatomical and therapeutic group | Drug utilisation analysis, research | `J05AR27` TLD |
| **NAPPI** | Specific medicine products and packs | SA private-sector claims and pharmacy systems | *(proprietary product codes)* |

> 🩺 **Clinic Corner — classification versus clinical terminology**
>
> **ICD-10 is a classification**: it puts conditions into buckets for counting, reporting and billing. It's
> deliberately coarse. **SNOMED CT is a clinical terminology**: it captures what the clinician actually meant, in
> detail, with relationships between concepts. They complement each other — many systems record in SNOMED CT and
> **map** to ICD-10 for reporting.

> ⚖️ **Licensing note:** LOINC and ICD-10 are free to use. SNOMED CT needs a licence: it's free in SNOMED International
> member countries and requires an affiliate licence elsewhere. Check the current national position before building
> SNOMED CT into a product.

## Part 2 · ICD-10 structure

An ICD-10 code has a letter, two digits for the **category**, and optionally a decimal for more detail:
`E11.9` = chapter IV (endocrine) → category `E11` (type 2 diabetes) → `.9` (without complications).
Categories are grouped into **22 chapters**.
"""),
code('''
term.ICD10_CHAPTERS
'''),
code('''
d = ilanga.load_district()
enc25 = d.encounters[d.encounters["encounter_date"].dt.year == 2025]

top = (enc25["icd10_primary"].value_counts().rename_axis("code").reset_index(name="visits")
       .merge(term.ICD10_CODES, on="code", how="left"))
top.head(10)
'''),
md("""
> 💻 **Code Corner — text comparison works on ICD-10 ranges**
>
> Python compares strings character by character, so `"E11" >= "E00"` and `"E11" <= "E90"` are both `True`.
> That means you can check whether a category falls in a chapter's range with ordinary `<=` comparisons —
> as long as you compare the **first three characters** (the category), not the full code.

### 🌱 Seedling — which chapter is this code in?
Write `icd10_chapter(code)` that returns the chapter **title** from `term.ICD10_CHAPTERS`. Careful: some letters are
split across two chapters (`D`, `H`). Hints: `ilanga.hint("NQ-006.1")`.
"""),
ex('''
def icd10_chapter(code):
    # 👈 your code here
    return None

for c in ["I10", "H10.9", "H60.0", "D50.9", "Z34.9", "T14.1"]:
    print(c, "->", icd10_chapter(c))
''', '''
def icd10_chapter(code):
    category = str(code)[:3]
    for row in term.ICD10_CHAPTERS.itertuples():
        if row.start <= category <= row.end:
            return row.title
    return None

for c in ["I10", "H10.9", "H60.0", "D50.9", "Z34.9", "T14.1"]:
    print(c, "->", icd10_chapter(c))
'''),
code('''
# Once your function works, this chart shows 2025 activity by chapter
if icd10_chapter("I10"):
    by_chapter = enc25["icd10_primary"].map(icd10_chapter).value_counts()
    fig, ax = plt.subplots(figsize=(8, 4))
    by_chapter.sort_values().plot.barh(ax=ax, color=BRAND["teal"])
    ax.set_title("Ilanga 2025 visits by ICD-10 chapter"); ax.set_xlabel("Visits")
    plt.show()
'''),
md("""
> 🩺 **Clinic Corner — "Factors influencing health status" is huge**
>
> Chapter XXI (Z codes) covers visits that aren't about a disease: child health checks, antenatal care,
> contraception. In primary care these are a big share of the work. A dashboard that only counts "diseases"
> makes preventive care invisible.

## Part 3 · LOINC: naming lab tests

Each lab has its own internal test codes (`VL`, `CD4`...). LOINC gives every test a universal code, so a result from
one lab means the same thing in any system.
"""),
code('''
term.LOINC
'''),
md("""
### A mapping you should *not* guess

Look at the Xpert MTB/RIF Ultra row. It has **no LOINC code** and its status is `needs_review`. Why?

1. **One test, two answers.** Xpert reports whether TB DNA was detected *and* whether rifampicin resistance was
   detected. That's two observations, usually needing two codes (or a panel).
2. **Codes go out of date.** LOINC has a code for "*Mycobacterium tuberculosis* rifampicin resistance (rpoB) gene
   [Presence]" — **48176-2** — that you'll still find in older systems. LOINC has **deprecated** it, because the
   rpoB gene is present in all mycobacteria. It's *mutations* in rpoB that signal resistance, so the old term was
   modelled wrongly.

> 🤝 **Ubuntu Moment — "I don't know" is a professional answer**
>
> When you can't map a code with confidence, **mark it for review and escalate to a terminologist** — never pick the
> closest-looking code. A wrong code is worse than a missing one, because it looks trustworthy. Behind a TB result
> is a patient whose drug-resistant TB must not be misclassified.

## Part 4 · SNOMED CT for programme conditions
"""),
code('''
term.SNOMED
'''),
md("""
### 🌿 Sapling — code every condition in SNOMED CT
Build `conditions_coded`: the `d.conditions` table with an extra `snomed_code` column. The number of rows must not
change. Hints: `ilanga.hint("NQ-006.2")`.
"""),
ex('''
conditions_coded = None   # 👈 your code here
''', '''
conditions_coded = d.conditions.merge(term.SNOMED[["condition", "snomed_code"]], on="condition", how="left")
assert len(conditions_coded) == len(d.conditions)
conditions_coded[["condition_id", "condition", "icd10_code", "snomed_code"]].head()
'''),
md("""
> 💻 **Code Corner — merges that multiply rows**
>
> If a mapping table accidentally has two rows for "HIV", every HIV condition is duplicated by the merge — and
> suddenly the district has twice as many people living with HIV. Always compare row counts before and after a merge.
> `pd.merge(..., validate="many_to_one")` makes pandas raise an error if the right-hand table has duplicates.

## Part 5 · Medicines and the ATC classification

ATC codes read from general to specific: `J` anti-infectives → `J05` antivirals for systemic use → `J05A` direct
acting antivirals → `J05AR` HIV combinations → `J05AR27` lamivudine, tenofovir disoproxil and dolutegravir (TLD).
"""),
code('''
term.medicines()
'''),
code('''
# The curated layer already has ATC codes. Which therapeutic groups dominate dispensing?
disp = d.dispensing.assign(atc_group=d.dispensing["atc_code"].str[:3].map(term.ATC_LEVEL2))
disp.groupby("atc_group")["patient_id"].nunique().sort_values(ascending=False).rename("patients")
'''),
md("""
### The raw pharmacy data

Before e-Impilo, dispensing was captured as free text. Here's what the raw layer looks like:
"""),
code('''
raw = ilanga.load_district(layer="raw")
raw.dispensing["medicine_text"].value_counts().head(25)
'''),
md("""
### 🌳 Baobab — map free-text medicines to ATC codes
Build `atc_mapped`: a Series with one ATC code per row of `raw.dispensing`, **in the same order**. The gate compares
your codes with the curated ones. Target: **≥ 98% accurate**. Hints: `ilanga.hint("NQ-006.3")`.

*Tip:* write your rules as a function, test it on `raw.dispensing["medicine_text"].unique()` (only about 50 distinct
texts), then apply it to the whole column.
"""),
ex('''
def map_to_atc(text):
    # 👈 your code here
    return None

atc_mapped = raw.dispensing["medicine_text"].apply(map_to_atc)
atc_mapped.value_counts(dropna=False).head()
''', '''
RULES = [  # (keywords that must ALL appear, ATC) - most specific first
    (["dolutegravir"], "J05AR27"), (["dtg", "3tc", "tdf"], "J05AR27"), (["tld"], "J05AR27"),
    (["emtricitabine"], "J05AR06"), (["ftc"], "J05AR06"), (["tee"], "J05AR06"),
    (["zidovudine"], "J05AR01"), (["azt"], "J05AR01"),
    (["lopinavir"], "J05AR10"), (["lpv"], "J05AR10"),
    (["abacavir"], "J05AR02"), (["abc"], "J05AR02"),
    (["dtg"], "J05AX12"),
    (["amlodipin"], "C08CA01"), (["hydrochlorothiazide"], "C03AA03"), (["hct"], "C03AA03"),
    (["enalapril"], "C09AA02"), (["metformin"], "A10BA02"), (["mtf"], "A10BA02"), (["gliclazid"], "A10BB09"),
    (["pyrazinamide"], "J04AM06"), (["rhze"], "J04AM06"), (["4fdc"], "J04AM06"),
    (["rifampicin"], "J04AM02"), (["2fdc"], "J04AM02"), (["rh"], "J04AM02"),
]

def map_to_atc(text):
    t = str(text).lower().replace(" ", "")
    if "dolutegravir" in t and "tenofovir" not in t:
        return "J05AX12"                      # dolutegravir on its own (paediatric 10 mg)
    for keywords, atc in RULES:
        if all(k in t for k in keywords):
            return atc
    return None

atc_mapped = raw.dispensing["medicine_text"].apply(map_to_atc)
print("Unmapped texts:", raw.dispensing.loc[atc_mapped.isna(), "medicine_text"].unique())
atc_mapped.value_counts(dropna=False).head()
'''),
md("""
## 🚦 Quality gate
"""),
code('''
passed = ilanga.tickets.check_nq006(icd10_chapter, conditions_coded, atc_mapped)
'''),
md("""
## 📝 Handover note — mapping note
> **NQ-006 — done. For: Dr Priya Naidoo.**
> *ICD-10 chapters: the biggest 2025 chapters were …*
> *SNOMED CT: all … conditions coded; mapping table checked for duplicates.*
> *ATC: … % of dispensing lines mapped automatically. The texts that needed care were …*
> *Not mapped with confidence: Xpert MTB/RIF Ultra LOINC coding — referred for terminology review because …*

## 🧭 Career Lens
**Clinical coders**, **terminologists** and **health information managers** keep codes accurate, and they're in
demand wherever claims, audits or EMRs exist. Private hospital groups, medical scheme administrators and the
NHLS all employ people who can read ICD-10 and LOINC fluently. If you come from nursing or medical technology, your
clinical knowledge is a genuine advantage here.

## 📚 Glossary
**Terminology** – agreed codes for concepts · **Classification** – grouping for counting (ICD-10) · **Semantic
interoperability** – systems agreeing on meaning · **LOINC** – codes for tests · **SNOMED CT** – detailed clinical
terminology · **ATC** – WHO medicine classification · **NAPPI** – SA medicine product codes · **Deprecated code** –
retired code that should no longer be used · **Mapping** – linking codes between systems

## ✅ Checkpoint
<details><summary>1. What's the difference between ICD-10 and SNOMED CT?</summary>ICD-10 classifies conditions into reporting categories; SNOMED CT records detailed clinical meaning. Systems often record in SNOMED CT and map to ICD-10.</details>
<details><summary>2. A mapping table merge turns 7,845 condition rows into 10,845. What happened?</summary>The mapping table had duplicate keys, so the merge multiplied rows. Check with validate="many_to_one".</details>
<details><summary>3. You're not sure which LOINC code fits a test. What do you do?</summary>Leave it unmapped, flag it for review, and escalate to a terminologist. Never guess.</details>

**Next up → Module 07:** Systems exchanging data. You'll read HL7 v2 lab messages and turn them into FHIR resources —
the standard e-Impilo is built to speak.
"""),
md(FOOTER),
]

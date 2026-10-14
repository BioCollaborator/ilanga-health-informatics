"""Quality gates for Phase 2: Data engineering (Modules 5-8)."""
from __future__ import annotations

import sqlite3

import numpy as np
import pandas as pd

from . import _answer_key, cleaning, fhir, hl7, load_district
from .brand import gate_report
from .terminology import ICD10_CHAPTERS, SNOMED

HINTS2 = {
    # ---------------- Module 5 ----------------
    "NQ-005.1": {1: "Look at raw.patients['sex'].value_counts() first. How many different spellings are there?",
                 2: "Strip spaces and lowercase everything, then map 'f'/'female' to 'F' and 'm'/'male' to 'M'.",
                 3: "s.astype(str).str.strip().str.lower().map({'f':'F','female':'F','m':'M','male':'M'}).fillna('U')"},
    "NQ-005.2": {1: "Collect every distinct VL text first: raw VL rows' result_text.value_counts(). Which ones mean 'below the limit'?",
                 2: "Treat '<50', '< 50', '<50 copies/mL', 'LDL', 'TND' and 'Target not detected' as below the limit. Everything else should be a number.",
                 3: "Normalise with t.strip().lower(), check membership in a set of below-limit phrases, else return (float(t), False)."},
    "NQ-005.3": {1: "Comparing all 20,500 patients with each other is 210 million pairs. Block first: only compare people who share a date of birth.",
                 2: "Score name similarity with difflib.SequenceMatcher. Also try the names swapped (first vs surname). Add a second pass for day/month-swapped birth dates.",
                 3: "Pass 1: merge patients to itself on date_of_birth, keep pairs with average name similarity >= 0.85 (either order). Pass 2: merge on first name + surname + swapped day/month."},
    # ---------------- Module 6 ----------------
    "NQ-006.1": {1: "Chapters are ranges. Compare the first three characters of the code with each chapter's start and end.",
                 2: "Text comparison works for ICD-10 categories: 'J06' >= 'J00' and 'J06' <= 'J99' is True.",
                 3: "For each row in ICD10_CHAPTERS: if start <= code[:3] <= end: return title."},
    "NQ-006.2": {1: "You need one SNOMED CT code per condition row. Which table holds the mapping?",
                 2: "Merge conditions with ilanga.terminology.SNOMED on 'condition' using how='left'.",
                 3: "Then check len(result) == len(conditions). If a merge adds rows, your mapping table has duplicates."},
    "NQ-006.3": {1: "Start with raw.dispensing['medicine_text'].str.lower().value_counts(). Group the variants by medicine.",
                 2: "Keyword rules work well: if 'dolutegravir' or 'dtg' appears with tenofovir/'tld', it's TLD (J05AR27). Order your rules from most to least specific.",
                 3: "Normalise text (lowercase, remove spaces), then test rules in order: combinations first (TLD, TEE, AZT/3TC, LPV/r, ABC/3TC), then single drugs."},
    # ---------------- Module 7 ----------------
    "NQ-007.1": {1: "Split the message into segments first (message.split('\\r')), then find the segment whose first field matches.",
                 2: "For most segments, field n is parts[n] after splitting on '|'. MSH is special.",
                 3: "In MSH, the '|' itself is MSH-1, so MSH field n is parts[n - 1]."},
    "NQ-007.2": {1: "Use your hl7_field function for each value you need.",
                 2: "specimen_id = OBR-3, patient_id = the first component of PID-3, code = first component of OBX-3, value = OBX-5, unit = OBX-6.",
                 3: "Components are separated by '^' and repeats by '~': PID-3.split('~')[0].split('^')[0]."},
    "NQ-007.3": {1: "Start from the Observation example in the lesson and replace the hard-coded values with the row's values.",
                 2: "Below-limit viral loads need valueQuantity with comparator '<' and value 50. Xpert results are text: use valueString.",
                 3: "Tests without a LOINC code still need a coding: use the Ilanga local code system URI with the local test code."},
    # ---------------- Module 8 ----------------
    "NQ-008.1": {1: "SELECT facility_id, COUNT(*) ... FROM fact_encounter ... GROUP BY facility_id",
                 2: "Filter to 2025 with strftime('%Y', encounter_date) = '2025'.",
                 3: "Name the count column: COUNT(*) AS headcount. Then pd.read_sql(query, conn)."},
    "NQ-008.2": {1: "You need lab results joined to facilities to get the subdistrict.",
                 2: "Suppressed = below_detection_limit = 1 OR result_numeric < 1000. SUM(CASE WHEN ... THEN 1 ELSE 0 END) counts them.",
                 3: "pct_suppressed = ROUND(100.0 * suppressed / tests, 1). A CTE (WITH ...) keeps it readable."},
    "NQ-008.3": {1: "Each test is one SQL query that counts problems. Zero problems = the test passes.",
                 2: "Unique: SELECT COUNT(*) - COUNT(DISTINCT col). Not null: COUNT(*) WHERE col IS NULL.",
                 3: "Relationship: LEFT JOIN child to parent and count child rows where the parent key IS NULL."},
}


def _ok(name, cond, hint):
    try:
        return (name, bool(cond), hint)
    except Exception:
        return (name, False, hint)


# ============================== Module 5 ==============================
def check_nq005(clean_sex_values=None, parse_vl=None, duplicate_pairs=None) -> bool:
    raw = load_district("raw")
    res = []
    try:
        got = clean_sex_values(raw.patients["sex"])
        good1 = got.reset_index(drop=True).equals(cleaning.clean_sex(raw.patients["sex"]).reset_index(drop=True))
    except Exception:
        good1 = False
    res.append(_ok("🌱 Sex values standardised to F / M / U", good1, "Try ilanga.hint('NQ-005.1')"))

    try:
        cur = load_district().lab_results.set_index("specimen_id")
        rv = raw.lab_results[raw.lab_results["test_code"] == "VL"].set_index("specimen_id")
        out = rv["result_text"].apply(parse_vl)
        below = pd.Series([bool(b) for _, b in out], index=rv.index)
        vals = pd.Series([v for v, _ in out], index=rv.index, dtype=float)
        exp_b = cur.loc[rv.index, "below_detection_limit"].astype(bool)
        exp_v = cur.loc[rv.index, "result_numeric"]
        good2 = below.equals(exp_b) and np.allclose(vals[~exp_b], exp_v[~exp_b])
    except Exception:
        good2 = False
    res.append(_ok("🌿 All viral load texts parsed correctly", good2, "Try ilanga.hint('NQ-005.2')"))

    try:
        key = _answer_key()
        truth = set(map(tuple, np.sort(key[["original_patient_id", "duplicate_patient_id"]].values, axis=1)))
        pred = set(map(tuple, np.sort(duplicate_pairs[["patient_id_a", "patient_id_b"]].astype(str).values, axis=1)))
        pred = {p for p in pred if p[0] != p[1]}
        if not pred:
            raise ValueError("empty")
        tp = len(truth & pred)
        precision = tp / len(pred) if pred else 0
        recall = tp / len(truth)
        res.append(_ok(f"🌳 Precision ≥ 90% (yours: {precision:.1%})", precision >= 0.9,
                       "Too many false matches. A wrong merge puts someone else's results in a patient's file - tighten your threshold."))
        res.append(_ok(f"🌳 Recall ≥ 95% (yours: {recall:.1%})", recall >= 0.95,
                       "Missing duplicates. Did you handle swapped names and day/month swaps? Try ilanga.hint('NQ-005.3')"))
    except Exception:
        res.append(_ok("🌳 Duplicate pairs", False,
                       "No pairs yet - need a DataFrame with columns patient_id_a and patient_id_b. Try ilanga.hint('NQ-005.3')"))
    return gate_report("NQ-005", res)


# ============================== Module 6 ==============================
def _ref_chapter(code):
    c = str(code)[:3]
    for r in ICD10_CHAPTERS.itertuples():
        if r.start <= c <= r.end:
            return r.title
    return None


def check_nq006(icd10_chapter=None, conditions_coded=None, atc_mapped=None) -> bool:
    d = load_district()
    res = []
    codes = list(d.encounters["icd10_primary"].unique()) + ["H60.0", "D50.9", "O80", "U07.1"]
    try:
        good1 = all(icd10_chapter(c) == _ref_chapter(c) for c in codes)
    except Exception:
        good1 = False
    res.append(_ok("🌱 ICD-10 chapter lookup works (including tricky ranges)", good1,
                   "Watch the chapters that share a letter (D, H). Try ilanga.hint('NQ-006.1')"))
    try:
        exp = d.conditions.merge(SNOMED[["condition", "snomed_code"]], on="condition", how="left")
        cc = conditions_coded
        good2 = len(cc) == len(d.conditions) and cc.sort_values("condition_id")["snomed_code"].astype(str).tolist() == \
            exp.sort_values("condition_id")["snomed_code"].astype(str).tolist()
        hint2 = "Row count changed - check your merge." if len(cc) != len(d.conditions) else "Try ilanga.hint('NQ-006.2')"
    except Exception:
        good2, hint2 = False, "conditions_coded should be the conditions table plus a snomed_code column."
    res.append(_ok("🌿 Every condition coded in SNOMED CT, no rows lost or added", good2, hint2))
    try:
        truth = d.dispensing["atc_code"].reset_index(drop=True)
        got = pd.Series(atc_mapped).reset_index(drop=True).astype(str)
        acc = (got == truth).mean() if len(got) == len(truth) else 0
    except Exception:
        acc = 0
    res.append(_ok(f"🌳 Free-text medicines mapped to ATC, ≥ 98% accurate (yours: {acc:.1%})", acc >= 0.98,
                   "Try ilanga.hint('NQ-006.3')"))
    return gate_report("NQ-006", res)


# ============================== Module 7 ==============================
def _ref_field(msg, seg, n):
    for s in msg.replace("\n", "\r").split("\r"):
        parts = s.split("|")
        if parts[0] == seg:
            idx = n - 1 if seg == "MSH" else n
            return parts[idx] if idx < len(parts) else ""
    return None


def check_nq007(hl7_field=None, hl7_to_dataframe=None, lab_to_observation=None) -> bool:
    d = load_district()
    msgs = hl7.lab_messages(d, limit=200, seed=7)
    res = []
    probes = [("MSH", 9), ("MSH", 12), ("MSH", 5), ("PID", 5), ("OBR", 3), ("OBX", 5), ("OBX", 6)]
    try:
        good1 = all(hl7_field(m, s, n) == _ref_field(m, s, n) for m in msgs[:40] for s, n in probes)
    except Exception:
        good1 = False
    res.append(_ok("🌱 hl7_field reads fields correctly (including MSH)", good1, "Try ilanga.hint('NQ-007.1')"))
    try:
        df = hl7_to_dataframe(msgs)
        exp = pd.DataFrame({
            "specimen_id": [_ref_field(m, "OBR", 3) for m in msgs],
            "patient_id": [_ref_field(m, "PID", 3).split("~")[0].split("^")[0] for m in msgs],
            "code": [_ref_field(m, "OBX", 3).split("^")[0] for m in msgs],
            "value": [_ref_field(m, "OBX", 5) for m in msgs],
            "unit": [_ref_field(m, "OBX", 6) for m in msgs],
        })
        good2 = list(df.columns) == list(exp.columns) and df.reset_index(drop=True).astype(str).equals(exp.astype(str))
    except Exception:
        good2 = False
    res.append(_ok("🌿 200 messages converted to a tidy table", good2,
                   "Columns must be: specimen_id, patient_id, code, value, unit. Try ilanga.hint('NQ-007.2')"))
    try:
        labs = d.lab_results
        sample = pd.concat([labs[labs["below_detection_limit"]].head(5), labs[labs["test_code"] == "XPERT"].head(5),
                            labs[labs["test_code"].isin(["HBA1C", "CREAT", "CD4", "HB"])].head(10),
                            labs[(labs["test_code"] == "VL") & labs["result_numeric"].notna()].head(5)])
        problems = []
        for _, r in sample.iterrows():
            o = lab_to_observation(r)
            if not o:
                raise ValueError("lab_to_observation returned an empty resource - build the Observation dict")
            problems += fhir.validate(o)
            if o["subject"]["reference"] != f"Patient/{r['patient_id']}":
                problems.append("subject")
            if pd.notna(r["loinc_code"]) and not any(c.get("system") == "http://loinc.org" and c.get("code") == r["loinc_code"]
                                                     for c in o["code"]["coding"]):
                problems.append("loinc")
            if r["below_detection_limit"]:
                vq = o.get("valueQuantity", {})
                if vq.get("comparator") != "<" or vq.get("value") != 50:
                    problems.append("censored")
            elif r["test_code"] == "XPERT":
                if o.get("valueString") != r["result_text"]:
                    problems.append("xpert")
            elif abs(o.get("valueQuantity", {}).get("value", -1) - r["result_numeric"]) > 1e-9:
                problems.append("value")
        good3 = not problems
        hint3 = "Try ilanga.hint('NQ-007.3')" if good3 else f"First issues found: {problems[:3]}"
    except Exception as ex:
        good3, hint3 = False, str(ex) if "empty resource" in str(ex) else f"lab_to_observation raised an error: {ex}"
    res.append(_ok("🌳 Valid FHIR Observations for every result type", good3, hint3))
    return gate_report("NQ-007", res)


# ============================== Module 8 ==============================
def _reference_warehouse():
    d = load_district()
    con = sqlite3.connect(":memory:")
    d.facilities.to_sql("dim_facility", con, index=False)
    d.encounters.to_sql("fact_encounter", con, index=False)
    d.lab_results.to_sql("fact_lab", con, index=False)
    return con


def check_nq008(facility_headcount_2025=None, vl_suppression_2025=None, test_unique=None, test_not_null=None,
                test_relationship=None) -> bool:
    con = _reference_warehouse()
    res = []
    exp1 = pd.read_sql("SELECT facility_id, COUNT(*) AS headcount FROM fact_encounter "
                       "WHERE strftime('%Y', encounter_date) = '2025' GROUP BY facility_id ORDER BY facility_id", con)
    try:
        got = facility_headcount_2025.sort_values("facility_id").reset_index(drop=True)
        good1 = got[["facility_id", "headcount"]].astype(str).equals(exp1.astype(str))
    except Exception:
        good1 = False
    res.append(_ok("🌱 2025 headcount per facility (SQL)", good1, "Try ilanga.hint('NQ-008.1')"))
    exp2 = pd.read_sql("""
        WITH vl AS (SELECT l.*, f.subdistrict FROM fact_lab l JOIN dim_facility f ON l.ordering_facility_id = f.facility_id
                    WHERE l.test_code = 'VL' AND strftime('%Y', l.collected_at) = '2025')
        SELECT subdistrict, COUNT(*) AS tests,
               SUM(CASE WHEN below_detection_limit = 1 OR result_numeric < 1000 THEN 1 ELSE 0 END) AS suppressed
        FROM vl GROUP BY subdistrict ORDER BY subdistrict""", con)
    exp2["pct_suppressed"] = (100 * exp2["suppressed"] / exp2["tests"]).round(1)
    try:
        got = vl_suppression_2025.sort_values("subdistrict").reset_index(drop=True)
        good2 = got["subdistrict"].tolist() == exp2["subdistrict"].tolist() and \
            np.allclose(got[["tests", "suppressed", "pct_suppressed"]].astype(float), exp2[["tests", "suppressed", "pct_suppressed"]], atol=0.11)
    except Exception:
        good2 = False
    res.append(_ok("🌿 2025 viral load suppression by sub-district (SQL)", good2, "Try ilanga.hint('NQ-008.2')"))
    try:
        t = sqlite3.connect(":memory:")
        t.executescript("""
            CREATE TABLE parent (id TEXT); INSERT INTO parent VALUES ('a'),('b');
            CREATE TABLE good (id TEXT, pid TEXT); INSERT INTO good VALUES ('1','a'),('2','b');
            CREATE TABLE bad (id TEXT, pid TEXT); INSERT INTO bad VALUES ('1','a'),('1',NULL),('3','zz');""")
        good3 = (test_unique(t, "good", "id") is True and test_unique(t, "bad", "id") is False and
                 test_not_null(t, "good", "pid") is True and test_not_null(t, "bad", "pid") is False and
                 test_relationship(t, "good", "pid", "parent", "id") is True and
                 test_relationship(t, "bad", "pid", "parent", "id") is False)
    except Exception:
        good3 = False
    res.append(_ok("🌳 Data tests catch duplicates, nulls and orphan keys", good3,
                   "Each test must return True or False (a Python bool). Try ilanga.hint('NQ-008.3')"))
    return gate_report("NQ-008", res)

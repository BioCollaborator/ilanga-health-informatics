"""
Quality gates for each module's ticket.

A quality gate is how real data teams stop broken work reaching a client: automated
checks run before anything is handed over. Each check recomputes the expected answer
from the data, so there is no answer key to copy - only work to do.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import age_band, age_years, load_district, sa_id
from .brand import gate_report
from .dictionary import DICTIONARY

HINTS = {
    # ---------------- Module 1 ----------------
    "NQ-001.1": {1: "The facilities table has an emr_go_live column. What does an empty value mean?",
                 2: "Use .notna() on emr_go_live, then .sum(). The laboratory never has a go-live date.",
                 3: "n_emr_live = int(district.facilities['emr_go_live'].notna().sum())"},
    "NQ-001.2": {1: "Count patients per subdistrict - value_counts() is your friend.",
                 2: "district.patients['subdistrict'].value_counts() is sorted largest first. Which label is at the top?",
                 3: "biggest_subdistrict = district.patients['subdistrict'].value_counts().idxmax()"},
    "NQ-001.3": {1: "Encounters don't have a subdistrict column, but facilities do. You'll need to merge them.",
                 2: "Filter encounter_date to 2025, merge facilities on facility_id, then group by subdistrict.",
                 3: "Inside the groupby, compute (capture_mode == 'Digital (e-Impilo)').mean() * 100 for each subdistrict."},
    # ---------------- Module 2 ----------------
    "NQ-002.1": {1: "Two filters: the clinic (facility_id == 'ILN-CL01') and the year (encounter_date.dt.year == 2025).",
                 2: "Combine the filters with &, wrapping each condition in brackets.",
                 3: "headcount_2025 = len(enc[(enc['facility_id']=='ILN-CL01') & (enc['encounter_date'].dt.year==2025)])"},
    "NQ-002.2": {1: "Start from your filtered 2025 Mfula Gateway visits, then group by month.",
                 2: "Use .groupby(visits['encounter_date'].dt.month).size()",
                 3: "Make sure the index runs 1-12; .reindex(range(1, 13), fill_value=0) guarantees it."},
    "NQ-002.3": {1: "You need each patient's date of birth next to each visit. Merge with patients.",
                 2: "Use ilanga.age_years(merged['date_of_birth'], merged['encounter_date']) to get age at each visit.",
                 3: "Keep rows where age < 5, then group by month exactly as in exercise 2."},
    # ---------------- Module 3 ----------------
    "NQ-003.1": {1: "Only patients with id_type == 'SA_ID' have a number to check.",
                 2: "Apply ilanga.sa_id.is_valid to the sa_id_number column with .apply().",
                 3: "n_valid_ids = int(ids.apply(ilanga.sa_id.is_valid).sum())"},
    "NQ-003.2": {1: "Luhn walks the 12 digits from the right and doubles every second digit, starting with the rightmost.",
                 2: "If doubling gives more than 9, subtract 9. Sum everything. The check digit is (10 - total % 10) % 10.",
                 3: "Loop with enumerate(reversed(first12)); double when the position index is even (0, 2, 4...)."},
    "NQ-003.3": {1: "Generate age and sex first, then give each person an asthma probability based on age.",
                 2: "np.where(age < 15, 0.08, 0.05) gives each person their own probability.",
                 3: "has_asthma = rng.random(5000) < prob. Use a fixed seed so the result is reproducible."},
    # ---------------- Module 4 ----------------
    "NQ-004.1": {1: "A direct identifier points to one person on its own - no other information needed.",
                 2: "Think: name parts, document numbers, contact details, where someone lives.",
                 3: "Check the catalogue: ilanga.data_dictionary('patients') has a privacy_class column. Compare your list."},
    "NQ-004.2": {1: "If k is below 5, some combinations of quasi-identifiers are too rare. Generalise one of them.",
                 2: "ART start year is very fine-grained. Try grouping years into periods such as '2004-2015', '2016-2020', '2021-2025'.",
                 3: "After generalising, recount with groupby(QIs).size(). Drop only the few rows still below k=5."},
    "NQ-004.3": {1: "Build the counts with pd.crosstab or groupby().size().unstack().",
                 2: "Any cell from 1 to 4 must become the text '<5'. Zeros can stay as 0.",
                 3: "table.map(lambda v: '<5' if 0 < v < 5 else v)  (use .applymap on older pandas)."},
}


def _ok(name, cond, hint):
    try:
        return (name, bool(cond), hint)
    except Exception:
        return (name, False, hint)


# ---------------------------------------------------------------------------------------------
def check_nq001(n_emr_live=None, biggest_subdistrict=None, digital_share_2025=None) -> bool:
    d = load_district()
    fac, pat, enc = d.facilities, d.patients, d.encounters
    exp1 = int(fac["emr_go_live"].notna().sum())
    exp2 = pat["subdistrict"].value_counts().idxmax()
    e = enc[enc["encounter_date"].dt.year == 2025].merge(fac[["facility_id", "subdistrict"]], on="facility_id")
    exp3 = e.groupby("subdistrict")["capture_mode"].apply(lambda s: (s == "Digital (e-Impilo)").mean() * 100)
    res = [_ok("🌱 Facilities live on e-Impilo", n_emr_live == exp1, "Count facilities with a go-live date. Try ilanga.hint('NQ-001.1')")]
    res.append(_ok("🌿 Largest subdistrict by registered patients", biggest_subdistrict == exp2,
                   "Expecting a subdistrict name as text. Try ilanga.hint('NQ-001.2')"))
    try:
        s = pd.Series(digital_share_2025).astype(float)
        good = set(s.index) == set(exp3.index) and np.allclose(s.reindex(exp3.index), exp3, atol=0.5)
        if good is False and s.max() <= 1.0:
            hint3 = "Looks like proportions (0-1). The ticket asks for percentages (0-100)."
        else:
            hint3 = "Need a Series indexed by subdistrict with % of 2025 visits captured digitally. Try ilanga.hint('NQ-001.3')"
    except Exception:
        good, hint3 = False, "digital_share_2025 should be a pandas Series indexed by subdistrict."
    res.append(_ok("🌳 Digital capture share per subdistrict (2025)", good, hint3))
    return gate_report("NQ-001", res)


def _mfula_2025():
    d = load_district()
    enc = d.encounters
    v = enc[(enc["facility_id"] == "ILN-CL01") & (enc["encounter_date"].dt.year == 2025)]
    return v, d.patients


def check_nq002(headcount_2025=None, monthly_headcount=None, under5_monthly=None) -> bool:
    v, pat = _mfula_2025()
    exp_m = v.groupby(v["encounter_date"].dt.month).size().reindex(range(1, 13), fill_value=0)
    m = v.merge(pat[["patient_id", "date_of_birth"]], on="patient_id")
    m = m[age_years(m["date_of_birth"], m["encounter_date"]) < 5]
    exp_u5 = m.groupby(m["encounter_date"].dt.month).size().reindex(range(1, 13), fill_value=0)
    res = [_ok("🌱 2025 headcount at Mfula Gateway Clinic", headcount_2025 == len(v),
               "Filter by facility AND year. Try ilanga.hint('NQ-002.1')")]
    try:
        s = pd.Series(monthly_headcount).reindex(range(1, 13)).astype(int)
        good2 = s.equals(exp_m.astype(int))
    except Exception:
        good2 = False
    res.append(_ok("🌿 Monthly headcount, Jan-Dec", good2, "Index should be month numbers 1-12. Try ilanga.hint('NQ-002.2')"))
    try:
        u = pd.Series(under5_monthly).reindex(range(1, 13)).fillna(0).astype(int)
        good3 = bool((u - exp_u5).abs().max() <= 2)
    except Exception:
        good3 = False
    res.append(_ok("🌳 Under-5 headcount by month", good3, "Age at the date of the visit, not today. Try ilanga.hint('NQ-002.3')"))
    return gate_report("NQ-002", res)


def check_nq003(n_valid_ids=None, my_luhn=None, mini_population=None) -> bool:
    pat = load_district().patients
    ids = pat.loc[pat["id_type"] == "SA_ID", "sa_id_number"]
    exp1 = int(ids.apply(sa_id.is_valid).sum())
    res = [_ok("🌱 Valid SA ID numbers counted", n_valid_ids == exp1, "Count only id_type == 'SA_ID'. Try ilanga.hint('NQ-003.1')")]
    try:
        sample = ids.sample(200, random_state=7)
        agree = all(int(my_luhn(s[:12])) == int(s[12]) for s in sample)
    except Exception:
        agree = False
    res.append(_ok("🌿 Your Luhn function matches 200 real-format IDs", agree,
                   "my_luhn('first 12 digits') should return the check digit as an int. Try ilanga.hint('NQ-003.2')"))
    try:
        mp = mini_population
        kids = mp.loc[mp["age"] < 15, "has_asthma"].mean()
        adults = mp.loc[mp["age"] >= 15, "has_asthma"].mean()
        good3 = len(mp) == 5000 and 0.06 <= kids <= 0.10 and 0.03 <= adults <= 0.07
    except Exception:
        good3 = False
    res.append(_ok("🌳 Mini-population with asthma hits its targets", good3,
                   "Need 5,000 rows with age, sex, has_asthma; ~8% children, ~5% adults. Try ilanga.hint('NQ-003.3')"))
    return gate_report("NQ-003", res)


def _eligible_hiv_adults():
    d = load_district()
    c = d.conditions
    hiv = c[(c["condition"] == "HIV") & c["art_start_date"].notna()]
    p = d.patients.set_index("patient_id")
    ages = age_years(p.loc[hiv["patient_id"], "date_of_birth"], pd.Timestamp("2025-12-31"))
    return hiv[(ages >= 18).values]


def check_nq004(my_direct_identifiers=None, research_extract=None, suppressed_table=None) -> bool:
    catalogue = {c for c, _, _, cls in DICTIONARY["patients"] if cls == "direct_identifier"}
    mine = set(my_direct_identifiers or [])
    missed, extra = catalogue - mine, mine - catalogue
    hint1 = "Matches the catalogue." if not (missed or extra) else \
        f"Missed: {sorted(missed) or 'none'}; not direct identifiers: {sorted(extra) or 'none'}. Try ilanga.hint('NQ-004.1')"
    res = [_ok("🌱 Direct identifiers classified", not (missed or extra), hint1)]

    qi = ["age_band", "sex", "subdistrict", "art_start_year"]
    try:
        x = research_extract
        need = {"study_id", "age_band", "sex", "subdistrict", "art_start_year", "latest_vl_suppressed"}
        forbidden = catalogue | {"patient_id", "date_of_birth", "ward"}
        cols_ok = set(x.columns) == need
        no_pii = not (set(x.columns) & forbidden)
        eligible = _eligible_hiv_adults()
        ids_ok = x["study_id"].is_unique and not x["study_id"].astype(str).isin(eligible["patient_id"]).any()
        k = int(x.groupby(qi, observed=True).size().min())
        coverage = len(x) / len(eligible)
        res.append(_ok("🌿 Extract has exactly the approved columns", cols_ok,
                       f"Expected columns: {sorted(need)}"))
        res.append(_ok("🌿 No identifiers leak into the extract", no_pii and ids_ok,
                       "Remove identifiers and replace patient_id with a keyed pseudonym (study_id)."))
        res.append(_ok(f"🌿 k-anonymity ≥ 5 (yours: k={k})", k >= 5, "Try ilanga.hint('NQ-004.2')"))
        res.append(_ok(f"🌿 Keeps ≥ 90% of eligible patients (yours: {coverage:.0%})", coverage >= 0.9,
                       "Generalise before you suppress - researchers need the data to be useful."))
    except Exception as ex:
        msg = "research_extract is still None - build it first." if research_extract is None \
            else f"Could not check research_extract: {ex}"
        res.append(_ok("🌿 Research extract", False, msg))
    try:
        vals = pd.Series(np.asarray(suppressed_table, dtype=object).ravel())
        nums = pd.to_numeric(vals, errors="coerce")
        good3 = not nums.between(1, 4).any() and len(vals) > 1
    except Exception:
        good3 = False
    res.append(_ok("🌳 Small cells (1-4) suppressed in the aggregate table", good3, "Try ilanga.hint('NQ-004.3')"))
    return gate_report("NQ-004", res)

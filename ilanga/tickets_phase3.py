"""Quality gates for Phase 3: Analytics (Modules 9-12)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import load_district
from .brand import gate_report
from .extensions_v12 import OUTBREAK, PHC_TYPES, SLA_HOURS

HINTS3 = {
    # ---------------- Module 9 ----------------
    "NQ-009.1": {1: "Expected reports = number of PHC facilities in the sub-district x 12 months.",
                 2: "Use rows where data_element == 'PHC headcount total' and period starts with '2025'. Each row is one report received.",
                 3: "received.groupby('subdistrict').size() / expected * 100, where expected = PHC facilities per sub-district * 12."},
    "NQ-009.2": {1: "Only compare months the facility actually reported - otherwise a missing report looks like an undercount.",
                 2: "Count 2025 encounters per facility and month, merge onto the reported rows on facility_id + period, then sum both columns per facility.",
                 3: "pct_difference = 100 * (reported - computed) / computed."},
    "NQ-009.3": {1: "Work step by step, filtering the previous step's patients each time.",
                 2: "In care = HIV records not Died or Transferred out. On ART = status 'Active'. Eligible for VL = ART start on or before 2025-06-30.",
                 3: "Suppressed = the patient's LATEST 2025 viral load is below the detection limit or < 1,000 copies/mL."},
    # ---------------- Module 10 ----------------
    "NQ-010.1": {1: "The Wilson interval uses p = k/n, z = 1.96, and a centre that is pulled towards 0.5.",
                 2: "centre = (p + z²/2n) / (1 + z²/n);  half-width = z·sqrt(p(1-p)/n + z²/4n²) / (1 + z²/n)",
                 3: "Return (centre - half_width, centre + half_width) as a tuple of proportions (0-1), not percentages."},
    "NQ-010.2": {1: "Split the registered population into two groups: people with an HIV record and people without.",
                 2: "Risk in each group = people with a TB record / people in the group.",
                 3: "Rate ratio = risk among people with HIV / risk among people without HIV."},
    "NQ-010.3": {1: "Compare each week with a baseline built from EARLIER weeks at the same facility - never including the week itself.",
                 2: "A baseline of weeks t-3 to t-10 (a guard band of two weeks) stops an outbreak from raising its own baseline.",
                 3: "Flag when cases > baseline mean + z x baseline SD. Try different z values and count your alerts."},
    # ---------------- Module 11 ----------------
    "NQ-011.1": {1: "Convert degrees to radians first with np.radians.",
                 2: "a = sin²(Δlat/2) + cos(lat1)·cos(lat2)·sin²(Δlon/2); distance = 2·R·arcsin(√a), R = 6371 km.",
                 3: "Use numpy functions (np.sin, np.cos, np.arcsin, np.sqrt) so the function works on arrays too."},
    "NQ-011.2": {1: "For each ward, measure the distance to every PHC facility, then keep the smallest.",
                 2: "PHC facilities are Clinics, CHCs and the Mobile Clinic - not hospitals, not the laboratory.",
                 3: "Loop over wards, compute haversine_km to all PHC facilities at once (arrays), then use argmin()."},
    "NQ-011.3": {1: "Build each KPI as a Series indexed by sub-district, then combine them with pd.concat(axis=1).",
                 2: "Headcount, suppression and referrals are counted by the FACILITY's sub-district. Access uses ward populations.",
                 3: "pct_pop_within_5km = population in wards with distance_km <= 5, divided by total population, per sub-district."},
    # ---------------- Module 12 ----------------
    "NQ-012.1": {1: "Total turnaround time = reported_at - collected_at, converted to hours.",
                 2: "Filter to results collected in 2025, then groupby('test_code')['tat_h'].",
                 3: ".agg(median_h='median', p90_h=lambda s: s.quantile(0.9))"},
    "NQ-012.2": {1: "The SLA measures what the lab controls: received_at to reported_at.",
                 2: "Map each test_code to its SLA hours with ilanga.extensions_v12.SLA_HOURS.",
                 3: "Compliance = (lab_tat_h <= sla_h).mean() * 100, grouped by test_code."},
    "NQ-012.3": {1: "Start with VL results >= 1,000 copies/mL collected 1 Jan - 30 Sep 2025.",
                 2: "For each result, look for any encounter by the same patient from the day after the report up to 28 days after.",
                 3: "Merge results with encounters on patient_id, compute days = (encounter_date - reported_at.normalize()).dt.days, keep 1 <= days <= 28."},
}


def _ok(name, cond, hint):
    try:
        return (name, bool(cond), hint)
    except Exception:
        return (name, False, hint)


# ------------------------------- shared reference definitions -------------------------------
def ref_completeness_2025(d):
    fac = d.facilities
    phc = fac[fac["facility_type"].isin(PHC_TYPES)]
    rep = d.dhis_monthly[(d.dhis_monthly["data_element"] == "PHC headcount total") & d.dhis_monthly["period"].str.startswith("2025")]
    rep = rep.merge(fac[["facility_id", "subdistrict"]], on="facility_id")
    return (rep.groupby("subdistrict").size() / (phc.groupby("subdistrict").size() * 12) * 100)


def ref_concordance_2025(d):
    e = d.encounters[d.encounters["encounter_date"].dt.year == 2025].copy()
    e["period"] = e["encounter_date"].dt.strftime("%Y-%m")
    comp = e.groupby(["facility_id", "period"]).size().rename("computed").reset_index()
    rep = d.dhis_monthly[(d.dhis_monthly["data_element"] == "PHC headcount total") & d.dhis_monthly["period"].str.startswith("2025")]
    m = rep[["facility_id", "period", "reported_value"]].merge(comp, on=["facility_id", "period"], how="left").fillna({"computed": 0})
    out = m.groupby("facility_id")[["reported_value", "computed"]].sum().rename(columns={"reported_value": "reported"})
    out["pct_difference"] = 100 * (out["reported"] - out["computed"]) / out["computed"]
    return out


def ref_hiv_cascade(d):
    c = d.conditions[d.conditions["condition"] == "HIV"]
    in_care = c[~c["status"].isin(["Died", "Transferred out"])]
    on_art = in_care[in_care["status"] == "Active"]
    eligible = on_art[on_art["art_start_date"] <= pd.Timestamp("2025-06-30")]
    vl = d.lab_results[(d.lab_results["test_code"] == "VL") & (d.lab_results["collected_at"].dt.year == 2025)]
    vl = vl[vl["patient_id"].isin(eligible["patient_id"])]
    latest = vl.sort_values("collected_at").groupby("patient_id").tail(1)
    suppressed = latest["below_detection_limit"] | (latest["result_numeric"] < 1000)
    return pd.DataFrame({"step": ["Living with HIV, in care", "On ART", "Viral load done (2025)", "Virally suppressed (<1000)"],
                         "count": [len(in_care), len(on_art), latest["patient_id"].nunique(), int(suppressed.sum())]})


def ref_wilson(k, n, z=1.96):
    p = k / n
    denom = 1 + z ** 2 / n
    centre = (p + z ** 2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denom
    return centre - half, centre + half


def ref_tb_rr(d):
    hiv = set(d.conditions.loc[d.conditions["condition"] == "HIV", "patient_id"])
    tb = set(d.conditions.loc[d.conditions["condition"] == "Tuberculosis", "patient_id"])
    ids = d.patients["patient_id"]
    exposed = ids.isin(hiv)
    has_tb = ids.isin(tb)
    return has_tb[exposed].mean() / has_tb[~exposed].mean()


def haversine_ref(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(a))


def ref_ward_access(d):
    phc = d.facilities[d.facilities["facility_type"].isin(PHC_TYPES)].reset_index(drop=True)
    rows = []
    for w in d.wards.itertuples():
        dist = haversine_ref(w.latitude, w.longitude, phc["latitude"].values, phc["longitude"].values)
        i = int(np.argmin(dist))
        rows.append({"ward": w.ward, "nearest_facility_id": phc.loc[i, "facility_id"], "distance_km": float(dist[i])})
    return pd.DataFrame(rows)


def ref_kpi_table(d):
    fsub = d.facilities.set_index("facility_id")["subdistrict"]
    e = d.encounters[d.encounters["encounter_date"].dt.year == 2025]
    headcount = e["facility_id"].map(fsub).value_counts()
    vl = d.lab_results[(d.lab_results["test_code"] == "VL") & (d.lab_results["collected_at"].dt.year == 2025)]
    supp = (vl["below_detection_limit"] | (vl["result_numeric"] < 1000)).groupby(vl["ordering_facility_id"].map(fsub)).mean() * 100
    r = d.referrals[d.referrals["referral_date"].dt.year == 2025]
    arrive = (r["outcome"] == "Seen").groupby(r["from_facility_id"].map(fsub)).mean() * 100
    acc = d.wards.merge(ref_ward_access(d), on="ward")
    within = acc.assign(p5=acc["estimated_population"].where(acc["distance_km"] <= 5, 0)).groupby("subdistrict")
    access = within["p5"].sum() / within["estimated_population"].sum() * 100
    return pd.concat([headcount.rename("headcount_2025"), supp.rename("vl_suppression_pct"),
                      arrive.rename("referral_arrival_pct"), access.rename("pct_pop_within_5km")], axis=1).sort_index()


def ref_tat(d):
    l = d.lab_results[d.lab_results["collected_at"].dt.year == 2025].copy()
    l["tat_h"] = (l["reported_at"] - l["collected_at"]).dt.total_seconds() / 3600
    l["lab_tat_h"] = (l["reported_at"] - l["received_at"]).dt.total_seconds() / 3600
    return l


def ref_high_vl_followup(d):
    l = d.lab_results
    hv = l[(l["test_code"] == "VL") & (l["result_numeric"] >= 1000) &
           l["collected_at"].between("2025-01-01", "2025-09-30 23:59")][["specimen_id", "patient_id", "reported_at"]]
    m = hv.merge(d.encounters[["patient_id", "encounter_date"]], on="patient_id", how="left")
    days = (m["encounter_date"] - m["reported_at"].dt.normalize()).dt.days
    m["hit"] = days.between(1, 28)
    seen = m.groupby("specimen_id")["hit"].any()
    return hv.assign(seen_within_28d=hv["specimen_id"].map(seen).fillna(False).astype(bool))


# ============================== Module 9 ==============================
def check_nq009(reporting_completeness=None, concordance_2025=None, hiv_cascade=None) -> bool:
    d = load_district()
    res = []
    try:
        exp = ref_completeness_2025(d)
        got = pd.Series(reporting_completeness).astype(float)
        good1 = set(got.index) == set(exp.index) and np.allclose(got.reindex(exp.index), exp, atol=0.1)
        hint1 = "Values look like proportions - the ticket asks for %." if good1 is False and got.max() <= 1 else "Try ilanga.hint('NQ-009.1')"
    except Exception:
        good1, hint1 = False, "Need a Series indexed by sub-district. Try ilanga.hint('NQ-009.1')"
    res.append(_ok("🌱 2025 reporting completeness by sub-district", good1, hint1))
    try:
        exp = ref_concordance_2025(d)
        got = concordance_2025.set_index("facility_id") if "facility_id" in concordance_2025.columns else concordance_2025
        got = got.reindex(exp.index)
        good2 = np.allclose(got[["reported", "computed", "pct_difference"]].astype(float), exp, atol=0.1)
    except Exception:
        good2 = False
    res.append(_ok("🌿 Reported vs computed headcount per facility", good2, "Try ilanga.hint('NQ-009.2')"))
    try:
        exp = ref_hiv_cascade(d)
        good3 = list(hiv_cascade["count"].astype(int)) == list(exp["count"])
        hint3 = "Try ilanga.hint('NQ-009.3')" if good3 else f"Expected 4 steps in order. Yours: {list(hiv_cascade['count'])}"
    except Exception:
        good3, hint3 = False, "hiv_cascade needs columns 'step' and 'count', four rows in cascade order."
    res.append(_ok("🌳 HIV care cascade matches the district definition", good3, hint3))
    return gate_report("NQ-009", res)


# ============================== Module 10 ==============================
def check_nq010(wilson_ci=None, tb_rate_ratio=None, outbreak_alerts=None) -> bool:
    d = load_district()
    res = []
    try:
        cases = [(12, 40), (0, 25), (95, 100), (500, 20000), (7, 7)]
        good1 = all(np.allclose(wilson_ci(k, n), ref_wilson(k, n), atol=1e-6) for k, n in cases)
    except Exception:
        good1 = False
    res.append(_ok("🌱 Wilson 95% confidence interval", good1, "Return proportions (0-1). Try ilanga.hint('NQ-010.1')"))
    try:
        exp = ref_tb_rr(d)
        good2 = abs(float(tb_rate_ratio) - exp) < 0.01
    except Exception:
        good2 = False
    res.append(_ok("🌿 TB risk ratio, HIV vs no HIV", good2, "Try ilanga.hint('NQ-010.2')"))
    try:
        a = outbreak_alerts
        a25 = a[a["iso_week"].astype(str).str.startswith("2025")]
        hit = ((a25["facility_id"] == OUTBREAK["facility_id"]) & a25["iso_week"].isin(OUTBREAK["weeks"][:2])).any()
        n = len(a25)
        res.append(_ok("🌳 Outbreak detected within its first two weeks", hit,
                       "Your rule missed the start of the outbreak - too strict? Try ilanga.hint('NQ-010.3')"))
        res.append(_ok(f"🌳 False-alarm budget: ≤ 15 alerts in 2025 (yours: {n})", 0 < n <= 15,
                       "Too many alerts and the district team stops reading them. Raise your threshold."))
    except Exception:
        res.append(_ok("🌳 Outbreak alerts", False, "Need a DataFrame with columns facility_id and iso_week."))
    return gate_report("NQ-010", res)


# ============================== Module 11 ==============================
def check_nq011(haversine_km=None, ward_access=None, kpi_table=None) -> bool:
    d = load_district()
    res = []
    try:
        tests = [(-29.40, 31.26, -29.19, 30.74), (-29.3, 31.0, -29.3, 31.0), (-33.92, 18.42, -29.86, 31.02)]
        good1 = all(abs(float(haversine_km(*t)) - float(haversine_ref(*t))) < 0.01 for t in tests)
    except Exception:
        good1 = False
    res.append(_ok("🌱 Haversine distance (Cape Town to Durban ≈ 1,275 km)", good1, "Try ilanga.hint('NQ-011.1')"))
    try:
        exp = ref_ward_access(d).set_index("ward")
        got = ward_access.set_index("ward").reindex(exp.index)
        good2 = (got["nearest_facility_id"] == exp["nearest_facility_id"]).all() and \
            np.allclose(got["distance_km"].astype(float), exp["distance_km"], atol=0.05)
    except Exception:
        good2 = False
    res.append(_ok("🌿 Nearest PHC facility and distance for every ward", good2, "Try ilanga.hint('NQ-011.2')"))
    try:
        exp = ref_kpi_table(d)
        got = kpi_table.reindex(exp.index)[exp.columns].astype(float)
        good3 = np.allclose(got, exp, atol=0.1)
    except Exception:
        good3 = False
    res.append(_ok("🌳 District KPI table", good3,
                   "Index = sub-district; columns: headcount_2025, vl_suppression_pct, referral_arrival_pct, pct_pop_within_5km"))
    return gate_report("NQ-011", res)


# ============================== Module 12 ==============================
def check_nq012(tat_summary=None, sla_compliance=None, high_vl_followup=None) -> bool:
    d = load_district()
    l = ref_tat(d)
    res = []
    try:
        exp = l.groupby("test_code")["tat_h"].agg(median_h="median", p90_h=lambda s: s.quantile(0.9))
        got = tat_summary.reindex(exp.index)[["median_h", "p90_h"]].astype(float)
        good1 = np.allclose(got, exp, atol=0.1)
    except Exception:
        good1 = False
    res.append(_ok("🌱 Turnaround time: median and 90th percentile by test", good1, "Try ilanga.hint('NQ-012.1')"))
    try:
        exp = (l["lab_tat_h"] <= l["test_code"].map(SLA_HOURS)).groupby(l["test_code"]).mean() * 100
        got = pd.Series(sla_compliance).astype(float).reindex(exp.index)
        good2 = np.allclose(got, exp, atol=0.1)
    except Exception:
        good2 = False
    res.append(_ok("🌿 SLA compliance by test (lab-controlled TAT)", good2, "Try ilanga.hint('NQ-012.2')"))
    try:
        exp = ref_high_vl_followup(d).set_index("specimen_id")
        got = high_vl_followup.set_index("specimen_id")
        good3 = set(got.index) == set(exp.index) and \
            (got.loc[exp.index, "seen_within_28d"].astype(bool) == exp["seen_within_28d"]).all()
        hint3 = "Try ilanga.hint('NQ-012.3')" if set(got.index) == set(exp.index) else \
            f"Expected {len(exp)} high viral load results; you have {len(got)}. Check the date window and threshold."
    except Exception:
        good3, hint3 = False, "Need columns specimen_id, patient_id, reported_at, seen_within_28d."
    res.append(_ok("🌳 High viral load follow-up within 28 days", good3, hint3))
    return gate_report("NQ-012", res)

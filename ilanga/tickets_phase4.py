"""Quality gates for Phase 4: Advanced & Capstone (Modules 13-16)."""
from __future__ import annotations

import re

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from . import load_district, ml
from .brand import gate_report
from .extensions_v12 import PHC_TYPES
from .tickets_phase3 import ref_concordance_2025, ref_high_vl_followup

HINTS4 = {
    # ---------------- Module 13 ----------------
    "NQ-013.1": {1: "Count referrals per (from, to) pair first with groupby, then add one edge per pair.",
                 2: "G = nx.DiGraph(); G.add_edge(a, b, weight=n, arrived=k) for each row.",
                 3: "Every facility should also be a node, even if it has no referrals: G.add_nodes_from(facility_ids)."},
    "NQ-013.2": {1: "Start from each patient's set of distinct facilities they VISITED (encounters), not where they registered.",
                 2: "For each patient with 2+ facilities, every pair of their facilities gets +1 shared patient. itertools.combinations helps.",
                 3: "Sort each pair so (A, B) and (B, A) count together, then use a Counter or groupby."},
    "NQ-013.3": {1: "In the knowledge graph, start at the COND:HIV node and walk to patients, then check their other edges.",
                 2: "G.predecessors('COND:HIV') gives patients with HIV. For each, check G.has_edge(patient, 'COND:Tuberculosis').",
                 3: "Then find that patient's LabResult nodes, take the one with the latest collected_at, and keep the patient if it is not suppressed."},
    # ---------------- Module 14 ----------------
    "NQ-014.1": {1: "ilanga.ml.at_risk_cohort(d) already applies the definition. Your job is to understand it, then use it.",
                 2: "labels = cohort.set_index('patient_id')['ltfu_next_12m']",
                 3: "It must be a Series indexed by patient_id, values 0 or 1."},
    "NQ-014.2": {1: "Only use information from BEFORE the cutoff date. Missed appointments in the last 6 months are a strong signal.",
                 2: "Train on ilanga.ml.train_test_ids(d)[0], predict on [1]. LogisticRegression with class_weight='balanced' is a good start.",
                 3: "test_risk = pd.Series(model.predict_proba(X.loc[test_ids])[:, 1], index=test_ids)"},
    "NQ-014.3": {1: "The tracing team can call 20% of test patients. Flag the top 20% of risk scores.",
                 2: "flagged = test_risk >= test_risk.quantile(0.8). Then group by sub-district.",
                 3: "recall = flagged LTFU / all LTFU in that group; flag_rate = flagged / people in that group."},
    # ---------------- Module 15 ----------------
    "NQ-015.1": {1: "Blood pressure appears as 'BP 152/96'. A regular expression can capture both numbers.",
                 2: r"re.search(r'BP\s*(\d{2,3})\s*/\s*(\d{2,3})', note)",
                 3: "Return (float(m.group(1)), float(m.group(2))) if found, else (np.nan, np.nan)."},
    "NQ-015.2": {1: "Split the note into clauses at commas and full stops. Decide each clause separately.",
                 2: "Search for negation cues ANYWHERE in the clause, not just at the start - the first clause reads 'Pt no fever'. Cues: no, not, denies, nil, afebrile, stable, or a trailing '-'.",
                 3: "Keywords: cough; fever/febrile/T 38; night sweats/NS; LOW/wt loss/lost __kg. Watch out: splitting on full stops also splits 'T 38.4', and 'weight stable' means no weight loss."},
    "NQ-015.3": {1: "Check for urgent danger signs FIRST, in English and isiZulu, before any other intent.",
                 2: "Urgent words include: bleeding, ngiyopha, breathing, ayiphefumuli, fits, blurred vision, severe headache.",
                 3: "Then medication (pills, tablets, amaphilisi), results (results, imiphumela), appointment (date, appointment, emtholampilo, when), else feedback."},
    # ---------------- Module 16 ----------------
    "NQ-016.1": {1: "Build one column at a time, each a Series indexed by facility_id, then pd.concat(axis=1).",
                 2: "Reuse your Module 9 (completeness, concordance) and Module 12 (high VL follow-up) logic.",
                 3: "criteria_met counts how many of the five thresholds are met; a missing value counts as not met."},
}


def _ok(name, cond, hint):
    try:
        return (name, bool(cond), hint)
    except Exception:
        return (name, False, hint)


# ------------------------------------------------------------------ reference definitions
def ref_referral_graph(d):
    r = d.referrals.assign(arrived=(d.referrals["outcome"] == "Seen").astype(int))
    agg = r.groupby(["from_facility_id", "to_facility_id"]).agg(weight=("referral_id", "size"), arrived=("arrived", "sum"))
    G = nx.DiGraph()
    G.add_nodes_from(d.facilities["facility_id"])
    for (a, b), row in agg.iterrows():
        G.add_edge(a, b, weight=int(row["weight"]), arrived=int(row["arrived"]))
    return G


def ref_shared_patients(d):
    from collections import Counter
    from itertools import combinations
    visits = d.encounters.groupby("patient_id")["facility_id"].unique()
    cnt = Counter()
    for facs in visits:
        for a, b in combinations(sorted(facs), 2):
            cnt[(a, b)] += 1
    return pd.DataFrame([(a, b, n) for (a, b), n in cnt.items()], columns=["facility_a", "facility_b", "patients"])


def ref_hiv_tb_unsuppressed(d):
    c = d.conditions
    both = set(c.loc[c["condition"] == "HIV", "patient_id"]) & set(c.loc[c["condition"] == "Tuberculosis", "patient_id"])
    vl = d.lab_results[(d.lab_results["test_code"] == "VL") & d.lab_results["patient_id"].isin(both)]
    latest = vl.sort_values("collected_at").groupby("patient_id").tail(1)
    unsupp = latest[~(latest["below_detection_limit"] | (latest["result_numeric"] < 1000))]
    return set(unsupp["patient_id"])


def ref_bp(note):
    m = re.search(r"BP\s*(\d{2,3})\s*/\s*(\d{2,3})", str(note))
    return (float(m.group(1)), float(m.group(2))) if m else (np.nan, np.nan)


def ref_readiness(d):
    fac = d.facilities[d.facilities["facility_type"].isin(PHC_TYPES)].set_index("facility_id")
    e25 = d.encounters[d.encounters["encounter_date"].dt.year == 2025]
    digital = (e25["capture_mode"] == "Digital (e-Impilo)").groupby(e25["facility_id"]).mean() * 100
    rep = d.dhis_monthly[(d.dhis_monthly["data_element"] == "PHC headcount total") & d.dhis_monthly["period"].str.startswith("2025")]
    completeness = rep.groupby("facility_id").size() / 12 * 100
    gap = ref_concordance_2025(d)["pct_difference"].abs()
    c = d.conditions
    act = c[(c["condition"] == "HIV") & (c["status"] == "Active") & (c["art_start_date"] <= "2025-06-30")]
    act = act.assign(home=act["patient_id"].map(d.patients.set_index("patient_id")["home_facility_id"]))
    vl25 = set(d.lab_results.loc[(d.lab_results["test_code"] == "VL") & (d.lab_results["collected_at"].dt.year == 2025), "patient_id"])
    vl_done = act["patient_id"].isin(vl25).groupby(act["home"]).mean() * 100
    fu = ref_high_vl_followup(d)
    fu = fu.assign(fac=fu["specimen_id"].map(d.lab_results.set_index("specimen_id")["ordering_facility_id"]))
    followup = fu.groupby("fac")["seen_within_28d"].mean() * 100
    t = pd.DataFrame({"digital_capture_pct": digital, "reporting_completeness_pct": completeness,
                      "concordance_gap_pct": gap, "vl_done_pct": vl_done, "high_vl_followup_pct": followup}).reindex(fac.index)
    met = pd.DataFrame({
        "a": t["digital_capture_pct"] >= 90, "b": t["reporting_completeness_pct"] >= 95,
        "c": t["concordance_gap_pct"] <= 2, "d": t["vl_done_pct"] >= 90, "e": t["high_vl_followup_pct"] >= 50})
    t["criteria_met"] = met.sum(axis=1)
    t["readiness"] = np.select([t["criteria_met"] >= 4, t["criteria_met"] == 3], ["Ready", "Nearly ready"], "Not ready")
    return t


# ============================== Module 13 ==============================
def check_nq013(referral_graph=None, shared_patients=None, hiv_tb_unsuppressed=None) -> bool:
    d = load_district()
    res = []
    try:
        exp = ref_referral_graph(d)
        G = referral_graph
        good1 = isinstance(G, nx.DiGraph) and set(G.nodes) == set(exp.nodes) and set(G.edges) == set(exp.edges) and \
            all(G.edges[e].get("weight") == exp.edges[e]["weight"] for e in exp.edges)
    except Exception:
        good1 = False
    res.append(_ok("🌱 Directed referral network with weighted edges", good1, "Try ilanga.hint('NQ-013.1')"))
    try:
        exp = ref_shared_patients(d)
        sp = shared_patients.copy()
        sp[["facility_a", "facility_b"]] = np.sort(sp[["facility_a", "facility_b"]].values, axis=1)
        got = sp.groupby(["facility_a", "facility_b"])["patients"].sum()
        good2 = got.sort_index().equals(exp.set_index(["facility_a", "facility_b"])["patients"].sort_index().astype(got.dtype))
    except Exception:
        good2 = False
    res.append(_ok("🌿 Shared-patient network between facilities", good2, "Try ilanga.hint('NQ-013.2')"))
    try:
        exp = ref_hiv_tb_unsuppressed(d)
        got = set(hiv_tb_unsuppressed)
        good3 = got == exp
        hint3 = "Try ilanga.hint('NQ-013.3')" if good3 else f"Expected {len(exp)} patients; you found {len(got)} ({len(got & exp)} correct)."
    except Exception:
        good3, hint3 = False, "hiv_tb_unsuppressed should be a set of patient IDs."
    res.append(_ok("🌳 Multi-hop query: HIV + TB + latest viral load unsuppressed", good3, hint3))
    return gate_report("NQ-013", res)


# ============================== Module 14 ==============================
def check_nq014(labels=None, test_risk=None, fairness_table=None) -> bool:
    d = load_district()
    cohort = ml.at_risk_cohort(d).set_index("patient_id")["ltfu_next_12m"]
    _, test_ids = ml.train_test_ids(d)
    res = []
    try:
        good1 = pd.Series(labels).astype(int).sort_index().equals(cohort.sort_index())
    except Exception:
        good1 = False
    res.append(_ok("🌱 Outcome labels match the team's cohort definition", good1, "Try ilanga.hint('NQ-014.1')"))
    try:
        tr = pd.Series(test_risk).astype(float)
        same = set(tr.index) == set(test_ids)
        auc = roc_auc_score(cohort.loc[test_ids], tr.loc[test_ids]) if same else 0
        res.append(_ok("🌿 Predictions for exactly the team's test patients", same,
                       "Use ilanga.ml.train_test_ids(d)[1] - and never train on these patients."))
        res.append(_ok(f"🌿 Test AUC ≥ 0.60 (yours: {auc:.3f})", auc >= 0.60,
                       "Stronger pre-cutoff features help: recent missed appointments, last viral load. Try ilanga.hint('NQ-014.2')"))
        if auc > 0.9:
            res.append(_ok("🌿 Leakage check", False,
                           "AUC above 0.9 on this problem almost always means leakage. Did any feature use data after the cutoff?"))
    except Exception:
        res.append(_ok("🌿 Test predictions", False, "test_risk should be a Series of risk scores indexed by patient_id."))
    try:
        tr = pd.Series(test_risk).astype(float).loc[test_ids]
        flagged = tr >= tr.quantile(0.8)
        sd = d.patients.set_index("patient_id").loc[test_ids, "subdistrict"]
        y = cohort.loc[test_ids]
        exp = pd.DataFrame({"n": sd.value_counts(), "flag_rate": flagged.groupby(sd).mean() * 100,
                            "recall": (flagged & (y == 1)).groupby(sd).sum() / (y == 1).groupby(sd).sum() * 100})
        got = fairness_table.reindex(exp.index)[["n", "flag_rate", "recall"]].astype(float)
        good3 = np.allclose(got, exp, atol=0.1)
    except Exception:
        good3 = False
    res.append(_ok("🌳 Fairness table by sub-district (flag rate and recall at top 20%)", good3, "Try ilanga.hint('NQ-014.3')"))
    return gate_report("NQ-014", res)


# ============================== Module 15 ==============================
SYMPTOM_COLS = ["cough", "fever", "night_sweats", "weight_loss"]


def check_nq015(extract_bp=None, tb_symptoms=None, triage=None) -> bool:
    d = load_district()
    notes = d.clinical_notes.merge(d.note_annotations, on="note_id")
    res = []
    try:
        got = notes["note_text"].apply(extract_bp)
        s = got.apply(lambda t: t[0])
        di = got.apply(lambda t: t[1])
        ok_s = (s.fillna(-1) == notes["bp_systolic"].fillna(-1))
        ok_d = (di.fillna(-1) == notes["bp_diastolic"].fillna(-1))
        acc1 = (ok_s & ok_d).mean()
    except Exception:
        acc1 = 0
    res.append(_ok(f"🌱 Blood pressure extracted from every note (accuracy {acc1:.1%}, need ≥ 99%)", acc1 >= 0.99,
                   "Try ilanga.hint('NQ-015.1')"))
    try:
        pred = pd.DataFrame(list(notes["note_text"].apply(tb_symptoms)))
        accs = {c: (pred[c].astype(bool).values == notes[c].astype(bool).values).mean() for c in SYMPTOM_COLS}
        worst = min(accs, key=accs.get)
        good2 = all(a >= 0.95 for a in accs.values())
        hint2 = "Try ilanga.hint('NQ-015.2')" if good2 else f"Weakest: {worst} at {accs[worst]:.1%}. Check negations. Try ilanga.hint('NQ-015.2')"
    except Exception:
        good2, hint2 = False, "tb_symptoms should return a dict with keys cough, fever, night_sweats, weight_loss."
    res.append(_ok("🌿 TB symptoms detected with negation handling (≥ 95% each)", good2, hint2))
    try:
        m = d.helpdesk_messages
        pred = m["message_text"].apply(triage)
        urgent_recall = (pred[m["intent"] == "urgent"] == "urgent").mean()
        acc = (pred == m["intent"]).mean()
        res.append(_ok(f"🌳 Every urgent message caught (recall {urgent_recall:.0%}, must be 100%)", urgent_recall == 1.0,
                       "A missed danger sign could cost a life. Check isiZulu and code-switched urgent messages."))
        res.append(_ok(f"🌳 Overall triage accuracy ≥ 85% (yours: {acc:.1%})", acc >= 0.85, "Try ilanga.hint('NQ-015.3')"))
    except Exception:
        res.append(_ok("🌳 Helpline triage", False, "triage(message) should return one intent string."))
    return gate_report("NQ-015", res)


# ============================== Module 16 ==============================
REPORT_SECTIONS = ["Executive summary", "Data quality", "Clinical performance", "Access", "Governance", "Recommendations"]


def check_nq016(readiness=None, report_path: str = "capstone_report.md") -> bool:
    d = load_district()
    res = []
    try:
        exp = ref_readiness(d)
        got = readiness.reindex(exp.index)
        num = ["digital_capture_pct", "reporting_completeness_pct", "concordance_gap_pct", "vl_done_pct", "high_vl_followup_pct"]
        good1 = np.allclose(got[num].astype(float).fillna(-1), exp[num].fillna(-1), atol=0.1) and \
            (got["criteria_met"].astype(int) == exp["criteria_met"]).all() and (got["readiness"] == exp["readiness"]).all()
    except Exception:
        good1 = False
    res.append(_ok("🎓 Facility readiness scorecard", good1, "Try ilanga.hint('NQ-016.1')"))
    try:
        text = open(report_path, encoding="utf-8").read()
        missing = [s for s in REPORT_SECTIONS if not re.search(rf"^#+\s*{re.escape(s)}", text, re.M | re.I)]
        words = len(re.findall(r"\w+", text))
        res.append(_ok("🎓 Report has all six required sections", not missing, f"Missing headings: {missing}"))
        res.append(_ok(f"🎓 Report is substantive (≥ 400 words; yours: {words})", words >= 400,
                       "Explain your findings - numbers need interpretation."))
    except FileNotFoundError:
        res.append(_ok("🎓 Capstone report", False, f"Could not find {report_path}. Save your report first."))
    return gate_report("NQ-016", res)

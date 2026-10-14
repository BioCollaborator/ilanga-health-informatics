"""
Dataset v1.1 extensions: medicine dispensing and referrals.

Built from the curated tables with their OWN random generator, so everything generated in
v1.0 (patients, visits, labs) is byte-for-byte unchanged and Phase 1 notebooks behave exactly
as before.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# medicine key: (display name, strength, ATC code, tablets per day)
MEDICINES = {
    "TLD":      ("Tenofovir/Lamivudine/Dolutegravir", "300/300/50 mg", "J05AR27", 1),
    "TEE":      ("Tenofovir/Emtricitabine/Efavirenz", "300/200/600 mg", "J05AR06", 1),
    "AZT3TC":   ("Zidovudine/Lamivudine", "300/150 mg", "J05AR01", 2),
    "LPVR":     ("Lopinavir/Ritonavir", "200/50 mg", "J05AR10", 4),
    "ABC3TC":   ("Abacavir/Lamivudine", "120/60 mg", "J05AR02", 1),
    "DTG10":    ("Dolutegravir", "10 mg", "J05AX12", 1),
    "AMLO":     ("Amlodipine", "5 mg", "C08CA01", 1),
    "HCTZ":     ("Hydrochlorothiazide", "12.5 mg", "C03AA03", 1),
    "ENAL":     ("Enalapril", "10 mg", "C09AA02", 1),
    "METF":     ("Metformin", "500 mg", "A10BA02", 2),
    "GLIC":     ("Gliclazide", "80 mg", "A10BB09", 1),
    "RHZE":     ("Rifampicin/Isoniazid/Pyrazinamide/Ethambutol", "150/75/400/275 mg", "J04AM06", 4),
    "RH":       ("Rifampicin/Isoniazid", "150/75 mg", "J04AM02", 4),
}
REGIMEN_LINES = {"TLD": ["TLD"], "TEE": ["TEE"], "AZT/3TC/LPV/r": ["AZT3TC", "LPVR"], "ABC/3TC/DTG": ["ABC3TC", "DTG10"]}

# Free-text variants seen in real dispensing systems (used for the raw layer, Module 6)
MESSY_NAMES = {
    "TLD":    ["TLD", "Tenofovir/Lamivudine/Dolutegravir 300/300/50mg", "TDF/3TC/DTG", "tld 1 tab daily", "TENOFOVIR+LAMIVUDINE+DOLUTEGRAVIR"],
    "TEE":    ["TEE", "Tenofovir/Emtricitabine/Efavirenz", "TDF/FTC/EFV", "tee fdc"],
    "AZT3TC": ["AZT/3TC", "Zidovudine/Lamivudine 300/150", "zidovudine + lamivudine"],
    "LPVR":   ["LPV/r", "Lopinavir/Ritonavir 200/50mg", "LPV/RTV", "lopinavir/ritonavir"],
    "ABC3TC": ["ABC/3TC 120/60", "Abacavir/Lamivudine dispersible", "abc/3tc"],
    "DTG10":  ["DTG 10mg", "Dolutegravir 10 mg dispersible", "dtg10"],
    "AMLO":   ["Amlodipine 5mg", "AMLODIPINE 5 MG", "amlodipine", "Amlodipin 5mg"],
    "HCTZ":   ["HCTZ 12.5mg", "Hydrochlorothiazide 12.5 mg", "hydrochlorothiazide", "HCT 12.5"],
    "ENAL":   ["Enalapril 10mg", "ENALAPRIL 10 MG", "enalapril", "Enalapril10"],
    "METF":   ["Metformin 500mg", "METFORMIN 500 MG", "metformin tabs", "Metformine 500", "MTF 500"],
    "GLIC":   ["Gliclazide 80mg", "GLICLAZIDE 80 MG", "gliclazide", "Gliclazid 80"],
    "RHZE":   ["RHZE", "Rifampicin/Isoniazid/Pyrazinamide/Ethambutol", "4FDC", "rhze intensive phase"],
    "RH":     ["RH", "Rifampicin/Isoniazid 150/75", "2FDC", "rh continuation"],
}


def build_extensions(curated: dict, seed: int) -> dict:
    rng = np.random.default_rng(seed + 11)
    enc, cond, pat, fac = (curated[k] for k in ("encounters", "conditions", "patients", "facilities"))

    # ---------------- dispensing ----------------
    hiv = cond[(cond["condition"] == "HIV") & cond["regimen"].notna()].set_index("patient_id")
    tb = cond[cond["condition"] == "Tuberculosis"].set_index("patient_id")
    patients_htn = cond.loc[cond["condition"] == "Hypertension", "patient_id"].unique()
    patients_dm = cond.loc[cond["condition"] == "Type 2 diabetes", "patient_id"].unique()
    htn_choice = dict(zip(patients_htn, rng.choice(["AMLO", "HCTZ", "ENAL"], size=len(patients_htn), p=[0.6, 0.25, 0.15])))
    dm_glic = dict(zip(patients_dm, rng.random(len(patients_dm)) < 0.3))
    ccmdd = dict(zip(pat["patient_id"], rng.random(len(pat)) < 0.35))

    rows = []
    did = 0
    chronic = enc[enc["visit_type"].isin(["Chronic", "TB"])]
    for e in chronic.itertuples(index=False):
        codes = {e.icd10_primary} | (set(e.icd10_secondary.split(";")) if isinstance(e.icd10_secondary, str) else set())
        lines = []
        if e.visit_type == "TB" and e.patient_id in tb.index:
            onset = tb.loc[e.patient_id, "onset_date"]
            onset = onset.iloc[0] if isinstance(onset, pd.Series) else onset
            intensive = (e.encounter_date - onset).days < 56
            lines.append(("RHZE" if intensive else "RH", 14 if (e.encounter_date - onset).days < 60 else 30))
        else:
            if "B24" in codes and e.patient_id in hiv.index:
                h = hiv.loc[e.patient_id]
                h = h.iloc[0] if isinstance(h, pd.DataFrame) else h
                if pd.notna(h["art_start_date"]) and h["art_start_date"] <= e.encounter_date:
                    lines += [(k, 56) for k in REGIMEN_LINES[h["regimen"]]]
            if "I10" in codes and e.patient_id in htn_choice:
                lines.append((htn_choice[e.patient_id], 56))
            if "E11.9" in codes:
                lines.append(("METF", 56))
                if dm_glic.get(e.patient_id):
                    lines.append(("GLIC", 56))
        stable = e.visit_type == "Chronic" and ccmdd[e.patient_id]
        for key, days in lines:
            did += 1
            name, strength, atc, per_day = MEDICINES[key]
            rows.append({
                "dispense_id": f"ILN-D-{did:07d}", "encounter_id": e.encounter_id, "patient_id": e.patient_id,
                "facility_id": e.facility_id, "dispense_date": e.encounter_date,
                "medicine_key": key, "medicine_name": name, "strength": strength, "atc_code": atc,
                "days_supply": days, "quantity": days * per_day,
                "channel": "CCMDD pick-up point" if stable else "Facility pharmacy",
            })
    dispensing = pd.DataFrame(rows)

    # ---------------- referrals ----------------
    ftype = dict(zip(fac["facility_id"], fac["facility_type"]))
    fsub = dict(zip(fac["facility_id"], fac["subdistrict"]))
    district_hosp = {"Mfula": "ILN-DH01", "Ntaba": "ILN-DH02", "Lwandle": "ILN-RH01"}
    ref_rows, rid = [], 0
    candidates = enc[enc["visit_type"].isin(["Acute", "Chronic", "Antenatal"])]
    roll = rng.random(len(candidates))
    for r, e in zip(roll, candidates.itertuples(index=False)):
        t = ftype[e.facility_id]
        if t in ("Clinic", "CHC", "Mobile Clinic") and r < 0.025:
            to = district_hosp[fsub[e.facility_id]]
        elif t == "District Hospital" and r < 0.08:
            to = "ILN-RH01"
        else:
            continue
        rid += 1
        p_arrive = 0.7 if fsub[e.facility_id] == "Ntaba" else 0.82
        ref_rows.append({
            "referral_id": f"ILN-R-{rid:06d}", "patient_id": e.patient_id, "encounter_id": e.encounter_id,
            "from_facility_id": e.facility_id, "to_facility_id": to, "referral_date": e.encounter_date,
            "reason_icd10": e.icd10_primary,
            "urgency": "Urgent" if rng.random() < 0.3 else "Routine",
            "outcome": "Seen" if rng.random() < p_arrive else "Did not arrive",
        })
    # rifampicin-resistant TB is always referred to the regional DR-TB unit
    labs = curated["lab_results"]
    rr = labs[labs["result_text"] == "MTB detected; Rif resistance detected"]
    for l in rr.itertuples(index=False):
        rid += 1
        ref_rows.append({
            "referral_id": f"ILN-R-{rid:06d}", "patient_id": l.patient_id, "encounter_id": l.encounter_id,
            "from_facility_id": l.ordering_facility_id, "to_facility_id": "ILN-RH01",
            "referral_date": l.reported_at.normalize(), "reason_icd10": "A15.0", "urgency": "Urgent",
            "outcome": "Seen",
        })
    referrals = pd.DataFrame(ref_rows)
    return {"dispensing": dispensing, "referrals": referrals}


def messy_dispensing(dispensing: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Raw-layer dispensing: free-text medicine names, no ATC codes."""
    rng = np.random.default_rng(seed + 12)
    raw = dispensing.drop(columns=["medicine_key", "medicine_name", "strength", "atc_code"]).copy()
    raw.insert(4, "medicine_text", [MESSY_NAMES[k][int(rng.integers(len(MESSY_NAMES[k])))]
                                    for k in dispensing["medicine_key"]])
    return raw

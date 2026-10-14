"""
Dataset v1.2 extensions (Phase 3 - Analytics).

New tables only. Each uses its own random generator, so every v1.0 and v1.1 table is unchanged.

    wards                 ward centroids, registered patients and estimated population (access & denominators)
    dhis_monthly          facility monthly aggregate submissions, as REPORTED (tally errors, missing and late reports)
    weekly_surveillance   weekly syndromic surveillance returns 2023-2025, with one planted outbreak
    specimen_rejections   specimens the lab rejected before testing (never appear in lab_results)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .generator import SUBDISTRICTS

PHC_TYPES = ("Clinic", "CHC", "Mobile Clinic")
DATA_ELEMENTS = ["PHC headcount total", "PHC headcount under 5 years", "Viral load test done", "Antenatal 1st visit"]
SLA_HOURS = {"VL": 120, "CD4": 48, "HBA1C": 72, "CREAT": 24, "HB": 24, "XPERT": 48}   # fictional district SLA, lab-controlled TAT
OUTBREAK = {"facility_id": "ILN-CL06", "weeks": ["2025-W06", "2025-W07", "2025-W08", "2025-W09"], "syndrome": "Diarrhoea under 5"}


def _wards(curated, rng) -> pd.DataFrame:
    fac = curated["facilities"]
    pat = curated["patients"]
    spread = {"Lwandle": 0.035, "Mfula": 0.06, "Ntaba": 0.11}   # degrees; ~0.01 deg = 1.1 km
    coverage = {"Lwandle": (0.80, 0.92), "Mfula": (0.70, 0.88), "Ntaba": (0.55, 0.78)}
    rows = []
    for sd, cfg in SUBDISTRICTS.items():
        f = fac[(fac["subdistrict"] == sd) & fac["facility_type"].isin(PHC_TYPES)]
        clat, clon = f["latitude"].mean(), f["longitude"].mean()
        for w in cfg["wards"]:
            registered = int((pat["ward"] == w).sum())
            cov = rng.uniform(*coverage[sd])
            rows.append({"ward": w, "subdistrict": sd,
                         "latitude": round(clat + rng.normal(0, spread[sd]), 4),
                         "longitude": round(clon + rng.normal(0, spread[sd]), 4),
                         "registered_patients": registered,
                         "estimated_population": int(round(registered / cov, -1))})
    return pd.DataFrame(rows)


def _dhis_monthly(curated, rng) -> pd.DataFrame:
    fac, enc, pat, labs, cond = (curated[k] for k in ("facilities", "encounters", "patients", "lab_results", "conditions"))
    phc = fac[fac["facility_type"].isin(PHC_TYPES)]
    e = enc[enc["facility_id"].isin(phc["facility_id"])].copy()
    e["period"] = e["encounter_date"].dt.strftime("%Y-%m")
    dob = pat.set_index("patient_id")["date_of_birth"]
    e["age"] = ((e["encounter_date"] - e["patient_id"].map(dob)).dt.days // 365.25)

    anc_first = (e[e["visit_type"] == "Antenatal"].sort_values("encounter_date")
                 .groupby("patient_id").head(1))
    vl = labs[(labs["test_code"] == "VL") & labs["ordering_facility_id"].isin(phc["facility_id"])].copy()
    vl["period"] = vl["collected_at"].dt.strftime("%Y-%m")

    true = pd.concat([
        e.groupby(["facility_id", "period"]).size().rename("PHC headcount total"),
        e[e["age"] < 5].groupby(["facility_id", "period"]).size().rename("PHC headcount under 5 years"),
        vl.groupby(["ordering_facility_id", "period"]).size().rename_axis(["facility_id", "period"]).rename("Viral load test done"),
        anc_first.groupby(["facility_id", "period"]).size().rename("Antenatal 1st visit"),
    ], axis=1)
    periods = pd.period_range("2024-01", "2025-12", freq="M").strftime("%Y-%m")
    grid = pd.MultiIndex.from_product([phc["facility_id"], periods], names=["facility_id", "period"])
    true = true.reindex(grid).fillna(0).astype(int)

    golive = dict(zip(fac["facility_id"], fac["emr_go_live"]))
    fsub = dict(zip(fac["facility_id"], fac["subdistrict"]))
    rows = []
    for (fid, per), vals in true.iterrows():
        period_start = pd.Timestamp(per + "-01")
        digital = pd.notna(golive[fid]) and period_start >= golive[fid]
        p_missing = 0.0 if digital else (0.10 if fsub[fid] == "Ntaba" else 0.04)
        if rng.random() < p_missing:
            continue                                     # report never submitted
        due = (period_start + pd.offsets.MonthBegin(1)) + pd.Timedelta(days=9)   # due by the 10th of next month
        if digital:
            submitted = due - pd.Timedelta(days=int(rng.integers(3, 8)))
        else:
            late = rng.random() < (0.30 if fsub[fid] == "Ntaba" else 0.15)
            submitted = due + pd.Timedelta(days=int(rng.integers(1, 25))) if late else due - pd.Timedelta(days=int(rng.integers(0, 8)))
        for de in DATA_ELEMENTS:
            v = int(vals[de])
            if not digital and v > 0:
                v = max(0, int(round(v * (1 + rng.normal(0, 0.05)))))          # tally errors
                if v >= 100 and rng.random() < 0.02:                            # transposition, e.g. 1204 -> 1024
                    s = list(str(v)); i = int(rng.integers(0, len(s) - 1)); s[i], s[i + 1] = s[i + 1], s[i]
                    v = int("".join(s))
            rows.append({"facility_id": fid, "period": per, "data_element": de, "reported_value": v,
                         "submitted_date": submitted.normalize(), "source": "e-Impilo (automatic)" if digital else "Paper tally"})
    return pd.DataFrame(rows)


def _weekly_surveillance(curated, rng) -> pd.DataFrame:
    fac = curated["facilities"]
    phc = fac[fac["facility_type"].isin(PHC_TYPES)]
    weeks = pd.date_range("2023-01-02", "2025-12-29", freq="W-MON")       # ISO week Mondays
    iso = weeks.isocalendar()
    labels = [f"{y}-W{w:02d}" for y, w in zip(iso["year"], iso["week"])]
    doy = weeks.dayofyear.values
    rows = []
    for f in phc.itertuples():
        size = {"CHC": 2.0, "Clinic": 1.0, "Mobile Clinic": 0.4}[f.facility_type]
        for syndrome, base, peak_day, amp in (("Diarrhoea under 5", 5.0, 30, 0.45), ("Influenza-like illness", 7.0, 200, 0.6)):
            season = 1 + amp * np.cos(2 * np.pi * (doy - peak_day) / 365)    # summer diarrhoea, winter ILI
            lam = base * size * season
            counts = rng.poisson(lam)
            for lab, wk, c in zip(labels, weeks, counts):
                if syndrome == OUTBREAK["syndrome"] and f.facility_id == OUTBREAK["facility_id"] and lab in OUTBREAK["weeks"]:
                    c = int(c + rng.poisson(lam[0] * 2.0))
                rows.append({"facility_id": f.facility_id, "iso_week": lab, "week_start": wk, "syndrome": syndrome,
                             "cases": int(c)})
    return pd.DataFrame(rows)


def _specimen_rejections(curated, rng) -> pd.DataFrame:
    labs = curated["lab_results"]
    fsub = dict(zip(curated["facilities"]["facility_id"], curated["facilities"]["subdistrict"]))
    reasons = ["Haemolysed", "Insufficient volume", "Unlabelled or mislabelled", "Wrong tube type",
               "Leaking container", "Exceeded stability time"]
    base_p = {"Lwandle": 0.02, "Mfula": 0.03, "Ntaba": 0.055}
    rows, n = [], 0
    sample = labs[labs["test_code"] != "XPERT"]
    for r in sample.itertuples():
        sd = fsub[r.ordering_facility_id]
        if rng.random() >= base_p[sd]:
            continue
        w = np.array([0.25, 0.2, 0.15, 0.1, 0.05, 0.25 if sd == "Ntaba" else 0.08])
        n += 1
        transit = rng.uniform(*SUBDISTRICTS[sd]["transport"])
        rows.append({"rejection_id": f"ILN-REJ-{n:05d}", "patient_id": r.patient_id,
                     "ordering_facility_id": r.ordering_facility_id, "test_code": r.test_code,
                     "collected_at": r.collected_at - pd.Timedelta(days=int(rng.integers(3, 20))),
                     "received_at": None, "reason": reasons[int(rng.choice(6, p=w / w.sum()))]})
        rows[-1]["received_at"] = (rows[-1]["collected_at"] + pd.Timedelta(hours=float(transit))).floor("min")
    return pd.DataFrame(rows)


def build_v12(curated: dict, seed: int) -> dict:
    return {
        "wards": _wards(curated, np.random.default_rng(seed + 21)),
        "dhis_monthly": _dhis_monthly(curated, np.random.default_rng(seed + 22)),
        "weekly_surveillance": _weekly_surveillance(curated, np.random.default_rng(seed + 23)),
        "specimen_rejections": _specimen_rejections(curated, np.random.default_rng(seed + 24)),
    }

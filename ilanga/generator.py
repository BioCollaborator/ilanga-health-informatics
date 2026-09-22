"""
Ilanga District synthetic data generator  (dataset v1.0 - Phase 1 & 2 tables)

Ilanga District is FICTIONAL. Its facilities, people and results are generated
from the parameters below. Parameters are *illustrative* - chosen to feel like a
KwaZulu-Natal district (young population, high HIV burden, rising NCDs, uneven
digitisation) - they are NOT official statistics and must never be quoted as such.

Two layers are produced, like a real data platform:
    curated : cleaned, conformed, analysis-ready  (Modules 1-4 use this)
    raw     : as extracted from source systems, with realistic defects
              (duplicates, invalid IDs, messy lab text, bad dates) - Module 5 onward
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import sa_id

DATASET_VERSION = "1.0.0"
DEFAULT_SEED = 2026
PERIOD_START = pd.Timestamp("2024-01-01")
PERIOD_END = pd.Timestamp("2025-12-31")
REFERENCE_DATE = PERIOD_END

# --------------------------------------------------------------------------------------
# Geography & facilities
# --------------------------------------------------------------------------------------
SUBDISTRICTS = {
    #  name       share of population, setting,       wards,          transport hours to lab (min, max)
    "Lwandle": dict(weight=0.42, setting="Urban coastal", wards=range(19, 31), transport=(2, 12)),
    "Mfula":   dict(weight=0.33, setting="Peri-urban",    wards=range(1, 11),  transport=(4, 24)),
    "Ntaba":   dict(weight=0.25, setting="Rural inland",  wards=range(11, 19), transport=(10, 60)),
}

FACILITIES = [
    # id,          name,                         type,                subdistrict, lat,     lon,     EMR go-live (None = paper)
    ("ILN-RH01",  "Ilanga Regional Hospital",    "Regional Hospital", "Lwandle", -29.401, 31.262, "2025-02-01"),
    ("ILN-DH01",  "Mfula District Hospital",     "District Hospital", "Mfula",   -29.312, 31.021, "2025-06-01"),
    ("ILN-DH02",  "Ntaba District Hospital",     "District Hospital", "Ntaba",   -29.188, 30.742, None),
    ("ILN-CHC01", "Lwandle Community Health Centre", "CHC",           "Lwandle", -29.436, 31.301, "2024-09-01"),
    ("ILN-CHC02", "Ntaba Community Health Centre",   "CHC",           "Ntaba",   -29.231, 30.815, None),
    ("ILN-CL01",  "Mfula Gateway Clinic",        "Clinic",            "Mfula",   -29.305, 31.035, "2024-11-01"),
    ("ILN-CL02",  "Emthonjeni Clinic",           "Clinic",            "Mfula",   -29.351, 30.978, None),
    ("ILN-CL03",  "Ezimbali Clinic",             "Clinic",            "Lwandle", -29.382, 31.244, "2025-03-01"),
    ("ILN-CL04",  "Lwandle Beach Clinic",        "Clinic",            "Lwandle", -29.458, 31.322, "2024-07-01"),
    ("ILN-CL05",  "Ithemba Clinic",              "Clinic",            "Lwandle", -29.412, 31.198, None),
    ("ILN-CL06",  "KwaNtaba Clinic",             "Clinic",            "Ntaba",   -29.152, 30.701, None),
    ("ILN-CL07",  "Umthombo Clinic",             "Clinic",            "Ntaba",   -29.268, 30.866, "2025-08-01"),
    ("ILN-MOB01", "Ntaba Mobile Clinic",         "Mobile Clinic",     "Ntaba",   -29.205, 30.780, None),
    ("ILN-LAB01", "NHLS Ilanga Laboratory",      "Laboratory",        "Lwandle", -29.398, 31.255, None),
]

# --------------------------------------------------------------------------------------
# People (name pools are generic and common; no real individuals are intended)
# --------------------------------------------------------------------------------------
NAMES = {
    "nguni": {
        "F": ["Nomvula", "Thandeka", "Zanele", "Nokuthula", "Lindiwe", "Ntombi", "Sibongile",
              "Nompumelelo", "Zodwa", "Nosipho", "Busisiwe", "Hlengiwe", "Lungile", "Mbali",
              "Nandi", "Philisiwe", "Sindisiwe", "Slindile", "Thobeka", "Khanyisile", "Minenhle",
              "Snenhlanhla", "Ayanda", "Nontobeko", "Zinhle", "Samkelisiwe"],
        "M": ["Sipho", "Bongani", "Mandla", "Sibusiso", "Themba", "Lwazi", "Musa", "Nkosinathi",
              "Sizwe", "Siyabonga", "Mthokozisi", "Sandile", "Mlungisi", "Bheki", "Njabulo",
              "Lindani", "Xolani", "Thulani", "Vusi", "Zakhele", "Kwanele", "Nhlanhla", "Mfundo",
              "Andile", "Sanele", "Lungelo"],
        "surname": ["Dlamini", "Ngcobo", "Zulu", "Mkhize", "Khumalo", "Nxumalo", "Mthembu",
                    "Ndlovu", "Shezi", "Buthelezi", "Cele", "Majola", "Mhlongo", "Ntuli", "Zungu",
                    "Mbatha", "Hlongwane", "Sithole", "Mngadi", "Mnguni", "Ngubane", "Xulu",
                    "Msomi", "Maphumulo", "Chiliza", "Ngema", "Mchunu", "Khoza", "Biyela", "Nene"],
        "languages": (["isiZulu", "isiXhosa", "English"], [0.94, 0.04, 0.02]),
    },
    "indian_sa": {
        "F": ["Priya", "Kavitha", "Shanti", "Anusha", "Reshma", "Nirasha", "Kerusha", "Thashni"],
        "M": ["Rajesh", "Pravin", "Kumaran", "Deshen", "Kribashen", "Vishal", "Nishan", "Yuvan"],
        "surname": ["Naidoo", "Pillay", "Govender", "Moodley", "Reddy", "Chetty", "Singh", "Padayachee"],
        "languages": (["English", "isiZulu"], [0.95, 0.05]),
    },
    "anglo_afrikaans": {
        "F": ["Sarah", "Michelle", "Chantelle", "Anna", "Nicole", "Megan", "Lize", "Carmen"],
        "M": ["John", "Pieter", "Craig", "Jason", "Ruan", "Grant", "Wayne", "Keegan"],
        "surname": ["van der Merwe", "Botha", "Smith", "Williams", "Jacobs", "Pretorius", "Adams", "Nel"],
        "languages": (["English", "Afrikaans"], [0.7, 0.3]),
    },
}
NAME_GROUP_WEIGHTS = {"nguni": 0.82, "indian_sa": 0.10, "anglo_afrikaans": 0.08}

# Age structure: (min_age, max_age_exclusive, weight) - young population pyramid
AGE_BANDS = [
    (0, 5, 10.0), (5, 10, 9.8), (10, 15, 9.4), (15, 20, 8.6), (20, 25, 8.7), (25, 30, 9.0),
    (30, 35, 8.8), (35, 40, 7.8), (40, 45, 6.4), (45, 50, 5.4), (50, 55, 4.5), (55, 60, 3.8),
    (60, 65, 2.9), (65, 70, 2.1), (70, 75, 1.5), (75, 80, 1.0), (80, 96, 0.9),
]
P_FEMALE = 0.53  # clinic-registered populations skew female

# Illustrative condition probabilities (point prevalence by 31 Dec 2025)
HIV_PREV = {  # (age_lo, age_hi): (female, male)
    (0, 15): (0.02, 0.02), (15, 25): (0.12, 0.05), (25, 35): (0.30, 0.15),
    (35, 50): (0.35, 0.28), (50, 200): (0.18, 0.15),
}
HTN_PREV = {(0, 15): 0.0, (15, 35): 0.06, (35, 50): 0.20, (50, 65): 0.42, (65, 200): 0.58}
DM_PREV = {(0, 15): 0.0, (15, 35): 0.02, (35, 50): 0.08, (50, 65): 0.16, (65, 200): 0.20}
TB_INCIDENCE_2Y = 0.009          # per person over the 2-year period (x4 if living with HIV)
PREGNANCY_2Y = 0.14              # women 15-44, over the 2-year period
ART_COVERAGE = 0.90              # of diagnosed HIV
VL_SUPPRESSED_LT1000 = 0.88      # of those active on ART

ICD10 = {
    "HIV": "B24", "Hypertension": "I10", "Type 2 diabetes": "E11.9",
    "Tuberculosis": "A15.0", "Pregnancy": "Z34.9", "Child health": "Z00.1",
}
ACUTE_CODES = [  # (ICD-10, label, weight)
    ("J06.9", "Acute upper respiratory infection", 24), ("A09", "Gastroenteritis/diarrhoea", 10),
    ("M54.5", "Low back pain", 9), ("N39.0", "Urinary tract infection", 8),
    ("L30.9", "Dermatitis", 7), ("R51", "Headache", 7), ("K29.7", "Gastritis", 5),
    ("H10.9", "Conjunctivitis", 5), ("Z30.9", "Contraceptive management", 12),
    ("Z00.0", "General adult examination", 8), ("T14.1", "Open wound", 5),
]

LAB_TESTS = {  # key: (display name, LOINC, unit)
    "VL":   ("HIV-1 viral load", "20447-9", "copies/mL"),
    "CD4":  ("CD4 count", "24467-3", "cells/uL"),
    "HBA1C": ("HbA1c", "4548-4", "%"),
    "CREAT": ("Creatinine", "14682-9", "umol/L"),
    "HB":   ("Haemoglobin", "718-7", "g/dL"),
    "XPERT": ("Xpert MTB/RIF Ultra", None, None),  # LOINC deliberately left for Module 6
}
LAB_PROCESSING_HOURS = {"VL": (24, 120), "CD4": (6, 24), "HBA1C": (6, 48), "CREAT": (4, 24),
                        "HB": (2, 12), "XPERT": (2, 24)}


# --------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------
def _band_lookup(table: dict, age: float):
    for (lo, hi), v in table.items():
        if lo <= age < hi:
            return v
    raise ValueError(age)


def _rand_date(rng, start: pd.Timestamp, end: pd.Timestamp) -> pd.Timestamp:
    if end <= start:
        return start
    return start + pd.Timedelta(days=int(rng.integers(0, (end - start).days + 1)))


def _facilities_df() -> pd.DataFrame:
    df = pd.DataFrame(FACILITIES, columns=["facility_id", "facility_name", "facility_type",
                                           "subdistrict", "latitude", "longitude", "emr_go_live"])
    df["emr_go_live"] = pd.to_datetime(df["emr_go_live"])
    df["emr_system"] = np.where(df["emr_go_live"].notna(), "e-Impilo", "Paper + legacy registers")
    df.loc[df["facility_type"] == "Laboratory", "emr_system"] = "NHLS LIS"
    df["setting"] = df["subdistrict"].map({k: v["setting"] for k, v in SUBDISTRICTS.items()})
    return df


# --------------------------------------------------------------------------------------
# main build
# --------------------------------------------------------------------------------------
def build_curated(seed: int = DEFAULT_SEED, n_patients: int = 20_000) -> dict:
    rng = np.random.default_rng(seed)
    fac = _facilities_df()
    service_points = fac[fac["facility_type"].isin(["Clinic", "CHC", "Mobile Clinic"])]
    hospitals = fac[fac["facility_type"].str.contains("Hospital")]
    sp_by_subd = {s: service_points.loc[service_points["subdistrict"] == s, "facility_id"].tolist() for s in SUBDISTRICTS}
    hospital_ids = hospitals["facility_id"].tolist()
    ftype = dict(zip(fac["facility_id"], fac["facility_type"]))
    fsubd = dict(zip(fac["facility_id"], fac["subdistrict"]))
    fgolive = dict(zip(fac["facility_id"], fac["emr_go_live"]))

    # ---------------- patients ----------------
    bands = np.array([b[2] for b in AGE_BANDS]); bands = bands / bands.sum()
    band_idx = rng.choice(len(AGE_BANDS), size=n_patients, p=bands)
    ages = np.array([rng.uniform(AGE_BANDS[i][0], AGE_BANDS[i][1]) for i in band_idx])
    dob = REFERENCE_DATE - pd.to_timedelta((ages * 365.25).astype(int), unit="D")
    sex = np.where(rng.random(n_patients) < P_FEMALE, "F", "M")
    groups = rng.choice(list(NAME_GROUP_WEIGHTS), size=n_patients, p=list(NAME_GROUP_WEIGHTS.values()))
    subd = rng.choice(list(SUBDISTRICTS), size=n_patients, p=[v["weight"] for v in SUBDISTRICTS.values()])

    first, last, lang, ward, home_fac = [], [], [], [], []
    for i in range(n_patients):
        g = NAMES[groups[i]]
        first.append(rng.choice(g[sex[i]]))
        last.append(rng.choice(g["surname"]))
        langs, lp = g["languages"]
        lang.append(rng.choice(langs, p=lp))
        ward.append(int(rng.choice(list(SUBDISTRICTS[subd[i]]["wards"]))))
        opts = sp_by_subd[subd[i]]
        home_fac.append(opts[int(rng.integers(len(opts)))])

    id_roll = rng.random(n_patients)
    id_type = np.where(id_roll < 0.88, "SA_ID", np.where(id_roll < 0.92, "PASSPORT", "NONE"))
    id_type = np.where((ages < 5) & (rng.random(n_patients) < 0.5), "NONE", id_type)  # many under-5s lack ID on file
    sa_ids, passports = [], []
    for i in range(n_patients):
        if id_type[i] == "SA_ID":
            sa_ids.append(sa_id.make_sa_id(dob[i].date(), sex[i], int(rng.integers(0, 5000)),
                                           citizen=rng.random() < 0.97))
            passports.append(None)
        elif id_type[i] == "PASSPORT":
            sa_ids.append(None)
            passports.append("SYN" + "".join(str(d) for d in rng.integers(0, 10, 7)))
        else:
            sa_ids.append(None); passports.append(None)

    # 099 prefix used deliberately so numbers are not in normal SA mobile ranges
    phone = [f"099 {rng.integers(100, 999)} {rng.integers(1000, 9999)}" if rng.random() < 0.72 else None
             for _ in range(n_patients)]
    reg_start = pd.Timestamp("2012-01-01")
    reg_date = [max(_rand_date(rng, reg_start, pd.Timestamp("2025-10-31")), dob[i] + pd.Timedelta(days=3))
                for i in range(n_patients)]
    reg_date = [min(d, pd.Timestamp("2025-12-15")) for d in reg_date]

    patients = pd.DataFrame({
        "patient_id": [f"ILN-P-{i:06d}" for i in range(1, n_patients + 1)],
        "first_name": first, "surname": last, "sex": sex,
        "date_of_birth": pd.to_datetime(dob).normalize(),
        "id_type": id_type, "sa_id_number": sa_ids, "passport_number": passports,
        "phone": phone, "home_language": lang,
        "subdistrict": subd, "ward": ward,
        "address": [f"House {rng.integers(1, 3000)}, Ward {w}" for w in ward],
        "home_facility_id": home_fac,
        "has_medical_aid": rng.random(n_patients) < 0.12,
        "registration_date": pd.to_datetime(reg_date),
    })

    pid_arr = patients["patient_id"].tolist()
    home_arr = patients["home_facility_id"].tolist()
    reg_arr = patients["registration_date"].tolist()

    # ---------------- conditions ----------------
    cond_rows = []
    cid = 0

    def add(**kw):
        nonlocal cid
        cid += 1
        kw["condition_id"] = f"ILN-C-{cid:06d}"
        cond_rows.append(kw)

    per_patient = {}  # patient index -> list of condition dicts (for encounters/labs)
    for i in range(n_patients):
        a, s, pid = ages[i], sex[i], pid_arr[i]
        dob_i = dob[i]
        conds = []
        f_p, m_p = _band_lookup(HIV_PREV, a)
        if rng.random() < (f_p if s == "F" else m_p):
            earliest = dob_i + pd.Timedelta(days=30) if a < 15 else max(dob_i + pd.Timedelta(days=int(15 * 365.25)), pd.Timestamp("2004-01-01"))
            onset = _rand_date(rng, earliest, pd.Timestamp("2025-09-30"))
            on_art = rng.random() < ART_COVERAGE
            art_start = onset + pd.Timedelta(days=int(rng.integers(0, 45 if onset.year >= 2016 else 900))) if on_art else pd.NaT
            if on_art and art_start > PERIOD_END:
                art_start = PERIOD_END - pd.Timedelta(days=5)
            r = rng.random()
            status, sdate = "Active", pd.NaT
            if not on_art:
                status = "Not on ART"
            elif r < 0.10:
                status, sdate = "Lost to follow-up", _rand_date(rng, max(PERIOD_START, art_start), PERIOD_END - pd.Timedelta(days=90))
            elif r < 0.13:
                status, sdate = "Transferred out", _rand_date(rng, max(PERIOD_START, art_start), PERIOD_END)
            elif r < 0.14:
                status, sdate = "Died", _rand_date(rng, max(PERIOD_START, art_start), PERIOD_END)
            regimen = None
            if on_art:
                regimen = "ABC/3TC/DTG" if a < 10 else rng.choice(["TLD", "TLD", "TLD", "TLD", "TLD", "TLD", "TEE", "AZT/3TC/LPV/r"])
            d = dict(patient_id=pid, condition="HIV", icd10_code=ICD10["HIV"], onset_date=onset,
                     status=status, status_date=sdate, art_start_date=art_start, regimen=regimen)
            add(**d); conds.append(d)
        for name, table in (("Hypertension", HTN_PREV), ("Type 2 diabetes", DM_PREV)):
            if rng.random() < _band_lookup(table, a):
                onset = _rand_date(rng, max(dob_i + pd.Timedelta(days=int(18 * 365.25)), pd.Timestamp("2005-01-01")),
                                   pd.Timestamp("2025-10-31"))
                d = dict(patient_id=pid, condition=name, icd10_code=ICD10[name], onset_date=onset,
                         status="Active", status_date=pd.NaT, art_start_date=pd.NaT, regimen=None)
                add(**d); conds.append(d)
        has_hiv = any(c["condition"] == "HIV" for c in conds)
        if a >= 1 and rng.random() < TB_INCIDENCE_2Y * (4 if has_hiv else 1):
            onset = _rand_date(rng, PERIOD_START, PERIOD_END - pd.Timedelta(days=14))
            if onset > PERIOD_END - pd.Timedelta(days=180):
                outcome = "On treatment"
            else:
                outcome = rng.choice(["Cured", "Treatment completed", "Lost to follow-up", "Died", "Treatment failed"],
                                     p=[0.52, 0.26, 0.12, 0.07, 0.03])
            sdate = pd.NaT if outcome == "On treatment" else onset + pd.Timedelta(days=int(rng.integers(150, 200)))
            d = dict(patient_id=pid, condition="Tuberculosis", icd10_code=ICD10["Tuberculosis"], onset_date=onset,
                     status=outcome, status_date=sdate, art_start_date=pd.NaT, regimen="RHZE" )
            add(**d); conds.append(d)
        if s == "F" and 15 <= a < 45 and rng.random() < PREGNANCY_2Y:
            onset = _rand_date(rng, PERIOD_START, PERIOD_END - pd.Timedelta(days=30))
            d = dict(patient_id=pid, condition="Pregnancy", icd10_code=ICD10["Pregnancy"], onset_date=onset,
                     status="Delivered" if onset < PERIOD_END - pd.Timedelta(days=200) else "Antenatal",
                     status_date=pd.NaT, art_start_date=pd.NaT, regimen=None)
            add(**d); conds.append(d)
        per_patient[i] = conds

    conditions = pd.DataFrame(cond_rows)[["condition_id", "patient_id", "condition", "icd10_code", "onset_date",
                                          "status", "status_date", "art_start_date", "regimen"]]

    # ---------------- encounters + labs ----------------
    enc, labs = [], []
    acute_codes = [c[0] for c in ACUTE_CODES]
    acute_w = np.array([c[2] for c in ACUTE_CODES], float); acute_cum = np.cumsum(acute_w / acute_w.sum())
    eid = lid = 0

    def visit_facility(i):
        r = rng.random()
        if r < 0.86:
            return home_arr[i]
        if r < 0.95:
            same = sp_by_subd[subd[i]]
            return same[int(rng.integers(len(same)))]
        return hospital_ids[int(rng.integers(len(hospital_ids)))]

    def cadre_for(fid):
        r = rng.random()
        if "Hospital" in ftype[fid]:
            return "Medical Officer" if r < 0.8 else "Professional Nurse"
        if r < 0.74:
            return "Professional Nurse"
        if r < 0.89:
            return "Enrolled Nurse"
        return "Clinical Associate" if r < 0.95 else "Medical Officer"

    def add_enc(i, date, vtype, icd, secondary=None):
        nonlocal eid
        eid += 1
        fid = visit_facility(i)
        golive = fgolive[fid]
        rec = dict(encounter_id=f"ILN-E-{eid:07d}", patient_id=pid_arr[i], facility_id=fid,
                   encounter_date=date, visit_type=vtype, icd10_primary=icd, icd10_secondary=secondary,
                   clinician_cadre=cadre_for(fid),
                   capture_mode="Digital (e-Impilo)" if pd.notna(golive) and date >= golive else "Paper register")
        enc.append(rec)
        return rec

    def add_lab(i, e, key, text, numeric, below_limit=False):
        nonlocal lid
        lid += 1
        name, loinc, unit = LAB_TESTS[key]
        collected = e["encounter_date"] + pd.Timedelta(hours=int(rng.integers(8, 14)), minutes=int(rng.integers(0, 60)))
        tmin, tmax = SUBDISTRICTS[fsubd[e["facility_id"]]]["transport"]
        received = collected + pd.Timedelta(hours=float(rng.uniform(tmin, tmax)))
        pmin, pmax = LAB_PROCESSING_HOURS[key]
        reported = received + pd.Timedelta(hours=float(rng.uniform(pmin, pmax)))
        labs.append(dict(specimen_id=f"ILN{lid:08d}", patient_id=pid_arr[i],
                         encounter_id=e["encounter_id"], ordering_facility_id=e["facility_id"],
                         test_code=key, test_name=name, loinc_code=loinc, result_text=text,
                         result_numeric=numeric, unit=unit, below_detection_limit=below_limit,
                         collected_at=collected, received_at=received, reported_at=reported))

    for i in range(n_patients):
        a = ages[i]
        dob_i = dob[i]
        start = max(PERIOD_START, reg_arr[i])
        conds = per_patient[i]

        # acute visits
        lam = 3.0 if (a < 5 or a >= 65) else 1.8
        for _ in range(rng.poisson(lam)):
            d = _rand_date(rng, start, PERIOD_END)
            add_enc(i, d, "Acute", acute_codes[int(np.searchsorted(acute_cum, rng.random()))])

        # child health (under 5 during period)
        if a < 6:
            d = max(start, dob_i + pd.Timedelta(days=42))
            while d <= PERIOD_END and (d - dob_i).days < 5 * 365:
                if d >= PERIOD_START:
                    add_enc(i, d, "Child health", ICD10["Child health"])
                d += pd.Timedelta(days=int(rng.integers(150, 220)))

        # chronic care
        chronic = [c for c in conds if c["condition"] in ("HIV", "Hypertension", "Type 2 diabetes")
                   and c["status"] != "Not on ART"]
        if chronic:
            priority = {"HIV": 0, "Type 2 diabetes": 1, "Hypertension": 2}
            chronic.sort(key=lambda c: priority[c["condition"]])
            first_date = max(start, min(c["onset_date"] for c in chronic))
            stop = PERIOD_END
            hiv = next((c for c in chronic if c["condition"] == "HIV"), None)
            if hiv is not None and pd.notna(hiv["status_date"]):
                stop = min(stop, hiv["status_date"])
            d = first_date + pd.Timedelta(days=int(rng.integers(0, 40)))
            chronic_encs = []
            while d <= stop:
                active = [c for c in chronic if c["onset_date"] <= d]
                if active:
                    sec = ";".join(c["icd10_code"] for c in active[1:]) or None
                    chronic_encs.append(add_enc(i, d, "Chronic", active[0]["icd10_code"], sec))
                d += pd.Timedelta(days=int(rng.integers(50, 75)))

            # labs on chronic visits
            if hiv is not None and pd.notna(hiv["art_start_date"]) and chronic_encs:
                art = hiv["art_start_date"]
                if art >= PERIOD_START:  # new on ART in period: baseline CD4 at first visit
                    add_lab(i, chronic_encs[0], "CD4", None, None)
                due = [art + pd.Timedelta(days=182)] + [art + pd.Timedelta(days=365 * k) for k in range(1, 30)]
                for dd in due:
                    if PERIOD_START <= dd <= PERIOD_END:
                        e = min(chronic_encs, key=lambda x: abs((x["encounter_date"] - dd).days))
                        if abs((e["encounter_date"] - dd).days) <= 60:
                            add_lab(i, e, "VL", None, None)
            has_dm = any(c["condition"] == "Type 2 diabetes" for c in chronic)
            has_htn = any(c["condition"] == "Hypertension" for c in chronic)
            for k, e in enumerate(chronic_encs):
                if has_dm and k % 3 == 0:
                    add_lab(i, e, "HBA1C", None, None)
                if (has_dm or has_htn) and k % 6 == 1:
                    add_lab(i, e, "CREAT", None, None)

        # TB
        for c in conds:
            if c["condition"] == "Tuberculosis":
                d0 = c["onset_date"]
                e0 = add_enc(i, d0, "TB", ICD10["Tuberculosis"])
                add_lab(i, e0, "XPERT", None, None)
                end = c["status_date"] if pd.notna(c["status_date"]) else PERIOD_END
                d = d0 + pd.Timedelta(days=14)
                while d <= min(end, PERIOD_END):
                    add_enc(i, d, "TB", ICD10["Tuberculosis"])
                    d += pd.Timedelta(days=14 if (d - d0).days < 60 else 30)
            if c["condition"] == "Pregnancy":
                d = c["onset_date"]
                for k in range(int(rng.integers(3, 7))):
                    if d > PERIOD_END:
                        break
                    e = add_enc(i, d, "Antenatal", ICD10["Pregnancy"])
                    if k == 0:
                        add_lab(i, e, "HB", None, None)
                    d += pd.Timedelta(days=int(rng.integers(28, 45)))

        # presumptive TB screening negatives (adults)
        if a >= 15 and rng.random() < 0.02:
            d = _rand_date(rng, start, PERIOD_END)
            e = add_enc(i, d, "Acute", "R05")
            add_lab(i, e, "XPERT", None, None)

    encounters = pd.DataFrame(enc)
    labs_df = pd.DataFrame(labs)

    # ---------------- lab result values (vectorised by test) ----------------
    hiv_status = {c["patient_id"]: c["status"] for rows in per_patient.values() for c in rows if c["condition"] == "HIV"}
    labs_df["result_text"] = labs_df["result_text"].astype(object)
    labs_df["result_numeric"] = np.nan
    labs_df["below_detection_limit"] = False

    def _set(mask, values):
        vals = np.asarray(values)
        labs_df.loc[mask, "result_numeric"] = vals.astype(float)
        labs_df.loc[mask, "result_text"] = [str(v) for v in vals]

    # Viral load: suppression depends on programme status
    vl = labs_df["test_code"] == "VL"
    p_supp = np.where(labs_df.loc[vl, "patient_id"].map(hiv_status).eq("Active"), VL_SUPPRESSED_LT1000, 0.6)
    u1, u2 = rng.random(vl.sum()), rng.random(vl.sum())
    ldl = (u1 < p_supp) & (u2 < 0.82)
    low = (u1 < p_supp) & ~ldl
    vl_idx = labs_df.index[vl]
    labs_df.loc[vl_idx[ldl], ["result_text", "below_detection_limit"]] = ["<50", True]
    _set(vl_idx[low], rng.integers(50, 1000, low.sum()))
    high = ~(ldl | low)
    _set(vl_idx[high], (10 ** rng.uniform(3, 6, high.sum())).astype(int))
    # Other tests
    m = labs_df["test_code"] == "CD4"
    _set(m, np.clip(rng.gamma(2.2, 150, m.sum()), 5, 1600).astype(int))
    m = labs_df["test_code"] == "HBA1C"
    _set(m, np.clip(rng.normal(8.1, 1.8, m.sum()), 4.8, 15.5).round(1))
    m = labs_df["test_code"] == "CREAT"
    _set(m, np.clip(rng.lognormal(np.log(82), 0.28, m.sum()), 35, 900).astype(int))
    m = labs_df["test_code"] == "HB"
    _set(m, np.clip(rng.normal(11.4, 1.5, m.sum()), 6.0, 16.0).round(1))
    labs_df.loc[labs_df["test_code"] == "XPERT", "result_text"] = "MTB not detected"
    # TB patients' diagnostic Xperts are positive
    tb_diag_encs = set(encounters.loc[encounters["visit_type"] == "TB"].groupby("patient_id")["encounter_id"].first())
    mask = (labs_df["test_code"] == "XPERT") & labs_df["encounter_id"].isin(tb_diag_encs)
    labs_df.loc[mask, "result_text"] = np.where(rng.random(mask.sum()) < 0.95,
                                                "MTB detected; Rif resistance not detected",
                                                "MTB detected; Rif resistance detected")
    labs_df["below_detection_limit"] = labs_df["below_detection_limit"].astype(bool)
    labs_df["result_numeric"] = pd.to_numeric(labs_df["result_numeric"], errors="coerce")

    encounters = encounters.sort_values(["encounter_date", "encounter_id"]).reset_index(drop=True)
    for col in ("received_at", "reported_at"):
        labs_df[col] = labs_df[col].dt.floor("min")
    labs_df = labs_df.sort_values("collected_at").reset_index(drop=True)
    return {"facilities": fac, "patients": patients, "conditions": conditions,
            "encounters": encounters, "lab_results": labs_df}


# --------------------------------------------------------------------------------------
# raw layer: inject realistic source-system defects (answer key kept separately)
# --------------------------------------------------------------------------------------
def _typo(rng, name: str) -> str:
    if len(name) < 4:
        return name + "e"
    k = int(rng.integers(0, 4))
    j = int(rng.integers(1, len(name) - 1))
    if k == 0:   # swap adjacent letters
        return name[:j] + name[j + 1] + name[j] + name[j + 2:]
    if k == 1:   # vowel change
        vowels = "aeiou"
        return name[:j] + rng.choice([v for v in vowels if v != name[j].lower()]) + name[j + 1:]
    if k == 2:   # drop a letter
        return name[:j] + name[j + 1:]
    return name.upper()


def build_raw(curated: dict, seed: int = DEFAULT_SEED) -> tuple[dict, pd.DataFrame]:
    rng = np.random.default_rng(seed + 1)
    raw = {k: v.copy() for k, v in curated.items()}
    p = raw["patients"]
    n = len(p)

    # 1) duplicate registrations (~2.5%) with variants
    dup_src = rng.choice(n, size=int(n * 0.025), replace=False)
    dups, key = [], []
    next_id = n + 1
    for i in dup_src:
        r = p.iloc[i].copy()
        orig = r["patient_id"]
        variant = rng.choice(["first_name_typo", "surname_typo", "dob_day_month_swap", "id_missing", "names_swapped"])
        if variant == "first_name_typo":
            r["first_name"] = _typo(rng, r["first_name"])
        elif variant == "surname_typo":
            r["surname"] = _typo(rng, r["surname"])
        elif variant == "dob_day_month_swap" and r["date_of_birth"].day <= 12:
            d = r["date_of_birth"]; r["date_of_birth"] = pd.Timestamp(d.year, d.day, d.month)
        elif variant == "names_swapped":
            r["first_name"], r["surname"] = r["surname"], r["first_name"]
        else:
            variant = "id_missing"
            r["sa_id_number"] = None; r["passport_number"] = None
        r["patient_id"] = f"ILN-P-{next_id:06d}"; next_id += 1
        r["registration_date"] = r["registration_date"] + pd.Timedelta(days=int(rng.integers(30, 900)))
        r["home_facility_id"] = rng.choice(curated["facilities"].query("facility_type in ['Clinic','CHC']")["facility_id"])
        dups.append(r)
        key.append({"original_patient_id": orig, "duplicate_patient_id": r["patient_id"], "variant": variant})
    p = pd.concat([p, pd.DataFrame(dups)], ignore_index=True)

    # 2) invalid SA ID check digits (~0.5% of SA IDs) - transcription errors
    has_id = p.index[p["sa_id_number"].notna()]
    bad = rng.choice(has_id, size=int(len(has_id) * 0.005), replace=False)
    for i in bad:
        s = p.at[i, "sa_id_number"]
        p.at[i, "sa_id_number"] = s[:12] + str((int(s[12]) + int(rng.integers(1, 9))) % 10)
    # 3) inconsistent sex capture and blanks
    flip = rng.choice(n, size=int(n * 0.004), replace=False)
    p.loc[flip, "sex"] = p.loc[flip, "sex"].map({"F": "M", "M": "F"})
    p.loc[rng.choice(n, size=int(n * 0.01), replace=False), "sex"] = rng.choice(["U", "f", "Female", "m"], size=int(n * 0.01))
    p.loc[rng.choice(n, size=int(n * 0.03), replace=False), "home_language"] = None
    raw["patients"] = p

    # 4) encounters: impossible dates
    e = raw["encounters"]
    fut = rng.choice(len(e), size=int(len(e) * 0.002), replace=False)
    e.loc[fut, "encounter_date"] = e.loc[fut, "encounter_date"] + pd.DateOffset(years=1)
    raw["encounters"] = e

    # 5) labs: messy text + reversed timestamps + unit mix-ups
    lab = raw["lab_results"]
    vl_ldl = lab.index[(lab["test_code"] == "VL") & lab["below_detection_limit"]]
    lab.loc[vl_ldl, "result_text"] = rng.choice(["<50", "< 50", "LDL", "TND", "Target not detected", "<50 copies/mL"],
                                                size=len(vl_ldl))
    lab["result_numeric"] = np.nan  # raw layer has no parsed numerics
    lab = lab.drop(columns=["below_detection_limit"])
    cr = lab.index[lab["test_code"] == "CREAT"]
    mg = rng.choice(cr, size=int(len(cr) * 0.04), replace=False)
    lab.loc[mg, "result_text"] = (curated["lab_results"].loc[mg, "result_numeric"] / 88.4).round(2).astype(str)
    lab.loc[mg, "unit"] = "mg/dL"
    rev = rng.choice(len(lab), size=int(len(lab) * 0.01), replace=False)
    lab.loc[rev, "reported_at"] = lab.loc[rev, "received_at"] - pd.Timedelta(hours=3)
    raw["lab_results"] = lab
    return raw, pd.DataFrame(key)

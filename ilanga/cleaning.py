"""
Shared cleaning functions - the team's reviewed versions of the Module 5 techniques.
(In the storyline, your Module 5 code went through code review and was promoted here.)
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from . import sa_id

SEX_MAP = {"f": "F", "female": "F", "m": "M", "male": "M"}
BELOW_LIMIT = re.compile(r"^\s*(<\s*50(\s*copies/ml)?|ldl|tnd|target not detected)\s*$", re.I)


def clean_sex(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower().map(SEX_MAP).fillna("U")


def parse_vl(text):
    """Return (numeric value or NaN, below_detection_limit)."""
    if text is None or (isinstance(text, float) and np.isnan(text)):
        return np.nan, False
    t = str(text).strip()
    if BELOW_LIMIT.match(t):
        return np.nan, True
    try:
        return float(t.replace(",", "")), False
    except ValueError:
        return np.nan, False


def creatinine_umol(value, unit):
    """Convert creatinine to umol/L (1 mg/dL = 88.4 umol/L)."""
    v = pd.to_numeric(value, errors="coerce")
    return np.where(pd.Series(unit).str.lower().eq("mg/dl"), (v * 88.4).round(0), v)


def curate_raw(raw) -> dict:
    """Apply the standard fixes to a raw district. Returns a dict of cleaned DataFrames (not deduplicated)."""
    p = raw.patients.copy()
    p["sex"] = clean_sex(p["sex"])
    p["sa_id_valid"] = p["sa_id_number"].apply(lambda x: sa_id.is_valid(x) if isinstance(x, str) else None)

    e = raw.encounters.copy()
    e["date_valid"] = e["encounter_date"] <= pd.Timestamp("2025-12-31")

    l = raw.lab_results.copy()
    vl = l["test_code"] == "VL"
    parsed = l.loc[vl, "result_text"].apply(parse_vl)
    l["below_detection_limit"] = False
    l.loc[vl, "below_detection_limit"] = [b for _, b in parsed]
    l["result_numeric"] = pd.to_numeric(l["result_text"], errors="coerce")
    l.loc[vl, "result_numeric"] = [v for v, _ in parsed]
    cr = l["test_code"] == "CREAT"
    l.loc[cr, "result_numeric"] = creatinine_umol(l.loc[cr, "result_text"], l.loc[cr, "unit"].values)
    l.loc[cr, "unit"] = "umol/L"
    l["timestamps_valid"] = l["reported_at"] >= l["received_at"]
    return {"facilities": raw.facilities.copy(), "patients": p, "encounters": e, "lab_results": l,
            "conditions": raw.conditions.copy(), "dispensing": raw.dispensing.copy(), "referrals": raw.referrals.copy()}

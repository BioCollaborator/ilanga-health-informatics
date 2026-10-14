"""Shared definitions for Module 14 so everyone predicts the same outcome on the same patients."""
from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split

CUTOFF = pd.Timestamp("2024-10-01")          # the day the model is "run"
HORIZON_DAYS = 365                           # predict LTFU in the following 12 months


def at_risk_cohort(district) -> pd.DataFrame:
    """People on ART at the cutoff (started >= 90 days before, not already out of care), with the outcome label."""
    c = district.conditions
    h = c[(c["condition"] == "HIV") & (c["status"] != "Not on ART") &
          (c["art_start_date"] < CUTOFF - pd.Timedelta(days=90))]
    h = h[~(h["status_date"] < CUTOFF)].copy()
    end = CUTOFF + pd.Timedelta(days=HORIZON_DAYS)
    h["ltfu_next_12m"] = ((h["status"] == "Lost to follow-up") & (h["status_date"] < end)).astype(int)
    return h[["patient_id", "art_start_date", "regimen", "ltfu_next_12m"]].reset_index(drop=True)


def train_test_ids(district, test_size: float = 0.3, seed: int = 2026):
    """The team's fixed patient-level split, so every model is compared on the same test patients."""
    cohort = at_risk_cohort(district)
    tr, te = train_test_split(cohort["patient_id"], test_size=test_size, random_state=seed,
                              stratify=cohort["ltfu_next_12m"])
    return sorted(tr), sorted(te)

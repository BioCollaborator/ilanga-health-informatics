"""
ilanga - the shared data platform for the BioCollaborator Health Informatics Programme.

    import ilanga
    district = ilanga.load_district()          # curated layer (analysis-ready)
    district.patients.head()
    raw = ilanga.load_district(layer="raw")    # source-system extract with real-world defects (Module 5+)

Everything in Ilanga District is synthetic. No real patients, facilities or results.
"""
from __future__ import annotations

import os
import pickle

import pandas as pd

from . import brand, sa_id
from .dictionary import data_dictionary
from .generator import DATASET_VERSION, DEFAULT_SEED, REFERENCE_DATE, build_curated, build_raw

__all__ = ["load_district", "data_dictionary", "hint", "age_years", "age_band", "hello", "sa_id", "brand"]
__version__ = DATASET_VERSION

_MEM: dict = {}
_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "ilanga")


class District:
    """A bundle of tables. Access them as attributes: district.patients, district.encounters, ..."""

    def __init__(self, tables: dict, layer: str, seed: int):
        self._tables = tables
        self.layer, self.seed, self.version = layer, seed, DATASET_VERSION
        for name, df in tables.items():
            setattr(self, name, df)

    def tables(self) -> list:
        return list(self._tables)

    def summary(self) -> pd.DataFrame:
        return pd.DataFrame(
            [{"table": t, "rows": len(df), "columns": df.shape[1]} for t, df in self._tables.items()]
        ).set_index("table")

    def __repr__(self) -> str:
        parts = ", ".join(f"{t}={len(df):,}" for t, df in self._tables.items())
        return f"<Ilanga District v{self.version} [{self.layer}] seed={self.seed}: {parts}>"


def _build(seed: int, n_patients: int):
    key = (seed, n_patients)
    if key in _MEM:
        return _MEM[key]
    path = os.path.join(_CACHE_DIR, f"ilanga_v{DATASET_VERSION}_{seed}_{n_patients}.pkl")
    if os.path.exists(path):
        try:
            with open(path, "rb") as fh:
                _MEM[key] = pickle.load(fh)
                return _MEM[key]
        except Exception:
            pass
    print("⏳ Generating Ilanga District (first run in this session only, ~10 seconds)...")
    curated = build_curated(seed=seed, n_patients=n_patients)
    raw, answer_key = build_raw(curated, seed=seed)
    _MEM[key] = (curated, raw, answer_key)
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        with open(path, "wb") as fh:
            pickle.dump(_MEM[key], fh)
    except Exception:
        pass
    return _MEM[key]


def load_district(layer: str = "curated", seed: int = DEFAULT_SEED, n_patients: int = 20_000) -> District:
    """Load Ilanga District. layer='curated' (clean) or 'raw' (as extracted from source systems)."""
    if layer not in ("curated", "raw"):
        raise ValueError("layer must be 'curated' or 'raw'")
    curated, raw, _ = _build(seed, n_patients)
    src = curated if layer == "curated" else raw
    return District({k: v.copy() for k, v in src.items()}, layer, seed)


def _answer_key(seed: int = DEFAULT_SEED, n_patients: int = 20_000) -> pd.DataFrame:
    """Duplicate-registration answer key (used by the Module 5 quality gate)."""
    return _build(seed, n_patients)[2].copy()


def age_years(date_of_birth, on_date):
    """Age in completed years on a given date. Works with pandas Series or single dates."""
    delta = pd.to_datetime(on_date) - pd.to_datetime(date_of_birth)
    days = delta.dt.days if hasattr(delta, "dt") else delta.days
    return (days // 365.25).astype(int) if hasattr(days, "astype") else int(days // 365.25)


def age_band(age, scheme: str = "dhis"):
    """Standard age bands. scheme='dhis' (routine reporting) or 'research' (coarser, for de-identified data)."""
    schemes = {
        "dhis": ([0, 5, 15, 25, 50, 200], ["<5", "5-14", "15-24", "25-49", "50+"]),
        "research": ([18, 30, 40, 50, 200], ["18-29", "30-39", "40-49", "50+"]),
    }
    bins, labels = schemes[scheme]
    return pd.cut(age, bins=bins, labels=labels, right=False)


def hint(ticket_id: str, level: int = 1) -> None:
    """Progressive hints: level 1 nudges, level 2 points the way, level 3 nearly solves it."""
    from .tickets import HINTS
    tips = HINTS.get(ticket_id, {})
    if level not in tips:
        print(f"No hint {level} for {ticket_id}. Available levels: {sorted(tips)}")
        return
    brand.hint_box(ticket_id, level, tips[level])


def hello() -> None:
    print(f"✅ ilanga v{DATASET_VERSION} ready  |  BioCollaborator Health Informatics  |  Innovate Naturally")
    print("   All data is synthetic. Ilanga District and Nqaba Health Informatics are fictional.")

from . import tickets  # noqa: E402  (quality gates: ilanga.tickets.check_nq001(...))

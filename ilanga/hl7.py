"""
HL7 v2.5.1 ORU^R01 lab result messages, as an NHLS-style LIS might send them to an EMR.

Segments are separated by carriage returns (\\r), fields by |, components by ^, repeats by ~.
Remember the MSH quirk: MSH-1 IS the field separator, so after splitting on | the index is one
lower than the field number for MSH only.
"""
from __future__ import annotations

import pandas as pd

LOCAL = {"XPERT": ("XPERT", "Xpert MTB/RIF Ultra", "L")}   # HL7 table 0396: L = local code


def _ts(t) -> str:
    return pd.Timestamp(t).strftime("%Y%m%d%H%M")


def _value(row):
    if row["test_code"] == "XPERT":
        return "ST", row["result_text"], "", ""
    if row["test_code"] == "VL" and bool(row.get("below_detection_limit", False)):
        return "SN", "<^50", row["unit"], ""
    v = row["result_numeric"]
    txt = f"{v:g}" if pd.notna(v) else str(row["result_text"])
    flag = "A" if row["test_code"] == "VL" and pd.notna(v) and v >= 1000 else ""
    return "NM", txt, row["unit"], flag


def build_message(row, patient, n: int, receiver: str = "EIMPILO") -> str:
    code, name, system = (row["loinc_code"], row["test_name"], "LN") if pd.notna(row["loinc_code"]) \
        else LOCAL[row["test_code"]]
    ids = f"{patient['patient_id']}^^^ILANGA^MR"
    if isinstance(patient.get("sa_id_number"), str):
        ids += f"~{patient['sa_id_number']}^^^ZAF^NI"
    vtype, value, unit, flag = _value(row)
    obr = ["OBR", "1", row["encounter_id"], row["specimen_id"], f"{code}^{name}^{system}", "", "",
           _ts(row["collected_at"])] + [""] * 6 + [_ts(row["received_at"])] + [""] * 7 + [_ts(row["reported_at"]), "", "", "F"]
    segments = [
        f"MSH|^~\\&|NHLS_LIS|ILN-LAB01|{receiver}|{row['ordering_facility_id']}|{_ts(row['reported_at'])}||ORU^R01^ORU_R01|MSG{n:07d}|P|2.5.1",
        f"PID|1||{ids}||{patient['surname'].upper()}^{patient['first_name'].upper()}||"
        f"{pd.Timestamp(patient['date_of_birth']):%Y%m%d}|{patient['sex']}",
        "|".join(obr),
        f"OBX|1|{vtype}|{code}^{name}^{system}||{value}|{unit}||{flag}|||F",
    ]
    return "\r".join(segments)


def lab_messages(district, limit: int | None = None, facility_id: str | None = None, seed: int = 1) -> list:
    """Build ORU^R01 messages from the curated lab_results table."""
    labs = district.lab_results
    if facility_id:
        labs = labs[labs["ordering_facility_id"] == facility_id]
    if limit:
        labs = labs.sample(min(limit, len(labs)), random_state=seed).sort_values("reported_at")
    pats = district.patients.set_index("patient_id")
    golive = dict(zip(district.facilities["facility_id"], district.facilities["emr_go_live"]))
    out = []
    for n, (_, row) in enumerate(labs.iterrows(), start=1):
        p = pats.loc[row["patient_id"]].to_dict()
        p["patient_id"] = row["patient_id"]
        live = golive.get(row["ordering_facility_id"])
        receiver = "EIMPILO" if pd.notna(live) and row["reported_at"] >= live else "RESULTS_PRINT"
        out.append(build_message(row, p, n, receiver))
    return out

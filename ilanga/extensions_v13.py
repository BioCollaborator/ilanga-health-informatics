"""
Dataset v1.3 extensions (Phase 4 - Advanced).

New tables only; every earlier table is unchanged.

    missed_appointments  scheduled chronic-care visits that did not happen (the strongest real-world LTFU signal)
    clinical_notes       short free-text notes in South African clinical shorthand
    note_annotations     the clinician-annotated "gold standard" for each note (for evaluating NLP)
    helpdesk_messages    patient messages to the district WhatsApp helpline: English, isiZulu and code-switched

isiZulu content is intentionally simple and templated. It should be reviewed by a first-language speaker
before the course is used widely.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .generator import PERIOD_END, PERIOD_START


# ------------------------------------------------------------------ missed appointments
def _missed_appointments(curated, rng) -> pd.DataFrame:
    c = curated["conditions"]
    fsub = dict(zip(curated["facilities"]["facility_id"], curated["facilities"]["subdistrict"]))
    home = dict(zip(curated["patients"]["patient_id"], curated["patients"]["home_facility_id"]))
    chronic = c[c["condition"].isin(["HIV", "Hypertension", "Type 2 diabetes"]) & (c["status"] != "Not on ART")]
    rows, n = [], 0
    for pid, g in chronic.groupby("patient_id"):
        hiv = g[g["condition"] == "HIV"]
        ltfu_date = hiv["status_date"].iloc[0] if len(hiv) and hiv["status"].iloc[0] == "Lost to follow-up" else pd.NaT
        start = max(PERIOD_START, g["onset_date"].min())
        end = PERIOD_END if pd.isna(ltfu_date) else ltfu_date
        if end <= start:
            continue
        months = (end - start).days / 30.4
        base = 0.035 * (1.6 if fsub[home[pid]] == "Ntaba" else 1.0)          # distance makes missing more likely
        k = rng.poisson(base * months)
        dates = [start + pd.Timedelta(days=int(rng.integers(0, (end - start).days + 1))) for _ in range(k)]
        if pd.notna(ltfu_date):                                               # disengagement builds up before LTFU
            win_start = max(PERIOD_START, ltfu_date - pd.Timedelta(days=300))
            if ltfu_date > win_start:
                for _ in range(rng.poisson(2.2)):
                    dates.append(win_start + pd.Timedelta(days=int(rng.integers(0, (ltfu_date - win_start).days + 1))))
        for dt in dates:
            n += 1
            rows.append({"appointment_id": f"ILN-A-{n:06d}", "patient_id": pid, "facility_id": home[pid],
                         "scheduled_date": dt, "traced": bool(rng.random() < 0.45)})
    return pd.DataFrame(rows).sort_values("scheduled_date").reset_index(drop=True)


# ------------------------------------------------------------------ clinical notes
SYMPTOMS = {
    "cough": {"pos": ["c/o cough x{w}/52", "productive cough {w} weeks", "cough +", "coughing for {w}/52"],
              "neg": ["no cough", "cough -", "denies cough"]},
    "fever": {"pos": ["fever +", "febrile, T 38.{t}", "reports fevers", "hot at night, T 38.{t}"],
              "neg": ["no fever", "afebrile", "denies fever"]},
    "night_sweats": {"pos": ["night sweats +", "NS +", "drenching night sweats"],
                     "neg": ["no night sweats", "NS -", "denies night sweats"]},
    "weight_loss": {"pos": ["LOW +", "wt loss +", "lost {kg}kg in {m} months"],
                    "neg": ["no LOW", "nil wt loss", "weight stable"]},
}
ADHERENCE_BAD = ["missed doses last week", "ran out of meds 2/52 ago", "defaulted for 2/12", "not taking meds regularly",
                 "stopped ART due to side effects"]
ADHERENCE_OK = ["adherence good", "taking meds well", "no missed doses", "adherence counselling reinforced"]


def _phrase(rng, options, **fmt):
    return options[int(rng.integers(len(options)))].format(**fmt)


def _clinical_notes(curated, rng):
    enc = curated["encounters"]
    tb_first = enc[enc["visit_type"] == "TB"].sort_values("encounter_date").groupby("patient_id").head(1)
    presumptive = enc[enc["icd10_primary"] == "R05"]
    chronic = enc[enc["visit_type"] == "Chronic"].sample(1400, random_state=int(rng.integers(1e6)))
    chosen = pd.concat([tb_first.assign(kind="tb"), presumptive.assign(kind="presumptive"), chronic.assign(kind="chronic")])
    notes, ann = [], []
    for i, e in enumerate(chosen.itertuples(), start=1):
        truth = {s: False for s in SYMPTOMS}
        parts = []
        if e.kind == "tb":
            present = [s for s in SYMPTOMS if rng.random() < 0.75] or ["cough"]
        elif e.kind == "presumptive":
            present = ["cough"] + [s for s in ("fever", "night_sweats", "weight_loss") if rng.random() < 0.3]
        else:
            present = [s for s in SYMPTOMS if rng.random() < 0.04]
        mentioned = [s for s in SYMPTOMS if s in present or rng.random() < 0.6]
        for s in mentioned:
            pos = s in present
            truth[s] = pos
            parts.append(_phrase(rng, SYMPTOMS[s]["pos" if pos else "neg"], w=int(rng.integers(2, 6)),
                                 t=int(rng.integers(1, 9)), kg=int(rng.integers(3, 9)), m=int(rng.integers(2, 5))))
        rng.shuffle(parts)
        sys_bp = dia_bp = np.nan
        text = "Pt " + ", ".join(parts) + "." if parts else "Pt well."
        if e.kind == "chronic":
            if e.icd10_primary in ("I10", "E11.9") or (isinstance(e.icd10_secondary, str) and "I10" in e.icd10_secondary) \
                    or rng.random() < 0.5:
                sys_bp, dia_bp = int(rng.normal(142, 18)), int(rng.normal(88, 11))
                text += f" BP {sys_bp}/{dia_bp}" + (" mmHg." if rng.random() < 0.5 else ".")
            bad = rng.random() < 0.18
            text += " " + _phrase(rng, ADHERENCE_BAD if bad else ADHERENCE_OK) + "."
        else:
            bad = False
            text += " TB screen " + ("positive" if any(truth.values()) else "negative") + "."
            if e.kind == "tb":
                text += " Sputum sent for Xpert."
        nid = f"ILN-N-{i:05d}"
        notes.append({"note_id": nid, "encounter_id": e.encounter_id, "patient_id": e.patient_id,
                      "note_date": e.encounter_date, "note_text": text})
        ann.append({"note_id": nid, **truth, "bp_systolic": sys_bp, "bp_diastolic": dia_bp, "adherence_concern": bad})
    return (pd.DataFrame(notes).sort_values("note_date").reset_index(drop=True),
            pd.DataFrame(ann).sort_values("note_id").reset_index(drop=True))


# ------------------------------------------------------------------ helpdesk messages
MESSAGES = {
    "appointment": [
        ("English", "Hi, can I change my clinic date to next week?"),
        ("English", "When is my next appointment at the clinic?"),
        ("isiZulu", "Sawubona, ngicela ukushintsha usuku lokuza emtholampilo."),
        ("isiZulu", "Ngizoza nini emtholampilo?"),
        ("Code-switched", "Sawubona sister, can I come ngoLwesihlanu instead?"),
    ],
    "medication": [
        ("English", "My pills are finished, what must I do?"),
        ("English", "I ran out of my BP tablets yesterday."),
        ("isiZulu", "Amaphilisi ami aphelile."),
        ("isiZulu", "Ngiphelelwe ngamaphilisi, ngenzeni?"),
        ("Code-switched", "Hi, my pills aphelile, can I fetch tomorrow?"),
    ],
    "results": [
        ("English", "Are my blood results back yet?"),
        ("English", "Please can you tell me my viral load results."),
        ("isiZulu", "Ngicela ukwazi imiphumela yami yegazi."),
        ("Code-switched", "Sawubona, are my results ready? Ngilinde isikhathi eside."),
    ],
    "urgent": [
        ("English", "I am pregnant and bleeding a lot, please help."),
        ("English", "My baby is not breathing properly."),
        ("English", "Severe headache and blurred vision, I am 34 weeks pregnant."),
        ("isiZulu", "Ngiyopha kakhulu futhi ngikhulelwe."),
        ("isiZulu", "Ingane ayiphefumuli kahle."),
        ("Code-switched", "Please help, ingane has fits and won't wake up."),
    ],
    "feedback": [
        ("English", "Thank you to the nurses at the clinic, they were very kind."),
        ("English", "I waited 6 hours yesterday, this is not right."),
        ("isiZulu", "Ngiyabonga kakhulu kubahlengikazi."),
        ("Code-switched", "The queue was too long, sesilinde amahora amaningi."),
    ],
}


def _helpdesk(rng) -> pd.DataFrame:
    weights = {"appointment": 0.3, "medication": 0.25, "results": 0.2, "urgent": 0.08, "feedback": 0.17}
    rows = []
    start = pd.Timestamp("2025-01-01")
    intents = list(weights)
    for i in range(1, 801):
        intent = intents[int(rng.choice(len(intents), p=list(weights.values())))]
        lang, text = MESSAGES[intent][int(rng.integers(len(MESSAGES[intent])))]
        if rng.random() < 0.3:
            text = text.lower()
        if rng.random() < 0.2:
            text = text.rstrip(".?!") + ("!!" if intent == "urgent" else " pls")
        rows.append({"message_id": f"ILN-M-{i:04d}", "received_at": start + pd.Timedelta(minutes=int(rng.integers(0, 525600))),
                     "language": lang, "message_text": text, "intent": intent})
    return pd.DataFrame(rows).sort_values("received_at").reset_index(drop=True)


def build_v13(curated: dict, seed: int) -> dict:
    notes, annotations = _clinical_notes(curated, np.random.default_rng(seed + 32))
    return {
        "missed_appointments": _missed_appointments(curated, np.random.default_rng(seed + 31)),
        "clinical_notes": notes,
        "note_annotations": annotations,
        "helpdesk_messages": _helpdesk(np.random.default_rng(seed + 33)),
    }

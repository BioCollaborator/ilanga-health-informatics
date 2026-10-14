"""
Small, curated terminology extracts for the course.

These are teaching extracts, not full code systems. In real work you'd use the full releases:
WHO ICD-10, LOINC (loinc.org), SNOMED CT (licensed via SNOMED International) and the WHO ATC index.
"""
import pandas as pd

# WHO ICD-10 chapters (start, end inclusive at category level)
ICD10_CHAPTERS = pd.DataFrame([
    ("I", "A00", "B99", "Certain infectious and parasitic diseases"),
    ("II", "C00", "D48", "Neoplasms"),
    ("III", "D50", "D89", "Diseases of the blood and immune mechanism"),
    ("IV", "E00", "E90", "Endocrine, nutritional and metabolic diseases"),
    ("V", "F00", "F99", "Mental and behavioural disorders"),
    ("VI", "G00", "G99", "Diseases of the nervous system"),
    ("VII", "H00", "H59", "Diseases of the eye and adnexa"),
    ("VIII", "H60", "H95", "Diseases of the ear and mastoid process"),
    ("IX", "I00", "I99", "Diseases of the circulatory system"),
    ("X", "J00", "J99", "Diseases of the respiratory system"),
    ("XI", "K00", "K93", "Diseases of the digestive system"),
    ("XII", "L00", "L99", "Diseases of the skin and subcutaneous tissue"),
    ("XIII", "M00", "M99", "Diseases of the musculoskeletal system"),
    ("XIV", "N00", "N99", "Diseases of the genitourinary system"),
    ("XV", "O00", "O99", "Pregnancy, childbirth and the puerperium"),
    ("XVI", "P00", "P96", "Certain conditions originating in the perinatal period"),
    ("XVII", "Q00", "Q99", "Congenital malformations and chromosomal abnormalities"),
    ("XVIII", "R00", "R99", "Symptoms, signs and abnormal findings"),
    ("XIX", "S00", "T98", "Injury, poisoning and other consequences of external causes"),
    ("XX", "V01", "Y98", "External causes of morbidity and mortality"),
    ("XXI", "Z00", "Z99", "Factors influencing health status and contact with health services"),
    ("XXII", "U00", "U99", "Codes for special purposes"),
], columns=["chapter", "start", "end", "title"])

ICD10_CODES = pd.DataFrame([
    ("B24", "Unspecified human immunodeficiency virus [HIV] disease"),
    ("I10", "Essential (primary) hypertension"),
    ("E11.9", "Type 2 diabetes mellitus without complications"),
    ("A15.0", "Tuberculosis of lung, bacteriologically confirmed"),
    ("Z34.9", "Supervision of normal pregnancy, unspecified"),
    ("Z00.1", "Routine child health examination"),
    ("Z00.0", "General medical examination"),
    ("Z30.9", "Contraceptive management, unspecified"),
    ("J06.9", "Acute upper respiratory infection, unspecified"),
    ("A09", "Diarrhoea and gastroenteritis of presumed infectious origin"),
    ("M54.5", "Low back pain"),
    ("N39.0", "Urinary tract infection, site not specified"),
    ("L30.9", "Dermatitis, unspecified"),
    ("R51", "Headache"),
    ("R05", "Cough"),
    ("K29.7", "Gastritis, unspecified"),
    ("H10.9", "Conjunctivitis, unspecified"),
    ("T14.1", "Open wound of unspecified body region"),
], columns=["code", "label"])

LOINC = pd.DataFrame([
    ("VL", "20447-9", "HIV 1 RNA [#/volume] (viral load) in Serum or Plasma by NAA with probe detection", "active"),
    ("CD4", "24467-3", "CD3+CD4+ (T4 helper) cells [#/volume] in Blood", "active"),
    ("HBA1C", "4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", "active"),
    ("CREAT", "14682-9", "Creatinine [Moles/volume] in Serum or Plasma", "active"),
    ("HB", "718-7", "Hemoglobin [Mass/volume] in Blood", "active"),
    ("XPERT", None, "Xpert MTB/RIF Ultra - two results (MTB detection + rifampicin resistance); mapping needs review", "needs_review"),
], columns=["local_code", "loinc_code", "loinc_long_name", "mapping_status"])

# SNOMED CT concepts for Ilanga's programme conditions (International Edition concept IDs)
SNOMED = pd.DataFrame([
    ("HIV", "86406008", "Human immunodeficiency virus infection"),
    ("Hypertension", "38341003", "Hypertensive disorder, systemic arterial"),
    ("Type 2 diabetes", "44054006", "Diabetes mellitus type 2"),
    ("Tuberculosis", "154283005", "Pulmonary tuberculosis"),
    ("Pregnancy", "77386006", "Pregnancy"),
], columns=["condition", "snomed_code", "snomed_term"])

ATC_LEVEL2 = {
    "A10": "Drugs used in diabetes", "C03": "Diuretics", "C08": "Calcium channel blockers",
    "C09": "Agents acting on the renin-angiotensin system", "J04": "Antimycobacterials",
    "J05": "Antivirals for systemic use",
}

SYSTEM_URIS = {
    "LOINC": "http://loinc.org",
    "SNOMED CT": "http://snomed.info/sct",
    "ICD-10 (WHO)": "http://hl7.org/fhir/sid/icd-10",
    "ATC": "http://www.whocc.no/atc",
    "UCUM (units)": "http://unitsofmeasure.org",
}


def medicines() -> pd.DataFrame:
    from .extensions import MEDICINES
    return pd.DataFrame([(k, n, s, a, ATC_LEVEL2[a[:3]]) for k, (n, s, a, _) in MEDICINES.items()],
                        columns=["medicine_key", "medicine_name", "strength", "atc_code", "atc_level2_name"])

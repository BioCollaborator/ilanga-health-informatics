"""Data dictionary for the Ilanga District dataset (curated layer)."""
import pandas as pd

# table -> list of (column, type, description, privacy_class)
# privacy_class: direct_identifier | quasi_identifier | sensitive | operational
DICTIONARY = {
    "facilities": [
        ("facility_id", "string", "Unique facility code (fictional, ILN- prefix)", "operational"),
        ("facility_name", "string", "Facility name", "operational"),
        ("facility_type", "string", "Clinic, CHC, Mobile Clinic, District/Regional Hospital, Laboratory", "operational"),
        ("subdistrict", "string", "Lwandle (urban coastal), Mfula (peri-urban), Ntaba (rural inland)", "operational"),
        ("latitude", "float", "Fictional coordinates for mapping", "operational"),
        ("longitude", "float", "Fictional coordinates for mapping", "operational"),
        ("emr_go_live", "date", "Date the facility went live on e-Impilo; empty = still paper-based", "operational"),
        ("emr_system", "string", "e-Impilo, Paper + legacy registers, or NHLS LIS", "operational"),
        ("setting", "string", "Urban coastal / Peri-urban / Rural inland", "operational"),
    ],
    "patients": [
        ("patient_id", "string", "Internal master patient index ID (ILN-P-######)", "quasi_identifier"),
        ("first_name", "string", "Given name (synthetic)", "direct_identifier"),
        ("surname", "string", "Family name (synthetic)", "direct_identifier"),
        ("sex", "string", "F / M as recorded at registration", "quasi_identifier"),
        ("date_of_birth", "date", "Date of birth", "quasi_identifier"),
        ("id_type", "string", "SA_ID, PASSPORT or NONE (no document on file)", "operational"),
        ("sa_id_number", "string", "Synthetic 13-digit SA ID (format-valid, not a real person)", "direct_identifier"),
        ("passport_number", "string", "Synthetic passport number (SYN prefix)", "direct_identifier"),
        ("phone", "string", "Synthetic phone number (099 prefix)", "direct_identifier"),
        ("home_language", "string", "Preferred language", "quasi_identifier"),
        ("subdistrict", "string", "Residential subdistrict", "quasi_identifier"),
        ("ward", "int", "Municipal ward number (fictional)", "quasi_identifier"),
        ("address", "string", "Residential address (synthetic)", "direct_identifier"),
        ("home_facility_id", "string", "Facility where the patient usually attends", "quasi_identifier"),
        ("has_medical_aid", "bool", "Member of a medical scheme", "sensitive"),
        ("registration_date", "date", "Date first registered at a facility", "operational"),
    ],
    "conditions": [
        ("condition_id", "string", "Unique condition record ID", "operational"),
        ("patient_id", "string", "Links to patients", "quasi_identifier"),
        ("condition", "string", "HIV, Hypertension, Type 2 diabetes, Tuberculosis, Pregnancy", "sensitive"),
        ("icd10_code", "string", "WHO ICD-10 code", "sensitive"),
        ("onset_date", "date", "Diagnosis / first ANC / TB start date", "sensitive"),
        ("status", "string", "Programme status (e.g. Active, Lost to follow-up, Cured)", "sensitive"),
        ("status_date", "date", "Date the status last changed", "sensitive"),
        ("art_start_date", "date", "HIV only: date antiretroviral therapy started", "sensitive"),
        ("regimen", "string", "HIV: TLD, TEE, AZT/3TC/LPV/r, ABC/3TC/DTG; TB: RHZE", "sensitive"),
    ],
    "encounters": [
        ("encounter_id", "string", "Unique visit ID", "operational"),
        ("patient_id", "string", "Links to patients", "quasi_identifier"),
        ("facility_id", "string", "Where the visit happened", "operational"),
        ("encounter_date", "date", "Date of visit", "quasi_identifier"),
        ("visit_type", "string", "Acute, Chronic, Child health, Antenatal, TB", "sensitive"),
        ("icd10_primary", "string", "Main ICD-10 code for the visit", "sensitive"),
        ("icd10_secondary", "string", "Other codes, semicolon-separated", "sensitive"),
        ("clinician_cadre", "string", "Professional Nurse, Enrolled Nurse, Clinical Associate, Medical Officer", "operational"),
        ("capture_mode", "string", "Digital (e-Impilo) or Paper register", "operational"),
    ],
    "lab_results": [
        ("specimen_id", "string", "Laboratory specimen barcode", "operational"),
        ("patient_id", "string", "Links to patients", "quasi_identifier"),
        ("encounter_id", "string", "Visit where specimen was collected", "operational"),
        ("ordering_facility_id", "string", "Facility that sent the specimen", "operational"),
        ("test_code", "string", "VL, CD4, HBA1C, CREAT, HB, XPERT", "sensitive"),
        ("test_name", "string", "Human-readable test name", "sensitive"),
        ("loinc_code", "string", "LOINC code (Xpert left blank on purpose - Module 6)", "operational"),
        ("result_text", "string", "Result exactly as reported (e.g. '<50')", "sensitive"),
        ("result_numeric", "float", "Parsed numeric value; empty if censored or qualitative", "sensitive"),
        ("unit", "string", "Unit of measure", "operational"),
        ("below_detection_limit", "bool", "True when VL was below the assay limit (<50)", "sensitive"),
        ("collected_at", "datetime", "Specimen collection time", "operational"),
        ("received_at", "datetime", "Time received at the lab", "operational"),
        ("reported_at", "datetime", "Time result was released", "operational"),
    ],
}


def data_dictionary(table: str | None = None) -> pd.DataFrame:
    rows = []
    for t, cols in DICTIONARY.items():
        if table and t != table:
            continue
        for c, typ, desc, priv in cols:
            rows.append({"table": t, "column": c, "type": typ, "description": desc, "privacy_class": priv})
    return pd.DataFrame(rows)

"""
Minimal HL7 FHIR R4 helpers and a teaching validator.

The validator checks the rules this course relies on. It is NOT a full FHIR validator - for
production use the official HL7 validator or a FHIR server's $validate operation.
"""
from __future__ import annotations

import re

OBS_STATUS = {"registered", "preliminary", "final", "amended", "corrected", "cancelled", "entered-in-error", "unknown"}
ENC_STATUS = {"planned", "arrived", "triaged", "in-progress", "onleave", "finished", "cancelled", "entered-in-error", "unknown"}
GENDERS = {"male", "female", "other", "unknown"}
COMPARATORS = {"<", "<=", ">=", ">"}
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?([+-]\d{2}:\d{2}|Z)?)?$")
REF = re.compile(r"^(urn:uuid:[0-9a-fA-F-]+|[A-Z][A-Za-z]+/[A-Za-z0-9\-.]{1,64})$")

ILANGA_PATIENT_ID = "https://fhir.ilanga.example/sid/patient-id"
ZA_ID_EXAMPLE = "https://fhir.ilanga.example/sid/za-id-number"   # real namespaces come from national IGs


def _coding_issues(cc, where):
    issues = []
    if not isinstance(cc, dict) or not cc.get("coding"):
        return [f"{where}: needs a CodeableConcept with at least one coding"]
    for i, c in enumerate(cc["coding"]):
        if not str(c.get("system", "")).startswith(("http://", "https://", "urn:")):
            issues.append(f"{where}.coding[{i}].system must be a URI (e.g. http://loinc.org)")
        if not c.get("code"):
            issues.append(f"{where}.coding[{i}].code is missing")
    return issues


def validate(resource: dict) -> list:
    """Return a list of human-readable issues. An empty list means the resource passed."""
    if not isinstance(resource, dict):
        return ["resource must be a dict (JSON object)"]
    rt = resource.get("resourceType")
    issues = []
    if rt == "Patient":
        for i, ident in enumerate(resource.get("identifier", [])):
            if not ident.get("system") or not ident.get("value"):
                issues.append(f"identifier[{i}] needs both system and value")
        if "gender" in resource and resource["gender"] not in GENDERS:
            issues.append(f"gender must be one of {sorted(GENDERS)}")
        if "birthDate" in resource and not DATE.match(str(resource["birthDate"])):
            issues.append("birthDate must look like YYYY-MM-DD")
    elif rt == "Observation":
        if resource.get("status") not in OBS_STATUS:
            issues.append(f"status is required and must be one of {sorted(OBS_STATUS)}")
        issues += _coding_issues(resource.get("code"), "code")
        if not REF.match(str(resource.get("subject", {}).get("reference", ""))):
            issues.append("subject.reference should look like 'Patient/123'")
        if "effectiveDateTime" in resource and not DATETIME.match(str(resource["effectiveDateTime"])):
            issues.append("effectiveDateTime must be ISO 8601, e.g. 2025-03-04T09:30:00+02:00")
        vq = resource.get("valueQuantity")
        if vq is not None:
            if not isinstance(vq.get("value"), (int, float)):
                issues.append("valueQuantity.value must be a number (not text)")
            if "comparator" in vq and vq["comparator"] not in COMPARATORS:
                issues.append(f"valueQuantity.comparator must be one of {sorted(COMPARATORS)}")
    elif rt == "Encounter":
        if resource.get("status") not in ENC_STATUS:
            issues.append(f"status must be one of {sorted(ENC_STATUS)}")
        if not isinstance(resource.get("class"), dict) or not resource["class"].get("code"):
            issues.append("class (a Coding) is required in FHIR R4")
        if not REF.match(str(resource.get("subject", {}).get("reference", ""))):
            issues.append("subject.reference should look like 'Patient/123'")
    elif rt == "Bundle":
        if resource.get("type") not in {"transaction", "batch", "collection", "searchset", "document", "message"}:
            issues.append("Bundle.type is missing or invalid")
        for i, e in enumerate(resource.get("entry", [])):
            sub = validate(e.get("resource", {}))
            issues += [f"entry[{i}] {s}" for s in sub]
            if resource.get("type") == "transaction" and not e.get("request", {}).get("method"):
                issues.append(f"entry[{i}] needs request.method/url in a transaction bundle")
    else:
        issues.append(f"unsupported or missing resourceType: {rt!r}")
    return issues

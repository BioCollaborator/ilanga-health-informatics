# Ilanga District — synthetic dataset specification (v1.3.0)

This is the contract every module relies on. If the generator changes, this document and the version number change
with it.

## Principles

1. **Fictional and synthetic.** No real people, facilities or results. Facility names are generic; coordinates are
   invented; ID numbers are format-valid but randomly generated; phone numbers use a `099` prefix outside normal
   mobile ranges; passport numbers start with `SYN`.
2. **Illustrative, not official.** Disease rates are chosen to *feel* like a KwaZulu-Natal district. They are not
   statistics and must never be quoted as such.
3. **Reproducible.** Seed `2026` and 20,000 patients are the course defaults. Same seed → identical data everywhere.
4. **Two layers, like a real platform.** `curated` is clean and conformed (Modules 1–4). `raw` is "as extracted from
   source systems", with realistic defects (Module 5 onward).
5. **Light enough for Colab.** Generates in about 10 seconds; cached on disk for the rest of the session.

## Setting

| Sub-district | Share of population | Setting | Wards | Specimen transport to lab |
|---|---|---|---|---|
| Lwandle | 42% | Urban coastal | 19–30 | 2–12 hours |
| Mfula | 33% | Peri-urban | 1–10 | 4–24 hours |
| Ntaba | 25% | Rural inland | 11–18 | 10–60 hours |

**Facilities (14):** 1 regional hospital, 2 district hospitals, 2 CHCs, 7 clinics, 1 mobile clinic, 1 NHLS
laboratory. Seven facilities go live on e-Impilo between July 2024 and August 2025; the rest remain on paper.
Rural Ntaba is least digitised — deliberately, because that's the reality the course wants learners to notice.

**Period:** 1 January 2024 – 31 December 2025. Reference date for ages: 31 December 2025.

## Tables (curated layer)

| Table | Rows (approx.) | Grain |
|---|---|---|
| `facilities` | 14 | one per facility |
| `patients` | 20,000 | one per registered person (HPRS-style register) |
| `conditions` | 7,800 | one per diagnosis / programme enrolment |
| `encounters` | 109,000 | one per visit (PHC headcount) |
| `lab_results` | 16,000 | one per specimen result |

Column-level definitions and privacy classes live in the data catalogue: `ilanga.data_dictionary()`.

## Population and conditions (illustrative parameters)

- **Age structure:** young pyramid; about 29% under 15.
- **Sex:** 53% female (clinic-registered populations skew female).
- **Names:** mix of isiZulu, South African Indian, and English/Afrikaans name pools. No ethnicity column exists —
  names are for realism in matching exercises only.
- **Identity documents:** 88% SA ID, 4% passport, 8% none on file (higher among under-5s).
- **HIV:** age- and sex-specific prevalence peaking at 35% in women aged 35–49. 90% of those diagnosed start ART
  (same-month start after 2016). Programme outcomes: active, lost to follow-up (~10%), transferred out, died.
  Regimens: TLD for most adults, legacy TEE, second-line AZT/3TC/LPV/r, ABC/3TC/DTG for young children.
- **Hypertension:** 6% (15–34) rising to 58% (65+). **Type 2 diabetes:** 2% rising to 20%.
- **Tuberculosis:** ~0.9% over two years, four times higher for people living with HIV. Outcomes include cured,
  completed, lost to follow-up, died, failed, still on treatment.
- **Pregnancy:** ~14% of women aged 15–44 over the period, with 3–6 antenatal visits.

## Visits

Acute visits (Poisson, higher for under-5s and 65+), child-health visits for under-5s, roughly two-monthly chronic
visits (stopping at loss to follow-up, transfer or death), fortnightly-then-monthly TB visits, antenatal visits.
Visits carry WHO ICD-10 codes (primary + secondary), clinician cadre, and a **capture mode** (digital vs paper)
determined by the facility's e-Impilo go-live date.

## Laboratory

| Test | LOINC | Unit | Scheduling |
|---|---|---|---|
| HIV-1 viral load | 20447-9 | copies/mL | 6 months after ART start, then annually |
| CD4 count | 24467-3 | cells/µL | at ART start (if started in period) |
| HbA1c | 4548-4 | % | roughly every third diabetes visit |
| Creatinine | 14682-9 | µmol/L | periodically for hypertension/diabetes |
| Haemoglobin | 718-7 | g/dL | first antenatal visit |
| Xpert MTB/RIF Ultra | *(blank — Module 6 task)* | — | TB diagnosis + presumptive screening |

About 88% of active ART patients are suppressed below 1,000 copies/mL; most suppressed results are reported as
`<50` (censored). Turnaround = transport time (by sub-district) + processing time (by test).

## Raw-layer defects (Module 5 answer key held in `ilanga._answer_key()`)

| Defect | Rate | Why it's realistic |
|---|---|---|
| Duplicate registrations (name typos, swapped names, day/month swaps, missing ID) | ~2.5% of patients | Patients registering again at another facility |
| Invalid SA ID check digits | ~0.5% of SA IDs | Transcription errors at registration |
| Sex flipped or non-standard codes (`U`, `f`, `Female`) | ~1.4% | Free-text fields, inconsistent capture |
| Missing home language | ~3% | Optional fields skipped |
| Encounter dates a year in the future | ~0.2% | Date-entry errors |
| Viral load text variants (`< 50`, `LDL`, `TND`, `Target not detected`) | all censored VL | Different lab systems and eras |
| Creatinine reported in mg/dL instead of µmol/L | ~4% of creatinine | Unit mix-ups between systems |
| Result reported before specimen received | ~1% of labs | Clock and interface errors |

## v1.1 additions (Phase 2)

v1.1 tables are generated with their own random generator, so every v1.0 table is unchanged.

| Table | Rows (approx.) | Grain | Notes |
|---|---|---|---|
| `dispensing` | 74,000 | one per medicine line dispensed | Chronic ART, hypertension, diabetes and TB medicines with WHO ATC codes; ~1/3 of chronic patients collect via CCMDD pick-up points |
| `referrals` | 2,750 | one per referral | Clinics → district hospital (or regional in Lwandle), district → regional; ~20% "did not arrive" (30% from rural Ntaba); all rifampicin-resistant TB referred to the regional DR-TB unit |

**Raw-layer dispensing** replaces standard names and ATC codes with free text (`medicine_text`) in about 50
realistic variants, e.g. "TLD", "TDF/3TC/DTG", "tld 1 tab daily" (Module 6).

**HL7 v2 messages** (`ilanga.hl7.lab_messages`) render lab results as ORU^R01 v2.5.1 messages, with SA ID numbers as
national identifiers, LOINC codes (local code for Xpert), structured numeric `<^50` for censored viral loads, and the
receiving application set to e-Impilo only for facilities live on e-Impilo at the time of reporting (Module 7).

## v1.2 additions (Phase 3)

New tables only; verified by fingerprinting that all v1.0 and v1.1 tables are byte-identical.

| Table | Rows (approx.) | Grain | Notes |
|---|---|---|---|
| `wards` | 30 | one per ward | Fictional centroids; registered patients; estimated population (coverage 55–92%, lowest in Ntaba). Ntaba wards are 5–27 km from the nearest PHC facility |
| `dhis_monthly` | 900 | facility × month × data element (as reported) | e-Impilo facilities report exactly and on time; paper facilities have ~5% tally noise, occasional digit transpositions, missing reports (Ntaba ~10%) and late submissions (due by the 10th of the next month) |
| `weekly_surveillance` | 3,100 | facility × ISO week × syndrome, 2023–2025 | Diarrhoea under 5 (summer peak) and influenza-like illness (winter peak). **Planted outbreak:** diarrhoea at KwaNtaba Clinic (ILN-CL06), 2025-W06 to W09, about three times baseline |
| `specimen_rejections` | 500 | one per rejected specimen | Haemolysed, insufficient volume, mislabelled, wrong tube, leaking, exceeded stability time. Rejection rate and stability failures are highest in Ntaba (transport) |

**Fictional SLA** for lab-controlled turnaround (receipt to report): VL 120 h, CD4 48 h, HbA1c 72 h, creatinine 24 h,
haemoglobin 24 h, Xpert 48 h (`ilanga.extensions_v12.SLA_HOURS`).

## v1.3 additions (Phase 4)

New tables only; verified by fingerprinting that all v1.0–v1.2 tables are byte-identical.

| Table | Rows (approx.) | Grain | Notes |
|---|---|---|---|
| `missed_appointments` | 5,400 | one per missed chronic-care appointment | Baseline ~3.5%/month, 1.6× in rural Ntaba. Patients who are later lost to follow-up accumulate extra misses in the ~10 months before disengaging — the signal Module 14 learns from |
| `clinical_notes` | 1,950 | one per note | SA clinical shorthand (`c/o`, `x3/52`, `NS +`, `LOW`, `afebrile`). TB visits, presumptive-TB visits and a sample of chronic visits |
| `note_annotations` | 1,950 | one per note | Clinician "gold standard": four TB symptoms (present and not negated), blood pressure, adherence concern. Used to score Module 15's extractors |
| `helpdesk_messages` | 800 | one per WhatsApp message | English (43%), isiZulu (33%) and code-switched (24%); intents: appointment, medication, results, urgent (8%), feedback |

**Module 14's shared definitions** (`ilanga.ml`): cutoff 1 October 2024, 12-month horizon, cohort of people on ART
for at least 90 days and still in care at the cutoff (~2,270 people, ~5.8% lost to follow-up), and a fixed
patient-level train/test split so every learner's model is compared on the same patients.

**isiZulu caveat:** helpline messages are short and templated. They should be reviewed by first-language speakers
before the course is used widely.

## Status

The dataset is complete for all 16 modules. Future work: richer free-text notes, a stock visibility table,
and facility-level staffing data.

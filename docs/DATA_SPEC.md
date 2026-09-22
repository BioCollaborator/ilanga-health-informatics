# Ilanga District — synthetic dataset specification (v1.0.0)

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

## Planned for later phases

- v1.1 (Phase 2): medicine dispensing table (ATC codes), referral links between facilities, HL7 v2 lab messages.
- v1.2 (Phase 3): monthly DHIS-style aggregate submissions, stock visibility data.
- v1.3 (Phase 4): short clinical notes in English and isiZulu for NLP.

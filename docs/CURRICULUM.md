# Curriculum & notebook standard

## Who this is for
Health workers new to code, data and IT people new to health, and students in between. One notebook serves all three
through the two-lane design (🩺 Clinic Corner / 💻 Code Corner) and tiered exercises (🌱 🌿 🌳).

**Environment:** Google Colab, Python only. SQL (Module 8) and Cypher (Module 13) are written inside Python via
DuckDB and the Neo4j Python driver. No local installation is ever required.

## The storyline
You're a new analyst at **Nqaba Health Informatics**, contracted to **Ilanga District Health Services**. Recurring
people: Ayanda Mthembu (your team lead), Sister Nomvula Dlamini (Mfula Gateway Clinic), Sipho Ngcobo (district
information manager). More join as the district's needs grow.

## Modules and learning outcomes

### Phase 1 · Onboarding
| # | Module | By the end you can… |
|---|---|---|
| 01 | The SA health data landscape | Describe levels of care and the main public-sector information systems; run Python in Colab; query a DataFrame; measure digitisation by sub-district |
| 02 | Python & pandas: PHC headcount | Use variables, lists, dicts, functions, loops; filter, group, merge and chart clinic data; calculate age at the time of service |
| 03 | Synthetic data done right | Explain what synthetic data can and can't do; use seeds; decode and validate SA ID numbers; build and validate a mini-population |
| 04 | POPIA & de-identification | Apply POPIA concepts to health data; classify identifiers; pseudonymise with keyed hashes; achieve k-anonymity; suppress small cells; log access |

### Phase 2 · Data engineering
| # | Module | By the end you can… |
|---|---|---|
| 05 | Data quality & patient matching | Profile the raw layer; standardise messy values; detect duplicate patients with fuzzy matching; measure precision and recall against an answer key |
| 06 | Clinical terminologies | Work with ICD-10, LOINC, SNOMED CT and medicine codes; map local codes; fill terminology gaps |
| 07 | Interoperability | Parse HL7 v2 lab messages; build and validate FHIR Patient, Observation and Encounter resources; place them in SA's standards landscape |
| 08 | SQL & the district warehouse | Write SQL through DuckDB; design a star schema; build a repeatable pipeline from raw to curated to reporting |

### Phase 3 · Analytics
| # | Module | By the end you can… |
|---|---|---|
| 09 | Routine indicators & cascades | Define indicators with numerators and denominators; reproduce DHIS-style reports; build HIV and TB care cascades |
| 10 | Epidemiology & biostatistics | Calculate incidence, prevalence and retention; confidence intervals; basic survival analysis; outbreak signals |
| 11 | Dashboards & geospatial | Build interactive Plotly dashboards in Colab; map facilities and access; design for decision-makers |
| 12 | Laboratory informatics | Model the specimen lifecycle; analyse turnaround time by distance and test; flag results needing clinical action |

### Phase 4 · Advanced & capstone
| # | Module | By the end you can… |
|---|---|---|
| 13 | Knowledge graphs | Model patients, facilities and referrals as a graph; query with Cypher; trace TB contact and referral networks |
| 14 | Machine learning | Predict loss to follow-up; evaluate properly; audit fairness across sub-districts and sex; explain limits |
| 15 | GenAI & NLP | Process multilingual clinical text; use LLMs safely; consider SAHPRA and POPIA for AI tools |
| 16 | Capstone | Deliver an end-to-end pipeline and an e-Impilo / NHI-readiness report to the district, with a governance appendix |

## Notebook standard (every module)
1. Title, Colab badge, "save a copy" instruction
2. Setup cell (identical in every module)
3. Branded banner + ticket card with definition of done
4. **Policy Watch** where policy is relevant, always dated
5. Guided build: techniques demonstrated on one slice of data (e.g. 2024), applied by learners to another (e.g. 2025)
6. Callouts: 🩺 Clinic Corner, 💻 Code Corner, 🤝 Ubuntu Moment
7. 🌱 Seedling · 🌿 Sapling · 🌳 Baobab exercises with three-level hints
8. 🚦 Quality gate — checks recompute expected answers from the data
9. 📝 Handover note · 🧭 Career Lens · 📚 Glossary · ✅ Checkpoint quiz
10. BioCollaborator footer

## Quality bar for contributors
- Every facilitator notebook must pass its gate in `tests/run_notebooks.py`; every student notebook must run without
  errors and fail its gate.
- Any factual claim about SA policy or systems carries the date it was checked.
- Parameters are labelled illustrative. No real names of patients, staff or facilities.
- Plain language first; jargon is introduced, explained and added to the glossary.

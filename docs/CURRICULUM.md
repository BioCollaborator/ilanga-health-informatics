# Curriculum & notebook standard

## Who this is for
Health workers new to code, data and IT people new to health, and students in between. One notebook serves all three
through the two-lane design (🩺 Clinic Corner / 💻 Code Corner) and tiered exercises (🌱 🌿 🌳).

**Environment:** Google Colab, Python only. SQL (Module 8) and Cypher (Module 13) are written inside Python via
SQLite (built into Python, nothing to install) and the Neo4j Python driver. No local installation is ever required.

## The storyline
You're a new analyst at **Nqaba Health Informatics**, contracted to **Ilanga District Health Services**. Recurring
people: Ayanda Mthembu (your team lead), Sister Nomvula Dlamini (Mfula Gateway Clinic), Sipho Ngcobo (district
information manager), Lerato Mokoena (e-Impilo implementation lead), Dr Priya Naidoo (clinical governance lead), Dr Musa Zungu
(district epidemiologist), Mrs Nokuthula Cele (district manager), Zanele Khumalo (NHLS laboratory manager),
Bheki Ntuli (HIV programme manager) and Thandeka Mbatha (helpline coordinator).

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
| 06 | Clinical terminologies | Work with ICD-10, LOINC, SNOMED CT and ATC; map free text to codes; recognise when a mapping must be escalated rather than guessed |
| 07 | Interoperability | Parse HL7 v2 lab messages; build and validate FHIR Patient, Observation and Bundle resources; place them in SA's standards landscape |
| 08 | SQL & the district warehouse | Write SQL through SQLite; design a star schema; build a repeatable pipeline from raw to curated to reporting |

### Phase 3 · Analytics
| # | Module | By the end you can… |
|---|---|---|
| 09 | Routine indicators & cascades | Define indicators with numerators and denominators; measure reporting completeness, timeliness and concordance; build HIV and TB care cascades |
| 10 | Epidemiology & biostatistics | Wilson confidence intervals; risk ratios with CIs; Kaplan–Meier retention; baseline-based outbreak detection that balances sensitivity and alert fatigue |
| 11 | Dashboards & geospatial | Calculate haversine distances and ward access; design RAG-status KPI dashboards; ship a single-file offline HTML dashboard (Plotly optional) |
| 12 | Laboratory informatics | Separate transport, lab and total turnaround time; measure SLA compliance; analyse specimen rejections; audit follow-up of high viral loads |

### Phase 4 · Advanced & capstone
| # | Module | By the end you can… |
|---|---|---|
| 13 | Knowledge graphs | Build referral and shared-patient networks in NetworkX; run community detection; walk a district knowledge graph for multi-hop clinical questions; write the same queries in Cypher (Neo4j optional) |
| 14 | Machine learning | Frame a prediction problem (cohort, cutoff, horizon, action); build leakage-free features; evaluate with AUC rather than accuracy; set thresholds from real team capacity; audit fairness and write a model card |
| 15 | Clinical NLP & GenAI | Extract structured values from SA clinical shorthand; handle negation; triage English, isiZulu and code-switched helpline messages with 100% urgent recall; assess LLMs against POPIA, SAHPRA and a gold standard |
| 16 | Capstone | Build a five-criterion facility readiness scorecard, write a six-section district report, ship a dashboard, and distinguish facility-level problems from system-level ones |

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

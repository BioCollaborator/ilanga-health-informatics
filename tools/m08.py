from nb import md, code, ex, SETUP, FOOTER, colab_badge

PATH = "notebooks/phase2_data_engineering/M08_sql_pipelines_district_warehouse.ipynb"

CELLS = [
md(f"""
# Module 08 · The district data warehouse — SQL, pipelines and data tests
**BioCollaborator Health Informatics Programme** · Phase 2: Data Engineering · *Innovate Naturally*

{colab_badge(PATH)}

> **File → Save a copy in Drive**, then run cells top to bottom with **Shift + Enter**.
"""),
code(SETUP),
code('''
import sqlite3

ilanga.brand.banner(8, "The district data warehouse: SQL, pipelines & data tests", "Phase 2 · Data Engineering", minutes=150)
ilanga.brand.ticket(
    "NQ-008", "Sipho Ngcobo", "District Information Manager, Ilanga District Health Services",
    "Build the district reporting warehouse",
    "Every month my team rebuilds the same reports from scratch in spreadsheets, and every month the numbers "
    "come out slightly different. I want one warehouse, rebuilt the same way every time, with checks that shout "
    "when something's wrong - before a wrong number reaches the provincial report.",
    ["A repeatable pipeline that loads Ilanga into a star-schema warehouse",
     "SQL for 2025 headcount per facility",
     "SQL for 2025 viral load suppression by sub-district",
     "Reusable data tests for uniqueness, missing values and broken links between tables"],
    priority="High")
'''),
md("""
## Part 1 · Why a warehouse?

Source systems like e-Impilo are built for **transactions**: register a patient, record a visit, fast, one at a time.
Reporting needs the opposite: scan millions of rows, group, count, compare. So we copy data into a separate
**warehouse** built for analysis, in layers:

| Layer | Also called | What it holds |
|---|---|---|
| **Raw / staging** | bronze | Data as received (Module 5's raw layer) |
| **Curated** | silver | Cleaned, conformed, de-duplicated |
| **Marts** | gold | Report-ready tables and indicators |

### The star schema

Analysts organise the curated layer as a **star**: **fact** tables in the middle hold events (visits, lab results,
dispensing), and **dimension** tables around them describe the who, where, what and when.

```
                dim_date
                    |
  dim_patient — fact_encounter — dim_facility
                    |
               fact_lab — dim_test
```

> 🩺 **Clinic Corner — facts are things that happened**
>
> A visit happened. A test was done. A medicine was handed over. Those are **facts**. The clinic, the patient's age
> band, the month: those **describe** facts. Asking "how many viral loads were done in Ntaba last quarter?" is just
> counting facts filtered by dimensions.

## Part 2 · A repeatable pipeline

**SQLite** is a complete SQL database that lives in a single file and comes built into Python — nothing to install.
The same SQL you learn here works, with small dialect differences, in PostgreSQL, SQL Server, BigQuery and others.

A good pipeline is **idempotent**: run it once or ten times, you get the same result. Ours rebuilds every table from
scratch on each run.
"""),
code('''
def build_warehouse(conn, district):
    """Load the curated district into a star schema. Safe to re-run (idempotent)."""
    d = district
    dim_patient = d.patients.assign(
        age_band=ilanga.age_band(ilanga.age_years(d.patients["date_of_birth"], ilanga.REFERENCE_DATE)).astype(str)
    )[["patient_id", "sex", "age_band", "subdistrict", "home_facility_id", "has_medical_aid"]]   # no direct identifiers!

    dates = pd.DataFrame({"date": pd.date_range("2024-01-01", "2025-12-31")})
    dim_date = dates.assign(year=dates["date"].dt.year, quarter=dates["date"].dt.quarter,
                            month=dates["date"].dt.month, month_name=dates["date"].dt.strftime("%b"))

    dim_test = ilanga.terminology.LOINC.rename(columns={"local_code": "test_code"})

    fact_lab = d.lab_results.assign(
        tat_hours=(d.lab_results["reported_at"] - d.lab_results["collected_at"]).dt.total_seconds() / 3600)

    tables = {
        "dim_patient": dim_patient, "dim_facility": d.facilities, "dim_date": dim_date, "dim_test": dim_test,
        "fact_encounter": d.encounters, "fact_lab": fact_lab, "fact_dispense": d.dispensing,
        "fact_referral": d.referrals,
    }
    for name, df in tables.items():
        df.to_sql(name, conn, if_exists="replace", index=False)
    return {name: len(df) for name, df in tables.items()}

conn = sqlite3.connect("ilanga_warehouse.db")
load_report = build_warehouse(conn, ilanga.load_district())
pd.Series(load_report, name="rows_loaded")
'''),
md("""
> 🤝 **Ubuntu Moment — governance by design**
>
> Look at `dim_patient`: no names, no ID numbers, no phone numbers, no addresses. Reporting doesn't need them, so the
> warehouse never receives them. That's POPIA's **processing limitation** principle (Module 4) built into the
> architecture instead of left to good intentions.

## Part 3 · SQL in fifteen minutes

SQL (Structured Query Language) describes *what* you want, not *how* to get it. `pd.read_sql(query, conn)` runs a
query and returns a DataFrame.
"""),
code('''
def sql(query):
    return pd.read_sql(query, conn)

# SELECT columns FROM a table, filter with WHERE, sort with ORDER BY, cap with LIMIT
sql("""
SELECT facility_id, facility_name, facility_type, subdistrict
FROM dim_facility
WHERE facility_type = 'Clinic'
ORDER BY subdistrict, facility_name
""")
'''),
code('''
# GROUP BY: count visits by type in 2024
sql("""
SELECT visit_type, COUNT(*) AS visits
FROM fact_encounter
WHERE strftime('%Y', encounter_date) = '2024'
GROUP BY visit_type
ORDER BY visits DESC
""")
'''),
code('''
# JOIN: bring in facility details to count 2024 visits by sub-district and capture mode
sql("""
SELECT f.subdistrict, e.capture_mode, COUNT(*) AS visits
FROM fact_encounter AS e
JOIN dim_facility AS f ON e.facility_id = f.facility_id
WHERE strftime('%Y', e.encounter_date) = '2024'
GROUP BY f.subdistrict, e.capture_mode
ORDER BY f.subdistrict
""")
'''),
code('''
# CTE + window function: 2024 monthly lab volume with a running total
sql("""
WITH monthly AS (
    SELECT strftime('%m', collected_at) AS month, COUNT(*) AS tests
    FROM fact_lab
    WHERE strftime('%Y', collected_at) = '2024'
    GROUP BY month
)
SELECT month, tests, SUM(tests) OVER (ORDER BY month) AS running_total
FROM monthly
""")
'''),
md("""
> 💻 **Code Corner — reading SQL**
>
> SQL is *written* in the order `SELECT … FROM … WHERE … GROUP BY … ORDER BY`, but it *runs* in the order
> **FROM → WHERE → GROUP BY → SELECT → ORDER BY**. When a query confuses you, read it in running order.
> A **CTE** (`WITH name AS (...)`) is a named temporary result that makes long queries readable.
> A **window function** (`SUM(...) OVER (...)`) calculates across rows without collapsing them.

### 🌱 Seedling — 2025 headcount per facility
Write SQL that returns `facility_id` and `headcount` (visits in 2025) for every facility. Store the DataFrame in
`facility_headcount_2025`. Hints: `ilanga.hint("NQ-008.1")`.
"""),
ex('''
facility_headcount_2025 = sql("""
-- 👈 your SQL here
SELECT 1 AS placeholder
""")
facility_headcount_2025
''', '''
facility_headcount_2025 = sql("""
SELECT facility_id, COUNT(*) AS headcount
FROM fact_encounter
WHERE strftime('%Y', encounter_date) = '2025'
GROUP BY facility_id
ORDER BY facility_id
""")
facility_headcount_2025
'''),
md("""
### 🌿 Sapling — 2025 viral load suppression by sub-district
Return `subdistrict`, `tests`, `suppressed` and `pct_suppressed` (one decimal place) for viral loads **collected in
2025**. Suppressed means **below the detection limit or below 1,000 copies/mL**. Use the ordering facility's
sub-district. Store in `vl_suppression_2025`. Hints: `ilanga.hint("NQ-008.2")`.
"""),
ex('''
vl_suppression_2025 = sql("""
-- 👈 your SQL here
SELECT 1 AS placeholder
""")
vl_suppression_2025
''', '''
vl_suppression_2025 = sql("""
WITH vl AS (
    SELECT l.*, f.subdistrict
    FROM fact_lab AS l
    JOIN dim_facility AS f ON l.ordering_facility_id = f.facility_id
    WHERE l.test_code = 'VL' AND strftime('%Y', l.collected_at) = '2025'
)
SELECT subdistrict,
       COUNT(*) AS tests,
       SUM(CASE WHEN below_detection_limit = 1 OR result_numeric < 1000 THEN 1 ELSE 0 END) AS suppressed,
       ROUND(100.0 * SUM(CASE WHEN below_detection_limit = 1 OR result_numeric < 1000 THEN 1 ELSE 0 END) / COUNT(*), 1)
           AS pct_suppressed
FROM vl
GROUP BY subdistrict
ORDER BY subdistrict
""")
vl_suppression_2025
'''),
md("""
> 🩺 **Clinic Corner — suppression is only as good as its denominator**
>
> This measures suppression **among people who got a viral load test**. People who missed their test — often the
> ones struggling with treatment — aren't in the denominator at all. That's why the HIV cascade (Module 9) also asks
> *what share of people on ART had a viral load done?* A high suppression rate with low testing coverage can hide
> real problems.

## Part 4 · Data tests: making the warehouse shout

A warehouse that silently loads bad data is worse than no warehouse. Modern data teams attach **tests** to every
table and run them after every load. The four classics:

| Test | Catches |
|---|---|
| **unique** | Duplicate keys (the same visit loaded twice) |
| **not_null** | Missing values in required columns |
| **relationship** | Facts pointing to things that don't exist (a visit at facility "ILN-CL99") |
| **accepted values** | Values outside an allowed list (sex = "Female" instead of "F") |

Here's the accepted-values test, written as a Python function that runs SQL:
"""),
code('''
def test_accepted_values(conn, table, column, allowed):
    allowed_sql = ", ".join(f"'{v}'" for v in allowed)
    bad = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} NOT IN ({allowed_sql})").fetchone()[0]
    return bad == 0

print("dim_patient.sex accepted values:", test_accepted_values(conn, "dim_patient", "sex", ["F", "M"]))
print("fact_encounter.capture_mode accepted values:",
      test_accepted_values(conn, "fact_encounter", "capture_mode", ["Digital (e-Impilo)", "Paper register"]))
'''),
md("""
### 🌳 Baobab — write the other three tests
Write three functions that each return a Python `True` (test passes) or `False` (problem found):
- `test_unique(conn, table, column)`
- `test_not_null(conn, table, column)`
- `test_relationship(conn, child_table, child_column, parent_table, parent_column)` — every non-empty child key must
  exist in the parent table

The gate runs your functions against tables with known problems. Hints: `ilanga.hint("NQ-008.3")`.
"""),
ex('''
def test_unique(conn, table, column):
    # 👈 your code here
    return None

def test_not_null(conn, table, column):
    # 👈 your code here
    return None

def test_relationship(conn, child_table, child_column, parent_table, parent_column):
    # 👈 your code here
    return None
''', '''
def test_unique(conn, table, column):
    dupes = conn.execute(f"SELECT COUNT(*) - COUNT(DISTINCT {column}) FROM {table}").fetchone()[0]
    return dupes == 0

def test_not_null(conn, table, column):
    nulls = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL").fetchone()[0]
    return nulls == 0

def test_relationship(conn, child_table, child_column, parent_table, parent_column):
    orphans = conn.execute(f"""
        SELECT COUNT(*) FROM {child_table} AS c
        LEFT JOIN {parent_table} AS p ON c.{child_column} = p.{parent_column}
        WHERE c.{child_column} IS NOT NULL AND p.{parent_column} IS NULL""").fetchone()[0]
    return orphans == 0
'''),
code('''
# Run the full test suite on the warehouse - the way a pipeline would after every load
if test_unique(conn, "dim_facility", "facility_id") is not None:
    suite = [
        ("unique", "fact_encounter.encounter_id", lambda: test_unique(conn, "fact_encounter", "encounter_id")),
        ("unique", "fact_lab.specimen_id", lambda: test_unique(conn, "fact_lab", "specimen_id")),
        ("not_null", "fact_encounter.patient_id", lambda: test_not_null(conn, "fact_encounter", "patient_id")),
        ("not_null", "fact_lab.reported_at", lambda: test_not_null(conn, "fact_lab", "reported_at")),
        ("relationship", "fact_encounter -> dim_facility",
         lambda: test_relationship(conn, "fact_encounter", "facility_id", "dim_facility", "facility_id")),
        ("relationship", "fact_lab -> dim_patient",
         lambda: test_relationship(conn, "fact_lab", "patient_id", "dim_patient", "patient_id")),
        ("relationship", "fact_referral -> dim_facility",
         lambda: test_relationship(conn, "fact_referral", "to_facility_id", "dim_facility", "facility_id")),
        ("accepted_values", "dim_patient.sex", lambda: test_accepted_values(conn, "dim_patient", "sex", ["F", "M"])),
    ]
    results = pd.DataFrame([{"test": t, "target": target, "passed": fn()} for t, target, fn in suite])
    display(results)
    print("✅ All data tests passed" if results["passed"].all() else "❌ Some tests failed - do not publish reports")
'''),
md("""
## Part 5 · A report-ready mart

The last layer is a **mart**: a table shaped exactly like the report. We save it as a **view**, so it's always
up to date with the warehouse and everyone uses the same definition.
"""),
code('''
conn.execute("DROP VIEW IF EXISTS mart_monthly_headcount")
conn.execute("""
CREATE VIEW mart_monthly_headcount AS
SELECT f.subdistrict, f.facility_name, strftime('%Y-%m', e.encounter_date) AS month,
       COUNT(*) AS headcount,
       SUM(CASE WHEN e.visit_type = 'Child health' THEN 1 ELSE 0 END) AS child_health_visits
FROM fact_encounter AS e JOIN dim_facility AS f ON e.facility_id = f.facility_id
GROUP BY f.subdistrict, f.facility_name, month
""")
mart = sql("SELECT * FROM mart_monthly_headcount WHERE month LIKE '2025-%' ORDER BY subdistrict, facility_name, month")
mart.to_csv("ilanga_monthly_headcount_2025.csv", index=False)
print(f"Saved {len(mart)} rows to ilanga_monthly_headcount_2025.csv (find it in Colab's Files panel)")
mart.head(12)
'''),
md("""
> 💻 **Code Corner — the runbook habit**
>
> In a real team, this whole notebook becomes a scheduled job: **load → test → build marts → publish**, and the job
> stops at "test" if anything fails. The steps are written down in a **runbook** so anyone can re-run or fix it at 2am.
> Your handover note below is the first draft of Ilanga's runbook.

## 🚦 Quality gate
"""),
code('''
passed = ilanga.tickets.check_nq008(facility_headcount_2025, vl_suppression_2025,
                                    test_unique, test_not_null, test_relationship)
'''),
md("""
## 📝 Handover note — draft runbook
> **NQ-008 — done. For: Sipho Ngcobo.**
> *To refresh the warehouse: 1) … 2) run the data tests … 3) if a test fails …*
> *2025 viral load suppression ranged from …% in … to …% in … (among people tested).*
> *Caveat for the provincial report: …*

---
### 🎓 Phase 2 complete
You can now clean raw health data, match patients, code diagnoses, tests and medicines, read HL7 v2 and write FHIR,
and run a tested, repeatable warehouse. That's the full foundation of a data engineering role in health.
**Phase 3 — Analytics** puts it to work: indicators and cascades, epidemiology, dashboards and laboratory informatics.

## 🧭 Career Lens
**Data engineers**, **BI developers** and **M&E data managers** build and run exactly this kind of pipeline at
provincial departments, NGOs, implementing partners and private hospital groups. SQL is the single most requested
skill in South African data job adverts — and "I built a tested warehouse" is a strong line on a CV.

## 📚 Glossary
**Warehouse** – a database built for analysis · **Staging / curated / mart** – raw, cleaned and report-ready layers
(bronze / silver / gold) · **Star schema** – facts surrounded by dimensions · **Idempotent** – same result however
many times you run it · **CTE** – a named sub-query (WITH …) · **Window function** – a calculation across rows
(… OVER …) · **View** – a saved query that acts like a table · **Data test** – an automated check on loaded data ·
**Runbook** – written steps for operating a pipeline

## ✅ Checkpoint
<details><summary>1. In what order does SQL actually execute SELECT, FROM, WHERE and GROUP BY?</summary>FROM → WHERE → GROUP BY → SELECT (then ORDER BY).</details>
<details><summary>2. Why doesn't dim_patient include names or ID numbers?</summary>Reporting doesn't need them. Leaving them out applies POPIA's processing-limitation principle by design.</details>
<details><summary>3. A relationship test finds 40 lab results for patient IDs that aren't in dim_patient. What might have happened?</summary>Patients were merged or deleted upstream without updating the facts, the patient load failed, or IDs were changed. Stop and investigate before publishing.</details>
"""),
md(FOOTER),
]

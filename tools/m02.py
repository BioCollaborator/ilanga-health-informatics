from nb import md, code, ex, SETUP, FOOTER, colab_badge

PATH = "notebooks/phase1_onboarding/M02_python_pandas_phc_headcount.ipynb"

CELLS = [
md(f"""
# Module 02 · Python & pandas through a clinic's eyes — the PHC headcount report
**BioCollaborator Health Informatics Programme** · Phase 1: Onboarding · *Innovate Naturally*

{colab_badge(PATH)}

> **File → Save a copy in Drive**, then run cells top to bottom with **Shift + Enter**.
"""),
code(SETUP),
code('''
ilanga.brand.banner(2, "Python & pandas: the PHC headcount report", "Phase 1 · Onboarding", minutes=120)
ilanga.brand.ticket(
    "NQ-002", "Sister Nomvula Dlamini", "Operational Manager, Mfula Gateway Clinic",
    "Automate our monthly headcount for DHIS",
    "Every month my team spends hours tallying the registers for our DHIS monthly report. We've been live "
    "on e-Impilo since November 2024, so the visits are all in the system now. Can you give me our 2025 "
    "headcount, the month-by-month trend, and our under-5 headcount? If it's right, we never tally by hand again.",
    ["Total 2025 headcount for Mfula Gateway Clinic (ILN-CL01)",
     "Monthly headcount for January to December 2025",
     "Monthly under-5 headcount for 2025 (age on the day of the visit)",
     "A chart Sister Nomvula can pin on the staff noticeboard"],
    priority="High")
'''),
md("""
## How this module works

We learn every technique on **2024** data, then you apply it to **2025** for the ticket. Same skills, fresh problem —
that's how you know you've *learned* rather than *copied*.

> 🩺 **Clinic Corner — what is "headcount"?**
>
> In South African routine reporting, **PHC headcount** counts **visits**, not unique people. If Sipho comes in
> three times in March, that's three headcounts. It measures **workload**, which is why managers use it for
> staffing. **Under-5 headcount** counts visits by children younger than five — a key child-health indicator.

---
## Part 1 · Python building blocks (with a clinic in mind)

> 💻 **Code Corner — types of values**
>
> Python values have **types**: whole numbers (`int`), decimals (`float`), text (`str`), and True/False (`bool`).
> `type(x)` tells you what you're holding. Mixing them up is the #1 beginner bug.
"""),
code('''
clinic_code = "ILN-CL01"      # str  (text always goes in quotes)
visits_today = 142            # int
average_wait_hours = 2.5      # float
is_emr_live = True            # bool

for value in [clinic_code, visits_today, average_wait_hours, is_emr_live]:
    print(repr(value), "->", type(value).__name__)
'''),
md("""
### Lists: the morning queue
A **list** keeps things in order. Python counts from **0**, so the first person in the queue is `queue[0]`.
"""),
code('''
queue = ["Sipho", "Zanele", "Thabo", "Nokuthula"]
print("First in line:", queue[0])
print("Last in line:", queue[-1])     # negative numbers count from the end

queue.append("Priya")                  # someone new arrives
print(f"{len(queue)} people waiting: {queue}")
'''),
md("""
### Dictionaries: one patient's record
A **dictionary** stores **key → value** pairs. It's the closest Python gets to a filled-in form — and, as you'll see
in Module 7, it's almost exactly the shape of a FHIR health record.
"""),
code('''
patient = {
    "first_name": "Zanele",
    "age": 34,
    "systolic_bp": 152,
    "diastolic_bp": 94,
    "on_treatment": False,
}
print(patient["first_name"], "is", patient["age"])
patient["on_treatment"] = True      # update a field
patient
'''),
md("""
### Decisions with `if`: a blood-pressure check

> ⚠️ Teaching example only — **not clinical guidance.** It uses the common adult threshold where a reading of
> 140/90 mmHg or higher is raised, and 180/110 or higher is in the severe range.
"""),
code('''
def classify_bp(systolic, diastolic):
    """Return a simple category for an adult blood pressure reading."""
    if systolic >= 180 or diastolic >= 110:
        return "Severe range - follow urgent protocol"
    elif systolic >= 140 or diastolic >= 90:
        return "Raised"
    else:
        return "Below 140/90"

print(classify_bp(patient["systolic_bp"], patient["diastolic_bp"]))
'''),
md("""
> 💻 **Code Corner — functions**
>
> `def classify_bp(...)` defines a **function**: a reusable recipe. Write it once, use it a thousand times.
> Indentation (the spaces at the start of lines) is how Python knows what belongs inside the function or the `if`.

### Loops: the whole morning's readings
"""),
code('''
readings = [("Sipho", 128, 82), ("Zanele", 152, 94), ("Bheki", 184, 112), ("Priya", 138, 88)]

for name, sys_bp, dia_bp in readings:
    print(f"{name:<8} {sys_bp}/{dia_bp}  ->  {classify_bp(sys_bp, dia_bp)}")
'''),
md("""
---
## Part 2 · pandas: from registers to reports

A clinic's register is just a table. pandas lets you ask a table questions at the speed of thought.
"""),
code('''
district = ilanga.load_district()
enc = district.encounters

print("Rows, columns:", enc.shape)
enc.head()
'''),
code('''
enc.dtypes
'''),
md("""
> 💻 **Code Corner — dates are special**
>
> `encounter_date` has type `datetime64`. That means pandas *understands* it as a date, so we can pull out the year
> or month with `.dt.year` and `.dt.month`. If dates arrive as plain text (they often do — Module 5!), none of this works
> until we convert them.

### Filtering: one clinic, one year
A **boolean mask** is a column of True/False answers. Putting it inside `enc[...]` keeps only the True rows.
"""),
code('''
is_mfula_gateway = enc["facility_id"] == "ILN-CL01"
is_2024 = enc["encounter_date"].dt.year == 2024

visits_2024 = enc[is_mfula_gateway & is_2024]      # & means AND; each condition is its own mask
print(f"Mfula Gateway Clinic, 2024 headcount: {len(visits_2024):,}")
'''),
code('''
visits_2024["visit_type"].value_counts()
'''),
md("""
### Grouping: the monthly picture
`groupby` splits a table into groups, does something to each group, and combines the answers. It's the single most
useful idea in data analysis.
"""),
code('''
monthly_2024 = visits_2024.groupby(visits_2024["encounter_date"].dt.month).size()
monthly_2024
'''),
code('''
# Pivot: months down the side, visit types across the top
visits_2024.pivot_table(index=visits_2024["encounter_date"].dt.month, columns="visit_type",
                        values="encounter_id", aggfunc="count", fill_value=0)
'''),
md("""
### Joining tables: bringing in date of birth
Visits don't store age — patients do. **Merging** joins two tables on a shared column, just like matching a folder
number between the register and the patient file.
"""),
code('''
with_dob = visits_2024.merge(district.patients[["patient_id", "date_of_birth", "sex"]], on="patient_id", how="left")

# Age on the day of the visit - NOT today's age
with_dob["age_at_visit"] = ilanga.age_years(with_dob["date_of_birth"], with_dob["encounter_date"])
with_dob["age_band"] = ilanga.age_band(with_dob["age_at_visit"])

with_dob[["encounter_date", "date_of_birth", "age_at_visit", "age_band", "visit_type"]].head(8)
'''),
code('''
with_dob["age_band"].value_counts().sort_index()
'''),
md("""
> 🩺 **Clinic Corner — why "age at visit"?**
>
> A child born in March 2020 was *under five* at a visit in January 2025, but is *five* by the time you run the report
> in December. Reports must use the age **on the day of the service**. Getting this wrong is a classic reporting error
> that quietly shifts indicators — and sometimes funding.

### A chart for the noticeboard
"""),
code('''
fig, ax = plt.subplots(figsize=(9, 3.5))
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
ax.bar(months, monthly_2024.reindex(range(1, 13), fill_value=0).values, color=BRAND["teal"])
ax.set_title("Mfula Gateway Clinic — PHC headcount, 2024")
ax.set_ylabel("Visits")
plt.show()
'''),
md("""
> 🤝 **Ubuntu Moment — give data back to the people who made it**
>
> Nurses record every visit, often at the end of an exhausting shift, and rarely see what happens to that data.
> A simple chart on the noticeboard that shows *their* workload is powerful: it says "your records matter".
> Data used at the point of collection gets better, because people care about it.

---
## 🎯 Your turn — now do it for 2025
Hints: `ilanga.hint("NQ-002.1")`, `ilanga.hint("NQ-002.2")`, `ilanga.hint("NQ-002.3")` — levels 1 to 3.

### 🌱 Seedling — total 2025 headcount at Mfula Gateway Clinic
Store an integer in `headcount_2025`.
"""),
ex('''
headcount_2025 = None   # 👈 your code here
print(headcount_2025)
''', '''
visits_2025 = enc[(enc["facility_id"] == "ILN-CL01") & (enc["encounter_date"].dt.year == 2025)]
headcount_2025 = len(visits_2025)
print(headcount_2025)
'''),
md("""
### 🌿 Sapling — monthly headcount for 2025
Store a Series indexed by month number (1–12) in `monthly_headcount`.
"""),
ex('''
monthly_headcount = None   # 👈 your code here
monthly_headcount
''', '''
monthly_headcount = visits_2025.groupby(visits_2025["encounter_date"].dt.month).size().reindex(range(1, 13), fill_value=0)
monthly_headcount
'''),
md("""
### 🌳 Baobab — monthly under-5 headcount for 2025
Store a Series indexed by month (1–12) in `under5_monthly`. Then, for bonus credit with Sister Nomvula, draw a chart
showing total headcount and under-5 headcount together.
"""),
ex('''
under5_monthly = None   # 👈 your code here
under5_monthly
''', '''
v = visits_2025.merge(district.patients[["patient_id", "date_of_birth"]], on="patient_id")
v = v[ilanga.age_years(v["date_of_birth"], v["encounter_date"]) < 5]
under5_monthly = v.groupby(v["encounter_date"].dt.month).size().reindex(range(1, 13), fill_value=0)

fig, ax = plt.subplots(figsize=(9, 3.5))
ax.bar(months, monthly_headcount.values, color=BRAND["teal"], label="All visits")
ax.bar(months, under5_monthly.values, color=BRAND["ochre"], label="Under-5 visits")
ax.set_title("Mfula Gateway Clinic — PHC headcount, 2025"); ax.legend()
plt.show()
under5_monthly
'''),
md("""
## 🚦 Quality gate
"""),
code('''
passed = ilanga.tickets.check_nq002(headcount_2025, monthly_headcount, under5_monthly)
'''),
md("""
## 📝 Handover note
> **NQ-002 — done. For: Sister Nomvula.**
> *The 2025 headcount was … The busiest month was … Under-5 visits made up about …% of visits.*
> *One thing I'd check with the team before this replaces the manual tally: …*

## 🧭 Career Lens
You just automated a report that clinics across the country still build by hand. **Data capturers**, **facility
information officers** and **junior data analysts** who can do this are the people who free nurses to nurse.
Python + pandas is also the entry ticket for most **health data analyst** job adverts.

## 📚 Glossary
**Headcount** – count of visits (not unique people) · **Variable** – a named value · **List / dictionary** – ordered
items / key-value pairs · **DataFrame** – a pandas table · **Boolean mask** – True/False column used to filter ·
**groupby** – split, apply, combine · **merge** – join two tables on a shared key

## ✅ Checkpoint
<details><summary>1. Sipho visits three times in March. What does he add to March headcount?</summary>3 — headcount counts visits.</details>
<details><summary>2. Why do we calculate age on the date of the visit?</summary>Because indicators like under-5 headcount depend on age at the time of the service, not when the report is run.</details>
<details><summary>3. What does <code>enc[mask1 & mask2]</code> do?</summary>Keeps only rows where both conditions are True.</details>

**Next up → Module 03:** Where does Ilanga's data actually come from? You'll open the hood of the synthetic data
generator — and build your own.
"""),
md(FOOTER),
]

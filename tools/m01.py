from nb import md, code, ex, SETUP, FOOTER, colab_badge

PATH = "notebooks/phase1_onboarding/M01_welcome_sa_health_data_landscape.ipynb"

CELLS = [
md(f"""
# Module 01 · Sawubona! Welcome to Nqaba — the South African health data landscape
**BioCollaborator Health Informatics Programme** · Phase 1: Onboarding · *Innovate Naturally*

{colab_badge(PATH)}

> **Before you start:** In Colab, go to **File → Save a copy in Drive**. Now it's your notebook — break things freely.
> Run cells one at a time with **Shift + Enter**. If anything feels stuck, **Runtime → Restart session** and run from the top.
"""),
code(SETUP),
code('''
ilanga.brand.banner(1, "Sawubona! The SA health data landscape", "Phase 1 · Onboarding", minutes=90)
ilanga.brand.ticket(
    "NQ-001", "Ayanda Mthembu", "Lead Data Engineer, Nqaba Health Informatics",
    "Onboarding: map Ilanga District's data landscape",
    "Welcome to the team! Before you touch any analysis, I need you to understand where health data "
    "lives in South Africa and in our client's district. Ilanga is part-way through moving from paper "
    "registers to e-Impilo, and that shapes everything we'll build together.",
    ["You can explain the main public-sector health information systems and what each holds",
     "You know which Ilanga facilities are live on e-Impilo",
     "You've measured how much of 2025's clinical activity was captured digitally, per subdistrict",
     "Your quality gate passes and you've written a short handover note"],
    priority="Onboarding")
'''),
md("""
## A note from your team lead

I'm really glad you're here. Whether you've spent ten years at a clinic counter or ten years writing code, you're
going to be useful on this team — and a little uncomfortable, because health informatics sits exactly where
those two worlds meet.

Here's how we work at Nqaba, and how every module in this programme works:

| You'll see | What it means |
|---|---|
| 🎫 **Ticket** | A real-style request from a client or teammate. It tells you *why* the work matters. |
| 🩺 **Clinic Corner** | Health context, for those of you coming from tech. |
| 💻 **Code Corner** | Code explained line by line, for those of you coming from health. |
| 🤝 **Ubuntu Moment** | *Umuntu ngumuntu ngabantu.* Every row is a person. We pause to remember that. |
| 🌱 🌿 🌳 **Seedling · Sapling · Baobab** | Your exercises, from gentle to stretching. Do what you can; come back for more. |
| 🚦 **Quality gate** | Automated checks — like a real team's CI pipeline — that tell you if your work is ready. |
| 📝 **Handover** | A short note, the way real teams communicate finished work. |

Stuck? Use `ilanga.hint("NQ-001.1")` — hints come in three levels, so you only take as much help as you need.

— *Ayanda*
"""),
md("""
## 📜 Policy Watch — as of 22 September 2026

Health informatics in South Africa is shaped by policy that is still moving. Here's where things stand:

- **National Health Insurance (NHI).** The NHI Act was signed in May 2024 but has **not been brought into operation**.
  In February 2026 the President undertook not to proclaim any of its provisions until the Constitutional Court rules on
  challenges about Parliament's public participation process. The Court heard those cases on 5–7 May 2026 and
  **reserved judgment**.
- **A related ruling.** In May 2026 the Constitutional Court struck down the "certificate of need" provisions
  (sections 36–40 of the *National Health Act*). The Department of Health says this does not affect the NHI Act itself.
- **Digital Health Strategy.** The National Digital Health Strategy 2019–2024 has expired. A 2025–2029 successor
  has been referenced publicly but not yet published.
- **e-Impilo.** The national Department of Health's own electronic medical record (EMR) is being rolled out in primary
  health care, using international interoperability standards like HL7 FHIR. Free State's rollout won a public-sector
  digital innovation award at Africa Tech Week in May 2026.

**Why this matters to you:** whatever happens with NHI, the health system needs the same foundations —
reliable patient identity, electronic records, systems that talk to each other, and trustworthy indicators.
That's exactly what this programme teaches. We build for the foundations, not the headlines.

*Dig deeper:* [National Digital Health Strategy 2019–2024](https://knowledgehub.health.gov.za/elibrary/national-digital-health-strategy-south-africa-2019-2024) ·
[The Emerging SA Digital Health System (NDoH & CSIR, 2024)](https://www.health.gov.za/wp-content/uploads/2025/07/Web-Version-The-Emerging-South-African-Digital-Health-System.pdf)
"""),
md("""
## Part 1 · The South African health system in five minutes

> 🩺 **Clinic Corner — how care is organised**
>
> South Africa has **two sectors**. The **public sector** serves most people — roughly five in six South Africans
> rely on it. The **private sector** is funded mostly through medical schemes (medical aid).
>
> In the public sector, care is organised in **levels**. A patient usually enters at the bottom and is
> **referred up** when they need more specialised care:
>
> **Clinic** (primary health care, mostly nurse-led) → **Community Health Centre (CHC)** → **District hospital**
> → **Regional hospital** → **Tertiary** and **central** hospitals
>
> - The **National Department of Health (NDoH)** sets policy, norms and national systems.
> - **Nine provincial health departments** run most services.
> - Provinces are divided into **health districts** (52 of them), each with sub-districts and facilities.
> - The **National Health Laboratory Service (NHLS)** does almost all public-sector laboratory testing.

Every level of care produces data. A nurse's tick in a clinic register becomes a monthly total, which becomes a
district indicator, which lands in a provincial report, which informs a national budget. **Health informatics is the
discipline of making that journey accurate, safe and useful.**
"""),
md("""
## Part 2 · Your first lines of Python

> 💻 **Code Corner — cells, comments and variables**
>
> - A **code cell** holds Python. Click it and press **Shift + Enter** to run it.
> - Anything after `#` is a **comment**. Python ignores it; humans read it. Good analysts comment generously.
> - A **variable** is a labelled box: `nurses_on_duty = 4` puts the value `4` in a box called `nurses_on_duty`.
> - `print(...)` shows something on screen. The `f"..."` is an **f-string**: anything inside `{curly braces}` gets filled in.
"""),
code('''
# A Monday morning at a busy clinic
clinic = "Mfula Gateway Clinic"
patients_seen_today = 142
nurses_on_duty = 4

patients_per_nurse = patients_seen_today / nurses_on_duty
print(f"{clinic}: {patients_seen_today} patients today, about {patients_per_nurse:.0f} per nurse.")
'''),
md("""
✏️ **Try it:** change `nurses_on_duty` to `3` and run the cell again. That one number is a staffing conversation
a facility manager has every week. Data turns gut feel into evidence.
"""),
md("""
## Part 3 · Where health data lives

South Africa doesn't have *one* health information system — it has many, built at different times for different
programmes. Part of e-Impilo's purpose is to bring more of this together. Let's put the landscape into a table,
the way an analyst would.
"""),
code('''
systems = pd.DataFrame([
    ("e-Impilo", "Electronic medical record for public-sector care, starting with primary health care", "Patient-level", "Public sector (NDoH & provinces)"),
    ("HPRS", "Health Patient Registration System: registers patients and gives each a unique identifier", "Patient-level", "Public sector (NDoH)"),
    ("DHIS", "District Health Information System: monthly routine indicators from every facility", "Aggregate", "Public sector (NDoH & provinces)"),
    ("TIER.Net", "Monitors people living with HIV on antiretroviral therapy (ART)", "Patient-level", "Public sector (NDoH)"),
    ("ETR.Net", "Electronic register for drug-susceptible tuberculosis", "Patient-level", "Public sector (NDoH)"),
    ("EDRWeb", "Register for drug-resistant tuberculosis", "Patient-level", "Public sector (NDoH)"),
    ("NHLS LIS", "Laboratory information system: specimens, tests and results", "Patient-level", "NHLS"),
    ("SVS", "Stock Visibility System: medicine stock levels at clinics", "Facility-level", "Public sector (NDoH)"),
    ("MomConnect", "Mobile messaging platform supporting pregnant women and new mothers", "Patient-level", "Public sector (NDoH)"),
    ("CCMDD", "Chronic medicines dispensed to convenient pick-up points", "Patient-level", "Public sector (NDoH)"),
    ("Medical scheme claims", "Private-sector billing using ICD-10 diagnosis codes and tariff codes", "Patient-level", "Private sector"),
], columns=["system", "what_it_holds", "data_level", "sector"])

systems
'''),
md("""
> 💻 **Code Corner — the DataFrame**
>
> `pd.DataFrame(...)` creates a **DataFrame**: a table with named columns, like a spreadsheet you control with code.
> `pd` is the nickname for **pandas**, Python's workhorse library for tables. You'll use it in every module.
>
> Writing just `systems` on the last line of a cell displays it. No `print` needed.

Now let's *ask the table questions*. Which systems hold information about individual patients?
"""),
code('''
# A "filter": keep only rows where data_level equals "Patient-level"
patient_level = systems[systems["data_level"] == "Patient-level"]
print(f"{len(patient_level)} of {len(systems)} systems hold patient-level data:")
print(", ".join(patient_level["system"]))
'''),
code('''
counts = systems["data_level"].value_counts()

fig, ax = plt.subplots(figsize=(6, 3))
counts.plot.barh(ax=ax, color=[BRAND["teal"], BRAND["ochre"], BRAND["navy"]])
ax.set_xlabel("Number of systems")
ax.set_title("Health information systems by level of data")
plt.show()
'''),
md("""
> 🩺 **Clinic Corner — patient-level versus aggregate**
>
> **Patient-level** data is about one person: *Nomvula, 34, viral load <50 copies/mL on 3 March.*
> **Aggregate** data is a count: *Mfula Gateway Clinic saw 1,204 patients in March.*
>
> For decades, most facilities recorded patient details on paper and sent **only totals** upward to DHIS.
> Electronic records like e-Impilo change that: the totals can be *calculated* from patient records instead of
> tallied by hand. That's more accurate — and it means analysts like you now handle far more sensitive data.
> (Module 4 is all about doing that responsibly.)
"""),
md("""
## Part 4 · Meet Ilanga District

Our client, **Ilanga District Health Services**, is a fictional district in KwaZulu-Natal. It has three sub-districts:

| Sub-district | Setting | What to expect |
|---|---|---|
| **Lwandle** | Urban, coastal | Regional hospital, most e-Impilo sites, fastest lab turnaround |
| **Mfula** | Peri-urban | Mix of digital and paper facilities |
| **Ntaba** | Rural, inland | Mobile clinic, long distances, mostly paper |

The data comes from our shared platform, the `ilanga` package. Every module uses the same district, so your
understanding compounds as you go.
"""),
code('''
district = ilanga.load_district()   # the curated (clean) layer - we meet the messy "raw" layer in Module 5
district
'''),
code('''
district.summary()
'''),
code('''
district.facilities
'''),
code('''
fac = district.facilities[district.facilities["facility_type"] != "Laboratory"]
colours = {"Lwandle": BRAND["teal"], "Mfula": BRAND["ochre"], "Ntaba": BRAND["navy"]}

fig, ax = plt.subplots(figsize=(8, 6))
for _, f in fac.iterrows():
    digital = f["emr_system"] == "e-Impilo"
    ax.scatter(f["longitude"], f["latitude"], s=220 if "Hospital" in f["facility_type"] else 110,
               color=colours[f["subdistrict"]] if digital else "white",
               edgecolor=colours[f["subdistrict"]], linewidth=2.5, zorder=3)
    ax.annotate(f["facility_name"].replace(" Clinic", ""), (f["longitude"], f["latitude"]),
                xytext=(6, 6), textcoords="offset points", fontsize=8)
ax.set_title("Ilanga District facilities  (filled = live on e-Impilo, hollow = paper)")
ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
for name, c in colours.items():
    ax.scatter([], [], color=c, label=name)
ax.legend(title="Sub-district", loc="lower left")
plt.show()
'''),
md("""
> 🤝 **Ubuntu Moment — the digital divide is a care divide**
>
> Look at the map. The rural sub-district, Ntaba, is mostly hollow circles. That isn't a coincidence in real life
> either: connectivity, electricity and staffing all make digitisation harder in rural areas.
>
> When a patient from Ntaba is referred to the regional hospital, their paper history may not travel with them.
> When we build dashboards from digital data only, **Ntaba's patients can quietly disappear from the evidence**.
> Good informaticians always ask: *whose data is missing, and what does that do to our conclusions?*
"""),
code('''
# How is clinical activity captured across the whole district?
district.encounters["capture_mode"].value_counts(normalize=True).mul(100).round(1)
'''),
md("""
## 🎯 Your turn

Your ticket asks for three things. Write your code where you see `# 👈 your code here`.
If you're stuck, run `ilanga.hint("NQ-001.1")` (then level 2, then 3) in a new cell.

### 🌱 Seedling — how many facilities are live on e-Impilo?
Store the number (an integer) in `n_emr_live`.
"""),
ex('''
n_emr_live = None   # 👈 your code here
print(n_emr_live)
''', '''
n_emr_live = int(district.facilities["emr_go_live"].notna().sum())
print(n_emr_live)
'''),
md("""
### 🌿 Sapling — which sub-district has the most registered patients?
Store the sub-district's name (text) in `biggest_subdistrict`.
"""),
ex('''
biggest_subdistrict = None   # 👈 your code here
print(biggest_subdistrict)
''', '''
biggest_subdistrict = district.patients["subdistrict"].value_counts().idxmax()
print(biggest_subdistrict)
'''),
md("""
### 🌳 Baobab — what share of 2025 visits was captured digitally, per sub-district?
Store a pandas **Series** indexed by sub-district, with values as **percentages (0–100)**, in `digital_share_2025`.

*Why it matters:* this single table tells the district manager where e-Impilo support should go next.
"""),
ex('''
digital_share_2025 = None   # 👈 your code here
digital_share_2025
''', '''
enc25 = district.encounters[district.encounters["encounter_date"].dt.year == 2025]
enc25 = enc25.merge(district.facilities[["facility_id", "subdistrict"]], on="facility_id")
digital_share_2025 = enc25.groupby("subdistrict")["capture_mode"].apply(
    lambda s: (s == "Digital (e-Impilo)").mean() * 100)
digital_share_2025.round(1)
'''),
md("""
## 🚦 Quality gate
Run the checks. Anything that isn't ready comes back with a note — fix, re-run, repeat. That loop *is* the job.
"""),
code('''
passed = ilanga.tickets.check_nq001(n_emr_live, biggest_subdistrict, digital_share_2025)
'''),
md("""
## 📝 Handover note
Double-click this cell and replace the italics with your own words. Three to five sentences — the way you'd
post it in the team channel when you close the ticket.

> **NQ-001 — done.**
> *What I found: …*
> *What surprised me: …*
> *What I'd flag to the district manager: …*
"""),
md("""
## 🧭 Career Lens
The skills in this module — knowing which system holds what, and being able to query it — are the daily bread of
**facility and district information officers**, **health information managers**, and **monitoring & evaluation
(M&E) officers** at NGOs and implementing partners. Informatics roles at the NHLS, provincial departments and health
tech companies expect this landscape knowledge on day one.

## 📚 Glossary
**PHC** – primary health care · **CHC** – community health centre · **EMR** – electronic medical record ·
**HPRS** – Health Patient Registration System · **DHIS** – District Health Information System ·
**NHLS** – National Health Laboratory Service · **ART** – antiretroviral therapy · **NHI** – National Health Insurance ·
**Aggregate data** – counts and totals rather than individual records

## ✅ Checkpoint
<details><summary>1. A clinic sends DHIS "1,204 visits in March". Is that patient-level or aggregate?</summary>
Aggregate — it's a total, not a record about one person.</details>
<details><summary>2. Name the national system that registers patients and issues a unique identifier.</summary>
HPRS, the Health Patient Registration System.</details>
<details><summary>3. Why might a district dashboard built only on e-Impilo data be misleading?</summary>
Facilities still on paper (often rural) are under-represented, so their patients' needs can be invisible.</details>
<details><summary>4. As of September 2026, is the NHI Act in operation?</summary>
No. It is law, but its provisions have not been proclaimed, pending a Constitutional Court judgment.</details>

**Next up → Module 02:** Sister Nomvula needs her monthly headcount report, and you're going to learn Python and
pandas by building it.
"""),
md(FOOTER),
]

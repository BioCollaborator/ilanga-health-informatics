from nb import md, code, ex, SETUP, FOOTER, colab_badge

PATH = "notebooks/phase3_analytics/M09_routine_indicators_cascades.ipynb"

CELLS = [
md(f"""
# Module 09 · Numbers that run a district — routine indicators and care cascades
**BioCollaborator Health Informatics Programme** · Phase 3: Analytics · *Innovate Naturally*

{colab_badge(PATH)}

> **File → Save a copy in Drive**, then run cells top to bottom with **Shift + Enter**.
"""),
code(SETUP),
code('''
ilanga.brand.banner(9, "Numbers that run a district: indicators & cascades", "Phase 3 · Analytics", minutes=150)
ilanga.brand.ticket(
    "NQ-009", "Sipho Ngcobo", "District Information Manager, Ilanga District Health Services",
    "Evidence pack for the quarterly district health review",
    "The quarterly review is in two weeks. Before anyone argues about performance, I want to know whether our "
    "routine data can be trusted: are facilities reporting, and do the numbers they report match what actually "
    "happened? Then I need the HIV care cascade, calculated one consistent way, so programme managers stop "
    "quoting different numbers for the same thing.",
    ["Reporting completeness for 2025, by sub-district",
     "Reported versus computed headcount for every PHC facility, with the gap as a percentage",
     "The HIV care cascade as at 31 December 2025, using the district's definitions",
     "A one-paragraph interpretation for programme managers"],
    priority="High - quarterly review")
'''),
md("""
## Part 1 · Anatomy of an indicator

An indicator is not just a number — it's a **definition**. Two analysts with different definitions will produce
different numbers from the same data, and both will be "right". South Africa manages this through standard indicator
definitions for routine health data. The Ilanga definitions below are modelled on the same conventions.

| Element | Example: PHC utilisation rate |
|---|---|
| **Name** | PHC utilisation rate |
| **Definition** | Average number of PHC visits per person per year |
| **Numerator** | PHC headcount (all visits) in the period |
| **Denominator** | Catchment population |
| **Formula** | Numerator ÷ denominator, annualised |
| **Data source** | Facility monthly reports (numerator), population estimates (denominator) |
| **Frequency** | Monthly, reviewed quarterly |
| **Interpretation** | Higher suggests better access — or more illness. Always read it in context. |
"""),
code('''
d = ilanga.load_district()
fsub = d.facilities.set_index("facility_id")["subdistrict"]

enc25 = d.encounters[d.encounters["encounter_date"].dt.year == 2025]
headcount = enc25["facility_id"].map(fsub).value_counts()
population = d.wards.groupby("subdistrict")["estimated_population"].sum()

utilisation = pd.DataFrame({"headcount_2025": headcount, "population": population})
utilisation["visits_per_person"] = (utilisation["headcount_2025"] / utilisation["population"]).round(2)
utilisation
'''),
md("""
> 🩺 **Clinic Corner — the denominator decides the story**
>
> Ntaba's utilisation is lowest. Is that because people are healthier, or because the nearest clinic is 10 km away?
> The indicator can't tell you. And if the population estimate is wrong — common in rural areas and informal
> settlements — every rate built on it is wrong too. **Always ask where the denominator came from.**

## Part 2 · Routine aggregate data

Every PHC facility submits a **monthly report** of key data elements. e-Impilo facilities produce theirs
automatically from patient records. Paper facilities **tally** registers by hand — with all the errors that come
with tired eyes at month-end.
"""),
code('''
dh = d.dhis_monthly
print(dh["data_element"].unique())
dh.head(8)
'''),
code('''
# One data element as a facility x month grid - the classic view of routine data
grid = dh[dh["data_element"] == "PHC headcount total"].pivot(index="facility_id", columns="period", values="reported_value")
grid.iloc[:, -8:]   # the last 8 months; blanks are reports that never arrived
'''),
md("""
## Part 3 · Can we trust the routine data?

Before interpreting any indicator, check three things:

1. **Completeness** — did every facility report every month?
2. **Timeliness** — did reports arrive by the deadline (here, the **10th of the following month**)?
3. **Accuracy / concordance** — does the reported number match the source records?

South African districts run **data verification** exercises that compare reported totals with registers. With
e-Impilo patient-level data, we can do it for every facility, every month.

Here's timeliness — completeness and concordance are yours.
"""),
code('''
reports = dh[dh["data_element"] == "PHC headcount total"].copy()
due = pd.to_datetime(reports["period"] + "-01") + pd.offsets.MonthBegin(1) + pd.Timedelta(days=9)
reports["on_time"] = reports["submitted_date"] <= due
reports["subdistrict"] = reports["facility_id"].map(fsub)

timeliness = reports[reports["period"].str.startswith("2025")].groupby(["subdistrict", "source"])["on_time"].mean().mul(100).round(1)
timeliness.unstack()
'''),
md("""
### 🌱 Seedling — reporting completeness, 2025
Build `reporting_completeness`: a Series indexed by sub-district with the **percentage** of expected 2025 monthly
reports that were received. Expected reports = PHC facilities (Clinics, CHCs and the Mobile Clinic) × 12 months.
Hints: `ilanga.hint("NQ-009.1")`.
"""),
ex('''
reporting_completeness = None   # 👈 your code here
reporting_completeness
''', '''
phc = d.facilities[d.facilities["facility_type"].isin(["Clinic", "CHC", "Mobile Clinic"])]
expected = phc.groupby("subdistrict").size() * 12
received = reports[reports["period"].str.startswith("2025")].groupby("subdistrict").size()
reporting_completeness = (received / expected * 100).round(1)
reporting_completeness
'''),
md("""
### 🌿 Sapling — reported versus computed headcount
Build `concordance_2025`: one row per PHC facility with columns `facility_id`, `reported`, `computed` and
`pct_difference`, for **2025 months that the facility reported**. `computed` comes from counting encounters.
`pct_difference = 100 × (reported − computed) ÷ computed`. Hints: `ilanga.hint("NQ-009.2")`.
"""),
ex('''
concordance_2025 = None   # 👈 your code here
concordance_2025
''', '''
e = enc25.assign(period=enc25["encounter_date"].dt.strftime("%Y-%m"))
computed = e.groupby(["facility_id", "period"]).size().rename("computed").reset_index()
rep25 = reports[reports["period"].str.startswith("2025")][["facility_id", "period", "reported_value"]]
m = rep25.merge(computed, on=["facility_id", "period"], how="left").fillna({"computed": 0})
concordance_2025 = (m.groupby("facility_id")[["reported_value", "computed"]].sum()
                    .rename(columns={"reported_value": "reported"}).reset_index())
concordance_2025["pct_difference"] = (100 * (concordance_2025["reported"] - concordance_2025["computed"])
                                      / concordance_2025["computed"]).round(2)
concordance_2025.sort_values("pct_difference", key=abs, ascending=False)
'''),
md("""
Look at the facility with the biggest gap. Now look at its monthly numbers — can you spot what kind of error caused it?
*(Hint: think about how a tired person copies "1204" onto a form.)*

> 🤝 **Ubuntu Moment — errors are system problems, not people problems**
>
> It's tempting to blame the clerk. But a mobile clinic nurse tallying hundreds of visits by hand, at month-end, on
> the back seat of a vehicle, *will* make errors. The fix is better systems — simpler forms, digital capture,
> feedback loops — not blame. Good informaticians protect the people at the bottom of the data chain.

## Part 4 · Care cascades

A **cascade** follows a group of people through the steps of care and shows where they drop off. UNAIDS's
**95-95-95** targets frame HIV care this way: 95% of people living with HIV know their status, 95% of those are on
treatment, and 95% of those are virally suppressed.

Our cascade is **clinic-based**: we can only see people already diagnosed and registered. The first "95" (people
who don't know their status) is invisible in facility data — it needs surveys.

First, a TB example: **treatment success** for the 2024 cohort.
"""),
code('''
tb = d.conditions[d.conditions["condition"] == "Tuberculosis"]
cohort_2024 = tb[tb["onset_date"].dt.year == 2024]
outcomes = cohort_2024["status"].value_counts()
success = outcomes.get("Cured", 0) + outcomes.get("Treatment completed", 0)
evaluated = outcomes.drop("On treatment", errors="ignore").sum()
print(outcomes.to_string(), "\\n")
print(f"TB treatment success, 2024 cohort: {success}/{evaluated} = {100 * success / evaluated:.1f}%")
'''),
md("""
> 🩺 **Clinic Corner — cohorts and outcomes**
>
> TB outcomes are reported for **cohorts**: everyone who started treatment in a given period, followed until they
> finish. **Treatment success = cured + treatment completed.** Loss to follow-up and death are the outcomes
> programmes work hardest to prevent. Because treatment takes about six months, a 2025 cohort can't be fully
> evaluated until well into 2026.

### 🌳 Baobab — the HIV care cascade as at 31 December 2025
Build `hiv_cascade`: a DataFrame with columns `step` and `count`, four rows in this order:

1. **Living with HIV, in care** — HIV records whose status is not *Died* or *Transferred out*
2. **On ART** — of those, status *Active*
3. **Viral load done (2025)** — of those on ART who started **on or before 30 June 2025** (so they're due for a
   viral load), the number with at least one viral load collected in 2025
4. **Virally suppressed (<1000)** — of those with a 2025 viral load, the number whose **latest** 2025 result is below
   the detection limit or under 1,000 copies/mL

Then chart it, with each step's percentage of the previous step. Hints: `ilanga.hint("NQ-009.3")`.
"""),
ex('''
hiv_cascade = None   # 👈 your code here
hiv_cascade
''', '''
c = d.conditions[d.conditions["condition"] == "HIV"]
in_care = c[~c["status"].isin(["Died", "Transferred out"])]
on_art = in_care[in_care["status"] == "Active"]
eligible = on_art[on_art["art_start_date"] <= "2025-06-30"]

vl = d.lab_results[(d.lab_results["test_code"] == "VL") & (d.lab_results["collected_at"].dt.year == 2025)]
vl = vl[vl["patient_id"].isin(eligible["patient_id"])]
latest = vl.sort_values("collected_at").groupby("patient_id").tail(1)
suppressed = latest["below_detection_limit"] | (latest["result_numeric"] < 1000)

hiv_cascade = pd.DataFrame({
    "step": ["Living with HIV, in care", "On ART", "Viral load done (2025)", "Virally suppressed (<1000)"],
    "count": [len(in_care), len(on_art), latest["patient_id"].nunique(), int(suppressed.sum())]})
hiv_cascade["pct_of_previous"] = (100 * hiv_cascade["count"] / hiv_cascade["count"].shift(1)).round(1)

fig, ax = plt.subplots(figsize=(9, 3.8))
ax.bar(hiv_cascade["step"], hiv_cascade["count"], color=[BRAND["navy"], BRAND["teal"], BRAND["teal"], BRAND["ochre"]])
for i, r in hiv_cascade.iterrows():
    label = f"{r['count']:,}" + ("" if pd.isna(r["pct_of_previous"]) else f"\\n{r['pct_of_previous']}%")
    ax.text(i, r["count"], label, ha="center", va="bottom", fontsize=9)
ax.set_title("Ilanga District HIV care cascade, 31 Dec 2025"); ax.set_ylabel("People")
plt.xticks(fontsize=8); plt.show()
hiv_cascade
'''),
md("""
> 🩺 **Clinic Corner — the biggest drop is the story**
>
> Look for the largest fall between steps. Here, a large share of people "in care" are no longer active on
> treatment — mostly **lost to follow-up**. That's where programme effort should go: tracing, differentiated care,
> fewer barriers to collecting medicines. Module 14 will try to *predict* who is at risk of dropping out.

## 🚦 Quality gate
"""),
code('''
passed = ilanga.tickets.check_nq009(reporting_completeness, concordance_2025, hiv_cascade)
'''),
md("""
## 📝 Handover note — for programme managers
> **NQ-009 — done. For: Sipho Ngcobo.**
> *Data quality: reporting completeness was … ; the largest reported-vs-computed gap was at … (…%), probably caused by …*
> *HIV cascade: of … people in care, …% are active on ART, …% of eligible patients had a 2025 viral load, and …%
> of those tested were suppressed. The biggest drop-off is …*
> *Caveat: this cascade only includes people already diagnosed and registered.*

## 🧭 Career Lens
**Monitoring and evaluation (M&E) officers**, **health information officers** and **programme data analysts** live
in indicators, cascades and data verification. Implementing partners, provincial departments and NGOs across
South Africa hire for exactly these skills, and being able to explain *why* a number might be wrong is what makes
you senior.

## 📚 Glossary
**Indicator** – a defined measure with numerator and denominator · **Data element** – a raw count collected
routinely · **Completeness / timeliness / concordance** – reports received / on time / matching source · **Data
verification** – checking reported numbers against source records · **Cascade** – people remaining at each step of
care · **Cohort** – a group followed from a common starting point · **Treatment success** – cured + completed

## ✅ Checkpoint
<details><summary>1. Why compare only months that a facility actually reported?</summary>Otherwise a missing report looks like a massive undercount, mixing a completeness problem into an accuracy measure.</details>
<details><summary>2. Why can't a clinic-based cascade measure the first 95?</summary>People who don't know their HIV status never appear in facility records; that step needs population surveys.</details>
<details><summary>3. What is TB treatment success?</summary>The proportion of an evaluated cohort who were cured or completed treatment.</details>

**Next up → Module 10:** From counting to *inference*. Confidence intervals, risk ratios, retention curves — and a
real-time outbreak hunt in the weekly surveillance data.
"""),
md(FOOTER),
]

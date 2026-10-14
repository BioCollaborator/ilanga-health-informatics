from nb import md, code, ex, SETUP, FOOTER, colab_badge

PATH = "notebooks/phase4_advanced/M16_capstone_eimpilo_readiness.ipynb"

CELLS = [
md(f"""
# Module 16 · Capstone — the Ilanga District digital health readiness report
**BioCollaborator Health Informatics Programme** · Phase 4: Advanced & Capstone · *Innovate Naturally*

{colab_badge(PATH)}

> **File → Save a copy in Drive**, then run cells top to bottom with **Shift + Enter**.
> This is the final module. Give it a proper session — it uses everything you've learned.
"""),
code(SETUP),
code('''
from ilanga.dashboard import build_dashboard, fig_to_img, rag
from ilanga.tickets_phase4 import REPORT_SECTIONS

ilanga.brand.banner(16, "Capstone: the district readiness report", "Phase 4 · Advanced & Capstone", minutes=240)
ilanga.brand.ticket(
    "NQ-016", "Mrs Nokuthula Cele", "District Manager, Ilanga District Health Services",
    "Digital health readiness report for the provincial review",
    "The province is deciding where to invest next in e-Impilo, and they've asked every district for an evidence-based "
    "readiness assessment. You've spent this year inside our data - nobody knows it better. I want one report: which "
    "facilities are ready, which need work and what specifically to fix. Be honest about our weaknesses; the province "
    "respects a district that knows its own gaps. And I need to be able to defend every number in the room.",
    ["A facility-level readiness scorecard against five agreed criteria",
     "A written report with six sections, defensible and specific",
     "A one-page dashboard for the provincial meeting",
     "A governance appendix: what we'd need before any of this touches real patient data"],
    priority="Critical - provincial review")
'''),
md("""
## Your capstone brief

This is not a new topic. It's your whole year, applied to one real question:

> **Is Ilanga District ready to rely on e-Impilo data for clinical care and reporting — and if not, what exactly
> must change?**

| Module | What you bring to this report |
|---|---|
| 01–04 | The SA system, pandas, synthetic data ethics, POPIA governance |
| 05–08 | Data quality, terminologies, interoperability, a tested warehouse |
| 09–12 | Indicators, epidemiology, dashboards, laboratory informatics |
| 13–15 | Referral networks, risk prediction, clinical NLP |

### The five readiness criteria

Agreed with Mrs Cele and the provincial team. A facility meets a criterion if it clears the threshold:

| # | Criterion | Column | Threshold | Why it matters |
|---|---|---|---|---|
| 1 | Digital capture | `digital_capture_pct` | ≥ 90% | Paper records can't feed a shared EMR |
| 2 | Reporting completeness | `reporting_completeness_pct` | ≥ 95% | Missing months break every indicator |
| 3 | Data accuracy | `concordance_gap_pct` | ≤ 2% | Reported numbers must match reality |
| 4 | Viral load coverage | `vl_done_pct` | ≥ 90% | Monitoring people on treatment |
| 5 | Results acted on | `high_vl_followup_pct` | ≥ 50% | A result that changes nothing is waste |

**Readiness rating:** 4–5 criteria = *Ready* · exactly 3 = *Nearly ready* · 0–2 = *Not ready*

> 🤝 **Ubuntu Moment — write for the people in the room, and the people who aren't**
>
> Your report will be read by managers who decide where money goes. It's also, indirectly, about the woman in Ntaba
> who walks 10 km with a sick child, and the clerk tallying registers at month-end. Write so that both the province
> and the people at the bottom of the data chain would recognise the truth in it.

## Part 1 · Build the scorecard

### 🎓 The scorecard
Build `readiness`: a DataFrame **indexed by `facility_id`** covering the **10 PHC facilities** (Clinics, CHCs and the
Mobile Clinic — not hospitals or the laboratory), with these columns:

| Column | Definition (2025) |
|---|---|
| `digital_capture_pct` | % of the facility's 2025 visits with `capture_mode == "Digital (e-Impilo)"` |
| `reporting_completeness_pct` | monthly reports received ÷ 12 × 100 (`PHC headcount total`) |
| `concordance_gap_pct` | **absolute** % difference between reported and computed headcount (Module 9) |
| `vl_done_pct` | of patients whose **home facility** this is, who are active on ART with `art_start_date ≤ 2025-06-30`: % with a 2025 viral load |
| `high_vl_followup_pct` | of high viral loads **ordered by** this facility (Module 12's Jan–Sep window): % seen within 28 days |
| `criteria_met` | how many of the five thresholds are met (a missing value counts as not met) |
| `readiness` | `Ready` / `Nearly ready` / `Not ready` |

Hints: `ilanga.hint("NQ-016.1")`.
"""),
ex('''
d = ilanga.load_district()
readiness = None   # 👈 your code here
readiness
''', '''
d = ilanga.load_district()
PHC = ["Clinic", "CHC", "Mobile Clinic"]
fac = d.facilities[d.facilities["facility_type"].isin(PHC)].set_index("facility_id")

# 1. Digital capture
e25 = d.encounters[d.encounters["encounter_date"].dt.year == 2025]
digital = (e25["capture_mode"] == "Digital (e-Impilo)").groupby(e25["facility_id"]).mean() * 100

# 2. Reporting completeness
rep = d.dhis_monthly[(d.dhis_monthly["data_element"] == "PHC headcount total")
                     & d.dhis_monthly["period"].str.startswith("2025")]
completeness = rep.groupby("facility_id").size() / 12 * 100

# 3. Concordance gap (Module 9)
computed = e25.assign(period=e25["encounter_date"].dt.strftime("%Y-%m")).groupby(["facility_id", "period"]).size().rename("computed")
m = rep[["facility_id", "period", "reported_value"]].merge(computed.reset_index(), on=["facility_id", "period"], how="left").fillna({"computed": 0})
agg = m.groupby("facility_id")[["reported_value", "computed"]].sum()
gap = (100 * (agg["reported_value"] - agg["computed"]) / agg["computed"]).abs()

# 4. Viral load coverage
c = d.conditions
act = c[(c["condition"] == "HIV") & (c["status"] == "Active") & (c["art_start_date"] <= "2025-06-30")]
act = act.assign(home=act["patient_id"].map(d.patients.set_index("patient_id")["home_facility_id"]))
vl25 = set(d.lab_results.loc[(d.lab_results["test_code"] == "VL") & (d.lab_results["collected_at"].dt.year == 2025), "patient_id"])
vl_done = act["patient_id"].isin(vl25).groupby(act["home"]).mean() * 100

# 5. High viral loads acted on (Module 12)
hv = d.lab_results[(d.lab_results["test_code"] == "VL") & (d.lab_results["result_numeric"] >= 1000)
                   & d.lab_results["collected_at"].between("2025-01-01", "2025-09-30 23:59")]
j = hv[["specimen_id", "patient_id", "reported_at", "ordering_facility_id"]].merge(
    d.encounters[["patient_id", "encounter_date"]], on="patient_id", how="left")
j["hit"] = (j["encounter_date"] - j["reported_at"].dt.normalize()).dt.days.between(1, 28)
seen = j.groupby("specimen_id")["hit"].any()
hv = hv.assign(seen=hv["specimen_id"].map(seen).fillna(False))
followup = hv.groupby("ordering_facility_id")["seen"].mean() * 100

readiness = pd.DataFrame({
    "digital_capture_pct": digital, "reporting_completeness_pct": completeness,
    "concordance_gap_pct": gap, "vl_done_pct": vl_done, "high_vl_followup_pct": followup}).reindex(fac.index)

met = pd.DataFrame({
    "a": readiness["digital_capture_pct"] >= 90, "b": readiness["reporting_completeness_pct"] >= 95,
    "c": readiness["concordance_gap_pct"] <= 2, "d": readiness["vl_done_pct"] >= 90,
    "e": readiness["high_vl_followup_pct"] >= 50})
readiness["criteria_met"] = met.sum(axis=1)
readiness["readiness"] = np.select([readiness["criteria_met"] >= 4, readiness["criteria_met"] == 3],
                                   ["Ready", "Nearly ready"], "Not ready")
readiness.round(1)
'''),
code('''
if readiness is not None:
    names = d.facilities.set_index("facility_id")["facility_name"]
    colours = {"Ready": "#2E7D5B", "Nearly ready": "#C98A1B", "Not ready": "#B23A2E"}
    order = readiness.sort_values("criteria_met")

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh([names[i] for i in order.index], order["criteria_met"],
            color=[colours[r] for r in order["readiness"]])
    ax.set_xlim(0, 5); ax.set_xlabel("Readiness criteria met (of 5)")
    ax.set_title("e-Impilo readiness by facility, Ilanga District, 2025")
    for i, (idx, row) in enumerate(order.iterrows()):
        ax.text(row["criteria_met"] + 0.08, i, row["readiness"], va="center", fontsize=8)
    readiness_chart = fig
    plt.show()
    display(readiness["readiness"].value_counts())
'''),
md("""
## Part 2 · Diagnose, don't just score

A scorecard says *what*. A report says *why* and *what to do*. Use the cells below to dig into the pattern — then
draw your own conclusions.
"""),
code('''
if readiness is not None:
    view = readiness.join(d.facilities.set_index("facility_id")[["facility_name", "subdistrict", "facility_type", "emr_go_live"]])
    display(view.groupby("subdistrict")[["digital_capture_pct", "reporting_completeness_pct", "concordance_gap_pct",
                                          "vl_done_pct", "high_vl_followup_pct", "criteria_met"]].mean().round(1))

    failing = {
        "1. Digital capture < 90%": (readiness["digital_capture_pct"] < 90).sum(),
        "2. Reporting completeness < 95%": (readiness["reporting_completeness_pct"] < 95).sum(),
        "3. Concordance gap > 2%": (readiness["concordance_gap_pct"] > 2).sum(),
        "4. Viral load coverage < 90%": (readiness["vl_done_pct"] < 90).sum(),
        "5. Follow-up < 50%": (readiness["high_vl_followup_pct"] < 50).sum(),
    }
    print("Facilities failing each criterion (of 10):")
    for k, v in failing.items():
        print(f"  {k:<34} {v}")
'''),
md("""
> 🩺 **Clinic Corner — look for the criterion that fails everywhere**
>
> When *every* facility fails the same criterion, it isn't a facility problem — it's a **system** problem, and no
> amount of facility-level effort will fix it. That distinction is the most valuable thing in your report, because
> it tells the province whether to fund training, hardware, or a change in how results reach clinicians.
"""),
code('''
# Supporting evidence you may want to cite - reuse your earlier modules freely
if readiness is not None:
    fsub = d.facilities.set_index("facility_id")["subdistrict"]
    l = d.lab_results[d.lab_results["collected_at"].dt.year == 2025]
    tat = pd.DataFrame({
        "transport_h": ((l["received_at"] - l["collected_at"]).dt.total_seconds() / 3600),
        "lab_h": ((l["reported_at"] - l["received_at"]).dt.total_seconds() / 3600),
        "subdistrict": l["ordering_facility_id"].map(fsub)}).groupby("subdistrict").median().round(1)
    ref = d.referrals[d.referrals["referral_date"].dt.year == 2025]
    arrival = (ref["outcome"] == "Seen").groupby(ref["from_facility_id"].map(fsub)).mean().mul(100).round(1)
    print("Median lab turnaround (hours), 2025:"); display(tat)
    print("Referral arrival rate (%), 2025:"); display(arrival.rename("arrival_%"))
'''),
md("""
## Part 3 · Write the report

Write `capstone_report.md` with these six headings, exactly as `##` markdown headings:

1. `## Executive summary` — the answer in five sentences, with your headline numbers
2. `## Data quality` — completeness, timeliness, concordance; which facilities and why
3. `## Clinical performance` — the HIV cascade, viral load coverage, follow-up of high results
4. `## Access` — who lives far from care; referral arrival; the urban–rural gap
5. `## Governance` — POPIA, de-identification, access control, what's needed before real data
6. `## Recommendations` — specific, prioritised, each one naming *who* does *what*

**Minimum 400 words.** Write it in your own voice, for Mrs Cele to defend in a provincial meeting. Every number must
be one you can trace back to a calculation in your notebooks.

> 💻 **Code Corner — writing a file from Python**
>
> Edit the text between the triple quotes, run the cell, and the file is written into your Colab session. You can
> also write your report in a text editor and upload it — the quality gate just reads `capstone_report.md`.
"""),
ex('''
report = """
# Ilanga District — Digital Health Readiness Report 2025
Prepared by: [your name], Nqaba Health Informatics
Prepared for: Mrs Nokuthula Cele, District Manager

## Executive summary
👈 your report here (replace this and every section below)

## Data quality

## Clinical performance

## Access

## Governance

## Recommendations
"""

with open("capstone_report.md", "w", encoding="utf-8") as fh:
    fh.write(report)
print(f"Saved capstone_report.md ({len(report.split())} words)")
''', '''
r = readiness
ready_n = (r["readiness"] == "Ready").sum()
worst_gap = r["concordance_gap_pct"].idxmax()
names = d.facilities.set_index("facility_id")["facility_name"]

report = f"""
# Ilanga District — Digital Health Readiness Report 2025
Prepared by: Analyst, Nqaba Health Informatics
Prepared for: Mrs Nokuthula Cele, District Manager
Data: Ilanga District synthetic dataset v{ilanga.__version__}, calendar year 2025

## Executive summary
Ilanga District is **partially ready** to rely on e-Impilo data. Of our ten primary health care facilities,
{ready_n} meet at least four of the five agreed readiness criteria, {(r["readiness"] == "Nearly ready").sum()} meet three,
and {(r["readiness"] == "Not ready").sum()} meet two or fewer. The binding constraint is not staff effort: our
facilities report reliably ({r["reporting_completeness_pct"].mean():.0f}% completeness on average) and our data is
broadly accurate (median concordance gap {r["concordance_gap_pct"].median():.1f}%). The two system-wide failures are
**digital capture**, where {(r["digital_capture_pct"] < 90).sum()} of 10 facilities fall below 90%, and
**acting on results**, where every facility falls below the 50% threshold for seeing patients within 28 days of a
high viral load. We recommend the province fund e-Impilo rollout to the remaining paper facilities and, separately,
a results-triggered recall process that no amount of digitisation will deliver on its own.

## Data quality
Reporting completeness averaged {r["reporting_completeness_pct"].mean():.0f}% across the district in 2025, with the
lowest performance in Ntaba sub-district, where distance and connectivity make month-end submission harder.
Accuracy is good overall: {(r["concordance_gap_pct"] <= 2).sum()} of 10 facilities report headcounts within 2% of
what their encounter records show. The exception is {names[worst_gap]}, with a
{r.loc[worst_gap, "concordance_gap_pct"]:.0f}% gap. Inspection of its monthly submissions shows a digit
transposition in a manual tally rather than systematic over-reporting — a predictable consequence of hand-counting
hundreds of visits at month-end, and an argument for digital capture rather than for retraining the clerk.
Facilities live on e-Impilo show no concordance gap at all, because their totals are computed rather than counted.

## Clinical performance
Viral load coverage is strong: every facility tests at least {r["vl_done_pct"].min():.0f}% of eligible patients
active on ART, and the district average is {r["vl_done_pct"].mean():.0f}%. The district HIV cascade shows the real
weakness elsewhere — a substantial share of people recorded as in care are no longer active on treatment, mostly
lost to follow-up. Follow-up of abnormal results is the district's single worst indicator: only
{r["high_vl_followup_pct"].mean():.0f}% of patients with a viral load above 1,000 copies/mL were seen within 28 days
of the result being reported. We are detecting treatment failure reliably and then not acting on it.

## Access
Access is sharply unequal. Roughly 15,000 residents live in wards more than 5 km from any PHC facility, almost all
of them in rural Ntaba, where the furthest ward is over 25 km from care. This is not only a travel burden: median
laboratory turnaround in Ntaba is roughly double Lwandle's, driven almost entirely by specimen transport rather than
laboratory processing, and Ntaba also has the district's highest specimen rejection rate, largely from specimens
exceeding stability time in transit. Referral arrival rates follow the same pattern, with the lowest arrival rates
on pathways originating in Ntaba. Distance compounds through every part of the system.

## Governance
Nothing in this report used identifiable data: the reporting warehouse holds no names, ID numbers, addresses or
contact details, in line with POPIA's processing limitation principle. Before any of this analysis touches real
patient records, the district requires: a designated information officer accountable for health data; documented
lawful basis and purpose specification for each data use; keyed pseudonymisation and k-anonymity checks for any
research extract; role-based access with audit logging; and research ethics and provincial approval for secondary
use. Any predictive model must be governed as decision support only, with human review, given POPIA's protections
against decisions based solely on automated processing.

## Recommendations
1. **Province: fund e-Impilo rollout** to the {(r["digital_capture_pct"] < 90).sum()} facilities still on paper,
   prioritising Ntaba sub-district. This single intervention addresses criteria 1, 2 and 3 simultaneously.
2. **District clinical governance (Dr Naidoo): implement a results-triggered recall list.** High viral load results
   must generate a same-week recall rather than waiting for the next routine appointment. This is the highest-impact
   change available and does not depend on new technology.
3. **District management (Mrs Cele): extend the mobile clinic route** to the wards more than 5 km from care, and
   review specimen transport scheduling in Ntaba to reduce stability-time rejections.
4. **Laboratory (Ms Khumalo): report total turnaround time alongside lab-controlled turnaround** so that transport
   delays are visible to the people who can fix them.
5. **Information office: complete the governance checklist above** before any real-data analysis, and formalise the
   indicator definitions used here so that the district and province compute the same numbers.
"""

with open("capstone_report.md", "w", encoding="utf-8") as fh:
    fh.write(report)
print(f"Saved capstone_report.md ({len(report.split())} words)")
'''),
md("""
## Part 4 · The dashboard for the meeting
"""),
code('''
if readiness is not None:
    kpis = [
        {"label": "Facilities ready", "value": f"{ready_n}/10", "unit": "", "status": rag(ready_n, 7, 4), "subdistrict": "All"},
        {"label": "Digital capture", "value": f"{readiness['digital_capture_pct'].mean():.0f}", "unit": "%",
         "status": rag(readiness["digital_capture_pct"].mean(), 90, 60), "subdistrict": "All"},
        {"label": "Reporting completeness", "value": f"{readiness['reporting_completeness_pct'].mean():.0f}", "unit": "%",
         "status": rag(readiness["reporting_completeness_pct"].mean(), 95, 90), "subdistrict": "All"},
        {"label": "Viral load coverage", "value": f"{readiness['vl_done_pct'].mean():.0f}", "unit": "%",
         "status": rag(readiness["vl_done_pct"].mean(), 90, 80), "subdistrict": "All"},
        {"label": "High VL acted on", "value": f"{readiness['high_vl_followup_pct'].mean():.0f}", "unit": "%",
         "status": rag(readiness["high_vl_followup_pct"].mean(), 50, 30), "subdistrict": "All"},
    ]
    panels = [{"title": "Readiness by facility", "html": fig_to_img(readiness_chart, "readiness"), "subdistrict": "All"}]
    page = build_dashboard("Ilanga District — e-Impilo Readiness 2025", kpis, panels,
                           subdistricts=["Lwandle", "Mfula", "Ntaba"],
                           period="Calendar year 2025 · synthetic data",
                           notes="Five criteria agreed with the district management team. Full method: capstone_report.md")
    with open("ilanga_readiness_dashboard.html", "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"Saved ilanga_readiness_dashboard.html ({len(page) / 1024:.0f} KB)")
    try:
        from IPython.display import HTML
        display(HTML(page))
    except ImportError:
        pass
'''),
md("""
## 🚦 Final quality gate
"""),
code('''
passed = ilanga.tickets.check_nq016(readiness)
'''),
code('''
# 🎓 When the gate passes, claim your certificate
if passed:
    YOUR_NAME = "Your Name"          # 👈 put your name here
    cert = ilanga.brand.certificate(YOUR_NAME, pd.Timestamp.today().strftime("%d %B %Y"))
    with open("biocollaborator_certificate.html", "w", encoding="utf-8") as fh:
        fh.write(cert)
    print("Saved biocollaborator_certificate.html - download it from the Files panel (📁).")
    try:
        from IPython.display import HTML
        display(HTML(cert))
    except ImportError:
        pass
'''),
md("""
## 🌳 You've finished

Sixteen tickets. One district. A year of work.

You started by asking where South African health data lives. You've since cleaned it, matched patients across
duplicate records, coded it in ICD-10 and SNOMED CT, moved it between HL7 and FHIR, warehoused and tested it, turned
it into indicators and cascades, measured uncertainty honestly, found an outbreak, mapped who is left behind, audited
a laboratory, walked a knowledge graph, built a fair risk model, read clinical notes in three languages — and written
a report a district manager could defend in front of a province.

**That's not a course exercise. That's the job.**

### Where to take this next

- **Build your portfolio.** Adapt Ilanga to your own district, or replace it with data you're authorised to use.
  A public repo of health data work is worth more than any certificate.
- **Go deeper where you lit up.** Graphs → Neo4j certification and Graph Database Africa. Epidemiology → an MPH or
  the Field Epidemiology Training Programme. Interoperability → HL7 FHIR community work.
- **Teach it.** Run a study group in the BioCollaborator **Health Career Hub**. Explaining a cascade to someone else
  is how you find out you really understand it.
- **Contribute back.** Found a bug, a better isiZulu phrasing, a clearer explanation? Open an issue or a pull
  request. This course belongs to the community that uses it.

> 🤝 **A last Ubuntu Moment**
>
> *Umuntu ngumuntu ngabantu* — a person is a person through other people. Every row you touched stood for someone:
> a mother at an antenatal visit, a man collecting his TLD, a child with diarrhoea in week 6. You now hold skills
> that decide whether their information helps them or fails them.
>
> Use them well. **Innovate Naturally.**

## 📚 Full glossary
Every module's glossary is collected in `docs/CURRICULUM.md`.
"""),
md(FOOTER),
]

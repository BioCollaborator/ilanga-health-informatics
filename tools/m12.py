from nb import md, code, ex, SETUP, FOOTER, colab_badge

PATH = "notebooks/phase3_analytics/M12_laboratory_informatics.ipynb"

CELLS = [
md(f"""
# Module 12 · Inside the laboratory — turnaround time, rejections and closing the loop
**BioCollaborator Health Informatics Programme** · Phase 3: Analytics · *Innovate Naturally*

{colab_badge(PATH)}

> **File → Save a copy in Drive**, then run cells top to bottom with **Shift + Enter**.
"""),
code(SETUP),
code('''
from ilanga.extensions_v12 import SLA_HOURS

ilanga.brand.banner(12, "Inside the laboratory: TAT, rejections & closing the loop", "Phase 3 · Analytics", minutes=150)
ilanga.brand.ticket(
    "NQ-012", "Zanele Khumalo", "Laboratory Manager, NHLS Ilanga Laboratory",
    "Laboratory performance review - and are high viral loads being acted on?",
    "Clinics tell me our results are slow. My bench data says we're fast. We're probably both right, because we're "
    "measuring different things. I need turnaround time broken down properly, our SLA compliance, a look at why "
    "specimens get rejected - and the question that keeps me up at night: when we report a high viral load, "
    "does anyone see the patient?",
    ["Median and 90th-percentile turnaround time per test for 2025",
     "SLA compliance per test, using lab-controlled turnaround time",
     "For every high viral load (Jan–Sep 2025): was the patient seen within 28 days of the result?",
     "A note separating lab, transport and clinic contributions to delay"],
    priority="High - quality review")
'''),
md("""
## Part 1 · The total testing process

A lab result's journey starts long before the analyser and ends long after it:

| Phase | Steps | Who controls it |
|---|---|---|
| **Pre-analytical** | Test ordered → specimen collected → labelled → transported → received | Clinic, courier, lab reception |
| **Analytical** | Tested, quality-controlled, verified | Laboratory |
| **Post-analytical** | Result released → delivered → read → **acted on** | Lab, IT systems, clinic |

Laboratory medicine has a long-standing finding: **most errors happen outside the analytical phase**, especially
before the specimen reaches the lab. The analyser is usually the most reliable part of the whole chain.

> 🩺 **Clinic Corner — the brain-to-brain loop**
>
> Lab professionals describe testing as a loop that starts in the requesting clinician's brain (*what do I need to
> know?*) and ends there (*what do I do now?*). A perfect result that arrives after the patient has left, or is never
> read, has the same clinical value as no result.

## Part 2 · Measuring turnaround time properly
"""),
code('''
d = ilanga.load_district()
fsub = d.facilities.set_index("facility_id")["subdistrict"]
l = d.lab_results[d.lab_results["collected_at"].dt.year == 2025].copy()

l["transport_h"] = (l["received_at"] - l["collected_at"]).dt.total_seconds() / 3600   # pre-analytical
l["lab_tat_h"] = (l["reported_at"] - l["received_at"]).dt.total_seconds() / 3600      # lab-controlled
l["tat_h"] = (l["reported_at"] - l["collected_at"]).dt.total_seconds() / 3600         # total, as the clinic sees it
l["subdistrict"] = l["ordering_facility_id"].map(fsub)

l[["test_code", "subdistrict", "transport_h", "lab_tat_h", "tat_h"]].head()
'''),
code('''
vl = l[l["test_code"] == "VL"]
fig, ax = plt.subplots(figsize=(8, 3.2))
ax.hist(vl["tat_h"], bins=40, color=BRAND["teal"])
for stat, val, col in [("mean", vl["tat_h"].mean(), BRAND["navy"]), ("median", vl["tat_h"].median(), BRAND["ochre"]),
                       ("90th pct", vl["tat_h"].quantile(0.9), "red")]:
    ax.axvline(val, color=col, ls="--"); ax.text(val, ax.get_ylim()[1] * 0.9, f" {stat}\\n {val:.0f} h", color=col, fontsize=8)
ax.set_xlabel("Hours from collection to report"); ax.set_title("Viral load total turnaround time, 2025")
plt.show()
'''),
md("""
> 💻 **Code Corner — why medians and percentiles?**
>
> Turnaround times are **skewed**: most are quick, a few take very long. The mean gets dragged towards the slow
> tail. The **median** tells you the typical experience, and the **90th percentile** tells you the bad-day experience —
> "9 in 10 results arrive within X hours". Laboratories commonly report both.

### 🌱 Seedling — TAT summary by test
Build `tat_summary`: a DataFrame **indexed by `test_code`** with columns `median_h` and `p90_h` — the median and
90th percentile of **total** turnaround time for results collected in 2025. Hints: `ilanga.hint("NQ-012.1")`.
"""),
ex('''
tat_summary = None   # 👈 your code here
tat_summary
''', '''
tat_summary = l.groupby("test_code")["tat_h"].agg(median_h="median", p90_h=lambda s: s.quantile(0.9)).round(1)
tat_summary
'''),
md("""
### Where does the time go?
"""),
code('''
parts = l.groupby("subdistrict")[["transport_h", "lab_tat_h"]].median()
fig, ax = plt.subplots(figsize=(7, 3))
ax.barh(parts.index, parts["transport_h"], color=BRAND["ochre"], label="Collection → lab (transport)")
ax.barh(parts.index, parts["lab_tat_h"], left=parts["transport_h"], color=BRAND["teal"], label="Lab receipt → report")
ax.set_xlabel("Median hours"); ax.set_title("Where does turnaround time go? (all tests, 2025)"); ax.legend(fontsize=8)
plt.show()
parts.round(1)
'''),
md("""
Now both sides of the argument make sense. The lab's own processing time is similar everywhere. **Transport** is what
makes Ntaba's results slow — and the clinic experiences the total.

### 🌿 Sapling — SLA compliance
Ilanga's (fictional) service-level agreement sets a maximum **lab-controlled** turnaround time per test,
in `SLA_HOURS`. Build `sla_compliance`: a Series indexed by `test_code` with the **percentage** of 2025 results whose
lab TAT was within the SLA. Hints: `ilanga.hint("NQ-012.2")`.
"""),
code('''
SLA_HOURS
'''),
ex('''
sla_compliance = None   # 👈 your code here
sla_compliance
''', '''
sla_compliance = ((l["lab_tat_h"] <= l["test_code"].map(SLA_HOURS)).groupby(l["test_code"]).mean() * 100).round(1)
sla_compliance
'''),
md("""
> 🤝 **Ubuntu Moment — measure what you control, report what patients experience**
>
> Holding the lab accountable for courier delays is unfair; hiding transport delays because "that's not the lab" is
> worse. Good performance reporting shows **both**: lab-controlled TAT for accountability, total TAT for the truth of
> what a patient in Ntaba waits for.

## Part 3 · Rejected specimens

When a specimen can't be tested — haemolysed, mislabelled, too old — the lab rejects it. It never appears in
`lab_results`. The patient must come back, and some never do.
"""),
code('''
rej = d.specimen_rejections.assign(subdistrict=d.specimen_rejections["ordering_facility_id"].map(fsub))
all_lab = d.lab_results.assign(subdistrict=d.lab_results["ordering_facility_id"].map(fsub))
non_xpert = all_lab[all_lab["test_code"] != "XPERT"]

rate = (rej.groupby("subdistrict").size() / (rej.groupby("subdistrict").size() + non_xpert.groupby("subdistrict").size()) * 100)
print("Rejection rate (% of specimens received):")
print(rate.round(2).to_string())

reasons = rej["reason"].value_counts()
cum = reasons.cumsum() / reasons.sum() * 100
fig, ax = plt.subplots(figsize=(8, 3.5))
ax.bar(reasons.index, reasons.values, color=BRAND["teal"])
ax2 = ax.twinx(); ax2.plot(reasons.index, cum.values, color=BRAND["ochre"], marker="o"); ax2.set_ylim(0, 105)
ax2.set_ylabel("Cumulative %"); ax.set_title("Pareto chart: why specimens are rejected")
plt.setp(ax.get_xticklabels(), rotation=25, ha="right", fontsize=8); plt.show()
'''),
code('''
pd.crosstab(rej["reason"], rej["subdistrict"], normalize="columns").mul(100).round(1)
'''),
md("""
> 🩺 **Clinic Corner — reading the Pareto chart**
>
> A **Pareto chart** sorts causes from most to least common, with a cumulative line. It shows where fixing a few
> causes removes most of the problem. Look at *exceeded stability time* in Ntaba: specimens that spent too long in
> transit. That's the same transport problem from Part 2, now costing whole results rather than hours. The fix is
> logistics (collection schedules, cool boxes, point-of-care testing), not bench work.

## Part 4 · Closing the loop: are high viral loads acted on?

A viral load of 1,000 copies/mL or more signals that treatment may be failing. South African guidelines expect a
response: adherence support, then a repeat viral load, typically around three months later. **The first step is simply
seeing the patient.** The result is only useful if it changes what happens next.
"""),
code('''
golive = d.facilities.set_index("facility_id")["emr_go_live"]
hv = d.lab_results[(d.lab_results["test_code"] == "VL") & (d.lab_results["result_numeric"] >= 1000)].copy()
hv["delivered_via"] = np.where(hv["reported_at"] >= hv["ordering_facility_id"].map(golive), "e-Impilo", "Printed report")
hv["delivered_via"].value_counts()
'''),
md("""
### 🌳 Baobab — high viral load follow-up
Build `high_vl_followup`: one row per viral load result **≥ 1,000 copies/mL** collected **1 January – 30 September
2025**, with columns `specimen_id`, `patient_id`, `reported_at` and `seen_within_28d`: `True` if the patient had **any
encounter** from the **day after** the result was reported up to **28 days** after it. Then report the overall
percentage, and compare e-Impilo versus printed delivery. Hints: `ilanga.hint("NQ-012.3")`.
"""),
ex('''
high_vl_followup = None   # 👈 your code here
high_vl_followup
''', '''
hv25 = hv[hv["collected_at"].between("2025-01-01", "2025-09-30 23:59")][["specimen_id", "patient_id", "reported_at", "delivered_via"]]
m = hv25.merge(d.encounters[["patient_id", "encounter_date"]], on="patient_id", how="left")
days = (m["encounter_date"] - m["reported_at"].dt.normalize()).dt.days
m["hit"] = days.between(1, 28)
seen = m.groupby("specimen_id")["hit"].any()
high_vl_followup = hv25.assign(seen_within_28d=hv25["specimen_id"].map(seen).fillna(False).astype(bool))

print(f"{len(high_vl_followup)} high viral loads; seen within 28 days: {high_vl_followup['seen_within_28d'].mean():.1%}")
print(high_vl_followup.groupby("delivered_via")["seen_within_28d"].agg(["size", "mean"]).round(3))
high_vl_followup.head()
'''),
md("""
> 🩺 **Clinic Corner — what would you recommend?**
>
> If most patients with a high viral load aren't seen within four weeks, the problem isn't the laboratory. It's the
> post-analytical loop: results filed without action, and routine two-month appointments that don't change when a
> worrying result arrives. Practical fixes include **results-triggered recall lists**, SMS recall, and EMR alerts
> that show high viral loads to the next clinician. This is where lab informatics saves lives.

## 🚦 Quality gate
"""),
code('''
passed = ilanga.tickets.check_nq012(tat_summary, sla_compliance, high_vl_followup)
'''),
md("""
## 📝 Handover note — for Zanele Khumalo
> **NQ-012 — done.**
> *TAT: median viral load turnaround was … h (90th percentile … h). Lab-controlled time is similar across
> sub-districts; transport explains most of Ntaba's delay.*
> *SLA: compliance ranged from …% (…) to …% (…).*
> *Rejections: the leading reasons were …; in Ntaba, … accounts for …% of rejections.*
> *Closing the loop: only …% of high viral loads were followed by a visit within 28 days. Recommend …*

---
### 🎓 Phase 3 complete
You can now define and verify indicators, build care cascades, quantify uncertainty, compare groups, estimate
retention, detect outbreaks, map access, build a decision dashboard and run a laboratory performance review.
**Phase 4 — Advanced & Capstone** takes you into knowledge graphs, machine learning, GenAI, and a final
end-to-end project for Ilanga District.

## 🧭 Career Lens
**Laboratory information managers**, **LIS analysts**, **quality managers** and **laboratory data scientists**
work at the NHLS, private pathology groups and research laboratories. Medical technologists who can analyse their
own lab's data and speak IT are rare and valuable — and exactly the bridge between the bench and the clinic.

## 📚 Glossary
**Total testing process** – pre-analytical, analytical and post-analytical phases · **Total TAT** – collection to
report · **Lab TAT** – receipt to report · **SLA** – service-level agreement · **90th percentile** – value that 90% of
results fall within · **Specimen rejection** – specimen unsuitable for testing · **Pareto chart** – causes sorted by
frequency with a cumulative line · **Closing the loop** – making sure results lead to action

## ✅ Checkpoint
<details><summary>1. The lab's median VL TAT is 3 days but clinics say results take a week. How can both be true?</summary>The lab measures receipt-to-report; clinics experience collection-to-report plus delivery. Transport and printed delivery add days.</details>
<details><summary>2. Why is "exceeded stability time" mainly a logistics problem?</summary>It happens when specimens spend too long in transit before testing — it's caused by distance and courier schedules, not bench work.</details>
<details><summary>3. Why measure whether patients are seen after a high viral load?</summary>A result only improves care if someone acts on it. Measuring the post-analytical loop shows whether results change clinical management.</details>
"""),
md(FOOTER),
]

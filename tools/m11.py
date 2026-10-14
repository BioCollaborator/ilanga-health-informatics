from nb import md, code, ex, SETUP, FOOTER, colab_badge

PATH = "notebooks/phase3_analytics/M11_dashboards_geospatial.ipynb"

CELLS = [
md(f"""
# Module 11 · From analysis to decisions — a district dashboard and a map of access
**BioCollaborator Health Informatics Programme** · Phase 3: Analytics · *Innovate Naturally*

{colab_badge(PATH)}

> **File → Save a copy in Drive**, then run cells top to bottom with **Shift + Enter**.
"""),
code(SETUP),
code('''
from ilanga.dashboard import build_dashboard, fig_to_img, rag

ilanga.brand.banner(11, "From analysis to decisions: dashboards & access maps", "Phase 3 · Analytics", minutes=150)
ilanga.brand.ticket(
    "NQ-011", "Mrs Nokuthula Cele", "District Manager, Ilanga District Health Services",
    "A one-page dashboard for the monthly management meeting",
    "My management team gets forty-page reports that nobody reads. I want one page: a handful of numbers that tell me "
    "where to act, per sub-district, with a clear signal of what's on track and what isn't. And show me who lives too "
    "far from a clinic - I'm fighting for a new mobile clinic route and I need evidence. It must open on a phone "
    "and work when the network is bad.",
    ["Distance from every ward to its nearest PHC facility",
     "A KPI table per sub-district: headcount, viral suppression, referral arrival and access",
     "A single-file HTML dashboard with red/amber/green status that works offline",
     "A short note recommending where the mobile route should go"],
    priority="High - management meeting")
'''),
md("""
## Part 1 · What makes a dashboard useful

Most dashboards fail because they show *everything*. A decision dashboard shows **what someone needs to act on**.

| Principle | In practice |
|---|---|
| **Start with the decision** | "Where should the mobile clinic go?" not "Here's all our data" |
| **Few numbers, clearly defined** | 4–6 KPIs, each with a definition people agree on (Module 9) |
| **Status against a target** | Red / amber / green says *act, watch, fine* faster than a raw number |
| **Trends beat snapshots** | Is it getting better or worse? |
| **Show data quality** | If a sub-district's reports are late or missing, say so on the page |
| **Accessible design** | Never rely on colour alone; label everything; test on a phone |
| **Fit the context** | Many managers read on phones with expensive data. One small offline file beats a heavy web app |

## Part 2 · Distances on a curved Earth

Coordinates are in **degrees**, not kilometres, and the Earth is round. The **haversine formula** gives the
straight-line ("as the crow flies") distance between two points:

$$d = 2R\\,\\arcsin\\sqrt{\\sin^2\\!\\left(\\tfrac{\\Delta\\varphi}{2}\\right) + \\cos\\varphi_1 \\cos\\varphi_2 \\sin^2\\!\\left(\\tfrac{\\Delta\\lambda}{2}\\right)}$$

where φ is latitude, λ is longitude (both in **radians**) and R ≈ 6,371 km.

### 🌱 Seedling — haversine distance
Write `haversine_km(lat1, lon1, lat2, lon2)` returning kilometres. Use numpy so it also works on arrays.
Check: Cape Town (−33.92, 18.42) to Durban (−29.86, 31.02) is about 1,275 km. Hints: `ilanga.hint("NQ-011.1")`.
"""),
ex('''
def haversine_km(lat1, lon1, lat2, lon2):
    # 👈 your code here
    return None

haversine_km(-33.92, 18.42, -29.86, 31.02)
''', '''
def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2)**2
    return 2 * 6371 * np.arcsin(np.sqrt(a))

haversine_km(-33.92, 18.42, -29.86, 31.02)
'''),
md("""
> 🩺 **Clinic Corner — crow-flies is the optimistic case**
>
> Real journeys follow roads, cross rivers, climb hills and depend on taxis that may run twice a day. Straight-line
> distance *underestimates* the burden, especially in rural areas. A commonly used South African access benchmark is
> living within **5 km of a PHC facility** — useful, but remember what a straight line hides.

## Part 3 · Mapping access
"""),
code('''
d = ilanga.load_district()
phc = d.facilities[d.facilities["facility_type"].isin(["Clinic", "CHC", "Mobile Clinic"])].reset_index(drop=True)
wards = d.wards
colours = {"Lwandle": BRAND["teal"], "Mfula": BRAND["ochre"], "Ntaba": BRAND["navy"]}

fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(wards["longitude"], wards["latitude"], s=wards["estimated_population"] / 6,
           c=wards["subdistrict"].map(colours), alpha=0.35, label="Ward (size = population)")
ax.scatter(phc["longitude"], phc["latitude"], marker="P", s=160, color="black", label="PHC facility")
for w in wards.itertuples():
    ax.annotate(str(w.ward), (w.longitude, w.latitude), fontsize=7, ha="center", va="center")
ax.set_title("Ilanga wards and PHC facilities"); ax.legend(loc="lower left")
plt.show()
'''),
md("""
### 🌿 Sapling — nearest facility for every ward
Build `ward_access`: one row per ward with columns `ward`, `nearest_facility_id` and `distance_km` — the straight-line
distance from the ward centroid to the **nearest PHC facility** (Clinic, CHC or Mobile Clinic). Hints:
`ilanga.hint("NQ-011.2")`.
"""),
ex('''
ward_access = None   # 👈 your code here
ward_access
''', '''
rows = []
for w in wards.itertuples():
    dist = haversine_km(w.latitude, w.longitude, phc["latitude"].values, phc["longitude"].values)
    i = int(np.argmin(dist))
    rows.append({"ward": w.ward, "nearest_facility_id": phc.loc[i, "facility_id"], "distance_km": round(float(dist[i]), 2)})
ward_access = pd.DataFrame(rows)
ward_access.sort_values("distance_km", ascending=False).head(8)
'''),
code('''
if ward_access is not None:
    acc = wards.merge(ward_access, on="ward")
    fig, ax = plt.subplots(figsize=(8, 6))
    far = acc["distance_km"] > 5
    ax.scatter(acc.loc[~far, "longitude"], acc.loc[~far, "latitude"], s=acc.loc[~far, "estimated_population"] / 6,
               color=BRAND["teal"], alpha=0.5, label="Within 5 km")
    ax.scatter(acc.loc[far, "longitude"], acc.loc[far, "latitude"], s=acc.loc[far, "estimated_population"] / 6,
               color=BRAND["ochre"], alpha=0.7, label="More than 5 km")
    ax.scatter(phc["longitude"], phc["latitude"], marker="P", s=160, color="black", label="PHC facility")
    for w in acc[far].itertuples():
        ax.annotate(f"W{w.ward}\\n{w.distance_km:.0f} km", (w.longitude, w.latitude), fontsize=7, ha="center")
    ax.set_title("Who lives more than 5 km from a PHC facility?"); ax.legend(loc="lower left")
    access_map = fig
    plt.show()
    print(f"{acc.loc[far, 'estimated_population'].sum():,} people live in wards more than 5 km from a facility.")
'''),
md("""
> 🤝 **Ubuntu Moment — distance is a cost paid by the poorest**
>
> Ten kilometres is a morning's walk with a sick child, or a taxi fare that competes with food. People who live far
> from care arrive later and sicker, and are more likely to drop out of treatment (Module 9's cascade). An access map
> turns that invisible burden into evidence a manager can fight with.

## Part 4 · The KPI table

### 🌳 Baobab — district KPIs for 2025
Build `kpi_table`: a DataFrame **indexed by sub-district** with four columns:

| Column | Definition (2025) |
|---|---|
| `headcount_2025` | Visits at facilities located in the sub-district |
| `vl_suppression_pct` | % of viral loads (by ordering facility's sub-district) below the limit or < 1,000 |
| `referral_arrival_pct` | % of referrals *from* the sub-district's facilities where the patient was seen |
| `pct_pop_within_5km` | % of estimated population living in wards ≤ 5 km from a PHC facility |

Hints: `ilanga.hint("NQ-011.3")`.
"""),
ex('''
kpi_table = None   # 👈 your code here
kpi_table
''', '''
fsub = d.facilities.set_index("facility_id")["subdistrict"]
e25 = d.encounters[d.encounters["encounter_date"].dt.year == 2025]
vl = d.lab_results[(d.lab_results["test_code"] == "VL") & (d.lab_results["collected_at"].dt.year == 2025)]
ref = d.referrals[d.referrals["referral_date"].dt.year == 2025]
acc = wards.merge(ward_access, on="ward")
within = acc.assign(near_pop=acc["estimated_population"].where(acc["distance_km"] <= 5, 0)).groupby("subdistrict")

kpi_table = pd.concat([
    e25["facility_id"].map(fsub).value_counts().rename("headcount_2025"),
    ((vl["below_detection_limit"] | (vl["result_numeric"] < 1000))
        .groupby(vl["ordering_facility_id"].map(fsub)).mean() * 100).rename("vl_suppression_pct"),
    ((ref["outcome"] == "Seen").groupby(ref["from_facility_id"].map(fsub)).mean() * 100).rename("referral_arrival_pct"),
    (within["near_pop"].sum() / within["estimated_population"].sum() * 100).rename("pct_pop_within_5km"),
], axis=1).sort_index().round(1)
kpi_table
'''),
md("""
## Part 5 · Build the dashboard

Targets turn numbers into status. These are **Ilanga's illustrative targets**, agreed with the management team:

| KPI | Green (on target) | Amber (watch) |
|---|---|---|
| Viral suppression | ≥ 90% | ≥ 80% |
| Referral arrival | ≥ 85% | ≥ 75% |
| Population within 5 km | ≥ 80% | ≥ 60% |

`ilanga.dashboard.build_dashboard` assembles KPI cards and chart panels into **one HTML file** with a sub-district
filter. Images are embedded inside the file, so it opens offline and can be sent by email or WhatsApp.
"""),
code('''
TARGETS = {"vl_suppression_pct": (90, 80), "referral_arrival_pct": (85, 75), "pct_pop_within_5km": (80, 60)}
LABELS = {"headcount_2025": ("PHC headcount", ""), "vl_suppression_pct": ("Viral suppression", "%"),
          "referral_arrival_pct": ("Referrals that arrived", "%"), "pct_pop_within_5km": ("Population within 5 km", "%")}

if kpi_table is not None and ward_access is not None:
    kpis = []
    for sd, row in kpi_table.iterrows():
        for col, (label, unit) in LABELS.items():
            status = rag(row[col], *TARGETS[col]) if col in TARGETS else None
            value = f"{row[col]:,.0f}" if col == "headcount_2025" else f"{row[col]:.1f}"
            kpis.append({"label": label, "value": value, "unit": unit, "status": status, "subdistrict": sd})

    # Panel 1: monthly headcount trend per sub-district
    e = d.encounters.assign(sd=d.encounters["facility_id"].map(fsub), month=d.encounters["encounter_date"].dt.to_period("M"))
    trend = e.groupby(["month", "sd"]).size().unstack()
    fig1, ax = plt.subplots(figsize=(6, 3))
    for sd in trend.columns:
        ax.plot(trend.index.to_timestamp(), trend[sd], label=sd, color=colours[sd])
    ax.set_title("Monthly PHC headcount"); ax.legend(fontsize=8)

    # Panel 2: suppression against target
    fig2, ax = plt.subplots(figsize=(6, 3))
    ax.bar(kpi_table.index, kpi_table["vl_suppression_pct"], color=[colours[s] for s in kpi_table.index])
    ax.axhline(90, ls="--", color="black"); ax.text(-0.4, 91, "target 90%", fontsize=8)
    ax.set_ylim(0, 100); ax.set_title("Viral suppression, 2025")

    panels = [{"title": "Monthly headcount, 2024–2025", "html": fig_to_img(fig1, "headcount trend")},
              {"title": "Viral suppression against target", "html": fig_to_img(fig2, "viral suppression")},
              {"title": "Access: wards more than 5 km from a facility", "html": fig_to_img(access_map, "access map")}]
    plt.close("all")

    html_page = build_dashboard(
        "Ilanga District — Management Dashboard", kpis, panels, subdistricts=list(kpi_table.index),
        period="January–December 2025 · synthetic data",
        notes="Definitions: Module 9 & 11 indicator sheets. Ntaba reporting completeness is below 100% - interpret its figures with care.")
    with open("ilanga_dashboard.html", "w", encoding="utf-8") as fh:
        fh.write(html_page)
    print(f"Dashboard saved: ilanga_dashboard.html ({len(html_page) / 1024:.0f} KB)")
'''),
code('''
# Preview it here. Download it from the Files panel (📁 on the left), or via the Colab download below.
if kpi_table is not None and ward_access is not None:
    try:
        from IPython.display import HTML
        display(HTML(html_page))
    except ImportError:
        print("Open ilanga_dashboard.html in a browser to preview it.")
    try:
        from google.colab import files
        files.download("ilanga_dashboard.html")
    except Exception:
        pass
'''),
md("""
> 💻 **Code Corner — why not a live web dashboard?**
>
> Tools like Power BI, Superset, Streamlit and Plotly Dash are excellent when you have servers, logins and good
> connectivity. A self-contained HTML file needs none of these and still has a working filter. **Choose the tool
> for the context, not the fashion.** If you'd like interactive zoom and hover, the optional cell below tries Plotly,
> which is preinstalled in Colab.
"""),
code('''
# Optional: an interactive Plotly chart (not part of the quality gate)
try:
    import plotly.express as px
    if ward_access is not None:
        acc = wards.merge(ward_access, on="ward")
        px.scatter(acc, x="longitude", y="latitude", size="estimated_population", color="distance_km",
                   hover_data=["ward", "nearest_facility_id"], title="Ward access (hover for details)").show()
except ImportError:
    print("Plotly isn't installed here - skip this optional cell.")
'''),
md("""
## 🚦 Quality gate
"""),
code('''
passed = ilanga.tickets.check_nq011(haversine_km, ward_access, kpi_table)
'''),
md("""
## 📝 Handover note — for Mrs Cele
> **NQ-011 — done.**
> *The dashboard (attached, … KB) shows four KPIs per sub-district. On target: … Watch: … Act: …*
> *Access: … people live in wards more than 5 km from a PHC facility, mostly in … . I'd recommend the mobile clinic
> route prioritises wards …, which together have … people.*
> *Caveat: distances are straight-line; road distance and transport will be worse.*

## 🧭 Career Lens
**BI developers**, **data visualisation specialists** and **GIS analysts** are in demand across health departments,
NGOs and consultancies. The rarest skill isn't the tool — it's knowing which five numbers a manager needs. Pair
this module with Modules 9 and 10 and you can build dashboards people actually use.

## 📚 Glossary
**KPI** – key performance indicator · **RAG status** – red/amber/green against targets · **Haversine** – great-circle
distance between coordinates · **Centroid** – the central point of an area · **Access benchmark** – a distance or
time standard for reaching services · **Self-contained HTML** – a single file with everything embedded

## ✅ Checkpoint
<details><summary>1. Why convert degrees to radians before using sin and cos?</summary>numpy's trigonometric functions expect radians.</details>
<details><summary>2. Why show reporting completeness on a performance dashboard?</summary>Missing or late reports can make performance look better or worse than it is; managers need to know how far to trust each number.</details>
<details><summary>3. Name one reason a single HTML file may suit a district manager better than a web dashboard.</summary>Works offline, small enough to email or WhatsApp, no login or server, opens on a phone.</details>

**Next up → Module 12:** Inside the laboratory: turnaround time, rejected specimens, and whether high viral load
results actually lead to action.
"""),
md(FOOTER),
]

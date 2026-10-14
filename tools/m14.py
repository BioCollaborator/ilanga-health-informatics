from nb import md, code, ex, SETUP, FOOTER, colab_badge

PATH = "notebooks/phase4_advanced/M14_machine_learning_ltfu_fairness.ipynb"

CELLS = [
md(f"""
# Module 14 · Predicting who might drop out of care — honestly and fairly
**BioCollaborator Health Informatics Programme** · Phase 4: Advanced & Capstone · *Innovate Naturally*

{colab_badge(PATH)}

> **File → Save a copy in Drive**, then run cells top to bottom with **Shift + Enter**.
"""),
code(SETUP),
code('''
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, accuracy_score
from ilanga import ml

ilanga.brand.banner(14, "Predicting disengagement: honest, fair machine learning", "Phase 4 · Advanced & Capstone", minutes=150)
ilanga.brand.ticket(
    "NQ-014", "Bheki Ntuli", "HIV Programme Manager, Ilanga District Health Services",
    "A risk list for the tracing team",
    "Our tracing team - two lay counsellors and a phone - can proactively contact about one in five people on ART. "
    "Right now they only chase people after they've already disappeared. If a model could tell us who is most likely "
    "to drop out in the next year, we could offer support before that happens. But I've seen 'AI' projects that "
    "look brilliant and then fail in the real world, so I need to trust it - and I need to know it isn't unfair to "
    "any community.",
    ["Outcome labels using the programme's agreed cohort definition",
     "Risk scores for the team's held-out test patients, using only information available at the cutoff date",
     "A fairness check: flag rate and recall by sub-district at the 20% capacity threshold",
     "A model card: what it does, how well, for whom, and what it must never be used for"],
    priority="High")
'''),
md("""
## Part 1 · Framing comes before modelling

A useful prediction problem answers four questions **before** any code:

| Question | Our answer |
|---|---|
| **Who** is being predicted for? | People on ART at the cutoff date who started at least 90 days before |
| **When** is the prediction made? | **1 October 2024** (the cutoff) — using only what was known that day |
| **What** outcome? | Lost to follow-up within the next **12 months** |
| **What action** will follow? | A supportive call or visit from the tracing team — capacity: **20%** of people |

> 🤝 **Ubuntu Moment — support, never punishment**
>
> A risk score must lead to *more* help: a call, a closer pick-up point, a counselling session. It must never lead to
> less care, blame or stigma. POPIA also protects people from decisions with serious effects that are based *solely*
> on automated processing. A model can prioritise; a person decides.

## Part 2 · Cohort and labels
"""),
code('''
d = ilanga.load_district()
cohort = ml.at_risk_cohort(d)
print(f"Cutoff {ml.CUTOFF.date()}, horizon {ml.HORIZON_DAYS} days")
print(f"{len(cohort):,} people at risk; {cohort['ltfu_next_12m'].sum()} ({cohort['ltfu_next_12m'].mean():.1%}) lost to follow-up in the next 12 months")
cohort.head()
'''),
md("""
### 🌱 Seedling — labels
Store the outcome as `labels`: a Series **indexed by `patient_id`** with values 0 or 1. Read `ilanga/ml.py` first and
make sure you could explain the cohort rules to Bheki. Hints: `ilanga.hint("NQ-014.1")`.
"""),
ex('''
labels = None   # 👈 your code here
''', '''
labels = cohort.set_index("patient_id")["ltfu_next_12m"]
labels.value_counts()
'''),
md("""
## Part 3 · Features: only what was known at the cutoff

Every feature must be computable **on 1 October 2024**. Using anything later is **leakage**: the model "sees the
future", scores brilliantly in testing, and fails in real use.
"""),
code('''
CUT = ml.CUTOFF
ids = cohort["patient_id"]
p = d.patients.set_index("patient_id").loc[ids]

def build_features(ids):
    X = pd.DataFrame(index=pd.Index(ids, name="patient_id"))
    X["age"] = ilanga.age_years(p.loc[ids, "date_of_birth"], CUT).values
    X["male"] = (p.loc[ids, "sex"] == "M").astype(int).values
    X["ntaba"] = (p.loc[ids, "subdistrict"] == "Ntaba").astype(int).values
    X["years_on_art"] = ((CUT - cohort.set_index("patient_id").loc[ids, "art_start_date"]).dt.days / 365.25).values
    X["second_line"] = (cohort.set_index("patient_id").loc[ids, "regimen"] == "AZT/3TC/LPV/r").astype(int).values

    ma = d.missed_appointments[d.missed_appointments["scheduled_date"] < CUT]
    X["missed_6m"] = ma[ma["scheduled_date"] >= CUT - pd.Timedelta(days=182)].groupby("patient_id").size().reindex(ids).fillna(0).values
    X["missed_before"] = ma.groupby("patient_id").size().reindex(ids).fillna(0).values

    vl = d.lab_results[(d.lab_results["test_code"] == "VL") & (d.lab_results["collected_at"] < CUT)]
    last = vl.sort_values("collected_at").groupby("patient_id").tail(1).set_index("patient_id")
    unsupp = ~(last["below_detection_limit"] | (last["result_numeric"] < 1000))
    X["last_vl_unsuppressed"] = unsupp.reindex(ids).fillna(False).astype(int).values
    X["no_vl_last_12m"] = (~pd.Index(ids).isin(last.index[last["collected_at"] >= CUT - pd.Timedelta(days=365)])).astype(int)

    disp = d.dispensing[(d.dispensing["dispense_date"] < CUT) & d.dispensing["channel"].str.startswith("CCMDD")]
    X["uses_ccmdd"] = pd.Index(ids).isin(disp["patient_id"]).astype(int)
    return X

X = build_features(ids)
y = labels if labels is not None else cohort.set_index("patient_id")["ltfu_next_12m"]
X.groupby(y.reindex(X.index)).mean().T.round(2).rename(columns={0: "stayed in care", 1: "lost to follow-up"})
'''),
md("""
> 🩺 **Clinic Corner — what the data is telling us**
>
> People who later disengage had already **missed appointments** in the months before, and more often had an
> **unsuppressed viral load**. That matches what clinicians see: disengagement is usually a slide, not a cliff.
> Every missed appointment is a chance to reach someone before they're gone.

### A leakage demonstration

Let's add one innocent-looking feature: the number of visits each person made **after** the cutoff.
"""),
code('''
train_ids, test_ids = ml.train_test_ids(d)

future_visits = d.encounters[d.encounters["encounter_date"] >= CUT].groupby("patient_id").size()
X_leaky = X.assign(visits_after_cutoff=future_visits.reindex(X.index).fillna(0))

leaky = LogisticRegression(max_iter=3000).fit(X_leaky.loc[train_ids], y.loc[train_ids])
print(f"AUC with a leaked feature: {roc_auc_score(y.loc[test_ids], leaky.predict_proba(X_leaky.loc[test_ids])[:, 1]):.3f}  <- too good to be true")
'''),
md("""
Near-perfect — and useless, because on 1 October 2024 nobody knows how many visits someone will make next year.
**When a health prediction looks too good to be true, look for leakage first.**

## Part 4 · Train, evaluate, and don't be fooled by accuracy
"""),
code('''
baseline_acc = accuracy_score(y.loc[test_ids], np.zeros(len(test_ids)))
print(f"A 'model' that predicts nobody will drop out is {baseline_acc:.1%} accurate - and helps no one.")
print("That's why we use AUC: the chance a random dropout is ranked above a random non-dropout (0.5 = coin toss).")
'''),
md("""
### 🌿 Sapling — risk scores for the test patients
Train a model on `train_ids` using only pre-cutoff features, and store its predicted risk for **every patient in
`test_ids`** (and only those) as `test_risk`: a Series indexed by `patient_id`. Target: **AUC ≥ 0.60** — realistic for
this problem; published loss-to-follow-up models often land between 0.6 and 0.8. Hints: `ilanga.hint("NQ-014.2")`.
"""),
ex('''
test_risk = None   # 👈 your code here
''', '''
model = LogisticRegression(max_iter=3000, class_weight="balanced")
model.fit(X.loc[train_ids], y.loc[train_ids])
test_risk = pd.Series(model.predict_proba(X.loc[test_ids])[:, 1], index=pd.Index(test_ids, name="patient_id"))
print(f"Logistic regression test AUC: {roc_auc_score(y.loc[test_ids], test_risk):.3f}")

rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=20, random_state=0, class_weight="balanced")
rf.fit(X.loc[train_ids], y.loc[train_ids])
print(f"Random forest test AUC:       {roc_auc_score(y.loc[test_ids], rf.predict_proba(X.loc[test_ids])[:, 1]):.3f}")

pd.Series(model.coef_[0], index=X.columns).sort_values().round(2).rename("coefficient")
'''),
md("""
> 💻 **Code Corner — simple models deserve respect**
>
> On small, noisy health datasets, a well-specified **logistic regression** often matches or beats fancier models,
> and its coefficients can be explained to a programme manager. Choose complexity only when it earns its keep on
> held-out data.

## Part 5 · From scores to action — and fairness

The team can contact **20%** of people. So the practical question isn't "what's the AUC?" but "if we call the top
20%, how many future dropouts do we reach?"
"""),
code('''
if test_risk is not None:
    yt = y.loc[test_ids]
    flagged = test_risk >= test_risk.quantile(0.8)
    captured = (flagged & (yt == 1)).sum() / (yt == 1).sum()
    print(f"Calling the top 20% reaches {captured:.0%} of people who would otherwise drop out.")
    print(f"Random calling would reach about 20%, so the model makes each call about {captured / 0.2:.1f} times as useful.")
'''),
md("""
### 🌳 Baobab — the fairness check
Using your `test_risk` and the **top-20% threshold** across all test patients, build `fairness_table`: a DataFrame
**indexed by sub-district** with columns:

- `n` — test patients in the sub-district
- `flag_rate` — % of them flagged
- `recall` — % of that sub-district's actual dropouts who were flagged

Hints: `ilanga.hint("NQ-014.3")`.
"""),
ex('''
fairness_table = None   # 👈 your code here
''', '''
sd = d.patients.set_index("patient_id").loc[test_ids, "subdistrict"]
yt = y.loc[test_ids]
flagged = test_risk >= test_risk.quantile(0.8)
fairness_table = pd.DataFrame({
    "n": sd.value_counts(),
    "flag_rate": flagged.groupby(sd).mean() * 100,
    "recall": (flagged & (yt == 1)).groupby(sd).sum() / (yt == 1).groupby(sd).sum() * 100,
}).round(1)
fairness_table
'''),
md("""
> 🩺 **Clinic Corner — is a higher flag rate unfair?**
>
> If the model flags Ntaba residents more often, is that bias or need? Distance genuinely makes appointments harder
> to keep, so more support there may be exactly right — *if* the extra calls lead to help, not suspicion. Fairness
> isn't one number. It's asking: **who benefits, who is burdened, and who is missed?** Watch **recall**: if one group's
> dropouts are rarely flagged, that group is being left behind. With test groups this small, treat differences as
> questions to investigate, not conclusions.

## 🚦 Quality gate
"""),
code('''
passed = ilanga.tickets.check_nq014(labels, test_risk, fairness_table)
'''),
md("""
## 📝 Handover — a model card for Bheki
> **Model card: Ilanga ART disengagement risk (prototype, synthetic data)**
> - **Purpose:** prioritise supportive outreach for people on ART. **Not** for eligibility, blame or reducing care.
> - **Population and timing:** …  **Outcome:** …
> - **Features:** … (all known at the cutoff). **Excluded:** … (leakage risk).
> - **Performance:** test AUC …; top 20% reaches …% of future dropouts.
> - **Fairness:** flag rate and recall by sub-district: … . Groups too small to conclude: …
> - **Limitations:** synthetic data; must be re-validated on real data, monitored monthly, and retrained when care models change.
> - **Human oversight:** counsellors decide who to contact; patients are never told they were "flagged".

## 🧭 Career Lens
**Health data scientists** and **clinical ML engineers** build models like this at research units, NGOs and health
tech companies. The rarest skill isn't training models — it's the judgement in this notebook: framing the problem,
catching leakage, choosing thresholds for real capacity, checking fairness and writing an honest model card.

## 📚 Glossary
**Cohort** – the population a model predicts for · **Cutoff / horizon** – when the prediction is made / how far ahead ·
**Leakage** – using information unavailable at prediction time · **AUC** – ranking quality (0.5 = chance) ·
**Class imbalance** – one outcome much rarer than the other · **Recall** – share of true cases caught · **Model card** –
a short document describing a model's purpose, performance and limits

## ✅ Checkpoint
<details><summary>1. Your model has 94% accuracy. Why might it be useless?</summary>If only ~6% of people drop out, predicting "nobody" is 94% accurate and catches no one.</details>
<details><summary>2. A feature gives AUC 0.99. What do you check first?</summary>Whether it uses information from after the prediction date — leakage.</details>
<details><summary>3. Why choose the threshold from team capacity?</summary>The model's value depends on the action. If the team can call 20% of people, the question is how many future dropouts are in that 20%.</details>

**Next up → Module 15:** Words as data — extracting information from clinical notes and triaging multilingual helpline
messages, safely, with and without large language models.
"""),
md(FOOTER),
]

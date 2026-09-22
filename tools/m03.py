from nb import md, code, ex, SETUP, FOOTER, colab_badge

PATH = "notebooks/phase1_onboarding/M03_synthetic_data_done_right.ipynb"

CELLS = [
md(f"""
# Module 03 · Building Ilanga — synthetic health data done right
**BioCollaborator Health Informatics Programme** · Phase 1: Onboarding · *Innovate Naturally*

{colab_badge(PATH)}

> **File → Save a copy in Drive**, then run cells top to bottom with **Shift + Enter**.
"""),
code(SETUP),
code('''
ilanga.brand.banner(3, "Building Ilanga: synthetic data done right", "Phase 1 · Onboarding", minutes=120)
ilanga.brand.ticket(
    "NQ-003", "Ayanda Mthembu", "Lead Data Engineer, Nqaba Health Informatics",
    "Understand, verify and extend the synthetic data platform",
    "Everything we build for Ilanga runs on synthetic data, so every analyst must understand how it's made, "
    "where it's realistic and where it isn't. I'd like you to verify the ID numbers, write an independent Luhn "
    "check (two implementations that agree are how we trust critical code), and prototype adding a new "
    "condition - asthma - so we can plan the next dataset release.",
    ["Count of valid SA ID numbers in the patient register",
     "Your own Luhn check-digit function that agrees with the platform's",
     "A reproducible 5,000-person mini-population with asthma at the target rates",
     "A handover note on one limitation of synthetic data"],
    priority="Normal")
'''),
md("""
## Part 1 · Why synthetic data?

Real health records are some of the most sensitive data that exists. In South Africa, health information is
**special personal information** under the *Protection of Personal Information Act (POPIA)*, with strict rules on
who may process it and why. There's also a practical catch: **Google Colab runs on servers that may be outside South
Africa**, and POPIA restricts sending personal information across borders. So real patient data has no place in a
learning notebook — full stop.

Synthetic data gives us realistic *patterns* without real *people*. Industry uses it constantly: for training,
for testing new systems before go-live, and for building pipelines before access to real data is approved.
Open-source tools like **Synthea** generate synthetic patient records; we built our own generator so it reflects
a South African district: SA ID numbers, a young population, a high HIV burden, rising hypertension and diabetes,
and uneven digitisation.

> ⚠️ **What synthetic data cannot do**
>
> A generator only knows what we tell it. Ilanga's disease rates are **illustrative parameters**, not official
> statistics. It can't discover a new risk factor, and if we encode a bias, it faithfully reproduces that bias.
> **Never draw real-world health conclusions from synthetic data.** Use it to learn methods, then apply those
> methods — with approvals — to real data.
"""),
md("""
## Part 2 · Randomness you can repeat

Synthetic data is built from random numbers. But "random" in a data platform must be **reproducible**: if a
colleague runs the same code, they must get the same dataset. The trick is a **seed**.
"""),
code('''
rng_a = np.random.default_rng(2026)
rng_b = np.random.default_rng(2026)
rng_c = np.random.default_rng(7)

print("seed 2026:", rng_a.integers(0, 100, 5))
print("seed 2026:", rng_b.integers(0, 100, 5), "<- identical: same seed, same numbers")
print("seed 7   :", rng_c.integers(0, 100, 5), "<- different seed, different numbers")
'''),
md("""
> 💻 **Code Corner — generators and seeds**
>
> `np.random.default_rng(seed)` creates a random-number **generator**. Same seed → same sequence, every time,
> on every computer. Ilanga uses seed `2026`, which is why your numbers match your classmates' numbers exactly.
> In enterprise teams, the seed is recorded with each dataset release, like a version number.

## Part 3 · Anatomy of a South African ID number

The 13-digit SA ID number packs a lot of information into a small space: **YYMMDD SSSS C A Z**.
"""),
code('''
district = ilanga.load_district()
pat = district.patients

example = pat.loc[pat["id_type"] == "SA_ID", "sa_id_number"].iloc[0]
print("Synthetic ID:", example)
print(f"  YYMMDD  {example[0:6]}   date of birth")
print(f"  SSSS    {example[6:10]}     sequence: 0000-4999 registered female, 5000-9999 registered male")
print(f"  C       {example[10]}        0 = citizen, 1 = permanent resident")
print(f"  A       {example[11]}        historical digit, usually 8")
print(f"  Z       {example[12]}        check digit (Luhn)")
ilanga.sa_id.parse(example)
'''),
md("""
> 🤝 **Ubuntu Moment — an ID number is not just a number**
>
> An ID number reveals a person's **date of birth** and their **registered sex** on its own. That makes it far more
> identifying than it looks — we'll come back to that in Module 4.
>
> Notice also that the sex digit reflects **registration at Home Affairs**. It may not match someone's gender
> identity, and it isn't clinical information. Well-designed health systems record what they need clinically and
> never *infer* it from an ID number.

## Part 4 · The Luhn check digit

The last digit exists to catch typing mistakes. It's calculated from the other 12 using the **Luhn algorithm** —
the same one that protects credit card numbers. Let's walk through it on a classic textbook number, `7992739871`,
whose correct check digit is **3**.
"""),
code('''
payload = "7992739871"
rows = []
for position, ch in enumerate(reversed(payload)):     # walk from the RIGHT
    digit = int(ch)
    doubled = position % 2 == 0                        # double the rightmost digit, then every second one
    value = digit * 2 if doubled else digit
    if value > 9:
        value -= 9                                     # e.g. 8*2 = 16 -> 16 - 9 = 7
    rows.append({"digit": digit, "doubled?": doubled, "contributes": value})

walk = pd.DataFrame(rows)
total = walk["contributes"].sum()
print(walk.to_string(index=False))
print(f"\\nTotal = {total}.  Check digit = (10 - {total} % 10) % 10 = {(10 - total % 10) % 10}")
'''),
md("""
If someone mistypes a single digit, the check digit almost always stops matching — so validation code can flag it
at the registration desk instead of the error spreading through every system downstream. (You'll hunt real-world
versions of this error in Module 5.)

## Part 5 · Build your own mini-population

Now let's build a small synthetic population from scratch, the same way the platform does it:
1. draw ages from South Africa's young age structure,
2. assign sex,
3. give each person a condition with an **age-dependent probability**,
4. check the result against the targets.
"""),
code('''
from ilanga.generator import AGE_BANDS, HTN_PREV

rng = np.random.default_rng(42)
n = 5000

weights = np.array([w for _, _, w in AGE_BANDS]); weights = weights / weights.sum()
band = rng.choice(len(AGE_BANDS), size=n, p=weights)
age = np.array([rng.uniform(AGE_BANDS[b][0], AGE_BANDS[b][1]) for b in band]).astype(int)
sex = np.where(rng.random(n) < 0.53, "F", "M")

def htn_probability(a):
    for (lo, hi), p in HTN_PREV.items():
        if lo <= a < hi:
            return p

p_htn = np.array([htn_probability(a) for a in age])
has_htn = rng.random(n) < p_htn          # each person "rolls the dice" against their own probability

mini = pd.DataFrame({"age": age, "sex": sex, "has_hypertension": has_htn})
mini.head()
'''),
code('''
# Did we hit the targets?
mini["band"] = pd.cut(mini["age"], bins=[0, 15, 35, 50, 65, 200], right=False,
                      labels=["0-14", "15-34", "35-49", "50-64", "65+"])
check = mini.groupby("band", observed=True)["has_hypertension"].mean().to_frame("observed")
check["target"] = [p for p in HTN_PREV.values()]
check.round(3)
'''),
md("""
> 💻 **Code Corner — the law of large numbers**
>
> Observed rates wobble around the target because of chance. The more people you simulate, the closer they get.
> Try changing `n = 5000` to `n = 200`, re-run, and watch the wobble grow. This is exactly why small clinics show
> "strange" monthly indicators — small numbers are noisy. Keep that in mind before you blame a nurse for a bad month.

## Part 6 · Validate the platform against its specification

A data engineer never assumes a dataset matches its spec — they **test** it. Here is Ilanga's population pyramid
and its hypertension prevalence compared to the generator's parameters.
"""),
code('''
pat = district.patients.copy()
pat["age"] = ilanga.age_years(pat["date_of_birth"], ilanga.REFERENCE_DATE)
pat["band5"] = (pat["age"] // 5 * 5).clip(upper=80)

pyramid = pat.groupby(["band5", "sex"]).size().unstack(fill_value=0)
fig, ax = plt.subplots(figsize=(7, 5))
ax.barh(pyramid.index, -pyramid["M"], height=4, color=BRAND["navy"], label="Male")
ax.barh(pyramid.index, pyramid["F"], height=4, color=BRAND["ochre"], label="Female")
ax.set_yticks(pyramid.index, [f"{b}-{b+4}" if b < 80 else "80+" for b in pyramid.index])
ax.set_xticks(ax.get_xticks(), [f"{abs(int(x)):,}" for x in ax.get_xticks()])
ax.set_title("Ilanga District — registered population, end 2025"); ax.legend()
plt.show()
'''),
code('''
htn_ids = set(district.conditions.loc[district.conditions["condition"] == "Hypertension", "patient_id"])
pat["has_htn"] = pat["patient_id"].isin(htn_ids)
pat["htn_band"] = pd.cut(pat["age"], bins=[0, 15, 35, 50, 65, 200], right=False,
                         labels=["0-14", "15-34", "35-49", "50-64", "65+"])
v = pat.groupby("htn_band", observed=True)["has_htn"].mean().to_frame("observed")
v["target"] = list(HTN_PREV.values())
v["within_2pp"] = (v["observed"] - v["target"]).abs() <= 0.02
v
'''),
md("""
The platform passes its own spec. That habit — **write down what the data should look like, then test it** — is how
enterprise data teams catch broken pipelines before a client does.

---
## 🎯 Your turn
Hints: `ilanga.hint("NQ-003.1")`, `("NQ-003.2")`, `("NQ-003.3")` — levels 1 to 3.

### 🌱 Seedling — how many SA ID numbers in the register are valid?
Use `ilanga.sa_id.is_valid` on patients whose `id_type` is `"SA_ID"`. Store an integer in `n_valid_ids`.
"""),
ex('''
n_valid_ids = None   # 👈 your code here
print(n_valid_ids)
''', '''
ids = district.patients.loc[district.patients["id_type"] == "SA_ID", "sa_id_number"]
n_valid_ids = int(ids.apply(ilanga.sa_id.is_valid).sum())
print(n_valid_ids, "of", len(ids))
'''),
md("""
### 🌿 Sapling — write your own Luhn function
Write `my_luhn(first12)` that takes the first 12 digits of an SA ID (as text) and returns the check digit as an `int`.
Don't call the platform's function — the point is an *independent* implementation.
"""),
ex('''
def my_luhn(first12):
    # 👈 your code here
    return None

print(my_luhn("800101500008"))   # try it out
''', '''
def my_luhn(first12):
    total = 0
    for position, ch in enumerate(reversed(first12)):
        d = int(ch)
        if position % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return (10 - total % 10) % 10

print(my_luhn("800101500008"))
'''),
md("""
### 🌳 Baobab — prototype asthma for the next dataset release
Build `mini_population`: a DataFrame of **5,000** people with columns `age`, `sex` and `has_asthma`.
Target prevalence: about **8% in children under 15** and **5% in people 15 and older** (illustrative rates).
Use a seed so it's reproducible, then show observed vs target.
"""),
ex('''
mini_population = None   # 👈 your code here
''', '''
rng = np.random.default_rng(2027)
n = 5000
band = rng.choice(len(AGE_BANDS), size=n, p=weights)
age = np.array([rng.uniform(AGE_BANDS[b][0], AGE_BANDS[b][1]) for b in band]).astype(int)
sex = np.where(rng.random(n) < 0.53, "F", "M")
prob = np.where(age < 15, 0.08, 0.05)
mini_population = pd.DataFrame({"age": age, "sex": sex, "has_asthma": rng.random(n) < prob})

print("children:", round(mini_population.loc[mini_population.age < 15, "has_asthma"].mean(), 3), "target 0.08")
print("15+     :", round(mini_population.loc[mini_population.age >= 15, "has_asthma"].mean(), 3), "target 0.05")
'''),
md("""
## 🚦 Quality gate
"""),
code('''
passed = ilanga.tickets.check_nq003(n_valid_ids, my_luhn, mini_population)
'''),
md("""
## 📝 Handover note
> **NQ-003 — done.**
> *ID validation: …  My Luhn implementation agrees with the platform on …*
> *Asthma prototype: observed rates were … against targets of 8% and 5%.*
> *One limitation of synthetic data the team should keep in mind: …*

## 🧭 Career Lens
Designing test data, validating datasets against specifications and double-implementing critical logic are core
**data engineering** and **QA / test analyst** skills. Every EMR rollout — e-Impilo included — needs people who can
build safe, realistic test patients before real ones ever touch the system.

## 📚 Glossary
**Synthetic data** – artificial records that mimic real patterns · **Seed** – starting value that makes randomness
repeatable · **Check digit** – extra digit that detects typing errors · **Luhn algorithm** – the check-digit method
used in SA ID numbers · **Specification** – written description of what data should look like

## ✅ Checkpoint
<details><summary>1. Why can't we use real patient records in Colab for learning?</summary>Health data is special personal information under POPIA, learners have no authorisation to process it, and Colab servers may be outside SA (cross-border transfer rules).</details>
<details><summary>2. What two personal details can be read straight from an SA ID number?</summary>Date of birth and registered sex (plus citizenship status).</details>
<details><summary>3. A clinic of 40 patients shows diabetes jumping from 10% to 17% in a month. First thought?</summary>Small numbers are noisy — check the counts before assuming a real change.</details>

**Next up → Module 04:** A university wants Ilanga's HIV data for research. Your job: make that possible *without*
exposing a single patient.
"""),
md(FOOTER),
]

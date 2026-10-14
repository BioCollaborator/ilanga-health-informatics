from nb import md, code, ex, SETUP, FOOTER, colab_badge

PATH = "notebooks/phase4_advanced/M15_nlp_genai_multilingual.ipynb"

CELLS = [
md(f"""
# Module 15 · Words as data — clinical notes, multilingual triage and responsible GenAI
**BioCollaborator Health Informatics Programme** · Phase 4: Advanced & Capstone · *Innovate Naturally*

{colab_badge(PATH)}

> **File → Save a copy in Drive**, then run cells top to bottom with **Shift + Enter**.
"""),
code(SETUP),
code('''
import re, json

ilanga.brand.banner(15, "Words as data: clinical NLP & responsible GenAI", "Phase 4 · Advanced & Capstone", minutes=150)
ilanga.brand.ticket(
    "NQ-015", "Thandeka Mbatha", "District Health Helpline Coordinator, Ilanga District Health Services",
    "Structure clinical notes and triage the WhatsApp helpline",
    "Two problems. First, e-Impilo notes are free text, so we can't easily audit TB screening or blood pressure "
    "control. Second, our WhatsApp helpline gets hundreds of messages - in English, isiZulu and a mix of both - and one "
    "person reads them in order. A pregnant woman who is bleeding waits behind someone asking about their appointment. "
    "Everyone is talking about AI. I need something that works, that we can check, and that never misses an emergency.",
    ["Blood pressure extracted from every note",
     "TB symptoms extracted with negation handled ('no fever' is not fever)",
     "A triage function that catches 100% of urgent messages and routes the rest accurately",
     "A short safety and privacy assessment for using large language models"],
    priority="High - patient safety")
'''),
md("""
## Part 1 · Text is data too

Much of what matters clinically lives in free text. South African notes add their own flavour:

| Shorthand | Meaning |
|---|---|
| `c/o` | complains of |
| `x3/52`, `x2/12` | for 3 weeks, for 2 months |
| `NS +` / `NS -` | night sweats present / absent |
| `LOW` | loss of weight |
| `afebrile` | no fever |
| `defaulted` | stopped attending or taking treatment |

And patients write the way people speak: South Africa has **twelve official languages** (South African Sign Language
became the twelfth in 2023), and people move between them mid-sentence. That's **code-switching**, and any tool
that only understands one language will fail many South Africans.
"""),
code('''
d = ilanga.load_district()
notes = d.clinical_notes
for t in notes["note_text"].sample(6, random_state=4):
    print("•", t)
'''),
md("""
### An annotated gold standard

To know whether an NLP tool works, you need notes where **clinicians have already marked the right answers**.
That's `note_annotations`. Building one is slow, expert work, and it's the foundation of any trustworthy clinical NLP.
"""),
code('''
gold = notes.merge(d.note_annotations, on="note_id")
gold[["note_text", "cough", "fever", "night_sweats", "weight_loss", "bp_systolic", "bp_diastolic"]].head(4)
'''),
md("""
## Part 2 · Regular expressions: precise patterns

A **regular expression** describes a text pattern. `\\d{2,3}` means "2 or 3 digits"; `\\s*` means "any spaces";
brackets `( )` **capture** the parts you want.
"""),
code('''
pattern = r"T\\s*(\\d{2}\\.\\d)"          # a temperature like "T 38.4"
for t in ["febrile, T 38.4", "afebrile", "hot at night, T 38.1"]:
    m = re.search(pattern, t)
    print(f"{t!r:28} ->", m.group(1) if m else None)
'''),
md("""
### 🌱 Seedling — extract blood pressure
Write `extract_bp(note)` returning `(systolic, diastolic)` as floats, or `(np.nan, np.nan)` if the note has no blood
pressure. Hints: `ilanga.hint("NQ-015.1")`.
"""),
ex('''
def extract_bp(note):
    # 👈 your code here
    return (np.nan, np.nan)

extract_bp("Pt no fever. BP 152/96 mmHg. adherence good.")
''', '''
def extract_bp(note):
    m = re.search(r"BP\\s*(\\d{2,3})\\s*/\\s*(\\d{2,3})", str(note))
    return (float(m.group(1)), float(m.group(2))) if m else (np.nan, np.nan)

extract_bp("Pt no fever. BP 152/96 mmHg. adherence good.")
'''),
md("""
## Part 3 · Negation: the hardest easy problem

A keyword search for "fever" matches "**no** fever", "denies fever" and "a**febrile**". Clinical NLP handles this
with **negation detection** — the classic NegEx approach looks for negation cues ("no", "denies", "nil") near a
symptom. Our notes are short, so a simple version works: split the note into **clauses**, and decide each clause on
its own.
"""),
code('''
def clauses(note):
    return [c.strip().lower() for c in re.split(r"[,.]", note) if c.strip()]

print(clauses("Pt c/o cough x3/52, afebrile, NS +, nil wt loss. TB screen positive."))
print(clauses("Pt febrile, T 38.4."))    # ⚠️ notice what happens to the temperature
'''),
md("""
### 🌿 Sapling — TB symptom screen
Write `tb_symptoms(note)` returning a dict with keys `cough`, `fever`, `night_sweats` and `weight_loss` (each
`True`/`False`) — **present and not negated**. The gate needs ≥ 95% accuracy for every symptom against the clinicians'
annotations. Hints: `ilanga.hint("NQ-015.2")`.
"""),
ex('''
def tb_symptoms(note):
    # 👈 your code here
    return {"cough": False, "fever": False, "night_sweats": False, "weight_loss": False}

tb_symptoms("Pt c/o cough x3/52, afebrile, NS +, nil wt loss.")
''', '''
# Negation cues can appear anywhere in a clause - "Pt no fever" does not START with "no".
NEGATION = re.compile(r"\\b(no|not|denies|nil|never)\\b|afebrile|stable")
KEYWORDS = {
    "cough": [r"cough"],
    "fever": [r"fever", r"febrile", r"\\bt\\s*3[89]\\b"],
    "night_sweats": [r"night sweats", r"\\bns\\b"],
    "weight_loss": [r"\\blow\\b", r"wt loss", r"lost \\d+\\s*kg"],
}

def tb_symptoms(note):
    found = {k: False for k in KEYWORDS}
    for cl in clauses(note):
        negated = bool(NEGATION.search(cl)) or cl.endswith("-")
        for symptom, patterns in KEYWORDS.items():
            if any(re.search(p, cl) for p in patterns) and not negated:
                found[symptom] = True
    return found

tb_symptoms("Pt c/o cough x3/52, afebrile, NS +, nil wt loss.")
'''),
code('''
# Evaluate against the gold standard: precision, recall and accuracy per symptom
if tb_symptoms("Pt cough +.")["cough"]:
    pred = pd.DataFrame(list(gold["note_text"].apply(tb_symptoms)))
    rows = []
    for s in ["cough", "fever", "night_sweats", "weight_loss"]:
        t, p = gold[s].astype(bool).values, pred[s].values
        tp, fp, fn = (t & p).sum(), (~t & p).sum(), (t & ~p).sum()
        rows.append({"symptom": s, "precision": tp / max(tp + fp, 1), "recall": tp / max(tp + fn, 1), "accuracy": (t == p).mean()})
    display(pd.DataFrame(rows).set_index("symptom").round(3))
'''),
md("""
> 💻 **Code Corner — two traps in those clauses**
>
> Run the cell above and look carefully. First, splitting on full stops also splits **"T 38.4"** into `t 38` and `4`,
> so a pattern that expects the decimal point will never match. Second, the first clause carries the note's opening
> word: **"Pt no fever"** does *not* start with "no". A negation test that only checks the start of a clause will
> mark that as fever present. Both traps are silent — your code runs fine and quietly gets the wrong answer, which is
> exactly why we evaluate against the clinicians' annotations rather than trusting the code.

> 🩺 **Clinic Corner — why this matters for TB**
>
> South Africa screens for TB using symptoms like these. If notes say "cough + NS +" but nobody sent sputum, the
> patient may have been missed. Extracting symptoms lets a district **audit screening quality across thousands of
> notes** — something no manager could do by reading.

## Part 4 · Multilingual helpline triage

Helpline messages arrive in English, isiZulu and code-switched mixes. Some are emergencies.
"""),
code('''
msgs = d.helpdesk_messages
display(msgs.groupby(["intent", "language"]).size().unstack(fill_value=0))
for _, m in msgs[msgs["intent"] == "urgent"].drop_duplicates("message_text").head(6).iterrows():
    print(f"[{m['language']}] {m['message_text']}")
'''),
md("""
> 🤝 **Ubuntu Moment — safety first, then efficiency**
>
> In triage, errors aren't equal. Sending an appointment question to the urgent queue wastes a few minutes. Sending
> *"Ngiyopha kakhulu futhi ngikhulelwe"* ("I'm bleeding heavily and I'm pregnant") to the appointments queue could
> cost two lives. So we design for **100% recall on urgent messages** first, and accept some false alarms.

*A note on language:* Ilanga's isiZulu messages are short and templated, and should be reviewed by first-language
speakers before wider use. Real deployments must be built and tested **with** speakers of every language they serve.

### 🌳 Baobab — the triage function
Write `triage(message)` returning one of: `"urgent"`, `"medication"`, `"results"`, `"appointment"`, `"feedback"`.
Gate: **every** urgent message caught, and overall accuracy **≥ 85%**. Hints: `ilanga.hint("NQ-015.3")`.
"""),
ex('''
def triage(message):
    # 👈 your code here
    return "feedback"

triage("Ngiyopha kakhulu futhi ngikhulelwe.")
''', '''
RULES = [
    ("urgent", ["bleeding", "ngiyopha", "breathing", "ayiphefumuli", "fits", "blurred vision", "severe headache",
                "won't wake", "please help"]),
    ("medication", ["pills", "tablets", "meds", "amaphilisi", "aphelile", "ngiphelelwe"]),
    ("results", ["results", "imiphumela", "viral load"]),
    ("appointment", ["appointment", "clinic date", "change my", "emtholampilo", "come ngo", "when is my next"]),
]

def triage(message):
    t = str(message).lower()
    for intent, words in RULES:
        if any(w in t for w in words):
            return intent
    return "feedback"

pred = msgs["message_text"].apply(triage)
print(f"Urgent recall: {(pred[msgs.intent == 'urgent'] == 'urgent').mean():.0%}   Overall accuracy: {(pred == msgs.intent).mean():.1%}")
pd.crosstab(msgs["intent"], pred, rownames=["true"], colnames=["predicted"])
'''),
md("""
## Part 5 · Large language models: power, limits and responsibility

Large language models (LLMs) can summarise notes, extract fields and understand many languages without hand-written
rules. They can also **invent facts** ("hallucinate"), perform unevenly across languages (often weaker in isiZulu than
English), and behave differently when the model version changes.

Before using an LLM with health data in South Africa, answer these questions:

| Question | Why it matters |
|---|---|
| **Is personal information leaving the organisation?** | Sending notes to an external API is processing by a third party and often a **cross-border transfer** under POPIA. De-identify first, and have an operator agreement. |
| **Is it making or informing clinical decisions?** | Software intended for diagnosis or treatment may be regulated as a **medical device** by SAHPRA. Check current guidance before deploying. |
| **How do we know it's right?** | Evaluate against a gold standard (like `note_annotations`), per language, before and after every model change. |
| **Who is accountable?** | A named person reviews outputs; the model never has the final word on care. |
| **What happens when it fails?** | Rule-based safety nets (like Part 4's urgent keywords) stay in place underneath. |

### Optional: try an LLM on a synthetic note

If you have a Claude API key, add it to Colab **Secrets** (🔑) as `ANTHROPIC_API_KEY`. The cell asks the model to
return structured JSON and compares the answer with the clinicians' annotations. Without a key, it skips itself.
Model names change over time — check [the Claude API documentation](https://docs.claude.com/en/api/overview) for
current ones. Other providers and open models work the same way in principle.
"""),
code('''
MODEL = "claude-haiku-4-5-20251001"   # check the docs for current model names

try:
    from google.colab import userdata
    api_key = userdata.get("ANTHROPIC_API_KEY")
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "anthropic"], check=True)
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    sample = gold.sample(5, random_state=11)
    for _, row in sample.iterrows():
        prompt = ("Extract from this South African clinical note. Reply with JSON only, keys: cough, fever, "
                  "night_sweats, weight_loss (true/false, true only if present and not negated).\\n\\nNote: " + row["note_text"])
        reply = client.messages.create(model=MODEL, max_tokens=200, messages=[{"role": "user", "content": prompt}])
        text = reply.content[0].text.strip().removeprefix("```json").removesuffix("```").strip()
        llm = json.loads(text)
        truth = {s: bool(row[s]) for s in ["cough", "fever", "night_sweats", "weight_loss"]}
        print("NOTE :", row["note_text"])
        print("LLM  :", llm, "✅" if llm == truth else "❌ differs from clinicians", "\\n")
except Exception as err:
    print("ℹ️ LLM demo skipped (", type(err).__name__, ") - add ANTHROPIC_API_KEY to Colab Secrets to try it.")
'''),
md("""
> 💻 **Code Corner — rules or LLMs?**
>
> Use **rules** when the pattern is regular, the stakes are high and you need full explainability (blood pressure,
> urgent keywords). Use **LLMs** when language is varied and a human reviews the output (summaries, drafting replies).
> The strongest systems combine both: LLMs for breadth, rules as guard-rails, and humans for accountability.

## 🚦 Quality gate
"""),
code('''
passed = ilanga.tickets.check_nq015(extract_bp, tb_symptoms, triage)
'''),
md("""
## 📝 Handover note — for Thandeka Mbatha
> **NQ-015 — done.**
> *Notes: blood pressure extracted with …% accuracy; TB symptom accuracy ranged from …% (…) to …% (…).*
> *Helpline: triage catches 100% of urgent messages in all three language groups; overall accuracy …%. Urgent messages
> should jump the queue immediately and trigger a call-back.*
> *LLM assessment: … Recommendation: …*

## 🧭 Career Lens
**Clinical NLP engineers**, **AI product managers** and **responsible-AI / AI governance specialists** are among the
fastest-growing roles in health tech. African-language NLP is a genuine frontier: researchers and communities across
the continent are building datasets and models for languages the big tech models still serve poorly. Speakers of
those languages who can also code are rare and needed.

## 📚 Glossary
**NLP** – natural language processing · **Regular expression** – a text pattern · **Negation detection** – recognising
when a finding is ruled out · **Gold standard** – expert-annotated data used for evaluation · **Code-switching** –
mixing languages in one utterance · **LLM** – large language model · **Hallucination** – confident but false output ·
**Guard-rail** – a rule that constrains an AI system's behaviour

## ✅ Checkpoint
<details><summary>1. Why does a plain keyword search for "fever" fail?</summary>It matches negations such as "no fever", "denies fever" and "afebrile".</details>
<details><summary>2. Why design triage for 100% urgent recall rather than best overall accuracy?</summary>Missing an emergency can cost lives; a false alarm only costs time.</details>
<details><summary>3. Name two POPIA concerns with sending clinical notes to an external LLM API.</summary>Third-party processing (needs an operator agreement and safeguards) and cross-border transfer; de-identify first and minimise what's sent.</details>

**Next up → Module 16 · Capstone:** Everything you've learned, in one report to the district.
"""),
md(FOOTER),
]

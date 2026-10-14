from nb import md, code, ex, SETUP, FOOTER, colab_badge

PATH = "notebooks/phase2_data_engineering/M07_interoperability_hl7_fhir.ipynb"

CELLS = [
md(f"""
# Module 07 · Systems that talk — HL7 v2 messages and FHIR resources
**BioCollaborator Health Informatics Programme** · Phase 2: Data Engineering · *Innovate Naturally*

{colab_badge(PATH)}

> **File → Save a copy in Drive**, then run cells top to bottom with **Shift + Enter**.
"""),
code(SETUP),
code('''
import json
from ilanga import hl7, fhir

ilanga.brand.banner(7, "Systems that talk: HL7 v2 & FHIR", "Phase 2 · Data Engineering", minutes=150)
ilanga.brand.ticket(
    "NQ-007", "Lerato Mokoena", "e-Impilo Implementation Lead, Ilanga District Health Services",
    "Prototype the lab-results interface: NHLS messages into e-Impilo",
    "Today, lab results for our e-Impilo sites arrive as HL7 v2 messages, and for paper sites they're printed. "
    "e-Impilo is built around FHIR. Before the vendor workshop I need a working prototype that reads the "
    "lab's messages and produces valid FHIR Observations - including the awkward results, like '<50' viral loads "
    "and Xpert text results.",
    ["A function that reads any field from an HL7 v2 message (including the MSH quirk)",
     "A converter that turns a batch of messages into a tidy table",
     "A function that turns a lab result into a valid FHIR R4 Observation",
     "A handover note on what a production interface would still need"],
    priority="High - vendor workshop")
'''),
md("""
## Part 1 · Four layers of interoperability

| Layer | Question | Example |
|---|---|---|
| **Foundational** | Can data move at all? | A network link between the lab and the clinic |
| **Structural** | Is the format agreed? | HL7 v2 message segments; FHIR JSON resources |
| **Semantic** | Is the meaning agreed? | LOINC `20447-9` means HIV-1 viral load everywhere (Module 6) |
| **Organisational** | Are governance, trust and workflow agreed? | Data-sharing agreements, consent, who fixes errors |

South Africa's **Health Normative Standards Framework (HNSF)** set out the standards the public health sector should
use for interoperability, and national digital health strategies have built on it. e-Impilo exchanges data using
international standards like **HL7 FHIR**. Most technical work lives in the structural and semantic layers;
most *failures* happen in the organisational one.

## Part 2 · Reading HL7 v2

HL7 version 2 has been the workhorse of hospital and lab interfaces since the 1990s, and it's still everywhere.
A message is plain text:

- **Segments** (lines) separated by a carriage return `\\r`, each starting with a 3-letter name
- **Fields** separated by `|`
- **Components** within a field separated by `^`, and **repeats** separated by `~`
"""),
code('''
d = ilanga.load_district()
messages = hl7.lab_messages(d, limit=300, seed=3)
print(f"{len(messages)} messages. Here is one:\\n")
print(messages[0].replace("\\r", "\\n"))
'''),
md("""
| Segment | Meaning | Fields you'll use |
|---|---|---|
| **MSH** | Message header: who sent it, to whom, what type | MSH-5 receiving application · MSH-9 message type · MSH-12 version |
| **PID** | Patient identification | PID-3 identifiers · PID-5 name · PID-7 date of birth · PID-8 sex |
| **OBR** | Observation request (the test order) | OBR-2 order ID · OBR-3 specimen ID · OBR-4 test · OBR-7 collected · OBR-22 reported |
| **OBX** | Observation result | OBX-2 value type · OBX-3 test code · OBX-5 value · OBX-6 unit · OBX-8 flag |
"""),
code('''
# Split a message into segments and fields
msg = messages[0]
for segment in msg.split("\\r"):
    fields = segment.split("|")
    print(fields[0], "->", len(fields) - 1, "fields")

pid = [s for s in msg.split("\\r") if s.startswith("PID")][0].split("|")
print("\\nPID-3 (identifiers):", pid[3])
print("PID-5 (name):       ", pid[5], "->", pid[5].split("^"))
'''),
md("""
> 💻 **Code Corner — the MSH trap**
>
> In every segment, field *n* is at position *n* after splitting on `|` (position 0 is the segment name). **Except
> MSH.** In MSH, the `|` character *is* field MSH-1, so after splitting, MSH field *n* is at position *n − 1*.
> Every HL7 developer gets bitten by this once. Now you won't.

> 🩺 **Clinic Corner — the receiving application**
>
> Look at MSH-5 across messages: some say `EIMPILO`, others `RESULTS_PRINT`. Results for facilities that are live on
> e-Impilo flow electronically; for paper facilities, they're printed and physically delivered. That's another
> reason rural Ntaba's results reach clinicians later than turnaround time alone suggests.
"""),
code('''
receivers = pd.Series([m.split("\\r")[0].split("|")[4] for m in messages]).value_counts()
receivers
'''),
md("""
### 🌱 Seedling — read any field
Write `hl7_field(message, segment, field)` that returns the text of that field (e.g. `hl7_field(msg, "OBX", 5)`
returns the result value). It must handle MSH correctly. Hints: `ilanga.hint("NQ-007.1")`.
"""),
ex('''
def hl7_field(message, segment, field):
    # 👈 your code here
    return None

print(hl7_field(msg, "MSH", 9), "|", hl7_field(msg, "PID", 5), "|", hl7_field(msg, "OBX", 5))
''', '''
def hl7_field(message, segment, field):
    for seg in message.replace("\\n", "\\r").split("\\r"):
        parts = seg.split("|")
        if parts[0] == segment:
            index = field - 1 if segment == "MSH" else field
            return parts[index] if index < len(parts) else ""
    return None

print(hl7_field(msg, "MSH", 9), "|", hl7_field(msg, "PID", 5), "|", hl7_field(msg, "OBX", 5))
'''),
md("""
### 🌿 Sapling — from messages to a table
Write `hl7_to_dataframe(messages)` that returns a DataFrame with exactly these columns, one row per message:

| Column | Source |
|---|---|
| `specimen_id` | OBR-3 |
| `patient_id` | first component of the **first** identifier in PID-3 |
| `code` | first component of OBX-3 |
| `value` | OBX-5 (as text, exactly as sent) |
| `unit` | OBX-6 |

Hints: `ilanga.hint("NQ-007.2")`.
"""),
ex('''
def hl7_to_dataframe(messages):
    # 👈 your code here
    return pd.DataFrame()

hl7_to_dataframe(messages).head()
''', '''
def hl7_to_dataframe(messages):
    rows = []
    for m in messages:
        rows.append({
            "specimen_id": hl7_field(m, "OBR", 3),
            "patient_id": hl7_field(m, "PID", 3).split("~")[0].split("^")[0],
            "code": hl7_field(m, "OBX", 3).split("^")[0],
            "value": hl7_field(m, "OBX", 5),
            "unit": hl7_field(m, "OBX", 6),
        })
    return pd.DataFrame(rows)

hl7_to_dataframe(messages).head()
'''),
md("""
Notice the viral load values `<^50`: HL7's **structured numeric** type (OBX-2 = `SN`) splits the comparator and the
number into components. That's HL7's own way of storing a censored value — the same problem you solved in Module 5.

## Part 3 · FHIR: resources for the web era

**FHIR** (Fast Healthcare Interoperability Resources) models health data as **resources** — Patient, Observation,
Encounter, MedicationDispense and about 150 more — exchanged as JSON over web APIs. If you've used a website API,
FHIR will feel familiar. It's what modern EMRs, including e-Impilo, are built to speak.
"""),
code('''
patient_row = d.patients.iloc[0]

patient = {
    "resourceType": "Patient",
    "id": patient_row["patient_id"],
    "identifier": [{"system": fhir.ILANGA_PATIENT_ID, "value": patient_row["patient_id"]}],
    "name": [{"family": patient_row["surname"], "given": [patient_row["first_name"]]}],
    "gender": {"F": "female", "M": "male"}.get(patient_row["sex"], "unknown"),
    "birthDate": patient_row["date_of_birth"].strftime("%Y-%m-%d"),
}
print(json.dumps(patient, indent=2))
print("Validation issues:", fhir.validate(patient) or "none ✅")
'''),
md("""
> 💻 **Code Corner — JSON is just dictionaries and lists**
>
> A FHIR resource in Python is a **dictionary** (Module 2!) containing strings, numbers, lists and more dictionaries.
> `json.dumps` turns it into JSON text for sending; `json.loads` turns JSON text back into a dictionary.

> 🩺 **Clinic Corner — identifiers need a namespace**
>
> An identifier is only meaningful with its **system**: "8004309360083" means nothing until you know it's an SA ID
> number. Real national systems publish official identifier namespaces in their implementation guides.
> We use made-up `ilanga.example` addresses, because Ilanga isn't real.

### An Observation
"""),
code('''
lab = d.lab_results
hba1c = lab[lab["test_code"] == "HBA1C"].iloc[0]

observation = {
    "resourceType": "Observation",
    "status": "final",
    "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                              "code": "laboratory"}]}],
    "code": {"coding": [{"system": "http://loinc.org", "code": hba1c["loinc_code"], "display": hba1c["test_name"]}]},
    "subject": {"reference": f"Patient/{hba1c['patient_id']}"},
    "effectiveDateTime": hba1c["collected_at"].strftime("%Y-%m-%dT%H:%M:00+02:00"),
    "valueQuantity": {"value": float(hba1c["result_numeric"]), "unit": "%", "system": "http://unitsofmeasure.org", "code": "%"},
}
print(json.dumps(observation, indent=2))
print("Validation issues:", fhir.validate(observation) or "none ✅")
'''),
code('''
# What does the validator catch? Break the resource on purpose:
broken = dict(observation, status="done", subject={"reference": "ILN-P-000001"},
              valueQuantity={"value": "7.9"})
fhir.validate(broken)
'''),
md("""
### Censored and text results in FHIR

- A viral load **<50** becomes `valueQuantity` with `"comparator": "<"` and `"value": 50`. (FHIR has a field for
  exactly this. No more "LDL" strings.)
- An **Xpert** result is text: use `valueString`. It has no LOINC code in our data (Module 6), so code it with the
  **local** code system, clearly labelled as local, until terminology review is done.

### 🌳 Baobab — lab result → FHIR Observation
Write `lab_to_observation(row)` that takes **one row** of `d.lab_results` and returns a valid FHIR Observation dict:
- `status` `"final"`, a `subject` reference to the patient, and an `effectiveDateTime`
- LOINC coding when `loinc_code` exists; otherwise the local system `https://fhir.ilanga.example/CodeSystem/local-lab`
  with the `test_code`
- the right value: `valueQuantity` (with `comparator` for below-limit viral loads) or `valueString` for Xpert

Hints: `ilanga.hint("NQ-007.3")`.
"""),
ex('''
def lab_to_observation(row):
    # 👈 your code here
    return {}

vl_ldl = lab[lab["below_detection_limit"]].iloc[0]
print(json.dumps(lab_to_observation(vl_ldl), indent=2))
''', '''
LOCAL_LAB = "https://fhir.ilanga.example/CodeSystem/local-lab"

def lab_to_observation(row):
    if pd.notna(row["loinc_code"]):
        coding = {"system": "http://loinc.org", "code": row["loinc_code"], "display": row["test_name"]}
    else:
        coding = {"system": LOCAL_LAB, "code": row["test_code"], "display": row["test_name"]}
    obs = {
        "resourceType": "Observation",
        "id": row["specimen_id"],
        "status": "final",
        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                  "code": "laboratory"}]}],
        "code": {"coding": [coding]},
        "subject": {"reference": f"Patient/{row['patient_id']}"},
        "effectiveDateTime": row["collected_at"].strftime("%Y-%m-%dT%H:%M:00+02:00"),
    }
    if row["test_code"] == "XPERT":
        obs["valueString"] = row["result_text"]
    elif row["below_detection_limit"]:
        obs["valueQuantity"] = {"value": 50, "comparator": "<", "unit": row["unit"]}
    else:
        obs["valueQuantity"] = {"value": float(row["result_numeric"]), "unit": row["unit"]}
    return obs

vl_ldl = lab[lab["below_detection_limit"]].iloc[0]
print(json.dumps(lab_to_observation(vl_ldl), indent=2))
'''),
md("""
## Part 4 · Bundles: sending many resources at once

A **Bundle** packages resources together. A `transaction` bundle asks the server to create all of them — or none.
"""),
code('''
if lab_to_observation(vl_ldl):
    sample = lab[lab["patient_id"] == vl_ldl["patient_id"]]
    bundle = {"resourceType": "Bundle", "type": "transaction", "entry": [
        {"resource": lab_to_observation(r), "request": {"method": "POST", "url": "Observation"}}
        for _, r in sample.iterrows()]}
    print(f"Bundle with {len(bundle['entry'])} observations. Issues:", fhir.validate(bundle) or "none ✅")
'''),
md("""
### Optional: send to a real FHIR test server (internet required)

The HAPI FHIR project runs a **public test server**. Anything you send is visible to anyone on the internet — which
is exactly why we only ever send **synthetic** data. (Module 4: never, ever send real patient data to a public server.)
This cell is optional and not part of the quality gate; public test servers are sometimes slow or offline.
"""),
code('''
SEND_TO_PUBLIC_SERVER = False   # change to True to try it

if SEND_TO_PUBLIC_SERVER:
    import urllib.request
    req = urllib.request.Request("https://hapi.fhir.org/baseR4/Patient", method="POST",
                                 data=json.dumps(patient).encode(), headers={"Content-Type": "application/fhir+json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print("Server replied:", resp.status, resp.headers.get("Location"))
    except Exception as err:
        print("The public server didn't respond this time:", err)
'''),
md("""
## 🚦 Quality gate
"""),
code('''
passed = ilanga.tickets.check_nq007(hl7_field, hl7_to_dataframe, lab_to_observation)
'''),
md("""
## 📝 Handover note — for the vendor workshop
> **NQ-007 — prototype done. For: Lerato Mokoena.**
> *The prototype parses … messages and produces valid FHIR Observations for all test types.*
> *Before production, the interface still needs: acknowledgements (ACK messages), error queues, patient matching
> against the MPI, official identifier namespaces, terminology review for Xpert, security and audit logging, and …*

## 🧭 Career Lens
**Integration engineers** and **interface analysts** are among the best-paid people in health IT, and they're scarce
in South Africa. EMR rollouts, lab system upgrades and every "why didn't the result arrive?" incident need someone
who can read an HL7 message and a FHIR resource side by side. Pair this with Module 6 and you're genuinely rare.

## 📚 Glossary
**HL7 v2** – pipe-delimited messaging standard · **Segment / field / component** – line / `|` part / `^` part ·
**ORU^R01** – unsolicited observation result message · **FHIR** – resource-based standard using JSON and web APIs ·
**Resource** – a unit of FHIR data (Patient, Observation…) · **Bundle** – a package of resources · **HNSF** – Health
Normative Standards Framework · **Structural / semantic interoperability** – shared format / shared meaning

## ✅ Checkpoint
<details><summary>1. After splitting an MSH segment on "|", where is MSH-9?</summary>At index 8, because MSH-1 is the field separator itself.</details>
<details><summary>2. How does FHIR represent a viral load of "<50 copies/mL"?</summary>valueQuantity with comparator "<" and value 50.</details>
<details><summary>3. Why is it fine to send Ilanga data to the public HAPI server but never real data?</summary>Everything on a public test server is visible to anyone. Ilanga data is synthetic; real data would be a POPIA breach.</details>

**Next up → Module 08:** You've cleaned, coded and exchanged data. Now you'll build the district data warehouse
that turns it into reports — with SQL and automated data tests.
"""),
md(FOOTER),
]

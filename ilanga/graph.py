"""
Graph helpers: a NetworkX knowledge graph (runs anywhere) and an optional Neo4j loader.

The Neo4j functions need the `neo4j` Python driver and a database (e.g. a free Neo4j AuraDB instance).
Only synthetic Ilanga data should ever be loaded into a cloud database you use for learning.
"""
from __future__ import annotations

import json

import networkx as nx
import pandas as pd


def build_knowledge_graph(district) -> nx.MultiDiGraph:
    """Patients, facilities, conditions, medicines and lab results as one graph."""
    d = district
    G = nx.MultiDiGraph()
    for f in d.facilities.itertuples():
        G.add_node(f.facility_id, label="Facility", name=f.facility_name, type=f.facility_type, subdistrict=f.subdistrict)
    for p in d.patients.itertuples():
        G.add_node(p.patient_id, label="Patient", sex=p.sex, subdistrict=p.subdistrict)
        G.add_edge(p.patient_id, p.home_facility_id, type="REGISTERED_AT")
    for name in d.conditions["condition"].unique():
        G.add_node(f"COND:{name}", label="Condition", name=name)
    for c in d.conditions.itertuples():
        G.add_edge(c.patient_id, f"COND:{c.condition}", type="HAS_CONDITION", status=c.status)
    meds = d.dispensing.drop_duplicates(["patient_id", "atc_code"])
    for atc, name in d.dispensing.drop_duplicates("atc_code")[["atc_code", "medicine_name"]].itertuples(index=False):
        G.add_node(f"ATC:{atc}", label="Medicine", name=name, atc=atc)
    for m in meds.itertuples():
        G.add_edge(m.patient_id, f"ATC:{m.atc_code}", type="RECEIVED")
    vl = d.lab_results[d.lab_results["test_code"] == "VL"]
    for r in vl.itertuples():
        G.add_node(r.specimen_id, label="LabResult", test="VL", collected_at=r.collected_at,
                   suppressed=bool(r.below_detection_limit or (r.result_numeric < 1000)))
        G.add_edge(r.patient_id, r.specimen_id, type="HAS_RESULT")
    return G


# ------------------------------------------------------------------ Neo4j (optional)
CONSTRAINTS = [
    "CREATE CONSTRAINT facility_id IF NOT EXISTS FOR (f:Facility) REQUIRE f.id IS UNIQUE",
    "CREATE CONSTRAINT patient_id IF NOT EXISTS FOR (p:Patient) REQUIRE p.id IS UNIQUE",
]

LOAD_FACILITIES = """
UNWIND $rows AS r
MERGE (f:Facility {id: r.facility_id})
SET f.name = r.facility_name, f.type = r.facility_type, f.subdistrict = r.subdistrict
"""

LOAD_REFERRALS = """
UNWIND $rows AS r
MATCH (a:Facility {id: r.from_facility_id}), (b:Facility {id: r.to_facility_id})
MERGE (a)-[x:REFERS_TO]->(b)
SET x.referrals = r.referrals, x.arrived = r.arrived
"""

LOAD_PATIENTS = """
UNWIND $rows AS r
MERGE (p:Patient {id: r.patient_id})
SET p.sex = r.sex, p.subdistrict = r.subdistrict
WITH p, r
MATCH (f:Facility {id: r.home_facility_id})
MERGE (p)-[:REGISTERED_AT]->(f)
"""


def _rows(df: pd.DataFrame) -> list:
    return json.loads(df.to_json(orient="records", date_format="iso"))   # plain Python types for the driver


def load_to_neo4j(driver, district, database: str = "neo4j", batch: int = 2000) -> dict:
    """Load facilities, referral pathways and patients (no names or ID numbers) into Neo4j."""
    d = district
    ref = (d.referrals.assign(arrived=(d.referrals["outcome"] == "Seen").astype(int))
           .groupby(["from_facility_id", "to_facility_id"]).agg(referrals=("referral_id", "size"), arrived=("arrived", "sum"))
           .reset_index())
    pats = d.patients[["patient_id", "sex", "subdistrict", "home_facility_id"]]
    with driver.session(database=database) as s:
        for q in CONSTRAINTS:
            s.run(q)
        s.run(LOAD_FACILITIES, rows=_rows(d.facilities[["facility_id", "facility_name", "facility_type", "subdistrict"]]))
        s.run(LOAD_REFERRALS, rows=_rows(ref))
        for i in range(0, len(pats), batch):
            s.run(LOAD_PATIENTS, rows=_rows(pats.iloc[i:i + batch]))
    return {"facilities": len(d.facilities), "referral_pathways": len(ref), "patients": len(pats)}

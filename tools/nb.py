"""Tiny notebook builder: one source -> student edition + facilitator edition (no nbformat needed)."""
import json, os

REPO_SLUG = "BioCollaborator/ilanga-health-informatics"

def md(text):   return {"kind": "md", "src": text.strip("\n")}
def code(text): return {"kind": "code", "src": text.strip("\n")}
def ex(student, solution): return {"kind": "ex", "student": student.strip("\n"), "solution": solution.strip("\n")}

def _cell(cell_type, src):
    lines = src.split("\n")
    source = [l + "\n" for l in lines[:-1]] + [lines[-1]]
    c = {"cell_type": cell_type, "metadata": {}, "source": source}
    if cell_type == "code":
        c.update({"execution_count": None, "outputs": []})
    return c

def build(cells, path, edition):
    out = []
    for c in cells:
        if c["kind"] == "md":
            out.append(_cell("markdown", c["src"]))
        elif c["kind"] == "code":
            out.append(_cell("code", c["src"]))
        else:
            out.append(_cell("code", c["student"] if edition == "student" else c["solution"]))
    nb = {"cells": out, "metadata": {
            "colab": {"provenance": [], "toc_visible": True},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"}},
          "nbformat": 4, "nbformat_minor": 0}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(nb, fh, indent=1, ensure_ascii=False)

def colab_badge(relpath):
    url = f"https://colab.research.google.com/github/{REPO_SLUG}/blob/main/{relpath}"
    return f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({url})"

SETUP = '''
# ⚙️ SETUP — run this cell first (click it, then press Shift + Enter)
import os, sys, subprocess

REPO_URL = "https://github.com/''' + REPO_SLUG + '''.git"

def _find_repo():
    for p in [".", "..", "../..", "ilanga-health-informatics"]:
        if os.path.exists(os.path.join(p, "ilanga", "__init__.py")):
            return os.path.abspath(p)
    return None

root = _find_repo()
if root is None:                                  # first run in Colab: fetch the course code
    subprocess.run(["git", "clone", "-q", REPO_URL], check=True)
    root = os.path.abspath("ilanga-health-informatics")
if root not in sys.path:
    sys.path.insert(0, root)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ilanga

pd.set_option("display.max_columns", 30)
plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False})
BRAND = {"navy": "#0A2540", "ochre": "#C85A32", "teal": "#1A7A6E", "forest": "#14283E", "cream": "#F7F1E3"}
ilanga.hello()
'''

FOOTER = '''
---
<div align="center">

**BioCollaborator Health Informatics Programme** · *Innovate Naturally*<br>
Nqaba Health Informatics and Ilanga District are fictional. All data is synthetic.<br>
Questions and wins → the BioCollaborator **Health Career Hub** community.

</div>
'''

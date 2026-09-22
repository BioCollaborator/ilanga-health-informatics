"""Build student + facilitator editions of every module notebook.  Run: python tools/build_all.py"""
import importlib, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from nb import build

MODULES = ["m01", "m02", "m03", "m04"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for m in MODULES:
    mod = importlib.import_module(m)
    build(mod.CELLS, os.path.join(ROOT, mod.PATH), "student")
    fac_path = mod.PATH.replace("notebooks/", "facilitator/").replace(".ipynb", "_FACILITATOR.ipynb")
    build(mod.CELLS, os.path.join(ROOT, fac_path), "facilitator")
    print("built", mod.PATH)

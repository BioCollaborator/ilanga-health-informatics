"""Execute every facilitator notebook top-to-bottom and require its quality gate to pass.
Student notebooks are executed too (they must run without errors; their gate is expected to fail)."""
import glob, json, os, sys, traceback
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

def run(path):
    nb = json.load(open(path, encoding="utf-8"))
    ns = {"display": lambda *a, **k: None, "__name__": "__main__"}
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        try:
            exec(compile(src, f"{os.path.basename(path)}[cell {i}]", "exec"), ns)
        except Exception:
            traceback.print_exc()
            return False, f"error in cell {i}"
        plt.close("all")
    return True, ns.get("passed")

ok_all = True
for path in sorted(glob.glob("facilitator/**/*.ipynb", recursive=True)):
    ok, passed = run(path)
    print(f"{'OK ' if ok and passed else 'FAIL'}  facilitator  {path}  gate={passed}")
    ok_all &= bool(ok and passed)
for path in sorted(glob.glob("notebooks/**/*.ipynb", recursive=True)):
    ok, passed = run(path)
    print(f"{'OK ' if ok and not passed else 'FAIL'}  student      {path}  gate={passed}")
    ok_all &= bool(ok and not passed)
sys.exit(0 if ok_all else 1)

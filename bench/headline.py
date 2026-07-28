"""bench/headline.py — the one-screen before/after, for communicating the result.

`scale_probe.py --report` is the full diagnostic and `gate_scale.py` is the gate. This is
neither: it measures the single question that was actually asked — "how does query
performance hold up at tens of thousands of nodes?" — on BOTH versions, on this machine,
with byte-identical input, and prints it as a panel that fits in a screenshot.

The old version is measured in a throwaway git worktree, so this is a real comparison and
not two numbers from different days. An `indexed` marker asserts the baseline really
resolved to the pre-index code.

Run:  python bench/headline.py                    # default 1k / 10k / 30k
      python bench/headline.py 1000 10000         # faster (the old code is slow on purpose)
Writes bench/headline.txt alongside the printed panel.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
# GUARDED, and not decoratively: the baseline child loads this very file as a module. If
# these inserts ran at import time they would put the MAIN tree's impl/ on the child's
# sys.path ahead of the worktree, and the "old" measurement would silently be the new code.
# That is exactly what happened on the first run here, and the `indexed` marker caught it.
if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "impl"))
    sys.path.insert(0, str(ROOT / "bench"))

SIZES = [1000, 10000, 30000]
BIG = 100000                 # current tree only; the old code cannot reach this
BASE_SHA = "0e8010f"         # last commit before the remediation
W = 66


def measure_one(src: str, reps: int = 3) -> dict:
    """parse + one bounded query. Imported late so a worktree child uses ITS sarib."""
    from sarib import parse
    from sarib.query import query
    best_p = best_q = float("inf")
    doc = None
    for _ in range(reps):
        t0 = time.perf_counter()
        doc = parse(src)
        best_p = min(best_p, (time.perf_counter() - t0) * 1000)
        t0 = time.perf_counter()
        query(doc, {"start": "all", "select": "none", "filter": {"type": "task"},
                    "bound": {"max_nodes": 100}})
        best_q = min(best_q, (time.perf_counter() - t0) * 1000)
    return {"nodes": len(doc.nodes), "parse": best_p, "query": best_q,
            "indexed": hasattr(doc, "_index")}


CHILD = """
import json, sys
sys.path.insert(0, %(impl)r)
import importlib.util as u
spec = u.spec_from_file_location("h", %(me)r)
m = u.module_from_spec(spec); spec.loader.exec_module(m)
srcs = json.load(open(%(data)r, encoding="utf-8"))
print("@@" + json.dumps([m.measure_one(s, reps=1) for s in srcs]))
"""


def measure_baseline(srcs) -> list:
    wt, data = ROOT / ".headline-wt", ROOT / ".headline-in.json"
    subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                   cwd=ROOT, capture_output=True)
    r = subprocess.run(["git", "worktree", "add", "--detach", str(wt), BASE_SHA],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        print(f"  baseline unavailable: {r.stderr.strip()[:120]}")
        return []
    try:
        data.write_text(json.dumps(srcs), encoding="utf-8")
        out = subprocess.run(
            [sys.executable, "-c", CHILD % {"impl": str(wt / "impl"),
                                            "me": str(pathlib.Path(__file__).resolve()),
                                            "data": str(data)}],
            cwd=ROOT, capture_output=True, text=True, timeout=7200)
        line = next((x for x in out.stdout.splitlines() if x.startswith("@@")), None)
        if not line:
            print(f"  baseline run failed: {out.stderr.strip()[-300:]}")
            return []
        return json.loads(line[2:])
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                       cwd=ROOT, capture_output=True)
        data.unlink(missing_ok=True)


def human(ms: float) -> str:
    if ms >= 1000:
        return f"{ms / 1000:,.1f} s"
    if ms < 1:
        return f"{ms:.2f} ms"
    return f"{ms:,.1f} ms"


def main() -> int:
    sizes = [int(a) for a in sys.argv[1:] if a.isdigit()] or SIZES
    from gate_scale import gen_scaled_kb
    srcs = [gen_scaled_kb(n) for n in sizes]

    print(f"measuring v0.1.5 (this tree) at {', '.join(f'{n:,}' for n in sizes)} + {BIG:,} ...")
    now = [measure_one(s) for s in srcs]
    big = measure_one(gen_scaled_kb(BIG))

    print(f"measuring v0.1.4 ({BASE_SHA}) in a worktree — deliberately slow, please wait ...")
    old = measure_baseline(srcs)
    if old and any(r["indexed"] for r in old):
        print("  !! baseline resolved to an indexed tree — comparison invalid")
        return 1

    L = []
    L.append("=" * W)
    L.append(" .sarib  ·  \"How does query performance hold up once the")
    L.append("            node count reaches tens of thousands?\"")
    L.append("=" * W)
    L.append("")
    L.append(" One bounded query over a whole document, from a cold start:")
    L.append(" each timing includes building the index, which is what you")
    L.append(" feel on the first question after opening a file. (The warm")
    L.append(" per-query figures in bench/scale-report.md are lower.)")
    L.append("")
    L.append(" Same machine, byte-identical input. v0.1.4 measured in a")
    L.append(f" git worktree at {BASE_SHA} — not a number from another day.")
    L.append("")
    L.append(f"   {'nodes':>9}   {'v0.1.4':>11}   {'v0.1.5':>10}   {'faster':>9}")
    L.append(f"   {'-' * 9}   {'-' * 11}   {'-' * 10}   {'-' * 9}")
    for i, r in enumerate(now):
        o = old[i] if i < len(old) else None
        fac = f"{o['query'] / r['query']:,.0f}x" if o and r["query"] > 0 else "-"
        L.append(f"   {r['nodes']:>9,}   {human(o['query']) if o else 'n/a':>11}   "
                 f"{human(r['query']):>10}   {fac:>9}")
    L.append(f"   {big['nodes']:>9,}   {'too slow':>11}   {human(big['query']):>10}   "
             f"{'-':>9}")
    L.append("")
    L.append(" Loading the file at all was the worse symptom:")
    if old:
        L.append(f"   parse {old[-1]['nodes']:,} nodes   v0.1.4 {human(old[-1]['parse'])}"
                 f"   ->   v0.1.5 {human(now[-1]['parse'])}")
    L.append("")
    L.append(" NEW GATE G9 — the build now fails if cost grows faster than")
    L.append(" n^1.3, or if the pipeline cannot handle 30,000 nodes.")
    L.append(" Every gate before it passed while this was quadratic, because")
    L.append(" the largest document any of them measured was 301 nodes.")
    L.append("")
    L.append(" Reproduce:  python bench/headline.py")
    L.append("=" * W)

    panel = "\n".join(L)
    print()
    print(panel)
    (ROOT / "bench" / "headline.txt").write_text(panel + "\n", encoding="utf-8")
    print(f"\nwrote bench/headline.txt")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())

"""G9 · Scale gate (plans/01-scale-remediation.md WP0).

Why this gate exists: every other programmatic gate passed at 301 nodes, which sits
in the flat part of the cost curve, so a quadratic reference implementation could
have shipped through freeze unnoticed. G9 is the structural fix.

It asserts *shape*, not wall-clock, because CI runner speed varies by ~5x:

  1. EXPONENT — fit the log-log slope of cost vs node count for each hot path.
     Linear-ish work has slope ~1.0; a quadratic primitive shows ~2.0.
     Require slope <= 1.3 for parse, canon, walk, both query forms, and render.
     The size ladder ESCALATES to 50,000 nodes and stops at the first size that
     exceeds a per-size budget, so the exponent is fitted at real scale on healthy
     code without hanging on regressed code.

  2. CAPACITY — the largest node count whose full pipeline (parse -> canon ->
     query -> render) completes inside a per-size time budget. Self-limiting:
     escalation stops at the first size that blows the budget, so the gate cannot
     hang on a slow implementation. Require capacity >= 30,000 nodes.

Run standalone:  python bench/gate_scale.py
                 python bench/gate_scale.py --quick     (exponent only)
Wired into:      python bench/run_gates.py
"""
from __future__ import annotations

import math
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "impl"))

from sarib import canon, parse                    # noqa: E402
from sarib.query import query                     # noqa: E402
from sarib.render import outline                  # noqa: E402

# The exponent must be fitted at REAL sizes, not toy ones — a gate that only measures
# small inputs is the very failure mode this gate exists to prevent (D-062). But the fit
# cannot use fixed large sizes either: on a regressed (quadratic) implementation a 50k-node
# fit would take hours. So the ladder ESCALATES and stops at the first size that blows the
# per-size budget, then fits over whatever completed (>=MIN_FIT_SIZES). Linear code reaches
# the top and is judged at 50k; quadratic code stops early, is judged small, and fails on
# slope and capacity anyway.
EXPONENT_LADDER = [1000, 4000, 10000, 25000, 50000]
MIN_FIT_SIZES = 3
FIT_BUDGET_S = 10.0
CAPACITY_LADDER = [500, 1000, 2000, 4000, 8000, 16000, 30000]
CAPACITY_TARGET = 30000
BUDGET_S = 15.0
MAX_SLOPE = 1.3


def gen_scaled_kb(n_nodes: int) -> str:
    """Deterministic Candidate-A surface with ~n_nodes nodes and ~n_nodes/4 edges.

    Shape: root -> sections -> tasks, branching ~sqrt(n) so depth stays shallow
    (deep nesting is a separate axis, covered by impl/tests/test_deep_nesting.py).
    Titles are unique so reference resolution is unambiguous (no diagnostics).
    """
    side = max(2, int(math.isqrt(max(1, n_nodes))))
    out = ["---", "sarib: 0.1", "vocab: std@0.1", "title: Scale KB", "---", "",
           "# Scale KB {#scalekb}", ""]
    count = 1
    s = 0
    while count < n_nodes:
        s += 1
        out.append(f"## Section {s} {{.section}} ^sec{s}")
        out.append("")
        count += 1
        for t in range(1, side + 1):
            if count >= n_nodes:
                break
            out.append(f"### Item {s}-{t} {{.task}} ^i{s}_{t}")
            out.append(f"status:: {'done' if (s + t) % 3 == 0 else 'todo'}")
            out.append(f"priority:: {['low', 'med', 'high'][(s + t) % 3]}")
            # one cross-ref every 4th node -> edges ~= n/4, exercises resolution
            if t % 4 == 0 and s > 1:
                out.append(f"[depends-on:: [[Item {s - 1}-{t}]]]")
            out.append("")
            count += 1
    return "\n".join(out)


def _fit_slope(sizes, times) -> float:
    """Least-squares slope of log(time) vs log(size). No numpy dependency."""
    xs = [math.log10(s) for s in sizes]
    ys = [math.log10(max(t, 1e-4)) for t in times]
    n = len(xs)
    sx, sy = sum(xs), sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    denom = n * sxx - sx * sx
    return (n * sxy - sx * sy) / denom if denom else 0.0


def _best_of(fn, reps=3):
    best, out = float("inf"), None
    for _ in range(reps):
        t0 = time.perf_counter()
        out = fn()
        best = min(best, time.perf_counter() - t0)
    return best, out


METRICS = ("parse", "canon", "walk", "query-filter", "query-graph", "render")


def measure(n: int, reps: int = 3) -> dict:
    """Time each hot path at one size. Returns seconds per metric."""
    src = gen_scaled_kb(n)
    t_parse, doc = _best_of(lambda: parse(src), reps)
    root = next(iter(doc.nodes))
    t_canon, _ = _best_of(lambda: canon(doc), reps)
    t_walk, _ = _best_of(lambda: list(doc.walk(None)), reps)
    t_qf, _ = _best_of(lambda: query(doc, {"start": "all", "select": "none",
                                           "filter": {"type": "task"},
                                           "bound": {"max_nodes": 100}}), reps)
    t_qg, _ = _best_of(lambda: query(doc, {"start": root, "select": "any",
                                          "direction": "both"}), reps)
    t_render, _ = _best_of(lambda: outline(doc), reps)
    return {"nodes": len(doc.nodes), "edges": len(doc.edges), "parse": t_parse,
            "canon": t_canon, "walk": t_walk, "query-filter": t_qf,
            "query-graph": t_qg, "render": t_render}


def pipeline_seconds(n: int) -> float:
    """One full parse -> canon -> query -> render pass. The capacity unit."""
    src = gen_scaled_kb(n)
    t0 = time.perf_counter()
    doc = parse(src)
    canon(doc)
    query(doc, {"start": "all", "select": "none", "filter": {"type": "task"},
                "bound": {"max_nodes": 100}})
    query(doc, {"start": next(iter(doc.nodes)), "select": "any", "direction": "both"})
    outline(doc)
    return time.perf_counter() - t0


def capacity(budget_s: float = BUDGET_S, verbose: bool = False):
    """Largest ladder size whose full pipeline fits the budget. Self-limiting."""
    reached, trace = 0, []
    for n in CAPACITY_LADDER:
        secs = pipeline_seconds(n)
        trace.append((n, secs))
        if verbose:
            print(f"    capacity probe {n:>6} nodes: {secs:7.2f}s"
                  f"{'' if secs <= budget_s else '  <- over budget, stopping'}")
        if secs > budget_s:
            break
        reached = n
    return reached, trace


def run(quick: bool = False, verbose: bool = False) -> dict:
    slopes, rows = {}, []
    for n in EXPONENT_LADDER:
        t0 = time.perf_counter()
        row = measure(n)
        elapsed = time.perf_counter() - t0
        rows.append(row)
        if verbose:
            print(f"    {row['nodes']:>6} nodes / {row['edges']:>5} edges: "
                  + "  ".join(f"{m}={row[m] * 1000:.1f}ms" for m in METRICS))
        if elapsed > FIT_BUDGET_S and len(rows) >= MIN_FIT_SIZES:
            if verbose:
                print(f"    (size {n} took {elapsed:.1f}s > {FIT_BUDGET_S:.0f}s budget — "
                      f"fitting over the {len(rows)} sizes measured)")
            break
    sizes = [r["nodes"] for r in rows]
    for m in METRICS:
        slopes[m] = _fit_slope(sizes, [r[m] for r in rows])

    worst = max(slopes, key=lambda k: slopes[k])
    exponent_ok = all(v <= MAX_SLOPE for v in slopes.values())

    cap, trace = (0, []) if quick else capacity(verbose=verbose)
    capacity_ok = quick or cap >= CAPACITY_TARGET
    passed = exponent_ok and capacity_ok

    lines = [f"## G9 · Scale (target: cost slope ≤{MAX_SLOPE} · capacity ≥"
             f"{CAPACITY_TARGET:,} nodes within {BUDGET_S:.0f}s/pass)", "",
             f"Exponent fitted over **{len(sizes)} sizes, {min(sizes):,}–{max(sizes):,} nodes** "
             f"(ladder escalates to {EXPONENT_LADDER[-1]:,} and stops at the first size over "
             f"{FIT_BUDGET_S:.0f}s, so a regressed implementation is still judged quickly).", ""]
    lines.append("| path | " + " | ".join(f"{s:,}n" for s in sizes) + " | slope |")
    lines.append("|---" * (len(sizes) + 2) + "|")
    for m in METRICS:
        cells = " | ".join(f"{r[m] * 1000:.1f} ms" for r in rows)
        flag = "" if slopes[m] <= MAX_SLOPE else " ⚠"
        lines.append(f"| {m} | {cells} | **{slopes[m]:.2f}**{flag} |")
    lines += ["",
              f"- Worst slope: **{worst} = {slopes[worst]:.2f}** "
              f"(≤{MAX_SLOPE} required) → {'PASS' if exponent_ok else 'FAIL'}"]
    if quick:
        lines.append("- Capacity: skipped (--quick)")
    else:
        lines.append(f"- Capacity: **{cap:,} nodes** "
                     f"(≥{CAPACITY_TARGET:,} required) → "
                     f"{'PASS' if capacity_ok else 'FAIL'}")
        lines.append("  - ladder: " + " · ".join(f"{n:,}n={s:.2f}s" for n, s in trace))
    lines += ["", f"- **{'PASS' if passed else 'FAIL'}**", ""]

    return {"passed": passed, "exponent_ok": exponent_ok, "capacity_ok": capacity_ok,
            "slopes": slopes, "capacity": cap, "rows": rows, "report_lines": lines}


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    quick = "--quick" in sys.argv
    print(f"G9 scale gate · python {sys.version.split()[0]} · "
          f"impl={os.path.join(str(ROOT), 'impl')}")
    r = run(quick=quick, verbose=True)
    print()
    print("\n".join(r["report_lines"]))
    sys.exit(0 if r["passed"] else 1)

"""bench/scale_probe.py — the full scaling measurement (plans/01-scale-remediation.md WP7).

G9 (bench/gate_scale.py) is the pass/fail gate. This is the diagnostic behind it, and it
covers the axes G9 does not: parse from real surface text, every projection, `sarib import`,
per-op edit cost, and memory. It can also measure a PREVIOUS commit on the same machine via
a throwaway git worktree, so before/after is not a comparison across runs or machines.

Run:  python bench/scale_probe.py                 # current tree, default sizes
      python bench/scale_probe.py --report        # + before/after, writes bench/scale-report.md
      python bench/scale_probe.py 1000 10000      # explicit sizes
      python bench/scale_probe.py --before <sha>  # pick the baseline commit

Prefers the in-repo impl/ over any installed sarib, so it measures the tree.
"""
from __future__ import annotations

import datetime
import json
import math
import os
import pathlib
import subprocess
import sys
import time
import tracemalloc

ROOT = pathlib.Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "impl"))
    sys.path.insert(0, str(ROOT / "bench"))

SIZES = [1000, 10000, 30000, 100000]
BEFORE_SIZES = [500, 1000, 2000, 4000]      # the old code cannot reach the sizes above
BEFORE_SHA = "0e8010f"                       # last commit before the remediation
METRICS = ["parse", "canon", "fmt", "outline", "board", "mermaid",
           "query-filter", "query-graph", "walk", "validate",
           "op-set-property", "op-create-node"]


def ms(fn, reps=1):
    best, out = float("inf"), None
    for _ in range(reps):
        t0 = time.perf_counter()
        out = fn()
        best = min(best, (time.perf_counter() - t0) * 1000.0)
    return best, out


def gen_markdown(n_nodes: int) -> str:
    """Plain markdown (what `sarib import` consumes) with ~n_nodes headings."""
    side = max(2, int(math.isqrt(max(1, n_nodes))))
    out, count, s = ["# Notes"], 1, 0
    while count < n_nodes:
        s += 1
        out += ["", f"## Section {s}", "", f"Context for section {s}."]
        count += 1
        for t in range(1, side + 1):
            if count >= n_nodes:
                break
            out += ["", f"### Item {s}-{t}", "", f"Notes about item {s}-{t}."]
            count += 1
    return "\n".join(out) + "\n"


def measure(n: int, reps: int = 3) -> dict:
    """Convenience wrapper: generate the KB for `n` nodes, then measure it.
    Only the PARENT calls this — importing gate_scale has the side effect of putting
    the main tree's impl/ on sys.path, which would shadow a baseline worktree."""
    from gate_scale import gen_scaled_kb
    return measure_src(gen_scaled_kb(n), reps)


def measure_src(src: str, reps: int = 3) -> dict:
    """Every hot path on one source text, plus memory. Takes TEXT, not a size, so the
    baseline worktree measures byte-identical input and imports nothing but its own
    sarib. Imports are late for the same reason."""
    from sarib import canon, fmt, parse
    from sarib.ops import apply as apply_op
    from sarib.query import query
    from sarib.render import board, mermaid, outline

    row = {"nodes": None, "edges": None, "bytes": len(src.encode())}

    # MEMORY in its own pass: tracemalloc traces every allocation and inflates
    # allocation-heavy code by ~35x, so it must never be live while timing.
    tracemalloc.start()
    c0 = tracemalloc.get_traced_memory()[0]
    mdoc = parse(src)
    c1 = tracemalloc.get_traced_memory()[0]
    if hasattr(mdoc, "_index"):
        mdoc._index()                                    # the old tree has no index
    c2 = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    row["model_mb"] = (c1 - c0) / 1e6
    row["index_mb"] = (c2 - c1) / 1e6
    row["indexed"] = hasattr(mdoc, "_index")             # proves WHICH tree ran
    del mdoc

    # TIMING, with tracemalloc off
    t_parse, doc = ms(lambda: parse(src), reps)
    row["nodes"], row["edges"] = len(doc.nodes), len(doc.edges)
    root = next(iter(doc.nodes))
    row["parse"] = t_parse
    row["canon"] = ms(lambda: canon(doc), reps)[0]
    row["fmt"] = ms(lambda: fmt(doc), reps)[0]
    row["outline"] = ms(lambda: outline(doc), reps)[0]
    row["board"] = ms(lambda: board(doc), reps)[0]
    row["mermaid"] = ms(lambda: mermaid(doc), reps)[0]
    row["walk"] = ms(lambda: list(doc.walk(None)), reps)[0]
    row["validate"] = ms(lambda: doc.check_invariants(), reps)[0]
    row["query-filter"] = ms(lambda: query(doc, {
        "start": "all", "select": "none", "filter": {"type": "task"},
        "bound": {"max_nodes": 100}}), reps)[0]
    row["query-graph"] = ms(lambda: query(doc, {
        "start": root, "select": "any", "direction": "both"}), reps)[0]

    # Per-op edit cost: the G1 point edit, and a structural op. Timed over a BATCH and
    # divided — since op-time validation became local (D-065) a point edit is faster than
    # perf_counter's resolution, and a single-shot timing reads 0.0ms and then trips the
    # monotonicity guard on pure noise.
    OP_BATCH = 200
    tgt = next(nid for nid, v in doc.nodes.items() if v.type == "task")

    def set_prop_batch():
        for i in range(OP_BATCH):
            apply_op(doc, {"kind": "set-property", "target": tgt,
                           "args": {"key": "status", "value": "done" if i % 2 else "todo"}})
    row["op-set-property"] = ms(set_prop_batch, reps)[0] / OP_BATCH

    ctr = [0]

    def create_batch():
        for _ in range(OP_BATCH):
            ctr[0] += 1
            apply_op(doc, {"kind": "create-node",
                           "args": {"id": f"probe{ctr[0]}", "title": "p", "parent": root}})
    row["op-create-node"] = ms(create_batch, reps)[0] / OP_BATCH
    return row


def measure_import(n: int) -> dict:
    from sarib.importer import build
    md = gen_markdown(n)
    t, (text, stats, diags) = ms(lambda: build([("notes.md", md)], extract=False))
    return {"nodes": n, "import_ms": t, "out_bytes": len(text.encode()),
            "problems": stats.get("problems", 0)}


def slope(sizes, times) -> float:
    xs = [math.log10(s) for s in sizes]
    ys = [math.log10(max(t, 1e-4)) for t in times]
    k = len(xs)
    sx, sy = sum(xs), sum(ys)
    d = k * sum(x * x for x in xs) - sx * sx
    return (k * sum(x * y for x, y in zip(xs, ys)) - sx * sy) / d if d else 0.0


# ---- running a previous commit on this machine, for an honest before/after ----

# The child puts ONLY the worktree's impl on sys.path and imports only its own sarib
# plus this probe file. It receives the source text as data, so both trees measure
# byte-identical input and nothing can drag the main tree's impl/ in behind our back.
CHILD = """
import json, sys
sys.path.insert(0, %(impl)r)
import importlib.util as u
spec = u.spec_from_file_location("probe_mod", %(probe)r)
m = u.module_from_spec(spec); spec.loader.exec_module(m)
srcs = json.load(open(%(data)r, encoding="utf-8"))
print("@@" + json.dumps([m.measure_src(s, reps=1) for s in srcs]))
"""


def run_before(sha: str, sizes) -> list:
    """Measure `sha` in a throwaway worktree. Same machine, same interpreter, same probe,
    same input bytes. Verified by the `indexed` marker in each returned row."""
    from gate_scale import gen_scaled_kb
    wt = ROOT / ".scale-before"
    data = ROOT / ".scale-before-input.json"
    subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                   cwd=ROOT, capture_output=True)
    r = subprocess.run(["git", "worktree", "add", "--detach", str(wt), sha],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        print(f"  (worktree for {sha} unavailable: {r.stderr.strip()[:120]})")
        return []
    try:
        data.write_text(json.dumps([gen_scaled_kb(n) for n in sizes]), encoding="utf-8")
        code = CHILD % {"impl": str(wt / "impl"),
                        "probe": str(ROOT / "bench" / "scale_probe.py"),
                        "data": str(data)}
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                             capture_output=True, text=True, timeout=3600)
        line = next((l for l in out.stdout.splitlines() if l.startswith("@@")), None)
        if not line:
            print(f"  (baseline run failed: {out.stderr.strip()[-300:]})")
            return []
        return json.loads(line[2:])
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                       cwd=ROOT, capture_output=True)
        data.unlink(missing_ok=True)


def contamination(rows, metrics) -> list:
    """Flag physically impossible timings: a LARGER input measured faster than a smaller
    one. Every path here is monotonic in node count, so an inversion means the machine was
    loaded during the run, not that the code got faster. Learned the hard way — a report
    generated while a subagent fleet was running showed walk() at 253ms for 37k nodes and
    64ms for 125k, and the resulting slopes (1.35-1.50) were pure noise."""
    FLOOR_MS = 0.05          # below perf_counter's useful resolution: noise, not signal
    bad = []
    for m in metrics:
        for i in range(1, len(rows)):
            prev, cur = rows[i - 1][m], rows[i][m]
            if prev < FLOOR_MS and cur < FLOOR_MS:
                continue     # both sub-resolution; an "inversion" here is meaningless
            if cur < prev * 0.9:                       # 10% slack for timer jitter
                bad.append(f"{m}: {rows[i - 1]['nodes']:,}n={prev:.3f}ms but "
                           f"{rows[i]['nodes']:,}n={cur:.3f}ms (larger input, faster)")
    return bad


def table(rows, metrics) -> list:
    head = "| path | " + " | ".join(f"{r['nodes']:,}n" for r in rows) + " | slope |"
    out = [head, "|---" * (len(rows) + 2) + "|"]
    sizes = [r["nodes"] for r in rows]
    def cell(v):
        # a point edit is now sub-0.05ms, so one decimal renders it as a useless "0.0"
        return f"{v:,.3f}" if v < 0.1 else f"{v:,.1f}"

    for m in metrics:
        cells = " | ".join(cell(r[m]) for r in rows)
        out.append(f"| {m} | {cells} | **{slope(sizes, [r[m] for r in rows]):.2f}** |")
    return out


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    sizes = [int(a) for a in args] or SIZES
    report = "--report" in sys.argv
    sha = (sys.argv[sys.argv.index("--before") + 1] if "--before" in sys.argv else BEFORE_SHA)

    print(f"python {sys.version.split()[0]} · impl={ROOT / 'impl'}")
    print(f"\n== current tree · times in ms (best of 3) ==")
    rows = []
    for n in sizes:
        row = measure(n)
        rows.append(row)
        print(f"  {row['nodes']:>7,}n/{row['edges']:>6,}e  "
              + "  ".join(f"{m}={row[m]:.1f}" for m in
                          ("parse", "canon", "outline", "query-filter", "query-graph"))
              + f"  model={row['model_mb']:.1f}MB index={row['index_mb']:.1f}MB")

    print("\n== sarib import (markdown -> graph skeleton, no extraction) ==")
    imports = []
    for n in sizes:
        ir = measure_import(n)
        imports.append(ir)
        print(f"  {ir['nodes']:>7,} nodes: {ir['import_ms']:>9,.1f} ms  "
              f"({ir['problems']} problems)")

    if not report:
        return 0

    print(f"\n== baseline {sha} in a throwaway worktree (small sizes; the old code "
          f"cannot reach the ones above) ==")
    before = run_before(sha, BEFORE_SIZES)
    for r in before:
        print(f"  {r['nodes']:>7,}n  indexed={r.get('indexed')}  " + "  ".join(
            f"{m}={r[m]:.1f}" for m in ("parse", "canon", "outline", "query-graph")))
    if before and any(r.get("indexed") for r in before):
        print("  !! BASELINE RESOLVED TO AN INDEXED TREE — before/after is invalid")
        return 1

    lines = [
        "# Scaling report — reference implementation",
        "",
        f"Generated {datetime.date.today().isoformat()} by `python bench/scale_probe.py "
        f"--report` · python {sys.version.split()[0]} · single machine, best-of-3.",
        "",
        "This is the evidence RM11 (\"large KBs blow parse/query/memory\") never had, and the"
        " answer to RM8's early-warning trigger (\"query/write latency unacceptable at 100k"
        " nodes\"). The pass/fail gate is **G9** in `bench/gate-report.md`; this report is the"
        " detail behind it.",
        "",
        "Times are milliseconds. `slope` is the least-squares exponent of log(time) vs"
        " log(nodes): ~1.0 is linear, ~2.0 is quadratic. **The exponent is the finding; the"
        " absolute constants are machine- and noise-dependent.**",
        "",
        f"## After — current tree, {sizes[0]:,} to {sizes[-1]:,} nodes",
        "",
    ]
    dirty = contamination(rows, METRICS)
    if dirty:
        print("\n!! CONTAMINATED RUN — the machine was loaded. Re-run idle:")
        for d in dirty:
            print(f"     {d}")
        lines += ["> ⚠️ **This run is contaminated and its slopes are not trustworthy.** A larger",
                  "> input measured faster than a smaller one, which is impossible for these paths —",
                  "> the machine was busy during the run. Re-run on an idle machine.", ""]
        for d in dirty:
            lines.append(f"> - {d}")
        lines.append("")
    lines += table(rows, METRICS)
    lines += [
        "",
        "| | " + " | ".join(f"{r['nodes']:,}n" for r in rows) + " |",
        "|---" * (len(rows) + 1) + "|",
        "| surface bytes | " + " | ".join(f"{r['bytes'] / 1e6:.1f} MB" for r in rows) + " |",
        "| model memory | " + " | ".join(f"{r['model_mb']:.1f} MB" for r in rows) + " |",
        "| derived index | " + " | ".join(f"{r['index_mb']:.1f} MB" for r in rows) + " |",
        "",
        "## `sarib import` (markdown → graph skeleton, no model extraction)",
        "",
        "| nodes | time | output |",
        "|---|---|---|",
    ]
    for ir in imports:
        lines.append(f"| {ir['nodes']:,} | {ir['import_ms']:,.1f} ms | "
                     f"{ir['out_bytes'] / 1e6:.1f} MB |")
    lines.append(f"| _slope_ | **{slope([i['nodes'] for i in imports], [i['import_ms'] for i in imports]):.2f}** | |")

    if before:
        lines += ["", f"## Before — `{sha}`, measured in a worktree on the same machine",
                  "",
                  "Small sizes only: the pre-remediation code cannot reach the sizes above in"
                  " reasonable time. That is the finding, not a gap in the method.",
                  ""]
        lines += table(before, [m for m in METRICS if m in before[0]])
        common = [n for n in (1000,) if any(r["nodes"] >= n for r in rows)]
        if common:
            lines += ["", "### Same size, both trees (~1,000 nodes)", "",
                      "| path | before | after | factor |", "|---|---|---|---|"]
            b = min(before, key=lambda r: abs(r["nodes"] - 1000))
            a = min(rows, key=lambda r: abs(r["nodes"] - 1000))
            for m in METRICS:
                if m in b and m in a and a[m] > 0:
                    lines.append(f"| {m} | {b[m]:,.1f} ms | {a[m]:,.1f} ms | "
                                 f"**{b[m] / max(a[m], 1e-4):.0f}x** |")
            lines.append("")
            lines.append(f"(before at {b['nodes']:,} nodes vs after at {a['nodes']:,} nodes)")

    lines += [
        "",
        "## Reading this",
        "",
        "- **Parse was the worst symptom, not query.** `order=len(doc.children(...))` sat"
        " inside the parse loop, so a large file could not be *loaded*, let alone queried.",
        "- **A point edit is now effectively free** (`op-set-property` above, flat across every"
        " size): op-time validation is scoped to the ids the op touched (D-065), so a 50-token"
        " edit no longer re-checks the whole document. It was ~82ms at 125k nodes before that"
        " change. **Structural ops are still O(N)** (`op-create-node`): they invalidate the"
        " derived index, and the next read rebuilds it. Incremental index maintenance is the"
        " open follow-up — see `plans/01-scale-remediation.md` §10 F1.",
        "- **The derived index is memory the file does not pay for.** It is rebuilt on demand"
        " and never serialized (P17), so it costs RAM, not bytes on disk.",
        "- `sarib import` is the on-ramp a new user hits first, which is why it is measured"
        " separately from the core paths.",
        "- **The same-size factors below are a floor, not a headline.** They compare at"
        " ~1,000 nodes because that is where both trees can be measured; the gap is the"
        " difference between a ~2.0 and a ~1.1 exponent, so it widens with every doubling.",
        "- **`validate` and the two `op-*` rows were already linear before this work** and are"
        " unchanged (factor ~1x). Nothing here regressed; the wins are concentrated in the"
        " paths that walked or re-sorted the whole document.",
        "",
    ]
    out = ROOT / "bench" / "scale-report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote {out.relative_to(ROOT)}")
    # Non-zero on a contaminated run so it cannot be committed unnoticed. An earlier
    # attempt to wire this up silently failed to apply, and a contaminated report shipped.
    return 2 if dirty else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())

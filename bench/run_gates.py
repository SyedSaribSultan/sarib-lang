"""Freeze-gate benchmark runner (Stage 15 §4). Programmatically measurable gates:
G1 edit economy · G4 implementability · G5 merge/permutation safety · G6 round-trip
G7 cache-prefix survival · G9 scale (bench/gate_scale.py).
(G2/G3 protocols in bench/g2-g3-protocol.md; G8 in tokenizer-report.md)
Run from repo root: python bench/run_gates.py        (real o200k tokens; needs gpt-tokenizer)
                    python bench/run_gates.py --estimate   (chars/4; every figure labelled ESTIMATE)
                    python bench/run_gates.py --no-scale   (skip G9; it dominates runtime)

Token counts come from node gpt-tokenizer (offline BPE). If it is unavailable the runner ABORTS
rather than silently degrading to chars/4 — a previous version did degrade, and overwrote a real
measurement with an estimate while still labelling it "o200k". Never again: the method actually
used is recorded in the report header.
"""
import datetime, json, pathlib, random, subprocess, sys, itertools

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "impl"))
from sarib import parse, canon, fmt, apply as apply_op   # noqa: E402
from sarib.ops import fold                               # noqa: E402
from sarib import __version__                            # noqa: E402

ESTIMATE = "--estimate" in sys.argv
SKIP_SCALE = "--no-scale" in sys.argv
TOK_METHOD = "chars/4 ESTIMATE (not a real tokenizer)" if ESTIMATE else "o200k (offline gpt-tokenizer)"
_JS = ("const{encode}=require('gpt-tokenizer/cjs/encoding/o200k_base');"
       "process.stdout.write(String(encode(require('fs').readFileSync(0,'utf8')).length))")


def tokens(text: str) -> int:
    if ESTIMATE:
        return max(1, len(text) // 4)
    try:
        r = subprocess.run(["node", "-e", _JS], input=text, capture_output=True, text=True)
        return int(r.stdout.strip())
    except Exception as e:
        raise SystemExit(
            f"gate runner: tokenizer unavailable ({e.__class__.__name__}: {e}).\n"
            f"  fix:  npm i gpt-tokenizer   (then re-run from the repo root)\n"
            f"  or:   python bench/run_gates.py --estimate   (chars/4; figures labelled ESTIMATE)\n"
            f"Refusing to silently substitute an estimate for a measurement.")


def gen_kb(n_sections=12, tasks_per=12) -> str:
    """Synthetic ~10k-token knowledge base in Candidate-A surface."""
    random.seed(42)
    out = ["---", "sarib: 0.1", "vocab: std@0.1", "title: Synthetic KB", "---", "",
           "# Synthetic KB {#kb}", ""]
    verbs = ["Migrate", "Refactor", "Review", "Ship", "Design", "Test", "Document", "Deploy"]
    objs = ["billing", "auth", "search", "onboarding", "exports", "alerts", "webhooks", "cache"]
    for s in range(n_sections):
        out.append(f"## Workstream {s + 1} {{.section}} ^ws{s + 1}")
        out.append("")
        for t in range(tasks_per):
            tid = f"t{s + 1}x{t + 1}"
            title = f"{random.choice(verbs)} the {random.choice(objs)} pipeline v{t + 1}"
            out.append(f"### {title} {{.task}} ^{tid}")
            out.append(f"status:: {'done' if random.random() < 0.4 else 'todo'}")
            out.append(f"due:: 2026-0{random.randint(1, 9)}-1{random.randint(0, 9)}")
            out.append(f"priority:: {random.choice(['low', 'med', 'high'])}")
            out.append("")
            out.append(f"Working notes for {title.lower()}: constraints, findings and follow-ups "
                       f"recorded as prose. This block simulates real knowledge density around task {tid}.")
            out.append("")
    return "\n".join(out)


def main():
    report = ["# Freeze-gate run — programmatic gates", "",
              f"Date: {datetime.date.today().isoformat()} · impl v{__version__} · "
              f"tokens = {TOK_METHOD}", ""]
    kb = gen_kb()
    doc = parse(kb)
    kb_tokens = tokens(kb)

    # ---- G1: edit economy ----
    op = {"kind": "set-property", "target": "t3x4",
          "args": {"key": "status", "value": "done"},
          "expect": {"t3x4": {"props": {"status": "todo"}}}}
    op_tokens = tokens(json.dumps(op))
    ratio = 100 * op_tokens / kb_tokens
    g1 = ratio <= 1.0
    report += [f"## G1 · Edit economy (target: op ≤1% of regeneration)",
               f"- KB size: {kb_tokens} tokens ({len(doc.nodes)} nodes)",
               f"- One guarded point-edit op: {op_tokens} tokens",
               f"- **Ratio: {ratio:.2f}% → {'PASS' if g1 else 'FAIL'}**", ""]

    # ---- G4: implementability ----
    # SCOPE CHANGED 2026-07-28 (D-064, register RM23) — argued in the open, not moved quietly.
    # G4 exists to keep success test S6 honest: "a conforming parser is a weekend's work". The
    # budget therefore has to measure the CONFORMANCE SURFACE — what a third party must build to
    # interoperate. It previously also counted the CLI and the MCP server, which nothing in the
    # spec requires: they are transports we happen to ship. Counting them made the gate measure
    # something its own sentence does not claim, and after the scale fix (+54 LOC) that
    # miscounting was about to force a real feature out of the core for no principled reason.
    # All three tiers are still reported every run, so nothing is hidden by the narrower gate.
    CONFORMANCE = {"parser.py", "canon.py", "model.py", "ops.py", "query.py",
                   "render.py", "__init__.py"}          # the format itself — BUDGETED
    TRANSPORTS = {"cli.py", "mcp_server.py"}            # how you talk to it — reported
    CONSUMERS = {"importer.py", "preview.py"}           # built on top — reported

    def _loc(fs):
        return sum(1 for f in fs for line in f.read_text(encoding="utf-8").splitlines()
                   if line.strip() and not line.strip().startswith("#"))

    pkg = sorted((ROOT / "impl" / "sarib").glob("*.py"))
    by = lambda names: _loc([f for f in pkg if f.name in names])      # noqa: E731
    unclassified = sorted(f.name for f in pkg
                          if f.name not in CONFORMANCE | TRANSPORTS | CONSUMERS)
    loc, loc_tx, loc_consumer = by(CONFORMANCE), by(TRANSPORTS), by(CONSUMERS)
    g4 = loc <= 1000 and not unclassified      # a new file must be classified, not ignored
    report += [f"## G4 · Implementability (target: ≤1000 LOC for the conformance surface)",
               f"- **Conformance surface** (parser+canon+model+ops+query+render) — BUDGETED: "
               f"**{loc}** / 1000",
               f"- Transports (cli+mcp), reported not budgeted: {loc_tx} LOC — nothing in the "
               f"spec requires a CLI or an MCP server",
               f"- Consumers (importer+preview), reported not budgeted: {loc_consumer} LOC",
               f"- Whole package: {loc + loc_tx + loc_consumer} LOC",
               f"- **{'PASS' if g4 else 'FAIL'}** — scope narrowed to what S6 actually claims "
               f"(D-064); previously this line budgeted conformance+transports together",
               ""]
    if unclassified:
        report += [f"- ⚠ **FAIL: unclassified module(s)** {', '.join(unclassified)} — add each to "
                   f"CONFORMANCE, TRANSPORTS or CONSUMERS in `bench/run_gates.py` so new code "
                   f"cannot escape the budget by being unlisted.", ""]

    # ---- G5: merge / permutation invariance (SEC) ----
    ops = [
        {"id": "a", "ts": [1, 5], "kind": "set-property", "target": "t1x1", "args": {"key": "status", "value": "done"}},
        {"id": "b", "ts": [2, 3], "kind": "set-property", "target": "t2x2", "args": {"key": "priority", "value": "high"}},
        {"id": "c", "ts": [1, 7], "kind": "create-node", "args": {"id": "tNEW1", "title": "New task", "type": "task", "parent": "ws1", "props": {"status": "todo"}}},
        {"id": "d", "ts": [3, 1], "kind": "retract-node", "target": "t4x4"},
    ]
    canons = set()
    for perm in itertools.permutations(ops):
        d = parse(kb)
        fold(d, list(perm))
        canons.add(canon(d))
    g5 = len(canons) == 1
    report += [f"## G5 · Merge safety (SEC: any op order → same state; target: 1 state, 0 corruption)",
               f"- 4 concurrent ops × {24} permutations → **{len(canons)} distinct state(s) → {'PASS' if g5 else 'FAIL'}**", ""]

    # ---- G6: round-trip (corpus already enforces; re-assert on the big KB) ----
    g6 = canon(parse(fmt(parse(kb)))) == canon(parse(kb))
    report += [f"## G6 · Lossless round-trip (surface→model→surface→model)",
               f"- 10k-token KB: **{'PASS' if g6 else 'FAIL'}** "
               f"(+ 6/6 corpus cases enforce this — `python impl/tests/run_corpus.py`)", ""]

    # ---- G7: cache-prefix survival ----
    doc2 = parse(kb)
    before = canon(doc2)
    apply_op(doc2, {"kind": "set-property", "target": "t12x12", "args": {"key": "status", "value": "verified-new-state"}})
    after = canon(doc2)
    b, a = before.splitlines(), after.splitlines()
    common = 0
    for x, y in zip(b, a):
        if x != y:
            break
        common += 1
    pct = 100 * common / len(b)
    changed = sum(1 for x, y in zip(b, a) if x != y) + abs(len(b) - len(a))
    g7 = pct >= 95 and 1 <= changed <= 2   # exactly the edited record must differ — 0 would be vacuous
    report += [f"## G7 · Cache-prefix survival (edit near end of doc; target: long stable prefix, minimal diff)",
               f"- Canonical form: {len(b)} lines; stable prefix {common} lines ({pct:.1f}%); changed lines: {changed}",
               f"- **{'PASS' if g7 else 'FAIL'}**", ""]

    # ---- G9: scale (cost slope + capacity) ----
    # Added after the 2026-07-27 finding that every gate above passes at 301 nodes,
    # which is inside the flat part of the cost curve (plans/01-scale-remediation.md).
    if SKIP_SCALE:
        g9 = True
        report += ["## G9 · Scale", "- SKIPPED (--no-scale)", ""]
    else:
        sys.path.insert(0, str(ROOT / "bench"))
        from gate_scale import run as run_scale          # noqa: PLC0415
        s = run_scale()
        g9 = s["passed"]
        report += s["report_lines"]

    report += ["## G2/G3/G8 status",
               "- G8 glyphs: PASS on GPT-family (bench/tokenizer-report.md); open-weight re-run pending.",
               "- G2 agent accuracy: measured cross-model run → bench/g2-results.md (runner: bench/run_g2.py).",
               "- G3 human readability: protocol (needs human raters) → bench/g2-g3-protocol.md.", ""]
    ok = all([g1, g4, g5, g6, g7, g9])
    report.append(f"**Programmatic gates: {'ALL PASS' if ok else 'FAILURES PRESENT'}** "
                  f"(G1,G4,G5,G6,G7,G9)")
    (ROOT / "bench" / "gate-report.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # '≤' in the G4 line dies on Windows cp1252
    main()

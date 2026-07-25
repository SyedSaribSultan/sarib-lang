"""L4 measurement: run the entailment verifier over the cached L1-L3 proposals.

The Layers 1-3 run (extract_poc.py) produced 14 surviving proposals at 93% precision
(13 correct, 1 direction-flip: d-013 --supersedes--> d-016, where the source actually
says D-013 was *amended by* D-016). This script measures whether Layer 4 -- an
independent entailment check on each edge's cited span -- rejects that error while
keeping the 13 correct edges.

Ground truth (hand-verified against decisions/decision-log.md, recorded here so the
result is reproducible without re-judging): every proposal is correct EXCEPT the
d-013 -> d-016 'supersedes' claim.

Run: python bench/importer-poc/verify_poc.py   (needs Ollama + qwen2.5:7b)
"""
from __future__ import annotations
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "impl"))
from sarib.importer import _verify  # the shipping L4 verifier

HERE = pathlib.Path(__file__).resolve().parent
MODEL, ENDPOINT = "qwen2.5:7b", "http://localhost:11434/api/chat"
WRONG = {("d-013", "supersedes", "d-016")}   # the one known-bad proposal


def main():
    rows = [json.loads(l) for l in (HERE / "proposals.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"{len(rows)} cached L1-L3 proposals; running L4 verify with {MODEL}\n")
    tp = fp = tn = fn = 0
    out = []
    for r in rows:
        key = (r["source"], r["type"], r["target"])
        truth_ok = key not in WRONG
        kept = _verify(MODEL, ENDPOINT, r["source"], r["type"], r["target"], r["span"])
        if kept and truth_ok:
            tp += 1; verdict = "kept   (correct)"
        elif kept and not truth_ok:
            fp += 1; verdict = "KEPT   (WRONG - L4 missed it)"
        elif not kept and truth_ok:
            fn += 1; verdict = "dropped (correct edge lost)"
        else:
            tn += 1; verdict = "DROPPED (bad edge caught)"
        print(f"  {r['source']} -{r['type']}-> {r['target']}: {verdict}")
        out.append(dict(r, l4_kept=kept, truth_correct=truth_ok))
    kept_total = tp + fp
    prec_before = (len(rows) - len(WRONG & {(r['source'], r['type'], r['target']) for r in rows})) / len(rows)
    print(f"\nL1-L3 precision (before L4): {prec_before*100:.1f}%  ({len(rows)} kept)")
    if kept_total:
        print(f"L4 precision:                {tp/kept_total*100:.1f}%  ({kept_total} kept)")
    else:
        print("L4 kept nothing -- verifier is too strict (recall collapse)")
    print(f"bad edges caught by L4:      {tn}/{len(WRONG)}")
    print(f"correct edges lost to L4:    {fn}/{len(rows)-len(WRONG)}")
    (HERE / "l4-results.jsonl").write_text(
        "\n".join(json.dumps(o, ensure_ascii=False) for o in out), encoding="utf-8")
    print("\nwrote bench/importer-poc/l4-results.jsonl")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()

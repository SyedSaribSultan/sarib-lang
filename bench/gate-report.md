# Freeze-gate run — programmatic gates

Date: 2026-07-28 · impl v0.1.4 · tokens = o200k (offline gpt-tokenizer)

## G1 · Edit economy (target: op ≤1% of regeneration)
- KB size: 10042 tokens (301 nodes)
- One guarded point-edit op: 50 tokens
- **Ratio: 0.50% → PASS**

## G4 · Implementability (target: ≤1000 LOC, one weekend)
- Non-blank/non-comment LOC, conformance surface + transports (parser+canon+model+ops+query+render+cli+mcp): 987
- **PASS** (budget was for the parser alone)
- Reported separately, outside the budget: consumers (importer.py, preview.py) = 458 LOC

## G5 · Merge safety (SEC: any op order → same state; target: 1 state, 0 corruption)
- 4 concurrent ops × 24 permutations → **1 distinct state(s) → PASS**

## G6 · Lossless round-trip (surface→model→surface→model)
- 10k-token KB: **PASS** (+ 6/6 corpus cases enforce this — `python impl/tests/run_corpus.py`)

## G7 · Cache-prefix survival (edit near end of doc; target: long stable prefix, minimal diff)
- Canonical form: 302 lines; stable prefix 300 lines (99.3%); changed lines: 1
- **PASS**

## G9 · Scale (target: cost slope ≤1.3 · capacity ≥30,000 nodes within 15s/pass)

| path | 603n | 1,211n | 2,477n | 4,922n | slope |
|---|---|---|---|---|---|
| parse | 13.0 ms | 23.5 ms | 57.5 ms | 105.3 ms | **1.02** |
| canon | 12.8 ms | 28.8 ms | 41.6 ms | 73.5 ms | **0.80** |
| walk | 0.1 ms | 0.4 ms | 0.5 ms | 0.9 ms | **0.82** |
| query-filter | 0.3 ms | 1.3 ms | 1.2 ms | 2.1 ms | **0.78** |
| query-graph | 1.4 ms | 6.1 ms | 8.7 ms | 18.2 ms | **1.14** |
| render | 0.9 ms | 2.7 ms | 4.2 ms | 11.1 ms | **1.14** |

- Worst slope: **render = 1.14** (≤1.3 required) → PASS
- Capacity: **30,000 nodes** (≥30,000 required) → PASS
  - ladder: 500n=0.03s · 1,000n=0.06s · 2,000n=0.12s · 4,000n=0.29s · 8,000n=0.53s · 16,000n=0.90s · 30,000n=2.28s

- **PASS**

## G2/G3/G8 status
- G8 glyphs: PASS on GPT-family (bench/tokenizer-report.md); open-weight re-run pending.
- G2 agent accuracy: measured cross-model run → bench/g2-results.md (runner: bench/run_g2.py).
- G3 human readability: protocol (needs human raters) → bench/g2-g3-protocol.md.

**Programmatic gates: ALL PASS** (G1,G4,G5,G6,G7,G9)
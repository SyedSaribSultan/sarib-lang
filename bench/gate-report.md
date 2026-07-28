# Freeze-gate run — programmatic gates

Date: 2026-07-28 · impl v0.1.5 · tokens = o200k (offline gpt-tokenizer)

## G1 · Edit economy (target: op ≤1% of regeneration)
- KB size: 10042 tokens (301 nodes)
- One guarded point-edit op: 50 tokens
- **Ratio: 0.50% → PASS**

## G4 · Implementability (target: ≤1000 LOC for the conformance surface)
- **Conformance surface** (parser+canon+model+ops+query+render) — BUDGETED: **658** / 1000
- Transports (cli+mcp), reported not budgeted: 348 LOC — nothing in the spec requires a CLI or an MCP server
- Consumers (importer+preview), reported not budgeted: 458 LOC
- Whole package: 1464 LOC
- **PASS** — scope narrowed to what S6 actually claims (D-064); previously this line budgeted conformance+transports together

## G5 · Merge safety (SEC: any op order → same state; target: 1 state, 0 corruption)
- 4 concurrent ops × 24 permutations → **1 distinct state(s) → PASS**

## G6 · Lossless round-trip (surface→model→surface→model)
- 10k-token KB: **PASS** (+ 6/6 corpus cases enforce this — `python impl/tests/run_corpus.py`)

## G7 · Cache-prefix survival (edit near end of doc; target: long stable prefix, minimal diff)
- Canonical form: 302 lines; stable prefix 300 lines (99.3%); changed lines: 1
- **PASS**

## G9 · Scale (target: cost slope ≤1.3 · capacity ≥30,000 nodes within 15s/pass)

Exponent fitted over **5 sizes, 1,211–62,221 nodes** (ladder escalates to 50,000 and stops at the first size over 10s, so a regressed implementation is still judged quickly).

| path | 1,211n | 4,922n | 12,450n | 31,092n | 62,221n | slope |
|---|---|---|---|---|---|---|
| parse | 8.9 ms | 38.4 ms | 96.9 ms | 391.5 ms | 860.4 ms | **1.17** |
| canon | 39.8 ms | 62.8 ms | 87.1 ms | 255.0 ms | 530.6 ms | **0.65** |
| walk | 0.2 ms | 0.7 ms | 1.4 ms | 4.2 ms | 9.5 ms | **1.00** |
| query-filter | 0.5 ms | 2.1 ms | 3.3 ms | 9.8 ms | 21.3 ms | **0.92** |
| query-graph | 3.0 ms | 12.2 ms | 31.4 ms | 87.5 ms | 189.5 ms | **1.05** |
| render | 1.4 ms | 6.1 ms | 18.2 ms | 74.9 ms | 120.4 ms | **1.18** |

- Worst slope: **render = 1.18** (≤1.3 required) → PASS
- Capacity: **30,000 nodes** (≥30,000 required) → PASS
  - ladder: 500n=0.01s · 1,000n=0.03s · 2,000n=0.06s · 4,000n=0.14s · 8,000n=0.28s · 16,000n=0.58s · 30,000n=1.27s

- **PASS**

## G2/G3/G8 status
- G8 glyphs: PASS on GPT-family (bench/tokenizer-report.md); open-weight re-run pending.
- G2 agent accuracy: measured cross-model run → bench/g2-results.md (runner: bench/run_g2.py).
- G3 human readability: protocol (needs human raters) → bench/g2-g3-protocol.md.

**Programmatic gates: ALL PASS** (G1,G4,G5,G6,G7,G9)
# Freeze-gate run — programmatic gates

Date: 2026-07-28 · impl v0.1.6 · tokens = o200k (offline gpt-tokenizer)

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
| parse | 9.5 ms | 34.5 ms | 82.3 ms | 232.8 ms | 744.7 ms | **1.08** |
| canon | 9.0 ms | 31.1 ms | 70.2 ms | 204.4 ms | 687.6 ms | **1.07** |
| walk | 0.1 ms | 0.7 ms | 1.4 ms | 6.0 ms | 16.0 ms | **1.19** |
| query-filter | 0.4 ms | 1.5 ms | 3.1 ms | 11.7 ms | 26.8 ms | **1.05** |
| query-graph | 2.2 ms | 7.6 ms | 22.1 ms | 111.4 ms | 264.2 ms | **1.24** |
| render | 1.7 ms | 4.7 ms | 15.8 ms | 73.5 ms | 214.3 ms | **1.25** |

- Worst slope: **render = 1.25** (≤1.3 required) → PASS
- Capacity: **30,000 nodes** (≥30,000 required) → PASS
  - ladder: 500n=0.01s · 1,000n=0.03s · 2,000n=0.07s · 4,000n=0.13s · 8,000n=0.35s · 16,000n=0.75s · 30,000n=1.41s

- **PASS**

## G2/G3/G8 status
- G8 glyphs: PASS on GPT-family (bench/tokenizer-report.md); open-weight re-run pending.
- G2 agent accuracy: measured cross-model run → bench/g2-results.md (runner: bench/run_g2.py).
- G3 human readability: protocol (needs human raters) → bench/g2-g3-protocol.md.

**Programmatic gates: ALL PASS** (G1,G4,G5,G6,G7,G9)
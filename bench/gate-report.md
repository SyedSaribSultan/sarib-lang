# Freeze-gate run — programmatic gates

Date: 2026-10-15 · impl v0.1.7 · tokens = o200k (offline gpt-tokenizer)

## G1 · Edit economy (target: op ≤1% of regeneration)
- KB size: 10042 tokens (301 nodes)
- One guarded point-edit op: 50 tokens
- **Ratio: 0.50% → PASS**

## G4 · Implementability (target: ≤1000 LOC for the conformance surface)
- **Conformance surface** (parser+canon+model+ops+query+render) — BUDGETED: **742** / 1000
- Transports (cli+mcp), reported not budgeted: 359 LOC — nothing in the spec requires a CLI or an MCP server
- Consumers (importer+preview), reported not budgeted: 473 LOC
- Whole package: 1574 LOC
- **PASS** — scope narrowed to what S6 actually claims (D-064); previously this line budgeted conformance+transports together

## G5 · Merge safety (SEC: any op order → same state; target: 1 state, 0 corruption)
- 4 concurrent ops × 24 permutations → **1 distinct state(s) → PASS**

## G6 · Lossless round-trip (surface→model→surface→model)
- 10k-token KB: **PASS** (+ 10 corpus cases enforce this — `python impl/tests/run_corpus.py`)

## G7 · Cache-prefix survival (edit near end of doc; target: long stable prefix, minimal diff)
- Canonical form: 302 lines; stable prefix 300 lines (99.3%); changed lines: 1
- **PASS**

## G9 · Scale (target: cost slope ≤1.3 · capacity ≥30,000 nodes within 15s/pass)

Exponent fitted over **5 sizes, 1,211–62,221 nodes** (ladder escalates to 50,000 and stops at the first size over 10s, so a regressed implementation is still judged quickly).

| path | 1,211n | 4,922n | 12,450n | 31,092n | 62,221n | slope |
|---|---|---|---|---|---|---|
| parse | 18.8 ms | 92.8 ms | 241.9 ms | 765.5 ms | 1401.1 ms | **1.11** |
| canon | 16.4 ms | 82.7 ms | 196.0 ms | 457.7 ms | 884.6 ms | **1.00** |
| walk | 0.3 ms | 1.2 ms | 3.5 ms | 7.0 ms | 16.7 ms | **1.04** |
| query-filter | 0.9 ms | 2.2 ms | 6.5 ms | 14.5 ms | 37.5 ms | **0.95** |
| query-graph | 3.2 ms | 17.3 ms | 57.6 ms | 210.7 ms | 422.9 ms | **1.26** |
| render | 1.9 ms | 11.0 ms | 24.6 ms | 105.9 ms | 220.4 ms | **1.21** |

- Worst slope: **query-graph = 1.26** (≤1.3 required) → PASS
- Capacity: **30,000 nodes** (≥30,000 required) → PASS
  - ladder: 500n=0.03s · 1,000n=0.06s · 2,000n=0.15s · 4,000n=0.25s · 8,000n=0.45s · 16,000n=0.82s · 30,000n=1.92s

- **PASS**

## G2/G3/G8 status
- G8 glyphs: **PASS** on GPT-family (bench/tokenizer-report.md) AND on five open-weight tokenizers — Llama 3.1, Qwen 2.5, Mistral v0.3, Gemma 2, DeepSeek-V3 (bench/tokenizer-open-weight.md). Not run in CI: it fetches tokenizer.json over the network, so it is a pre-freeze artifact rather than a per-commit check — re-run `python bench/tokenizer_check_open.py`.
- G2 agent accuracy: measured cross-model run → bench/g2-results.md (runner: bench/run_g2.py).
- G3 human readability: protocol (needs human raters) → bench/g2-g3-protocol.md.

**Programmatic gates: ALL PASS** (G1,G4,G5,G6,G7,G9)
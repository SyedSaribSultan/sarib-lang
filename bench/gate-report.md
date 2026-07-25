# Freeze-gate run — programmatic gates

Date: 2026-07-19 · impl v0.1 · tokens = o200k (offline gpt-tokenizer)

## G1 · Edit economy (target: op ≤1% of regeneration)
- KB size: 10040 tokens (301 nodes)
- One guarded point-edit op: 50 tokens
- **Ratio: 0.50% → PASS**

## G4 · Implementability (target: ≤1000 LOC, one weekend)
- Non-blank/non-comment LOC, ALL components (parser+canon+ops+query+render+cli+mcp): 690
- **PASS** (budget was for the parser alone)

## G5 · Merge safety (SEC: any op order → same state; target: 1 state, 0 corruption)
- 4 concurrent ops × 24 permutations → **1 distinct state(s) → PASS**

## G6 · Lossless round-trip (surface→model→surface→model)
- 10k-token KB: **PASS** (+ 6/6 corpus cases enforce this in CI)

## G7 · Cache-prefix survival (edit near end of doc; target: long stable prefix, minimal diff)
- Canonical form: 302 lines; stable prefix 300 lines (99.3%); changed lines: 1
- **PASS**

## G2/G3/G8 status
- G8 glyphs: PASS on GPT-family (bench/tokenizer-report.md); open-weight re-run pending.
- G2 agent accuracy: **measured run IN PROGRESS (2026-07-20)** → `bench/g2-results.md`.
  Harness proven (mock oracle/adversary self-test); 2/7 models complete so far, rest
  quota-gated to next daily reset. Interim: **split result** — qwen2.5:7b: C beats A
  +27.8pts (McNemar p=0.002) at 3.5× fewer tokens; llama3.2-3B: C *under*performs A
  −11.1pts (n.s., p=0.39; 21/67 misses are id-for-title format errors). Whole-file
  .sarib (B) beats Markdown (A) on neither small model — the win, where present, is
  bounded retrieval (D-002), not the typed surface in context. Verdict deferred to
  the full matrix.
- G3 human readability: protocol (needs human raters) → bench/g2-g3-protocol.md.

**Programmatic gates: ALL PASS** (G1,G4,G5,G6,G7)
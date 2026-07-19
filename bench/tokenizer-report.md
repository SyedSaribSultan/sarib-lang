# Sprint 0 — Tokenizer verification report (RA11 / freeze-gate G8)

**Date:** 2026-07-19 · **Method:** `bench/tokenizer_check.js` (npm `gpt-tokenizer`, offline BPE ranks) · **Encodings:** o200k_base (GPT-4o/o-series), cl100k_base (GPT-4/3.5), r50k_base (GPT-2 lineage)
**Residual:** open-weight tokenizers (Llama/Qwen) unreachable in-sandbox (network blocked) — re-run against them before final freeze. GPT-family results below are definitive for those encodings.

## Verdict

**The Candidate-A glyph set is confirmed token-cheap. No fatal fragmentation. RA11 → mitigated (GPT-family measured; open-weight residual).**

## Key measurements

| Construct | o200k | cl100k | r50k | Reading |
|---|---|---|---|---|
| `::` `[[` `]]` `^` `#` `-` `>` `\|` | **1** | **1** | **1** | all load-bearing sigils single-token |
| `:::` | 1 | 2 | 2 | fine (rare construct) |
| `{.` / `{#` | 2 | 2 | 2 | the attribute braces cost one extra token — acceptable; occurs once per typed node |
| `status:: done` | 3 | 3 | 3 | property line ≈ free: word + `::` + word |
| `[[Target]]` | 3 | 3 | 3 | wikilink ≈ free: `[[` + word + `]]` |
| `[depends-on:: [[Migrate invoices]]]` | 9 | 10 | 14 | a full typed edge in prose ≈ 9 tokens |
| `{.task}` | 4 | 4 | 4 | typing a node costs ~3 tokens over the brace pair |
| full typed heading + slug + id | 15 | 15 | 20 | dominated by the words, not the sigils |

Boundary check (o200k): `status:: done` → `status` · `::` · ` done`; `::` and `[[`/`]]` merge exactly as hoped. Hyphenated slugs (`migrate-invoices`) fragment — slugs are optional, so this is a style note (prefer short slugs), not a defect.

## Whole-file: Candidate A vs Candidate B (same knowledge, comments stripped)

| | o200k tokens | cl100k tokens |
|---|---|---|
| A — prose-native | 242 | 244 |
| B — outline-dense | 177 | 179 |
| **B saves** | **26.9%** | **26.6%** |

This lands inside the Stage 10 estimate (20–35%) and is now a measured fact: **B's density advantage is real but bounded at ~27%** on structure-dense content — against which A holds the carrier (renders everywhere) and the in-distribution accuracy advantage. Note the deeper point from D-002: a point edit via op is ~10–20 tokens *regardless of surface*, so the surface delta matters mainly for first-load/full-read, which bounded queries (D-028) already minimize.

## Actions

- RA11 updated in the risk register (mitigated; open-weight residual noted).
- Stage 14 §7 glyph table: status updated from "provisional" to "verified (GPT-family)".
- Re-run `bench/tokenizer_check.js` against Llama-3/Qwen tokenizers before final v1.0 freeze (G8 completes then).

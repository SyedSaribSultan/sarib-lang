# G2 corpus — agent accuracy vs Markdown (gate G2 / success test S4)

Everything here is generated and graded **programmatically** — no hand-written
answer key, no LLM judge, no designer-in-the-loop accuracy claims (RP3 discipline).

## Files

| File | What it is |
|---|---|
| `build.py` | ONE fact table → the three corpora + `questions.json`. Rerun anytime; output is deterministic. |
| `kb.sarib` | Candidate-A surface: 44 typed nodes, 42 typed edges (`depends-on`, `owned-by`, `cites`, `blocks`, `part-of`) over task/decision/question/agent/source/goal. ~1.8k tokens (o200k). |
| `kb.md` | The **same facts** as plain Markdown (headings + prose) — the honest baseline a normal user would keep. No typed fields, no wikilinks. ~1.2k tokens. |
| `kb.notypes.sarib` | **Ablation**: `kb.sarib`'s exact skeleton (same headings, nesting, field lines, prose, order) with types, ids, and typed-edge markup stripped. Isolates *types+edges* as the only variable vs condition B. ~1.2k tokens. |
| `questions.json` | 36 questions — 12 single-hop lookup, 12 multi-hop/relationship, 12 aggregate/count. Each record stores the exact `sarib query` spec, the mechanical extraction rule, and the derived answer. |
| `providers.py` | Provider registry (OpenAI-compatible): Ollama (local), Groq, Gemini, Cerebras, OpenRouter. A model is used only if its key is set / Ollama is up. |
| `results/raw-*.jsonl` | One line per (question, condition, run): model answer, provider-reported input tokens, grade. First line is a `meta` pin (model id, digest, temp, seed, date). Delete a file to force that model's rerun. |

## Ground truth: correct by construction, cross-checked

For every question, `build.py`:
1. runs the stored query spec through `impl/sarib` `query()` against the parsed `kb.sarib`,
2. applies a mechanical extraction rule (read a property / edge endpoints / count) — no inference,
3. independently recomputes the expected answer from the fact table, and
4. **aborts the build if the two disagree** (this catch found a real over-count in an early draft).

## Conditions (identical knowledge in every arm)

| Cond | Context given to the model | ~input tokens |
|---|---|---|
| A | whole `kb.md` | ~1250 |
| B | whole `kb.sarib` | ~1860 |
| C | ONLY the bounded query result for that question (the intended agent loop) | ~350 (210–615) |
| D | whole `kb.notypes.sarib` | ~1310 |

Reading the effects: **C vs A** = the S4 headline (structure + bounded retrieval);
**B vs D** = types/edges alone (same nesting); **C vs B** = retrieval alone.
Note C's token count excludes the ~30–60 tokens an agent would spend *writing*
the query; even charged, C stays far below A.

## Bias controls

- All three corpora emitted from one fact table — cannot drift apart.
- Question order shuffled per (model, condition, run), seeded.
- Grading is blind by construction (a normalizer + exact/set match; rubric fixed
  in advance in `run_g2.py`, validated by `selftest` oracle/noisy-oracle/adversary mocks).
- Temperature 0, seed 42 where the provider accepts it; 3 runs per cell, mean±std reported.

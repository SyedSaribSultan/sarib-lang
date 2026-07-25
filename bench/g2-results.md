# G2 results — agent accuracy vs Markdown (gate G2 / success test S4)

Protocol: `bench/g2-g3-protocol.md` · corpora+questions: `bench/g2-corpus/build.py` (one fact table → identical knowledge in `kb.md` / `kb.sarib` / `kb.notypes.sarib`; 36 questions, ground truth constructed via `sarib query` and cross-checked — no hand-written key, no LLM judge).

Conditions: **A** whole kb.md · **B** whole kb.sarib · **C** bounded query result only (the agent loop) · **D** kb.notypes ablation. 3 runs/cell, temp 0, seed 42 where accepted; grading = pre-registered normalized exact match (rubric in `bench/run_g2.py`). Input tokens = provider-reported `usage.prompt_tokens` (the model's own tokenizer).

## Incomplete models (rate-capped; excluded from all averages and the verdict)

- `gemini/gemini-3-flash-preview`: 20/432 cells cached — resume with `python bench/run_g2.py run --providers gemini`
- `gemini/gemini-3.5-flash`: 49/432 cells cached — resume with `python bench/run_g2.py run --providers gemini`
- `groq/llama-3.3-70b-versatile`: 245/432 cells cached — resume with `python bench/run_g2.py run --providers groq`
- `groq/qwen/qwen3.6-27b`: 357/432 cells cached — resume with `python bench/run_g2.py run --providers groq`
- `openrouter/nvidia/nemotron-3-super-120b-a12b:free`: 215/432 cells cached — resume with `python bench/run_g2.py run --providers openrouter`

## Matrix (live models)

| Model | Cond | Accuracy (mean±std) | lookup | multihop | aggregate | in-tokens | acc/1k tok |
|---|---|---|---|---|---|---|---|
| groq/llama-3.1-8b-instant | A | 58.3%±0.0 | 75.0%±0.0 | 75.0%±0.0 | 25.0%±0.0 | 1293 | 0.45 |
| groq/llama-3.1-8b-instant | B | 58.3%±0.0 | 83.3%±0.0 | 50.0%±0.0 | 41.7%±0.0 | 1905 | 0.31 |
| groq/llama-3.1-8b-instant | C | 75.0%±0.0 | 100.0%±0.0 | 50.0%±0.0 | 75.0%±0.0 | 382 | 1.96 |
| groq/llama-3.1-8b-instant | D | 47.2%±0.0 | 66.7%±0.0 | 66.7%±0.0 | 8.3%±0.0 | 1352 | 0.35 |
| groq/openai/gpt-oss-120b | A | 99.1%±1.3 | 100.0%±0.0 | 100.0%±0.0 | 97.2%±3.9 | 1325 | 0.75 |
| groq/openai/gpt-oss-120b | B | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 1929 | 0.52 |
| groq/openai/gpt-oss-120b | C | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 420 | 2.38 |
| groq/openai/gpt-oss-120b | D | 99.1%±1.3 | 100.0%±0.0 | 97.2%±3.9 | 100.0%±0.0 | 1383 | 0.72 |
| ollama/llama3.2:latest (digest=a80c4f17acd5) | A | 50.0%±0.0 | 91.7%±0.0 | 25.0%±0.0 | 33.3%±0.0 | 1283 | 0.39 |
| ollama/llama3.2:latest (digest=a80c4f17acd5) | B | 42.6%±1.3 | 86.1%±3.9 | 25.0%±0.0 | 16.7%±0.0 | 1895 | 0.22 |
| ollama/llama3.2:latest (digest=a80c4f17acd5) | C | 38.0%±1.3 | 58.3%±0.0 | 16.7%±0.0 | 38.9%±3.9 | 372 | 1.02 |
| ollama/llama3.2:latest (digest=a80c4f17acd5) | D | 52.8%±0.0 | 100.0%±0.0 | 25.0%±0.0 | 33.3%±0.0 | 1342 | 0.39 |
| ollama/qwen2.5:7b (digest=845dbda0ea48) | A | 60.2%±1.3 | 100.0%±0.0 | 50.0%±0.0 | 30.6%±3.9 | 1348 | 0.45 |
| ollama/qwen2.5:7b (digest=845dbda0ea48) | B | 55.6%±0.0 | 100.0%±0.0 | 33.3%±0.0 | 33.3%±0.0 | 1970 | 0.28 |
| ollama/qwen2.5:7b (digest=845dbda0ea48) | C | 88.9%±0.0 | 100.0%±0.0 | 91.7%±0.0 | 75.0%±0.0 | 387 | 2.30 |
| ollama/qwen2.5:7b (digest=845dbda0ea48) | D | 59.3%±1.3 | 100.0%±0.0 | 50.0%±0.0 | 27.8%±3.9 | 1407 | 0.42 |

## Significance — the S4 claim (C strictly beats A at ≤ token cost)

| Model | acc A | acc C | Δ (majority) | McNemar p | bootstrap 95% CI | tok A | tok C | S4? |
|---|---|---|---|---|---|---|---|---|
| groq/llama-3.1-8b-instant | 58.3% | 75.0% | +0.167 | 0.1796 | [-0.028, +0.361] | 1293 | 382 | PASS (not significant) |
| groq/openai/gpt-oss-120b | 99.1% | 100.0% | +0.000 | 1.0000 | [+0.000, +0.000] | 1325 | 420 | PASS (not significant) |
| ollama/llama3.2:latest | 50.0% | 38.0% | -0.111 | 0.3877 | [-0.306, +0.083] | 1283 | 372 | fail (not significant) |
| ollama/qwen2.5:7b | 60.2% | 88.9% | +0.278 | 0.0020 * | [+0.139, +0.417] | 1348 | 387 | PASS |

**Pooled (all models, 144 question-pairs):** Δ = +0.083, McNemar p = 0.0652 (n01=12, n10=24), bootstrap 95% CI [+0.000, +0.167].

## A vs B — the negative result (whole `.sarib` vs whole Markdown)

The claim this benchmark was built to test honestly: does handing a model the whole `.sarib` file beat handing it the same knowledge as Markdown? **It does not.** Across 4 complete model(s): worse on 2, flat on 1, better on 1 — while costing +45.6% to +47.7% more input tokens. There is no consistent accuracy gain from the surface syntax; the measured win (C vs A below) comes from **bounded retrieval and id-addressed edits**, not from how the file is written. This is what D-002 predicted, and it is why the syntax is not the pitch.

| Model | A acc (md) | B acc (.sarib) | B−A | A tokens | B tokens | token cost |
|---|---|---|---|---|---|---|
| groq/llama-3.1-8b-instant | 58.3% | 58.3% | +0.000 | 1293 | 1905 | +47.3% |
| groq/openai/gpt-oss-120b | 99.1% | 100.0% | +0.009 | 1325 | 1929 | +45.6% |
| ollama/llama3.2:latest | 50.0% | 42.6% | -0.074 | 1283 | 1895 | +47.7% |
| ollama/qwen2.5:7b | 60.2% | 55.6% | -0.046 | 1348 | 1970 | +46.1% |

## Ablation reads

- **B vs D (types/edges on↔off, same nesting):** structure-vs-semantics effect.
- **C vs A:** bounded retrieval + structure combined (the S4 headline).
- **C vs B:** the part of the win that is retrieval (context bounding) alone.

| Model | B acc | D acc | B−D (types effect) | C acc | C−B (retrieval effect) |
|---|---|---|---|---|---|
| groq/llama-3.1-8b-instant | 58.3% | 47.2% | +0.111 | 75.0% | +0.167 |
| groq/openai/gpt-oss-120b | 100.0% | 99.1% | +0.009 | 100.0% | +0.000 |
| ollama/llama3.2:latest | 42.6% | 52.8% | -0.102 | 38.0% | -0.046 |
| ollama/qwen2.5:7b | 55.6% | 59.3% | -0.037 | 88.9% | +0.333 |

## Diagnostic (post-hoc, NOT graded): id-for-title answers in condition C

The C context is a JSON subgraph where nodes carry both `id` and `title`; small models sometimes answer with the id of the *correct* node (`t2` instead of its title). The pre-registered grade counts these wrong (format non-compliance). Share per model:

| Model | C cells wrong | of which id-for-title (right node, wrong surface) |
|---|---|---|
| groq/llama-3.1-8b-instant | 27 | 15 |
| groq/openai/gpt-oss-120b | 0 | 0 |
| ollama/llama3.2:latest | 67 | 21 |
| ollama/qwen2.5:7b | 12 | 3 |

## Harness self-test (mock, NOT evidence)

| Model | Cond | Accuracy (mean±std) | lookup | multihop | aggregate | in-tokens | acc/1k tok |
|---|---|---|---|---|---|---|---|
| mock/adversary | A | 0.0%±0.0 | 0.0%±0.0 | 0.0%±0.0 | 0.0%±0.0 | 1254 | 0.00 |
| mock/adversary | B | 0.0%±0.0 | 0.0%±0.0 | 0.0%±0.0 | 0.0%±0.0 | 1858 | 0.00 |
| mock/adversary | C | 0.0%±0.0 | 0.0%±0.0 | 0.0%±0.0 | 0.0%±0.0 | 349 | 0.00 |
| mock/adversary | D | 0.0%±0.0 | 0.0%±0.0 | 0.0%±0.0 | 0.0%±0.0 | 1312 | 0.00 |
| mock/noisy-oracle | A | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 1254 | 0.80 |
| mock/noisy-oracle | B | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 1858 | 0.54 |
| mock/noisy-oracle | C | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 349 | 2.86 |
| mock/noisy-oracle | D | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 1312 | 0.76 |
| mock/oracle | A | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 1254 | 0.80 |
| mock/oracle | B | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 1858 | 0.54 |
| mock/oracle | C | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 349 | 2.86 |
| mock/oracle | D | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 100.0%±0.0 | 1312 | 0.76 |

`oracle` must be 100% (plumbing+grading), `noisy-oracle` 100% (normalization), `adversary` 0% (no false credit).

## Reproduce

```
python bench/g2-corpus/build.py      # regenerate corpora + ground truth
python bench/run_g2.py selftest      # mock harness proof
python bench/run_g2.py run           # every provider with a key set / Ollama up
python bench/run_g2.py report        # rebuild this file from results/*.jsonl
```

Providers/models/pins: `bench/g2-corpus/providers.py` + the `meta` line of each `results/raw-*.jsonl`. Raw per-call records (model answer, tokens, verdict) live in those jsonl files; delete a file to force that model's rerun.

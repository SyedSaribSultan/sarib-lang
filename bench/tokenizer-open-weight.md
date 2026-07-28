# G8 — open-weight tokenizer verification

**Date:** 2026-07-29 · **Method:** `bench/tokenizer_check_open.py` (HuggingFace `tokenizers`, tokenizer.json only) · **Companion:** `bench/tokenizer-report.md` (GPT family, Sprint 0)

This closes the residual left in Sprint 0, when the open-weight vocabularies could not be fetched. Test strings are **identical** to `bench/tokenizer_check.js`, so the two reports are directly comparable.

## Verdict

**PASS** — no fragmentation: every load-bearing sigil is 1–2 tokens on every tokenizer tested, and the realistic property line and wikilink stay within budget.

## Tokenizer identity (proven, not assumed)

| Family | Repo actually loaded | Vocab | Probe fingerprint |
|---|---|---|---|
| Llama 3.1 (128k BPE) | `NousResearch/Meta-Llama-3.1-8B` | 128,256 | `[2899, 487, 2884, 4416, 6531, 5163, 51436, 8366]` (12 tok) |
| Qwen 2.5 (151k BPE) | `Qwen/Qwen2.5-7B` | 151,665 | `[2829, 486, 2814, 4318, 6397, 5053, 50336, 8202]` (12 tok) |
| Mistral v0.3 (32k SP) | `unsloth/mistral-7b-v0.3` | 32,768 | `[4193, 1332, 2971, 8838, 6100, 8468, 1139, 29491]` (13 tok) |
| Gemma 2 (256k SP) | `unsloth/gemma-2-9b` | 256,000 | `[3325, 1220, 3015, 15695, 9267, 10761, 31853, 8277]` (12 tok) |
| DeepSeek-V3 (129k BPE) | `deepseek-ai/DeepSeek-V3-Base` | 128,815 | `[19027, 2366, 3989, 12955, 29753, 11621, 680, 16]` (13 tok) |

Fingerprint = first 8 token ids of `status:: done [[Target]] {.task} ^t1`. All 5 fingerprints are distinct, so these are genuinely different vocabularies.

## Bare sigils

| Sigil | Llama 3.1 (128k BPE) | Qwen 2.5 (151k BPE) | Mistral v0.3 (32k SP) | Gemma 2 (256k SP) | DeepSeek-V3 (129k BPE) |
|---|---|---|---|---|---|
| `::` | 1 | 1 | 1 | 1 | 1 |
| `[[` | 1 | 1 | 1 | 1 | 1 |
| `]]` | 1 | 1 | 2 | 1 | 1 |
| `^` | 1 | 1 | 1 | 1 | 1 |
| `#` | 1 | 1 | 1 | 1 | 1 |
| `-` | 1 | 1 | 1 | 1 | 1 |
| `>` | 1 | 1 | 1 | 1 | 1 |
| `|` | 1 | 1 | 1 | 1 | 1 |
| `{.` *(secondary)* | 2 | 2 | 2 | 1 | 1 |
| `{#` *(secondary)* | 2 | 2 | 2 | 1 | 1 |
| `:::` *(secondary)* | 1 | 2 | 2 | 1 | 1 |

## Constructs in context

| Construct | Llama 3.1 (128k BPE) | Qwen 2.5 (151k BPE) | Mistral v0.3 (32k SP) | Gemma 2 (256k SP) | DeepSeek-V3 (129k BPE) |
|---|---|---|---|---|---|
| `status:: done` | 3 | 3 | 3 | 3 | 3 |
| `due:: 2026-08-01` | 9 | 13 | 13 | 13 | 9 |
| `[due:: 2026-08-01]` | 11 | 15 | 15 | 15 | 11 |
| `priority:: high` | 3 | 3 | 3 | 3 | 3 |
| `[[Target]]` | 3 | 3 | 3 | 3 | 3 |
| `[[Adopt the new billing provider]]` | 8 | 8 | 9 | 7 | 8 |
| `[depends-on:: [[Migrate invoices]]]` | 10 | 10 | 15 | 9 | 11 |
| `{.task}` | 4 | 4 | 4 | 3 | 3 |
| `{.task #migrate-invoices}` | 9 | 9 | 11 | 7 | 9 |
| `### Migrate invoices {.task #migrate-invoices} ^t1` | 15 | 15 | 21 | 13 | 17 |
| `^t1` | 3 | 3 | 3 | 3 | 3 |
| `## Tasks [0/2 done]` | 8 | 8 | 9 | 8 | 8 |

## What the numbers say

1. **The sigils do not fragment.** All 8 load-bearing sigils are single-token everywhere except `]]` = 2 on Mistral v0.3 (32k SP) — still inside the ≤2 criterion, and a bracket pair, not a semantic mark.
2. **The attribute braces are cheaper here than on GPT models.** `{.`/`{#` cost 2 tokens on the GPT family; they cost 1 on Gemma 2 (256k SP), DeepSeek-V3 (129k BPE).
3. **Cost concentrates in content, not syntax.** `due:: 2026-08-01` ranges from 9 tokens (Llama 3.1 (128k BPE)) to 13 (Qwen 2.5 (151k BPE)) — the ISO date fragments, the `::` never does. Likewise Mistral v0.3 (32k SP) needs 15 tokens for `[depends-on:: [[Migrate invoices]]]` purely because a 32k vocabulary splits ordinary words; its `::` and `[[`/`]]` still merge intact. Short slugs and plain words remain the cheapest style, as on GPT.


## Boundary check — how the sigils actually split

**Llama 3.1 (128k BPE)**

- `status:: done` → 3 tokens: `status :: ·done`
- `[depends-on:: [[Migrate invoices]]]` → 10 tokens: `[ depends -on :: ·[[ M igrate ·invoices ]] ]`
- `^t1` → 3 tokens: `^ t 1`

**Qwen 2.5 (151k BPE)**

- `status:: done` → 3 tokens: `status :: ·done`
- `[depends-on:: [[Migrate invoices]]]` → 10 tokens: `[ depends -on :: ·[[ M igrate ·invoices ]] ]`
- `^t1` → 3 tokens: `^ t 1`

**Mistral v0.3 (32k SP)**

- `status:: done` → 3 tokens: `·status :: ·done`
- `[depends-on:: [[Migrate invoices]]]` → 15 tokens: `·[ depend s - on :: ·[[ M igr ate ·inv o ices ]] ]`
- `^t1` → 3 tokens: `·^ t 1`

**Gemma 2 (256k SP)**

- `status:: done` → 3 tokens: `status :: ·done`
- `[depends-on:: [[Migrate invoices]]]` → 9 tokens: `[ depends - on :: ·[[ Migrate ·invoices ]]]`
- `^t1` → 3 tokens: `^ t 1`

**DeepSeek-V3 (129k BPE)**

- `status:: done` → 3 tokens: `status :: ·done`
- `[depends-on:: [[Migrate invoices]]]` → 11 tokens: `[ dep ends -on :: ·[[ Mig rate ·invoices ]] ]`
- `^t1` → 3 tokens: `^ t 1`

## Scope

- Covers the **sigil/construct** half of G8, which is the half that could have invalidated the surface design (D-046).
- The whole-file Candidate A vs B comparison in `bench/tokenizer-report.md` (B saves ~27%) is **not** re-run here: `examples/B-outline-dense.sarib` is not in the repository, so that figure is not currently reproducible. Recorded as a gap; it does not affect this criterion, and A is the ratified normative surface (D-061).
- `·` in the boundary check marks a leading-space token (`\u0120` in BPE, `\u2581` in SentencePiece).


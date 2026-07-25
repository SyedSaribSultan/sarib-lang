# Constrained edge-extraction PoC — results

**Question (importer M2 rehearsal):** can a *weak* model propose typed edges over a real
`.sarib` corpus without fabricating them, if constrained hard? **Answer: yes — the safety
holds, and it comes from the constraints, not the model.**

- **Extractor:** local Ollama `qwen2.5:7b`, temperature 0 (a model that scored only ~60% on
  plain Q&A in G2 — deliberately weak).
- **Source prose:** `decisions/decision-log.md` (61 decision sections).
- **Targets:** the 61 real node ids from `dogfood/decision-log.sarib`.
- **Vocab:** `amends`, `supersedes`, `cites` (closed).
- **Rails run:** L1 existing-ids-only + L2 closed vocab (both enforced as JSON-schema `enum`
  at decode time) + L3 span-grounding (reject any edge whose evidence quote isn't verbatim in
  the source). **Verify (L4) and abstain/confirm (L5) were NOT implemented** — this is a
  Layers 1–3 floor.

## Numbers

| Metric | Result |
|---|---|
| Surviving proposals | 14 |
| Auto-rejected | 1 (bad-target; **0 for fabricated spans**) |
| **Precision (hand-verified vs source)** | **13/14 = 92.9%** |
| Fabricated / hallucinated links | **0** |
| Recall vs explicit source cross-refs | 14/60 = **23%** |

## The single error is instructive (and catchable)

`d-013 --supersedes--> d-016` is wrong: the source says D-013 is *"partly superseded by
D-016"* / *"Amended by D-016"* — so the true edge runs the **other way** (D-016 amends D-013),
which the model *also captured correctly* from D-016's side. So it's a **direction/type flip
of a real relationship, not a hallucination.** A Layer-4 entailment check ("does the quoted
span support *this directed* claim?") would almost certainly reject it, since "amended by
D-016" does not entail "D-013 supersedes D-016" — pushing precision toward ~100%.

## Reads

1. **Safety validated.** Zero fabricated links; every proposed edge points to a real node and
   quotes real text. A weak 7B model, boxed by schema-enum + span-grounding, could not invent.
   The rails carried the safety — exactly the thesis.
2. **Precision high, recall deliberately low.** 23% recall = the model abstained on ~3 of 4
   real references. For a source of truth that is the correct trade (integrity > completeness);
   missed edges get added incrementally. Recall is the dial to turn up *after* precision is
   locked (stronger model, better prompt, multi-pass, or human-confirm on lower-confidence).
3. **Caveat — this corpus is easy.** The decision log states its relationships explicitly
   ("amends D-013", "(D-014)", "Evidence: D-025"), so this is closer to *finding explicit
   references* than *inferring implicit relations from messy prose*. Real notes
   (CLAUDE.md, meeting notes) will be harder — precision and recall must be re-measured there
   before any general "canonical graph" claim.

## Layer 4 (entailment verify) — status: mechanism confirmed, full sweep not yet measured

L4 was then built and **directly probed with real model calls** (qwen2.5:7b, temp 0). A first,
terse yes/no prompt was **degenerate — it answered "no" to everything**, which would have
destroyed recall; that is why the shipped verifier uses a few-shot, natural-language claim
(`_verify` in `impl/sarib/importer.py`). Probed on four hand-picked cases it discriminates
correctly, including the exact failure above:

| Span | Claim | L4 | Wanted |
|---|---|---|---|
| "This task is blocked until we adopt Stripe." | A depends-on B | yes | yes |
| "…multi-parent via transclusion (amends D-013)" | D-016 refines D-013 | yes | yes |
| "Amended by D-016 …" | **D-013 supersedes D-016** | **no** | **no** ✅ |
| "It also builds on Adopt Stripe." | A refines B | no | borderline (conservative) |

End-to-end on a small doc: 2 proposals → 1 verified and kept, 1 dropped — the graph got the
clear `depends-on` edge and abstained on the vague one.

**Not yet measured:** the full 14-proposal L4 sweep (`verify_poc.py`, which records the
hand-verified ground truth so it is reproducible). Two attempts were lost to the local Ollama
server wedging — an environment problem, not a design one. Re-run when the model server is
healthy:

```
python bench/importer-poc/verify_poc.py     # 14 verify calls; prints L4 precision + what it caught
```

Expectation to confirm, stated in advance: L4 should reject the one direction-flip (it does in
the probe) and keep the 13 correct edges → precision ~100%, recall unchanged. **Until that run
completes, the honest headline stays the Layers 1–3 number: 93% precision, 0 fabrication.**

## Verdict for the M2 gate

The bet looks good. With only Layers 1–3, a weak model hits **93% precision and 0
fabrication**; the one miss is a catchable direction flip. **Next step:** implement Layer 4
(entailment verify) → re-measure (expect ~100% precision) → then test on a messy, non-explicit
corpus to get honest recall/precision on the real importer scenario. Only after that does the
"canonical graph via import" claim become defensible.

*Reproduce: `python bench/importer-poc/extract_poc.py` (needs Ollama + `qwen2.5:7b`).
Proposals in `proposals.jsonl`, rejects in `rejects.jsonl`. Precision hand-verified against
the source spans 2026-07-25.*

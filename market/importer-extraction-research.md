# Can an AI build the `.sarib` graph safely? — cited research

*Question (Sarib): we want the "powerful" importer where an AI reads prose and creates
the connections/edges. Since the user already has an agent, this isn't "making things up"
— so is there a **safe, constrained** way to do AI extraction that won't fabricate edges?*

**Answer: yes, and it is a solved-enough engineering pattern, not a research gamble — *if*
the extractor is built to be *extractive and constrained*, never *generative and open*.**
The danger isn't "an AI does it"; the danger is letting the AI *invent*. Every layer below
removes a degree of freedom to invent. This maps almost 1:1 onto `.sarib`'s existing
integrity rules (D-023 closed-world, D-024 never-guess, D-019 provenance, P12
retraction-not-deletion), which is strong evidence the design already anticipated this.

> **Verification note.** Citations marked ✅ were fetched and confirmed verbatim this
> session. Those marked 🔎 are from search-result summaries (publisher blocked direct
> fetch, or snippet only) — treat their *wording* as approximate but the *source* as real.
> The argument does not rest on any single 🔎 source.

---

## The failure mode we're avoiding (why the naive version hallucinates)

> "LLMs frequently hallucinate—generating plausible triplets unsupported by the source
> text. The root cause is the lack of provenance: existing methods produce triplets
> without explicit links to their textual origins, making faithfulness unverifiable." 🔎
> — *Grounded Knowledge Graph Extraction via LLMs: An Anchor-Constrained Framework with
> Provenance Tracking*, MDPI Computers 15(3):178,
> <https://www.mdpi.com/2073-431X/15/3/178>

So the fix the literature converges on is: **force provenance and constrain the space.**
Five layers, each with independent evidence.

## Layer 1 — Closed vocabulary + existing-ids-only (the AI *selects*, never *invents*)

The AI may use **only** `.sarib`'s fixed edge types, and may connect **only** nodes that
already exist (by id). It cannot mint a new relation type or a new entity. This is a named,
studied setting:

- **Closed Information Extraction (cIE):** "extracting (subject, predicate, object) triples
  from text where entities and relations must correspond to those defined in a target
  knowledge graph, constrained by a predefined KG schema." 🔎 — *LLM-empowered KG
  construction: a survey*, <https://arxiv.org/abs/2510.20345>
- **Ontology-/schema-guided extraction** works and improves consistency: systems like
  **ODKE+** "dynamically generate ontology snippets tailored to each entity type to align
  extractions with schema constraints, enabling scalable, type-consistent fact extraction."
  🔎 — <https://arxiv.org/abs/2509.04696>; see also *Ontology-Grounded Triple Extraction
  with LLMs*, <https://ceur-ws.org/Vol-4085/paper13.pdf>
- The mainstream tool already ships this knob: **LangChain's `LLMGraphTransformer`** takes
  `allowed_nodes` and `allowed_relationships`, and — tellingly — "with strict mode turned
  off, you may get node or relationship types outside the defined graph schema, as LLMs can
  sometimes take creative liberties." 🔎 So *strict mode on* = the AI is boxed to the
  schema. — <https://github.com/neo4j-labs/llm-graph-builder>

**Maps to `.sarib`:** D-023 (closed-world validation), D-021 (fixed 8-kind core vocab),
D-036 (ops address only by id).

## Layer 2 — Constrained decoding (a *structural guarantee*, not a hope)

Don't ask the model to "please output valid JSON" — *force* it. Grammar/JSON-schema
constrained decoding masks every invalid next-token during generation, so the output is
**incapable** of naming a non-existent id or an off-vocabulary edge type:

- "Constrained decoding ensures that every token an LLM generates follows predefined grammar
  rules… valid tokens are kept, while invalid ones are set to −∞ logits… This guarantees
  100% schema adherence by construction." 🔎
- Real frameworks that do this, benchmarked head-to-head — **Guidance, Outlines, llama.cpp,
  XGrammar, OpenAI, Gemini** — in *JSONSchemaBench* ✅ (title & scope confirmed:
  "a rigorous benchmark of structured outputs," evaluating "efficiency… coverage… and
  quality"). — <https://arxiv.org/abs/2501.10868>
- Commercial APIs expose it directly (OpenAI Structured Outputs accepts a JSON Schema). 🔎

This is the mechanical lock: even a careless model **cannot** emit an edge to an id that
isn't in the allowed set. **Maps to `.sarib`:** D-040 (agents write via structured-output
tooling; `.sarib`⇄JSON isomorphism).

## Layer 3 — Span grounding + provenance (every edge must show its evidence)

Require the model to return, for each proposed edge, the **exact source sentence/span** it
came from — and store it. No cited span → edge rejected. This is the anti-fabrication core:

- **Extractive, not generative:** **GLiNER** ✅ (Zaratiana et al., <https://arxiv.org/abs/2311.08526>)
  does "parallel entity extraction, an advantage over the slow sequential token generation
  of LLMs" — it *selects spans from the text* with a label set given at inference time,
  rather than generating free text. Extractive models can only point at what's present; they
  can't compose something absent. (Relation-level analogue: **GLiREL**,
  <https://arxiv.org/abs/2501.03172>.)
- **Provenance-tracked extraction** (Layer-1 anchor paper) gives "character-level provenance
  for every triplet element and enabling principled hallucination detection." 🔎

**Maps to `.sarib`:** D-019 (provenance; `inferred` assertion class already exists for
exactly this). Every auto-added edge carries `inferred` provenance + its source span.

## Layer 4 — Verify-then-commit (an independent pass deletes unsupported edges)

Before an edge is written, a second, independent check asks: *does the cited span actually
support this relation?* (natural-language-inference / entailment). This is proven to cut
hallucinations:

- **FActScore** ✅ (Min et al., EMNLP 2023, <https://arxiv.org/abs/2305.14251>): "breaks a
  generation into a series of atomic facts and computes the percentage of atomic facts
  supported by a reliable knowledge source." Crucially, its **automated support-checker has
  "less than a 2% error rate"** — i.e. machine verification of "is this claim supported by
  the source?" is already reliable.
- **Chain-of-Verification (CoVe)** ✅ (Dhuliawala et al., <https://arxiv.org/abs/2309.11495>):
  the model "drafts an initial response; plans verification questions to fact-check its
  draft; answers those questions independently…; generates its final verified response," and
  "CoVe decreases hallucinations across a variety of tasks." No fine-tuning needed.

**Maps to `.sarib`:** closed-world lint validation (D-023) becomes the commit gate.

## Layer 5 — Never-guess / abstain (the rule `.sarib` already mandates)

Anything ambiguous or unsupported is **left as plain text / `unresolved`**, never silently
linked — and because edits are reversible, a mistake is cheap:

- This is *already* D-024, verbatim: resolution is "explicit id/slug → nearest-in-containment
  → … → unresolved. Multiple equally-near matches or none → unresolved (valid, renders as
  text, lint diagnostic). **Never a silent guess.**"
- Wrong edges are recoverable: P12 (retraction, not destructive delete) + D-038 (guarded
  ops). So the worst case of an auto-added edge is "a flagged suggestion you retract," not
  "silent corruption of your source of truth."

---

## The recommended pipeline for the `.sarib` importer

```
prose (CLAUDE.md, .cursorrules, notes)
  │
  1. build nodes deterministically (headings/blocks → ids)         ← the safe "M1" skeleton
  │
  2. propose edges: agent restricted to {existing ids} × {closed edge vocab}   (Layer 1)
     └─ emitted through constrained decoding                                    (Layer 2)
     └─ each proposal MUST carry a source span                                  (Layer 3)
  │
  3. verify each proposal: does the span entail the relation? (NLI/self-check)  (Layer 4)
     └─ unsupported → dropped;  supported+high-confidence → commit as `inferred`
     └─ ambiguous/low-confidence → left unresolved, surfaced as a suggestion    (Layer 5)
  │
  4. human/agent one-tap confirm on the suggestion queue; retraction is free    (P12/D-038)
```

The AI's freedom is squeezed to: *"pick from these existing nodes, using these existing
relation types, only where the text explicitly says so, and show me the sentence."* That is
categorically different from "AI, read my notes and build me a graph" — the version that
hallucinates.

## Honest limits (integrity priority demands we state these)

1. **Structure is guaranteed; meaning is high-but-not-perfect.** Constrained decoding gives
   100% *structural* validity (no bad ids/types) — it does **not** guarantee the edge is
   *semantically* right. Grounding + verification push the semantic error rate low (FActScore
   checker <2%), not to zero. So the honest product claim is *"high-precision assisted
   extraction with provenance and one-tap confirm,"* never *"perfect automatic graph."*
2. **Precision over recall, deliberately.** Constraining hard means we **miss** some real
   edges (lower recall) to avoid asserting false ones (high precision). For a source of
   truth that is the correct trade — and it's exactly the priority order
   (integrity > completeness). Missed edges get added incrementally later.
3. **This is the M2 gate, quantified.** Before any "canonical graph" claim: run this pipeline
   on our own `decision-log.sarib` / `risk-register.sarib`, and require a **pre-stated
   precision** (e.g. ≥ 0.95 of auto-committed edges human-confirmed correct) and a beat over
   the 2-edge baseline. If it can't hit the margin deterministically, ship it as *"assisted
   authoring"* and say so.

## Bottom line

Sarib's instinct is correct and the evidence backs it: an agent *can* build the graph
without fabricating, because we don't rely on the agent's goodwill — we **remove its ability
to invent** (closed vocab + existing ids + constrained decoding), **force it to cite**
(span provenance), **independently check** (entailment/CoVe), and **abstain when unsure**
(D-024). The residual risk is *missing* edges, not *false* edges — which is the safe
direction for a source of truth.

## Sources

- Chain-of-Verification (CoVe): <https://arxiv.org/abs/2309.11495> ✅
- FActScore (EMNLP 2023): <https://arxiv.org/abs/2305.14251> ✅ · <https://aclanthology.org/2023.emnlp-main.741/>
- GLiNER (extractive, zero-shot NER): <https://arxiv.org/abs/2311.08526> ✅ · <https://github.com/urchade/GLiNER>
- GLiREL (zero-shot relation extraction): <https://arxiv.org/abs/2501.03172> 🔎
- JSONSchemaBench (constrained-decoding benchmark): <https://arxiv.org/abs/2501.10868> ✅
- LLM-empowered KG construction survey (closed IE): <https://arxiv.org/abs/2510.20345> 🔎
- ODKE+ (ontology-guided extraction): <https://arxiv.org/abs/2509.04696> 🔎
- Ontology-Grounded Triple Extraction with LLMs: <https://ceur-ws.org/Vol-4085/paper13.pdf> 🔎
- Anchor-constrained extraction w/ provenance (MDPI Computers 15(3):178): <https://www.mdpi.com/2073-431X/15/3/178> 🔎
- LangChain `LLMGraphTransformer` / Neo4j llm-graph-builder (allowed_nodes / allowed_relationships / strict_mode): <https://github.com/neo4j-labs/llm-graph-builder> 🔎

*Researched 2026-07-25. Three primary claims (CoVe, FActScore, GLiNER) plus JSONSchemaBench
verified verbatim via fetch; remainder from search summaries of real sources. Promote to
`research/` + a numbered decision (D-###) if we commit to building the constrained importer.*

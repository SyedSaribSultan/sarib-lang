# Stage 11 — Validation Rules

**Status:** Draft v0.1 — open for critique by Stage 12 · **Date:** 2026-07-15
**Input:** Stage 10 §8 brief; principles P1–P17; decisions D-001…D-048
**Decisions logged:** D-049 … D-051 (this stage)
**Phase:** D (Human Surface), stage 2 of 3.
**Scope:** How a `.sarib` artifact is checked — from "does it parse at all" to "does it conform to a vocabulary." Validation is the guarantee layer that lets humans write loosely (P3/P15) while agents and tools rely on structure. It defines nothing new about the model; it defines what "valid" *means* at three tiers and how the surface (Stage 10) maps deterministically to the model (Stage 4–5) and canonical form (Stage 9).

---

## 1. Critique of Stage 10

Stage 10 gave a forgiving surface but left three obligations that only a validation spec can discharge. **(C1)** "Everything parses; validity is lint-grade" (P15) is only safe if *un-parseability is essentially impossible* — Stage 11 must prove the surface→model mapping is total (every byte string yields a model). **(C2)** "Normalizes losslessly to the canonical form" (D-040/D-045) is a round-trip *claim* with no stated check — Stage 11 must define the idempotence/round-trip test. **(C3)** Stage 10 introduced two surfaces and derived spatial cues; validation must say what happens when a derived cue (`[1/2 done]`) is *stale* or an author hand-edits one — is that an error? (Answer: no — derived cues are ignored on read and regenerated; §4.) No principle reversed.

---

## 2. The three tiers (D-049)

Validation is layered so that authorability (P3) and machine-reliability (P10) don't fight. Each tier is a superset-check of the one below; only Tier 0 can "fail" in a way that blocks, and the forgiving surface makes even that near-impossible.

| Tier | Question | Outcome if it fails | Who relies on it |
|---|---|---|---|
| **0 · Well-formed** | Does it parse to a model at all? | (near-impossible — prose degrades to L0 nodes) a *repair* to L0, never a hard stop | everyone |
| **1 · Structurally valid** | Do the model invariants hold (single home, no dangling edges, unique ids, ids-not-positions)? | lint error with location; model still loads (offending edge dormant) | tools, agents |
| **2 · Schema-valid** | Does it conform to the active vocabulary schema (types, properties, cardinalities, edge endpoints)? | lint warning; document fully usable | schema-checked workflows |

**Nothing above Tier 0 is fatal** (P15 — forgiving surface, deterministic parse). A `.sarib` file with schema violations still opens, renders, and round-trips; the violations are *diagnostics*, not gates. This is the deliberate opposite of XML's draconian error handling and the deliberate cure for Markdown's silent divergence: every input parses, *and* every deviation is reported (Stage 2 §2.2).

---

## 3. Tier 0 — well-formedness and total parsing

The surface→model mapping is **total**: every byte string maps to a valid model.

- Any line the grammar doesn't recognize as a structural construct becomes the **content of an L0 prose node** (P9 rung 0). There is no "syntax error" that halts parsing — the worst case is that intended structure is read as plain prose (a lint hint, §5).
- Parsing is **local / no-backtracking** (djot discipline, D-045): a construct is identifiable from its shape without whole-document lookahead — required for streaming LLM generation and incremental edits (P15; Stage 6 locality).
- The parser is **deterministic** (P14): one input → one model. Ambiguity is resolved by fixed precedence rules (stated in the Stage 14 grammar), never by guessing.

Because Tier 0 cannot fail destructively, "is this valid `.sarib`?" is almost always "yes, at some rung" — which is exactly what lets a human dump prose and enrich later (D-010).

## 4. Round-trip and normalization (resolves C2)

The surface is the third serialization (D-040); validation defines its fidelity contract:

- **Normalization is idempotent:** `normalize(parse(surface))` produces the canonical form (D-041), and `normalize(normalize(x)) = normalize(x)`. A "gofmt for `.sarib`" (D-003 write-loose/store-canonical) — authors write freely; the tool settles it to one form.
- **Round-trip is lossless at the model level (P17):** `surface → model → canonical → surface'` preserves all knowledge; `surface'` may differ from `surface` in incidental formatting (whitespace, cue freshness) but never in model content. This is the writability-layer analogue of the byte-level equivalence (Stage 9 §6).
- **Derived cues are read-transparent (resolves C3):** spatial-legibility annotations (`[1/2 done]`, dotted paths, summaries — D-047) are *ignored on parse* and *regenerated on render*. A stale or hand-edited cue is never an error and never affects the model; it is silently recomputed. This keeps determinism (P14) while letting the surface carry helpful, possibly-stale scent.

## 5. Diagnostics (the lint layer)

Diagnostics are structured, located, non-fatal reports — the mechanism that makes "forgiving but not silently divergent" real. The core set:

| Diagnostic | Tier | Example |
|---|---|---|
| unresolved reference | 1 | `[[Adopt billing]]` matches no node (D-024) — link kept as text |
| ambiguous reference | 1 | a name matches multiple equally-near nodes (D-024) — never auto-picked |
| duplicate slug | 1 | two nodes claim `{#migrate}` |
| dangling/retracted endpoint | 1 | an edge to a retracted node (edge goes dormant, invariant 3) |
| cycle in acyclic edge type | 1 | a `depends-on` cycle (D-027) — reported, traversal still safe |
| unknown type/property | 2 | `{.tsak}` under an active schema — probable typo |
| cardinality / endpoint-type violation | 2 | a `cites` edge whose target isn't a `source` (D-023) |
| structure-read-as-prose | 0-hint | a line that looks like an intended construct but parsed as prose |

Each diagnostic carries a stable node/edge id (P8) and a surface location, so tools can point to it and agents can query for it (diagnostics are themselves queryable — they can be surfaced as derived nodes, D-030/P17).

## 6. Self-hosted validation (D-050)

Schemas are `.sarib` (D-023), so **validation is self-hosting**: the validator is a function `(document, active-schemas) → diagnostics`, and the schemas it checks against are themselves `.sarib` documents that can be validated by the meta-schema. Consequences:

- **No second validation language** (no separate SHACL/XSD to keep in sync — the semantic-web trap, Stage 2 §2.1). Constraints are expressed as `.sarib` nodes/edges.
- **Validation is closed-world** (D-008): an unknown type/property against an *active* schema is a diagnostic, not silent acceptance and not open-world inference. Absent an active schema, rungs 0–1 still apply and anything typed is accepted structurally.
- **Diagnostics are deterministic** (P14): same `(document, schemas)` → same diagnostics, in canonical order — so they are cacheable and CI-friendly.

## 7. Conformance surface (what a validator must do)

A conforming `.sarib` validator, given an artifact:

1. parses it to a model (Tier 0, total — never crashes on input);
2. checks the 10 invariants (Tier 1) and emits located diagnostics;
3. if schemas are active, checks conformance (Tier 2) and emits diagnostics;
4. can normalize to canonical form and confirm round-trip idempotence.

This conformance surface, plus the grammar (Stage 14) and a **conformance test corpus** (a set of input→expected-diagnostics+expected-canonical-form pairs, shipped with v0.1 per Stage 2's Markdown lesson: spec + test suite from day one, RG2), is what prevents the parser divergence that fragmented Markdown.

## 8. New decisions

- **D-049** — Three validation tiers: well-formed (Tier 0, total/near-unfailable, prose→L0), structurally valid (Tier 1, the 10 invariants), schema-valid (Tier 2, active vocabulary). Only un-parseability blocks, and the forgiving surface precludes it; all else is located, non-fatal diagnostics.
- **D-050** — Validation is self-hosted and closed-world: schemas are `.sarib` checked by a meta-schema; no second constraint language; unknown-vs-active-schema = diagnostic, not inference; diagnostics deterministic and queryable.
- **D-051** — Fidelity contract: surface normalization is idempotent to the canonical form; model-level round-trip is lossless (incidental formatting may change, knowledge never does); derived spatial cues are read-transparent (ignored on parse, regenerated on render) so staleness is never an error.

## 9. What Stage 12 (Rendering Architecture) must deliver

1. **The projection engine:** model → any view (document, outline, mind-map, dependency graph, board, timeline, table, slides) as a query (Stage 7) + a template, with every projected element carrying its node id (P8/D-033) so edits flow back (P1/P17).
2. **Writable vs terminal projections** (D-009/P17): which views are live windows (edits map back) vs explicitly read-only, and how a view declares which it is.
3. **Spatial-cue rendering** (D-047): how the derived skeleton/counts/summaries are computed and shown per view.
4. **Streaming/partial render** (D-044): render a bounded subgraph without the whole model.
5. **Determinism** (P14): same (model, view spec) → same rendering.

Then Phase D closes and Phase E (reference implementation, spec, v1.0) opens.

## 10. Risks surfaced

- **RG2 (mitigation strengthened)** — parser divergence: the three-tier conformance surface (§7) plus a day-one conformance test corpus is the concrete defense; still open until the corpus exists (Stage 13/14).
- **RM20 (new)** — normalization instability: if `normalize` isn't provably idempotent, formatting churn or diff noise results (undermining D-004/RM10). *Mitigation:* idempotence is a conformance requirement (D-051) with test-corpus coverage; canonical form is the fixed point. Medium.

This document is unratified until Stage 12 critiques it.

# Stage 6 — Traversal Model

**Status:** Draft v0.1 — open for critique by Stage 7 · **Date:** 2026-07-15
**Input:** Stage 5 (Abstract Semantic Model) §9 brief; principles P1–P17; decisions D-001…D-025
**Decisions logged:** D-026 … D-029 (this stage)
**Phase:** B (Semantic Core), stage 3 of 4.
**Scope guard:** Stage 6 defines *how knowledge is walked* — the abstract semantics of traversal over (N, E_c ∪ E_x). It does **not** define a query surface/language (Stage 7), operations (Stage 8), or syntax (Stage 10). All notation is abstract.

This stage discharges "The Most Important Requirement" of the brief: that the same knowledge support every traversal without changing the underlying representation.

---

## 1. Critique of Stage 5

Stage 5 was sound; four things it left implicit block a traversal spec.

**C1 — Stage 5 declared edge types "acyclic" but never said who enforces it or what traversal does with a cycle.** `depends-on`, `part-of`, `refines` are marked acyclic (§3.2), but *nothing prevents* a document from containing a `depends-on` cycle — a user or agent can assert one. If traversal assumes acyclicity, a single bad edge causes an infinite loop or a crash. **Resolution (§5, D-027):** "acyclic" is a *validation expectation* (a lint warning when violated), never a traversal precondition. Traversal is cycle-safe by construction (visited-set), always.

**C2 — "Compute transitive relations at query time" (D-022) has no termination story.** Query-time closure over a large or cyclic graph can be unbounded. Stage 6 must give traversal explicit bounds (§6, D-028), or D-022's no-materialization stance is unsafe in practice (this is register risk RA5).

**C3 — Stage 5 treated the brief's 13 traversals as 13 things.** They are not. Most are the same walk with different parameters, and three are not traversals at all but ways of *driving* traversals. Stage 6's central job is the reduction (§2–3), which also tells Stage 7 exactly what a query surface must parameterize.

**C4 — Unresolved references (D-024) were never given a traversal semantics.** A cross-reference can be "unresolved" (renders as text, no target). Stage 6 must say what a walk does at an unresolved edge: it is simply absent from the graph — there is no edge to follow — and optionally surfaced as a diagnostic, never a dangling pointer (§5).

No principle reversed. The big move is analytical: 13 → a handful.

---

## 2. The reduction: traversal is one parameterized walk (D-026)

Every traversal the brief names is a setting of **seven orthogonal axes** over the one graph (N, E_c ∪ E_x). There is no "linear engine" and separate "graph engine"; there is one walk, parameterized.

| Axis | Choices | What it controls |
|---|---|---|
| **Start** | a node · a set · the root · all nodes | where the walk begins |
| **Edge selector** | containment · a cross-ref type (e.g. `depends-on`) · a type set · any | which edges are eligible to follow |
| **Direction** | forward (source→target) · backward (inverse) · both | which way along edges |
| **Frontier order** | depth-first · breadth-first · priority (by property/weight) | the order the frontier is expanded and results emitted |
| **Filter** | predicate over node/edge (type, tag, property, time range, status) | which nodes are included/pruned |
| **Bound** | max-depth · max-nodes · subgraph boundary | where the walk stops (always present — §6) |
| **Derivation** | literal edges only · expand transitive closure / inverses | whether declared algebraic relations (D-022) are followed transitively |

A **traversal spec** is a choice on each axis. The result is a **bounded subgraph** (the visited nodes and the edges walked) in a **deterministic order** (§7), optionally with a continuation cursor (§6).

Three of the brief's "traversals" are not points in this space — they are **composition strategies** that drive one or more parameterized walks:

- **AI-selected** — the agent *chooses the axis settings at query time*. This is not a fixed traversal; it is the whole point of the design — the model is expressive enough that an agent composes its own walk. It presupposes the reduction rather than being a preset.
- **Parallel** — run multiple walks concurrently over disjoint or overlapping subgraphs and union the results (relevant to multi-agent work, D-014). An execution strategy, not a walk shape.
- **Comparative** — run two or more walks and align/diff their results (compare two entities' neighborhoods, two versions, two subtrees). A post-processing strategy over walks.

**So: 10 of the brief's 13 are presets of one walk; 3 are ways to drive it.** "Traversal" is not a feature list — it is one primitive with parameters (D-026). This is the precise discharge of Stage 1's C5 ("the 13 traversals collapse into … a query over a sufficiently expressive model").

---

## 3. The 13 traversals as presets

Each named traversal is the following axis setting over (N, E_c ∪ E_x):

| # | Brief traversal | Start | Edge selector | Dir | Order | Filter | Derivation |
|---|---|---|---|---|---|---|---|
| 1 | **Linear reading** | root | containment | fwd | DFS pre-order, sibling `order` | — | literal |
| 2 | **Tree** | node/root | containment | fwd | DFS or BFS | — | literal |
| 3 | **Breadth-first** | node | containment or any | fwd | BFS | — | literal |
| 4 | **Depth-first** | node | containment or any | fwd | DFS | — | literal |
| 5 | **Dependency** | node/set | `depends-on` | fwd | topological | often type=task/goal | transitive |
| 6 | **Priority** | set | (none/any) | — | priority (sort by `priority`) | often type=task | literal |
| 7 | **Semantic** | node | `relates-to`,`refines`,`tag` | both | DFS/ranked | — | transitive (concept hier.) |
| 8 | **Chronological** | set | (none/any) | — | order by `timestamp`/`from` | often type=event | literal |
| 9 | **Tag** | a concept | `tag` | backward (`tagged-by`) | any | — | transitive over concept `part-of` |
| 10 | **Relationship** | node | any cross-ref | both | BFS, bounded depth | — | literal |
| 11 | **AI-selected** | — | *(agent composes any of the above at query time)* | — | — | — | — |
| 12 | **Parallel** | — | *(N independent walks, results unioned)* | — | — | — | — |
| 13 | **Comparative** | — | *(≥2 walks, results aligned/diffed)* | — | — | — | — |

Two observations fall out:

- **Priority and chronological aren't graph walks at all** — they are *orderings of a node set* (sort by a property). They fit the same spec (start = a set, edge selector = none, order = by-property), which is why one primitive covers them: a "walk" with no edges is just a filtered, ordered selection. This unifies "query the set" and "walk the graph" under one operation.
- **Tag traversal is relationship traversal in reverse** — following `tag` backward from a concept. It needs no special machinery, only the `direction=backward` axis over declared inverses (D-022).

---

## 4. The linear-reading anchor (deliverable 2)

Linear reading (preset #1) is privileged for one reason: it is the *only* traversal that is also the **serialization order** (Stage 4 §6). The document you read top-to-bottom is `inorder(N, E_c)` — DFS pre-order of the containment tree by sibling `order`.

Every other preset in §3 reuses the **exact same (N, E_c ∪ E_x)** with different axis settings. Nothing is restructured, duplicated, or re-indexed to support them — the direct realization of P1 (store once, render infinitely): the boards, timelines, dependency graphs, and tag clusters the brief wants are all presets over the one structure that also happens to serialize as a readable document. The document is traversal #1, not a separate artifact.

---

## 5. Traversing derived relations, cycle-safely (deliverable 3; D-027)

**Derived edges are never read from storage — they are computed by the walk** (D-022). Two cases:

- **Inverse** (e.g., `owns` = inverse of `owned-by`): to walk `owns` from an agent, the engine follows `owned-by` edges *backward*. No `owns` edge is stored; `direction=backward` over the declared inverse is the whole mechanism.
- **Transitive closure** (e.g., all transitive `part-of` ancestors): the engine follows `part-of` recursively, accumulating reached nodes. `A part-of B`, `B part-of C` are stored; `A part-of C` is produced by the walk, not written (honoring P10/P11 — derived stays derived).

**Cycle-safety is unconditional (D-027).** The walk maintains a visited-set keyed by node id; a node is emitted on first visit and pruned on any re-encounter. This holds regardless of an edge type's declared algebra: even though `depends-on` is *expected* acyclic (Stage 5 §3.2), traversal never assumes it. A real cycle (asserted by a user/agent) yields a finite walk plus an optional `cycle-detected` diagnostic (and, for topological order, the cycle's members are reported rather than ordered). "Acyclic" is a lint expectation, never a traversal precondition — this is the resolution of C1 and closes a latent infinite-loop/crash hazard.

**Unresolved references (C4):** an unresolved cross-reference (D-024) is *not an edge* — there is no target node, so there is nothing to follow; the walk simply never sees it. It may be surfaced as a diagnostic for the author, but it is never a dangling pointer that a traversal can trip on (satisfies invariant 3 of Stage 4 §11).

---

## 6. Scope, bounds, and cost (deliverable 4; D-028)

**Every traversal is bounded. Unbounded traversal is not part of the standard interface (D-028).** A spec always carries at least one of: `max-depth`, `max-nodes`, or a `subgraph boundary` (e.g., "within this section's containment subtree"). Filters are applied at the frontier so pruned branches are never expanded.

A traversal returns a **bounded result subgraph plus an optional continuation cursor**: if the walk hits its bound before exhausting the frontier, it returns what it has and a cursor to resume. This gives three properties the AI-native goal requires:

- **Minimal context.** An agent fetches only the subgraph it needs, not the whole file — the direct answer to length-degradation and context economics ([ai-context.md](../research/ai-context.md); P14). "Request only the required context" (the brief's AI-experience goal) is this.
- **Streaming.** Large results arrive in bounded pages via the cursor (P14; supports partial loading).
- **Cost proportional to result, not graph.** Work is bounded by (frontier discipline × bounds), independent of total graph size — the property that keeps traversal viable as a knowledge base grows (register RM11).

Cost note for derived relations (C2/RA5): transitive closure is bounded by the same `max-depth`/`max-nodes`, so query-time derivation (D-022) can never run away; the bound is the safety valve that makes no-materialization affordable.

---

## 7. Determinism (deliverable 5; D-029)

Traversal is a **pure function of (graph, traversal spec)** — every conforming engine yields identical results in identical order. This requires a total tie-break order wherever the graph offers a choice of next edge. The cascade:

1. **Containment** siblings: by their `order` ordinal (Stage 4 §5.1) — the authorial sequence.
2. **Cross-reference** edges from a node, when order matters: by (edge-type name, then target node canonical id, then edge id).
3. **Frontier discipline** (DFS/BFS): expand candidates in the order given by 1–2.
4. **Property orders** (priority/chronological): by the sort key, with a stable tie-break on node id.
5. **Visit-once**: a node is emitted at its first visit; the visited-set is keyed by node id (§5).

Because node and edge ids are totally orderable (the `(replica, counter)`/ULID constraint, D-014), the cascade is total — there is never an undefined "which next." Determinism here composes with the deterministic serialization (invariant 10) and reference resolution (D-024): the whole pipeline from bytes → model → traversal is reproducible across tools (P14/P15), which is also what makes traversal results safely cacheable for KV-cache reuse (P14).

---

## 8. Worked examples (abstract — reusing the Stage 4 graph)

Recall the Stage 4 §10 graph: document n1 with sections n2 (Decisions) and n4 (Tasks); decision n3; tasks n5 (Migrate invoices), n6 (Notify customers); person n7 (Alice). Edges: `n5 depends-on n3`, `n6 depends-on n5`, `n5 owned-by n7`, `n3 tag c1(billing)`.

**A · Linear reading** (preset #1): start=n1, containment, DFS pre-order →
`n1 → n2 → n3 → n4 → n5 → n6`. This is the document. Alice (n7) lives in the hidden entity home, so she is absent from the prose reading (P17 — hidden, not dropped).

**B · Dependency** (preset #5): start=n6, selector=`depends-on`, forward, topological, transitive →
`n6 → n5 → n3`. Produces the build/authoring order for "Notify customers." The `n5→n3` and `n6→n5` edges are literal; the transitive `n6 ⇒ n3` relation is computed by the walk, never stored (D-022).

**C · By-person** (relationship, backward): start=n7, selector=`owned-by`, direction=backward (`owns`) →
`n7 owns {n5}`. No `owns` edge exists in storage; the walk follows `owned-by` backward (§5).

**D · Comparative** (strategy #13): run B for n6 and for a hypothetical n8, align the two dependency sets → the shared prerequisite n3 surfaces as the intersection. Two walks, one diff.

**E · Rename resilience:** rename n7 "Alice" → "Alice Chen". Every traversal above is unchanged — walks follow ids, not names (Stage 4 §4). This is the payoff of stable identity showing up at the traversal layer.

Same graph, five readings, zero restructuring.

---

## 9. New decisions

Full entries in `../decisions/decision-log.md`:

- **D-026** — The brief's 13 traversals reduce to one parameterized walk over seven axes (start · edge-selector · direction · frontier-order · filter · bound · derivation); 10 are presets, 3 (AI-selected, parallel, comparative) are composition strategies over it. Traversal is one primitive, not a feature list.
- **D-027** — Traversal is cycle-safe by construction (visited-set by node id, emit-once); edge-type "acyclic" metadata is a validation expectation (lint), never a traversal precondition.
- **D-028** — Every traversal is bounded (depth/nodes/subgraph); the standard interface has no unbounded traversal. Results are a bounded subgraph + optional continuation cursor (minimal context, streaming).
- **D-029** — Traversal is a pure function of (graph, spec) via a total tie-break cascade (containment order → edge-type → target id → edge id), reproducible across tools.

---

## 10. What Stage 7 (Query Model) must deliver

Stage 6 defined the walk; Stage 7 defines how a human or agent *asks for* one:

1. **A query surface over the seven axes** (D-026) — how a caller specifies start/selector/direction/order/filter/bound/derivation, abstractly (not syntax).
2. **Filter/predicate language** — the expression sublanguage for the `filter` axis (type, tag, property comparisons, time ranges, status), kept minimal (priority rule 4).
3. **Return shape** — the bounded subgraph + cursor contract (D-028) as a first-class query result; how it maps back to node/edge ids for editing (P8/P17).
4. **Composition** — how AI-selected/parallel/comparative (the three strategies) are expressed as compositions of base queries.
5. **Determinism & cost contract** — surfacing D-029/D-028 guarantees to the caller (stable order, bounded cost) so agents can rely on them for caching.
6. **The read/write bridge** — a query result carries ids, so it is the addressing mechanism operations (Stage 8) use to target edits. Stage 7 should define that hand-off.

Deferred still: operations (Stage 8), syntax (Stage 10).

## 11. Risks surfaced by this stage

Filed/updated in `../risks/risk-register.md`:

- **RA5 (updated)** — derived-relation query cost: now mitigated by mandatory bounds (D-028); residual only for very large transitive closures within-bound. Status stays open, mitigation strengthened.
- **RM15 (new)** — traversal determinism depends on a total order over edges; if edge ids were not totally orderable across replicas, the tie-break cascade (D-029) would break. Mitigated by the `(replica,counter)`/ULID id constraint (D-014). Low.
- **RA9 (new)** — "semantic traversal" (#7) partly wants an external similarity signal (embeddings) not in the model; the canonical form follows explicit semantic edges (`relates-to`/`refines`/`tag`) deterministically, and any embedding-ranked variant is an explicitly non-canonical, tool-provided extension (so results stay reproducible where it matters). Medium.

This document is unratified until Stage 7 critiques it.

# Stage 7 — Query Model

**Status:** Draft v0.1 — open for critique by Stage 8 · **Date:** 2026-07-15
**Input:** Stage 6 (Traversal Model) §10 brief; principles P1–P17; decisions D-001…D-029
**Decisions logged:** D-030 … D-034 (this stage)
**Phase:** B (Semantic Core), stage 4 of 4 — **this stage closes Phase B.**
**Scope guard:** Stage 7 defines the *query model* — the abstract structure of a request for knowledge and the shape of what comes back. It does **not** define a query *syntax* (Phase D / Stage 10), operations (Stage 8), or serialization (Stage 9). All notation is abstract.

Where Stage 6 defined the *walk* (execution), Stage 7 defines the *ask* (specification) and the *answer* (result), and — most importantly — the **read/write bridge** that turns "read the graph" into "edit the graph atomically," which is the token-efficiency payoff the whole project is built on (D-002).

---

## 1. Critique of Stage 6

Stage 6 was clean; four things it left open block a usable query model.

**C1 — The `filter` axis was hand-waved.** Stage 6 said filter is "a predicate over node/edge (type, tag, property, time range, status)" but never defined the predicate language. This is the single most dangerous underspecification in the project: make it too rich and `.sarib` grows an embedded programming language (scope death, priority rule 4); make it too poor and real questions can't be asked. Stage 7 must pin the *minimal sufficient* predicate algebra (§4, D-031).

**C2 — "Returns a bounded subgraph" was never given a shape.** A subgraph of *what* — just ids? full nodes? which properties? The return shape is not a detail; it *is* the read/write bridge and the token-budget control. Stage 7 must specify it precisely (§5, D-032).

**C3 — The three composition strategies (AI-selected, parallel, comparative) had no mechanics.** Stage 6 named them; Stage 7 must say how they actually compose (§6, D-034), or they remain hand-waves.

**C4 — Stage 6 conflated "traversal" and "query."** They are different layers: a **query** is the caller's specification; a **traversal** is the execution primitive it compiles to (Stage 6). Keeping them distinct matters because a query can compile to *several* traversals (composition) and because a query is itself knowledge worth storing (§2, D-030). No syntax is introduced — the query *model* is structural.

No principle reversed.

---

## 2. Queries are self-hosted (D-030)

A query is knowledge — a saved view ("my open tasks," "decisions this quarter," "everything blocking the launch") is a durable, shareable, versionable thing. So, consistent with D-015 (everything worth structure is a node) and D-023 (schemas are self-hosted `.sarib`):

**A query is a node** of kind `query`/`view` whose properties specify the seven traversal axes plus a projection. There is no separate query-object language to invent; the object model already has everything needed. Consequences:

- **Saved views are first-class knowledge** — they live in the graph, carry ids, are cited, versioned, retracted, and projected like any node (P1). A dashboard is a set of `query` nodes.
- **Queries are addressable and composable** — one query can name another as its input (§6), because inputs are just node references.
- **The query surface (how you *write* one) is deferred to Phase D**, exactly like every other surface. Stage 7 fixes the query *model*, not its syntax.

A query node's fields:

```
Query = (
  start:       NodeSet            // ids, "all", "root", or a ref to another query's result
  select:      EdgeSelector       // edge type(s), family(ies), or "any", or "none" (pure selection)
  direction:   forward | backward | both
  order:       document | dfs | bfs | topological | by-property(key, asc|desc)
  filter:      Predicate?         // §4 — absent = match all
  bound:       { max_depth?, max_nodes?, within?: NodeSet }   // at least one required (D-028)
  derivation:  literal | transitive | inverse-expanded         // D-022
  projection:  Projection         // §5 — what to return per node/edge
)
```

The first seven fields are precisely Stage 6's axes (D-026); `projection` is new here and controls the return shape (§5). This is the whole query surface — seven axes and a projection.

---

## 3. From query to execution

A query compiles to one or more Stage-6 traversals:

- A **simple query** (single start, single selector) → one parameterized walk (Stage 6 §2).
- A **pure selection** (`select: none`) → the degenerate no-edge walk: filter + order over a node set (Stage 6 §3 — this is how priority/chronological work).
- A **composed query** (§6) → several walks whose results are combined by set operations.

The compilation is deterministic (D-029) and bounded (D-028): those guarantees flow straight through from traversal to query, and are surfaced to the caller as a contract (§7).

---

## 4. The filter predicate algebra (resolves C1; D-031)

The filter axis is a **decidable boolean predicate algebra** — deliberately not a programming language. It is exactly powerful enough to select nodes/edges by their own fields, and no more.

**Atomic predicates** (each evaluates against a single node or edge):

| Predicate | Tests |
|---|---|
| `type-in {…}` | node/edge type membership |
| `has-tag C` | an outgoing `tag` edge to concept C (or its `part-of` descendants, under `derivation:transitive`) |
| `prop(key) OP value` | property comparison; `OP ∈ {=, ≠, <, ≤, >, ≥}` on scalars/timestamps/quantities |
| `prop(key) exists` | property presence |
| `prop(key) contains v` | membership for `list<>` / substring for `text` |
| `status = active \| retracted` | lifecycle state (D-019) |
| `asserted-by class` | provenance class ∈ {asserted, inferred, imported} (D-019) — e.g. *exclude agent-inferred facts* |
| `has-edge T [to X]` | existence of an incident edge of type T (optionally to a node/type X) — a relationship/degree test |

**Combinators:** `AND`, `OR`, `NOT` over a finite predicate tree. Nothing else.

**Deliberately excluded** (priority rule 4 — these turn a filter into a language, and each is either the agent's job or a result transform):

- arithmetic / computed expressions (`prop(a) + prop(b) > 10`);
- user-defined functions, recursion, or quantifiers over arbitrary subqueries;
- joins on arbitrary conditions (relationship structure is expressed by the `select`/`direction` axes, not the filter).

**Aggregation** (count, group-by, min/max/sum over a result) is a **separate, optional result transform** applied *after* the query returns (§5), never inside the predicate. This keeps predicate evaluation O(fields) per node — cheap, decidable, and bounded — which is what lets the cost contract (§7) hold.

The design test (D-031): the filter language must be **decidable and per-node-local** — every predicate is answerable by looking at one node/edge and its immediate incident edges, with no unbounded computation. Anything requiring more is the agent's reasoning job (AI-selected, §6), not the filter's.

---

## 5. The result subgraph (resolves C2; D-032)

A query returns a **result subgraph** — the single most important object for the AI-native goal, because it is simultaneously the answer *and* the edit target.

```
Result = (
  nodes:   [ { id, projected fields } … ]   // in deterministic order (D-029)
  edges:   [ { id, type, source, target, projected props } … ]  // those walked / among matched nodes
  cursor:  Cursor?                           // present iff a bound was hit (D-028)
  diagnostics: [ … ]                         // unresolved refs seen, cycles detected, lint
)
```

The **projection** (a query field, §2) controls what each node/edge carries back, which is the token-budget dial:

- default projection: `id, type, name` + a short content snippet — enough to identify and reason, cheap in tokens;
- expandable: the caller asks for full `content`, specific properties, specific incident edges — pulled only when needed.

Two properties make this the linchpin of the design:

1. **Every returned node and edge carries its stable id** (P8). The result is not prose *about* the knowledge; it is an *addressed selection of* the knowledge.
2. **The projection is minimal by default.** An agent fetches `id + name + snippet` for 20 nodes (cheap), reasons, then pulls full content for the 2 it needs — the direct realization of "request only the required context" (the brief's AI goal; P14; length-degradation economics, [ai-context.md](../research/ai-context.md)).

Retracted nodes/edges are excluded unless `status` is explicitly queried (D-019/P12); derived relations appear only under `derivation` and are marked `inferred` if surfaced (D-022).

---

## 6. Composition (resolves C3; D-034)

Because a result is a node-set (each with an id), queries compose by **piping** (one query's result is another's `start`) and by **set operations** on result node-sets (`union`, `intersect`, `difference`, keyed by id). This gives the three Stage-6 strategies concrete mechanics:

| Stage-6 strategy | Query-model mechanics |
|---|---|
| **Parallel** (#12) | run N independent queries; `union` their results (dedupe by id). The walks may run concurrently (multi-agent, D-014); union is order-deterministic by the tie-break cascade (D-029) |
| **Comparative** (#13) | run ≥2 queries; combine by `intersect` (shared), `difference` (only-in-A), and align by id/name — e.g. shared prerequisites of two tasks = `intersect(deps(A), deps(B))` |
| **AI-selected** (#11) | the agent *constructs a Query node at runtime* from the seven axes and issues it. No special machinery — it is just building an object and running it. This is the point of the whole model: expressive enough that an agent composes its own view |

So the three "strategies" are not new primitives; they are set-algebra and runtime construction over the base query. That closes the loop Stage 6 opened.

---

## 7. Determinism & cost contract (D-028/D-029 surfaced)

A query offers the caller two guarantees it can build on:

- **Determinism:** same `(graph state, query)` → identical result, identical order (D-029). Reproducible across conforming engines; safe to cache (KV-cache reuse for agents, P14).
- **Bounded cost:** work ≤ `bound` × per-node predicate cost, and predicate cost is O(fields) (D-031) — so cost is proportional to the *result*, not the graph (D-028). An agent can predict token/compute budget before issuing the query.

These are contract-level promises, not implementation notes: a `.sarib` query engine that violates determinism or unboundedness is non-conforming. This is what makes the read/write loop (§8) safe to automate.

---

## 8. The read/write bridge (D-033) — the hand-off to Phase C

This is the architectural pivot of the whole standard. A query result is an **addressed selection**: a set of `(id, projection)` pairs. Operations (Stage 8) take **ids** as their targets. Therefore:

> **Query results are the sole addressing mechanism for edits.** An agent reads a minimal subgraph by query, reasons over it, then issues operations that target the exact node/edge ids the query returned — never positions, never regenerated documents (D-033, reaffirming P13).

The agent loop this enables:

1. **Query** — fetch the minimal relevant subgraph (cheap: ids + snippets).
2. **Reason** — over that small, high-signal context.
3. **Operate** — emit atomic operations addressed by id (Stage 8): create/retract/link/set-property/move…
4. **Re-query** — to see the effect.

Step 3 costs tens of tokens (a delta); the naïve alternative — regenerate the document — costs thousands (D-002, the founding efficiency thesis). The query model is what makes step 1 minimal and step 3 precisely addressable. **This loop is the concrete meaning of "touch knowledge atomically; never regenerate what you can address"** (Stage 1 vision).

One hazard this bridge introduces (filed as RM17): the graph can change between the read (step 1) and the write (step 3) — a classic lost-update race. Stage 8 must give operations an **optimistic-concurrency precondition** (a version/status check on the targeted id, the `test`-op pattern of JSON Patch, [RFC 6902](https://www.rfc-editor.org/rfc/rfc6902)) so a stale write is rejected rather than silently clobbering. Flagged here, designed there.

---

## 9. Worked examples (abstract — reusing the Stage 4 graph)

Graph recap (Stage 4 §10): sections n2 (Decisions)/n4 (Tasks) under doc n1; decision n3; tasks n5 (Migrate invoices, due 2026-08-01)/n6 (Notify customers); person n7 (Alice). Edges: `n5 depends-on n3`, `n6 depends-on n5`, `n5 owned-by n7`, `n3 tag c1(billing)`.

**Q1 — "Open tasks by due date"** (pure selection):
`start:all · select:none · filter: type-in{task} AND prop(status)≠done · order:by-property(due,asc) · bound:max_nodes 50 · projection:{id,name,due}`
→ Result nodes: `[n5 (Migrate invoices, 2026-08-01), n6 (Notify customers, —)]`, deterministic order, no cursor.

**Q2 — "What must happen before Notify customers?"** (dependency walk):
`start:{n6} · select:depends-on · direction:forward · order:topological · derivation:transitive · bound:max_depth 10 · projection:{id,name,type}`
→ Result: nodes `{n6, n5, n3}`, edges `{n6→n5, n5→n3}`. The transitive `n6⇒n3` is computed, not stored (D-022).

**Q3 — "Shared prerequisites of n6 and n8"** (comparative composition):
`intersect( Q2(start:n6), Q2(start:n8) )` → the common blocker surfaces as the id-keyed intersection (§6).

**Q4 — the read/write loop** (the payoff): agent runs Q1, gets `n5`'s id, decides it's done, and issues (Stage 8) `set-property(n5, status, done)` — an edit addressed by id costing ~a dozen tokens. No section was re-read, no document regenerated (D-033/D-002). Re-running Q1 now returns only `n6`.

**Q5 — trust filter** (provenance): `filter: type-in{decision} AND asserted-by=asserted` → returns only human-asserted decisions, excluding agent-inferred ones (D-019) — a one-line guard against inference pollution.

---

## 10. New decisions

Full entries in `../decisions/decision-log.md`:

- **D-030** — Queries are self-hosted: a query/view is a node specifying the seven axes + a projection; saved views are first-class knowledge. Query *syntax* is deferred to Phase D.
- **D-031** — The filter axis is a decidable, per-node-local boolean predicate algebra (type/tag/property-compare/exists/contains/status/provenance-class/edge-existence, combined by AND/OR/NOT); no arithmetic, functions, recursion, or joins. Aggregation is a separate post-query result transform.
- **D-032** — A query returns a result subgraph: matched nodes+edges each carrying a stable id and a caller-specified projection, in deterministic order, with an optional cursor and diagnostics.
- **D-033** — Query results are the sole addressing mechanism for operations (the read/write bridge): edits target ids surfaced by queries, never positions.
- **D-034** — Composition: parallel = union of results; comparative = intersect/difference + id/name alignment; AI-selected = runtime construction of a query node. The three Stage-6 strategies are set-algebra + runtime construction over the base query, not new primitives.

---

## 11. Phase B exit check

Charter exit criterion for Phase B: *"All 13 traversals from the brief expressible as queries over the model."* Status: **met.**

- Stage 4 gave the object model (one graph; document = containment spanning-tree).
- Stage 5 gave it meaning (vocabulary, edge semantics, schemas, resolution).
- Stage 6 reduced the 13 traversals to presets of one parameterized walk.
- Stage 7 exposes that walk as a self-hosted query with a minimal filter algebra, a result-subgraph return shape, composition, and the read/write bridge.

Every one of the brief's 13 traversals is a query object per §2 + the §3 presets table of Stage 6, and the three that were "strategies" are now set-algebra compositions (§6). The abstract machine is complete and internally consistent: **one identified property graph; one canonical serialization (its containment spanning-tree); one parameterized traversal; one self-hosted query; one id-addressed edit bridge.** Phase C can now define how bytes and agents interact with it.

Coherence note: nothing in Stages 5–7 contradicts the Stage 4 invariants or the priority ordering (integrity > writability > efficiency > completeness); the filter-language cut (D-031) and the mandatory bound (D-028) are both that priority rule applied.

---

## 12. What Stage 8 (AI Interaction Protocol) must deliver

Phase C opens. Stage 8 defines the **operation vocabulary** — the atomic edits that are the canonical unit of change (P11) and the token-efficiency engine (D-002):

1. **The op set** — create/retract node, set/unset property, add/retract edge, move (retarget containment), merge, split, promote/demote (Stage 4 §3.1), tag — closed under the 10 model invariants (Stage 4 §11; register RM14).
2. **Addressing** — ops target ids from query results (D-033); never positions (P13).
3. **Commutativity & merge** — ops designed so concurrent ops commute (D-014); the CRDT-ready path.
4. **Optimistic concurrency** — a precondition/version check per op to prevent lost updates (RM17; JSON Patch `test`-pattern).
5. **Retraction semantics** — deletion as status assertion (P12); compaction as a separate explicit op.
6. **Op-log ↔ state** — ops as the canonical journal; state as a fold (P11; event-sourcing/Datomic, [versioning-and-merge.md](../research/versioning-and-merge.md)); demonstrate op-log/state equivalence (charter Phase C exit criterion).
7. **Transport-agnostic shape** — ops as data (self-hosted where possible), so they ride any channel (MCP, file patches).

Deferred still: serialization/canonical form (Stage 9), syntax (Stage 10).

## 13. Risks surfaced by this stage

Filed in `../risks/risk-register.md`:

- **RM16 (new)** — filter-algebra too weak: a real, common query can't be expressed within D-031's decidable subset. *Mitigation:* saved/composed queries + the escape that genuinely complex analysis is the agent's job (AI-selected), not the filter's; revisit the atomic-predicate set after dogfooding. Medium.
- **RM17 (new)** — query→operation staleness (lost update): the graph changes between read and write, so an id-addressed edit clobbers a concurrent change. *Mitigation:* optimistic-concurrency precondition per op (Stage 8, D-014/RFC 6902 `test`); this is *the* correctness item Stage 8 must nail. High impact, medium likelihood.

This document is unratified until Stage 8 critiques it.

# Stage 5 — Abstract Semantic Model

**Status:** Draft v0.1 — open for critique by Stage 6 · **Date:** 2026-07-15
**Input:** Stage 4 (Core Object Model) §13 brief; principles P1–P17; decisions D-001…D-019
**Decisions logged:** D-020 … D-025 (this stage)
**Phase:** B (Semantic Core), stage 2 of 4.
**Scope guard:** Stage 4 fixed the *shape* of knowledge (nodes, edges, identity, invariants). Stage 5 fixes its *meaning* — what types exist, what edges mean, how constraints are stated, how names resolve, how vocabularies evolve. Still no file syntax (Phase D / Stage 10); no operations (Stage 8); no query execution (Stage 7). All notation is abstract.

---

## 1. Critique of Stage 4

Stage 4 was structurally sound; three gaps and one latent error surface once you try to give the model meaning.

**C1 — Stage 4's edges are binary, but knowledge is often n-ary and time-qualified.** "Alice worked at Acme from 2020 to 2023 as CTO" is one fact with four arguments (person, org, interval, role). A directed binary edge `Alice —worked-at→ Acme` drops the interval and the role. Stage 4 never said how. **Resolution (§4, D-020):** a first-class edge (D-017) already carries properties, so it *is* a qualified statement — `worked-at` with properties `{from, to, role}`. This is exactly Wikidata's qualifier model ([Wikidata CACM](https://iccl.inf.tu-dresden.de/w/images/8/89/Wikidata-CACM-2014.pdf)), and it means `.sarib` needs no hyperedges in v1. Stage 5 must state this explicitly, because it was luck, not design, that the Stage 4 edge could carry it.

**C2 — Several of the brief's "node types" are category errors.** The brief lists `dependency` and `relationship` as node kinds — but those are *edges*, not nodes. It lists `constraint`, `risk`, and (elsewhere) `priority` as first-class objects — but those are usually *properties* of a task/decision, or prose, not entities with identity. Stage 4 deferred the vocabulary; Stage 5 must reclassify before it can choose a vocabulary, or the standard library inherits the brief's confusion (§2, D-020).

**C3 — Reference resolution was only sketched (Stage 4 §4).** "Resolved by context (nearest-in-containment, or explicit)" is not a specification. Two authors, two agents, and one parser must resolve the same name to the same node or the graph silently forks. Stage 5 must give the deterministic rule (§6, D-024).

**C4 — The ladder put tags at L4 (properties) but Stage 4 §5.4 modeled them as edges (L3).** A real inconsistency. **Resolution:** a tag is *semantically* a cross-reference edge to a concept node (L3), and the "L4 tag" rung is only the ergonomic gesture; the two are the same edge viewed at different rungs. Stated in §2 and reconciled in the ladder note.

No principle reversed; one Stage 4 construct (binary edges) is shown to be sufficient only because edges carry properties — a dependency now made explicit.

---

## 2. The standard vocabulary v0

### 2.1 The inclusion test (operationalizes priority rule 4)

A type earns a place in the **core standard vocabulary** only if it passes all three gates:

1. **Domain-agnostic** — it appears across knowledge domains (planning, research, writing, ops), not just one (software, design).
2. **Behavior-changing** — knowing the type changes what an agent or a projection *does* (a `task` appears on a board and has done/undone; a `question` appears in a Q&A view). A type that only relabels prose fails this gate.
3. **Irreducible** — it cannot be expressed adequately as a tag or property on a prose node without losing queryable behavior.

Everything that fails a gate goes to a **domain vocabulary** (optional, namespaced) or becomes a **property/edge** instead of a node kind.

### 2.2 Reclassifying the brief's 28 (resolves C2) — D-020

| Brief term | Correct classification | Rationale |
|---|---|---|
| task, decision, question, goal | **core node kind** | domain-agnostic, behavior-changing, irreducible |
| person, organization | **core node kind** → unified as `agent` with a `kind` property | both are "actors"; one kind, a discriminator property |
| reference, file | **core node kind** → unified as `source` | an external citable thing; `file` is a `source` with a locator |
| meeting, experiment, event | **core node kind** → `event` (temporal); meeting/experiment are `event` subtypes in domain vocab | time-anchored occurrences; one temporal primitive |
| concept | **core node kind** | the tag/topic target; enables semantic grouping |
| metric, vision | **domain / property** | `metric` → domain vocab; `vision` → a `goal` with scope, or prose |
| API, database, component, bug, feature | **domain vocab** (`sarib-software`) | single-domain (fails gate 1) |
| animation, motion | **domain vocab** (`sarib-design`) | single-domain |
| dependency, relationship | **edge type, not node** | these *are* relationships (§3) |
| constraint, risk, priority | **property, not node** | attributes of a task/decision/goal; `risk` may also be prose |

### 2.3 Core standard vocabulary v0 (D-021)

Node kinds — eight, each passing the test:

| Kind | Purpose | Distinguishing behavior |
|---|---|---|
| `task` | actionable item | status (todo/doing/done), due, assignee → boards, checklists |
| `decision` | a settled choice | status (proposed/accepted/superseded), rationale → decision logs |
| `question` | an open inquiry | status (open/answered), links to answers → Q&A / research views |
| `goal` | a desired outcome | measurable?, timeframe, parent/child goals → OKR/roadmap views |
| `event` | a time-anchored occurrence | start/end, participants → timeline, calendar |
| `agent` | a person or organization | kind (person/org), contact → by-owner views, responsibility |
| `source` | an external citable thing | locator (URL/file/DOI) → citations, bibliographies |
| `concept` | a topic/tag target | broader/narrower → tag hierarchies, semantic grouping |

Everything else from the brief is a domain vocabulary, a property, or an edge. This is the aggressive cut priority rule 4 demanded (S6 — keep the core small): eight node kinds, not twenty-eight, and even these ship as *optional* schemas (D-018) — strip them and every node degrades to titled prose (P9 rung L0/L1).

*Inclusion is provisional and falsifiable:* if real corpora show a kind is unused or that a "domain" type is actually universal, the vocabulary is revised (this is why vocabularies version — §7).

---

## 3. Edge-type semantics (D-020, D-022)

### 3.1 Edge properties beyond the binary (resolves C1)

A cross-reference edge is a **qualified statement**: `(source) —type→ (target)` plus properties that qualify it. N-ary and temporal facts are edges with qualifier properties, following Wikidata — no hyperedges in v1 (D-020):

- "Alice worked at Acme 2020–2023 as CTO" → edge `Alice —worked-at→ Acme` with `{from:2020, to:2023, role:CTO}`.
- "Bob cited Smith 2019, p.42" → edge `Bob-node —cites→ Smith2019` with `{page:42}`.

Temporal validity (a fact true only in an interval) is the qualifier pattern applied to time: any edge may carry `from`/`to`. The model records *when a claim holds*, composing with provenance's *when a claim was asserted* (D-019) — two different times, both representable.

### 3.2 Edge-type metadata

Each edge type declares semantic metadata (in its vocabulary schema), which the query layer (Stage 7) uses:

| Edge type | Family | Direction / inverse | Algebraic property | Typical endpoints |
|---|---|---|---|---|
| `contains` | containment | parent→child / `part-of`(effective) | acyclic (tree) | any → any |
| `transcludes` | crossref | source→target / — | acyclic (no cycles, §RS) | any → any |
| `relates-to` | crossref | symmetric / self | none | any ↔ any |
| `depends-on` | crossref | dependent→dependency / `enables` | transitive, acyclic | task/goal → task/goal |
| `blocks` | crossref | blocker→blocked / `blocked-by` | (inverse of enable-path) | task → task |
| `refines` | crossref | specific→general / `refined-by` | transitive, acyclic | any → any |
| `part-of` | crossref | part→whole / `has-part` | transitive, acyclic | any → any |
| `contradicts` | crossref | symmetric / self | non-transitive | claim ↔ claim |
| `supports` | crossref | evidence→claim / `supported-by` | non-transitive | source/claim → claim |
| `cites` | crossref | citing→source / `cited-by` | non-transitive | any → source |
| `answers` | crossref | answer→question / `answered-by` | non-transitive | any → question |
| `tag` | crossref | node→concept / `tagged-by` | (concept hierarchy via `part-of`) | any → concept |
| `owned-by` | crossref | node→agent / `owns` | non-transitive | any → agent |
| `supersedes` | crossref | new→old / `superseded-by` | acyclic | any → any (same kind) |
| `merged-into` / `split-from` | crossref | lineage (from D-016/§4 Stage 4) | acyclic | node → node |

### 3.3 The materialization rule (D-022)

**Transitive, inverse, and symmetric relations are declared as edge-type metadata and computed at query time — never stored as materialized edges.** If `A part-of B` and `B part-of C`, the model stores two edges; `A part-of C` is *derived on demand*, not written. Inverses (`owns` for `owned-by`) are likewise views, not stored twins.

Rationale: materializing entailments is precisely what polluted OWL graphs — inferred triples became indistinguishable from asserted ones and forced batch reloads ([TerminusDB](https://terminusdb.com/blog/the-semantic-web-is-dead/)). Keeping derivations query-time honors P10 (segregate asserted from derived) and P11 (state is a projection over stored facts), and keeps the file small and diff-stable (P14). Any derived edge that *is* persisted (for caching) carries `inferred` provenance (D-019) and is regenerable (P17 layer rules).

---

## 4. Property value types

Deliberately minimal (priority rule 4; avoid RDF's datatype ceremony, [semantic-web.md](../research/semantic-web.md)):

| Type | Notes |
|---|---|
| `text` | Unicode string (may itself contain inline content at L0) |
| `number` | integer or decimal; arbitrary precision permitted |
| `boolean` | true/false |
| `timestamp` | date or date-time, ISO-8601 semantics; the basis for chronological traversal |
| `duration` | length of time (for `event`, `task` estimates) |
| `quantity` | a `number` with an optional `unit` tag — the one concession to typed literals, so "5 kg" ≠ "5" without a datatype registry |
| `list<T>` | ordered, native (the thing RDF lacked, P7 / [Sporny](http://manu.sporny.org/2014/json-ld-origins-2/)) |
| `ref` | a node id (a property whose value is another node) |

There are **no nested object values.** If a value has internal structure, it is a node reached by a `ref` (or an edge). This keeps properties flat and pushes all structure into the node/edge graph, where it has identity and is queryable — a direct application of D-015 (everything worth structure is a node).

---

## 5. The schema language (D-023)

**Schemas are `.sarib` documents.** A schema is knowledge about knowledge, so it is expressed in the same model (self-hosting) — no second language to learn, and schemas are versionable, diffable, and projectable like any `.sarib` file.

A schema declares, as nodes of reserved structural kinds:

- **node-kind declarations** — name, allowed properties (each: value-type, cardinality `0..1 / 1 / 0..n / 1..n`, required?), allowed status values, optional canonical home (§ OQ3 fix).
- **edge-kind declarations** — name, source-type constraint, target-type constraint, cardinality, direction, inverse name, algebraic property (§3.2).
- **property declarations** — reusable named properties with value-types.

**Validation is closed-world and lint-grade** (P10/P15, D-008): against an *active* schema, an unknown type, a missing required property, a cardinality violation, or an endpoint-type mismatch is a **diagnostic** (warning), not a fatal error — the document still parses and renders (P15). Absent an active schema, anything goes (rung L0–L4 need no schema). There is no open-world inference: the checker validates what is stated; it never invents facts to satisfy a constraint (OWL's fatal choice, [semantic-web.md §3](../research/semantic-web.md)).

**The meta-schema** (the schema describing schemas) is itself a schema — the model is self-describing, which is how a frozen core (P16) supports unbounded vocabularies without core changes.

---

## 6. Reference resolution (resolves C3) — D-024

Given a name (or slug) referenced from a source node, resolution proceeds deterministically:

1. **Explicit identity.** If the reference carries an id or a unique slug, resolve to that node. Unambiguous; done.
2. **Nearest-in-containment.** Otherwise, search for a node whose name/slug matches, walking *up* the source's containment ancestors and their subtrees, nearest scope first. The closest single match wins.
3. **Document-global.** If no ancestor-scope match, search the whole document for a unique match.
4. **Vocabulary / imported.** If still unresolved, search active imported vocabularies/namespaces.
5. **Unresolved.** If none match, or if **any** step finds *multiple* equally-near matches, the reference is **unresolved**: it remains valid, renders as plain text, and emits a lint diagnostic (P15). The model **never silently guesses** among ambiguous targets — a wrong guess corrupts the graph invisibly (the failure D-024 exists to prevent).

Normalization: names are matched after Unicode NFC + case-folding + whitespace-collapse; slugs match exactly. Resolution is a pure function of (reference, document state, active vocabularies), so every conforming tool resolves identically (determinism, P14/P15).

This is the closed-world discipline (D-008) applied to linking: better an honest "unresolved, please disambiguate" than a confident wrong edge.

---

## 7. Vocabulary evolution (D-025)

- **The core never versions its constructs.** The node, the two edge families, the structural roles, the property value-types, and the resolution rule are frozen at v1 (P16 — JSON froze and won; YAML's versioned meaning-drift is the anti-pattern, [YAML from hell](https://ruudvanasseldonk.com/2023/01/11/the-yaml-document-from-hell)).
- **Vocabularies are semver-versioned.** A `.sarib` document pins the vocabulary + version it was written against (a document-level property). Within a major version, evolution is **additive only** — new kinds, new optional properties, new edge types. Removing a kind, changing a property's meaning, or tightening a constraint is a **major** bump → a new namespace, so old documents keep their meaning (P16).
- **Unknown vocabulary or version degrades gracefully** (P17/D-011): unknown kinds render as generic nodes, unknown properties round-trip untouched. A document written against `std@2` opened by a tool knowing only `std@1` loses no data — it just under-interprets the `@2` additions.
- **Deprecation, not deletion** (mirrors P12): a vocabulary marks a kind deprecated with a successor pointer; it is never silently removed.

---

## 8. New decisions

Full entries in `../decisions/decision-log.md`:

- **D-020** — Reclassify the brief's pseudo-types: `dependency`/`relationship` are edge types; `constraint`/`risk`/`priority` are properties; n-ary/temporal facts are edges with qualifier properties (no hyperedges in v1).
- **D-021** — Core standard vocabulary v0 = {`task`, `decision`, `question`, `goal`, `event`, `agent`, `source`, `concept`}, chosen by a 3-gate inclusion test; domain sets (`sarib-software`, `sarib-design`) are separate optional vocabularies.
- **D-022** — Transitive/inverse/symmetric relations are edge-type metadata computed at query time, never materialized as stored edges; any cached derivation carries `inferred` provenance.
- **D-023** — Schemas are self-hosted `.sarib`; validation is closed-world and lint-grade; a meta-schema makes the model self-describing.
- **D-024** — Reference resolution order: explicit → nearest-in-containment → document-global → vocabulary → unresolved+diagnostic; ambiguity never resolves to a guess.
- **D-025** — Core never versions; vocabularies are semver, pinned per document, additive-only within a major, degrade gracefully, deprecate-not-delete.

---

## 9. What Stage 6 (Traversal Model) must deliver

Stage 5 gave the graph meaning; Stage 6 gives it motion — the 13 traversals from the brief, shown to be queries over this model (Stage 1 C5):

1. **Traversal as query, formally.** Define each of the brief's 13 traversals (linear, tree, BFS, DFS, dependency, priority, semantic, chronological, tag, relationship, AI-selected, parallel, comparative) as a parameterized walk over (N, E_c ∪ E_x) using the edge metadata from §3.2.
2. **The linear-reading anchor.** Confirm linear reading = inorder walk of E_c (Stage 4 §6) and show every other traversal reuses the same node/edge set without restructuring (P1 — one store, many renderings).
3. **Traversal over derived relations.** How transitive/inverse relations (D-022) are traversed without materialization.
4. **Scoping and cost.** How a traversal bounds itself (subgraph, depth, filter) so an agent loads a minimal context (P14; length degradation, [ai-context.md](../research/ai-context.md)).
5. **Determinism of ordering.** Tie-breaking so a traversal yields identical results across tools (P14/P15).

Deferred still: query *language/surface* (Stage 7), operations (Stage 8), syntax (Stage 10).

## 10. Risks surfaced by this stage

Logged in the consolidated register (`../risks/risk-register.md`), which this session also establishes:

- **RM6 — vocabulary mis-cut.** The v0 eight (D-021) may be wrong — too few (users reach for a missing kind and overload `concept`) or too many (a kind goes unused). *Mitigation:* falsifiable inclusion test + additive vocab versioning (D-025); revisit after reference-implementation dogfooding.
- **RM7 — resolution ambiguity in practice.** Nearest-in-containment (D-024) may surprise users when the same name recurs across scopes. *Mitigation:* unresolved-not-guessed + lint diagnostics; measure real ambiguity rates on corpora.
- **RA5 — derived-relation query cost.** Computing transitive closures at query time (D-022) may be too slow on large graphs, tempting materialization (which reintroduces OWL's pollution). *Mitigation:* Stage 6 cost bounds + provenance-marked caches.
- **RG4 — vocabulary fragmentation.** Competing community vocabularies for the same domain could fork the ecosystem (Markdown-flavor risk at the vocabulary layer). *Mitigation:* a blessed standard library + namespacing + a registry (governance, Stage 13+).

This document is unratified until Stage 6 critiques it.

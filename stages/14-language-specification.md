# Stage 14 — .sarib Language Specification (v0.1 draft)

**Status:** Draft v0.1 — open for critique by Stage 15 · **Date:** 2026-07-15
**Input:** Stages 4–13; principles P1–P17; decisions D-001…D-057
**Decisions logged:** D-058 … D-059 (this stage)
**Phase:** E (Standardization), stage 2 of 3.
**What this is:** the consolidated, standalone specification — the model, semantics, serialization, operations, query, author grammar, validation, projection, and conformance in one document, written to be implementable from alone. Rationale for each choice lives in the referenced stage/decision; this document states *what conforms*, teach-by-example first (the JSON-LD/Swartz spec-readability lesson, Stage 2 §2.2), normative detail after.

---

## 0. Critique of Stage 13 (seams consolidation exposed)

Assembling the spec surfaced three gaps the architecture left implicit, now fixed here: **(a)** no file/versioning conventions were stated (extension, MIME type, version pin) — §9, D-058; **(b)** the actual sigils were never committed, pending tokenizer verification — §7 commits Candidate-A glyphs *provisionally* and marks the freeze-gate (RA11); **(c)** no explicit compatibility contract (what a v1 reader does with v2 content) — §9/§10, D-059. No principle reversed.

---

## 1. Overview — the model in one screen

A `.sarib` knowledge base is **one set of identified nodes connected by identified, typed edges** (a labeled property graph). Edges come in two families:

- **containment** edges form a single-parent, ordered **spanning tree** — walking it in order *is* the readable document;
- **cross-reference** edges (typed, property-bearing, incl. transclusion) overlay an arbitrary graph on the same nodes.

There is one graph; the document is the view you get by walking its containment spanning-tree in order (Stage 4). Everything else — outlines, boards, timelines, dependency graphs, an agent's context window — is a **projection** (a query + a template) over that one graph (Stage 12). Knowledge is **stored once, rendered infinitely** (P1); edits are **atomic operations addressed by id, never regenerations** (P11/D-002); **semantics are canonical, every syntax and view is a projection** (P2).

A `.sarib` file is valid at any of six progressive rungs (L0 prose → L5 schema-checked, Stage 4 §7 / principle P9); pure Markdown prose is valid L0. Humans write prose and light structure; agents enrich to graph; both read the same knowledge without translation (D-010).

---

## 2. Data model (normative; full rationale Stage 4)

**Node** — the atom of knowledge:
`Node = (id, type?, content, properties, status, provenance?)`. One node kind, progressively typed (D-015): a paragraph is an untyped node with content; an entity ("Alice") is a typed node with properties.

**Edge** — first-class and identified (D-017):
`Edge = (id, type?, family∈{containment,crossref}, source, target, order?, anchor?, properties, status, provenance?)`.

**Identity** (D-009/D-014): every node and edge has an opaque, durable, content-independent, position-independent id, assignable offline without coordination (`(replica,counter)`/ULID). Humans reference by name/slug; the system resolves name→id. Ids never appear in prose except as an optional human slug.

**The 10 invariants** (a structure is valid `.sarib` iff all hold — Stage 4 §11):
1 unique durable id per node/edge · 2 every non-root node has exactly one active containment parent (spanning tree) · 3 every edge's endpoints exist (edge to a retracted node is dormant, not dangling) · 4 no positional addressing anywhere · 5 siblings totally ordered · 6 unknown types parse, degrade, round-trip untouched · 7 provenance defaults to owner; inferred/imported distinguishable · 8 removal = retraction, not deletion · 9 session state never canonical; derived material provenance-marked · 10 serialization order is unique.

---

## 3. Semantics (normative; full rationale Stage 5)

**Core structural roles:** `document`, `section`/`container`, `prose`, `list`, `item` (about document shape, not domain).

**Standard vocabulary v0** (optional, namespaced `std:`) — eight node kinds by the 3-gate inclusion test (D-021): `task`, `decision`, `question`, `goal`, `event`, `agent`, `source`, `concept`. Domain vocabularies (`sarib-software`, `sarib-design`) are separate and optional. Everything else from common briefs is an edge type, a property, or a domain type (D-020).

**Edge semantics** (D-020/D-022): edges carry qualifier properties, so n-ary and time-qualified facts need no hyperedges (Wikidata model). Each edge type declares direction, inverse, and algebra (transitive/symmetric/acyclic); **transitive/inverse relations are computed at query time, never materialized** (D-022). Standard edges: `contains`, `transcludes`, `relates-to`, `depends-on`, `blocks`, `refines`, `part-of`, `contradicts`, `supports`, `cites`, `answers`, `tag`, `owned-by`, `supersedes`, `merged-into`/`split-from`.

**Property values:** text, number, boolean, timestamp, duration, quantity(number+unit), list<>, ref. No nested objects — structure becomes a node (D-015).

**Provenance & status** (D-019): implicit provenance = owner (never materialized); materialized only when non-default with class ∈ {asserted, inferred, imported}. Status ∈ {active, retracted}; retraction is a status assertion, not erasure (P12).

**Schemas** are self-hosted `.sarib` (D-023), checked closed-world; a meta-schema makes the model self-describing.

**Reference resolution** (D-024): explicit id/slug → nearest-in-containment → document-global → vocabulary → unresolved (valid, renders as text, diagnostic). Never a silent guess. Matching after NFC + case-fold + whitespace-collapse.

---

## 4. Serialization (normative; full rationale Stage 9)

**Three serializations of one model** (D-040): canonical form (integrity), op-log (edits/sync), author text (§7). All lossless inter-conversions.

**Canonical normal form** (D-041): line-oriented canonical JSON (RFC 8785 JCS rules) over the `.sarib`⇄JSON isomorphism — document-order nodes, deterministic edge/property ordering (D-029 cascade), canonical scalars, NFC strings, fixed field order. **Exactly one byte-string per state** → stable hash (sign/dedup) and minimal diffs simultaneously.

**File = canonical snapshot + append-only op-log** (D-042): read = load snapshot + fold suffix; the canonical *state* is content-addressed. Byte-level op-log↔state equivalence holds: `canon(fold(ops))` is a unique function of the op-set (Stage 9 §6).

**Load safety** (D-043): pure-data load (no code/directives); acyclic + depth/size-bounded transclusion; canonicalizer rejects ambiguous encodings; content is inert data, never instructions.

**Partial/streaming** (D-044): id-addressable records + a derived id→offset index; containment-order sections are contiguous ranges; locality guarantees streaming and bounded-subgraph loads.

---

## 5. Operations (normative; full rationale Stage 8)

`Op = (id, ts, kind, target(s), args, expect?, provenance?)` — transport-agnostic data, addressing targets **by id only** (D-036).

**8 primitives** (closed under the 10 invariants, D-035): `create-node`, `retract-node`, `set-content`, `set-property`, `unset-property`, `add-edge`, `retract-edge`, `move`. Containment edited only via create-node/move (protects single-home). **Composite macros** (atomic): `merge`, `split`, `promote`, `demote`. `tag`=add-edge, `reorder`=move. `compact` is the sole destructive op, explicit.

**Convergence** (D-037): additive=grow-set, retract=status flag, set-*/move=LWW-register (Lamport tie-break) → order-independent fold → Strong Eventual Consistency (server-free merge, CRDT-ready).

**Optimistic concurrency** (D-038): an op may carry `expect(version|field OP value)`; violated → rejected + re-query. Default unguarded = LWW converge.

---

## 6. Traversal & Query (normative; full rationale Stages 6–7)

**Traversal** is one parameterized walk over seven axes (D-026): start · edge-selector · direction · frontier-order · filter · bound · derivation. Cycle-safe by construction (visited-set, D-027); **always bounded** (max-depth/nodes/subgraph) → returns a subgraph + cursor (D-028); deterministic via the tie-break cascade (D-029). The brief's 13 traversals are presets; AI-selected/parallel/comparative are composition strategies.

**Query** is self-hosted (a query/view is a node, D-030) over those axes + a projection. **Filter** is a decidable, per-node-local boolean predicate algebra (D-031): type-in, has-tag, prop-compare/exists/contains, status, asserted-by-class, has-edge — combined by AND/OR/NOT; no arithmetic/functions/recursion; aggregation is a post-query transform. **Result** is a subgraph carrying stable ids + a caller projection, deterministic order, cursor, diagnostics (D-032). **Composition** (D-034): parallel=union, comparative=intersect/difference+align, AI-selected=runtime construction. **Query results are the sole addressing mechanism for operations** (D-033) — the read→reason→operate-by-id→re-query loop.

---

## 7. Author syntax (normative surface = Candidate A; full rationale Stage 10)

A CommonMark superset (D-045): a `.sarib` file renders acceptably in any Markdown renderer; unknown marks degrade to literal text. Discipline from djot (unambiguous, local, no-backtracking); surface from Pandoc/MyST/Dataview.

**Conventions** (D-046) — *glyphs verified token-cheap on GPT-family encodings (o200k/cl100k/r50k), 2026-07-19, `bench/tokenizer-report.md`; open-weight re-run pending before freeze (RA11/G8)*:

| Construct | Surface | Model |
|---|---|---|
| containment | heading level / list nesting | containment edge (ordered) |
| node type | trailing `{.type}` | node.type |
| slug | trailing `{#slug}` | human slug |
| block id | trailing `^id` | node id (tooling-assigned) |
| property | `key:: value` (line) or `[key:: value]` (inline) | property |
| typed edge | `[rel:: [[Target]]]` inline | crossref edge (source=containing node) |
| plain link | `[[Target]]` | `relates-to` edge |
| importance | `priority:: high` (a field, D-048) | property (not typography) |
| file metadata | YAML front matter `--- … ---` | document properties (vocab pin, schema) |
| emphasis | `*`/`_`/`**` | presentation only (human scan) |

**Business-card grammar** (Tier-0, EBNF sketch — the S6 centerpiece; full grammar frozen only after tokenizer verification):

```
document    = frontmatter? , block* ;
frontmatter = "---" NL , yaml , "---" NL ;
block       = heading | listitem | fenced | fieldline | paragraph ;
heading     = "#"+ , SP , inline+ , attrs? , blockid? , NL ;
listitem    = indent , ("-"|"*"|ordinal) , SP , inline+ , attrs? , blockid? , NL ;
fenced      = "```" , any* , "```" ;                 (* opaque/code — passthrough *)
fieldline   = key , "::" , SP , value , NL ;         (* property of enclosing node *)
paragraph   = inline+ , (NL , inline+)* , NL ;       (* → L0 prose node *)
attrs       = "{" , (typeMark | idMark | kv)+ , "}" ;
typeMark    = "." , name ;  idMark = "#" , name ;  kv = key , "=" , val ;
blockid     = "^" , idchars ;
inline      = text | typedlink | wikilink | emph | codespan ;
typedlink   = "[" , rel , "::" , SP , wikilink , "]" ;
wikilink    = "[[" , name , ("#" , anchor)? , "]]" ;
emph        = "*" inline "*" | "_" inline "_" | "**" inline "**" ;
```

Anything unrecognized → the content of an L0 prose node (Tier-0 total parse, D-049). Parsing is local/no-backtracking. Candidate B (outline-dense) is a documented alternative surface / future compact profile, not the normative grammar.

---

## 8. Validation (normative; full rationale Stage 11)

Three tiers (D-049): **Tier 0** well-formed (total; unrecognized → L0; near-unfailable), **Tier 1** structurally valid (the 10 invariants), **Tier 2** schema-valid (active vocabulary). Only un-parseability blocks; the forgiving surface precludes it. All else is **located, non-fatal diagnostics** carrying node/edge ids: unresolved/ambiguous reference, duplicate slug, dangling/retracted endpoint, cycle-in-acyclic-edge, unknown type/property, cardinality/endpoint-type violation, structure-read-as-prose. Validation is self-hosted and closed-world; diagnostics are deterministic and queryable (D-050). Fidelity: normalization is idempotent to the canonical form; model round-trip is lossless; derived cues are read-transparent (D-051).

---

## 9. Projection, files, versioning (normative; Stages 12 + D-058/D-059)

**Projection** (D-052): a view = query (subgraph+order) + template (element→presentation), every element carrying its id. Views are **live windows** (edits → id-addressed ops) or **terminal exports** (read-only, self-declared) — never the ambiguous middle (D-053). Derived spatial cues (skeleton/TOC, `[k/n]` counts, subtree size, ordinal, fold markers, summaries) are computed per view, never authored (D-054).

**File conventions** (D-058): extension `.sarib`; media type `text/sarib` (provisional registration target); UTF-8, NFC; the file declares its `sarib` core version and pinned `vocab@version` in front matter.

**Compatibility contract** (D-059): the **core is frozen** at v1 — a document's meaning never changes under a later core revision. **Vocabularies are semver, additive-only within a major** (D-025). A reader encountering an unknown core minor or unknown vocabulary version **degrades gracefully** (unknown types → generic nodes, unknown properties round-trip untouched — P17/D-011); it never fails and never silently reinterprets (the YAML 1.1→1.2 anti-pattern). Deprecate-not-delete (mirrors P12).

---

## 10. Conformance (normative)

A **conforming reader** parses any input to a model (Tier 0 total), preserves unknown constructs byte-faithfully (invariant 6), and resolves references per D-024.
A **conforming writer** emits the canonical form (D-041) and idempotent normalization (D-051).
A **conforming validator** performs the three tiers (§8) with located diagnostics.
A **conforming editor/agent** addresses edits by id via operations (§5), honoring preconditions (D-038) and the invariants (never emitting an op that would break one).
A **conforming projector** renders (query, template) views carrying ids, declaring live vs terminal (D-053).

**The operational definition of "conforming" is the conformance corpus** (Stage 13 §6): `input → expected(model, canonical form, diagnostics)` — not any reference implementation (RM22). Conformance levels: **L-Read** (reader+validator), **L-Edit** (+op engine), **L-Project** (+projector), **L-Full** (all + canonical writer). v1.0 requires L-Full for the reference implementation and at least L-Read for third-party tools to claim `.sarib` support.

---

## 11. New decisions

- **D-058** — File conventions: extension `.sarib`, media type `text/sarib` (provisional), UTF-8/NFC, core-version + `vocab@version` declared in front matter.
- **D-059** — Compatibility contract: frozen core (meaning stable across core revisions); vocabularies semver additive-only within a major; unknown core-minor/vocabulary degrades gracefully, never fails, never silently reinterprets; deprecate-not-delete.

## 12. What Stage 15 (v1.0 Proposal) must deliver

The v1.0 scope line (what's in / deferred), the conformance-and-benchmark gate to freeze, governance (who extends the standard, how — RG1), the adoption path (MCP/CLI consumer, Markdown-superset carrier), the success-criteria retrospective (S1–S8), and the project close-out (reconcile README/charter/register/decision-log; state what remains). Then the project has reached a defensible v1.0 proposal — the objective set in the brief.

## 13. Risks surfaced

- **RG2/RM22 (mitigation):** the conformance corpus as the definition of conforming (§10) is the concrete defense against parser divergence and reference-code-as-spec.
- **RA11 (open, gated):** §7 glyphs are provisional; the grammar is frozen only after tokenizer verification — the freeze gate (Stage 15).

This document is unratified until Stage 15 critiques it.

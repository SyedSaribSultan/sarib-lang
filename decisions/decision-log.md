# Decision Log

Numbered, append-only. Each entry: context → options → choice → reversal condition. Reversals get a new entry referencing the old one; nothing is deleted.

---

## D-001 · Specify .sarib as a five-layer stack
**Date:** 2026-07-14 · **Stage:** 1 · **Status:** Provisional

**Context:** The brief asks for "a language" but describes substrate, data model, semantics, operations, and syntax at once (Stage 1, C1).
**Options:** (a) single monolithic language spec; (b) layered stack, specified model-first.
**Choice:** (b). Lower layers freeze earlier; syntax is the last layer decided.
**Reversal condition:** Stage 2 produces evidence that layer separation caused prior-format failures (rather than preventing them).

## D-002 · Optimize tokens-per-interaction, not tokens-per-byte
**Date:** 2026-07-14 · **Stage:** 1 · **Status:** Provisional

**Context:** Brief lists "tokenizer efficient" as a goal. Tokenizers change; syntax terseness saves tens of percent while atomic ops + subgraph retrieval save orders of magnitude (Stage 1, C2).
**Options:** (a) terse syntax as primary goal; (b) interaction efficiency primary, density as tiebreaker.
**Choice:** (b).
**Reversal condition:** Rule-6 benchmarks show syntax overhead dominates real agent workloads.

## D-003 · Write loose, store canonical
**Date:** 2026-07-14 · **Stage:** 1 · **Status:** Provisional

**Context:** "Human writable" and "deterministic" conflict on a single surface (Stage 1, C4).
**Options:** (a) one forgiving syntax (HTML path); (b) one strict syntax (XML path); (c) forgiving authoring dialect + strict canonical normal form (gofmt path).
**Choice:** (c). Humans write the dialect; tools normalize; agents edit via ops.
**Reversal condition:** The dialect/canonical split confuses users or fragments the ecosystem in practice.

## D-004 · History belongs to the substrate; diffability belongs to the format
**Date:** 2026-07-14 · **Stage:** 1 · **Status:** Provisional

**Context:** Brief lists "version history" as a language feature; git already exists (Stage 1, C3).
**Options:** (a) embed history in-file; (b) delegate history to git/tools, design the format for stable IDs, normalized ordering, line-oriented diffs, and define the op vocabulary as the unit of change.
**Choice:** (b).
**Reversal condition:** Op-log interchange requirements (multi-agent sync) exceed what external substrates can carry.

## D-005 · Identity, concurrency, provenance, adoption are first-class pillars
**Date:** 2026-07-14 · **Stage:** 1 · **Status:** Provisional

**Context:** Four hard problems unnamed in the brief predict success or failure (Stage 1, C6).
**Choice:** Added to the requirement set; each gets dedicated research (RQ1, RQ6, RQ8) and model-level treatment (Stages 4–5, 8).
**Reversal condition:** N/A (scope decision; individual pillars may be descoped with logged rationale).

---

## D-006 · Surface is a Markdown superset
**Date:** 2026-07-14 · **Stage:** 2 · **Status:** Provisional

**Context:** Every winning format had a carrier that pre-installed its parser; elegant formats without one (S-expressions, org-mode) stalled for decades (Stage 2, §2.2). `.sarib`'s carrier is the LLM+agent stack + existing Markdown renderers.
**Choice:** A `.sarib` file must render acceptably as Markdown in a standard CommonMark renderer; the format is a Markdown superset, not a novel grammar. Incremental adoption one file/block at a time.
**Reversal condition:** Markdown-superset constraints prove to block a required model feature that no extension mechanism can carry.
**Evidence:** [twobithistory/JSON](https://twobithistory.org/2017/09/21/the-rise-and-rise-of-json.html), [RFC 9804 / S-expr 28-yr lag](https://www.rfc-editor.org/rfc/rfc9804.pdf), [AGENTS.md vs llms.txt](https://www.infoq.com/news/2025/08/agents-md/).

## D-007 · Labeled property-graph model; reject RDF/triples lineage
**Date:** 2026-07-14 · **Stage:** 2 · **Status:** Provisional

**Context:** RDF lacks native lists and edge properties; reification quadruples dataset size; JSON-LD/Turtle scored worst for LLMs on accuracy and token cost. Property graphs (Cypher/GQL) match how people whiteboard and put properties directly on edges (Stage 2, §2.1, §2.4, §3).
**Options:** (a) RDF triples + profile; (b) labeled property graph; (c) custom.
**Choice:** (b) — nodes + typed edges carrying properties; native lists; no IRI ceremony.
**Reversal condition:** A property-graph model proves unable to express a required knowledge pattern that triples handle natively.
**Evidence:** [Sporny](http://manu.sporny.org/2014/json-ld-origins-2/), [KG-LLM-Bench](https://arxiv.org/abs/2504.07087), [Cypher origin](https://www.thobe.org/work/cypher/), [RDF-star motivation](https://www.ontotext.com/knowledgehub/fundamentals/what-is-rdf-star/).

## D-008 · Closed-world validation; segregated inference; claims-not-truth
**Date:** 2026-07-14 · **Stage:** 2 · **Status:** Provisional

**Context:** OWL's open-world + no-unique-names assumption made basic error-checking impossible; industry fled to SHACL. Doctorow's "metacrap" objections (people lie, err, disagree) sank one-true-metadata; Wikidata's plurality model (referenced claims with ranks) survived (Stage 2, §2.1).
**Choice:** Validate documents like a type system (closed-world, unique names). Keep derived/inferred facts visibly separate from asserted facts. Model stores attributable claims with provenance, not adjudicated truth.
**Reversal condition:** Single-author use shows provenance/claim overhead outweighs its value (would narrow, not remove).
**Evidence:** [TerminusDB](https://terminusdb.com/blog/the-semantic-web-is-dead/), [Metacrap](https://people.well.com/user/doctorow/metacrap.htm), [Wikidata CACM](https://iccl.inf.tu-dresden.de/w/images/8/89/Wikidata-CACM-2014.pdf).

## D-009 · Round-trip law: identity + single-owner-per-state-class
**Date:** 2026-07-14 · **Stage:** 2 · **Status:** Provisional

**Context:** Across every single-source-many-views system, round-trip held iff projections carried stable identity AND each class of state had one authoritative owner; Jupyter broke from conflating input/output/env state despite identity-ish matching (Stage 2, §2.3).
**Choice:** Every atom gets a stable, position-independent, collision-proof ID that all projections carry. Projections are windows that may hide but never silently drop fields. Content / derived-cache / session state are separate layers, one writer each.
**Reversal condition:** None foreseen; this is the empirically strongest finding in the corpus.
**Evidence:** [Portable Text](https://www.portabletext.org/specification/), [Notion data model](https://www.notion.com/blog/data-model-behind-notion), [fast.ai Jupyter+git](https://www.fast.ai/posts/2022-08-25-jupyter-git.html), [Pandoc manual](https://pandoc.org/MANUAL.html).

## D-010 · Division of labor — humans write prose, agents enrich to graph
**Date:** 2026-07-14 · **Stage:** 2 · **Status:** Provisional · **Challenges the brief**

**Context:** 20 years of evidence show humans do not hand-author structured knowledge inline, even sympathetic experts — Wikidata's form-based input displaced in-text annotation; RDF authoring never materialized (Stage 2, §1). This challenges the brief's assumption that humans write the graph.
**Choice:** "Human-writable" is satisfied by the surface being prose with *optional* light structure; the graph is mostly agent-produced and human-confirmed. LLMs make this viable now precisely because the structuring labor can move to the agent — though extraction cost/reliability (RQ7) must be respected by favoring incremental write-time structuring over bulk extraction.
**Reversal condition:** Evidence that target users will and do hand-author dense structure inline (would restore symmetric authoring).
**Evidence:** [Wikidata Making Of](https://iccl.inf.tu-dresden.de/w/images/9/9d/Vrandecic-Pintscher-Kroetzsch_Wikidata-History-WWW-2023.pdf), [Norvig↔Berners-Lee](https://grandtextauto.soe.ucsc.edu/2006/07/18/googles-norvig-questions-berners-lee-on-the-semantic-web/), [LazyGraphRAG](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/).

## D-011 · One in-core extension mechanism with graceful degradation
**Date:** 2026-07-14 · **Stage:** 2 · **Status:** Provisional

**Context:** Markdown's single deepest defect — no attribute/extension syntax — forced every platform to fork (GFM, MMD, Extra…); reST's directives show extension-without-forking works (Stage 2, §2.2, T6).
**Choice:** One blessed in-core attribute/extension mechanism. Unknown constructs must parse, render generically, and round-trip untouched. Core grammar frozen; extensions self-announcing and versioned separately.
**Reversal condition:** A generic extension slot proves to enable ambiguity that breaks deterministic parsing.
**Evidence:** [Beyond Markdown / MacFarlane](https://johnmacfarlane.net/beyond-markdown.html), [PEP 287 reST directives](https://peps.python.org/pep-0287/), [YAML versioning hazard](https://ruudvanasseldonk.com/2023/01/11/the-yaml-document-from-hell).

---

## D-012 · Edges emerge from prose; inline typed links are the primary edge mechanism
**Date:** 2026-07-15 · **Stage:** 3 · **Status:** Provisional

**Context:** Every graph-as-text syntax forces a standalone statement naming both endpoints + relation (edge-writing ceremony), which kept Turtle/Cypher/DOT/GraphML in query/viz/config niches; none became a thinking medium (Stage 2 §7, `research/graphs-and-databases.md`). In prose, "Alice knows Bob" *is* the edge.
**Options:** (a) block-form edge/triple lists as primary; (b) inline typed links inside sentences as primary, blocks as fallback.
**Choice:** (b). The primary edge-authoring act is an inline typed link within a natural sentence; block-form edge lists remain for cases prose can't carry but are not privileged.
**Reversal condition:** User testing shows inline link syntax disrupts prose more than block-form edge lists do.
**Evidence:** [graphs-and-databases.md §7](../research/graphs-and-databases.md), [W3C Turtle](https://www.w3.org/TR/turtle/), [openCypher](https://opencypher.org/), [Mermaid/GitHub](https://github.blog/developer-skills/github/include-diagrams-markdown-files-mermaid/).

## D-013 · Containment is a zero-ceremony implicit edge; model distinguishes containment from cross-reference
**Date:** 2026-07-15 · **Stage:** 3 · **Status:** Provisional — **partly superseded by D-016** (multi-parent claim only)

**Context:** Every hand-authored-at-scale text structure (Markdown, KDL, outliners, filesystems) is a tree because containment needs no naming; arbitrary typed edges must each be written out (`research/graphs-and-databases.md` §5, [KDL](https://kdl.dev/)).
**Choice:** Document hierarchy (headings, lists, nesting) compiles to zero-ceremony **containment edges**; the model distinguishes containment edges from **cross-reference edges**. ~~Containment is a DAG (multiple parents allowed), not a strict tree.~~ → **Amended by D-016 (Stage 4):** storage containment is a *single-parent, ordered spanning tree* (one home per node); multi-parent structure is delivered by transclusion (a cross-reference edge), not by multiple containment homes. The containment/cross-reference distinction itself stands.
**Reversal condition:** The containment/cross-reference distinction proves to confuse authors or complicate the model without payoff.
**Evidence:** [KDL](https://kdl.dev/), [graphs-and-databases.md §5](../research/graphs-and-databases.md).

## D-014 · Operations name identified elements, never positions; op set designed for commutativity; retraction not deletion
**Date:** 2026-07-15 · **Stage:** 3 · **Status:** Provisional · **Ratifies T7**

**Context:** Mergeability requires identified elements + commutative ops. JSON Patch's positional array addressing corrupts under concurrency; Automerge/Yjs `(replica, counter)` IDs merge server-free; CRDT beats OT for owned/offline files; event sourcing + Datomic converge on ops-canonical/state-as-projection and retract-not-destroy (`research/versioning-and-merge.md`).
**Choice:** Every edit operation references node/edge IDs (per D-009), never line/array positions. Prefer difference-form/commutative ops. Deletion is a status assertion (retraction), not erasure. v1 targets clean git 3-way merges on stable IDs + normal form; op vocabulary is CRDT-ready without model changes.
**Reversal condition:** Multi-agent concurrency requirements force a live CRDT store as canonical truth in v1 (file demotes to journal/snapshot — still specified).
**Evidence:** [RFC 6902 JSON Patch](https://www.rfc-editor.org/rfc/rfc6902), [Yjs INTERNALS](https://raw.githubusercontent.com/yjs/yjs/main/INTERNALS.md), [Seph Gentle OT→CRDT](https://josephg.com/blog/crdts-are-the-future/), [Fowler event sourcing](https://martinfowler.com/eaaDev/EventSourcing.html), [Datomic](https://docs.datomic.com/transactions/model.html).

---

## Ratification note (Stage 3, 2026-07-15)
Stage 3 ratifies D-001 … D-011 as binding principles (see `stages/03-design-principles.md` §3). No decision was reversed. T1 was revised (humans author prose, not graph structure — labor relocated to the agent) and remains ratified in its revised form. Priority ordering for principle conflicts: **integrity > human writability > machine efficiency > expressive completeness** (Stage 3 §4).

---

## D-015 · One node type, progressively typed
**Date:** 2026-07-15 · **Stage:** 4 · **Status:** Provisional

**Context:** The prose tree and the property graph must be one structure (Stage 3 C1). If prose blocks and semantic entities were different kinds of object, they would need constant reconciliation (the trap in `research/tools-for-thought.md`).
**Choice:** A paragraph and an entity ("Alice") are the same object — a node = (id, optional type, content, properties, status, provenance). Prose is an untyped node with content; an entity is a typed node with properties. Proven at scale by Notion's "everything is a block."
**Reversal condition:** Modeling entities and prose uniformly forces one to carry cost or ceremony that a split model would avoid.
**Evidence:** [Notion data model](https://www.notion.com/blog/data-model-behind-notion), [Portable Text](https://www.portabletext.org/specification/).

## D-016 · Storage containment is a single-parent spanning tree; multi-parent via transclusion (amends D-013)
**Date:** 2026-07-15 · **Stage:** 4 · **Status:** Provisional · **Amends D-013**

**Context:** D-013 said "containment is a DAG (multiple parents)." Stage 4 (CR1) found a multi-home node would appear twice in document order, breaking unique serialization (P6) and single-owner (P17).
**Choice:** Storage containment is a rooted, ordered, single-parent **spanning tree** (each node has exactly one home). Multi-parent/appears-in-many-places structure is delivered by **transclusion** — a cross-reference edge (`transcludes`), not a second home. The document is the containment tree walked in order; edits through a transclusion flow to the one home (edit-consistent by construction).
**Reversal condition:** A use case requires genuinely multiple equal homes that transclusion cannot model acceptably.
**Evidence:** Notion synced blocks / Roam embeds ([tools-for-thought.md](../research/tools-for-thought.md)); single-owner ([fast.ai Jupyter+git](https://www.fast.ai/posts/2022-08-25-jupyter-git.html)).

## D-017 · Edges are first-class, identified objects
**Date:** 2026-07-15 · **Stage:** 4 · **Status:** Provisional

**Context:** A relationship must be able to carry metadata (edge properties) and be addressed by operations and provenance. RDF's lack of this forced 4–5-triple reification (`research/semantic-web.md` §2).
**Choice:** An edge = (id, type, family, source, target, order?, anchor?, properties, status, provenance). Edges have identity and properties like nodes — the labeled-property-graph advantage (D-007).
**Reversal condition:** First-class edge identity proves to cost more than the reification it avoids.
**Evidence:** [RDF-star motivation / edge properties](https://www.ontotext.com/knowledgehub/fundamentals/what-is-rdf-star/), [Cypher/property graphs](https://www.thobe.org/work/cypher/).

## D-018 · Thin core; all semantic types are optional namespaced vocabulary
**Date:** 2026-07-15 · **Stage:** 4 · **Status:** Provisional

**Context:** Stage 3 (priority rule 4) demands cutting the brief's 28 node kinds; Stage 4 CR3 gives the rule. schema.org succeeded as vocabulary over a generic model; Wikidata types are community-defined, not in the data model (`research/semantic-web.md`).
**Choice:** The core defines only one node, two edge families, a few structural roles (`document`/`section`/`prose`/`list`/`item`), and the extension mechanism. Every semantic type (`task`, `person`, `decision`, `api`, `motion`, …) is a schema in an optional standard library, namespaced. Unknown types parse, degrade, and round-trip untouched.
**Reversal condition:** A semantic type proves so universal it must be core to keep the model coherent.
**Evidence:** [schema.org datamodel](http://schema.org/docs/datamodel.html), [semantic-web.md](../research/semantic-web.md), [Beyond Markdown extension gap](https://johnmacfarlane.net/beyond-markdown.html).

## D-019 · Sparse, owner-defaulted provenance; assertion class + status enums
**Date:** 2026-07-15 · **Stage:** 4 · **Status:** Provisional

**Context:** P10 requires attributable claims and segregated inference, but attaching provenance to every assertion drowns the single-author case (Stage 3 C3-class concern).
**Choice:** Implicit provenance = "asserted by file owner," never materialized. Provenance materializes only when non-default (agent `inferred`, external `imported`, other author, stated basis). Assertion class ∈ {asserted, inferred, imported}; status ∈ {active, retracted}, retraction not erasure.
**Reversal condition:** Sparse provenance proves ambiguous in multi-agent use, forcing explicit provenance everywhere.
**Evidence:** [Wikidata plurality (CACM)](https://iccl.inf.tu-dresden.de/w/images/8/89/Wikidata-CACM-2014.pdf), [Datomic retraction](https://docs.datomic.com/transactions/model.html), [OWL inference pollution](https://terminusdb.com/blog/the-semantic-web-is-dead/).

---

## D-020 · Reclassify the brief's pseudo-types
**Date:** 2026-07-15 · **Stage:** 5 · **Status:** Provisional

**Context:** Several brief "node types" are category errors (Stage 5 C2): `dependency`/`relationship` are relationships; `constraint`/`risk`/`priority` are attributes. And binary edges can't hold n-ary/temporal facts unless edges carry qualifiers.
**Choice:** `dependency`/`relationship` → edge types; `constraint`/`risk`/`priority` → properties; n-ary and time-qualified facts → edges with qualifier properties (Wikidata model), so no hyperedges in v1.
**Reversal condition:** A required fact pattern genuinely needs true hyperedges (>2 endpoints) that qualifiers can't model.
**Evidence:** [Wikidata CACM](https://iccl.inf.tu-dresden.de/w/images/8/89/Wikidata-CACM-2014.pdf).

## D-021 · Core standard vocabulary v0 (eight kinds) + inclusion test
**Date:** 2026-07-15 · **Stage:** 5 · **Status:** Provisional

**Context:** Priority rule 4 demands an aggressive cut of the brief's 28 kinds; a rule was missing (Stage 5 §2.1).
**Choice:** Core vocab v0 = {`task`, `decision`, `question`, `goal`, `event`, `agent`, `source`, `concept`}, admitted only if domain-agnostic AND behavior-changing AND irreducible. Domain sets (`sarib-software`, `sarib-design`) are separate optional vocabularies. All ship as optional schemas (per D-018).
**Reversal condition:** Dogfooding shows a kind unused or a "domain" type universal → revise via vocab versioning.
**Evidence:** [schema.org datamodel](http://schema.org/docs/datamodel.html), [semantic-web.md](../research/semantic-web.md).

## D-022 · Transitive/inverse/symmetric relations are query-time, never materialized
**Date:** 2026-07-15 · **Stage:** 5 · **Status:** Provisional

**Context:** Materializing entailments polluted OWL graphs (inferred indistinguishable from asserted) (`research/semantic-web.md` §3).
**Choice:** Declare algebraic properties (transitive/inverse/symmetric) as edge-type metadata; compute closures/inverses at query time (Stage 7). Any persisted derivation carries `inferred` provenance (D-019) and is regenerable.
**Reversal condition:** Query-time derivation is too slow at scale and caching with provenance proves insufficient (RA5).
**Evidence:** [TerminusDB / OWL inference pollution](https://terminusdb.com/blog/the-semantic-web-is-dead/).

## D-023 · Schemas are self-hosted .sarib; validation closed-world + lint-grade
**Date:** 2026-07-15 · **Stage:** 5 · **Status:** Provisional

**Context:** A schema is knowledge about knowledge; a second schema language would add ceremony and a learning tax.
**Choice:** Schemas are `.sarib` documents (self-hosting), with a self-describing meta-schema. Validation is closed-world (unknown-vs-active-schema = diagnostic, no open-world inference) and lint-grade (non-fatal, P15).
**Reversal condition:** Self-hosting proves too weak to express needed constraints, forcing a dedicated schema language.
**Evidence:** [semantic-web.md §3 (OWL open-world failure)](../research/semantic-web.md), P10/P15/D-008.

## D-024 · Deterministic reference resolution; ambiguity never guesses
**Date:** 2026-07-15 · **Stage:** 5 · **Status:** Provisional

**Context:** Stage 4 only sketched name→id resolution (Stage 5 C3); non-determinism forks the graph silently.
**Choice:** Resolution order — explicit id/slug → nearest-in-containment → document-global → vocabulary → unresolved. Multiple equally-near matches or none → unresolved (valid, renders as text, lint diagnostic). Never a silent guess. Matching after NFC + case-fold + whitespace-collapse; slugs exact. Pure function of (ref, document, active vocabs).
**Reversal condition:** Nearest-in-containment proves counter-intuitive in testing → revise the order (not the never-guess rule).
**Evidence:** closed-world discipline (D-008); [versioning-and-merge.md §2 (identity/tolerance)](../research/versioning-and-merge.md).

## D-025 · Core never versions; vocabularies are semver, pinned, additive-only
**Date:** 2026-07-15 · **Stage:** 5 · **Status:** Provisional

**Context:** YAML's versioned meaning-drift (1.1 vs 1.2) is the anti-pattern; JSON froze and won (`research/standards-adoption.md`).
**Choice:** Core constructs frozen at v1. Vocabularies semver-versioned, pinned per document; additive-only within a major (new kinds/optional props/edges); breaking changes → new namespace. Unknown vocab/version degrades gracefully (P17). Deprecate-not-delete (mirrors P12).
**Reversal condition:** Additive-only proves impossible for a needed correction that isn't a clean major bump.
**Evidence:** [YAML from hell](https://ruudvanasseldonk.com/2023/01/11/the-yaml-document-from-hell), P16/D-011.

---

## D-026 · Traversal is one parameterized walk; 13 traversals reduce to presets + strategies
**Date:** 2026-07-15 · **Stage:** 6 · **Status:** Provisional

**Context:** The brief lists 13 traversals; treating them as 13 features would bloat the model (Stage 6 C3). They are combinations of orthogonal axes over one graph.
**Choice:** Traversal is one primitive parameterized on seven axes — start · edge-selector · direction · frontier-order · filter · bound · derivation. 10 of the brief's 13 are presets; 3 (AI-selected, parallel, comparative) are composition strategies that drive the walk. Priority/chronological are the degenerate "no-edge" case (ordered selection of a set).
**Reversal condition:** A required traversal cannot be expressed as a setting of the seven axes.
**Evidence:** Stage 1 C5 (traversals = queries); discharges the brief's "Most Important Requirement."

## D-027 · Traversal is cycle-safe by construction; "acyclic" is a lint expectation
**Date:** 2026-07-15 · **Stage:** 6 · **Status:** Provisional

**Context:** Stage 5 marked edge types acyclic but nothing prevents an asserted cycle; a walk that assumes acyclicity loops/crashes (Stage 6 C1).
**Choice:** Every walk keeps a visited-set keyed by node id and emits each node once; this holds regardless of declared edge algebra. A real cycle yields a finite walk + a `cycle-detected` diagnostic. "Acyclic" is a validation expectation (lint), never a traversal precondition.
**Reversal condition:** None foreseen; unconditional cycle-safety is required for robustness.
**Evidence:** general graph-traversal safety; composes with invariants (Stage 4 §11).

## D-028 · Every traversal is bounded; results are subgraph + continuation cursor
**Date:** 2026-07-15 · **Stage:** 6 · **Status:** Provisional

**Context:** Query-time derivation (D-022) and large graphs make unbounded traversal unsafe; agents need minimal context (Stage 6 C2; register RA5/RM11).
**Choice:** A traversal spec always carries a bound (max-depth / max-nodes / subgraph boundary); the standard interface has no unbounded traversal. Results are a bounded subgraph plus an optional cursor to resume. Cost is proportional to result, not graph size.
**Reversal condition:** A required use case cannot be served by bounded+cursor paging.
**Evidence:** [ai-context.md (context economics, length degradation)](../research/ai-context.md); P14.

## D-029 · Traversal is a pure function of (graph, spec) via a total tie-break cascade
**Date:** 2026-07-15 · **Stage:** 6 · **Status:** Provisional

**Context:** Non-deterministic traversal order would make results irreproducible across tools and unsafe to cache (Stage 6 §7).
**Choice:** Wherever the graph offers a choice of next edge, break ties by: containment `order` → cross-ref (edge-type name → target canonical id → edge id) → property sort key with node-id tie-break → visit-once by node id. Total because ids are totally orderable (D-014). Traversal output is reproducible across conforming engines.
**Reversal condition:** A needed traversal semantics is inherently order-dependent in a way the cascade can't make total.
**Evidence:** P14/P15 (determinism, cache-safety); D-014 (orderable ids).

---

## D-030 · Queries are self-hosted (a query/view is a node)
**Date:** 2026-07-15 · **Stage:** 7 · **Status:** Provisional

**Context:** A saved view is durable, shareable knowledge; inventing a separate query-object language duplicates the model (Stage 7 §2). Consistent with D-015 (everything is a node) and D-023 (schemas self-hosted).
**Choice:** A query is a node of kind `query`/`view` whose properties specify the seven traversal axes (D-026) plus a projection. Saved views are first-class knowledge (addressable, versionable, composable). Query *syntax* is deferred to Phase D.
**Reversal condition:** Self-hosting queries proves too clumsy vs. a dedicated query representation.
**Evidence:** D-015, D-023; P1.

## D-031 · Filter axis is a decidable, per-node-local boolean predicate algebra
**Date:** 2026-07-15 · **Stage:** 7 · **Status:** Provisional

**Context:** The filter axis is the project's most dangerous underspecification — too rich = embedded programming language; too poor = can't ask real questions (Stage 7 C1).
**Choice:** Atomic predicates: type-in, has-tag, prop compare (=,≠,<,≤,>,≥), prop exists/contains, status, asserted-by class, has-edge — combined by AND/OR/NOT. Excluded: arithmetic, user functions, recursion, arbitrary joins. Aggregation (count/group) is a separate post-query result transform. Test: every predicate answerable per-node-locally with no unbounded computation.
**Reversal condition:** A common, legitimate query provably can't be expressed and isn't reasonably the agent's job (RM16).
**Evidence:** priority rule 4 (Stage 3 §4); bounded cost composes with D-028.

## D-032 · A query returns a result subgraph carrying stable ids + projection
**Date:** 2026-07-15 · **Stage:** 7 · **Status:** Provisional

**Context:** Stage 6 said "returns a bounded subgraph" without a shape; the shape is the read/write bridge and the token-budget dial (Stage 7 C2).
**Choice:** Result = matched nodes+edges, each carrying its stable id and a caller-specified projection (default: id+type+name+snippet; expandable), in deterministic order (D-029), with an optional continuation cursor (D-028) and diagnostics. Retracted excluded unless queried; derived marked `inferred`.
**Reversal condition:** The subgraph result shape proves insufficient for a required read pattern.
**Evidence:** P8 (ids), P14 ([ai-context.md](../research/ai-context.md) context economy), D-019/D-022.

## D-033 · Query results are the sole addressing mechanism for operations (read/write bridge)
**Date:** 2026-07-15 · **Stage:** 7 · **Status:** Provisional

**Context:** The token-efficiency thesis (D-002) requires editing by address, not regeneration; edits must target stable ids, never positions (P13).
**Choice:** Operations (Stage 8) target node/edge ids surfaced by query results. The agent loop is query→reason→operate(by id)→re-query. Positions are never an edit target.
**Reversal condition:** None foreseen; this is the linchpin of the AI-native efficiency claim.
**Evidence:** D-002, P13; [RFC 6902 positional anti-pattern](https://www.rfc-editor.org/rfc/rfc6902).

## D-034 · Composition = set-algebra + runtime construction over base queries
**Date:** 2026-07-15 · **Stage:** 7 · **Status:** Provisional

**Context:** Stage 6's three "strategies" (AI-selected/parallel/comparative) had no mechanics (Stage 7 C3).
**Choice:** Parallel = `union` of results (dedupe by id); comparative = `intersect`/`difference` + id/name alignment; AI-selected = the agent constructs a query node at runtime. The strategies are set-algebra and runtime construction over the base query (D-030), not new primitives.
**Reversal condition:** A needed composition can't be expressed as set-algebra over results.
**Evidence:** D-026 (one parameterized walk); D-032 (id-keyed results enable set ops).

---

## D-035 · Two-layer operation set (8 primitives + composite macros + compact)
**Date:** 2026-07-15 · **Stage:** 8 · **Status:** Provisional

**Context:** The write side was undefined (Stage 8 C1/C3); the op set must be small (S6) yet complete and invariant-preserving (RM14).
**Choice:** 8 primitives — create-node, retract-node, set-content, set-property, unset-property, add-edge, retract-edge, move — complete and closed under the 10 invariants (Stage 4 §11). Containment is edited only via create-node/move (protects single-home); nothing destroys. Composites (merge, split, promote, demote) are atomic macros = primitive sequences. tag = add-edge; reorder = move. `compact` is the sole destructive op, explicit and separate.
**Reversal condition:** A required edit can't be expressed as a primitive/composite without breaking an invariant.
**Evidence:** Stage 4 §11 invariants; S6; P12.

## D-036 · Ops address only by id; no positional addressing
**Date:** 2026-07-15 · **Stage:** 8 · **Status:** Provisional

**Context:** Positional addressing is the merge anti-pattern (JSON Patch, `research/versioning-and-merge.md` §9); the read/write bridge (D-033) supplies ids.
**Choice:** Every op targets node/edge ids from query results; create-node mints a new collision-free id (D-014); no op references a line/offset/index.
**Reversal condition:** None foreseen; positional addressing is incompatible with convergence.
**Evidence:** D-033, P13, D-014; [RFC 6902](https://www.rfc-editor.org/rfc/rfc6902).

## D-037 · Convergence by design (LWW registers + grow-sets → SEC)
**Date:** 2026-07-15 · **Stage:** 8 · **Status:** Provisional

**Context:** D-014 requires concurrent ops to commute for server-free merge.
**Choice:** create/add = grow-sets; retract = status flag (retract-wins); set-property/set-content/move = LWW-registers with Lamport-ts tie-break; list-valued props may opt into OR-Set semantics. The state-fold (partition by target+field; max-ts for LWW, union for sets) is order-independent → Strong Eventual Consistency; CRDT-ready without model change. v1 content merge is per-node LWW (coarse; RM18).
**Reversal condition:** A required edit semantics cannot be made commutative/convergent.
**Evidence:** [Shapiro CRDTs](../research/versioning-and-merge.md), D-014, T7.

## D-038 · Optimistic-concurrency preconditions (solves RM17)
**Date:** 2026-07-15 · **Stage:** 8 · **Status:** Provisional

**Context:** LWW converges but can silently lose a concurrent edit (RM18); the read→write loop races (RM17).
**Choice:** An op may carry an `expect(target, version=v | field OP value)` precondition; if it fails the op is rejected and the caller re-queries. Default (unguarded) = LWW converge; guarded = check-and-set. The version seen at query becomes the precondition at write.
**Reversal condition:** Preconditions prove insufficient and a stronger transactional model is required.
**Evidence:** [RFC 6902 test-op](https://www.rfc-editor.org/rfc/rfc6902); D-014; resolves RM17.

## D-039 · Op-log is canonical; state = deterministic fold (event sourcing)
**Date:** 2026-07-15 · **Stage:** 8 · **Status:** Provisional

**Context:** P11 — ops canonical, state a projection; charter Phase C exit criterion = op-log↔state equivalence.
**Choice:** The append-only op-log is the journal; state = order-independent fold over the op-set (D-037). Complete-rebuild and temporal-query follow. Semantic op-log↔state equivalence established here; byte-level demo completed in Stage 9 (needs the canonical form). Underwrites the file-as-truth fallback (RM8): file = op-log + snapshot if a live store is ever needed.
**Reversal condition:** Fold cost at scale forces a materialized-state-as-truth model (op-log demoted to audit).
**Evidence:** [Fowler event sourcing + Datomic](../research/versioning-and-merge.md), P11, D-016.

---

## D-040 · One model, three serializations
**Date:** 2026-07-15 · **Stage:** 9 · **Status:** Provisional

**Context:** Serialization must do integrity, edits, and human authoring — different jobs, different byte layouts (Stage 9 §2). Conflating them is how prior formats went wrong.
**Choice:** Three serializations of one model: (a) canonical normal form (hash/sign/dedup/diff), (b) append-only op-log (edits/sync/cache), (c) author-facing text (Phase D). All inter-convert losslessly; author text normalizes to the canonical form ("write loose, store canonical" at the byte level, D-003). JSON is the machine encoding for (a)/(b), never the author surface.
**Reversal condition:** Maintaining three serializations proves to cause drift/inconsistency that a single form would avoid.
**Evidence:** D-003, P17; [tools-for-thought.md (conflation failures)](../research/tools-for-thought.md).

## D-041 · Canonical normal form = line-oriented canonical JSON (RFC 8785)
**Date:** 2026-07-15 · **Stage:** 9 · **Status:** Provisional

**Context:** SEC gives same state, not same bytes (Stage 9 C2); hashing/signing/dedup/diff need exactly one byte-string per state (RM10).
**Choice:** `canon: State→Bytes` — document-order nodes, deterministic edge/property ordering (D-029 cascade), canonical scalars, NFC strings, fixed field order; line-oriented so one semantic change = one small diff and `hash(canon)` is stable. Realized as canonical JSON (JCS/RFC 8785 rules) over the `.sarib`⇄JSON isomorphism — don't reinvent canonicalization.
**Reversal condition:** JCS-style canonical JSON proves unable to encode a needed model element losslessly.
**Evidence:** [RFC 8785 JCS / RFC 9804 canonical S-expr](../research/standards-adoption.md); D-029, invariant 10.

## D-042 · File = canonical snapshot + append-only op-log
**Date:** 2026-07-15 · **Stage:** 9 · **Status:** Provisional

**Context:** Must decide what is stored and what is hashed (Stage 9 C4); need cache-stable growth (RA4) and the file-as-truth fallback (RM8).
**Choice:** A stored file = optional canonical snapshot + append-only op-log suffix; read = load snapshot + fold suffix; canonical *state* is content-addressed/hashed, the log carries history/sync. Append-only growth keeps KV-cache prefixes stable. This IS the "demote to live store + journal" fallback, so RM8 needs no model change.
**Reversal condition:** Snapshot+log proves worse than a single materialized file for real workloads.
**Evidence:** [event sourcing/Datomic snapshot](../research/versioning-and-merge.md), [KV-cache/Manus](../research/ai-context.md); D-039, RM8.

## D-043 · Load safety — pure data, bounded expansion, canonicalization resistance
**Date:** 2026-07-15 · **Stage:** 9 · **Status:** Provisional

**Context:** YAML's `load()`-RCE and billion-laughs (K8s CVE) are the cautionary tales (`research/standards-adoption.md`); RS1/RS2/RS6.
**Choice:** Pure-data load (no tags/constructors/macros/directives that execute); transclusion resolution is cycle-detected + depth/size-bounded; the canonicalizer rejects ambiguous encodings (duplicate keys, non-NFC, non-canonical numbers). Content is inert data, never instructions (format-level RS3 defense; the Crockford-removed-comments discipline).
**Reversal condition:** A required feature genuinely needs load-time evaluation (would demand a sandbox spec instead).
**Evidence:** [YAML RCE / billion-laughs, JSON comment-removal](../research/standards-adoption.md); RS1/RS2/RS3/RS6.

## D-044 · Partial/streaming load via addressable records + derived index
**Date:** 2026-07-15 · **Stage:** 9 · **Status:** Provisional

**Context:** Agents must load a subgraph, not the whole file (P14, RM11); length degradation makes whole-file loads costly.
**Choice:** Records are id-addressable; a derived, disposable id→byte-offset index gives random access; containment-order sections are contiguous byte ranges; locality (P15) guarantees streaming and bounded-subgraph loads (D-028). The index is derived-layer (P17), never canonical.
**Reversal condition:** Addressable-record layout proves incompatible with a needed canonical-form property.
**Evidence:** [ai-context.md (context economy, length degradation)](../research/ai-context.md); P14, P15, RM11.

---

## D-045 · Author surface = CommonMark superset (Candidate A recommended; B retained)
**Date:** 2026-07-15 · **Stage:** 10 · **Status:** Provisional

**Context:** Phase D opens; the surface must be one people prefer to the canonical JSON (RD6), render in Markdown tools (P6), and stay in the LLM distribution (`research/syntax-and-legibility.md`).
**Choice:** The surface is a CommonMark superset taking djot's discipline (unambiguous glyphs, attributes-on-any-element, no-backtracking locality) but a Pandoc/MyST/Dataview-compatible surface that degrades to literal text in vanilla renderers. **Candidate A (prose-native) is the recommended default**; Candidate B (outline-dense) is retained as an alternative and future compact profile. Both ship as judgeable example packages and normalize to the same model/canonical form.
**Reversal condition:** Writability testing shows authors prefer B's density, or A's Markdown constraints block a needed construct.
**Evidence:** [research/syntax-and-legibility.md](../research/syntax-and-legibility.md); [djot/Beyond Markdown](https://johnmacfarlane.net/beyond-markdown.html); P6, priority order.

## D-046 · Surface conventions (containment/type/props/edges/id/meta)
**Date:** 2026-07-15 · **Stage:** 10 · **Status:** Provisional

**Context:** The chosen surface needs concrete, tokenizer-cheap, gracefully-degrading conventions.
**Choice:** headings + list nesting → containment; trailing `{.type #slug}` → node type/slug; `key:: value` inline fields → properties; `[rel:: [[Target]]]` → typed edges (untyped `[[Target]]` → `relates-to`); `^id` → block identity; YAML front matter → file metadata. Glyphs drawn from the single-token ASCII set; multi-char sigils measured against real tokenizers before freeze.
**Reversal condition:** A convention proves to fragment tokens or collide ambiguously (RA11).
**Evidence:** [Pandoc attrs / MyST / Dataview inline fields / Obsidian ^id](../research/syntax-and-legibility.md).

## D-047 · Spatial legibility via derived, optional annotations
**Date:** 2026-07-15 · **Stage:** 10 · **Status:** Provisional

**Context:** The goal demands conveying the tree's shape/spread/depth to human and model; foraging theory + SoT/RAPTOR show scent and map-before-detail help both (`research/syntax-and-legibility.md` §Q1).
**Choice:** Deliver shape via **derived, optional** cues — statistics-cookie counts `[k/n]`, dotted-path/breadcrumb depth, ordinal position, fold/`…` markers, a generated typed skeleton/TOC, container summaries — regenerated from the model, never authored, never canonical (P17/D-019). Stable ids double as spatial anchors.
**Reversal condition:** Derived cues prove insufficient and authors need to hand-place shape hints.
**Evidence:** [Pirolli/Card foraging](http://act-r.psy.cmu.edu/wordpress/wp-content/uploads/2012/12/280uir-1999-05-pirolli.pdf), [SoT](https://arxiv.org/abs/2307.15337), [RAPTOR](https://arxiv.org/abs/2401.18059), [org cookies](https://orgmode.org/manual/Breaking-Down-Tasks.html).

## D-048 · Importance is a field, not typography; ship two judgeable syntaxes
**Date:** 2026-07-15 · **Stage:** 10 · **Status:** Provisional

**Context:** Models interpret bold/italic emphasis weakly; importance must survive projection and be queryable (`research/syntax-and-legibility.md` §Q2).
**Choice:** Priority/weight/importance is an addressable field (`priority::`), queryable and projection-stable; typographic emphasis is for human scanning only. Two full surfaces (A, B) are shipped as independently-judgeable example packages per Sarib's steer on taste-dependent choices.
**Reversal condition:** A field-based importance proves less usable than a typographic convention in testing.
**Evidence:** [emphasis weakness + format-sensitivity](../research/syntax-and-legibility.md), [arXiv 2411.10541](https://arxiv.org/html/2411.10541v1).

---

## D-049 · Three validation tiers; only un-parseability blocks
**Date:** 2026-07-15 · **Stage:** 11 · **Status:** Provisional

**Context:** Authorability (P3) and machine-reliability (P10) must coexist; XML's draconian errors and Markdown's silent divergence are both anti-patterns (Stage 2 §2.2).
**Choice:** Tier 0 well-formed (total; unrecognized input → L0 prose node; near-unfailable), Tier 1 structurally valid (the 10 invariants), Tier 2 schema-valid (active vocabulary). Nothing above Tier 0 is fatal; all deviations are located, non-fatal diagnostics carrying node/edge ids.
**Reversal condition:** A use case requires hard-blocking on schema violations (would add an opt-in strict mode, not change the default).
**Evidence:** P15, P3, P10; Stage 2 §2.2 (forgiving surface / deterministic parse).

## D-050 · Self-hosted, closed-world, deterministic validation
**Date:** 2026-07-15 · **Stage:** 11 · **Status:** Provisional

**Context:** A separate constraint language (SHACL/XSD kept in sync with the schema) is the semantic-web trap (Stage 2 §2.1).
**Choice:** Schemas are `.sarib` checked by a meta-schema; no second validation language; validation is closed-world (unknown-vs-active-schema = diagnostic, no inference); diagnostics are deterministic, canonical-ordered, and queryable (self-hosted as derived nodes).
**Reversal condition:** Self-hosted schemas prove unable to express a needed constraint class.
**Evidence:** D-023, D-008; [semantic-web.md (OWL/SHACL split)](../research/semantic-web.md).

## D-051 · Fidelity contract — idempotent normalization, lossless round-trip, read-transparent cues
**Date:** 2026-07-15 · **Stage:** 11 · **Status:** Provisional

**Context:** The surface is the third serialization (D-040) and needs a stated fidelity guarantee; derived spatial cues (D-047) can go stale.
**Choice:** `normalize(parse(surface))` = canonical form and is idempotent (a gofmt for `.sarib`); model-level round-trip is lossless (incidental formatting may change, knowledge never does); derived cues are ignored on parse and regenerated on render, so staleness/hand-edits are never errors.
**Reversal condition:** Idempotent normalization proves impossible for a needed construct.
**Evidence:** D-003, D-040, D-041, P17; [RM10/RM20 diffability].

---

## D-052 · Projection = query + template; all views (incl. the AI context window) are (query, template) pairs
**Date:** 2026-07-15 · **Stage:** 12 · **Status:** Provisional

**Context:** P1 (store once, render infinitely) needs an architecture; the brief lists ~13 view types.
**Choice:** A view = a query (subgraph + order, Stage 7) + a template (element→presentation), every projected element carrying its node/edge id. All brief views — document, outline, mind-map, dependency graph, board, timeline, table, slides, **AI context window** — are (query, template) pairs over the one model; no per-view engine. The agent's context window is a projection like any other (rendering-for-humans and rendering-for-agents are one operation).
**Reversal condition:** A required view can't be expressed as (query, template) over the model.
**Evidence:** P1, D-026, D-030, D-033.

## D-053 · Every projection declares live-window vs terminal-export
**Date:** 2026-07-15 · **Stage:** 12 · **Status:** Provisional

**Context:** Round-trip dies where a view is an ambiguous second edit surface (Stage 2 §2.3).
**Choice:** A projection is either a **live window** (edits become id-addressed operations, D-033) or a **terminal export** (read-only, self-declared, re-export to change). The ambiguous-editable-but-no-back-channel middle is forbidden (P17). Lossy live views hide but never drop fields.
**Reversal condition:** None foreseen; this is the empirically decisive round-trip rule.
**Evidence:** [tools-for-thought.md (Notion views vs exports; Jupyter)](../research/tools-for-thought.md), P17, D-009.

## D-054 · Derived spatial cues are computed per view on render
**Date:** 2026-07-15 · **Stage:** 12 · **Status:** Provisional

**Context:** D-047 defined spatial cues; rendering is where they're computed and placed, view-appropriately.
**Choice:** Rendering computes skeleton/TOC, `[k/n]` counts, subtree size, ordinal position, fold markers, and container summaries from the model on demand, presented per view (board=column counts, timeline=span, outline=depth+child counts, document=TOC). Always regenerated, never authored/canonical (P17/D-051); ids double as spatial anchors.
**Reversal condition:** Per-view derived computation proves too costly and cues must be materialized (would carry `inferred` provenance, D-019).
**Evidence:** [SoT/RAPTOR/foraging](../research/syntax-and-legibility.md), D-047, P17.

---

## D-055 · Reference architecture = 6 components as executable stages
**Date:** 2026-07-15 · **Stage:** 13 · **Status:** Provisional

**Context:** The paper design needs a buildable form small enough to satisfy S6 and instrument the existential risks.
**Choice:** parser · normalizer · model store · op engine (with validation) · query engine · projector. Query+projector are one mechanism (a view = query+template, D-052); op engine + validator share invariant checks (RM14). Each component is the executable form of one stage; data flows in the read→edit→render loop, not a pipeline.
**Reversal condition:** A needed capability doesn't fit the component decomposition.
**Evidence:** Stages 4–12; D-052, RM14.

## D-056 · Business-card parser — weekend / ≤~1000 LOC (S6)
**Date:** 2026-07-15 · **Stage:** 13 · **Status:** Provisional

**Context:** S6 (JSON-simplicity test) is a survival trait, not an aspiration (Stage 2 §2.2, standards-adoption).
**Choice:** A conforming Tier-0/1 parser is a weekend / ≤~1000 LOC build, made reachable by total+local+no-backtracking parsing (D-045/D-049), a business-card grammar (P16/D-018), and canonical-JSON reuse (D-041). Reference parsers ship in TypeScript/Python/Rust as adoption instruments (a free parser everywhere).
**Reversal condition:** Conformance genuinely requires more than ~1000 LOC (would signal the core grew too big — revisit priority rule 4).
**Evidence:** S6; [JSON simplicity/business-card grammar](../research/standards-adoption.md); P16.

## D-057 · Ship a consumer with v0.1 (MCP server + CLI) + harness + corpus
**Date:** 2026-07-15 · **Stage:** 13 · **Status:** Provisional

**Context:** A spec with no consumer is a dead letter (llms.txt ~0.1% reads vs AGENTS.md; Stage 2 §2.2); existential risks need an instrument.
**Choice:** The reference implementation ships a consumer with v0.1 — an MCP server (files as resources, ops as tools; the agent loop) and a `sarib` CLI (parse/fmt/query/apply/render/validate/diff), both thin transports over the components (D-035). A benchmark harness (S2/S4/S3/S6/RA11) and a conformance corpus (RG2) are required before spec freeze (Stage 15 gate).
**Reversal condition:** None foreseen; shipping a consumer is the adoption precondition.
**Evidence:** [AGENTS.md vs llms.txt](../research/ai-context.md); RD1/RD2, RP3, Rule 6.

---

## D-058 · File conventions
**Date:** 2026-07-15 · **Stage:** 14 · **Status:** Provisional

**Context:** Consolidation exposed that no file/versioning conventions were stated.
**Choice:** Extension `.sarib`; media type `text/sarib` (provisional registration target); UTF-8 + NFC; the file declares its core `sarib` version and pinned `vocab@version` in front matter.
**Reversal condition:** Registration or ecosystem constraints require different conventions.
**Evidence:** Stage 14 §9; D-025 (vocab pinning).

## D-059 · Compatibility contract
**Date:** 2026-07-15 · **Stage:** 14 · **Status:** Provisional

**Context:** No explicit contract for how a reader handles future-version content (YAML 1.1→1.2 meaning-drift is the anti-pattern).
**Choice:** Frozen core (a document's meaning never changes under a later core revision); vocabularies semver, additive-only within a major; unknown core-minor/vocabulary degrades gracefully (unknown types→generic nodes, unknown props round-trip untouched), never fails, never silently reinterprets; deprecate-not-delete.
**Reversal condition:** A required correction can't be expressed additively or as a clean major bump.
**Evidence:** P16/D-011/D-025; [YAML versioning hazard](../research/standards-adoption.md).

---

## D-060 · v1.0 is a conditional proposal, gated on measured evidence
**Date:** 2026-07-15 · **Stage:** 15 · **Status:** Provisional

**Context:** The 15-stage design is complete on paper, but every existential risk (RH2/RA1/RA2/RD1/RL2) is empirical (register §10); declaring "done" on paper would be the drift the charter warns against.
**Choice:** v1.0 is a *conditional* proposal — the specification is complete and internally consistent, but ratification/freeze is gated on the reference implementation clearing the Stage 15 §4 benchmark gate (success criteria S1–S8) and tokenizer-verifying the grammar (RA11). The standard ships only if measured evidence shows it beats the Markdown baseline (Rule 6). Overclaiming completion before this gate is drift.
**Reversal condition:** N/A — this is the project's terminal honesty condition; it can only be discharged by running the gate.
**Evidence:** Rule 6; Stage 1 §5 success criteria; register §10.

---

## D-061 · Candidate A ratified as the normative author surface (user judgment)
**Date:** 2026-07-19 · **Stage:** post-15 execution (Sprint 0→1) · **Status:** Ratified

**Context:** Stage 10 shipped two judgeable packages; Sprint 0 measured the real trade (B saves 26.9% tokens whole-file; A holds the Markdown carrier + in-distribution accuracy; point-edit cost ~equal via ops). Sarib reviewed both and chose.
**Choice:** **Candidate A (prose-native Markdown superset) is the normative surface.** Candidate B is preserved as the future *compact profile* for token-critical agent↔agent exchange (not author-facing). Reference implementation (Python), conformance corpus, and benchmarks build against A.
**Reversal condition:** Freeze-gate benchmarks (G1–G8) reveal an A-specific failure that B avoids.
**Evidence:** `bench/tokenizer-report.md`; Stage 10 §6; D-045; user ratification 2026-07-19.

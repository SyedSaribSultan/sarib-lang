# Stage 3 — Design Principles

**Status:** Draft v0.1 — open for critique by Stage 4 · **Date:** 2026-07-15
**Input:** Stage 1 (Vision), Stage 2 (Prior Art), all seven files in `../research/`
**Decisions logged:** D-012 … D-014 (this stage); ratifies D-001 … D-011
**Purpose:** This is the project's constitution. It converts two stages of vision and evidence into a numbered set of binding constraints that the Phase B model (Stages 4–7) must obey. Where Stage 1 offered *stances* (provisional, reversible) and Stage 2 offered *lessons* (evidence), Stage 3 offers *principles* (ratified constraints). A later stage may still amend a principle, but only by logging a reversal and showing what evidence changed.

---

## 1. Critique of Stage 2

Stage 2 did its job — five beats plus the three closed in session 2 gave enough evidence to ratify almost every Stage 1 stance. Three criticisms of Stage 2 itself, which this stage must resolve:

**C1 — Stage 2 accumulated decisions without resolving their collisions.** D-006 (be a Markdown superset) and D-007 (labeled property graph) are in latent tension: Markdown is a *tree* of prose blocks; a property graph is a *graph* of typed nodes with cross-edges. Stage 2 never said how one file is both. The edge-writing-ceremony finding (D-012/D-013) is what resolves it, and Stage 3 must make that resolution explicit and central, not incidental — it is the load-bearing design idea of the entire project (see P4, P5).

**C2 — "Progressive formalization" was asserted but never operationalized.** Stage 1 (T2) and Stage 2 (§2.1) both endorsed it; neither said what the *levels* are or how a document moves between them. A principle that can't be checked isn't a constraint. P9 defines the ladder concretely.

**C3 — The decisions are not yet ordered by authority.** When two principles conflict during model design (they will), which wins? Stage 2 left them as a flat list. Stage 3 imposes a lexicographic priority (§4) so Stage 4 has a tie-breaker instead of a debate.

One substantive correction to Stage 2: §2.4 leaned on the claim that authoring structure *deletes* GraphRAG's extraction cost. That is only true for structure the human or agent writes *deliberately at edit time*. It does not eliminate the cost of enriching a large existing prose corpus — that still requires an extraction pass. The principle (P11, P14) should claim the narrower, defensible thing: `.sarib` makes *incrementally authored* structure cheap and durable, so the cost is paid once at write time and never re-paid on read.

---

## 2. Design principles

Seventeen principles in five clusters. Each: the principle, why (with evidence), and the binding implication for the model. The one-line form of each is the canonical statement; the prose is commentary.

### Cluster A — Canonical form

**P1 · Store knowledge once; render it infinitely.**
The founding thesis, now evidence-backed: every single-source-many-views system that held together did so by keeping one canonical store and deriving views (Notion's blocks → table/board/timeline; [Notion](https://www.notion.com/blog/data-model-behind-notion)), and every one that broke did so at a projection that became a second source of edits ([fast.ai on Jupyter+git](https://www.fast.ai/posts/2022-08-25-jupyter-git.html)).
*Implication:* exactly one canonical representation; documents, outlines, graphs, boards, timelines, and context windows are all derived and disposable.

**P2 · Semantics are canonical; syntax is a projection.**
The five-layer stack (D-001). The abstract model (nodes, edges, properties) is the specification's primary object; the `.sarib` text file is its serialization; everything else is a view. This is the project's philosophy applied to its own artifacts.
*Implication:* the model is specified before and independently of the syntax (Phase B before Phase D). No semantic capability may exist only in the syntax.

### Cluster B — Human surface

**P3 · Prose is the surface; structure is progressive and largely agent-added.**
Twenty years of evidence show humans do not hand-author structured knowledge inline — form input displaced in-text annotation even in Wikipedia ([Wikidata WWW 2023](https://iccl.inf.tu-dresden.de/w/images/9/9d/Vrandecic-Pintscher-Kroetzsch_Wikidata-History-WWW-2023.pdf)); even sympathetic experts wrote prose instead of RDF ([Norvig↔Berners-Lee](https://grandtextauto.soe.ucsc.edu/2006/07/18/googles-norvig-questions-berners-lee-on-the-semantic-web/)). The AI-native premise relocates the labor: the human writes sentences, the agent enriches to graph, the human confirms (D-010).
*Implication:* a valid `.sarib` document may be pure prose. Every structural feature must be optional and additive — never a precondition for writing.

**P4 · Edges emerge from prose; standalone edge statements are the fallback, not the default.**
The sharpest prior-art finding: every graph-as-text syntax forces a standalone statement naming both endpoints and the relation — *edge-writing ceremony* — and that ceremony is exactly why Turtle, Cypher, DOT, and GraphML all stayed in query/viz/config niches and none became a medium people think in ([graphs-and-databases.md §7](../research/graphs-and-databases.md)). In prose, "Alice knows Bob" *is* the edge; the endpoints and relation are the sentence (D-012).
*Implication:* the primary edge-authoring mechanism is an inline typed link inside a natural sentence. Block-form edge lists remain available for the cases prose can't carry, but the model must not privilege them.

**P5 · Trees are free; graphs are opt-in but first-class.**
Every structure humans hand-author at scale is a tree — Markdown, outliners, KDL, filesystems — because the single implicit relation (containment) needs no naming, while arbitrary typed edges must each be written out ([KDL](https://kdl.dev/), [graphs-and-databases.md §5](../research/graphs-and-databases.md)). `.sarib` must make the tree case cost nothing and the graph case cheap (D-013).
*Implication:* document hierarchy (headings, lists, nesting) compiles to zero-ceremony **containment edges**; the model distinguishes containment edges from **cross-reference edges**. (Storage containment is a single-parent ordered spanning tree — one home per node — with multi-parent structure delivered by transclusion; this refines the earlier "DAG" framing, ratified as D-016 in Stage 4.)

**P6 · Be a Markdown superset; the carrier is Markdown renderers, LLM corpora, and agent runtimes.**
Adoption is distribution, not merit: every winning format had a carrier that pre-installed its parser, every elegant loser lacked one ([standards-adoption.md](../research/standards-adoption.md); S-expressions waited 28 years, [RFC 9804](https://www.rfc-editor.org/rfc/rfc9804.pdf)). Mermaid rode Markdown into ubiquity with no semantic model at all ([GitHub Blog](https://github.blog/developer-skills/github/include-diagrams-markdown-files-mermaid/)). `.sarib`'s carrier is the pretraining distribution plus existing Markdown renderers (D-006).
*Implication:* a `.sarib` file must render acceptably in a standard CommonMark renderer, and its constructs must look like text humans and LLMs already emit. A reference reader/writer ships with v0.1 — a spec with no consumer is a dead letter (llms.txt vs AGENTS.md).

### Cluster C — The model

**P7 · Labeled property graph, not triples.**
RDF lacks native lists and edge properties, and its reification quadruples data size; JSON-LD/Turtle also scored *worst* for LLMs on accuracy and token cost ([KG-LLM-Bench](https://arxiv.org/abs/2504.07087), [Sporny](http://manu.sporny.org/2014/json-ld-origins-2/)). Property graphs put properties directly on nodes *and edges* and match how people whiteboard ([Cypher origin](https://www.thobe.org/work/cypher/)) (D-007).
*Implication:* the atom is a node with properties; edges are typed, directed, and carry their own properties; lists are native. No IRI/prefix ceremony.

**P8 · Every atom has a durable, position-independent identity; humans read names, machines hold IDs.**
Identity-by-content is the core failure mode: because Git stores content without stable identity, it *cannot* track a rename and re-guesses heuristically ([Pro Git](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)). Round-trip and merge both require stable per-element identity ([Portable Text `_key`](https://www.portabletext.org/specification/), [Automerge/Yjs opIDs](https://raw.githubusercontent.com/yjs/yjs/main/INTERNALS.md)). And across every system, the more opaque the ID, the more completely tooling must hide it (D-009).
*Implication:* every node and edge gets a durable ID that survives rename/move/reword. Authors reference things by human-readable name/slug; the system assigns and resolves opaque IDs, surfacing them only when unavoidable (as readable slugs, quarantined from prose).

**P9 · Progressive formalization along a defined ladder.**
Endorsed by all evidence, now operationalized (resolving C2). RDF died of front-loaded formality; Markdown lost machines by refusing it; the dose must be titratable ([semantic-web.md](../research/semantic-web.md)).
The ladder — each rung is valid `.sarib`, and moving up is additive:

| L | Rung | Example gesture |
|---|---|---|
| 0 | Prose | plain paragraphs (valid Markdown) |
| 1 | Structured prose | headings, lists, nesting → containment edges (free, P5) |
| 2 | Typed nodes | mark a block as a `task`/`decision`/`person` |
| 3 | Typed edges | inline typed links between nodes (P4) |
| 4 | Properties & tags | key/value metadata, tags on nodes/edges |
| 5 | Schema-checked | optional schema validates types/properties |

*Implication:* the parser accepts every rung; validation is opt-in and layered; nothing above L0 is ever required. A document is a mix of rungs, per-node.

**P10 · Record attributable claims with provenance, not adjudicated truth; segregate asserted from derived.**
The one-true-metadata web sank on the fact that people lie, err, and disagree ([Metacrap](https://people.well.com/user/doctorow/metacrap.htm)); Wikidata's plurality model (referenced claims with ranks) is what survived ([Wikidata CACM](https://iccl.inf.tu-dresden.de/w/images/8/89/Wikidata-CACM-2014.pdf)). OWL's inability to separate inferred from asserted facts forced batch reloads ([TerminusDB](https://terminusdb.com/blog/the-semantic-web-is-dead/)) (D-008).
*Implication:* every assertion is attributable (who/what asserted it, when, on what basis); human statements, agent inferences, and imported facts are distinguishable at the model level; validation is closed-world (a type-checker, not an open-world reasoner).

### Cluster D — Change and the machine interface

**P11 · Operations are the canonical unit of change; state is a fold over them.**
Event sourcing, Datomic's accretion-only "database as a value," and both CRDT families independently converge here, and Fowler names a version-control system as the archetype ([Fowler](https://martinfowler.com/eaaDev/EventSourcing.html), [Datomic](https://docs.datomic.com/transactions/model.html)). This is also the token-economics win: address and edit atomically instead of regenerating (D-002).
*Implication:* the edit-operation vocabulary (Phase C) is a first-class part of the standard, not an API afterthought; any document state is reconstructable by folding its operation log. *(Scope guard from C1-correction: this makes incrementally authored change cheap; it does not eliminate bulk extraction cost on legacy prose.)*

**P12 · Retract, never destroy.**
Datomic models deletion as a new fact (`:db/retract` = "not true at a point in time"); CRDTs keep tombstones for convergence ([Datomic](https://docs.datomic.com/transactions/model.html), [Yjs INTERNALS](https://raw.githubusercontent.com/yjs/yjs/main/INTERNALS.md)). This composes with P10: a deletion is an assertion about status, auditable and reversible.
*Implication:* deletion is a status assertion, not an erasure; history is extended, never overwritten. (Physical garbage-collection is a separate, explicit compaction operation.)

**P13 · Operations name identified elements, never positions; design for commutativity.**
The entire difference between mergeable and unmergeable lives here: JSON Patch addresses array *positions*, so concurrent edits corrupt each other ([RFC 6902](https://www.rfc-editor.org/rfc/rfc6902)); Automerge/Yjs address *identified elements* with `(replica, counter)` IDs and merge with no server ([Yjs INTERNALS](https://raw.githubusercontent.com/yjs/yjs/main/INTERNALS.md)). CRDT beats OT for owned, offline-first files ([Seph Gentle](https://josephg.com/blog/crdts-are-the-future/)) (D-014).
*Implication:* every operation references node/edge IDs (P8), never line numbers or array indices; prefer difference-form/commutative operations ("add tag X" over "set tags = [...]"); the op set is specified so concurrent operations commute, making git-level (and later CRDT-level) merge automatic. v1 targets clean 3-way merges on stable IDs; the vocabulary is CRDT-ready without model changes (ratifies T7).

**P14 · Optimize tokens-per-interaction, not per-byte; design the byte layout for the cache.**
Syntax terseness saves tens of percent; atomic ops and subgraph retrieval save orders of magnitude, and prompt-cache reads (billed ~10% of base, matched on exact prefix) reward byte-stable, append-only files ([Manus](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)). Familiar low-punctuation syntax beats novel compact notations, which pay an accuracy tax ([Improving Agents](https://www.improvingagents.com/blog/best-nested-data-format/), [Notation Matters](https://arxiv.org/abs/2605.29676)) (D-002).
*Implication:* deterministic canonical ordering; new content appends (stable prefix); no volatile fields (timestamps, counters) near the top; every node addressable so agents fetch minimal subgraphs rather than whole files (length degradation persists — [NoLiMa](https://arxiv.org/abs/2502.05167)). A lossless `.sarib`⇄JSON mapping lets agents write through existing structured-output tooling without JSON on the authoring surface.

### Cluster E — Evolution and integrity

**P15 · Forgiving surface, deterministic parse.**
Markdown's "nothing is a syntax error" bought adoption but caused silent divergence (15 renderings from 22 parsers); XML's draconian errors killed casual authorship ([markup-and-documents.md](../research/markup-and-documents.md)). The winning zone is a surface that always parses without fatal errors, over a strict, well-defined parse.
*Implication:* any input parses deterministically to a model (prose degrades to L0 nodes); semantic validity is a separate, lint-grade layer with non-fatal diagnostics. A construct's meaning must be identifiable from its shape alone (locality — no whole-document lookahead), so streaming generation and incremental edits work.

**P16 · One frozen core; one in-core extension mechanism with graceful degradation.**
Markdown's single deepest defect — no attribute/extension syntax — forced every platform to fork ([Beyond Markdown](https://johnmacfarlane.net/beyond-markdown.html)); reST's directives show extension-without-forking works. JSON froze and won; YAML "actively evolves" and every document is version-ambiguous ([YAML from hell](https://ruudvanasseldonk.com/2023/01/11/the-yaml-document-from-hell)) (D-011).
*Implication:* the core grammar is small (business-card target, S6) and frozen once v1 ships; a single blessed extension mechanism lets unknown constructs parse, render generically, and round-trip untouched; extensions are self-announcing and versioned separately from the core. A document's meaning never changes under a spec revision.

**P17 · Projections may hide but never silently drop; one-way projections must be honestly terminal.**
Notion preserves invisible state through view/type changes ("we preserve as much user intention as possible", [Notion](https://www.notion.com/blog/data-model-behind-notion)); Portable Text's silent "skip unknown types" is the anti-pattern for knowledge ([spec](https://www.portabletext.org/specification/)). Round-trip holds only where projections carry identity *and* each state class has one owner — the fatal zone is an output that looks editable but has no back channel ([tools-for-thought.md](../research/tools-for-thought.md)).
*Implication:* a projection either is a live, ID-carrying window whose edits flow back, or is explicitly marked terminal (read-only). Lossy views must self-declare their losses. Content, derived/cache, and session state are separate layers with one authoritative writer each.

---

## 3. Ratification of the Stage 1 tensions

| # | Stage 1 stance | Verdict | Now carried by |
|---|---|---|---|
| T1 | Humans write trees, think graphs | **Revised & ratified** — humans write *prose*; structure is agent-added | P3, P4, P5 |
| T2 | Progressive formalization | **Ratified & operationalized** (the ladder) | P9 |
| T3 | Interaction over compression | **Ratified** | P11, P14 |
| T4 | Projections carry identity | **Ratified** | P1, P8, P17 |
| T5 | File is truth; indexes disposable | **Ratified, with risk** — Notion (the winning realization) uses a DB; the plain-text bet is deliberate and carries R-new-1 | P1, P2 |
| T6 | Determinism + graceful extensibility | **Ratified** | P15, P16 |
| T7 | Clean git merges v1; CRDT-ready | **Ratified** — evidence now in (D-014) | P13 |
| T8 | Every assertion attributable | **Ratified & promoted** to model pillar | P10 |

No tension was reversed. T1 was the only substantive revision (labor relocated to the agent), and it strengthens rather than weakens the project.

## 4. Priority ordering (the tie-breaker)

When two principles conflict during model design, the earlier cluster wins, and within the constraints below these override even that. This exists so Stage 4 has a rule, not an argument.

1. **Integrity first.** Determinism, lossless round-trip, and safe merge (P8, P13, P15, P17) are never traded away for ergonomics or terseness. A pleasant format that corrupts knowledge is a failure.
2. **Human writability second.** If a modeling choice makes the prose surface hostile (P3–P6), it loses to the choice that keeps writing natural — *except* where it would violate rule 1.
3. **Machine efficiency third.** Token/cache optimizations (P14) are pursued only after integrity and writability are satisfied.
4. **Expressive completeness last.** Adding a modeling capability (a new node kind, a richer edge) must justify itself against the business-card grammar budget (P16, S6); when in doubt, leave it out and let the extension mechanism carry it.

Rationale: this is the "worse is better" discipline aimed correctly — cut expressive completeness and ceremony freely, never cut determinism, safety, or the extension point, because those are the cuts that cannot be patched later ([standards-adoption.md](../research/standards-adoption.md)).

## 5. What Stage 4 (Core Object Model) must deliver

Stage 3 hands the model designer a constrained problem. Stage 4 must specify, obeying the principles above:

1. **The node.** What is an atom? (A block of prose with identity and an optional type — provisional.) What are its intrinsic fields vs. properties?
2. **The edge.** Containment vs. cross-reference (P5); direction; edge properties (P7); how an inline typed link (P4) desugars into an edge.
3. **Identity.** ID scheme (durable, position-independent, tooling-hidden, human-slug-resolvable) (P8). Where IDs come from; what survives rename/move/merge/split.
4. **The type system.** The L2–L5 ladder rungs (P9): core node kinds (the brief's list — task, decision, person… — is a starting menu, to be cut aggressively per priority rule 4), the extension mechanism (P16), closed-world validation (P10).
5. **Provenance & status.** How attribution and retraction (P10, P12) attach to nodes, edges, and properties without drowning the common single-author case.
6. **The containment/graph duality.** The precise answer to C1: one file that is simultaneously a readable prose tree and a queryable property graph.

Open questions explicitly deferred (not for Stage 4): the operation vocabulary (Phase C / Stage 8), the concrete syntax (Phase D / Stage 10), the query language (Stage 7). Stage 4 defines *what exists*, not *how it's written* or *how it's edited*.

## 6. Risk register update

- **R-new-1 (from T5): the plain-text bet.** The only fully-working single-source-many-views system (Notion) uses a proprietary database, not a file. `.sarib` bets that a plain-text canonical form plus an index beats a database on ownership, longevity, and carrier compatibility. If Phase B/C shows file-as-truth cannot deliver acceptable multi-agent write throughput or query latency, the fallback is a specified live store with the file as an append-only journal/snapshot — the op-log (P11) makes this fallback cheap, which is itself a reason to commit to P11 early.
- **R-new-2: the containment/graph duality (C1) may not have a clean answer.** If one artifact cannot be both a natural prose tree and a full property graph without one crippling the other, the project must choose which to privilege (priority rule 2 says: keep writability, demote graph completeness to the extension layer). Stage 4 is where this is proven or disproven.

This document is unratified until Stage 4 critiques it.

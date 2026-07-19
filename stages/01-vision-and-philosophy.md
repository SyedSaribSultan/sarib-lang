# Stage 1 — Vision & Philosophy

**Status:** Draft v0.1 — open for critique by Stage 2 · **Date:** 2026-07-14
**Input:** Project brief ("Stage 0")
**Decisions logged:** D-001 … D-005

---

## 1. Critique of Stage 0 (the brief)

Per Operating Rule 1, this stage begins by critiquing its input. The brief is strong on ambition and diagnosis; its weaknesses are conflation, one mis-aimed optimization target, and four unnamed hard problems.

### C1 — "A language" is five things wearing one coat

The brief asks for *a language* but describes five separable layers: bytes and files, a data model, a type system, an edit/query protocol, and a human-facing syntax. Treating these as one artifact is how prior formats went wrong — XML welded syntax to model, so every XML-based standard inherited its verbosity; Markdown has *only* syntax, so it has no model to query.

**Consequence:** `.sarib` should be specified as a layered standard (§3). The file extension is the least important layer. The project succeeds even if the eventual surface syntax is boring — provided the model underneath is right.

### C2 — "Tokenizer efficient" aims at the wrong target

Tokenizers are model-specific and change yearly; optimizing syntax for today's BPE vocabularies is building on sand. More importantly, syntax terseness saves perhaps tens of percent, while the brief's own "AI-First Design" section contains the real prize: **atomic operations**. A point edit expressed as an operation costs tens of tokens; regenerating a 10k-token document costs 10k. That is a 2–3 order-of-magnitude difference *(estimate — to be benchmarked per Rule 6)*, and it is syntax-independent.

**Consequence (D-002):** the optimization target is reframed from *tokens per byte of knowledge* to **tokens per interaction** — reads fetch only the needed subgraph; writes emit only the delta. Syntax density remains a tiebreaker, not the goal.

### C3 — Version history is the substrate's job; diffability is the format's job

The brief lists "version history" as a language feature. Embedding history in the file fights the strongest versioning substrate ever deployed (git) and bloats the canonical form. What the *format* must supply is being a good citizen of version control: **stable node identity, normalized ordering, and a line-oriented canonical form**, so that a small semantic change is a small textual diff and concurrent edits merge cleanly.

**Consequence (D-004):** history storage delegates to the substrate; the format owns diffability and defines the *vocabulary of change* (the op set), which any history mechanism can record.

### C4 — Humans and AI need the same model, not the same ergonomics

The brief implies one surface serves both. But humans want forgiving, low-ceremony authoring; determinism wants exactly one canonical encoding. These are reconcilable only by splitting them: humans may **write loose** (an authoring dialect with inference and shortcuts), tools **store canonical** (a single normalized form optimized for reading and diffing), and agents mostly **edit via operations**. The precedent is `gofmt`/`prettier`: write how you like, the canonical form is what's stored.

**Consequence (D-003):** "human writable" is a requirement on the authoring dialect; "deterministic" is a requirement on the canonical form. They stop being contradictory.

### C5 — The 13 traversals collapse into two requirements

Linear, BFS, DFS, dependency, priority, semantic, chronological, tag, relationship, comparative, AI-selected — none of these is a file-format feature. They are **query plans over a sufficiently expressive model**. If the model captures typed nodes, typed edges, ordered containment, time, tags, priority, and provenance, every listed traversal is a query. "AI-selected traversal" simply means the agent composes its own query.

The one real constraint hiding here: the model must represent authorial sequence (document order is knowledge — narrative *is* an ordering) **without privileging it** in a way that makes other traversals lossy or expensive.

**Consequence:** "The Most Important Requirement" of the brief becomes two requirements — model expressiveness (Stage 4–5) and a query layer (Stage 7). Nothing about traversal belongs in syntax.

### C6 — Four hard problems the brief doesn't name

1. **Identity.** Stable node IDs under rename, move, merge, and split are the make-or-break usability problem. Where do IDs come from? Who types them? What survives a human retitling a node? Every system that solved projections (git, Notion, CRDTs) solved identity first.
2. **Concurrency.** "Multiple agents collaborate" implies merge semantics. Git 3-way? Operation-based (CRDT-ish)? Deciding late means retrofitting; deciding wrong means silent data corruption.
3. **Provenance and trust.** When humans and agents write into one graph, *who asserted what, when, and on what basis* must be first-class — otherwise agent inference contaminates human knowledge and the graph rots. The brief lists "machine annotations" but doesn't elevate provenance to a design pillar.
4. **Adoption physics.** Formats win by distribution, not merit alone: HTML had browsers, Markdown had GitHub and Stack Overflow, JSON had JavaScript. A standard no tool emits is dead text. The interop/embedding story (live inside Markdown? export from existing tools?) is a *requirement*, studied in Stage 2 (RQ8).

**Consequence (D-005):** identity, concurrency, provenance, and adoption enter the requirement set as first-class pillars.

---

## 2. Vision

> **`.sarib` is a plain-text language for knowledge as a graph: typed nodes, typed relationships, one canonical source. Humans author it as naturally as an outline; agents edit it as precisely as a database. Everything currently maintained by hand — documents, boards, maps, timelines, context windows — becomes a projection that can be regenerated at will.**

The founding philosophy survives critique unchanged:

> **Store knowledge once. Render it infinitely.**

With one addition, from C2:

> **Touch knowledge atomically. Never regenerate what you can address.**

## 3. The layered stack

`.sarib` is specified as five layers. Lower layers are frozen earlier and change slower.

| Layer | Name | Defines | `.sarib`'s position |
|---|---|---|---|
| L4 | **Surface** | What humans type and read | One canonical text form + a forgiving authoring dialect (C4) |
| L3 | **Operations** | Atomic edits + queries — the AI protocol | An op vocabulary (create/update/link/move/merge/split…), transport-agnostic |
| L2 | **Semantics** | Types: node kinds, relationship kinds, schemas, extensions | Small core ontology + namespaced, gracefully-degrading extensions |
| L1 | **Data model** | The shape of knowledge: nodes, edges, containment, order, metadata | Typed property graph with ordered containment *(provisional — Stage 4 decides)* |
| L0 | **Substrate** | Bytes, files, history | UTF-8 plain text, git-compatible. **Not redefined** — we inherit, not reinvent |

The stack is the philosophy applied to itself: the abstract model (L1–L2) is the specification's primary object; the canonical file (L4) is its serialization; every other view — including what an agent sees in its context window — is a projection.

## 4. Design tensions and stances

Honest philosophy is a list of tensions with chosen sides, not a list of virtues. Each stance below is provisional and carries its reversal condition. Stage 2 gathers the evidence; Stage 3 ratifies or reverses.

| # | Tension | Stance (provisional) | Reversed if… |
|---|---|---|---|
| T1 | Graph-native vs human-writable | **Humans write trees, think graphs.** Authoring is local hierarchy (outlines) plus lightweight links; the canonical form is a graph rendered as tree-with-references. ID ceremony is the enemy. | User testing shows reference syntax, not IDs, is the real bottleneck |
| T2 | Semantic richness vs ceremony | **Progressive formalization.** Untyped text is valid `.sarib`; adding a type is one gesture; schemas are optional but checkable. RDF front-loaded formality and lost authors; Markdown refused formality and lost machines. The dose makes the poison. | Evidence that untyped islands rot into unqueryable mush in real corpora |
| T3 | Token economy | **Interaction over compression.** Optimize subgraph retrieval and delta writes; syntax density is a tiebreaker (C2). | Benchmarks show syntax overhead dominating real agent workloads |
| T4 | Canonical source vs projections | **Projections carry identity.** Every projected element keeps its node ID so edits in any view map back losslessly. Lossy projections are permitted but must self-declare. | Identity-carrying makes projections unusably noisy for humans |
| T5 | File vs database | **The file is the truth; indexes are disposable.** Partial loading and querying are tooling features enabled by format design (sectionable, streamable), not reasons to make a database canonical. | Multi-agent write throughput forces a live store as truth (file demotes to snapshot/journal — still specified) |
| T6 | Determinism vs extensibility | **One byte-stable normal form; namespaced extensions that degrade gracefully.** Unknown types must still parse, render generically, and round-trip untouched. HTML's forgiveness bought adoption and cost decades of parser divergence — we take strictness in the canonical form and pay tolerance in the dialect (C4). | Strictness measurably kills hand-authoring even with the dialect layer |
| T7 | Concurrency | **v1 targets clean git 3-way merges** (stable IDs + normalized form). The op vocabulary is designed so a CRDT/OT layer can be added *without changing the model*. | Agent-swarm concurrency becomes a v1 requirement |
| T8 | Provenance | **Every assertion is attributable.** Human statement, agent inference, and imported fact are distinguishable at the model level; trust is queryable (C6-3). | Attribution overhead proves heavier than its value in single-author use |

## 5. Success criteria (falsifiable)

The brief's success criteria restated as tests. Targets are provisional *(ratified in Stage 3, measured per Rule 6)*.

| # | Claim | Test | Target |
|---|---|---|---|
| S1 | Lossless projections | Property-based round-trip: model → view → model, ≥5 view types | 100% semantic equality |
| S2 | Edit efficiency | Token cost of a point edit on a ~10k-token knowledge base, op vs regeneration | ≤1% of full regeneration |
| S3 | Cold human readability | Spec-naive readers answer structural questions from a raw file | ≥90% accuracy |
| S4 | Cold agent readability | LLM relationship-query accuracy vs same knowledge in Markdown | Strictly better, at equal or lower token cost |
| S5 | Mergeability | Concurrent non-overlapping edits, plain git 3-way, no custom driver | ≥95% auto-merge; 0% silent corruption |
| S6 | Implementability | Independent parser written from spec alone | One developer, one weekend, ≤1000 LOC (the "JSON simplicity test") |

S6 deserves emphasis: JSON beat XML in large part because Crockford could fit the grammar on a business card. Every feature this project adds must be weighed against S6.

## 6. Research questions for Stage 2

Stage 2 is not a survey; it is targeted evidence-gathering for the tensions above.

| RQ | Question | Feeds |
|---|---|---|
| RQ1 | How do surviving systems solve **stable identity** in human-editable text (git objects, RDF IRIs, org-mode IDs, Notion blocks, CRDT IDs)? What ID schemes do humans actually tolerate? | T1, T4, C6-1 |
| RQ2 | Why did RDF/OWL/semantic web **stall** while schema.org, JSON-LD, and property graphs spread? What is the adoption-compatible dose of formality? | T2, R1 |
| RQ3 | Why did **Markdown win** despite semantic poverty? Where are the ceilings of plain-text friendliness (org-mode, AsciiDoc, reST trajectories)? | T1, T2 |
| RQ4 | What exists for **graphs-as-text** (Turtle, Cypher, DOT, Mermaid, KDL, GraphViz) and why is none of them the default knowledge medium? | T1, T6 |
| RQ5 | Which systems promised **single-source-many-views** (XML+XSLT, org-mode export, Notion, Jupyter, literate programming) and where exactly did round-tripping break? | T4 |
| RQ6 | What should the op vocabulary and merge story **steal from CRDTs** (Automerge, Yjs), OT, Datomic's immutable facts, and event sourcing? | T7, C3 |
| RQ7 | What is the current **evidence on LLMs and structured text**: do graphs-as-text improve retrieval/reasoning over prose (GraphRAG et al.)? Which formats do models parse most reliably? | T3, S4 |
| RQ8 | What do **winning open standards** share (JSON, Markdown, HTTP) versus losers (XHTML 2, XML-for-data, RDF), and which adoption preconditions must be designed in? | C6-4, R5 |

## 7. Amendments and open items

- Decisions D-001 through D-005 logged in `decisions/decision-log.md`.
- Open: whether "authoring dialect + canonical form" (C4) is one spec or two. Deferred to Stage 9/10.
- Open: minimum viable core ontology size (T2). Deferred to Stage 5 with Stage 2 evidence.
- This document is unratified until Stage 2 critiques it.

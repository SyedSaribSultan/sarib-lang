# Stage 12 — Rendering Architecture

**Status:** Draft v0.1 — open for critique by Stage 13 · **Date:** 2026-07-15
**Input:** Stage 11 §9 brief; principles P1–P17; decisions D-001…D-051
**Decisions logged:** D-052 … D-054 (this stage)
**Phase:** D (Human Surface), stage 3 of 3 — **this stage closes Phase D.**
**Scope:** How the one canonical model becomes the many views the brief demands — documents, outlines, mind-maps, dependency graphs, boards, timelines, tables, slides, and an AI context window. This is where "store knowledge once; render it infinitely" (P1) becomes an architecture.

---

## 1. Critique of Stage 11

Stage 11 nailed validation but assumed, without stating, that rendering is a *pure read* — that a projection never mutates the model. That assumption is exactly where every prior single-source-many-views system died (Stage 2 §2.3): the moment a view quietly became a second edit surface, round-trip broke. So Stage 12's first duty is to make the read/write status of every projection **explicit** (a view is a live window *or* an honestly-terminal export — never an ambiguous middle) — D-053. Second, Stage 11's derived spatial cues (D-047) were defined but not *placed*: rendering is where they're computed and shown, and different views need different cues (a board wants counts; a timeline wants dates). No principle reversed.

---

## 2. Projection = query + template (D-052)

A view is not a stored artifact and not a special engine. It is:

> **projection = a query (Stage 7) that selects a subgraph + an ordering, and a template that maps each node/edge to presentation, carrying every node id through.**

This falls straight out of the model:

- The **query** (self-hosted, D-030) picks *what* is shown and in *what order* — using the seven traversal axes (D-026). The document view is the containment spanning-tree walk (Stage 4 §6); a board groups tasks by `status`; a timeline orders `event`/`due` by `timestamp`; a dependency graph follows `depends-on`; a mind-map walks containment + cross-refs from a focus node.
- The **template** maps model elements to a target medium (Markdown/HTML/SVG/DOM/tokens) — pure, stateless, `element → presentation`.
- **Every projected element carries its node/edge id** (P8/D-033) — the property that makes a view addressable and (if live) writable.

So the same 13 brief-traversals-as-queries (Stage 6) become the 13-plus rendering targets, with zero new model machinery. The projections the brief lists (documents, trees, mind maps, dependency graphs, whiteboards, kanban, timelines, presentations, AI context windows, databases, spreadsheets, flowcharts) are each a (query, template) pair.

| Brief view | Query (select · order) | Template |
|---|---|---|
| Document | containment tree · document order | prose/Markdown |
| Outline / mind-map | containment (+ cross-refs from focus) · depth | nested list / radial |
| Dependency graph / flowchart | `depends-on`/`blocks` · topological | node-link (Mermaid/DOT projection) |
| Kanban board | `type=task` · group by `status` | columns |
| Timeline | timestamped nodes · by `timestamp` | lanes |
| Table / spreadsheet | a node set · by property | rows×columns of properties |
| Presentation | top containment level · document order | slides |
| **AI context window** | a bounded subgraph (D-028) · relevance | minimal-projection tokens |

The last row matters most for this project: **the agent's context window is just another projection** — a bounded, minimally-projected subgraph (Stage 7 §5). Rendering-for-humans and rendering-for-agents are the same operation with different templates and token budgets. That is the deepest expression of "AI and human read the same knowledge."

---

## 3. Live windows vs terminal exports (D-053; resolves C1)

Every projection declares its edit-flow status — the lesson that decides whether round-trip holds (Stage 2 §2.3):

- **Live window** — rendered in a `.sarib`-aware tool; every element carries its id, so an edit in the view is an **operation** (Stage 8) addressed by that id (D-033). Editing a card's title on a board, checking a task in an outline, dragging a node in a mind-map → `set-property`/`move`/`retract` on the model. No re-parsing, no regeneration (D-002). This is Notion's "views are configurations over one store" (Stage 2 §2.3) — but over a plain-text file.
- **Terminal export** — rendered to a foreign format (a PDF, a static HTML site, a `.pptx`, a PNG of a graph). Explicitly **read-only**: it does not carry a back-channel and must self-declare as terminal (P17). Edits happen in `.sarib`, then re-export. This is the honest one-way contract (Knuth's TANGLE, DITA-OT; Stage 2 §2.3) that keeps consistency by construction.

The fatal zone — a view that *looks* editable but silently can't flow back (Jupyter-in-git, Notion's re-imported export) — is **forbidden**: a projection is one or the other, and says which (P17). Lossy live views may *hide* fields but never *drop* them (D-009/P17).

---

## 4. Spatial-cue rendering (D-054; places D-047)

Rendering computes the derived legibility cues (D-047) per view, from the model, on demand:

- **Skeleton / map first:** every view can emit a typed table-of-contents (headings + counts) before detail — the Skeleton-of-Thought / RAPTOR benefit for agents, the "map before territory" sense-of-place for humans ([research §Q1]). For the AI-context projection this is the cheap high-scent header an agent reads before deciding what subgraph to pull.
- **Shape at every container:** statistics cookies `[k/n]`, subtree-size badges, ordinal position, fold/`…` markers — computed from the containment tree, shown inline (D-047). A human feels the spread; an agent gets explicit counts instead of having to infer extent.
- **Per-view cue selection:** a board shows per-column counts; a timeline shows span/density; an outline shows depth + child counts; the document shows a TOC. Same derived data, view-appropriate presentation.
- **Cues are always derived, never authored** (P17/D-051): recomputed each render, so they can never be stale-in-the-model. Stable ids double as spatial anchors ("where am I / return here").

This is the concrete delivery of the user's "spatial idea of the information" requirement: the model holds the tree; every projection paints its shape and size in the idiom that view affords.

---

## 5. Streaming, partial, deterministic (P14/D-044/P15)

- **Partial render** (D-044): a projection renders a bounded subgraph (a query result + cursor) without loading the whole model — the same minimal-context economy on the render side as on the read side (P14; length degradation, [ai-context.md]).
- **Streaming:** because parsing is local (P15) and content is document-ordered, a view streams top-to-bottom; large views page via the cursor.
- **Deterministic** (P14/D-029): same (model, view spec) → identical rendering, byte-for-byte for text targets — so renders are cacheable and diffable, and two tools agree.
- **Incremental:** an operation (Stage 8) invalidates only the projected elements whose ids it touched, so a live view updates the changed cards, not the whole board (the render-side twin of atomic edits).

## 6. Phase D exit check

Charter Phase D exit criterion: *"≥2 competing syntaxes tested against the writability criteria before one is chosen."* Status: **met** — Stage 10 designed Candidates A and B, evaluated them on the writability criteria (§6 there), recommended A, and shipped both as judgeable packages (`examples/`). Validation (Stage 11) and rendering (Stage 12) complete the human surface:

**The full stack now stands:** model (B) → operations + serialization (C) → author surface + validation + rendering (D). Knowledge is stored once as an identified property graph, edited atomically by id, serialized canonically, authored in a pleasant Markdown-superset, validated forgivingly, and projected into every view the brief named — each view a (query, template) pair carrying ids so live views flow back. Phase E can now build the reference implementation and freeze the spec.

## 7. New decisions

- **D-052** — A projection is `query (subgraph + order) + template (element→presentation)`, every projected element carrying its node/edge id. All brief views (document, outline, graph, board, timeline, table, slides, **AI context window**) are (query, template) pairs over the one model — no per-view engine. The agent's context window is a projection like any other.
- **D-053** — Every projection declares edit-flow status: **live window** (edits become id-addressed operations, D-033) or **terminal export** (read-only, self-declared, re-export to change). The ambiguous-editable-but-no-backchannel middle is forbidden (P17); lossy live views hide but never drop fields.
- **D-054** — Rendering computes derived spatial cues per view (skeleton/TOC, `[k/n]` counts, subtree size, ordinal, fold markers, container summaries) from the model on demand; cues are view-appropriate, always regenerated, never authored or canonical; ids double as spatial anchors.

## 8. What Stage 13 (Reference Implementation Architecture) must deliver

Phase E opens. Stage 13 specifies the buildable system:

1. **Component architecture:** parser → normalizer → model store → op engine → query engine → projector, plus a schema/validator — each mapping to a stage (10, 9/11, 4, 8, 7, 12, 5/11).
2. **The business-card parser** (S6): a conforming Tier-0/1 parser in ≤~1000 LOC, one developer, one weekend.
3. **The day-one consumer** (RD2/RD1): a reference MCP server + CLI that reads, queries, edits (ops), and projects — so the format ships with a consumer, not just a spec (the AGENTS.md-not-llms.txt lesson).
4. **The benchmark harness** (RP3/RA2): measure token-per-interaction and read/write accuracy vs Markdown *before* spec freeze — the existential-risk instrument.
5. **Conformance test corpus** (RG2): input→expected(model, canonical form, diagnostics) pairs shipped with v0.1.

## 9. Risks surfaced

- **RH2 / RD1 (render-side mitigation):** live writable projections (D-053) are what make the format *pay off per edit* for its author — the incentive that the existential adoption risks require. A board you can edit that saves back to plain text is the "immediate selfish payoff" (Stage 2 §2.1) that drove schema.org/Wikidata adoption.
- **RM21 (new)** — live-view edit ambiguity: a coarse view (e.g., a summary card) may not expose enough to disambiguate which model element an edit targets. *Mitigation:* every projected element carries its id (D-052), so the target is explicit even when the display is coarse; edits that can't be attributed to an id are rejected (surfaced as a diagnostic), never guessed. Low/medium.

This document is unratified until Stage 13 critiques it.

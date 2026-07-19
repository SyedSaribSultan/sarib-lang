# Stage 10 — Syntax Proposals

**Status:** Draft v0.1 — open for critique by Stage 11 · **Date:** 2026-07-15
**Input:** Stage 9 §12 brief; principles P1–P17; decisions D-001…D-044; `research/syntax-and-legibility.md`
**Decisions logged:** D-045 … D-048 (this stage)
**Phase:** D (Human Surface), stage 1 of 3 — **the "no author syntax" red line lifts here.**
**Scope:** The author-facing surface — what a human types and reads. Per the charter's Phase D exit criterion, this stage designs **two competing syntaxes**, tests them on writability, and recommends one; both are shipped as independently-judgeable example packages in `examples/`. Validation (Stage 11) and rendering (Stage 12) follow.

---

## 1. Critique of Stage 9

Stage 9 was solid and even over-delivered on one axis Stage 10 must respect: it made JSON the canonical/interchange encoding, which raises **RD6** — if the surface is unpleasant, people will just write the JSON and the human-writable goal dies. So the bar for this stage is higher than "a syntax": it must be a surface people *prefer* to the JSON they could otherwise use. Two other inheritances: Stage 9's canonical form (D-041) means the surface is a *third* serialization that must normalize to it losslessly (a parser + normalizer obligation, not a syntax obligation); and Stage 9's determinism must not be undermined by surface ambiguity (so we take djot's no-backtracking discipline). No principle reversed.

The user's goal statement adds an explicit requirement the earlier stages under-served: **spatial legibility** — the surface must let human *and* model perceive the shape, spread, and depth of the knowledge (where am I, how big is this, how deep does it go). §5 addresses it directly; it is the one genuinely novel contribution of this stage.

---

## 2. Shared surface principles (both candidates obey these)

From the ratified principles and `research/syntax-and-legibility.md`, both candidates share:

- **CommonMark superset** (P6/D-006): a `.sarib` file renders acceptably in any Markdown renderer; unknown constructs degrade to harmless literal text, never a hard break. Adopt **djot's discipline** (unambiguous single-char emphasis, attributes-on-any-element, no-backtracking locality) but **not djot's format** (it's a replacement, not a superset) — [research §Q3].
- **Prose is the surface; structure is progressive** (P3, P9): pure Markdown prose is valid L0 `.sarib`; every structural mark is optional and additive.
- **Edges emerge from prose** (P4/D-012): inline typed links inside sentences, with a Markdown-safe fallback.
- **Containment from nesting** (P5/D-013): headings and list indentation compile to containment edges — zero ceremony.
- **Ids without ceremony** (P8/D-009): humans write names; a block id (`^id`-style) is tooling-managed and quarantined; slugs are the only id that may appear in prose.
- **Single-token, in-distribution glyphs** (research §Q2): structural sigils drawn from the cheap ASCII set Markdown already uses (`#  -  *  >  :  |  ^  [ ]`); **any multi-char sigil is measured against real tokenizers before freeze** (Evidence rule; RP3).
- **Importance is a field, not typography** (research lesson 6): priority/weight is an addressable attribute (queryable, survives projection); emphasis glyphs (`*`, `_`) are for human scanning only, never load-bearing semantics.
- **Forgiving surface, deterministic parse** (P15): everything parses to a model (prose → L0 nodes); validity is lint-grade (Stage 11).

Both candidates encode the **same model** and normalize to the **same canonical form** (D-041). They differ only in the surface trade-off: **familiarity/adoption vs. density/compactness.**

---

## 3. Candidate A — "Prose-native" (Markdown-maximal) · RECOMMENDED

Optimizes **writability + adoption + formatting expressiveness**. Maximally CommonMark; a `.sarib` file *is* a Markdown document with typed structure layered in via widely-deployed attribute conventions (Pandoc/MyST/Dataview) that degrade gracefully.

Surface conventions (illustrative — the model is what's normative):

- **Containment:** Markdown headings for major structure; list nesting for finer. Depth = heading level / indentation.
- **Node type:** a trailing attribute on a heading/list-item — `## Migrate invoices {.task}` (Pandoc attribute; renders as text in vanilla Markdown, styled by aware tools).
- **Identity / slug:** `{#migrate-invoices}` in the same attribute block (Pandoc id); or a trailing `^id` for blocks. Tooling assigns opaque ids; the visible slug is optional.
- **Properties:** Dataview-style inline fields — `due:: 2026-08-01`, `priority:: high` — either on their own line or bracketed inline `[due:: 2026-08-01]`. A whole-line `key:: value` is a property of the enclosing node.
- **Edges (inline, prose-embedded):** the Obsidian-fallback pattern — `Blocked by [depends-on:: [[Adopt billing provider]]]`. In a vanilla renderer this shows readable text; an aware parser reads a typed edge. Untyped links `[[Target]]` become `relates-to` edges.
- **File metadata:** YAML front matter (`--- … ---`) for vocabulary pin, schema, etc.
- **Emphasis / hierarchy:** ordinary Markdown `**bold**`, `*italic*`, heading levels, lists — for human scanning; semantic importance lives in `priority::`.

**Why recommended:** the priority order is *integrity > human writability > machine efficiency > completeness* (Stage 3 §4). A wins decisively on writability and on the carrier bet (P6) — it renders in every Markdown tool today and looks like what humans and LLMs already emit, so it stays in the pretraining distribution. Its token cost is higher than B's, but the research shows dense/novel notations pay an accuracy tax that usually exceeds their savings ([ai-context.md]; TOON −9pp), and the real token win is interaction-level (ops, D-002), not surface density (D-002/RA2). A can borrow B's best idea — compact spatial cues (§5) — without B's out-of-distribution cost.

---

## 4. Candidate B — "Outline-dense" (token-minimal)

Optimizes **token density + depth legibility**. An indentation-structural outline: one node per line, indentation = containment, terse leading sigils for type, compact edge notation, explicit dotted-path depth cues.

Surface sketch (illustrative):

- **Containment:** pure indentation (2 spaces = one level); each line is a node.
- **Node type:** a leading sigil/word — `@task Migrate invoices` — chosen from the single-token set.
- **Properties:** trailing compact fields — `@task Migrate invoices | due=2026-08-01 pri=hi`.
- **Edges:** compact inline — `> dep #adopt-billing` (a typed edge line under the node).
- **Depth cue:** optional dotted path (`1.2.1`) so depth survives without counting columns (research lesson 10).
- **Ids:** trailing `^id`.

**Trade-offs:** B is ~20–35% fewer tokens than A on structure-dense content *(estimate — benchmark per RP3)* and its clean indentation gives excellent depth-at-a-glance. But: it is **not** CommonMark-renderable (it won't display in a Markdown tool — forfeiting the carrier), it sits further out of the pretraining distribution (the accuracy tax, ai-context.md), and pure significant-whitespace risks LLM indentation-drift on write (research lesson 10). It optimizes the axis (machine efficiency) that the priority order ranks *third*.

---

## 5. Spatial legibility — the shape/size affordances (D-047)

The novel requirement: convey the *spatial idea* of the knowledge — spread, depth, size, position — to both human and model, cheaply. Grounded in information-foraging theory (readers descend by **scent** — proximal cues predicting distal value — [Pirolli & Card](http://act-r.psy.cmu.edu/wordpress/wp-content/uploads/2012/12/280uir-1999-05-pirolli.pdf)) and the finding that a structural **map-before-detail** helps models too (Skeleton-of-Thought, RAPTOR — [research §Q1]).

`.sarib` conveys shape with four **derived, optional** annotations (derived-layer, P17/D-019 — they never fight determinism and are regenerated, not authored):

| Property | Compact encoding | Precedent |
|---|---|---|
| **Depth** (how deep am I) | indentation + optional dotted path `1.2.1` / breadcrumb | outliners, headings |
| **Breadth/size** (how much below) | org-style statistics cookie `[k/n]` or subtree count badge `⊕128` on a container | [org cookies](https://orgmode.org/manual/Breaking-Down-Tasks.html) |
| **Position** (where among peers) | ordinal `3/7` | pagination, breadcrumbs |
| **Hidden content** | fold glyph / trailing `…` | all outliners |

Two further affordances, both derived projections:

- **Skeleton / map:** a generated typed table-of-contents (headings + counts) that an agent or reader sees *before* the detail — the SoT/RAPTOR benefit baked into the format rather than recomputed per query.
- **Container summaries:** an optional one-line summary property on container nodes (the RAPTOR abstraction level), so scent is strong at every level.

Because these are derived (computed from the model), they cost the author nothing and never desync: the canonical form stores the tree; the counts/skeleton/summaries are projected on demand. Stable ids double as **spatial anchors** (research lesson 4) — "where am I / how do I get back here" for humans, subgraph addresses for agents.

---

## 6. Evaluation (writability test — charter Phase D gate)

Same knowledge (the Stage 4 "Q3 Planning" graph) rendered in both candidates (see `examples/`), scored against the goal:

| Criterion (weight by priority order) | A · Prose-native | B · Outline-dense |
|---|---|---|
| **Integrity** (normalizes to canonical form, deterministic parse) | ✓ (djot discipline) | ✓ |
| **Human writability** (S3 cold readability, hand-authoring) | **High** — familiar Markdown | Medium — new outline conventions |
| **Renders in existing Markdown tools** (carrier, P6) | **Yes** | No |
| **In-distribution for LLMs** (read/write accuracy) | **High** | Medium (OOD tax) |
| **Token density** (machine efficiency, ranked 3rd) | Medium | **High** (~20–35% leaner, est.) |
| **Spatial legibility** (§5) | High (with §5 cues) | **High** (clean indentation) |
| **Formatting expressiveness** (emphasis/hierarchy/importance) | **High** (full Markdown + `priority::`) | Medium |

**Recommendation: Candidate A, augmented with B's spatial cues (§5) and explicit-depth option.** It wins on the three highest-priority axes (integrity, writability, carrier) and closes most of the gap on the fourth (density) via interaction-level efficiency (ops) rather than surface compression. B is retained as a documented alternative and as the basis of a future *compact profile* (a lossless denser encoding for token-critical agent-to-agent exchange) — not the default author surface.

Both are shipped as example packages so the choice is independently judgeable (D-048): `examples/A-prose-native.sarib` and `examples/B-outline-dense.sarib` encode identical knowledge; `examples/README.md` is the comparison.

---

## 7. New decisions

- **D-045** — The author-facing surface is a **CommonMark superset** taking djot's discipline (unambiguous glyphs, attributes-on-any-element, no-backtracking locality) but a Pandoc/MyST/Dataview-compatible surface that degrades to literal text in vanilla renderers. **Candidate A (prose-native) is the recommended default;** Candidate B (outline-dense) is retained as an alternative / future compact profile.
- **D-046** — Surface conventions: headings+list-nesting → containment; trailing `{.type #slug}` attributes → node type/slug; `key:: value` inline fields → properties; `[rel:: [[Target]]]` → typed edges (untyped `[[Target]]` → `relates-to`); `^id` → block identity; YAML front matter → file metadata. All measured against real tokenizers before freeze (RP3).
- **D-047** — Spatial legibility is delivered by **derived, optional** annotations — statistics-cookie counts `[k/n]`, dotted-path/breadcrumb depth, ordinal position, fold/`…` markers, a generated typed skeleton/TOC, and container summaries — never authored, never canonical, regenerated on demand (P17). Stable ids double as spatial anchors.
- **D-048** — Importance/priority/weight is an **addressable field** (`priority::`), queryable and projection-stable; typographic emphasis (`*`,`_`,`**`) is for human scanning only and carries no load-bearing semantics (models read emphasis weakly). Two full syntaxes are shipped as independently-judgeable example packages.

---

## 8. What Stage 11 (Validation Rules) must deliver

1. **The three tiers:** *well-formed* (parses to a model at all — always succeeds, prose → L0), *schema-valid* (conforms to an active vocabulary schema, D-023), *lint* (style/consistency/spatial-cue staleness). All non-fatal except un-parseability, which the forgiving surface (P15) essentially precludes.
2. **Surface→model normalization rules:** how each Candidate-A construct maps to nodes/edges/properties and to the canonical form (D-041); ambiguity resolution (djot no-backtracking).
3. **Diagnostics:** unresolved references (D-024), cardinality/type violations (D-023), duplicate slugs, cycle-in-acyclic-edge (D-027) — as lint, with locations.
4. **Round-trip guarantee:** surface → model → canonical → surface is stable (idempotent normalization), the writability-layer analogue of D-040.

Then Stage 12 (rendering) and the Phase D close.

## 9. Risks surfaced

Filed in `../risks/risk-register.md`:

- **RD6 (reaffirmed, mitigation strengthened)** — JSON-as-format temptation: Candidate A is explicitly the pleasant surface that makes writing `.sarib` preferable to writing the JSON; adoption depends on A being genuinely nicer.
- **RA11 (new)** — surface glyph tokenization unverified: chosen multi-char sigils (`::`, `[[`, `{#`, `^`) must be confirmed single-token in target tokenizers before freeze; if they fragment, revise glyphs (research §Q2; RP3). Medium.
- **RH8 (new)** — attribute/inline-field ceremony (`{.task}`, `key::`) may still feel like "filling a database" to some authors, re-raising RH1/RH2; mitigation: keep all of it optional (L0 prose valid), let the agent add most structure (D-010), test hand-authoring cost. Medium.

This document is unratified until Stage 11 critiques it.

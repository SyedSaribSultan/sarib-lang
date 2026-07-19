# .sarib — Project Charter

**Version:** 0.1 · **Date:** 2026-07-14 · **Status:** Active

## Mission

Design and specify an AI-native knowledge representation language: a single semantic source of truth that humans read and write as plain text, AI agents read and edit through atomic operations, and from which documents, graphs, boards, timelines, and context windows are all generated projections.

The outcome is an **open standard and reference architecture** — not a product.

## Non-goals

- Not a note-taking app, PKM tool, or SaaS. No UI product ships from this project.
- Not a Markdown replacement for prose-first writing. Prose documents remain a projection target, not a competitor.
- v1.0 excludes: sync services, real-time collaboration servers, GUI editors, binary encodings. Any of these may become companion specs later.

## Deliverable map

The brief lists 15 deliverables. They are dependency-grouped into five phases. Each stage opens by critiquing its predecessor (Operating Rule 1).

| Phase | Stages (from brief) | Output | Exit criteria |
|---|---|---|---|
| **A · Foundations** | 1 Vision · 2 Prior art · 3 Design principles | The why and the constraints | Principles ratified; kill criteria (Rule 5) evaluated against evidence |
| **B · Semantic core** | 4 Core object model · 5 Abstract semantic model · 6 Traversal model · 7 Query model | The abstract machine | All 13 traversals from the brief expressible as queries over the model |
| **C · Machine interface** | 8 AI interaction protocol · 9 Serialization strategy | How agents touch knowledge | Atomic op set closed under composition; op-log ↔ state equivalence demonstrated |
| **D · Human surface** | 10 Syntax proposals · 11 Validation rules · 12 Rendering architecture | What people see and type | ≥2 competing syntaxes tested against writability criteria before one is chosen |
| **E · Standardization** | 13 Reference implementation architecture · 14 Language specification · 15 v1.0 proposal | The standard | Spec independently implementable; conformance test suite defined |

**Why this grouping:** syntax (Phase D) is a projection of the model (Phase B) — the project's own philosophy applied to its own process. Formats that decided surface before semantics accreted accidental complexity; YAML is the cautionary tale. Semantics first, surface last.

## Operating rules

1. **Critique-first.** Every stage document begins with a critique of the previous stage. Accepted amendments are logged. No stage is final until its successor has critiqued it.
2. **Decision log.** Design decisions are recorded as `D-###` entries in `decisions/decision-log.md`: context, options considered, choice, and explicit reversal conditions.
3. **No syntax before Phase D.** Syntax sketches are permitted only inside clearly-marked thought experiments. Rationale: premature syntax anchors thinking and forecloses the design space — the brief itself demands this.
4. **Evidence rule.** Factual claims about prior systems require citations. Design opinions are labeled as stances with reversal conditions. No unsourced history.
5. **Kill criteria.** If Stage 2 research shows an existing stack (e.g., a JSON-LD profile, a property-graph text format, an org-mode extension) satisfies ≥90% of ratified requirements, `.sarib` pivots to a **profile or binding of that stack** rather than a new language. Inventing a language is the last resort, not the goal. This rule exists to enforce the brief's instruction: challenge all assumptions, including the founding one.
6. **Measurement rule.** Claims like "token efficient" must be benchmarked against baselines (Markdown, JSON), not asserted. Benchmark harness is a Phase C deliverable, before spec freeze.

## Risk register

**The canonical, living risk register is `risks/risk-register.md`** (established session 3). It absorbs the five founding risks below plus every risk added in later stages, adds a forward-looking sweep across eight categories (model, human, AI, adoption, governance, longevity, security, process), and carries likelihood × impact, phase-when-it-bites, early-warning signals, mitigations, and status for each. Update that file, not this table.

The five founding risks (now migrated — see the crosswalk in the register §12):

| # | Risk | → register |
|---|---|---|
| R1 | Rediscovering RDF, badly | RP1 — mitigated (Stage 2 §3) |
| R2 | Graph purity destroys human writability | RH1 — mitigated (P3/P4) |
| R3 | Boil-the-ocean scope | RP2 — mitigated (scope cap: core + op vocab + 3 projections) |
| R4 | Efficiency claims don't survive measurement | RP3 — open (needs benchmark harness, Rule 6) |
| R5 | Technically sound, socially dead | RD1 — watch (existential) |

The register's headline finding: **the lethal risks are not technical.** The model problems are largely resolved; the killers are human (will people enrich? RH2), distributional (will agents and tools adopt it? RD1/RA1/RA2), and safety (prompt injection via file content, RS3).

## Cadence

One stage (or one coherent chunk of a stage) per working session. Session log lives in `README.md`. Do not optimize for speed; optimize for the thing surviving contact with Stage N+1's critique.

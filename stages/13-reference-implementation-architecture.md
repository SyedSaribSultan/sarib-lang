# Stage 13 — Reference Implementation Architecture

**Status:** Draft v0.1 — open for critique by Stage 14 · **Date:** 2026-07-15
**Input:** Stage 12 §8 brief; principles P1–P17; decisions D-001…D-054
**Decisions logged:** D-055 … D-057 (this stage)
**Phase:** E (Standardization), stage 1 of 3 — Phase E opens.
**Scope:** The architecture of a buildable reference implementation — components, interfaces, the parser LOC budget, the day-one consumer, the benchmark harness, and the conformance corpus. This is *architecture*, not the code; but it must be concrete enough that an engineer could build it and that S6 (a conforming parser in a weekend) is demonstrably reachable.

---

## 1. Critique of Stage 12

Stages 4–12 are a complete paper design — and that is precisely the danger. The register's existential risks (RH2, RA1, RA2, RD1) all share one property: **none can be tested on paper.** Every one only produces real signal from a running implementation with a benchmark. So Stage 13's job is not to add design — it is to specify the smallest system that turns the paper into measurable reality, and to make the consumer ship *with* the spec (the AGENTS.md-not-llms.txt lesson, Stage 2 §2.2). If Phase E produces a spec but no consumer and no benchmark, the project has optimized the recoverable risks and ignored the fatal ones (register §10). This stage is aimed at the fatal ones. No principle reversed.

---

## 2. Component architecture (D-055)

Six components, each the executable form of one stage. Data flows in a loop, not a pipeline — the read→reason→edit→re-render loop (Stage 7 §8).

```
            author text (Stage 10)                canonical form / op-log (Stage 9)
                    │                                        ▲
                    ▼                                        │
   ┌──────────┐   ┌──────────────┐   ┌───────────┐   ┌──────────────┐
   │  Parser  │──▶│  Normalizer  │──▶│   Model   │◀─▶│  Serializer  │
   │ (S10→model)│   │ (→canonical) │   │  Store    │   │ (canon+log)  │
   └──────────┘   └──────────────┘   │ (Stage 4) │   └──────────────┘
                                      └─────┬─────┘
                        ┌───────────────────┼───────────────────┐
                        ▼                   ▼                   ▼
                  ┌───────────┐      ┌───────────┐      ┌────────────┐
                  │ Op Engine │      │  Query    │      │ Projector  │
                  │ (Stage 8) │      │ Engine    │      │ (Stage 12) │
                  │ +validate │      │ (Stage 6/7)│      │ views      │
                  └───────────┘      └───────────┘      └────────────┘
                        │                   │                   │
                        └──────── consumer: MCP server + CLI ───┘
```

| Component | Realizes | Core responsibility | Interface (abstract) |
|---|---|---|---|
| **Parser** | Stage 10, Tier 0/1 | total surface→model (prose→L0, no-backtracking, local) | `parse(bytes) → (model, diagnostics)` |
| **Normalizer** | Stage 9/11 | model→canonical form; idempotent (D-051) | `canon(model) → bytes` |
| **Model Store** | Stage 4 | hold nodes/edges; enforce the 10 invariants | `get(id)`, `apply(op)` |
| **Op Engine** | Stage 8 | apply ops (primitives+composites), preconditions, fold op-log | `apply(op) → (Δ, diagnostics)`; `fold(log) → model` |
| **Query Engine** | Stage 6/7 | the parameterized walk + filter; bounded result subgraph + cursor | `query(spec) → result` |
| **Projector** | Stage 12 | (query, template) → view; ids carried; live vs terminal | `render(view-spec) → presentation` |
| **Validator** | Stage 5/11 | closed-world schema check; diagnostics | `validate(model, schemas) → diagnostics` |

Two properties make this small: the **Query Engine and Projector are one mechanism** (a view is a query + template, D-052), and the **Validator and Op Engine share the invariant checks** (an op is rejected iff it would break an invariant, RM14). So the "six components" are really parser + normalizer + store + op/validate + query/project.

---

## 3. The business-card parser (D-056; S6)

S6 (the JSON-simplicity test) is a first-class requirement, not an aspiration: **a conforming Tier-0/1 parser must be writable by one developer in a weekend, ≤~1000 LOC.** What makes it reachable:

- **Total, local, no-backtracking** parsing (D-045/D-049): every line is classified by its shape alone; unrecognized → L0 prose node. No global disambiguation pass.
- **Small core grammar** (S6/P16): a handful of block constructs (heading, list-item, fenced block, front matter) + inline constructs (typed link, inline field, emphasis) + the one attribute/extension mechanism (D-011). Everything else is vocabulary (D-018), not grammar.
- **JSON reuse** (D-041): the canonical form is canonical JSON, so serialization/deserialization leans on the ubiquitous JSON parser rather than bespoke code.
- **The grammar fits on a card** (Stage 14 delivers it): the parser's size is bounded by the grammar's size, which the priority rule (completeness last) keeps minimal.

A reference parser at this size, in several languages, is itself an adoption instrument — the JSON lesson (a free parser everywhere, Stage 2 §2.2). Target languages for v1: TypeScript (agent/web), Python (data/ML), Rust (performance/embedding).

---

## 4. The day-one consumer (D-057; the RD1/RD2 instrument)

A spec with no consumer is a dead letter (llms.txt: ~0.1% reads; Stage 2 §2.2). So the reference implementation **ships a consumer with v0.1**, in two forms:

- **MCP server** — the agent-native path. Exposes `.sarib` files as MCP resources (addressable, lazily-loaded subgraphs — Stage 7/D-044) and the operation vocabulary (Stage 8) as MCP tools. An agent reads minimal context, edits by id, and re-queries — the whole AI-native loop, through the standard agent protocol the ecosystem already speaks. This is the guaranteed consumer that closes the incentive loop (RH2/RD5): the user's own agent uses every feature the moment a fact is written.
- **CLI** (`sarib`) — the human/git-native path: `parse`, `fmt` (normalize — the gofmt for `.sarib`, D-051), `query`, `apply` (an op), `render <view>`, `validate`, `diff` (canonical). Makes `.sarib` a good git citizen (clean diffs, D-004) and scriptable.

Both are thin shells over the §2 components — they add no model logic, only transport (MCP framing / CLI args). This is D-035's "one protocol, many transports" made real.

---

## 5. The benchmark harness (the existential-risk instrument; RP3/RA2)

The register's most dangerous open risk is RA2 (does `.sarib` actually beat Markdown for LLMs?), and RP3 (efficiency claims must be measured, Rule 6). The harness is therefore a **first-class deliverable, required before spec freeze:**

| Measures | Against baseline | Success target (from Stage 1 §5) |
|---|---|---|
| tokens per point-edit (op vs regenerate) | Markdown/JSON full rewrite | ≤1% of regeneration (S2) |
| relationship-query accuracy | same knowledge in Markdown | strictly better at ≤ token cost (S4) |
| cache-hit rate under an agent edit loop | naïve full-context | high (append-only prefix survives, P14) |
| read/write round-trip accuracy across models | — | high; no format-drift failure (RA1) |
| cold human structural comprehension | same knowledge in Markdown | ≥90% (S3) |
| parser size / build time | JSON | weekend / ≤1000 LOC (S6) |
| **glyph tokenization** of chosen sigils | — | single-token in target tokenizers (RA11) |

The harness turns the paper success criteria (S1–S8) into a red/green dashboard. Freezing the spec (Stage 15) is gated on it — if `.sarib` doesn't beat Markdown here, the thesis is wrong and the design must change, not the benchmark.

---

## 6. Conformance corpus (RG2)

Shipped with v0.1: a set of `input → expected(model, canonical form, diagnostics)` cases, so independent implementations converge instead of diverging (the Markdown-flavor catastrophe, Stage 2 §2.2). Categories: prose-only (L0), each rung (L1–L5), each op, each diagnostic class, round-trip idempotence, canonical-form determinism, safety cases (cycles, expansion bounds, ambiguous encodings — D-043). The corpus *is* the operational definition of "conforming."

## 7. New decisions

- **D-055** — Reference architecture = parser · normalizer · model store · op engine (with validation) · query engine · projector; query+projector are one mechanism (D-052), op+validator share invariant checks (RM14). Each component is the executable form of one stage; data flows in the read→edit→render loop.
- **D-056** — A conforming Tier-0/1 parser is a weekend / ≤~1000 LOC build (S6), made reachable by total+local+no-backtracking parsing, a business-card grammar, and canonical-JSON reuse; reference parsers ship in TS/Python/Rust as adoption instruments.
- **D-057** — The reference implementation ships a **consumer with v0.1**: an MCP server (files as resources, ops as tools — the agent loop) and a `sarib` CLI (parse/fmt/query/apply/render/validate/diff). Both are thin transports over the components (one protocol, many transports). A benchmark harness and conformance corpus are required before spec freeze.

## 8. What Stage 14 (Language Specification) must deliver

The consolidated, standalone, implementable spec: the data model + invariants (Stage 4), semantics + standard vocabulary (Stage 5), traversal + query (6–7), operations (8), serialization + canonical form (9), the author grammar (10) + validation (11) + projection (12), and conformance (13). Written spec-readably (teach-by-example first, conformance language later — the JSON-LD/Swartz lesson, Stage 2 §2.2), with the **business-card grammar** as its centerpiece. Then Stage 15 proposes v1.0 scope, conformance levels, governance, and the adoption path.

## 9. Risks surfaced

- **RP5 (mitigation)** — analysis-paralysis / never shipping: Stage 13 makes the reference implementation + benchmark the gate to v1.0 (Stage 15), forcing the paper design into contact with reality. This is the antidote the register flagged.
- **RA1/RA2/RH2/RD1 (instrumented, still open):** these existential risks remain *open* — but Stage 13 defines the exact instrument (harness §5, consumer §4) that will finally measure them in Phase E execution. They cannot be closed until the implementation runs; naming the instrument is the most this design phase can do.
- **RM22 (new)** — reference-implementation-defines-truth drift: if the spec is ambiguous, implementers will treat the reference code as the spec (Markdown's fate). *Mitigation:* the conformance corpus (§6), not the code, is the operational definition; the reference implementation must itself pass the corpus. Medium.

This document is unratified until Stage 14 critiques it.

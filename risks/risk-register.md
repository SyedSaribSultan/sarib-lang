# .sarib — Consolidated Risk Register

**Status:** Living document · **Established:** 2026-07-15 (session 3) · **Owner:** project
**Supersedes:** the inline risk table in `00-charter.md` (R1–R5) and the ad-hoc `R-new-*` / `OQ*` entries in Stages 3–4. All are migrated here with a crosswalk (§12). This is now the single canonical register; every future stage adds and updates risks here.

## How to use this document

Every risk has: an ID (category-prefixed), a likelihood (L/M/H), an impact (L/M/H), the **phase where it bites** (so it can be watched at the right time), an **early-warning signal** (the observable that says the risk is materializing), a mitigation with the decision/principle that carries it, and a status.

**Severity** = Likelihood × Impact, banded: 🔴 critical (H×H, or existential), 🟠 high, 🟡 medium, ⚪ low/monitored.
**Status:** `open` (no mitigation yet) · `mitigated` (mitigation in place, residual remains) · `resolved` (design closed it) · `accepted` (a deliberate bet we are living with) · `watch` (can't act yet; monitor for the signal).

**Categories:** RM model/technical · RH human factors · RA AI/LLM · RD adoption/distribution · RG governance/ecosystem · RL longevity · RS security/safety · RP process.

Maintenance protocol: (1) each stage's "risks surfaced" section files new risks here; (2) each stage's critique re-checks its cluster; (3) a decision that closes a risk flips its status and links back; (4) nothing is deleted — resolved/retired risks move to §11 with their resolution.

---

## 1. Watch list — the risks that can actually kill .sarib

These six are existential: if any lands unmitigated, the project fails regardless of how good the rest is. Everything else is recoverable. Ordered by how early we get real signal.

| ID | Existential risk | Why fatal | Earliest true signal | The bet / mitigation |
|---|---|---|---|---|
| **RH2** | Humans won't add structure, even with agent help | The founding premise (D-010). If prose never gets enriched, there is no graph — just Markdown with extra steps | First dogfooding: enrichment rate per document over time | Agent does enrichment; every enriched fact pays off *immediately* for its author (schema.org's +82% CTR / Wikidata's in-wiki queries were the only things that drove annotation — [semantic-web.md](../research/semantic-web.md)). Measured, not assumed |
| **RA2** | `.sarib` doesn't beat Markdown for LLMs (accuracy/token) | Removes the reason to be AI-native; a worse Markdown loses | Benchmark harness (Rule 6) before spec freeze — S2/S4/S7 | The win is *tokens-per-interaction* (atomic ops, subgraph fetch), not syntax density (D-002); syntax stays in-distribution (P6). If ops don't win big, reconsider the whole thesis |
| **RD1/RD2** | Technically sound, socially dead / no consumer ships | Formats win on distribution; llms.txt got ~0.1% reads for lack of a consumer ([ai-context.md](../research/ai-context.md)) | v0.1 gate: does a reference reader/writer exist and get used? | Carrier = Markdown renderers + LLM corpora + agent runtimes (P6); ship an MCP/CLI consumer *with* v0.1 (S8); the guaranteed consumer is the user's own agent (no network effect needed) |
| **RA1** | LLMs don't reliably read/write the format | An AI-native format agents can't handle is dead on arrival | Reference-impl eval: round-trip + edit accuracy across models | Be a Markdown superset in the pretraining distribution (P6); provide a lossless `.sarib`⇄JSON map so agents write via existing structured-output tooling (Stage 4 §7 / RA-notes) |
| **RL2** | Frozen core has a latent fatal flaw found after freeze | Can't fix without breaking every document; the whole longevity promise dies | Post-freeze; mitigated only *before* freeze | Long critique cycles (Rule 1) + reference implementation + benchmarks *before* v1.0 freeze; a defined v2 migration/escape story (RL cluster) |
| **RM8** | The plain-text-as-truth bet loses to a database | The only fully-working single-source-many-views system (Notion) is a DB ([tools-for-thought.md](../research/tools-for-thought.md)); if files can't scale, the core stance is wrong | Phase B/C perf modeling; reference-impl query/write latency at 100k nodes | Accept as a deliberate bet (ownership/longevity/carrier); op-log (P11) makes the fallback cheap — file demotes to append-only journal + live index without model change (R-new-1 → accepted) |

---

## 2. RM — Model & technical correctness

| ID | Risk | L | I | Bites in | Early warning | Mitigation / link | Status |
|---|---|---|---|---|---|---|---|
| RM1 | Containment/graph duality has no clean answer | L | H | B (Stage 4) | model needs two out-of-sync structures | One graph; document = containment spanning-tree walked in order (D-016) | 🟢 resolved |
| RM2 | Block-granularity bet wrong — knowledge routinely needs sub-block structure | M | H | reference impl | promotion is the rule, not the exception | Promotion of spans to nodes on demand (Stage 4 §3.1, D-015); revisit if churn dominates | 🟡 watch |
| RM3 | Promotion churn — agents over-promote spans → node explosion, id churn | M | M | C/impl (Stage 8) | node count ≫ blocks; id turnover high | Promotion policy + demotion/GC of unreferenced promoted nodes (Stage 8) | 🟡 open |
| RM4 | Anchor stability — tracking a link's position inside an edited block reintroduces intra-text position tracking | H | M | C (Stage 8/9) | edits break/move anchors; merge conflicts on links | Per-character identity à la CRDT for anchors; budget the metadata weight ([versioning-and-merge.md §6](../research/versioning-and-merge.md)) | 🟡 open |
| RM5 | Entity-home "dumping ground" — auto-homed inline entities pile up | M | L | B (Stage 5) | reserved container holds thousands of nodes | Vocabularies declare canonical homes (D-023 schema); projections hide the container (P17) | 🟡 mitigated |
| RM6 | Vocabulary mis-cut — v0 eight are wrong (too few/many) | M | M | B→impl | `concept` overloaded; a kind unused | Falsifiable inclusion test + additive vocab versioning (D-021, D-025) | 🟡 mitigated |
| RM7 | Reference resolution surprises users (name recurs across scopes) | M | M | B/D | wrong-node links; frequent "unresolved" | Deterministic order + never-guess + diagnostics (D-024); measure ambiguity rates | 🟡 mitigated |
| RM8 | Plain-text-as-truth loses to a DB at scale | M | H | B/C | query/write latency unacceptable at 100k nodes | Op-log fallback to live index (R-new-1); see Watch list | 🟠 accepted |
| RM9 | Expressiveness gap — property graph can't model a needed pattern | L | H | B (Stage 5) | recurring facts don't fit edges+qualifiers | n-ary/temporal via edge qualifiers (D-020); extension mechanism (D-011) for the rest | 🟡 mitigated |
| RM10 | Determinism breaks — two valid byte-forms of one model → diff churn, cache misses | M | H | C (Stage 9) | same edit yields different files across tools | Canonical normal form = line-oriented canonical JSON (JCS/RFC 8785), exactly one byte-string per state (D-041) | 🟢 resolved |
| RM19 | Canonical-form recomputation cost — re-canonicalizing a large file on every change | M | L | C (Stage 9) | serialization dominates edit latency at scale | Edits run against the append-only op-log (cheap); canonicalization off-hot-path; incremental canonicalization possible (D-042) | 🟡 mitigated |
| RM20 | Normalization instability — `normalize` not provably idempotent → formatting churn / diff noise | M | M | D (Stage 11) | reformatting a file changes bytes without model change | Idempotence is a conformance requirement (D-051); canonical form is the fixed point; test-corpus coverage | 🟡 mitigated |
| RM21 | Live-view edit ambiguity — a coarse projection can't disambiguate the target model element | L | M | D (Stage 12) | an edit in a summary view maps to the wrong node | Every projected element carries its id (D-052); unattributable edits rejected as a diagnostic, never guessed | 🟡 mitigated |
| RM22 | Reference-impl-defines-truth drift — implementers treat the reference code as the spec (Markdown's fate) | M | M | E (Stage 13) | conforming = "matches our code," spec ignored | The conformance corpus (input→expected), not the code, is the operational definition; reference impl must itself pass the corpus (D-057) | 🟡 mitigated |
| RM11 | Scale — large KBs blow parse/query/memory | M | M | D (Stage 12) | slow load; whole-file-in-memory required | Partial loading, streaming, section anchors (P6/P14); Stage 12 rendering arch | 🟡 open |
| RM12 | Identity collision — offline id generation collides across replicas | L | H | C (Stage 9) | duplicate ids after merge | `(replica,counter)` / ULID collision-free scheme (D-014, Stage 4 §4) | 🟢 resolved |
| RM13 | Auto-merge produces valid-but-wrong result | M | H | C (Stage 8) | merged docs semantically corrupt, no conflict raised | Node/edge-level semantic merge; conservative conflict → human review (D-014, Stage 8) | 🟡 open |
| RM14 | An operation violates a model invariant (two homes, dangling edge) | L | H | C (Stage 8) | invariants (§11 Stage 4) breakable by an op sequence | **Implemented + tested (Sprint 1-3):** `ops.apply()` validates all 10 invariants after every op and rejects violations; containment only via create/move; corpus-tested | 🟢 mitigated |
| RM15 | Traversal determinism depends on a total order over edges | L | M | B (Stage 6) | same traversal yields different order across tools | Total tie-break cascade (D-029) grounded in totally-orderable `(replica,counter)`/ULID ids (D-014) | 🟢 mitigated |
| RM16 | Filter algebra too weak — a common query can't be expressed | M | M | B (Stage 7) | users hit the predicate ceiling routinely | Saved/composed queries + agent reasoning (AI-selected) as the escape (D-031/D-034); revisit predicate set after dogfooding | 🟡 open |
| RM17 | Query→operation staleness (lost update) — graph changes between read and id-addressed write | M | H | C (Stage 8) | concurrent edits silently clobber each other | Optimistic-concurrency `expect` precondition per op (version/status/value check); violated → rejected + re-query (D-038) | 🟢 mitigated |
| RM18 | LWW silently drops the losing side of a concurrent same-node content/move edit | M | M | C (Stage 8) | a collaborator's block edit vanishes without a conflict | Block-sized nodes bound blast radius; guarded ops (D-038) detect-not-lose; intra-node text CRDT deferred (RM4) | 🟡 open |

## 3. RH — Human factors & usability

| ID | Risk | L | I | Bites in | Early warning | Mitigation / link | Status |
|---|---|---|---|---|---|---|---|
| RH1 | Graph purity destroys writability | M | H | D (Stage 10) | authoring feels like filling a database | Prose-first; edges from prose (P3/P4); writability tests every syntax candidate | 🟡 mitigated |
| RH2 | Humans won't enrich even with agent help (founding bet) | H | H | reference impl | enrichment rate flat over time | See Watch list (agent enrichment + per-fact payoff, D-010) | 🔴 watch |
| RH3 | Inline typed-link gesture disrupts prose flow | M | M | D (Stage 10) | authors avoid links; prefer plain text | Writability testing (Stage 10); block-form fallback; D-012 reversal condition armed | 🟡 watch |
| RH4 | Cognitive overload — too many kinds/edges to remember | L | M | D | users can't recall the vocabulary | Thin core, 8 kinds, progressive ladder (D-018, P9) | 🟢 mitigated |
| RH5 | Dialect/canonical split confuses users | M | M | D (Stage 9/10) | users surprised by normalization | gofmt-style invisible normalization; one obvious canonical form (D-003) | 🟡 watch |
| RH6 | IDs/slugs leak into human view and get mis-edited | M | M | D | users hand-edit ids and break links | Tooling hides ids; slugs quarantined; names are the human handle (D-009) | 🟡 mitigated |
| RH7 | Agent enrichment the human didn't intend erodes trust | M | H | impl | users disable enrichment; distrust the graph | Provenance segregation (`inferred` vs `asserted`, D-019); human-confirm loop | 🟡 mitigated |
| RH8 | Attribute/inline-field ceremony (`{.task}`, `key::`) still feels like filling a database | M | M | D (Stage 10) | authors write plain prose, skip all structure | Everything optional (L0 prose valid); agent adds most structure (D-010); test hand-authoring cost; Candidate A minimizes marks | 🟡 open |

## 4. RA — AI / LLM-specific

| ID | Risk | L | I | Bites in | Early warning | Mitigation / link | Status |
|---|---|---|---|---|---|---|---|
| RA1 | LLMs can't reliably read/write .sarib | M | H | impl | round-trip/edit accuracy poor across models | Markdown-superset in-distribution (P6); .sarib⇄JSON for structured output. **G2 interim (2026-07-20, `bench/g2-results.md`):** whole-file .sarib read ≈ Markdown on 3B/7B (no penalty, no gain); 7B reads bounded query-result JSON at 89%; 3B fumbles the JSON surface (id-for-title answers) — small-model floor is real | 🔴 watch (measuring) |
| RA2 | Doesn't beat Markdown on accuracy/tokens | M | H | pre-freeze | benchmarks flat vs Markdown | Interaction-efficiency thesis (D-002); measure (Rule 6). **G2 interim:** split — qwen2.5:7b C>A +27.8pts (p=0.002) at 3.5× fewer tokens; llama3.2-3B C<A −11.1pts (n.s.). Win (where present) is bounded retrieval, NOT typed-surface-in-context (B≯A on both). Full matrix pending quota resets | 🔴 watch (measuring) |
| RA3 | Format drifts out of pretraining distribution as it enriches | M | M | D | richer constructs parse worse than prose | Keep surface Markdown-valid; quarantine extensions (P6/D-011) | 🟡 open |
| RA4 | KV-cache benefits don't materialize (top-of-file churn) | M | M | C (Stage 9) | cache-hit rate low in agent loops | Append-only, deterministic order, stable prefix (P14) | 🟡 mitigated |
| RA5 | Derived-relation query cost too high → tempts materialization | M | M | B (Stage 6) | transitive-closure queries slow on big graphs | Mandatory traversal bounds (D-028) cap closure cost; provenance-marked caches (D-022) | 🟡 mitigated |
| RA9 | "Semantic traversal" wants an embedding signal not in the model → non-deterministic across tools | M | M | B (Stage 6) | semantic-walk results differ per tool/model | Canonical form follows explicit semantic edges (`relates-to`/`refines`/`tag`) deterministically; embedding-ranked variant is explicitly non-canonical, tool-provided (D-026/D-029) | 🟡 open |
| RA10 | Token-economy win shrinks for large-content nodes (`set-content` replaces whole node) | M | L | C (Stage 8) | big prose nodes cost content-sized edits | Keep nodes block-sized; intra-node splicing later (RM4); still ≪ document regeneration (D-002) | 🟡 mitigated |
| RA11 | Surface glyph tokenization unverified — chosen multi-char sigils (`::`,`[[`,`{#`,`^`) may fragment into many tokens | L | M | D (Stage 10) | grammar sigils cost more tokens than assumed | **Measured 2026-07-19** (`bench/tokenizer-report.md`): all load-bearing sigils single-token on o200k/cl100k/r50k; `{.`/`{#` = 2 (acceptable); B saves 26.9% whole-file vs A. Residual: re-run on open-weight tokenizers before freeze (G8) | 🟢 mitigated |
| RA6 | Model-version drift — tuned for 2026 models, degrades later | M | M | ongoing | new model gen parses format worse | Don't optimize vs tokenizers (D-002); ride durable distribution, not quirks | 🟡 mitigated |
| RA7 | Agent inference pollutes graph despite provenance | M | H | impl | inferred facts read as asserted | Agent writes = `inferred` by default; enforce assertion class (D-019) | 🟡 mitigated |
| RA8 | Legacy-prose enrichment cost (bulk extraction still expensive) | M | M | impl | onboarding old corpora is slow/costly | Claim is *incremental write-time* structure, not bulk extraction; defer à la LazyGraphRAG ([ai-context.md](../research/ai-context.md)) | 🟡 accepted |

## 5. RD — Adoption & distribution

| ID | Risk | L | I | Bites in | Early warning | Mitigation / link | Status |
|---|---|---|---|---|---|---|---|
| RD1 | Technically sound, socially dead | M | H | post-v1 | no one emits .sarib | Carrier thesis (P6); ship consumers not just spec | 🔴 watch |
| RD2 | No consumer ships with v1 → dead letter | L | H | E (Stage 13) | v1.0 has spec but no reader/writer | **Shipped (Sprint 3):** working MCP server (5 tools, stdio-tested) + `sarib` CLI over the reference impl | 🟢 mitigated |
| RD3 | Markdown-superset constraint blocks a needed feature | M | M | D | a feature can't be expressed in valid Markdown | Extension mechanism (D-011); accept demotion to extension layer (D-006 reversal armed) | 🟡 mitigated |
| RD4 | A competing standard wins first (vendor blesses another format) | M | H | ongoing | a major agent stack standardizes elsewhere | Be a superset/interop layer, not a rival; move fast to reference impl; embeddable | 🟠 watch |
| RD5 | Network effects never start (chicken-and-egg) | M | H | post-v1 | no tools ⇒ no files ⇒ no tools | Single guaranteed consumer = the user's own agent; per-file payoff (RH2 mitigation) | 🟡 mitigated |
| RD6 | JSON-as-the-format temptation — adopters treat the JSON interchange as *the* format, skipping the human surface | M | M | D→post-v1 | ecosystem emits/edits JSON, human surface unused | Canonical/interchange JSON is machine-only; Phase D delivers the pleasant author surface; position JSON as wire/at-rest, never what humans write (D-040) | 🟡 open |

## 6. RG — Governance & ecosystem

| ID | Risk | L | I | Bites in | Early warning | Mitigation / link | Status |
|---|---|---|---|---|---|---|---|
| RG1 | Governance vacuum / BDFL problem (the Markdown–CommonMark war) | M | H | E | forks because no legitimate extension path | Explicit constitution at birth: who extends, what "conforming" means (P16; Stage 13+) | 🟠 open |
| RG2 | Spec ambiguity → divergent parsers (Markdown's fate) | M | H | D/E | same file, different parses across tools | Spec + conformance test suite from v0.1 (S6, P15/P16) | 🟠 open |
| RG3 | Flavor fragmentation despite extension mechanism | M | M | post-v1 | incompatible core extensions proliferate | Frozen core + self-announcing extensions + conformance brand (D-011, P16) | 🟡 mitigated |
| RG4 | Vocabulary fragmentation — competing community vocabularies | M | M | post-v1 | three rival `task` vocabularies | Blessed standard library + namespacing + registry (D-021, D-025; Stage 13+) | 🟡 mitigated |
| RG5 | Extension namespace squatting / collision | L | M | post-v1 | prefix clashes between vendors | Namespace registry; registered/reverse-DNS prefixes (D-025) | 🟡 open |
| RG6 | Vendor capture (embrace-extend-extinguish) | L | H | post-v1 | a platform ships an incompatible ".sarib+" | Open standard, permissive license, multi-implementer conformance (Stage 14/15) | 🟡 open |

## 7. RL — Longevity & future-proofing

| ID | Risk | L | I | Bites in | Early warning | Mitigation / link | Status |
|---|---|---|---|---|---|---|---|
| RL1 | Spec bloat over time violates the business-card target (S6) | M | M | E→post-v1 | core grammar keeps growing | Freeze core; push features to vocab/extension; priority rule 4 (P16) | 🟡 mitigated |
| RL2 | Frozen core has a latent fatal flaw found post-freeze | M | H | post-freeze | a common need is unrepresentable, no compat fix | Long critique cycles + reference impl + benchmarks *before* freeze; defined v2 migration story | 🔴 open |
| RL3 | Dependency on transient tech (tokenizer, model API, a CRDT lib) | L | M | ongoing | format tied to one vendor's runtime | Model-agnostic (D-002); substrate = plain UTF-8 + git, not reinvented (L0) | 🟢 mitigated |
| RL4 | Project outlives / loses its maintainers | M | M | post-v1 | bus factor = 1; no independent impls | Self-hosting spec + conformance suite → independently implementable in a weekend (S6, RL4) | 🟡 open |
| RL5 | The AI-native premise itself dates (context/tokenization paradigm shifts) | L | H | 5–10 yr | agent architectures make the format's rationale moot | Hedge on durable value (human-readable plain-text graph) that survives even if AI specifics change | 🟡 accepted |

## 8. RS — Security & safety

| ID | Risk | L | I | Bites in | Early warning | Mitigation / link | Status |
|---|---|---|---|---|---|---|---|
| RS1 | Code execution / unsafe load (YAML tag-constructor RCE fate) | L | H | C/D | any construct triggers evaluation on load | Pure-data load, no executable directives (D-043) | 🟢 mitigated |
| RS2 | Expansion DoS — transclusion cycles / billion-laughs (YAML→K8s CVE) | M | H | C (Stage 9) | a small file expands unboundedly | Acyclic transclusion + cycle-detection + depth/size bound on resolution (D-043) | 🟢 mitigated |
| RS3 | Prompt injection via .sarib content (a file that instructs the reading agent) | H | H | impl | file content steers an agent's behavior | Content is data, not instructions; agents treat .sarib as untrusted; no smuggled parser/model directives (Crockford-comments lesson, [standards-adoption.md](../research/standards-adoption.md)) | 🔴 open |
| RS4 | Provenance spoofing — forged `asserted-by`/human-claim | M | M | post-v1 | in-file provenance trusted as proof | Provenance is a *claim*, not proof; optional cryptographic signing as a companion spec; don't over-trust | 🟡 open |
| RS5 | Reference-resolution exploit — engineered name collision redirects a link | L | M | D | link resolves to attacker-controlled node | Deterministic nearest-scope (D-024); explicit ids for sensitive refs; ambiguity diagnostics | 🟡 mitigated |
| RS6 | Canonicalization attacks — byte-forms that hash differently but mean the same | L | M | C (Stage 9) | signing/dedup inconsistent | Canonical form + canonicalizer rejects ambiguous encodings (dup keys/non-NFC/non-canonical numbers) (D-041/D-043) | 🟢 mitigated |

## 9. RP — Process & project

| ID | Risk | L | I | Bites in | Early warning | Mitigation / link | Status |
|---|---|---|---|---|---|---|---|
| RP1 | Rediscovering RDF badly | M | H | A (Stage 2) | model converges on triples + ceremony | RDF-delta analysis done; kill-criterion (Rule 5) evaluated — no pivot needed (Stage 2 §3) | 🟢 mitigated |
| RP2 | Boil-the-ocean scope | H | M | ongoing | stages sprawl; no v1 boundary | v1 scope cap: core + op vocab + 3 projections; phase gates (charter) | 🟡 mitigated |
| RP3 | Efficiency claims unmeasured | L | H | pre-freeze | "token efficient" asserted, never benchmarked | **Measured (Sprint 4):** G1=0.50% edit ratio, G7=99.3% prefix, G2 token-side 29× on real data (`bench/gate-report.md`). **G2 accuracy run live (2026-07-20):** cross-model harness built + self-tested (no LLM judge, constructed ground truth); 2/7 models complete, rest quota-gated (`bench/g2-results.md`) | 🟢 mostly measured |
| RP4 | Decisions accumulate contradictions (25+ entries) | M | M | ongoing | a new decision silently conflicts with an old one | Critique-first (Rule 1); reversal conditions; per-stage verification; priority order (Stage 3 §4) | 🟡 mitigated |
| RP5 | Analysis paralysis / never shipping | M | H | C→E | endless refinement, no reference impl | Staged exit criteria; v1.0 is a defined endpoint (Stage 15); build reference impl in Phase E | 🟡 open |
| RP6 | Resource/continuity interruption (credit limits, session loss) | H | L | ongoing | a session ends mid-stage (has happened) | Everything persisted to repo; README session log = resume point; self-contained stages | 🟢 mitigated |

---

## 10. Severity summary

Indicative bands (not a precise tally — see each row for its authoritative status flag):

| Band | IDs |
|---|---|
| 🔴 critical / existential | RH2, RA1, RA2, RD1, RL2, RS3 |
| 🟠 high (accepted or open) | RM8 (accepted), RD2, RD4, RG1, RG2, RP3 |
| 🟡 medium / monitored | most of RM/RH/RA/RG/RS/RP |
| 🟢 resolved / strongly mitigated | RM1, RM10, RM12, RM15, RM17, RH4, RL3, RP1, RP6, RS1, RS2, RS6 |

The shape to notice: **the lethal risks are not technical.** The model problems (RM cluster) are mostly resolved or have clear mitigations; the killers are human (RH2), distributional (RD1/RA1/RA2), and safety (RS3). The project's hardest work is not designing the language — it is proving people and agents will actually use it and doing so safely. Phase E (reference implementation + benchmarks) is where the red risks finally get real signal, which is an argument for reaching it sooner rather than perfecting the paper design.

## 11. Retired / resolved risks

None retired yet. Resolved-by-design risks (RM1, RM12, and the strongly-mitigated set) stay in their category tables with 🟢 status and their closing decision, per the maintenance protocol (do not delete).

## 12. Crosswalk — old IDs → this register

| Old ID (origin) | New ID | Note |
|---|---|---|
| R1 charter — rediscover RDF badly | RP1 | mitigated (Stage 2) |
| R2 charter — graph purity kills writability | RH1 | mitigated (P3/P4) |
| R3 charter — boil the ocean | RP2 | mitigated (scope cap) |
| R4 charter — efficiency claims unmeasured | RP3 | open (needs harness) |
| R5 charter — technically sound, socially dead | RD1 | watch (existential) |
| R-new-1 (Stage 3) — plain-text vs DB bet | RM8 | accepted bet |
| R-new-2 (Stage 3) — duality no clean answer | RM1 | resolved (D-016) |
| R-new-3 (Stage 4) — block-granularity bet | RM2 | watch |
| OQ1 (Stage 4) — promotion churn | RM3 | open |
| OQ2 (Stage 4) — anchor stability | RM4 | open |
| OQ3 (Stage 4) — entity-home dumping | RM5 | mitigated |
| (Stage 5) RM6/RM7/RA5/RG4 surfaced | as-is | filed this session |

Every risk ever logged is now here. The charter's inline table is superseded; future stages update this file only.

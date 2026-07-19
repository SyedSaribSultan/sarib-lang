# Stage 2 — Prior Art & Design Lessons

**Status:** Draft v0.1 — open for critique by Stage 3 · **Date:** 2026-07-14
**Input:** Stage 1 (Vision & Philosophy); research notes in `../research/`
**Decisions logged:** D-006 … D-011
**Coverage:** 5 of 8 research questions completed with primary-source citations (RQ2, RQ3, RQ5, RQ7, RQ8). Three sub-beats deferred with primary-source gaps flagged in §7 (RQ1 identity internals, RQ4 graph-as-text syntaxes, RQ6 CRDT/Datomic/event-sourcing internals). Enough evidence landed to force the decisions below; the gaps refine rather than reverse them.

---

## 1. Critique of Stage 1

The evidence largely vindicated Stage 1's structure but landed one genuine blow to the founding thesis and sharpened three stances into decisions.

**The blow (challenges T1 and the brief itself).** Stage 1 assumed humans would author knowledge as "trees with light links" — local structure inline. The single most important finding in this research contradicts that. Wikidata's own history reports that when Semantic MediaWiki offered inline typed annotations in wikitext, "form-based input methods soon dominated over in-text annotations — a major deviation from the unity of data and text that was central to the Semantic Wikipedia concept" ([Wikidata: The Making Of](https://iccl.inf.tu-dresden.de/w/images/9/9d/Vrandecic-Pintscher-Kroetzsch_Wikidata-History-WWW-2023.pdf)). Even sympathetic experts defected: at AAAI 2006 a blogger reporting Berners-Lee's plea to contribute RDF noted "here I am typing up a blog post instead" ([grandtextauto](https://grandtextauto.soe.ucsc.edu/2006/07/18/googles-norvig-questions-berners-lee-on-the-semantic-web/)). Norvig's question to Berners-Lee — "many people have difficulty writing well-formed Web pages; how would they get RDF right?" — is the same objection.

Humans, at scale, do not hand-author structured knowledge inline. Twenty years of evidence says so. This does not kill `.sarib`; it **relocates the labor**. The AI-native premise is precisely what changes the equation: the agent does the structuring, the human writes prose and confirms. But this must be designed in, not assumed away. See D-010.

**Three sharpenings (T2, T4, T6 → decisions).** The formality/ceremony tension (T2), the projection/round-trip tension (T4), and the determinism/extensibility tension (T6) all resolved cleanly in the direction Stage 1 guessed — now backed by evidence and promoted to decisions D-007/D-008, D-009, and D-011.

**One vindication (T3).** D-002's reframe (interaction over compression) is confirmed and strengthened by the KV-cache and length-degradation literature (§4).

---

## 2. Consolidated findings by theme

### 2.1 Formality is adoption poison past a low threshold (RQ2)

The semantic web is the most thoroughly documented failure in this space, and its insiders wrote the postmortems.

- The founders conceded syntax killed it: RDF/XML's rendering is "quite clumsy syntactically, and its lack of transparency and readability might have been a factor inhibiting rapid adoption" ([Shadbolt/Hall/Berners-Lee 2006](https://eprints.soton.ac.uk/262614/1/Semantic_Web_Revisted.pdf)).
- The JSON-LD creator, chairing the standards group, disowned the stack: "after 7+ years… our company has never had a need for a quad store, RDF/XML, N3, NTriples, TURTLE, or SPARQL… even your company can't stomach the technologies involved" ([Sporny](http://manu.sporny.org/2014/json-ld-origins-2/)). His verdict on RDF's model: "RDF is a shitty data model. It doesn't have native support for lists."
- OWL's open-world assumption + no unique-name assumption made it unable to tell an author they'd made a mistake, so industry abandoned inference for validation and "eventually invented SHACL," leaving two languages to keep in sync ([TerminusDB](https://terminusdb.com/blog/the-semantic-web-is-dead/)).
- What won instead were deliberate simplifications by the same insiders: schema.org explicitly refuses a "universal ontology" for "a more practical and less abstract one, where immediate applications in search results were the focus" ([schema.org datamodel](http://schema.org/docs/datamodel.html)), reaching 31.3% of 10B pages ([ACM Queue](https://queue.acm.org/detail.cfm?id=2857276)). Wikidata is "not based on a standard semantics such as OWL" and uses form-based editing over abstract Q-IDs ([Wikidata Making Of](https://iccl.inf.tu-dresden.de/w/images/9/9d/Vrandecic-Pintscher-Kroetzsch_Wikidata-History-WWW-2023.pdf)).

**Lesson.** Progressive formalization (T2) is correct, and the dose is even lower than Stage 1 implied. Default to closed-world validation with unique names (be a type-checker, not a reasoner). Segregate any inferred fact from asserted facts. Record *claims with provenance*, not *truth* — Wikidata's plurality model (conflicting referenced statements with ranks) is the design that survived contact with reality, and it maps naturally onto an AI reader that can weigh sources.

### 2.2 Adoption is a distribution phenomenon, not a merit phenomenon (RQ3, RQ8)

Every winning format had a carrier that pre-installed its parser; every elegant loser lacked one.

- JSON: the parser "was already installed on every computer on earth" (the JS engine); standards bodies (ECMA-404 2013, RFC 8259 2017) arrived *after* victory to describe reality ([twobithistory](https://twobithistory.org/2017/09/21/the-rise-and-rise-of-json.html)).
- Markdown: rode GitHub READMEs, Stack Overflow, Reddit — places developers were forced to write — with essentially zero promotion by Gruber ([Coding Horror](https://blog.codinghorror.com/standard-flavored-markdown/)).
- CSV: the spreadsheet was the carrier; RFC 4180 (2005) admitted the format "has never been formally documented" and just wrote down practice ([RFC 4180](https://www.rfc-editor.org/rfc/rfc4180.html)).
- Control group: S-expressions — the most elegant, most trivially-parseable structured format ever — waited 28 years (1997 draft → RFC 9804 in 2025) and never escaped Lisp, because Lisp was its only carrier ([RFC 9804](https://www.rfc-editor.org/rfc/rfc9804.pdf)). org-mode is strictly more capable than Markdown and stayed niche because its power lives in Emacs, not the file ([HN](https://news.ycombinator.com/item?id=16198623)).
- The clean-break tax: XHTML 2.0 abandoned backward compatibility and died with zero browser implementations; the vendors defected to WHATWG/HTML5, whose written principles are "Support Existing Content / Pave the Cowpaths / Evolution, not Revolution" ([WHATWG history](https://wiki.whatwg.org/wiki/W3C), [HTML5 principles](https://html5forwebdesigners.com/design/)).
- The consumer-first rule, tested live in the AI era: **llms.txt** got ~10% publisher adoption but ~0.1% actual bot reads because no major consumer committed ([analysis](https://medium.com/@kaispriestersbach/the-llms-txt-is-dead-more-precisely-a-dud-ab7bee4f469c)); **AGENTS.md** — plain Markdown at a known path with day-one tool support across Codex/Cursor/Copilot — hit >60k repos and moved into a Linux Foundation body ([InfoQ](https://www.infoq.com/news/2025/08/agents-md/)).

**Lesson (the load-bearing one for the whole project).** `.sarib`'s carrier is the LLM+agent stack: pretraining corpora, agent runtimes, and editor/IDE renderers. Two hard requirements follow: (1) the surface must render acceptably wherever Markdown renders today, ideally *being* valid Markdown at the surface, so existing renderers adopt it at zero cost; (2) a reference consumer (MCP server / CLI reader/writer) must ship *with* v0.1 — a spec with no consumer is a dead letter. Keep the core grammar business-card-sized (JSON's six railroad diagrams vs YAML's 86 pages, which PEP 518 rejected *for that reason*, [PEP 518](https://peps.python.org/pep-0518/)); freeze the core and version only self-announcing extensions (YAML 1.1→1.2 silently changing what `no` means is the anti-pattern, [YAML from hell](https://ruudvanasseldonk.com/2023/01/11/the-yaml-document-from-hell)).

### 2.3 Round-trip requires identity + single-owner-per-state-class (RQ5)

The "store once, render infinitely" thesis has been attempted many times. The evidence gives a precise law for when it holds.

- **Identity must survive projection.** Portable Text puts a `_key` on every block specifically so "keys let the system identify which block changed without relying on array position" ([spec](https://www.portabletext.org/specification/)); Notion's UUID-per-block is why editing any view edits the record, and properties survive even a type change — a to-do turned into a heading and back is *still checked*, because "we preserve as much user intention as possible" ([Notion](https://www.notion.com/blog/data-model-behind-notion)). Where identity is absent, back-flow is impossible: Obsidian Dataview "is not meant to edit your notes and will always leave them untouched" because it indexes metadata, not addressable blocks ([Dataview](https://blacksmithgu.github.io/obsidian-dataview/)).
- **The refinement beyond identity: one owner per state class.** Jupyter+git broke catastrophically despite position-based matching because human inputs, machine outputs, execution counts, and kernel metadata cohabit one JSON file — "if you and a colleague run the cells in different orders, you'll have a conflict in every single cell" ([fast.ai](https://www.fast.ai/posts/2022-08-25-jupyter-git.html)). Every fix that worked partitions ownership: jupytext gives inputs to the text file and outputs to the `.ipynb`, and its only failure mode is when *both* are edited between syncs ([jupytext](https://github.com/mwouts/jupytext)).
- **One-way projections are fine if they're honestly terminal.** Knuth's TANGLE deliberately "scrambled" its output so nobody would edit it, keeping weave/tangle consistent by construction ([Wikipedia](https://en.wikipedia.org/wiki/Literate_programming)); XSLT survives in DITA-OT publishing precisely where the one-way contract is honest, even as browsers remove it ([DITA-OT](https://www.dita-ot.org/dev/reference/architecture.html), [Chrome deprecation](https://developer.chrome.com/docs/web-platform/deprecating-xslt)). The fatal zone is the *ambiguous middle*: an output that looks editable but has no back channel (Jupyter-in-git, Notion exports which are officially non-reimportable).
- **Don't be a lowest-common-denominator interlingua.** Pandoc's own manual states "one should not expect perfect conversions" because its AST is "less expressive than many of the formats it converts between," while only conversions *from pandoc's own Markdown* "aspire to be perfect" ([Pandoc](https://pandoc.org/MANUAL.html)).

**Lesson.** Give every knowledge atom a stable, position-independent, collision-proof ID that every projection carries. Make projections *windows* (live configurations over the canonical store), not *copies*; a projection may hide fields but must never silently drop them. Separate content / derived-cache / session state into layers with one authoritative writer each. `.sarib`'s text form should be a 1:1 lossless serialization of the `.sarib` model (a privileged dialect), with bounded, declared fidelity for foreign formats — never an interlingua.

### 2.4 For LLMs specifically: typed edges yes, ontology ceremony no; author structure, don't extract it (RQ7)

This beat is the newest evidence and the most directly decisive for an *AI-native* format.

- Structure helps LLMs on the hard questions: graph/multi-hop/global reasoning improves with explicit structure, but the field's 2025–26 correction is sharp — "GraphRAG frequently underperforms vanilla RAG on many real-world tasks" ([GraphRAG-Bench](https://arxiv.org/abs/2506.05690)), and its dominant cost was the LLM entity-extraction indexing pass, which LazyGraphRAG cut by ~1000x by deferring it ([Microsoft](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)).
- Format matters, and the semantic-web serializations are the *worst* choice: on KG-LLM-Bench, structured JSON/YAML and one-triple-per-line scored highest, while **RDF Turtle (0.35) and JSON-LD (0.34) scored worst on accuracy — and cost 8k / 13k+ tokens for the same graph** versus ~3k for the simple formats ([KG-LLM-Bench](https://arxiv.org/abs/2504.07087)). Indentation-based low-punctuation formats (YAML/Markdown-like) are the empirical sweet spot for input; XML-style tag pairs are worst on both tokens and accuracy; novel compact notations (TOON) pay an accuracy tax that exceeds their token savings ([Improving Agents](https://www.improvingagents.com/blog/best-nested-data-format/), [Notation Matters](https://arxiv.org/abs/2605.29676)).
- Byte-layout economics are real: prompt-cache reads bill at ~10% of base and match on *exact* prefix, so a single changed early character invalidates everything after it; production agents treat KV-cache hit rate as "the single most important metric" and demand deterministic serialization and append-only growth ([Manus](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)).
- Assume the whole file is never in context: length degradation persists in frontier models once lexical overlap is removed (NoLiMa: 10/12 models ≤50% of baseline by 32k tokens, [arXiv](https://arxiv.org/abs/2502.05167)), so addressable subgraphs with human-readable anchors beat monolithic dumps, and entity names should be repeated at point of use rather than normalized into opaque IDs.

**Lesson.** This is the project's sharpest wedge. `.sarib`'s core value is that humans and agents author typed structure *incrementally at write time*, deleting GraphRAG's dominant extraction cost — while the file stays useful read linearly, with no graph tooling required. Use familiar, pretraining-saturated surface syntax (Markdown headers + `key: value` + one-edge-per-line). Provide a lossless `.sarib`⇄JSON mapping so agents can write through existing constrained-decoding/structured-output tooling, but keep JSON off the authoring surface. Design the byte layout for cache hits: deterministic ordering, append-friendly, no volatile fields near the top.

---

## 3. Kill-criteria evaluation (Operating Rule 5)

Rule 5 requires `.sarib` to pivot to a profile/binding of an existing stack if one satisfies ≥90% of requirements. Verdict: **no existing stack clears the bar, but the closest one defines the design.**

| Candidate | Model fit | Human-writable + carrier | Stable block identity | LLM-friendly | Verdict |
|---|---|---|---|---|---|
| **JSON-LD / RDF** | Graph, but triples lack lists & edge properties; reification quadruples size | No — "clumsy," insider-disowned | IRIs (heavy ceremony) | **Worst measured** (accuracy + 13k tokens) | Reject as lineage; steal only the abstract-model-enables-format-agility idea (per [Brickley](http://manu.sporny.org/2014/json-ld-origins-2/)) |
| **Property graph (openCypher/GQL)** | Strong — nodes + typed edges *with edge properties*, matches whiteboard thinking ([Cypher origin](https://www.thobe.org/work/cypher/)) | No plain-text human-authorable *file* form; Cypher is a query language, not storage | Internal | Untested but structurally close to top formats | Adopt the **model**; it has no file surface to inherit |
| **Markdown + frontmatter (Obsidian model)** | Tree + tags + links; no typed edges | **Yes — the carrier is already there** | **No — the fatal gap** (index-only, read-only projections) | Excellent | Closest; its one missing piece (addressable block identity + typed edges) is exactly `.sarib`'s delta |
| **Portable Text** | Typed blocks + keyed identity + shared annotations | JSON, not hand-writable | Yes (`_key`) | JSON-shaped | Steal the identity/annotation design; wrong authoring surface |

**Conclusion.** `.sarib` is justified, but it should be positioned not as "a new language from first principles" so much as **"Markdown's surface + stable block identity + property-graph edges + a lossless model,"** carrying the property-graph data model, Portable Text's identity discipline, and Wikidata's claims-with-provenance epistemology. That framing is incremental-adoption-shaped (D-006) and honest about standing on giants.

---

## 4. Impact on Stage 1's tensions

| # | Stance after evidence | Change |
|---|---|---|
| T1 | Humans write **prose**; structure is optional and largely **agent-added** (D-010). Inline hand-authoring of graph structure is empirically rare even among experts. | **Revised** — labor relocated to the agent |
| T2 | Progressive formalization confirmed; dose is *low*. Closed-world validation, segregated inference, claims-not-truth. | Strengthened → D-007, D-008 |
| T3 | Interaction over compression confirmed; add KV-cache byte-layout discipline. | Vindicated |
| T4 | Projections are windows carrying IDs; hide-never-drop; content/derived/session layered by owner. | Confirmed → D-009 |
| T5 | File-as-truth holds, but the winning realization (Notion) uses a DB. `.sarib` keeps the file canonical and pays for it with an index; the bet is that plain-text + carrier beats DB power. | Unchanged, risk noted |
| T6 | Forgiving surface + deterministic parse; frozen core + self-announcing extensions; attribute/extension mechanism in core or suffer Markdown's flavor fragmentation. | Confirmed → D-011 |
| T7 | Concurrency: git 3-way on stable IDs + normal form for v1; op-vocabulary CRDT-ready. **Evidence still owed** (RQ6 gap). | Provisional |
| T8 | Provenance promoted further: claims-with-references is now a *model pillar*, not a nicety. | Strengthened |

---

## 5. New decisions (see decision log for full entries)

- **D-006** — Surface is a Markdown superset; a `.sarib` file must render acceptably as Markdown in existing renderers. Carrier = pretraining distribution + Markdown renderers + agent runtimes.
- **D-007** — Adopt the **labeled property-graph** model (nodes + typed edges carrying properties). Reject the RDF/triples lineage. Edge properties and native lists are first-class.
- **D-008** — Closed-world validation with unique names by default (type-checker, not reasoner). Inferred/derived facts are segregated from asserted facts. Store **claims with provenance**, not truth.
- **D-009** — Round-trip law: every atom has a stable, position-independent, collision-proof ID; projections are ID-carrying windows that may hide but never drop fields; content/derived/session are separate layers with one authoritative writer each.
- **D-010** — Division of labor: **humans author prose + light structure; agents enrich to graph.** "Human-writable" is satisfied by the surface being prose; structural richness is mostly agent-produced and human-confirmed. (Challenges the brief's assumption that humans hand-author the graph.)
- **D-011** — One blessed in-core extension/attribute mechanism with graceful degradation (unknown constructs parse, render generically, round-trip untouched). Frozen core grammar; extensions are self-announcing and versioned separately.

---

## 6. Impact on success criteria

- **S4 (cold agent readability)** gains a concrete baseline target: beat Markdown on relationship queries at ≤ its token cost, and specifically avoid the RDF-Turtle/JSON-LD failure region (worst accuracy at 3–4x tokens, [KG-LLM-Bench](https://arxiv.org/abs/2504.07087)).
- **S6 (implementability)** gains teeth: publish the core grammar's page count as a feature; target a conforming parser in a weekend (JSON, not YAML).
- **New S7 — cache-friendliness:** editing or appending one node must leave the file's leading bytes unchanged (deterministic order + append bias), so prompt-cache prefixes survive. Measured per Rule 6.
- **New S8 — carrier compatibility:** a `.sarib` file renders without error in a standard CommonMark renderer, and a reference MCP/CLI consumer reads and writes it. Gate for v0.1.

---

## 7. Open research items — CLOSED (session 2, 2026-07-15)

All three sub-beats were completed in session 2 and confirmed, not reversed, the Stage 2 decisions. They also produced the sharpest single design finding of the whole prior-art phase (the edge-writing-ceremony law → D-012/D-013) and let T7 be ratified (→ D-014). Full notes: `research/versioning-and-merge.md`, `research/graphs-and-databases.md`.

1. **RQ1 — identity internals. ✓** Git is the cautionary pole: a blob stores content with no filename, so Git *cannot track a rename* and re-guesses it heuristically at diff time (50% similarity, `-M`) — identity-by-content fails the one job a knowledge medium needs ([Pro Git](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)). Tolerance spectrum confirmed: the more opaque the ID (UUID, hash, Q-number), the more completely tooling must hide it; only human-readable slugs (org `CUSTOM_ID`, wiki-titles) survive in prose. → reinforces D-009.
2. **RQ4 — graph-as-text syntaxes. ✓** Confirmed the hypothesis decisively: every graph-as-text format (Turtle `S P O .`, Cypher `(a)-[:R]->(b)`, DOT `a -> b`, Mermaid `A -->|r| B`) forces a standalone statement naming both endpoints plus the relation — *edge-writing ceremony* — which is why all clustered in query/visualization/config niches and none became a thinking medium. Mermaid is the exception that proves the rule: it succeeded by dropping semantics (just diagrams) and riding Markdown/GitHub. Trees are hand-authored at scale (Markdown, KDL, outliners) because containment is a zero-ceremony implicit edge. → **new D-012, D-013.**
3. **RQ6 — edit-operation vocabulary & merge internals. ✓** Event sourcing, Datomic ("database as a value," accretion-only, `:db/retract` not destroy), and both CRDT families independently converge on *ops-canonical / state-as-projection*; Fowler names a VCS as the archetype. Mergeability requires identified elements + commutative ops: JSON Patch's positional array addressing is the anti-pattern, Automerge/Yjs `(replica, counter)` IDs are the fix; CRDT beats OT for owned/offline files (OT needs a central server). → **new D-014, ratifies T7.**

---

## 8. Reliability notes

The completed beats flag their own weak points inline. Carry these caveats forward: the LLM-format benchmarks (RQ7) are mostly small-model studies and format effects shrink with model size ([arXiv 2411.10541](https://arxiv.org/abs/2411.10541)); several KG-LLM-Bench and GraphRAG-Bench figures were taken from search digests, not re-read from paper tables (verify before quoting in the spec); "Let Me Speak Freely" (structured output hurts reasoning) partially failed to replicate under matched prompts ([dottxt](https://blog.dottxt.ai/say-what-you-mean.html)). None of these caveats overturns a Stage 2 decision; they set the confidence level for benchmark targets under Operating Rule 6.

This document is unratified until Stage 3 critiques it.

# RQ7 — Evidence on LLMs and Structured Text (2024–2026)

Raw research notes for the .sarib language project. Beat: empirical evidence on how LLMs handle
structured vs. prose context, serialization formats, typed relationships, context-window economics,
and prior "LLM-native format" attempts.

Compiled: 2026-07-14. Method: 25+ web searches + primary-source fetches. Confidence labels:
**[VERIFIED]** = claim read directly in fetched primary source; **[SEARCH-DIGEST]** = number seen in
search-result summaries of the cited source but source not fully fetched; **[WEAK]** = single
secondary source, treat as indicative only; **[CONTESTED]** = credible published disagreement exists.

---

## Q1. Does graph-structured context improve LLM retrieval/reasoning vs. prose?

**Short answer: yes for multi-hop and global/sensemaking questions; no (often negative) for simple
factual lookups — and the graph must be paid for at indexing time.**

### Evidence FOR

- Microsoft GraphRAG (Edge et al., Apr 2024): LLM-built entity knowledge graph + pre-generated
  community summaries. On "global sensemaking" questions over ~1M-token corpora, GraphRAG beat
  vanilla vector RAG on comprehensiveness and diversity of answers (e.g., comprehensiveness win
  rates ~57% on the Podcast dataset and ~64% on the News dataset for the best community-summary
  levels). Evaluation was LLM-as-judge pairwise, not exact-match QA. [Source](https://arxiv.org/abs/2404.16130)
  - Caveat: the evaluation is LLM-as-judge; independent work documents position/length/verbosity
    biases in LLM-judge pipelines generally, so win-rate magnitudes should be read cautiously.
    [SEARCH-DIGEST] [Source](https://arxiv.org/abs/2604.23178)
- GraphRAG-Bench / "When to use Graphs in RAG" (Xiang et al., v1 Jun 2025, v3 Feb 2026): systematic
  benchmark across fact retrieval, complex reasoning, contextual summarization, creative generation.
  Finds graphs help most on tasks needing hierarchical/multi-hop knowledge; confirms in its abstract
  that "recent studies report that GraphRAG frequently underperforms vanilla RAG on many real-world
  tasks" and maps out when graphs do pay off. [VERIFIED abstract] [Source](https://arxiv.org/abs/2506.05690)
  - Numbers circulating from this line of work: graph retrieval improved multi-hop reasoning depth
    ~+4.5% on HotpotQA but with ~2.3x average latency; GraphRAG ~13.4% lower accuracy than vanilla
    RAG on Natural Questions and ~16.6% worse on time-sensitive queries. [SEARCH-DIGEST — from search
    summaries of the paper; verify against paper tables before quoting in the spec]
    [Source](https://arxiv.org/html/2506.05690v3), [Benchmark repo](https://github.com/GraphRAG-Bench/GraphRAG-Benchmark)
- "RAG vs. GraphRAG: A Systematic Evaluation and Key Insights" (Han et al., Feb 2025): unified
  protocol over QA + query-based summarization. RAG and GraphRAG have *distinct* strengths (RAG on
  detail-oriented single-hop; GraphRAG on multi-hop and global summarization); combining them
  consistently improves. [Source](https://arxiv.org/abs/2502.11371)
- "Do We Still Need GraphRAG? Benchmarking RAG and GraphRAG for Agentic Search Systems" (RAGSearch,
  Apr 2026): with agentic multi-round search, dense RAG's gap to GraphRAG narrows substantially
  (especially with RL-trained searchers), i.e., *iterative retrieval partially substitutes for
  explicit graph structure*. "Nevertheless, GraphRAG remains advantageous for complex multi-hop
  reasoning, exhibiting more stable agentic search behavior when its offline cost is amortized."
  [VERIFIED abstract] [Source](https://arxiv.org/abs/2604.09666)
- Long-tail facts: prompting with KG triples beat passage-based prompting with a SOTA retriever in
  most conditions on the LTGen long-tail-facts benchmark. [SEARCH-DIGEST]
  [Source](https://www.sciencedirect.com/science/article/abs/pii/S095070512500694X)

### Evidence AGAINST / cost critique

- Indexing cost is the killer: a widely-cited practitioner figure is ~$33,000 to index a single 5GB
  legal corpus with full GraphRAG in early 2024 (one-time LLM entity extraction + community
  summarization). [WEAK — single Medium source, but consistent with GraphRAG's design]
  [Source](https://medium.com/graph-praxis/the-graphrag-cost-cliff-how-33-000-became-33-in-eighteen-months-be1b0fbe37e4)
- Microsoft's own follow-up, LazyGraphRAG (Nov 2024), implicitly concedes the cost problem: it defers
  all LLM summarization to query time; indexing cost is "identical to vector RAG and 0.1% of the
  costs of full GraphRAG," with answer quality comparable to GraphRAG global search at >700x lower
  query cost. [Source](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/),
  [coverage](https://www.thestack.technology/microsoft-lazygraphrag/)
- GraphRAG-Bench (above) explicitly frames "GraphRAG frequently underperforms vanilla RAG on many
  real-world tasks" as the motivating observation. [VERIFIED abstract] [Source](https://arxiv.org/abs/2506.05690)
- Vendor benchmarks claiming large GraphRAG accuracy wins exist (e.g., FalkorDB/Diffbot) but are
  conflicted-interest marketing; do not rely on them. [WEAK/vendor]
  [Source](https://www.falkordb.com/blog/graphrag-accuracy-diffbot-falkordb/)

### Net reading for .sarib
Graph structure demonstrably helps LLMs on relational/multi-hop/global questions, but the field's
2025-26 correction shows: (a) structure is not free — someone pays extraction cost; (b) for simple
lookups plain text + retrieval wins; (c) lazy/deferred structure (LazyGraphRAG) and agentic
iterative search (RAGSearch) both erode the case for heavyweight pre-built graphs. A format where
*humans/agents author the graph directly* (no LLM extraction pass) captures GraphRAG's benefit while
deleting its dominant cost.

---

## Q2. Which serialization formats do LLMs parse/produce most reliably and cheaply?

### Input-side (comprehension) benchmarks

- Improving Agents nested-data benchmark (Oct 2025; GPT-5 Nano, Gemini 2.5 Flash Lite, Llama 3.2 3B;
  1,000 questions/format, 95% CIs, deliberately stressed into the 40–60% accuracy range): [VERIFIED — fetched]
  [Source](https://www.improvingagents.com/blog/best-nested-data-format/)
  - GPT-5 Nano: YAML 62.1% > Markdown 54.3% > JSON 50.3% > XML 44.4% (YAML beats XML by 17.7 pp).
  - Gemini 2.5 Flash Lite: YAML 51.9% > Markdown 48.2% > JSON 43.1% > XML 33.8%.
  - Llama 3.2 3B: no significant format preference.
  - Tokens for the same data (GPT-5 Nano): JSON 57,933 vs YAML 42,477 vs Markdown 38,357 vs XML
    68,804. Markdown used 34–38% fewer tokens than JSON and ~10% fewer than YAML across models;
    XML needed ~80% more tokens than Markdown.
  - Their conclusion: YAML best default for accuracy, Markdown best for cost, avoid XML for bulk
    nested data.
- Same team's tabular benchmark + TOON test (Oct 2025, GPT-4.1 nano): Markdown key-value blocks were
  most accurate (60.7% @ 52,104 tokens); the most token-efficient formats were least accurate —
  CSV 44.3% @ 19,524 tokens, TOON 47.5% @ 21,518; JSON mid-pack (52.3% @ 66,396); markdown-table a
  good accuracy/cost middle (51.9% @ 25,140). Accuracy and token-efficiency trade off. [VERIFIED — fetched]
  [Source](https://www.improvingagents.com/blog/toon-benchmarks/)
- Microsoft/MIT, "Does Prompt Formatting Have Any Impact on LLM Performance?" (Nov 2024): same
  content rendered as plain text / Markdown / JSON / YAML changes performance by up to 40% for
  GPT-3.5-turbo (code translation); GPT-4 is markedly more robust; GPT-3.5 preferred JSON while
  GPT-4 preferred Markdown — i.e., **no universally best format, and bigger models care less**.
  [Source](https://arxiv.org/abs/2411.10541)
- "Table Meets LLM" (WSDM'24): for table understanding with GPT-3.5/4, markup (HTML) beat
  NL-with-separators by ~6.76%; structural understanding depends heavily on few-shot examples
  (~30 pp drop zero-shot). Older GPT-3.5/4-era result; direction may not hold for 2025-26 models.
  [Source](https://arxiv.org/abs/2305.13062)
- "Format as a Prior: Quantifying and Analyzing Bias in LLMs for Heterogeneous Data" (Aug 2025):
  format representation *alone* systematically shifts LLM behavior on mixed data.
  [Source](https://arxiv.org/html/2508.15793v1)
- "LLMs Are Biased Towards Output Formats!" (Aug 2024): first systematic eval of output-format bias;
  significant format bias across SOTA LLMs on 8 generation tasks. [Source](https://arxiv.org/abs/2408.08656)

### Output-side (generation/structured-output reliability)

- "Let Me Speak Freely?" (Tam et al., EMNLP 2024 Industry): format restrictions (JSON-mode etc.)
  degraded reasoning-task performance, with stricter constraints hurting more; classification tasks
  sometimes improved. Proposed NL-first-then-format as mitigation. [Source](https://arxiv.org/abs/2408.02442)
  - **[CONTESTED — partial failure to replicate]** dottxt's "Say What You Mean" rebuttal: the paper
    used different prompts for structured vs. unstructured runs and an LLM (Claude-3-Haiku) as answer
    parser; with matched prompts and proper parsing, structured generation performed as well as or
    better than unstructured on the same tasks (the paper's <10% JSON-mode "Last Letter" result did
    not reproduce). [VERIFIED blog] [Source](https://blog.dottxt.ai/say-what-you-mean.html)
  - Follow-up academic benchmark: "Generating Structured Outputs from Language Models: Benchmark and
    Studies" (Jan 2025) continues this evaluation line. [Source](https://arxiv.org/html/2501.10868v1)
- OpenAI Structured Outputs (Aug 6, 2024): constrained decoding against a JSON Schema; announced
  100% on OpenAI's internal complex-schema-following eval for gpt-4o-2024-08-06 vs <40% for
  gpt-4-0613 with prompting alone. Syntax-validity is now essentially a solved problem when
  constrained decoding is available (semantic correctness is not).
  [Source](https://openai.com/index/introducing-structured-outputs-in-the-api/)
- Berkeley Function Calling Leaderboard (BFCL): standard eval for emitting correct structured tool
  calls (AST-match + executable). Robustness findings: minor paraphrases of user queries cause
  11–19 pp absolute accuracy drops on hard splits; adding semantically-related distractor tools
  costs a further 1–8 pp. [SEARCH-DIGEST] [Source](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html),
  [BFCL paper](https://openreview.net/forum?id=2GmDdhBdDk)
- "Notation Matters" (Kutschka & Geiger, May 2026): evaluated token-optimized formats (TOON, TRON)
  inside *end-to-end agentic loops* (BFCL, MCPToolBenchPP, MCP-Universe, StableToolBench; 5
  open-weight LLMs), separating input compression from output compression. Verbatim from abstract:
  "TRON reduces tokens by up to 27% with accuracy within 14 pp of the JSON baseline. TOON achieves
  up to 18% reduction at a similar 9 pp accuracy cost, but additionally cascades on multi-turn
  parsing failures and collapses parallel tool-call output for most models." [VERIFIED — fetched abstract]
  [Source](https://arxiv.org/abs/2605.29676)
- "TOON vs JSON: A Benchmark of Plain and Constrained Decoding Generation" (Mar 2026): for
  *generation*, plain JSON had the best one-shot and final accuracy; TOON's only clear win was
  lowest token usage, traded against lower accuracy and significant degradation on some models.
  [SEARCH-DIGEST] [Source](https://arxiv.org/abs/2603.03306)

### Token-cost measurements

- Same-data token counts, measured (Improving Agents, above): JSON ≈ 1.36–1.5x YAML; XML ≈ 1.6–1.8x
  YAML; Markdown ≈ 0.9x YAML. [VERIFIED]
- Blog measurements repeatedly find YAML ~15–56% fewer tokens than equivalent JSON (varies with
  nesting/data). [WEAK — blog measurements, but directionally consistent everywhere]
  [Source](https://tashif.codes/blog/JSON-YAML-LLM)
- TOON's own repo benchmarks: ~39.9% fewer tokens than JSON at slightly *better* accuracy
  (76.4% vs 75.0%) on its own retrieval suite — **conflicts with independent tests** (Improving
  Agents could not find any circumstance where TOON was the best format, though they *did* reproduce
  TOON's numbers on TOON's own test code — the discrepancy is in test design, not measurement error).
  [VERIFIED both sides] [Source](https://github.com/toon-format/toon),
  [Independent](https://www.improvingagents.com/blog/toon-benchmarks/)

### Net reading for .sarib
Indentation-based, low-punctuation formats (YAML-like, Markdown-like) are the empirical sweet spot
for *input*: cheaper than JSON and as-or-more accurate on recent models. XML-style tag pairs are the
worst of both worlds at scale. JSON remains the safest *output* target only because constrained
decoding tooling targets it. Novel compact syntaxes pay an out-of-distribution "unfamiliarity tax"
that usually exceeds their token savings. Format effects shrink as models get bigger — design for
the pretraining distribution, not against it.

---

## Q3. Do LLMs handle explicit typed relationships better than implicit prose relationships?

- KG-LLM-Bench (Markowitz et al., NAACL 2025 KnowledgeNLP workshop): 7 LLMs x 5 KG textualization
  strategies x 5 reasoning tasks (triple retrieval, path reasoning, aggregation, multi-hop, global).
  [VERIFIED abstract; results via paper PDF in search results]
  [Source](https://arxiv.org/abs/2504.07087), [PDF](https://knowledge-nlp.github.io/naacl2025/papers/39.pdf)
  - Structured JSON scored best on average (0.42), followed by Structured YAML and List-of-Edges;
    **RDF Turtle (0.35) and JSON-LD (0.34) scored worst**. [SEARCH-DIGEST]
  - Token cost: List-of-Edges and Structured YAML under ~3,000 tokens/prompt; RDF Turtle ~8,000;
    **JSON-LD >13,000** for the same graphs — the semantic-web formats lose on accuracy AND cost.
    [SEARCH-DIGEST]
  - Simple one-triple-per-line ("list of edges") is near-top accuracy at the lowest token cost;
    grouping by subject (YAML/JSON) helps on aggregation tasks.
- Explicit triples vs. retrieved prose: KG-triple prompting beat passage-based prompting for
  long-tail factual QA in most conditions (LTGen). [SEARCH-DIGEST]
  [Source](https://www.sciencedirect.com/science/article/abs/pii/S095070512500694X)
- The cost asymmetry (structure pre-provided vs. inferred): LLM relation *extraction* — inferring
  typed structure from prose — is exactly the expensive, unreliable step:
  - Zero-shot end-to-end biomedical relation extraction with OpenAI models is "inching closer" to
    supervised methods on some datasets but still struggles on inputs expressing multiple relations.
    [SEARCH-DIGEST] [Source](https://arxiv.org/abs/2504.04083)
  - Zero-shot/cross-lingual RE reaches roughly 68–89% of supervised accuracy. [SEARCH-DIGEST]
    [Source](https://www.emergentmind.com/topics/zero-shot-entity-relation-extraction)
  - GraphRAG's dominant cost line-item IS this inference step done in bulk at index time (see Q1
    cost bullets); LazyGraphRAG's 1000x saving comes from *not* doing it up-front.
    [Source](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)
- Structure provided implicitly by *interaction* (agentic multi-round search) partially substitutes
  for explicit graph structure, but explicit structure still wins for complex multi-hop and is more
  stable (RAGSearch). [VERIFIED abstract] [Source](https://arxiv.org/abs/2604.09666)

### Net reading for .sarib
When typed relationships are *given* to the model in a cheap, familiar syntax, models use them well
(triples/YAML formats near-top). When the model must *infer* them, quality drops and cost explodes.
But heavyweight ontology serializations (RDF Turtle, JSON-LD) actively hurt: URIs, prefixes, and
context blocks quadruple token cost and reduce accuracy. Typed edges yes; semantic-web ceremony no.

---

## Q4. Context-window economics, 2024–2026

### Positional and length degradation — does "lost in the middle" persist?

- Original: Liu et al., "Lost in the Middle" (TACL 2024): U-shaped accuracy by position of relevant
  info; middle-of-context worst. [Source](https://arxiv.org/abs/2307.03172)
- RULER (2024): 17 long-context models tested; all degraded as input grew, well before their
  advertised context limits; larger windows moved the failure point out but did not remove it.
  [SEARCH-DIGEST] [Source](https://www.semanticscholar.org/paper/RULER:-What's-the-Real-Context-Size-of-Your-Models-Hsieh-Sun/ac5824e9ff924a937d9eef379d0b581de2417678)
- NoLiMa (ICML 2025): when the needle shares no literal keywords with the question (forcing
  associative rather than lexical matching), 10 of 12 models fell to half or less of their
  short-context score by 32K tokens; even GPT-4o dropped 99.3% → 69.7%. Long-context capability is
  substantially lexical-matching capability. [Source](https://arxiv.org/abs/2502.05167)
- Chroma "Context Rot" report (Jul 2025): 18 models including GPT-4.1, Claude 4, Gemini 2.5 —
  performance degrades non-uniformly as input length grows even on trivially simple tasks;
  degradation accelerates when needle-question semantic similarity is low, when topically-related
  distractors are present, and varies with haystack structure. [Source](https://research.trychroma.com/context-rot)
- HELMET / LongBench-v2-era evals continue to surface the same degradation patterns on 2025 frontier
  models. [SEARCH-DIGEST] [Source](https://arxiv.org/pdf/2410.02694)
- **Verdict: mitigated at small scales, not solved. Persists in current frontier models once lexical
  overlap is removed or distractors added.**

### Long-context vs. RAG

- Li et al. (Google DeepMind), "RAG or Long-Context LLMs?" (2024): when compute is unconstrained,
  long-context beats RAG on average for Gemini-1.5/GPT-4-class models, but RAG's dramatically lower
  cost is decisive in practice; their Self-Route hybrid (model self-decides) gets near-LC quality at
  much lower cost. [Source](https://arxiv.org/abs/2407.16833)

### KV-cache / prompt-caching economics (why byte-stable prefixes matter)

- Anthropic prompt caching: cache reads billed at ~10% of base input price (90% discount), cache
  writes at 1.25x; 5-minute default TTL (1-hour option); ~1,024-token minimum cacheable block; cache
  matches on *exact* prefix — a single changed character invalidates everything after it.
  [SEARCH-DIGEST of official docs via guides] [Source](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models)
- Manus, "Context Engineering for AI Agents" (Jul 2025): production-agent view — KV-cache hit rate is
  "the single most important metric" for agents; agent contexts run ~100:1 input:output tokens;
  cached vs uncached input differs ~10x in price ($0.30 vs $3.00/MTok on Claude Sonnet). Rules:
  keep the prompt prefix byte-stable (no timestamps up front), make context append-only, ensure
  deterministic serialization (they specifically warn that JSON libraries with unstable key ordering
  silently break caching), mask rather than remove tools. [Source](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)
- Anthropic, "Effective context engineering for AI agents" (Sep 2025): context is "a critical,
  finite resource with diminishing marginal returns" (attention budget); find "the smallest possible
  set of high-signal tokens"; techniques for long horizons: compaction (summarize + reinit),
  structured note-taking (external memory the agent re-reads), sub-agent architectures (isolated
  contexts returning condensed summaries). [Source](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
  - Companion cookbook implements memory + compaction + tool-result clearing patterns.
    [Source](https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools)
- MCP resource pattern: context exposed as URI-addressed resources that agents load on demand
  (rather than bulk-loading); MCP was donated to the Linux Foundation's Agentic AI Foundation in
  Dec 2025 alongside AGENTS.md — the ecosystem is standardizing on *addressable, lazily-loaded*
  context. [Source](https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation)

### Net reading for .sarib
Economics push hard toward: (1) small high-signal serializations over exhaustive dumps; (2)
byte-stable, deterministic, append-friendly file layout (cache-hit-maximizing); (3) addressable
chunks (stable node IDs / section anchors) so agents can load subgraphs instead of whole files;
(4) putting the most-load-bearing facts early or late in any large serialization, never only
mid-file.

---

## Q5. Prior "LLM-native format" attempts — what happened to them?

- **llms.txt** (Jeremy Howard / Answer.AI, proposed Sep 3, 2024): Markdown index file at site root
  to give LLMs a curated, context-window-sized map of a website.
  [Source](https://searchengineland.com/llms-txt-proposed-standard-453676)
  - Adoption: ~10.13% of 300k domains studied (SE Ranking, 2025). [SEARCH-DIGEST]
    [Source](https://llms-txt.io/blog/is-llms-txt-dead)
  - Actual consumption is near-zero: OtterlyAI's 90-day measurement found 84 of 62,100 AI-bot
    requests (~0.1%) touched llms.txt; no major AI search system (Google, OpenAI, Perplexity,
    Anthropic) reads it. Google's John Mueller compared it to the discredited keywords meta tag;
    Gary Illyes confirmed (Jul 2025) Google won't support it. [SEARCH-DIGEST]
    [Source](https://medium.com/@kaispriestersbach/the-llms-txt-is-dead-more-precisely-a-dud-ab7bee4f469c),
    [Source](https://www.indexlab.ai/blog/llms-txt-does-it-actually-work-october-2025-updated)
  - Surviving niche: dev-tool documentation as a structured entry point for coding agents
    (Cursor, Claude Code) — Howard's original use case. Lesson: a format proposal without committed
    *consumers* is a dead letter; the file format itself (plain Markdown) was never the problem.
- **TOON — Token-Oriented Object Notation** (Johann Schopplich, 2025): CSV-meets-YAML compact
  notation for uniform arrays; real ~40–60% token savings on tabular data.
  [Source](https://github.com/toon-format/toon), [InfoQ coverage](https://www.infoq.com/news/2025/11/toon-reduce-llm-cost-tokens/)
  - Independent evaluations (Improving Agents Oct 2025; "Notation Matters" May 2026; TOON-vs-JSON
    generation benchmark Mar 2026) consistently find accuracy costs — worst-in-class on nested-data
    retrieval, ~9 pp accuracy cost + cascading multi-turn parse failures in agentic loops, lower
    generation accuracy than plain JSON. Official-repo benchmarks show the opposite on their own
    test design; the conflict is unresolved but the independent evidence is broader.
    [Source](https://www.improvingagents.com/blog/toon-benchmarks/), [Source](https://arxiv.org/abs/2605.29676),
    [Source](https://arxiv.org/abs/2603.03306)
- **POML — Prompt Orchestration Markup Language** (Microsoft, Aug 2025): HTML-like markup
  (`<role>`, `<task>`, `<example>`) + styling/templating for *prompt engineering*, not knowledge
  representation. Tooling exists (VS Code extension, SDKs); adoption appears modest; it competes
  with plain Markdown prompts. [Source](https://arxiv.org/abs/2508.13948), [Repo](https://github.com/microsoft/poml)
- **AGENTS.md** (OpenAI + Google + Cursor + Factory + Sourcegraph, Aug 2025): "a README for agents" —
  plain Markdown, one well-known filename, no new syntax. >20k GitHub repos within weeks; >60k by
  late 2025; moved into the Linux Foundation's Agentic AI Foundation (Dec 2025, alongside MCP and
  goose); AAIF reached 170+ member orgs by Apr 2026. The one unambiguous adoption success in this
  space. [Source](https://www.infoq.com/news/2025/08/agents-md/),
  [Source](https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation),
  [Source](https://openai.com/index/agentic-ai-foundation/)
- Pattern across attempts: **conventions built on boring, pretraining-saturated syntax (Markdown)
  with committed tool-side consumers succeed (AGENTS.md, MCP). Novel syntaxes optimizing tokens
  (TOON) or semantics (RDF/JSON-LD, per Q3) lose accuracy; formats without consumers (llms.txt as
  used by SEO) go unread.**

---

## Design lessons for .sarib (evidence-tied)

1. **Stay inside the pretraining distribution.** Use familiar surface syntax — indentation +
   `key: value` (YAML-like), Markdown headers, one-triple-per-line edges. Novel compact notations
   pay an accuracy tax that exceeds their token savings (TOON: −9 pp + multi-turn parse cascades,
   [arXiv 2605.29676](https://arxiv.org/abs/2605.29676); TOON worst on nested retrieval,
   [Improving Agents](https://www.improvingagents.com/blog/toon-benchmarks/)); semantic-web formats
   are worst of all (JSON-LD/Turtle bottom on accuracy at 3–4x token cost,
   [KG-LLM-Bench](https://arxiv.org/abs/2504.07087)).
2. **One fact per line, typed edges, no ceremony.** Simple (subject, predicate, object) line formats
   are near-top accuracy at the lowest token cost, and grouping edges by subject (YAML-style blocks)
   helps aggregation tasks ([KG-LLM-Bench](https://arxiv.org/abs/2504.07087)). Explicitly provided
   triples beat prose passages for long-tail facts
   ([LTGen](https://www.sciencedirect.com/science/article/abs/pii/S095070512500694X)). Skip URIs,
   prefixes, and @context blocks entirely.
3. **Optimize for tokens second, comprehension first — and avoid XML-style syntax.** The empirical
   sweet spot is YAML/Markdown (~30–40% cheaper than JSON with equal-or-better accuracy); the
   cheapest formats (CSV/TOON) lose the most accuracy, and tag-pair markup costs the most tokens AND
   the most accuracy on bulk data ([Improving Agents nested benchmark](https://www.improvingagents.com/blog/best-nested-data-format/)).
4. **Make the graph cheap to build and lazy to exploit.** GraphRAG's benefit is real for multi-hop /
   global questions but its LLM-extraction indexing cost killed it ($33k/5GB early 2024, then
   LazyGraphRAG's 1000x cheaper deferred approach,
   [Microsoft Research](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)).
   .sarib's core value proposition should be that humans and agents author typed structure
   *incrementally at write time* — deleting the extraction pass — and the file must remain useful
   read linearly, without requiring graph tooling ([GraphRAG-Bench](https://arxiv.org/abs/2506.05690),
   [RAGSearch](https://arxiv.org/abs/2604.09666)).
5. **Design the byte layout for KV-cache economics.** Deterministic canonical ordering, append-only
   growth (new facts at the end), no volatile fields (timestamps, counters) near the top of file:
   exact-prefix caching gives ~10x cheaper input tokens and agents run at ~100:1 input:output
   ([Manus](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus),
   [caching guides](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models)).
6. **Assume the whole file will NOT be in context.** Length degradation persists in frontier models
   (NoLiMa: 10/12 models at ≤50% of baseline by 32K without lexical overlap,
   [arXiv 2502.05167](https://arxiv.org/abs/2502.05167); [Chroma context rot](https://research.trychroma.com/context-rot)).
   Give every node a stable, human-readable ID/anchor so agents and MCP-style resource loaders can
   retrieve minimal subgraphs; support summary-level sections (the compaction/note-taking pattern,
   [Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)).
7. **Keep lexical redundancy — don't over-normalize names.** NoLiMa shows retrieval collapses when
   surface keywords are removed; storing only opaque IDs with lookup tables would recreate that
   failure inside the format. Repeat human-readable entity names at the point of use
   ([NoLiMa](https://arxiv.org/abs/2502.05167)).
8. **Provide a lossless JSON mapping, but don't make JSON the authoring format.** Constrained
   decoding makes JSON-schema output ~100% syntactically reliable
   ([OpenAI](https://openai.com/index/introducing-structured-outputs-in-the-api/)), so a .sarib⇄JSON
   isomorphism lets agents *write* the graph through existing structured-output tooling — while the
   canonical on-disk format keeps the cheaper, more comprehensible YAML/Markdown-style surface.
   Keep any required output schema loose enough not to constrain reasoning mid-generation
   (["Let Me Speak Freely?"](https://arxiv.org/abs/2408.02442) — contested by
   [dottxt](https://blog.dottxt.ai/say-what-you-mean.html), but the safe design is reasoning-then-structure).
9. **Adoption lesson: ship consumers, not just a spec.** llms.txt got ~10% publisher adoption and
   ~0.1% actual bot reads because no major consumer committed
   ([analysis](https://medium.com/@kaispriestersbach/the-llms-txt-is-dead-more-precisely-a-dud-ab7bee4f469c));
   AGENTS.md won by being plain Markdown at a well-known path with day-one tool support across
   Codex/Cursor/Copilot/etc. ([InfoQ](https://www.infoq.com/news/2025/08/agents-md/)). .sarib needs a
   reference MCP server / CLI reader from day one.

---

## Replication & reliability flags (summary)

- **Failed/partial replication:** "Let Me Speak Freely" headline result (structured output hurts
  reasoning) did not reproduce under matched prompts (dottxt). Treat as contested; the field's
  current view is "constrained decoding done right is roughly neutral."
- **Conflicting benchmarks:** TOON repo benchmarks vs. three independent evaluations. Independent
  side is broader and includes a peer-reviewed-track paper (Notation Matters).
- **Weakly sourced numbers:** $33k GraphRAG indexing figure (single practitioner source);
  GraphRAG-Bench's specific 13.4%/16.6%/2.3x figures and KG-LLM-Bench's 0.42/0.35/0.34 averages were
  taken from search digests of the papers, not re-read from the papers' tables.
- **Vendor-conflicted:** FalkorDB GraphRAG accuracy benchmark; TOON's own benchmarks; (and note
  Microsoft evaluating Microsoft in the original GraphRAG paper, via LLM-as-judge).
- **Sample sizes:** Improving Agents benchmarks: 1,000 questions/format/model, 95% CIs reported, but
  small models only (GPT-5 Nano / Gemini 2.5 Flash Lite / Llama 3.2 3B) — format sensitivity is
  known to shrink with model size (arXiv 2411.10541), so effect sizes on frontier models are likely
  smaller. NoLiMa: 12 models; Chroma: 18 models; RULER: 17 models.

# Syntax & Legibility — research for the author-facing surface (Phase D)

Raw research notes for the .sarib language project. Beat: (Q1) how a text format can convey the
*spatial shape/size* of a knowledge tree to humans **and** LLMs; (Q2) 2026 refresh on token-efficiency
and legibility of surface syntaxes; (Q3) how to extend Markdown without breaking CommonMark rendering.

Compiled: 2026-07-15. Method: ~18 web searches + primary-source fetches. Confidence labels:
**[VERIFIED]** = read in fetched primary source; **[SEARCH-DIGEST]** = seen in search summaries of the
cited source, not fully fetched; **[WEAK]** = single secondary source, indicative only;
**[UNVERIFIED]** = plausible/analytic, no adequate source found — flagged for later measurement.
Cross-refs: prior format-benchmark evidence lives in `ai-context.md` (RQ7); Markdown adoption physics
and MacFarlane's "Beyond Markdown" postmortem live in `markup-and-documents.md` (RQ3).

---

## Q1 — Conveying the spatial shape/size of the tree (the novel requirement)

### Information foraging & information scent (Pirolli & Card)

- Information Foraging Theory (Pirolli & Card, PARC, 1990s) models information seekers as foragers who
  maximize `rate of gain = information value / cost of obtaining it`, and comprises three sub-models:
  **scent, patches, diet**. [Source](https://en.wikipedia.org/wiki/Information_foraging)
  [Primary — PARC tech report](http://act-r.psy.cmu.edu/wordpress/wp-content/uploads/2012/12/280uir-1999-05-pirolli.pdf)
- **Information scent** = "the (imperfect) perception of the value, cost, or access path of information
  sources obtained from proximal cues" (citations, links, icons, labels). Users *satisfice*: they read
  cheap proximal cues to predict distal value, and stop when scent drops. [VERIFIED — Pirolli 2004]
  [Source](http://act-r.psy.cmu.edu/wordpress/wp-content/uploads/2012/12/515uir-2004-07-pirolli.pdf)
  [Source](https://www.nngroup.com/articles/information-foraging/)
- Practical corollary (NN/g, Nielsen): users leave a "patch" (page/section) when its expected remaining
  yield falls below the cost of going elsewhere; strong, specific proximal cues keep them in-place and
  route them accurately. Weak/ambiguous cues cause premature abandonment or wrong turns.
  [Source](https://www.uxtigers.com/post/information-scent)
- Strong, *specific* labels are claimed to cut navigation time 30–50% vs. generic labels. [WEAK — single
  secondary UX source; treat as directional, not a measured constant]
  [Source](https://uxuiprinciples.com/en/principles/information-scent)
- Wayfinding decomposes into four cue types, all relevant to a text tree: **identification** (where am I
  — breadcrumbs, titles, active state), **orientation** (overall structure — sitemaps/outlines),
  **route decision** (where next — labels, scent), **closure** (have I arrived). [WEAK — secondary]
  [Source](https://www.wearediagram.com/blog/using-wayfinding-to-design-intuitive-navigation)
- **Design read:** the format's job is to emit *proximal cues that predict distal content* at every node —
  a child's label, type, and a cheap size/shape hint should let a reader (human or model) estimate the
  value of descending *without* descending. Scent is the core requirement behind "convey the spatial idea."

### Sense of place & spatial memory in documents (why size-intuition needs boundaries)

- Text memory is partly *spatial*: readers encode where on the page/in the document a fact sat and use
  those spatial markers to relocate it. When markers move (scrolling), recall and re-finding degrade.
  [SEARCH-DIGEST of peer-reviewed work] [Source](https://twosidesna.org/wp-content/uploads/sites/16/2018/05/To_Scroll_or_Not_to_Scroll_Scrolling_Working_Memory_Capacity_and_Comprehending_Complex_Texts.pdf)
- "Scrolling destroys the fixed location of digital text, creating an infinite vertical flow without
  boundaries or stable reference points"; pagination, by contrast, "gives users a sense of progress and
  completion, supports spatial memory." [WEAK — secondary synthesis, but consistent with the paper above]
  [Source](https://cardcatalogforlife.substack.com/p/what-scrolling-did-to-reading)
  [Source](https://www.uxmatters.com/mt/archives/2018/11/paging-scrolling-and-infinite-scroll.php)
- **Why infinite feeds give no size intuition:** with no boundary and no position-of-N marker, there is
  nothing to estimate extent against. The lesson for .sarib: *stable, addressable landmarks and explicit
  extent markers* (counts, totals, "x of N") are what turn an unbounded stream into a navigable space.
  Stable node IDs already required for edits (see `ai-context.md` lesson 6) double as spatial anchors.

### Outliner / fold affordances — how existing tools show depth, breadth, position

- **Fold indicators**: outliners (Obsidian, Workflowy, Dynalist, org-mode) place a disclosure marker
  (arrow / `+`/`–`) on any node *that has children* — presence of the glyph itself signals "there is more
  below," i.e., breadth/depth exists here without showing it. [Source](https://medium.com/obsidian-observer/demystifying-obsidians-outlining-superpowers-20c077793356)
- **Indentation = depth**, read pre-attentively: nesting level is legible at a glance from left-edge
  position; this is the cheapest possible depth encoding and is shared by outliners, code, and YAML.
  (Analytic; corroborated across all outliner sources above.)
- **Breadcrumbs = position + path**: a breadcrumb trail answers "where am I in the whole" and restores
  context when zoomed/focused into a subtree. [Source](https://uxpatterns.dev/patterns/navigation/breadcrumb)
  Numbered headings (`1.2.3`) encode the same path-and-depth information *inline in plain text* — a
  breadcrumb you can read without a viewer.
- **Minimaps / document outlines** give a whole-shape overview (a compressed map of the document's
  structure) alongside the detail view — the "map before territory" affordance in editors. [SEARCH-DIGEST]
  [Source](https://medium.com/obsidian-observer/demystifying-obsidians-outlining-superpowers-20c077793356)

### Compact notations that encode tree SHAPE / SIZE (the concrete ask)

- **org-mode statistics cookies** — the strongest existing precedent for a *compact inline subtree-size
  metric*. Insert `[/]` or `[%]` in a headline and it auto-renders as `[2/5]` (n-of-m done) or `[40%]`,
  counting direct children (or the whole subtree if configured). It is plain text, human-writable, and
  machine-updated. [VERIFIED — Org manual]
  [Source](https://orgmode.org/manual/Breaking-Down-Tasks.html) [Source](https://orgmode.org/manual/Checkboxes.html)
- **Collapsed-node child counts**: showing "N hidden children" on a collapsed bullet is a repeatedly
  *requested* affordance (Dynalist supports word/item counts under an item; a persistent count badge on
  collapsed nodes is a long-standing feature request) — evidence that users want breadth-at-a-glance even
  where tools don't ship it by default. [Source](https://talk.dynalist.io/t/an-item-is-collapsed-show-the-number-count-of-items-right-under-it/722)
- **File-tree precedents**: `tree`/file managers convey shape via indentation + line-drawing glyphs
  (`├─`, `└─`) and summary footers ("N directories, M files"). The pattern generalizes: *indentation for
  depth, terminal summary for size.* [UNVERIFIED as a citable claim — common-knowledge tooling behavior]
- **Notation inventory for shape/size** (synthesis; each element attested above):
  | Property to convey | Compact plain-text encoding | Precedent |
  |---|---|---|
  | Depth (how deep am I) | indentation; dotted path `1.2.3`; breadcrumb | outliners, headings |
  | Breadth (how many siblings/children) | `[k/n]`, count badge `(12)`, `n of N` | org cookies, Dynalist |
  | Subtree size (how big below) | subtree count `⊕128`, size annotation, `[%]` | org cookies, `tree` footer |
  | Position (where among peers) | `3/7`, ordinal, breadcrumb tail | pagination, breadcrumbs |
  | Presence of hidden content | fold glyph / trailing `…` / marker | all outliners |

### Does explicit structural signposting help LLMs? (map-before-detail)

- **Skeleton-of-Thought** (Ning et al., ICLR 2024): make the model emit a *skeleton* (an outline of
  3–5-word points) first, then expand each point. Explicitly "planning the answer structure in language"
  gave speed-ups across 12 LLMs and *improved answer quality* on several question categories — evidence
  that an explicit structural map is not just navigational sugar but improves generation. [VERIFIED —
  fetched abstract] [Source](https://arxiv.org/abs/2307.15337)
- **RAPTOR** (Sarthi et al., ICLR 2024): build a *tree of recursive summaries* (leaves = chunks, higher
  nodes = summaries of clusters) so retrieval can pull context "at different levels of abstraction."
  Coupling RAPTOR with GPT-4 improved QuALITY QA by ~20% — a hierarchical map materially helps models
  reason over long material. [VERIFIED abstract] [Source](https://arxiv.org/abs/2401.18059)
- **Hierarchical summarization** generally: dividing long documents into a hierarchy and summarizing
  bottom-up (hierarchical merging) is a dominant long-document strategy; injecting explicit document
  structure improves summarization of long/structured docs. [SEARCH-DIGEST]
  [Source](https://arxiv.org/abs/2502.00977) [Source](https://link.springer.com/article/10.1007/s44443-025-00041-2)
- **Net read for .sarib:** the same "table-of-contents / skeleton before detail" that gives humans a
  sense of place demonstrably helps LLMs. A .sarib file that carries a cheap structural map (typed
  headings + counts/size hints, summaries at container nodes) is emitting exactly the signal SoT/RAPTOR
  construct *at runtime* — so bake it into the format instead of regenerating it per query.

---

## Q2 — Token-efficiency & legibility of surface syntaxes for LLMs (2026 refresh)

*Prior findings (in `ai-context.md`, RQ7 Q2) stand: YAML/Markdown ~30–40% cheaper than JSON with
equal-or-better input accuracy; indentation formats beat tag-pair (XML) formats on both cost and
accuracy; novel compact notations (TOON/TRON) pay an out-of-distribution accuracy tax (~9 pp) that
usually exceeds their token savings. This section refreshes and extends: whitespace handling, glyph
tokenization, and emphasis encoding.*

### Indentation / significant whitespace — the failure modes

- Whitespace-significant syntax is fragile for *humans and machines*: with YAML, "incorrect indentation
  is the most common cause of syntax errors," and a 2-space standard "blurs indent levels together" so
  "deeply nested blocks written without explicit de-indents make YAML a poor experience." Guidance is to
  avoid nesting beyond ~2–3 levels. [WEAK/practitioner, but the consensus is uniform]
  [Source](https://moldstud.com/articles/p-understanding-yaml-parsing-errors-causes-fixes-and-best-practices)
  [Source](https://utcc.utoronto.ca/~cks/space/blog/tech/YamlWhitespaceProblem)
- Implication for LLMs: models generate token-by-token with no column counter, so *pure* indentation
  depth (especially deep, small-step indents) is exactly the kind of state they lose — an
  indentation-drift / miscount risk on write. [UNVERIFIED as a measured LLM result — no direct benchmark
  found; flagged for measurement. The human-side fragility is well attested; the model-side risk is a
  reasoned extrapolation and should be benchmarked before spec freeze per the Evidence rule.]
- Mitigation pattern to test: pair indentation (cheap, pre-attentive depth for shallow trees) with a
  *redundant explicit* depth/parent cue at each node (dotted path or parent-id) so depth is recoverable
  without counting columns — belt-and-suspenders that also survives reflow/streaming.

### Which glyphs are token-cheap (sigils/markers)

- Modern GPT tokenizers (tiktoken cl100k/o200k, GPT-2 lineage) are **byte-level BPE**: base vocabulary is
  the 256 byte values, so every ASCII punctuation character is representable, and frequent ones get merged
  into common tokens. Punctuation/symbols are grouped and "optionally preceded by a space" during merges,
  so a *leading space* changes the token (`"#"` vs `" #"`). [Source](https://huggingface.co/docs/transformers/tokenizer_summary)
- Concretely, tiktoken splits `"tiktoken is great!"` → `["t","ik","token"," is"," great","!"]`: note `"!"`
  is a single token and words carry their leading space. Common single-character ASCII sigils used by
  Markdown (`#  -  *  >  :  |  space`) are high-frequency and therefore typically **single tokens**;
  leading-space variants are usually their own single tokens too. [VERIFIED example — OpenAI cookbook]
  [Source](https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken)
- **Emoji, CJK, and rare Unicode glyphs fragment** into multiple byte-tokens (one emoji can be several
  tokens; per-emoji cost varies 14–24 tokens across tokenizer families for the same set) — they are the
  *opposite* of token-cheap and are also OOD for structural roles. Avoid emoji/exotic glyphs as
  structural sigils. [Source](https://atul4u.medium.com/tokenizer-comparison-part2-comprehensive-tokenizer-performance-analysis-a8e0613bed0d)
  [Source](https://huggingface.co/docs/transformers/tokenizer_summary)
- **Multi-character sigils** (`::`, `[[`, `]]`, `^`, `{#`, `:::`) may or may not be a single token
  depending on training frequency; `::` and `[[ ]]` are common in code/wikis and *often* merge, but exact
  counts differ by tokenizer. [UNVERIFIED — no per-glyph table found; MUST verify chosen sigils against
  tiktoken/o200k and the target open-weight tokenizers before freezing the grammar. This is a direct
  application of the "benchmark before spec freeze" Evidence rule.]
- **Design read:** prefer glyphs that (a) are single-token in the major tokenizers, (b) already carry the
  intended meaning in the pretraining distribution (Markdown/email/code conventions), and (c) don't
  require a leading space to stay cheap. Verify empirically; don't assume.

### Emphasis / importance / hierarchy — encode cheaply and legibly

- Macro-structure helps models; micro-emphasis mostly doesn't. Well-structured Markdown (headings,
  lists, code fences) "improves reasoning accuracy in complex text processing tasks," but an LLM's
  ability to interpret **bold/italic emphasis** reliably "is surprisingly weak and should be considered a
  low-impact tweak … use emphasis like salt, not the main course." [WEAK/practitioner synthesis, but
  aligns with the peer-reviewed format-sensitivity literature] [Source](https://www.neuralbuddies.com/p/marking-up-the-prompt-how-markdown-formatting-influences-llm-responses)
  [Source](https://www.searchcans.com/blog/markdown-vs-html-llm-context-optimization-2026/)
- Underlying peer-reviewed anchor (already in `ai-context.md`): prompt *formatting* moves performance up
  to ~40% on smaller models and the effect shrinks with model size; no universally best format.
  [Source](https://arxiv.org/html/2411.10541v1)
- **Design read:** encode importance **structurally and explicitly**, not typographically. A first-class
  priority/weight *field* (e.g., a small enumerated scale) that both humans scan and models read as data
  beats relying on `**bold**` to carry semantic weight — bold is a rendering hint, not a reliable signal.
  Reserve emphasis glyphs for human scanning; put load-bearing importance in an addressable attribute so
  it survives projection and is queryable.

---

## Q3 — Extending Markdown without breaking CommonMark rendering

*Goal: files must render acceptably in any CommonMark renderer (our adoption carrier — see
`markup-and-documents.md` lesson 4), while carrying typed structure an aware parser can exploit. The
core defect to route around is MacFarlane's: Markdown has "no general way to add attributes … and no
natural extension mechanism." [Source](https://johnmacfarlane.net/beyond-markdown.html)*

### The attribute/directive families (the four live conventions)

- **Pandoc attributes** — the most widely deployed attribute syntax. Curly-brace attribute lists attach
  id/class/key-value to elements: `[text]{#id .class key="value"}` (bracketed span) and fenced divs
  `::: {#id .class key="value"} … :::`. A bare word after `:::` is treated as a class. [VERIFIED — Pandoc
  docs] [Source](https://pandoc.org/demo/example33/8.18-divs-and-spans.html)
  [Source](https://benjaminwuethrich.dev/2020-05-04-everything-pandoc-markdown.html)
  - CommonMark-fallback note: unknown `{...}` after text and `:::` fences degrade to visible literal text
    in a vanilla renderer (ugly but non-destructive) — acceptable graceful degradation.
- **CommonMark "generic directives"** (MacFarlane's proposal, long-discussed on the CommonMark forum):
  a single generic block/inline directive syntax so extensions don't fork the grammar — "as simple and
  markdown-like as possible while accommodating many use cases." Not ratified into core after years of
  discussion (cautionary: even the reference community couldn't converge). [Source](https://talk.commonmark.org/t/generic-directives-plugins-syntax/444)
- **MyST directives & roles** (superset of CommonMark, RST-inspired): block **directives** reuse the code
  fence — ```` ```{name} ```` with an args line, an options block (`:key: value`), then content — and
  inline **roles** are one-liners: `` {rolename}`content` ``. Cleanly Markdown-compatible because it
  rides fences and backticks. [Source](https://mystmd.org/spec/overview)
  [Source](https://myst-parser.readthedocs.io/en/latest/syntax/roles-and-directives.html)
- **markdown-it container plugins** — the de-facto implementation route for `:::name … :::` custom
  containers in the JS ecosystem (VitePress/Docusaurus admonitions etc.); confirms `:::` fenced
  containers are a widely-shipped, renderer-supported extension shape. [SEARCH-DIGEST]
  [Source](https://talk.commonmark.org/t/generic-directives-plugins-syntax/444)

### djot — MacFarlane's own "Beyond Markdown, done right" (the key lesson set)

- **What it is:** djot (jgm/John MacFarlane, creator of CommonMark + Pandoc) is a light markup designed to
  be "more coherent and full-featured than CommonMark" and, crucially, **parseable without backtracking**
  — Markdown requires the parser to go back and reinterpret; djot was designed so it never has to.
  [Source](https://github.com/jgm/djot) [Source](https://php-collective.github.io/djot-php/guide/why-djot)
  [Source](https://johnmacfarlane.net/tools.html)
- **What it fixed vs Markdown** [SEARCH-DIGEST across corroborating sources]:
  - **Unambiguous emphasis:** consistent single characters — `_` emphasis, `*` strong — with a
    *balancing* rule, so results are always predictable (vs CommonMark's "17 principles" that still leave
    cases undecided, per Beyond Markdown). [Source](https://zine.dev/2022/12/djot-markdown-alternative/)
    [Source](https://johnmacfarlane.net/beyond-markdown.html)
  - **Attributes on ANY element:** `{.class #id key="value"}` can attach to any block or inline — the
    single feature Markdown lacks — plus **generic containers** (`:::`), definition lists, footnotes,
    tables, math, and new inline types (insert/delete/highlight/super/subscript). [Source](https://brunovellutini.com/posts/djot/)
    [Source](https://www.jonashietala.se/blog/2024/02/02/blogging_in_djot_instead_of_markdown/)
  - **Locality / streamability:** the no-backtracking design means a construct is identifiable from its
    shape locally — directly relevant to streaming LLM generation and incremental agent edits (the exact
    property `markup-and-documents.md` lesson 7 demands). [Source](https://github.com/jgm/djot)
- **The catch for .sarib:** djot is *not* a CommonMark superset — it is a cleaner *replacement* with
  different rules, so raw djot does **not** render correctly in a plain Markdown renderer. It is the right
  source of *design lessons* (unambiguous glyphs, attributes-on-everything, no-backtracking locality) but
  the *wrong adoption strategy* for us, since our carrier is "renders in any Markdown tool." Take djot's
  discipline; keep Pandoc/MyST-style CommonMark-compatible surface. [Source](https://php-collective.github.io/djot-php/guide/why-djot)

### Front matter & inline metadata conventions

- **Front matter:** YAML (or TOML) between `---` fences at file top is the ubiquitous document-metadata
  convention (Jekyll/Obsidian/Hugo/Pandoc). It is *not* CommonMark core, but virtually every renderer
  either parses or harmlessly hides it — safe carrier for file-level graph metadata. [SEARCH-DIGEST;
  corroborated in `markup-and-documents.md` (Jekyll front-matter) ]
- **Obsidian/Dataview inline fields:** `key:: value` writes a machine-readable field inline; `[key:: value]`
  (bracketed) renders both key and value, `(key:: value)` (parenthesized) hides the key and shows only the
  value. A line that is entirely `key:: value` is a full-line field. Keys are canonicalized for querying.
  This is the lightest-ceremony inline typed-metadata convention in wide human use. [Source](https://blacksmithgu.github.io/obsidian-dataview/annotation/add-metadata/)
  [Source](https://deepwiki.com/blacksmithgu/obsidian-dataview/6.3-inline-fields)
- **Block IDs & wikilinks (Obsidian/Roam):** `^blockid` at the end of a block assigns a stable, addressable
  id to that block (auto-generated on demand); `[[Note]]` / `[[Note#Heading]]` / `[[Note#^blockid]]` are
  low-ceremony typed references. `^id` is a strong precedent for **human-readable, positional-free block
  addressing** (aligns with .sarib's ids-only rule P13/D-033). [Source](https://blacksmithgu.github.io/obsidian-dataview/annotation/add-metadata/)
  [Source](https://markdownformatting.com/obsidian)
- **Typed links in prose with fallback:** the Obsidian pattern — a wikilink `[[X]]` optionally wrapped as
  an inline field `rel:: [[X]]` (or `[relates to:: [[X]]]`) — embeds a *typed edge* inside readable prose;
  in a vanilla renderer it degrades to visible text `[[X]]`, never breaking. This is the minimal-ceremony,
  Markdown-safe typed-edge pattern to emulate. [Source](https://blacksmithgu.github.io/obsidian-dataview/annotation/add-metadata/)

---

## Design lessons for .sarib syntax (evidence-tied)

1. **Emit information scent at every node — a proximal cue that predicts distal content.** Foraging theory
   says readers (and, per SoT/RAPTOR, models) decide whether to descend from cheap cues alone. Each
   container should surface a typed label + a cheap size/shape hint so value is estimable without
   descending. [Pirolli/Card](http://act-r.psy.cmu.edu/wordpress/wp-content/uploads/2012/12/280uir-1999-05-pirolli.pdf),
   [SoT](https://arxiv.org/abs/2307.15337), [RAPTOR](https://arxiv.org/abs/2401.18059)

2. **Convey tree shape/size with a compact, plain-text metric borrowed from org-mode cookies.** A
   `[k/n]`-style count (children shown/total, or subtree size) inline on a container is human-writable,
   machine-updatable, and the only battle-tested precedent for inline subtree metrics. Combine:
   *indentation or dotted path* → depth; *count badge* → breadth/size; *ordinal* → position. Make these
   derived/optional projections so they never fight determinism. [Org manual](https://orgmode.org/manual/Breaking-Down-Tasks.html),
   [Dynalist request](https://talk.dynalist.io/t/an-item-is-collapsed-show-the-number-count-of-items-right-under-it/722)

3. **Give the file a "map before territory": a skeleton/TOC of typed headings + summaries at container
   nodes.** This is exactly what SoT and RAPTOR construct at runtime to improve reasoning; baking it into
   the format captures the benefit without per-query regeneration, and gives humans the sense-of-place
   that boundaryless feeds destroy. [SoT](https://arxiv.org/abs/2307.15337),
   [RAPTOR](https://arxiv.org/abs/2401.18059), [scrolling/spatial memory](https://twosidesna.org/wp-content/uploads/sites/16/2018/05/To_Scroll_or_Not_to_Scroll_Scrolling_Working_Memory_Capacity_and_Comprehending_Complex_Texts.pdf)

4. **Stable IDs are spatial anchors, not just edit targets.** Boundaryless streams give no size intuition
   because they lack fixed reference points; addressable landmarks (`^id`-style, ids-only per P13) restore
   "where am I / how do I return here" for humans and enable subgraph loading for agents. [scrolling
   research](https://cardcatalogforlife.substack.com/p/what-scrolling-did-to-reading),
   [Obsidian block ids](https://blacksmithgu.github.io/obsidian-dataview/annotation/add-metadata/)

5. **Choose single-token, in-distribution glyphs — and verify them against real tokenizers before freeze.**
   Byte-level BPE makes common ASCII Markdown sigils (`#  -  *  >  :  |`) cheap and meaningful; emoji/exotic
   Unicode fragment into many tokens and are OOD — never use them structurally. Multi-char sigils
   (`::`, `[[`, `:::`, `{#`) must be *measured*, not assumed, in cl100k/o200k and target open-weight
   tokenizers (Evidence rule: benchmark before spec freeze). [HF tokenizer summary](https://huggingface.co/docs/transformers/tokenizer_summary),
   [tiktoken example](https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken)

6. **Encode importance/priority as an addressable field, not as typography.** Models read structure well
   but interpret bold/italic emphasis weakly ("salt, not the main course"). Put load-bearing weight in a
   queryable attribute (survives every projection); reserve emphasis glyphs for human scanning only.
   [neuralbuddies](https://www.neuralbuddies.com/p/marking-up-the-prompt-how-markdown-formatting-influences-llm-responses),
   [prompt-formatting study](https://arxiv.org/html/2411.10541v1)

7. **Stay a CommonMark superset; take djot's *discipline*, not its *format*.** djot proves the right design
   values — unambiguous single-char emphasis, attributes-on-any-element, no-backtracking locality — but it
   is a replacement, not a superset, so it won't render in Markdown tools. Adopt Pandoc/MyST-style
   attribute+directive surfaces (`[text]{#id .class k=v}`, `::: name … :::`, `` {role}`x` ``) that degrade
   to harmless literal text in vanilla renderers. [djot](https://github.com/jgm/djot),
   [Beyond Markdown](https://johnmacfarlane.net/beyond-markdown.html),
   [Pandoc divs/spans](https://pandoc.org/demo/example33/8.18-divs-and-spans.html), [MyST](https://mystmd.org/spec/overview)

8. **One blessed attribute/extension mechanism — decided up front — or suffer flavor forks.** Markdown's
   missing attribute syntax caused every platform to fork; even the CommonMark community failed to ratify
   generic directives after years. .sarib must ship *one* attribute/directive grammar from v0.1 (the
   feature MacFarlane says Markdown most lacks). [Beyond Markdown](https://johnmacfarlane.net/beyond-markdown.html),
   [generic directives thread](https://talk.commonmark.org/t/generic-directives-plugins-syntax/444)

9. **Embed typed edges in prose with the Obsidian-fallback pattern.** `rel:: [[Target]]` /
   `[relation:: [[Target]]]` carries a typed edge inline, queryable by an aware parser, and degrades to
   readable text in any renderer — minimum ceremony, non-destructive fallback, and ids-only friendly.
   [Dataview inline fields](https://blacksmithgu.github.io/obsidian-dataview/annotation/add-metadata/)

10. **Prefer redundant-explicit depth over pure significant-whitespace for deep trees.** Whitespace-only
    nesting is fragile for humans (indent blur past 2–3 levels) and a plausible miscount risk for
    token-by-token generation. Use indentation for cheap shallow depth, but carry a redundant explicit
    depth/parent cue (dotted path or parent-id) so structure is recoverable without counting columns —
    and benchmark model write-accuracy on deep indentation before committing. [YAML whitespace](https://utcc.utoronto.ca/~cks/space/blog/tech/YamlWhitespaceProblem),
    [YAML nesting guidance](https://moldstud.com/articles/p-understanding-yaml-parsing-errors-causes-fixes-and-best-practices)

---

## Reliability flags (summary)

- **Weakly sourced (secondary/practitioner):** the "30–50% navigation-time reduction from strong scent"
  figure; the "scrolling destroys spatial markers / pagination supports spatial memory" framing (the
  underlying scrolling-vs-comprehension study is peer-reviewed but was read via digest); the "emphasis is
  a low-impact tweak for LLMs" claim (aligns with peer-reviewed format-sensitivity work but the specific
  wording is a practitioner source); djot feature specifics (multiple corroborating secondary sources +
  primary GitHub, but the djot.net spec fetch timed out and was not read directly).
- **UNVERIFIED / needs measurement:** which multi-character sigils (`::`, `[[`, `:::`, `{#`) are single
  tokens per tokenizer (no per-glyph table found — must test with tiktoken/o200k + target open-weight
  tokenizers); whether LLM write-accuracy actually degrades on deep pure-indentation (reasoned from
  human-side fragility + token-by-token generation, but no direct benchmark located). Both are direct
  triggers of the "benchmark before spec freeze" Evidence rule.
- **Strong primary sources:** Pirolli & Card PARC reports (foraging/scent); Org manual (statistics
  cookies); Skeleton-of-Thought and RAPTOR (ICLR 2024 papers, abstracts fetched/verified); Pandoc docs
  (divs/spans); MyST spec; Obsidian Dataview docs; HF tokenizer summary + OpenAI cookbook (tokenization).

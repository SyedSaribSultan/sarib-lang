# RQ4 — Graph-as-text: why no graph syntax became a medium people think and write in

Raw research notes for the .sarib language project. Each bullet is a claim with an inline source.
Weakly-sourced or unverified claims are flagged inline as **[WEAK]**, **[INFERENCE]**, or **[UNVERIFIED]**.
Research date: 2026-07-15. Method: web search + primary-source fetches (W3C Turtle, openCypher/GQL, Graphviz DOT, mermaid.js docs, GitHub Blog, kdl.dev, GEXF/GraphML). Builds on `semantic-web.md` §6 (Cypher origin, property graphs) and `standards-adoption.md`.

**Hypothesis under test:** every graph-as-text syntax forces *edge-writing ceremony* — you must explicitly name both endpoints and the relation as a standalone statement — which breaks prose flow. So graphs-as-text stayed in visualization / query / config niches and never became a thinking-and-writing medium. The evidence below supports this, and identifies the one exception that proves the rule: **Mermaid, which succeeded precisely by *not* being a knowledge medium (just diagrams) and by riding Markdown/GitHub distribution.**

---

## 1. Turtle / N3 — the most human-friendly RDF, still unused for notes

Primary source: W3C, "RDF 1.1 Turtle — Terse RDF Triple Language" (Recommendation). [Source](https://www.w3.org/TR/turtle/)

- Turtle was explicitly designed for human readability: "This document defines a textual syntax for RDF called Turtle that allows an RDF graph to be completely written in a compact and natural text form, with abbreviations for common usage patterns and datatypes." [Source](https://www.w3.org/TR/turtle/)
- But the unit is still the **triple**: "A Turtle document allows writing down an RDF graph in a compact textual form. An RDF graph is made up of triples consisting of a subject, predicate and object," and "The simplest triple statement is a sequence of (subject, predicate, object) terms… terminated by '.'". Every fact is a standalone `S P O .` statement — the endpoints and relation named in full. [Source](https://www.w3.org/TR/turtle/)
- The abbreviations reduce *repetition*, not ceremony: `;` "is used to repeat the subject of triples that vary only in predicate and object," and `,` repeats subject+predicate. You still declare each relation explicitly; you just avoid re-typing the shared subject. [Source](https://www.w3.org/TR/turtle/)
- **Prefix ceremony** is mandatory for readable IRIs: the canonical spec example opens with four `@prefix` declarations (`rdf:`, `rdfs:`, `foaf:`, `rel:`) before any content. [Source](https://www.w3.org/TR/turtle/) This is the exact tax `semantic-web.md` §2 documents Verborgh complaining about ("the prefix expansion for the OWL ontology counts 30 characters"). [Source](https://ruben.verborgh.org/articles/the-semantic-web-identity-crisis/)
- Turtle's triple grammar is a subset of SPARQL's `TriplesBlock` — the authoring syntax and the query syntax are the same shape, underlining that this is a *data-statement* language, not a prose medium. [Source](https://www.w3.org/TR/turtle/)
- Verdict: Turtle is the friendliest RDF surface ever shipped and is still essentially never used to *take notes* or *think*. Being "compact and natural" was not enough, because it is still a wall of explicit triples with prefix setup — evidence that terseness ≠ writability. [Source](https://www.w3.org/TR/turtle/)

## 2. Cypher / openCypher / GQL — ASCII-art edges, but a *query* language

Primary sources: openCypher; Neo4j GQL announcement; ISO/IEC 39075; Tobias Lindaaker on Cypher's origin (already in `semantic-web.md` §6). [Source](https://opencypher.org/) [Source](https://neo4j.com/blog/cypher-and-gql/gql-database-language-standard/) [Source](https://www.thobe.org/work/cypher/)

- openCypher is "an open source specification of Cypher — the most widely adopted query language for property graph databases." [Source](https://opencypher.org/)
- Its signature is ASCII-art edges: patterns are drawn as `(a)-[:REL]->(b)` — "GQL uses ASCII art syntax to represent the patterns of data that you're searching for," letting users "visually express graph patterns with nodes and relationships." [Source](https://neo4j.com/blog/cypher-and-gql/gql-database-language-standard/)
- Crucially it is a **query/traversal language, not a storage or authoring format.** GQL was published 11 April 2024 as **ISO/IEC 39075**, "the first new ISO database language since SQL in 1987" — standardized as a database *query* language alongside SQL, not as a document format. [Source](https://neo4j.com/blog/cypher-and-gql/gql-database-language-standard/) [Source](https://en.wikipedia.org/wiki/Graph_Query_Language) [Source](https://www.iso.org/standard/76120.html)
- The ASCII-art itself is transcribed **whiteboard drawing**, not prose: Cypher's designer says it "was grounded in the diagrams I used to draw on whiteboards… [a colleague] would often transcribe those diagrams into ASCII art inside code comments… Cypher made those diagrams executable" (`semantic-web.md` §6). Graph-as-text here is a *picture rendered in characters*, confirming the niche is diagram/query, not writing. [Source](https://www.thobe.org/work/cypher/)
- Edge-writing ceremony is intrinsic: even the friendliest graph syntax makes you name the left node, the bracketed relation, the arrow direction, and the right node for every single edge — fine when querying a few patterns, exhausting as a way to record knowledge at prose density. **[INFERENCE from the syntax + its query-language framing]**

## 3. DOT / Graphviz — a visualization language, layout-oriented and verbose

Primary sources: Graphviz DOT language reference & site; Wikipedia DOT. [Source](https://graphviz.org/doc/info/lang.html) [Source](https://en.wikipedia.org/wiki/DOT_(graph_description_language))

- Graphviz is framed as *visualization*, not knowledge: "Graphviz is open-source graph visualization software that represents structural information as diagrams of abstract graphs and networks," rendering to images, SVG, PDF, PostScript. [Source](https://graphviz.org/) [Source](https://graphviz.org/doc/info/lang.html)
- DOT is "a plain-text… grammar-based specification for describing graphs and directed graphs (digraphs)… enabling the definition of nodes, edges, subgraphs, and associated attributes." Structure: `[strict] (graph | digraph) [name] '{' stmt_list '}'`, where statements are node/edge/attribute/subgraph declarations; directed edges use `->`, undirected `--`. [Source](https://graphviz.org/doc/info/lang.html)
- It is explicitly **layout/appearance-oriented**: Graphviz ships multiple layout engines that "position nodes and route edges… balancing aesthetic criteria such as edge crossing minimization, node overlap avoidance, and symmetry preservation." The value delivered is a *picture*, not a queryable knowledge store. [Source](https://graphviz.org/documentation/)
- Same ceremony, more verbose: every edge is a standalone declaration (`a -> b [label="rel"];`), and meaningful diagrams accrete attribute noise (`shape`, `color`, `rankdir`). Nobody writes DOT to *think*; they write it to *draw*. **[INFERENCE from the grammar + the software's stated purpose]**

## 4. Mermaid — the exception that proves the rule (no semantic model + Markdown carrier)

Primary sources: mermaid.js.org; Mermaid GitHub repo; GitHub Blog announcement. [Source](https://mermaid.js.org/intro/) [Source](https://github.com/mermaid-js/mermaid) [Source](https://github.blog/developer-skills/github/include-diagrams-markdown-files-mermaid/)

- Mermaid is purely presentational: "Mermaid lets you create diagrams and visualizations using text and code… a JavaScript based diagramming and charting tool that renders Markdown-inspired text definitions to create and modify diagrams dynamically." It emits SVG; there is **no queryable/semantic data model** behind it — a Mermaid flowchart is a drawing, not a knowledge graph you can traverse. [Source](https://mermaid.js.org/intro/)
- It was built for docs, not knowledge representation: "The main purpose of Mermaid is to help documentation catch up with development" ("Doc-Rot is a Catch-22 that Mermaid helps to solve"); "Mermaid was created by Knut Sveidqvist for easier documentation." [Source](https://mermaid.js.org/intro/)
- **It rides Markdown, deliberately.** The syntax is "Markdown-inspired" and the docs pitch the on-ramp as "If you are familiar with Markdown you should have no problem learning Mermaid's Syntax." The GitHub repo tagline: "Generation of diagrams… from text in a similar manner as markdown." [Source](https://mermaid.js.org/intro/) [Source](https://github.com/mermaid-js/mermaid)
- **The distribution win is the whole story.** In February 2022 GitHub added *native* Mermaid rendering inside Markdown: wrap a diagram in a ```` ```mermaid ```` code fence and it renders automatically in READMEs, issues, PRs, wikis, and discussions — "no plugins, extensions, or build steps." Mermaid became ubiquitous because it was already inside the Markdown files and platforms developers live in. [Source](https://github.blog/developer-skills/github/include-diagrams-markdown-files-mermaid/) [Source](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
- It still has the same edge-writing ceremony (`A[Client] -->|request| B[(Database)]`) — but that is *tolerated* because (a) the output is an immediately-visible diagram (instant payoff), and (b) it lives in a code fence, quarantined from the prose around it. It is not a medium you *think in*; it is a picture you *drop into* a document. [Source](https://mermaid.js.org/intro/) **[INFERENCE]**
- The lesson for the hypothesis: Mermaid is not a counterexample to "graphs-as-text never became a thinking medium." It succeeded by explicitly *not* being a knowledge medium (no semantics, just diagrams) and by using Markdown + GitHub as its carrier — exactly the carrier thesis behind .sarib. [Source](https://mermaid.js.org/intro/), [Source](https://github.blog/developer-skills/github/include-diagrams-markdown-files-mermaid/)

## 5. KDL — a "cuddly" *tree* language, and why trees out-author graphs

Primary source: kdl.dev (KDL 2.0.0). [Source](https://kdl.dev/) [Source](https://kdl.dev/spec)

- KDL is "a small, pleasant document language with XML-like node semantics that looks like you're invoking a bunch of CLI commands!" — tagline "A cuddly document language," meant "much like JSON, YAML, or XML" for config/serialization. [Source](https://kdl.dev/)
- Its data model is a **tree, not a graph**: "A KDL node is a node name string, followed by zero or more 'arguments', and children," with nested child blocks. KDL calls itself "node-based (like XML or HTML)." There is **no first-class edge / cross-reference** primitive — relationships are expressed only by *containment* (a child under a parent). [Source](https://kdl.dev/)
- Authoring is cheap precisely because hierarchy is implicit in nesting/indentation — you never name both endpoints of a relationship; the parent-child edge is the layout itself:
  ```
  contents {
    section "First section" {
      paragraph "This is the first paragraph"
    }
  }
  ```
  The edge (`section` contains `paragraph`) costs zero ceremony — no `-[:CONTAINS]->`, no triple. [Source](https://kdl.dev/)
- Its stated design principles are "Human Maintainability," "Cognitive Simplicity and Learnability," "Ease of… serialization" — a config language, and it lives in that niche (Zellij, Niri, mise, orogene, System76 Scheduler). [Source](https://kdl.dev/)
- KDL disclaims being a text/knowledge medium: "KDL is **not** a markup language. XML or HTML do a much better job of 'marking up' a text document." [Source](https://kdl.dev/)
- Contrast that sharpens the .sarib design point: **trees are easy to hand-author because the single implicit relation (containment) needs no naming; general graphs are hard because arbitrary typed edges between arbitrary nodes must each be written out.** Every widely hand-authored text structure — Markdown, outliners, KDL, YAML, filesystem paths — is a tree for this reason. **[INFERENCE — supported by KDL's tree model + the triple/edge ceremony documented in §§1–3]**

## 6. GraphML / GEXF — XML graph formats, machine-only

Primary sources: GEXF spec; Gephi/GraphML docs. [Source](https://gexf.net/) [Source](https://docs.gephi.org/desktop/User_Manual/Import/GraphML_Format/) [Source](http://graphml.graphdrawing.org/)

- **GraphML** is "an XML structured format using the .graphml extension" supporting nodes, edges, attributes, and hierarchical/nested graphs — designed as a graph *interchange* format. [Source](https://docs.gephi.org/desktop/User_Manual/Import/GraphML_Format/) [Source](http://graphml.graphdrawing.org/)
- **GEXF** (Graph Exchange XML Format) is "a language for describing complex network structures, their associated data and dynamics," created "together with the Gephi project… to enhance Graph data interoperability… the format of choice to exchange Graphs with Gephi." [Source](https://gexf.net/)
- The rationale is explicitly *tooling*, not human authoring: "XML is used because it is a well known language, XML parsers exist in all programming languages…"; both formats are "designed to be machine-generated" for exchange between graph tools. [Source](https://gexf.net/) [Source](https://docs.gephi.org/desktop/User_Manual/Import/GEXF_File_Format/)
- Nobody hand-writes GraphML/GEXF to record knowledge; they are export/import artifacts emitted by Gephi, NetworkX, etc. — the far end of the spectrum from a thinking medium (verbose XML, one `<node>`/`<edge id=… source=… target=…>` element per element). This is the machine-only endpoint that RDF/XML also occupies (`semantic-web.md` §1). [Source](https://gexf.net/) **[INFERENCE]**

## 7. Cross-cutting: the edge-writing-ceremony finding

Laying the syntaxes side by side, the same edge "Alice knows Bob" costs, in every graph-as-text format, a standalone statement naming both endpoints and the relation:

- Turtle: `:Alice foaf:knows :Bob .` [Source](https://www.w3.org/TR/turtle/)
- Cypher/GQL: `(:Person {name:"Alice"})-[:KNOWS]->(:Person {name:"Bob"})` [Source](https://opencypher.org/)
- DOT: `Alice -> Bob [label="knows"];` [Source](https://graphviz.org/doc/info/lang.html)
- Mermaid: `Alice -->|knows| Bob` [Source](https://mermaid.js.org/intro/)

- In prose, the same fact is written "Alice knows Bob" — the endpoints and relation are *the sentence*, with no separate declaration. Graph-as-text formats force you to *stop writing prose* and emit a structured statement, which is why they cluster in three niches — **query** (Cypher/GQL/SPARQL), **visualization** (DOT/Mermaid/GraphML/GEXF), and **config** (KDL) — and none became a medium for thinking or note-taking. **[INFERENCE — the load-bearing synthesis of §§1–6; each syntax claim is individually sourced above]**
- Supporting evidence that the successful cases are diagram/query transcription, not writing: Cypher literally began as ASCII transcriptions of whiteboard diagrams [Source](https://www.thobe.org/work/cypher/); Graphviz and Mermaid are defined as visualization tools [Source](https://graphviz.org/), [Source](https://mermaid.js.org/intro/); GEXF/GraphML are machine-exchange XML [Source](https://gexf.net/).
- The refutation-resistant part: even the *most* human-optimized entrants failed as writing media — Turtle ("compact and natural") is still unused for notes, and Mermaid (Markdown-native, hugely popular) only succeeded by dropping semantics and becoming pure diagrams. The ceremony is not an implementation wart to be polished away; it is inherent to representing an arbitrary graph as linear text. [Source](https://www.w3.org/TR/turtle/), [Source](https://mermaid.js.org/intro/)

---

## Design lessons for .sarib

1. **Let edges emerge from prose; never require standalone triple/edge statements as the primary authoring act.** Every graph-as-text syntax (Turtle `S P O .`, Cypher `(a)-[:R]->(b)`, DOT `a -> b`) forces the author to stop writing and declare both endpoints plus the relation — the ceremony that kept all of them in query/viz/config niches. .sarib's core innovation must be inline typed links inside natural sentences, so writing "Alice [knows](Bob)" (or similar) *is* asserting the edge. [Turtle](https://www.w3.org/TR/turtle/), [openCypher](https://opencypher.org/), [DOT](https://graphviz.org/doc/info/lang.html)

2. **Make the tree/prose case free and the graph case opt-in but first-class.** KDL, Markdown, and outliners are hand-authored at scale because their one implicit relation — containment via nesting/indentation — needs no naming, whereas arbitrary typed edges do. .sarib should treat a document's hierarchy (headings, lists, nesting) as zero-ceremony edges and reserve explicit syntax only for the cross-cutting links that a tree can't express. [KDL](https://kdl.dev/)

3. **Do not conflate the authoring surface with the query surface.** Cypher/GQL became an ISO standard (39075) as a *query* language, and Turtle's authoring grammar is literally a subset of SPARQL's — but reading/traversing a graph and writing one are different jobs. .sarib should be authored as prose-with-links and *queried* by a separate mechanism, not force authors to write in query-shaped patterns. [GQL/ISO 39075](https://neo4j.com/blog/cypher-and-gql/gql-database-language-standard/)

4. **The carrier beats the model — embed in Markdown and pay off instantly.** Mermaid has no semantic model at all yet is the one graph-ish text people actually write, because GitHub renders ```` ```mermaid ```` fences natively (Feb 2022) with no build step, right inside the Markdown developers already use. .sarib should be a Markdown superset that renders/acts usefully the moment it is saved in the tools people already have, rather than a new file type demanding a new viewer. [Mermaid](https://mermaid.js.org/intro/), [GitHub Blog](https://github.blog/developer-skills/github/include-diagrams-markdown-files-mermaid/)

5. **Keep the semantic graph canonical; treat diagrams as a disposable projection.** DOT and Mermaid optimize layout and appearance and discard identity/semantics — great for a picture, useless as knowledge. .sarib should store an identified labeled-property-graph as truth and *generate* Mermaid/DOT/SVG views from it on demand (never author into the lossy visual form). [Graphviz](https://graphviz.org/), [Mermaid](https://mermaid.js.org/intro/)

6. **Terseness is not writability — optimize the ergonomics of the common case.** Turtle was engineered to be "compact and natural" with prefix and predicate-list abbreviations and still nobody takes notes in it, because it is still explicit triples behind `@prefix` ceremony. .sarib should measure success by whether a human will fluently *write paragraphs* in it, not by character count. [Turtle](https://www.w3.org/TR/turtle/), [Verborgh](https://ruben.verborgh.org/articles/the-semantic-web-identity-crisis/)

7. **Machine-interchange formats must be generated, not hand-written — so keep them out of the authoring path.** GraphML/GEXF (and RDF/XML) exist purely for tool-to-tool exchange in verbose XML; they are never authored by hand. .sarib can *export* to such formats for interop with Gephi/graph tools, but its human-facing form must never look like them. [GEXF](https://gexf.net/), [GraphML](https://docs.gephi.org/desktop/User_Manual/Import/GraphML_Format/)

# Research notes

Raw evidence feeding the staged deliverables. One file per format family or research question. Every factual claim carries a source link (Operating Rule 4).

| File | Covers | Feeds | Status |
|---|---|---|---|
| `markup-and-documents.md` | Markdown, org-mode, AsciiDoc, reST, HTML lineage | RQ3, RQ8 | ✓ done |
| `semantic-web.md` | RDF, OWL, Turtle, JSON-LD, schema.org, Wikidata, Cypher/property graphs | RQ2, RQ4 (partial) | ✓ done |
| `tools-for-thought.md` | Notion, Roam, Obsidian, Tana, Jupyter/jupytext, Pandoc, Portable Text, literate programming | RQ1 (partial), RQ5 | ✓ done |
| `ai-context.md` | LLM format benchmarks, GraphRAG, KV-cache, context management, LLM-native format attempts | RQ7 | ✓ done |
| `standards-adoption.md` | Why JSON/HTML/CSV/Markdown/TOML won; why XHTML2/XML-data/YAML/S-expr lost/cursed | RQ8 | ✓ done |
| `graphs-and-databases.md` | Turtle/N3, Cypher/openCypher/GQL, DOT/Graphviz, Mermaid, KDL, GraphML/GEXF; the edge-writing-ceremony hypothesis | RQ4 | ✓ done |
| `versioning-and-merge.md` | Git object model, human-visible IDs, CRDTs (Shapiro, Automerge/Yjs), OT vs CRDT, Datomic, event sourcing, JSON Patch, structured merge | RQ1, RQ6 | ✓ done |
| `syntax-and-legibility.md` | Information foraging/scent, spatial memory, outliner fold/breadcrumb affordances, tree shape/size notations (org cookies), skeleton-of-thought/RAPTOR, glyph tokenization, emphasis encoding, Markdown-superset extension (djot, MyST, Pandoc attrs, Dataview inline fields) | Phase D / Stage 10 (author-facing syntax) | ✓ done |

All eight research files are now complete. Sub-topics also appear inside sibling files (identity via Wikidata in `semantic-web.md` and Notion/Roam/org in `tools-for-thought.md`; property-graph rationale via `semantic-web.md` §6; line-based-merge pain via `tools-for-thought.md`'s jupytext/nbdev sections), and are cross-referenced from the two new files. See `stages/02-prior-art.md` §7 for how these close the remaining gaps.

Notes are working documents — messy is fine here. Synthesis happens in `stages/`.

# .sarib — an AI-native knowledge language

*One plain-text source of truth. Humans write it like Markdown. Agents edit it like a database. Every view — document, outline, board, graph, timeline, context window — is a projection.*

**Status: v0.1 — working reference implementation; spec complete; freeze gated on benchmarks** (5 of 8 gates green, measured; 2 blocked on external eval; 1 partial). This is a research-grade open standard proposal, built in the open with its full design history.

```markdown
# Q3 Planning

## Migrate invoices {.task} ^t1
status:: todo
due:: 2026-08-01
owner:: [[Alice]]

Can't start until we [depends-on:: [[Adopt the new billing provider]]].
```

That is a valid `.sarib` file. It renders as ordinary Markdown everywhere — *and* it is a labeled property graph: `t1` is a `task` node with properties, `owner` and `depends-on` are typed edges an agent can query and edit atomically.

## Why

Every knowledge format serves one master: Markdown serves documents, JSON serves machines, databases serve queries. AI agents today burn thousands of tokens regenerating whole documents to change one word, and re-infer relationships that were obvious when written. `.sarib` stores knowledge once as an identified graph whose containment tree *is* the readable document, then lets both species work on it natively:

- **Humans** write prose + light marks (a Markdown superset; zero marks required — plain prose is valid).
- **Agents** query bounded subgraphs and apply id-addressed atomic operations — never regeneration.

**Measured, not promised** (`bench/gate-report.md`): a point edit costs **0.50%** of regenerating a 10k-token file (200×). A targeted question over a real 70-risk register costs **230 tokens** of context instead of 6,652 (29×). Concurrent edits merge order-independently (SEC, CRDT-convergent ops). Full round-trip losslessness enforced by a conformance corpus. The entire reference implementation — parser, canonicalizer, op engine, query engine, projections, CLI, MCP server — is **~700 lines of Python**.

## Install & try it (60 seconds)

```bash
pip install sarib          # zero-dependency core; installs the `sarib` command
sarib validate examples/A-prose-native.sarib
sarib render   examples/A-prose-native.sarib --view outline    # spatial cues
sarib render   examples/A-prose-native.sarib --view board      # kanban projection
sarib render   examples/A-prose-native.sarib --view mermaid    # dependency graph
sarib query    examples/A-prose-native.sarib --spec '{"select":"none","filter":{"type":"task"}}'
sarib apply    examples/A-prose-native.sarib --op '{"kind":"set-property","target":"t1","args":{"key":"status","value":"done"}}'
```

### Bring your own notes: `sarib import`

Turn existing Markdown into a `.sarib` knowledge graph:

```bash
sarib import notes/*.md -o knowledge.sarib                    # deterministic: headings->nodes, [[refs]]->edges
sarib import notes/*.md -o knowledge.sarib --extract-edges    # + typed edges (constrained + verified)
```

The default build is deterministic and dependency-free. `--extract-edges` adds typed edges an
agent proposes, but the agent is boxed so it can only *select and cite*, never invent: a closed
edge vocabulary and existing-id targets (schema-enforced at decode time), a verbatim-quote
requirement, and an independent entailment check on every edge; anything unsupported is dropped,
and kept edges carry `inferred` provenance. It is high-precision and deliberately conservative —
**assisted, verified extraction, not a perfect automatic graph.** (Uses a local Ollama model by
default; `--model` / `--endpoint` to point elsewhere. Method + citations:
[`research/importer-extraction.md`](research/importer-extraction.md).)

**See it, not just read it:** `python tools/preview.py knowledge.sarib` (from a repo clone) opens a local page with every projection as tabs — document, outline, board, dependency graph, canonical machine form.

**Agent-native:** the MCP server gives any MCP client (Claude Desktop, Claude Code, Cursor, …) five tools over a folder of `.sarib` files: `sarib_query / sarib_apply / sarib_render / sarib_validate / sarib_canon`.

```bash
pip install "sarib[mcp]"   # adds the MCP server
```

Then register it with your client (Claude Desktop: `claude_desktop_config.json`; Claude Code: a project `.mcp.json`):

```json
{ "mcpServers": { "sarib": {
    "command": "sarib-mcp",
    "args": ["<folder-of-.sarib-files>"] } } }
```

Restart the client, approve the server, and just talk: *"which tasks are open?"* runs a bounded query; *"mark t1 done"* applies one id-addressed op — the file changes by a delta, never a rewrite.

**VS Code:** `editors/vscode-sarib/` ships syntax highlighting plus a live preview panel (`Ctrl+Shift+V`). Install the prebuilt `.vsix` from Releases, or build it: `npx @vscode/vsce package && code --install-extension vscode-sarib-0.2.0.vsix`.

## The design, in five commitments

1. **One graph.** Nodes + typed edges; the document is the containment spanning-tree walked in order. Linear, tree, and non-linear readings are the same data.
2. **Ids, never positions.** Every node/edge has a durable id; all edits address ids; renames break nothing.
3. **Ops are the unit of change.** Create/retract/set/link/move — convergent (order-independent fold), guarded by optimistic preconditions, retract-never-delete.
4. **Exactly one byte-form per state.** A canonical JSON normal form for hashing, diffing, and caching; the op-log is append-only (cache-stable prefixes).
5. **Projections may hide, never drop.** Views are live windows (edits flow back by id) or declared terminal exports — never the ambiguous middle.

## Repository map

| Path | What |
|---|---|
| `stages/14-language-specification.md` | **The spec** (start here) |
| `stages/01…15-*.md` | The full staged design history — each stage critiques its predecessor |
| `impl/` | Reference implementation (Python, ~700 LOC) + conformance corpus |
| `examples/` | The two syntax candidates (A = normative, B = future compact profile) |
| `bench/` | Freeze-gate benchmarks + tokenizer verification + G2/G3 protocols |
| `research/` | 8 cited research files (why formats win/die, LLM format evidence, round-trip law) |
| `decisions/` · `risks/` | 61 logged decisions with reversal conditions · living risk register |
| `dogfood/` | The project's own decision log & risk register as `.sarib`, managed via ops |

## Honest status & what's next

The remaining gates need what a repo can't provide alone: **G2** (accuracy vs Markdown across model families — protocol ready, needs API runs), **G3** (cold human readability, needs raters), and an open-weight tokenizer re-run. The spec freezes only when they're green — if they fail, the design changes, not the benchmark. Contributions that run the protocols, port the parser (TS/Rust), or break the conformance corpus are the most valuable ones.

Licenses: code MIT, spec CC-BY-4.0. Conformance is defined by `impl/tests/corpus/`, not by any implementation.

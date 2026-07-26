# .sarib — an AI-native knowledge language

*One plain-text source of truth. Humans write it like Markdown. Agents edit it like a database. Every view — document, outline, board, graph, timeline, context window — is a projection.*

**Status: v0.1 — working reference implementation; spec complete; freeze gated on benchmarks.** 5 gates green and measured; **G2 measured with a mixed verdict** (4 models complete, 5 rate-capped — [`bench/g2-results.md`](bench/g2-results.md)); G3 blocked on human raters; G8 partial pending an open-weight tokenizer re-run. This is a research-grade open standard proposal, built in the open with its full design history — including the results that went against it.

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

**Measured, not promised.** A point edit costs **0.50%** of regenerating a 10k-token file — a 200× reduction against whole-document regeneration ([`bench/gate-report.md`](bench/gate-report.md), G1; run it yourself with `python bench/run_gates.py`). A targeted question over this project's real 70-risk register costs **230 tokens** of context instead of 6,652 ([`bench/g2-g3-protocol.md`](bench/g2-g3-protocol.md) — which also records a case where the win narrows to 1.8×). Concurrent edits merge order-independently (SEC, CRDT-convergent ops). Full round-trip losslessness enforced by a conformance corpus. The conformance surface — parser, canonicalizer, model, op engine, query engine, projections, CLI, MCP server — is **891 lines of Python**, inside a ≤1000-LOC budget declared before it was measured; the Markdown importer is a further 249 lines, reported outside the budget as a consumer.

## Install & try it (60 seconds)

Nothing but `pip` — this creates its own demo file, so it works from any empty directory:

```bash
pip install sarib          # zero-dependency core; installs the `sarib` command

cat > demo.sarib <<'EOF'
# Q3 Planning

## Migrate invoices {.task} ^t1
status:: todo
due:: 2026-08-01
owner:: [[Alice]]

Can't start until we [depends-on:: [[Adopt the new billing provider]]].

## Adopt the new billing provider {.decision} ^d1
status:: accepted
EOF

sarib validate demo.sarib
sarib render   demo.sarib --view outline           # spatial cues
sarib render   demo.sarib --view board             # kanban projection
sarib render   demo.sarib --view mermaid           # dependency graph
sarib query    demo.sarib --type task              # bounded query → a small subgraph
sarib query    demo.sarib --from t1 --edges depends-on    # what blocks t1
sarib set      demo.sarib t1 status=done --dry-run # a one-property edit, by id
```

`validate` will report one `unresolved-reference: 'Alice'` — that is the design, not a failure. There is no node named Alice, so the resolver leaves the link unresolved and says so rather than guessing which node you meant (D-024). Diagnostics are lint, never fatal: every byte string is a valid `.sarib` file.

Agents use the same engine through a machine-facing form — a full query spec or operation as JSON:

```bash
sarib query demo.sarib --spec '{"select":"none","filter":{"type":"task"}}'
sarib apply demo.sarib --op   '{"kind":"set-property","target":"t1","args":{"key":"status","value":"done"}}'
```

*(On Windows `cmd.exe`, swap the outer single quotes for double quotes and escape the inner ones — or just use the flag forms above.)*

### From a repo clone

`git clone` this repo for the worked examples, the conformance corpus, and the benchmarks:

```bash
sarib render examples/A-prose-native.sarib --view board
python impl/tests/run_corpus.py      # conformance: 6/6, no dependencies
python bench/run_gates.py            # the measured gates (needs: npm i gpt-tokenizer)
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

**See it, not just read it:** `sarib-preview knowledge.sarib` (or `python -m sarib.preview …`; ships with the pip package, so it works in any folder) opens a local page with every projection as tabs — document, outline, board, dependency graph, canonical machine form. The VS Code extension shows the same page live beside the editor (`Ctrl+Shift+V`).

**Agent-native:** the MCP server gives any MCP client (Claude Desktop, Claude Code, Cursor, …) five tools over a folder of `.sarib` files: `sarib_query / sarib_apply / sarib_render / sarib_validate / sarib_canon`.

```bash
pip install "sarib[mcp]"   # adds the MCP server (needs Python 3.10+; the core runs on 3.9)
```

Then register it with your client (Claude Desktop: `claude_desktop_config.json`; Claude Code: a project `.mcp.json`):

```json
{ "mcpServers": { "sarib": {
    "command": "sarib-mcp",
    "args": ["<folder-of-.sarib-files>"] } } }
```

Restart the client, approve the server, and just talk: *"which tasks are open?"* runs a bounded query; *"mark t1 done"* applies one id-addressed op — the file changes by a delta, never a rewrite.

**VS Code:** `editors/vscode-sarib/` ships syntax highlighting plus a live preview panel (`Ctrl+Shift+V`). Install the prebuilt `.vsix` from Releases, or build it: `npx @vscode/vsce package && code --install-extension vscode-sarib-0.3.0.vsix`. The panel calls the previewer from the installed package, so `pip install "sarib>=0.1.4"` is all it needs — `.sarib` files preview in any folder, no clone, no configuration.

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
| `impl/` | Reference implementation (Python, 891 LOC of conformance surface) + conformance corpus |
| `examples/` | The normative syntax candidate (A); candidate B is specified in `stages/10` but not shipped as a file |
| `bench/` | Freeze-gate benchmarks + tokenizer verification + the measured G2 run |
| `docs/` | Plain-language explainer of how it works |
| `research/` | 9 cited research files (why formats win/die, LLM format evidence, round-trip law) |
| `decisions/` · `risks/` | 61 logged decisions with reversal conditions · living risk register |
| `dogfood/` | The project's own decision log & risk register as `.sarib`, managed via ops |

## Honest status & what's next

**G2 has been run, and the honest reading is mixed** ([`bench/g2-results.md`](bench/g2-results.md), raw per-call records included). Answering from a bounded query beat pasting whole Markdown by **+27.8 points on a 7B model** (88.9% vs 60.2%, McNemar p=0.002) and reached **parity at ~⅓ the input tokens on a 120B model** (100% vs 99.1%, 420 vs 1,325 tokens). But pooled across models the gain is **not statistically significant** (Δ=+0.083, p=0.065), one model (`llama3.2`, 3B) **failed** the criterion outright at −0.111, and — the result that matters most — **feeding a model the whole `.sarib` file is not better than whole Markdown**, at ~46% more tokens. So the win is the bounded-retrieval-and-atomic-edit *architecture*, not syntax density. That is what D-002 predicted, and it is why the syntax is not the pitch.

Still outstanding: **G3** (cold human readability, needs raters) and an open-weight tokenizer re-run. The spec freezes only when the gates are green — if they fail, the design changes, not the benchmark. Contributions that run the protocols, port the parser (TS/Rust), or break the conformance corpus are the most valuable ones.

Licenses: code MIT, spec CC-BY-4.0. Conformance is defined by `impl/tests/corpus/`, not by any implementation.

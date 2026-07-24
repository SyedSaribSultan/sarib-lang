# sarib

Reference implementation of the **.sarib** knowledge language — a plain-text format
that is at once a readable document (a Markdown superset) and a labeled property graph.
Agents query bounded subgraphs and apply id-addressed atomic edits instead of
re-reading or regenerating whole files.

```bash
pip install sarib            # core, zero dependencies
pip install "sarib[mcp]"     # + the MCP server for agent clients
```

## CLI

```bash
sarib validate notes.sarib
sarib render   notes.sarib --view outline     # document | outline | board | mermaid
sarib query    notes.sarib --spec '{"select":"none","filter":{"type":"task"}}'
sarib apply    notes.sarib --op   '{"kind":"set-property","target":"t1","args":{"key":"status","value":"done"}}'
sarib canon    notes.sarib                     # canonical normal form (for hash/diff)
```

## MCP server

```bash
sarib-mcp /path/to/folder-of-.sarib-files
```

Exposes `sarib_query / sarib_apply / sarib_render / sarib_validate / sarib_canon`
to any MCP client (Claude Desktop, Claude Code, Cursor, …).

## Status

Research-grade **v0.1**. Spec, full design history, decision log, and benchmarks:
<https://github.com/SyedSaribSultan/sarib-lang>. License: MIT.

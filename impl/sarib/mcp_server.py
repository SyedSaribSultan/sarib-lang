"""sarib MCP server (Stage 13 §4, D-057) — the day-one consumer.
Exposes .sarib files to any MCP-speaking agent: bounded queries (never whole-file dumps),
id-addressed atomic ops (never regeneration), projections, and validation.

Run:  python -m sarib.mcp_server /path/to/knowledge/dir
Claude Desktop / Cowork config:
  { "mcpServers": { "sarib": { "command": "python",
      "args": ["-m", "sarib.mcp_server", "<dir>"], "cwd": "<repo>/impl" } } }
"""
from __future__ import annotations
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from mcp.server.fastmcp import FastMCP
from sarib import parse, canon, fmt, query as run_query
from sarib.ops import apply as apply_op, OpRejected
from sarib.render import VIEWS

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
mcp = FastMCP("sarib")


def _doc(file: str):
    p = (ROOT / file).resolve()
    assert str(p).startswith(str(ROOT)), "path escape"
    return p, parse(p.read_text(encoding="utf-8"))


@mcp.tool()
def sarib_query(file: str, spec: str) -> str:
    """Run a bounded 7-axis query over a .sarib file. spec is JSON:
    {start, select, direction, order, filter:{type,status,prop:[[k,op,v]]},
     bound:{max_nodes,max_depth}, projection:[...]}. Returns a result subgraph
    carrying stable ids — use those ids as op targets (the read/write bridge)."""
    _, doc = _doc(file)
    return json.dumps(run_query(doc, json.loads(spec)), ensure_ascii=False)


@mcp.tool()
def sarib_apply(file: str, op: str) -> str:
    """Apply one atomic operation (JSON: {kind, target, args, expect?}) addressed
    by node/edge id. Guarded ops (expect:{id:{version:v}}) are rejected if stale.
    Writes the updated surface back to the file. Costs a delta, not a regeneration."""
    p, doc = _doc(file)
    try:
        apply_op(doc, json.loads(op))
    except OpRejected as e:
        return f"REJECTED: {e}"
    p.write_text(fmt(doc), encoding="utf-8")
    return "applied"


@mcp.tool()
def sarib_render(file: str, view: str = "outline") -> str:
    """Project a .sarib file into a view: document | outline (spatial cues) |
    board (tasks by status) | mermaid (dependency graph, terminal export)."""
    _, doc = _doc(file)
    return VIEWS[view](doc)


@mcp.tool()
def sarib_validate(file: str) -> str:
    """Three-tier validation (D-049): parse is total; returns non-fatal diagnostics."""
    _, doc = _doc(file)
    return json.dumps({"nodes": len(doc.nodes), "edges": len(doc.edges),
                       "diagnostics": doc.diagnostics}, ensure_ascii=False)


@mcp.tool()
def sarib_canon(file: str) -> str:
    """Canonical normal form (D-041): one byte-string per state; for hashing/diff."""
    _, doc = _doc(file)
    return canon(doc)


def main():
    """Console-script entry point (`sarib-mcp <folder>`); folder read from argv at import."""
    mcp.run()


if __name__ == "__main__":
    main()

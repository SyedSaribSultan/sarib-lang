"""sarib MCP server (Stage 13 §4, D-057) — the day-one consumer.
Exposes .sarib files to any MCP-speaking agent: bounded queries (never whole-file dumps),
id-addressed atomic ops (never regeneration), projections, and validation.

Run:  python -m sarib.mcp_server /path/to/knowledge/dir
Claude Desktop / Cowork config:
  { "mcpServers": { "sarib": { "command": "python",
      "args": ["-m", "sarib.mcp_server", "<dir>"], "cwd": "<repo>/impl" } } }
"""
from __future__ import annotations
import functools, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from mcp.server.fastmcp import FastMCP
from sarib import parse, canon, fmt, query as run_query
from sarib.ops import apply as apply_op, OpRejected
from sarib.render import VIEWS

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
mcp = FastMCP("sarib")


class Denied(Exception):
    """The requested path is outside the managed folder."""


def _guard(fn):
    """Turn a containment failure into a message the agent can read, not a crashed server."""
    @functools.wraps(fn)
    def wrapped(*a, **k):
        try:
            return fn(*a, **k)
        except Denied as e:
            return f"DENIED: {e}"
    return wrapped


def _resolve(file: str) -> pathlib.Path:
    """Contain every tool call inside ROOT. An agent's `file` argument is untrusted —
    it can carry prompt-injected input — and sarib_apply WRITES, so this is the only
    thing standing between a managed notes folder and arbitrary file read/write.

    Three failure modes this deliberately closes:
      * `assert` would be stripped under `python -O`, removing the check entirely;
      * `str(p).startswith(str(ROOT))` is a *string* prefix test, so a sibling
        directory (ROOT=/x/notes, path=/x/notes-secret/…) slips through;
      * `ROOT / file` silently discards ROOT when `file` is absolute.
    `.resolve()` first also collapses `..` and follows symlinks, so a symlink inside
    the folder pointing outside it is caught too.
    """
    raw = pathlib.Path(file)
    if raw.is_absolute() or raw.drive or raw.root:
        raise Denied(f"path must be relative to the managed folder: {file!r}")
    p = (ROOT / raw).resolve()
    if p != ROOT and ROOT not in p.parents:      # true path containment, not prefix matching
        raise Denied(f"path escapes the managed folder: {file!r}")
    if p.suffix != ".sarib":
        raise Denied(f"only .sarib files are addressable: {file!r}")
    return p


def _doc(file: str):
    p = _resolve(file)
    if not p.is_file():
        raise Denied(f"no such file in the managed folder: {file!r}")
    return p, parse(p.read_text(encoding="utf-8"))


@mcp.tool()
@_guard
def sarib_query(file: str, spec: str) -> str:
    """Run a bounded 7-axis query over a .sarib file. spec is JSON:
    {start, select, direction, order, filter:{type,status,prop:[[k,op,v]]},
     bound:{max_nodes,max_depth}, projection:[...]}. Returns a result subgraph
    carrying stable ids — use those ids as op targets (the read/write bridge)."""
    _, doc = _doc(file)
    return json.dumps(run_query(doc, json.loads(spec)), ensure_ascii=False)


@mcp.tool()
@_guard
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
@_guard
def sarib_render(file: str, view: str = "outline") -> str:
    """Project a .sarib file into a view: document | outline (spatial cues) |
    board (tasks by status) | mermaid (dependency graph, terminal export)."""
    _, doc = _doc(file)
    return VIEWS[view](doc)


@mcp.tool()
@_guard
def sarib_validate(file: str) -> str:
    """Three-tier validation (D-049): parse is total; returns non-fatal diagnostics."""
    _, doc = _doc(file)
    return json.dumps({"nodes": len(doc.nodes), "edges": len(doc.edges),
                       "diagnostics": doc.diagnostics}, ensure_ascii=False)


@mcp.tool()
@_guard
def sarib_canon(file: str) -> str:
    """Canonical normal form (D-041): one byte-string per state; for hashing/diff."""
    _, doc = _doc(file)
    return canon(doc)


def main():
    """Console-script entry point (`sarib-mcp <folder>`); folder read from argv at import."""
    mcp.run()


if __name__ == "__main__":
    main()

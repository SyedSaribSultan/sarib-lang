"""sarib CLI (Stage 13 D-057): parse | validate | canon | fmt | query | apply | render | import"""
from __future__ import annotations
import argparse, json, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from sarib import parse, canon, fmt, VIEWS, apply as apply_op, query as run_query, __version__
from sarib.ops import OpRejected
from sarib.importer import build as import_build, DEFAULT_VOCAB

QUICKSTART = """\
quickstart (60 seconds):
  sarib import notes.md -o kb.sarib        turn your existing markdown into a knowledge graph
  sarib validate kb.sarib                  parse + lint (any text is valid; lint never fails hard)
  sarib render kb.sarib --view board       one source, many views: document/outline/board/mermaid
  sarib query kb.sarib --spec "{\\"select\\":\\"none\\",\\"filter\\":{\\"type\\":\\"task\\"}}"
  sarib apply kb.sarib --write --op "{\\"kind\\":\\"set-property\\",\\"target\\":\\"t1\\",\\"args\\":{\\"key\\":\\"status\\",\\"value\\":\\"done\\"}}"

a .sarib file reads like Markdown and queries like a graph: headings/bullets are nodes,
`key:: value` lines are properties, and `[rel:: [[Other]]]` / `[[wikilinks]]` are typed edges.

agent setup (MCP): pip install "sarib[mcp]"  then run  sarib-mcp <folder-of-.sarib-files>
docs, spec, examples: https://github.com/SyedSaribSultan/sarib-lang"""


def _load(path):
    return parse(pathlib.Path(path).read_text(encoding="utf-8"))


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # piped output on Windows defaults to cp1252
    ap = argparse.ArgumentParser(
        prog="sarib",
        description="The .sarib reference CLI — plain-text knowledge that reads like a "
                    "document and queries like a graph.",
        epilog=QUICKSTART,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"sarib {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    def cmd(name, help_, **kw):
        p = sub.add_parser(name, help=help_, description=help_,
                           formatter_class=argparse.RawDescriptionHelpFormatter, **kw)
        return p

    p = cmd("import", "turn markdown/prose files into a .sarib knowledge graph (start here)",
            epilog="examples:\n"
                   "  sarib import notes.md -o kb.sarib\n"
                   "  sarib import docs/*.md -o kb.sarib --title \"Team knowledge\"\n"
                   "  sarib import notes.md -o kb.sarib --extract-edges   # + AI-proposed, verified edges")
    p.add_argument("inputs", nargs="+", help="markdown/text file(s) to import")
    p.add_argument("-o", "--out", help="output .sarib path (default: print to stdout)")
    p.add_argument("--title", default=None, help="graph title (default: the source's own front-matter title)")
    p.add_argument("--extract-edges", action="store_true",
                   help="propose typed edges with a local LLM, constrained + independently verified; "
                        "conservative by design — unsupported edges are dropped, kept ones carry provenance")
    p.add_argument("--model", default="qwen2.5:7b", help="extraction model (default: qwen2.5:7b via Ollama)")
    p.add_argument("--endpoint", default="http://localhost:11434/api/chat",
                   help="OpenAI-style chat endpoint for --extract-edges (default: local Ollama)")
    p.add_argument("--vocab", default=",".join(DEFAULT_VOCAB),
                   help=f"closed edge-type list, comma-separated (default: {','.join(DEFAULT_VOCAB)})")

    p = cmd("validate", "parse + lint a file; prints node/edge counts and diagnostics (never fails hard)")
    p.add_argument("file", help="a .sarib file")

    p = cmd("render", "project the graph into a view",
            epilog="views:\n"
                   "  document   the readable document (the canonical surface)\n"
                   "  outline    indented skeleton with [done/total] task cues\n"
                   "  board      kanban of tasks grouped by status::\n"
                   "  mermaid    the dependency/edge graph (paste into mermaid.live)")
    p.add_argument("file", help="a .sarib file")
    p.add_argument("--view", default="outline", choices=list(VIEWS), help="which projection (default: outline)")

    p = cmd("query", "run a bounded query; returns a small subgraph with stable ids (what agents use)",
            epilog="spec is JSON: {start, select, direction, order, filter, bound, projection}\n"
                   "examples:\n"
                   "  --spec \"{\\\"select\\\":\\\"none\\\",\\\"filter\\\":{\\\"type\\\":\\\"task\\\"}}\"      all tasks\n"
                   "  --spec \"{\\\"select\\\":\\\"none\\\",\\\"filter\\\":{\\\"status\\\":\\\"todo\\\"}}\"    open items\n"
                   "  --spec \"{\\\"start\\\":\\\"t1\\\",\\\"select\\\":\\\"depends-on\\\"}\"              what t1 depends on")
    p.add_argument("file", help="a .sarib file")
    p.add_argument("--spec", required=True, help="JSON query spec (see examples below)")

    p = cmd("apply", "apply one id-addressed atomic operation (a ~dozen-token edit, never a rewrite)",
            epilog="ops: create-node retract-node set-content set-property unset-property add-edge retract-edge move\n"
                   "example:\n"
                   "  --op \"{\\\"kind\\\":\\\"set-property\\\",\\\"target\\\":\\\"t1\\\",\\\"args\\\":{\\\"key\\\":\\\"status\\\",\\\"value\\\":\\\"done\\\"}}\"\n"
                   "add \"expect\" preconditions to guard against stale edits (the op is rejected, never clobbered).")
    p.add_argument("file", help="a .sarib file")
    p.add_argument("--op", required=True, help="JSON operation (see example below)")
    p.add_argument("--write", action="store_true", help="write the result back to the file (default: print)")

    p = cmd("fmt", "normalize the author surface to its canonical layout (idempotent)")
    p.add_argument("file", help="a .sarib file")

    p = cmd("canon", "print the canonical normal form — exactly one byte-form per state (for hash/diff/cache)")
    p.add_argument("file", help="a .sarib file")

    p = cmd("parse", "parse and print the canonical form (alias of canon)")
    p.add_argument("file", help="a .sarib file")

    args = sys.argv[1:] if argv is None else argv
    if not args:
        ap.print_help()
        return
    ns = ap.parse_args(args)

    if ns.cmd == "import":
        inputs = [(pathlib.Path(pth).stem, pathlib.Path(pth).read_text(encoding="utf-8")) for pth in ns.inputs]
        text, stats, diags = import_build(
            inputs, title=ns.title, extract=ns.extract_edges, model=ns.model,
            endpoint=ns.endpoint, vocab=[v.strip() for v in ns.vocab.split(",") if v.strip()])
        if ns.out:
            pathlib.Path(ns.out).write_text(text, encoding="utf-8")
            print(f"wrote {ns.out}")
            print("stats: " + json.dumps(stats))
            hard = [d for d in diags if not d.startswith(("unresolved-reference", "ambiguous-reference"))]
            for d in hard:
                print(f"WARN: {d}")
            print(f"next:  sarib render {ns.out} --view outline")
        else:
            print(text, end="")
        return

    doc = _load(ns.file)
    if ns.cmd == "parse":
        print(canon(doc), end="")
    elif ns.cmd == "canon":
        print(canon(doc), end="")
    elif ns.cmd == "validate":
        for d in doc.diagnostics:
            print(f"lint: {d}")
        print(f"OK: {len(doc.nodes)} nodes, {len(doc.edges)} edges, "
              f"{len(doc.diagnostics)} diagnostics (non-fatal, D-049)")
    elif ns.cmd == "fmt":
        print(fmt(doc), end="")
    elif ns.cmd == "query":
        print(json.dumps(run_query(doc, json.loads(ns.spec)), indent=1, ensure_ascii=False))
    elif ns.cmd == "apply":
        try:
            apply_op(doc, json.loads(ns.op))
        except OpRejected as e:
            print(f"REJECTED: {e}"); sys.exit(1)
        out = fmt(doc)
        if ns.write:
            pathlib.Path(ns.file).write_text(out, encoding="utf-8")
            print(f"applied + written to {ns.file}")
        else:
            print(out, end="")
    elif ns.cmd == "render":
        print(VIEWS[ns.view](doc), end="")


if __name__ == "__main__":
    main()

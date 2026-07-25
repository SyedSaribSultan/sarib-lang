"""sarib CLI (Stage 13 D-057): import | validate | render | query | apply | set | fmt | canon"""
from __future__ import annotations
import argparse, json, os, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from sarib import parse, canon, fmt, VIEWS, apply as apply_op, query as run_query, __version__
from sarib.ops import OpRejected
from sarib.importer import build as import_build, DEFAULT_VOCAB

REPO = "https://github.com/SyedSaribSultan/sarib-lang"


def _ansi():
    """True if we should emit color: a real terminal, not piped, NO_COLOR unset."""
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return False
    if sys.platform == "win32":                      # enable VT processing on legacy consoles
        try:
            import ctypes
            k = ctypes.windll.kernel32
            k.SetConsoleMode(k.GetStdHandle(-11), 7)
        except Exception:
            return False
    return True


class _C:
    def __init__(self, on):
        self.h = "\033[1m" if on else ""              # section heading
        self.c = "\033[36m" if on else ""             # command / literal
        self.d = "\033[2m" if on else ""              # dim commentary
        self.r = "\033[0m" if on else ""


GROUPS = [
    ("START HERE", [
        ("import", "markdown/prose → a .sarib knowledge graph"),
        ("validate", "parse + lint (all text is valid; lint never blocks)"),
    ]),
    ("EXPLORE", [
        ("render", "project into a view: document · outline · board · mermaid"),
        ("query", "bounded query → a small subgraph with stable ids (what agents use)"),
    ]),
    ("EDIT", [
        ("set", "change one property by id — the everyday edit"),
        ("apply", "any atomic operation, addressed by id (never a rewrite)"),
        ("fmt", "normalize the surface to its canonical layout"),
    ]),
    ("MACHINE", [
        ("canon", "canonical normal form — one byte-form per state (hash/diff/cache)"),
        ("parse", "alias of canon"),
    ]),
]

EXAMPLES = [
    ("sarib import notes/*.md -o kb.sarib", "your markdown becomes a graph"),
    ("sarib render kb.sarib --view board", "same file, a kanban board"),
    ("sarib query  kb.sarib --type task", "every task, as a small subgraph"),
    ("sarib query  kb.sarib --from t1 --edges depends-on", "what blocks t1"),
    ("sarib set    kb.sarib t1 status=done", "a one-property edit, by id"),
]


def _help():
    c = _C(_ansi())
    w = 10
    out = [f"{c.h}sarib{c.r} — plain-text knowledge that reads like a document and queries like a graph.",
           "", f"{c.h}USAGE{c.r}", f"  {c.c}sarib{c.r} <command> [options]      "
           f"{c.d}·  sarib <command> --help for details{c.r}"]
    for title, cmds in GROUPS:
        out += ["", f"{c.h}{title}{c.r}"]
        out += [f"  {c.c}{name:<{w}}{c.r}{desc}" for name, desc in cmds]
    out += ["", f"{c.h}EXAMPLES{c.r}"]
    pad = max(len(x) for x, _ in EXAMPLES)
    out += [f"  {c.c}{cmd:<{pad}}{c.r}  {c.d}# {note}{c.r}" for cmd, note in EXAMPLES]
    out += ["", f"{c.h}THE FORMAT, IN THREE LINES{c.r}",
            f"  headings and bullets are {c.c}nodes{c.r} (each with a stable id)",
            f"  {c.c}key:: value{c.r} lines are properties",
            f"  {c.c}[depends-on:: [[Other]]]{c.r} and {c.c}[[wikilinks]]{c.r} are typed edges",
            "", f"{c.h}FOR AI AGENTS (MCP){c.r}",
            f"  {c.c}pip install \"sarib[mcp]\"{c.r}  then  {c.c}sarib-mcp <folder-of-.sarib-files>{c.r}",
            f"  {c.d}any MCP client (Claude, Cursor, …) can then query and edit your knowledge{c.r}",
            "", f"{c.d}docs, spec, examples: {REPO}{c.r}", ""]
    return "\n".join(out)


class _Parser(argparse.ArgumentParser):
    def format_help(self):
        return _help()


def _load(path):
    return parse(pathlib.Path(path).read_text(encoding="utf-8"))


def _kv(pairs, what):
    out = {}
    for p in pairs or []:
        if "=" not in p:
            sys.exit(f"error: {what} must be key=value (got {p!r})")
        k, v = p.split("=", 1)
        out[k] = v
    return out


def _build_spec(ns):
    """Ergonomic flags -> a query spec. --spec (raw JSON) is the escape hatch and the base."""
    spec = json.loads(ns.spec) if ns.spec else {}
    flt = dict(spec.get("filter", {}))
    if ns.type:
        flt["type"] = ns.type
    if ns.status:
        flt["status"] = ns.status
    props = _kv(ns.prop, "--prop")
    if props:
        flt["prop"] = list(flt.get("prop", [])) + [[k, "=", v] for k, v in props.items()]
    if flt:
        spec["filter"] = flt
    if ns.start:
        spec["start"] = ns.start
        spec.setdefault("select", ns.edges or "any")
    elif ns.edges:
        spec["select"] = ns.edges
    spec.setdefault("select", "none")
    return spec


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # piped output on Windows defaults to cp1252
    ap = _Parser(prog="sarib", add_help=False)
    ap.add_argument("-h", "--help", action="help", help=argparse.SUPPRESS)
    ap.add_argument("--version", action="version", version=f"sarib {__version__}",
                    help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="COMMAND")

    def cmd(name, desc, epilog=None):
        return sub.add_parser(name, help=desc, description=desc, epilog=epilog,
                              formatter_class=argparse.RawDescriptionHelpFormatter)

    p = cmd("import", "Turn markdown/prose files into a .sarib knowledge graph.",
            "examples:\n"
            "  sarib import notes.md -o kb.sarib\n"
            "  sarib import docs/*.md -o kb.sarib --title \"Team knowledge\"\n"
            "  sarib import notes.md -o kb.sarib --extract-edges   # + AI-proposed, verified edges")
    p.add_argument("inputs", nargs="+", help="markdown/text file(s) to import")
    p.add_argument("-o", "--out", help="output .sarib path (default: print to stdout)")
    p.add_argument("--title", default=None, help="graph title (default: the source's front-matter title)")
    p.add_argument("--extract-edges", action="store_true",
                   help="propose typed edges with a local model, constrained + independently "
                        "verified; conservative by design (unsupported edges are dropped)")
    p.add_argument("--model", default="qwen2.5:7b", help="extraction model (default: qwen2.5:7b via Ollama)")
    p.add_argument("--endpoint", default="http://localhost:11434/api/chat",
                   help="chat endpoint for --extract-edges (default: local Ollama)")
    p.add_argument("--vocab", default=",".join(DEFAULT_VOCAB),
                   help=f"closed edge-type list (default: {','.join(DEFAULT_VOCAB)})")

    p = cmd("validate", "Parse + lint: node/edge counts and diagnostics. Never fails hard.")
    p.add_argument("file")

    p = cmd("render", "Project the graph into a view.",
            "views:\n"
            "  document   the readable document (the canonical surface)\n"
            "  outline    indented skeleton with [done/total] task cues\n"
            "  board      kanban of tasks grouped by status::\n"
            "  mermaid    the edge graph (paste into mermaid.live)")
    p.add_argument("file")
    p.add_argument("--view", default="outline", choices=list(VIEWS), help="default: outline")

    p = cmd("query", "Run a bounded query; returns a small subgraph with stable ids.",
            "examples:\n"
            "  sarib query kb.sarib --type task                     every task\n"
            "  sarib query kb.sarib --status todo                   everything still open\n"
            "  sarib query kb.sarib --prop owner=Alice              by any property\n"
            "  sarib query kb.sarib --from t1 --edges depends-on    walk out from one node\n"
            "  sarib query kb.sarib --spec '{\"filter\":{\"type\":\"decision\"}}'   raw spec")
    p.add_argument("file")
    p.add_argument("--type", help="only nodes of this type (task, decision, …)")
    p.add_argument("--status", help="only nodes with this status")
    p.add_argument("--prop", action="append", metavar="K=V", help="only nodes with this property (repeatable)")
    p.add_argument("--from", dest="start", metavar="ID", help="start a walk at this node id")
    p.add_argument("--edges", metavar="REL", help="follow edges of this type (with --from)")
    p.add_argument("--spec", help="raw JSON spec: {start, select, direction, order, filter, bound}")

    p = cmd("set", "Change one property by id — the everyday edit. Writes the file.",
            "examples:\n"
            "  sarib set kb.sarib t1 status=done\n"
            "  sarib set kb.sarib t1 status=done --expect status=todo   # guarded: rejected if stale\n"
            "  sarib set kb.sarib t1 owner=Alice --dry-run              # preview, don't write")
    p.add_argument("file")
    p.add_argument("id", help="the node id to edit")
    p.add_argument("assignment", metavar="KEY=VALUE")
    p.add_argument("--expect", metavar="K=V", action="append",
                   help="only apply if the node still has these values (optimistic concurrency)")
    p.add_argument("--dry-run", action="store_true", help="print the result instead of writing")

    p = cmd("apply", "Apply any atomic operation, addressed by id (never a rewrite).",
            "kinds: create-node retract-node set-content set-property unset-property\n"
            "       add-edge retract-edge move merge tag\n\n"
            "example:\n"
            "  sarib apply kb.sarib --write \\\n"
            "    --op '{\"kind\":\"add-edge\",\"args\":{\"type\":\"depends-on\",\"source\":\"t1\",\"target\":\"d1\"}}'\n\n"
            "add \"expect\" for guarded edits — a stale op is rejected, never silently clobbered.\n"
            "for a one-property change, `sarib set` is the shortcut.")
    p.add_argument("file")
    p.add_argument("--op", required=True, help="JSON operation")
    p.add_argument("--write", action="store_true", help="write back (default: print)")

    p = cmd("fmt", "Normalize the author surface to its canonical layout (idempotent).")
    p.add_argument("file")
    p = cmd("canon", "Print the canonical normal form — one byte-form per state.")
    p.add_argument("file")
    p = cmd("parse", "Parse and print the canonical form (alias of canon).")
    p.add_argument("file")

    args = sys.argv[1:] if argv is None else argv
    if not args:
        print(_help(), end="")
        return
    ns = ap.parse_args(args)

    if ns.cmd == "import":
        inputs = [(pathlib.Path(x).stem, pathlib.Path(x).read_text(encoding="utf-8")) for x in ns.inputs]
        text, stats, diags = import_build(
            inputs, title=ns.title, extract=ns.extract_edges, model=ns.model,
            endpoint=ns.endpoint, vocab=[v.strip() for v in ns.vocab.split(",") if v.strip()])
        if not ns.out:
            print(text, end="")
            return
        pathlib.Path(ns.out).write_text(text, encoding="utf-8")
        print(f"wrote {ns.out}")
        print("stats: " + json.dumps(stats))
        for d in diags:
            if not d.startswith(("unresolved-reference", "ambiguous-reference")):
                print(f"WARN: {d}")
        print(f"next:  sarib render {ns.out} --view outline")
        return

    doc = _load(ns.file)
    if ns.cmd in ("parse", "canon"):
        print(canon(doc), end="")
    elif ns.cmd == "validate":
        for d in doc.diagnostics:
            print(f"lint: {d}")
        print(f"OK: {len(doc.nodes)} nodes, {len(doc.edges)} edges, "
              f"{len(doc.diagnostics)} diagnostics (non-fatal, D-049)")
    elif ns.cmd == "fmt":
        print(fmt(doc), end="")
    elif ns.cmd == "render":
        print(VIEWS[ns.view](doc), end="")
    elif ns.cmd == "query":
        print(json.dumps(run_query(doc, _build_spec(ns)), indent=1, ensure_ascii=False))
    elif ns.cmd in ("apply", "set"):
        if ns.cmd == "set":
            k, v = next(iter(_kv([ns.assignment], "KEY=VALUE").items()))
            op = {"kind": "set-property", "target": ns.id, "args": {"key": k, "value": v}}
            exp = _kv(ns.expect, "--expect")
            if exp:
                op["expect"] = {ns.id: {"props": exp}}
            write = not ns.dry_run
        else:
            op, write = json.loads(ns.op), ns.write
        try:
            apply_op(doc, op)
        except OpRejected as e:
            print(f"REJECTED: {e}")
            sys.exit(1)
        out = fmt(doc)
        if write:
            pathlib.Path(ns.file).write_text(out, encoding="utf-8")
            print(f"applied + written to {ns.file}")
        else:
            print(out, end="")


if __name__ == "__main__":
    main()

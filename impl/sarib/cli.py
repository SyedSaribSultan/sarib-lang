"""sarib CLI (Stage 13 D-057): parse | validate | canon | fmt | query | apply | render"""
from __future__ import annotations
import argparse, json, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from sarib import parse, canon, fmt, VIEWS, apply as apply_op, query as run_query
from sarib.ops import OpRejected


def _load(path):
    return parse(pathlib.Path(path).read_text(encoding="utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sarib", description=".sarib reference CLI v0.1")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("parse", "validate", "canon", "fmt"):
        sub.add_parser(c).add_argument("file")
    q = sub.add_parser("query"); q.add_argument("file"); q.add_argument("--spec", required=True)
    a = sub.add_parser("apply"); a.add_argument("file"); a.add_argument("--op", required=True); a.add_argument("--write", action="store_true")
    r = sub.add_parser("render"); r.add_argument("file"); r.add_argument("--view", default="outline", choices=list(VIEWS))
    ns = ap.parse_args(argv)

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

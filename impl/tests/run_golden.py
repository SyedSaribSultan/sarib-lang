"""Golden-output regression net (plans/01-scale-remediation.md §6 invariant 1).

The scale remediation replaces the primitives that supply iteration order
(`children()`'s `(order, id)` sort, `query.py`'s inner `sorted(doc.edges)`).
G5/G6/G7 depend on that order *incidentally*, so a reordering would be a
correctness regression wearing a performance change's clothes. This test pins
the observable behaviour of every projection, every query axis, and the op path
so that WP1-WP6 can be proven side-effect-free.

Covers, for every corpus/example/dogfood file plus the synthetic gate KB:
  - containment walk order (the node id sequence — the thing indexes change)
  - canon / fmt / outline / board / mermaid bytes
  - the preview HTML (its own nested-walk code path)
  - parse diagnostics
  - a 30-spec query matrix spanning all 7 axes, with result order and cursor
  - a fixed op sequence's canonical state after each op
  - op-order invariance (24 permutations -> 1 state)

Run:     python impl/tests/run_golden.py
Bless:   python impl/tests/run_golden.py --bless     (only when a change is
         intended AND explained in HISTORY.md — never to make red go green)
"""
from __future__ import annotations

import hashlib
import itertools
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "impl"))
sys.path.insert(0, str(ROOT))

from sarib import canon, fmt, parse                      # noqa: E402
from sarib.ops import OpRejected, apply as apply_op, fold  # noqa: E402
from sarib.preview import build_text                     # noqa: E402
from sarib.query import query                            # noqa: E402
from sarib.render import board, mermaid, outline          # noqa: E402

GOLDEN = pathlib.Path(__file__).parent / "golden.json"


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def gen_kb() -> str:
    """The gate KB, imported so golden and gates measure the same artifact."""
    from bench.run_gates import gen_kb as g
    return g()


def _tracked() -> set:
    """Paths git actually tracks.

    The golden set MUST be hermetic — identical in every clone. An earlier version
    globbed the working directory, which blessed `examples/C-fitsmart-company.sarib`
    (gitignored, local-only), so CI failed on a source it could never have had. Falls
    back to plain globbing only if git is unavailable, and says so.
    """
    try:
        r = subprocess.run(["git", "ls-files", "-z"], cwd=str(ROOT),
                           capture_output=True, text=True, check=True)
        return {(ROOT / p).resolve() for p in r.stdout.split("\0") if p}
    except Exception as e:                                   # noqa: BLE001
        print(f"WARNING: git unavailable ({e.__class__.__name__}); using every file on "
              f"disk, so this run is not hermetic")
        return set()


def sources() -> list:
    """(label, text) pairs — every git-tracked .sarib in the repo, plus the gate KB."""
    keep = _tracked()
    out = []
    for d, pat in ((ROOT / "impl" / "tests" / "corpus", "*.sarib"),
                   (ROOT / "examples", "*.sarib"),
                   (ROOT / "dogfood", "*.sarib")):
        for f in sorted(d.glob(pat)):
            if keep and f.resolve() not in keep:
                continue                                     # untracked / gitignored
            out.append((f"{d.name}/{f.name}", f.read_text(encoding="utf-8")))
    out.append(("synthetic/gate-kb", gen_kb()))
    return out


# ---- the query matrix: all 7 axes (start·select·direction·order·filter·bound·projection) ----
def query_specs(doc) -> list:
    """Deterministic spec list. Seeds come from the doc so it works on any file."""
    ids = list(doc.nodes)
    a = ids[0] if ids else "missing"
    b = ids[len(ids) // 2] if ids else "missing"
    c = ids[-1] if ids else "missing"
    etypes = sorted({e.type for e in doc.edges.values()}) or ["relates-to"]
    et = etypes[0]
    props = sorted({k for n in doc.nodes.values() for k in n.properties
                    if not k.startswith("_")})
    pk = props[0] if props else "status"
    return [
        # start axis
        {"start": "all", "select": "none"},
        {"start": a, "select": "contains"},
        {"start": [a, b], "select": "contains"},
        {"start": c, "select": "contains"},
        {"start": "no-such-id", "select": "contains"},
        # select axis
        {"start": a, "select": "any"},
        {"start": a, "select": et},
        {"start": a, "select": etypes[:2]},
        {"start": "all", "select": "none", "filter": {}},
        # direction axis
        {"start": b, "select": "any", "direction": "forward"},
        {"start": b, "select": "any", "direction": "backward"},
        {"start": b, "select": "any", "direction": "both"},
        # order axis
        {"start": "all", "select": "none", "order": "document"},
        {"start": "all", "select": "none", "order": f"by-{pk}"},
        {"start": "all", "select": "none", "order": "by-nonexistent"},
        # filter axis
        {"start": "all", "select": "none", "filter": {"type": "task"}},
        {"start": "all", "select": "none", "filter": {"status": "active"}},
        {"start": "all", "select": "none", "filter": {"prop": [[pk, "exists", None]]}},
        {"start": "all", "select": "none", "filter": {"prop": [[pk, "=", "done"]]}},
        {"start": "all", "select": "none", "filter": {"prop": [[pk, "!=", "done"]]}},
        {"start": "all", "select": "none",
         "filter": {"type": "task", "prop": [[pk, "exists", None]]}},
        # bound axis
        {"start": "all", "select": "none", "bound": {"max_nodes": 1}},
        {"start": "all", "select": "none", "bound": {"max_nodes": 5}},
        {"start": "all", "select": "none", "bound": {"max_nodes": 10 ** 9}},
        {"start": a, "select": "any", "bound": {"max_nodes": 500, "max_depth": 0}},
        {"start": a, "select": "any", "bound": {"max_nodes": 500, "max_depth": 1}},
        {"start": a, "select": "any", "bound": {"max_nodes": 3, "max_depth": 50}},
        # projection axis
        {"start": "all", "select": "none", "projection": ["id"]},
        {"start": "all", "select": "none", "projection": ["id", "type"]},
        {"start": "all", "select": "none",
         "projection": ["id", "type", "title", "props", "status", "parent"]},
        # combined
        {"start": a, "select": "any", "direction": "both", "order": "document",
         "filter": {"prop": [[pk, "exists", None]]},
         "bound": {"max_nodes": 25, "max_depth": 4},
         "projection": ["id", "title"]},
    ]


def query_fingerprint(doc, spec) -> dict:
    """Order-sensitive fingerprint: what must not move when indexes land."""
    r = query(doc, spec)
    return {
        "nodes": [n.get("id") for n in r["nodes"]],
        "edges": [e["id"] for e in r["edges"]],
        "endpoints": [[e["source"], e["target"]] for e in r["edges"]],
        "cursor": r["cursor"],
        "n_fields": sorted(r["nodes"][0]) if r["nodes"] else [],
    }


# ---- the op path ----
OP_SEQ = [
    {"kind": "set-property", "target": "t1x1", "args": {"key": "status", "value": "done"}},
    {"kind": "create-node", "args": {"id": "gNEW", "title": "Golden task", "type": "task",
                                     "parent": "ws1", "props": {"status": "todo"}}},
    {"kind": "create-node", "args": {"id": "gNEW2", "title": "Second", "type": "task",
                                     "parent": "ws1"}},
    {"kind": "add-edge", "args": {"id": "gE", "type": "depends-on",
                                  "source": "gNEW", "target": "t2x2"}},
    {"kind": "move", "target": "gNEW2", "args": {"parent": "ws2"}},
    {"kind": "set-content", "target": "gNEW", "args": {"content": "body"}},
    {"kind": "unset-property", "target": "gNEW", "args": {"key": "status"}},
    {"kind": "retract-edge", "target": "gE"},
    {"kind": "retract-node", "target": "gNEW2"},
    {"kind": "tag", "target": "gNEW", "args": {"concept": "t3x3"}},
    {"kind": "merge", "target": "t5x5", "args": {"into": "t5x6"}},
]

PERM_OPS = [
    {"id": "a", "ts": [1, 5], "kind": "set-property", "target": "t1x1",
     "args": {"key": "status", "value": "done"}},
    {"id": "b", "ts": [2, 3], "kind": "set-property", "target": "t2x2",
     "args": {"key": "priority", "value": "high"}},
    {"id": "c", "ts": [1, 7], "kind": "create-node",
     "args": {"id": "tNEW1", "title": "New task", "type": "task", "parent": "ws1",
              "props": {"status": "todo"}}},
    {"id": "d", "ts": [3, 1], "kind": "retract-node", "target": "t4x4"},
]

REJECT_CASES = [
    {"kind": "create-node", "args": {"id": "t1x1", "title": "dup"}},
    {"kind": "create-node", "args": {"id": "zz", "parent": "no-such-parent"}},
    {"kind": "add-edge", "args": {"type": "x", "source": "t1x1", "target": "nope"}},
    {"kind": "add-edge", "args": {"type": "x", "source": "t1x1", "target": "t2x2",
                                  "family": "containment"}},
    {"kind": "move", "target": "ws1", "args": {"parent": "no-such"}},
    {"kind": "move", "target": "ws1", "args": {"parent": "t1x1"}},   # cycle
    {"kind": "bogus-kind", "target": "t1x1"},
    {"kind": "set-property", "target": "t1x1", "args": {"key": "status", "value": "x"},
     "expect": {"t1x1": {"version": 999}}},
    {"kind": "set-property", "target": "t1x1", "args": {"key": "status", "value": "x"},
     "expect": {"no-such": {"version": 0}}},
]


def capture() -> dict:
    got = {"sources": {}, "queries": {}, "ops": {}}

    for label, text in sources():
        doc = parse(text)
        got["sources"][label] = {
            # the walk order is the invariant the child index most threatens
            "walk": sha(",".join(n.id for n in doc.walk(None))),
            "walk_len": len(list(doc.walk(None))),
            "canon": sha(canon(doc)),
            "fmt": sha(fmt(doc)),
            "outline": sha(outline(doc)),
            "board": sha(board(doc)),
            "mermaid": sha(mermaid(doc)),
            "preview": sha(build_text(text, label)),
            "n_nodes": len(doc.nodes),
            "n_edges": len(doc.edges),
            "diagnostics": sorted(doc.diagnostics),
            "invariants": sorted(doc.check_invariants()),
            "slugs": sha(",".join(sorted(
                f"{n.slug}={n.id}" for n in doc.nodes.values() if n.slug))),
        }

    # query matrix on the two richest real docs + the synthetic KB
    for label, text in sources():
        if not (label.startswith("dogfood/") or label == "synthetic/gate-kb"
                or label.startswith("examples/")):
            continue
        doc = parse(text)
        got["queries"][label] = [query_fingerprint(doc, s) for s in query_specs(doc)]

    # op path: canonical state after each op, on the gate KB
    kb = gen_kb()
    doc = parse(kb)
    states = []
    for op in OP_SEQ:
        apply_op(doc, op)
        states.append(sha(canon(doc)))
    got["ops"]["sequence"] = states
    got["ops"]["final_walk"] = sha(",".join(n.id for n in doc.walk(None)))

    # op-order invariance (G5's property, pinned here too)
    canons = set()
    for perm in itertools.permutations(PERM_OPS):
        d = parse(kb)
        fold(d, list(perm))
        canons.add(canon(d))
    got["ops"]["permutation_states"] = len(canons)
    got["ops"]["permutation_canon"] = sha(sorted(canons)[0])

    # rejections must keep rejecting, with the same messages
    rej = []
    for op in REJECT_CASES:
        d = parse(kb)
        try:
            apply_op(d, op)
            rej.append("ACCEPTED-should-not-be")
        except OpRejected as e:
            rej.append(str(e))
        except Exception as e:                      # noqa: BLE001 - shape matters
            rej.append(f"{e.__class__.__name__}: {e}")
    got["ops"]["rejections"] = rej

    return got


def diff(exp, got, path="") -> list:
    """Readable structural diff so a failure names the exact field."""
    out = []
    if isinstance(exp, dict) and isinstance(got, dict):
        for k in sorted(set(exp) | set(got)):
            if k not in exp:
                out.append(f"{path}.{k}: ADDED")
            elif k not in got:
                out.append(f"{path}.{k}: REMOVED")
            else:
                out += diff(exp[k], got[k], f"{path}.{k}")
    elif isinstance(exp, list) and isinstance(got, list):
        if len(exp) != len(got):
            out.append(f"{path}: length {len(exp)} -> {len(got)}")
        for i, (x, y) in enumerate(zip(exp, got)):
            out += diff(x, y, f"{path}[{i}]")
    elif exp != got:
        out.append(f"{path}: {exp!r} -> {got!r}")
    return out


def main():
    got = capture()
    if "--bless" in sys.argv:
        GOLDEN.write_text(json.dumps(got, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        n_q = sum(len(v) for v in got["queries"].values())
        print(f"BLESSED {GOLDEN.relative_to(ROOT)}")
        print(f"  {len(got['sources'])} sources · {n_q} query fingerprints · "
              f"{len(got['ops']['sequence'])} op states · "
              f"{got['ops']['permutation_states']} permutation state(s)")
        return 0
    if not GOLDEN.exists():
        print("NO GOLDEN — run with --bless first")
        return 1
    exp = json.loads(GOLDEN.read_text(encoding="utf-8"))
    d = diff(exp, got)
    if d:
        print(f"GOLDEN MISMATCH — {len(d)} difference(s):")
        for line in d[:60]:
            print(f"  {line}")
        if len(d) > 60:
            print(f"  ... and {len(d) - 60} more")
        print("\nThis means observable behaviour changed. WP1-WP6 must be byte-identical.")
        return 1
    n_q = sum(len(v) for v in got["queries"].values())
    print(f"GOLDEN OK — {len(got['sources'])} sources · {n_q} query fingerprints · "
          f"{len(got['ops']['sequence'])} op states · rejections "
          f"{len(got['ops']['rejections'])} · permutations "
          f"{got['ops']['permutation_states']} state(s)")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())

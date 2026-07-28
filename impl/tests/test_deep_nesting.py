"""Containment depth is an axis independent of node count.

`Doc.walk()` used to recurse once per containment level, so a deeply nested
document overflowed the stack at ~1000 levels no matter how small it was --
indexing does nothing for that (plans/01-scale-remediation.md D6/C5).

The surface grammar caps heading depth at 6 (`#{1,6}`), so parse cannot build a
deep chain; `move` ops and programmatic construction can. Both are covered here.

Run: python impl/tests/test_deep_nesting.py
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from sarib import canon, fmt                                    # noqa: E402
from sarib.model import Doc, Edge, Node                         # noqa: E402
from sarib.ops import apply as apply_op                         # noqa: E402
from sarib.query import query                                   # noqa: E402
from sarib.render import _stats, board, mermaid, outline  # noqa: E402

DEPTH = 5000            # 5x CPython's default recursion limit
LIMIT_AT_START = sys.getrecursionlimit()


def deep_doc(depth: int) -> Doc:
    """A single chain of `depth` nodes: parent -> child -> grandchild -> ..."""
    doc = Doc()
    prev = None
    for i in range(depth):
        nid = f"d{i}"
        doc.nodes[nid] = Node(id=nid, type="task" if i % 7 == 0 else None,
                              kind_hint="heading", title=f"Level {i}",
                              slug=f"lvl{i}", parent=prev,
                              properties={"_level": min(i + 1, 6),
                                          "status": "done" if i % 3 == 0 else "todo"})
        prev = nid
    doc.edges["e1"] = Edge(id="e1", type="depends-on", source=f"d{depth - 1}", target="d0")
    return doc


def check(name, cond):
    print(f"  {'ok  ' if cond else 'FAIL'} {name}")
    return 0 if cond else 1


def main() -> int:
    fails = 0
    print(f"deep chain: {DEPTH} levels (recursion limit {LIMIT_AT_START})")
    doc = deep_doc(DEPTH)

    walked = [n.id for n in doc.walk(None)]
    fails += check("walk() completes without recursion", len(walked) == DEPTH)
    fails += check("walk() order is the chain, top-down",
                   walked == [f"d{i}" for i in range(DEPTH)])

    depths, size, tasks, done = _stats(doc)
    fails += check("_stats() depth is exact",
                   depths[f"d{DEPTH - 1}"] == DEPTH - 1 and depths["d0"] == 0)

    fails += check("_stats() subtree sizes are exact",
                   size["d0"] == DEPTH - 1 and size[f"d{DEPTH - 1}"] == 0)
    fails += check("_stats() task tally is exact",
                   tasks["d0"] == sum(1 for i in range(1, DEPTH) if i % 7 == 0))

    fails += check("check_invariants() reports no false cycle",
                   doc.check_invariants() == [])
    fails += check("node_by_slug() resolves at the bottom",
                   doc.node_by_slug(f"lvl{DEPTH - 1}").id == f"d{DEPTH - 1}")

    c = canon(doc)
    fails += check("canon() completes", c.count("\n") == DEPTH + 2)
    fails += check("fmt() completes", fmt(doc).strip().startswith("# Level 0"))
    fails += check("outline() completes", outline(doc).count("\n") == DEPTH)
    fails += check("board() completes", "TODO" in board(doc) or "DONE" in board(doc))
    fails += check("mermaid() completes", "flowchart TD" in mermaid(doc))

    r = query(doc, {"start": "all", "select": "none", "filter": {"type": "task"},
                    "bound": {"max_nodes": 10 ** 9}})
    fails += check("query(select:none) spans the chain",
                   len(r["nodes"]) == sum(1 for i in range(DEPTH) if i % 7 == 0))
    r2 = query(doc, {"start": "d0", "select": "contains",
                     "bound": {"max_nodes": 10 ** 9, "max_depth": DEPTH + 1}})
    fails += check("query(select:contains) descends the chain",
                   len(r2["nodes"]) == DEPTH)

    # the op path can build depth even though the surface grammar cannot
    d2 = Doc()
    for i in range(3):
        d2.nodes[f"m{i}"] = Node(id=f"m{i}", kind_hint="heading", title=f"M{i}")
    d2.touch()
    apply_op(d2, {"kind": "move", "target": "m1", "args": {"parent": "m0"}})
    apply_op(d2, {"kind": "move", "target": "m2", "args": {"parent": "m1"}})
    fails += check("move ops build a chain the parser cannot",
                   [n.id for n in d2.walk(None)] == ["m0", "m1", "m2"])
    try:
        apply_op(d2, {"kind": "move", "target": "m0", "args": {"parent": "m2"}})
        fails += check("move still rejects a containment cycle", False)
    except Exception as e:                                   # noqa: BLE001
        fails += check("move still rejects a containment cycle", "cycle" in str(e))

    fails += check("recursion limit was never raised to pass",
                   sys.getrecursionlimit() == LIMIT_AT_START)

    print(f"\n{'DEEP-NESTING OK' if fails == 0 else f'{fails} FAILURES'}")
    return 1 if fails else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())

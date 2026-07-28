"""bench/scale_probe.py — scaling probe for the reference implementation.

Answers: how do parse / walk / query / canon / render cost scale with node count?
Builds synthetic Docs and times the hot paths. Not a gate (see G9 in
plans/01-scale-remediation.md); this is the diagnostic that motivated the plan.

Run:  python bench/scale_probe.py            # default sizes
      python bench/scale_probe.py 300 1000   # explicit sizes

Prefers the in-repo impl/ over any installed sarib, so it measures the tree.
"""
from __future__ import annotations
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "impl"))

from sarib.model import Doc, Edge, Node          # noqa: E402
from sarib.query import query                    # noqa: E402

DEFAULT_SIZES = [300, 1000, 3000, 10000, 30000]


def build(n_nodes: int, branching: int = 8, edge_ratio: float = 1.0) -> Doc:
    """Balanced containment tree of n_nodes, plus cross-ref edges."""
    doc = Doc()
    ids = []
    for i in range(n_nodes):
        nid = f"n{i}"
        parent = None if i == 0 else f"n{(i - 1) // branching}"
        doc.nodes[nid] = Node(
            id=nid,
            type="task" if i % 3 == 0 else "note",
            kind_hint="heading",
            title=f"Node {i}",
            slug=f"s{i}",
            parent=parent,
            order=i % branching,
            properties={"status": "open" if i % 2 else "done", "prio": str(i % 10)},
        )
        ids.append(nid)
    for j in range(int(n_nodes * edge_ratio)):
        eid = f"e{j}"
        doc.edges[eid] = Edge(id=eid, type="depends-on",
                              source=ids[j % n_nodes],
                              target=ids[(j * 7 + 3) % n_nodes])
    return doc


def ms(fn, *a, **k):
    s = time.perf_counter()
    r = fn(*a, **k)
    return (time.perf_counter() - s) * 1000.0, r


def probe(sizes):
    print("== hot paths (ms) ==")
    hdr = f"{'nodes':>7} {'full walk':>10} {'filter q':>10} {'walk q':>10} {'invariants':>11} {'by-slug':>8}"
    print(hdr)
    print("-" * len(hdr))
    for n in sizes:
        doc = build(n)
        t_walk, seen = ms(lambda: list(doc.walk(None)))
        # select:none — the priority/chronological path, goes through walk()
        t_filter, r1 = ms(query, doc, {"start": "all", "select": "none",
                                       "filter": {"type": "task"},
                                       "bound": {"max_nodes": 100}})
        # graph walk at the default bound — exposes the per-node edge sort
        t_hop, r2 = ms(query, doc, {"start": "n0", "select": "any",
                                    "direction": "both"})
        t_inv, _ = ms(doc.check_invariants)
        t_slug, _ = ms(doc.node_by_slug, f"s{n - 1}")
        print(f"{n:>7} {t_walk:>10.1f} {t_filter:>10.1f} {t_hop:>10.1f} "
              f"{t_inv:>11.1f} {t_slug:>8.1f}"
              f"   (walk {len(seen)}, filter {len(r1['nodes'])}, hop {len(r2['nodes'])})")


def prototype(sizes):
    """Indexed prototype, for comparison. NOT the shipped design — see the plan."""
    print()
    print("== indexed prototype (build-once child map + edge adjacency) ==")
    hdr = f"{'nodes':>7} {'index build':>12} {'indexed walk':>13}"
    print(hdr)
    print("-" * len(hdr))
    sys.setrecursionlimit(300000)

    def build_index(doc):
        kids = {}
        for nd in doc.nodes.values():
            if nd.status == "active":
                kids.setdefault(nd.parent, []).append(nd)
        for v in kids.values():
            v.sort(key=lambda x: (x.order, x.id))
        out, inn = {}, {}
        for eid in sorted(doc.edges):
            e = doc.edges[eid]
            out.setdefault(e.source, []).append(eid)
            inn.setdefault(e.target, []).append(eid)
        return kids, out, inn

    def walk_indexed(kids, nid=None):
        for c in kids.get(nid, []):
            yield c
            yield from walk_indexed(kids, c.id)

    for n in sizes:
        doc = build(n)
        t_idx, (kids, _out, _inn) = ms(build_index, doc)
        t_walk, got = ms(lambda: list(walk_indexed(kids)))
        print(f"{n:>7} {t_idx:>12.1f} {t_walk:>13.1f}   (saw {len(got)})")


if __name__ == "__main__":
    argv = [int(x) for x in sys.argv[1:]] or DEFAULT_SIZES
    print(f"python {sys.version.split()[0]} · impl = {os.path.join(REPO, 'impl')}")
    probe(argv)
    prototype(argv + [100000] if argv == DEFAULT_SIZES else argv)

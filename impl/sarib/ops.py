"""sarib.ops — the operation vocabulary (Stage 8, D-035..D-039).
Ops are data; targets are ids (never positions); expect = optimistic concurrency;
fold(op-set) is order-independent (ops sorted by Lamport ts -> LWW/grow-set semantics).
"""
from __future__ import annotations
from .model import Doc, Node, Edge

PRIMITIVES = {"create-node", "retract-node", "set-content", "set-property",
              "unset-property", "add-edge", "retract-edge", "move"}
COMPOSITES = {"merge", "tag"}


class OpRejected(Exception):
    pass


def _check_expect(doc: Doc, op: dict):
    exp = op.get("expect")
    if not exp:
        return
    for tid, cond in exp.items():
        obj = doc.nodes.get(tid) or doc.edges.get(tid)
        if obj is None:
            raise OpRejected(f"expect: target {tid} not found")
        if "version" in cond and obj.version != cond["version"]:
            raise OpRejected(f"expect: {tid} at version {obj.version}, expected {cond['version']}")
        for k, v in cond.get("props", {}).items():
            if (obj.properties if hasattr(obj, "properties") else {}).get(k) != v:
                raise OpRejected(f"expect: {tid}.{k} != {v!r}")


def apply(doc: Doc, op: dict) -> Doc:
    """Apply one op, preserving the 10 invariants (D-035). Mutates and returns doc."""
    _check_expect(doc, op)
    kind, t, a = op["kind"], op.get("target"), op.get("args", {})

    if kind == "create-node":
        nid = a.get("id") or f"n{len(doc.nodes) + 1}x"
        if nid in doc.nodes:
            raise OpRejected(f"create-node: id {nid} exists")
        parent = a.get("parent")
        if parent is not None and parent not in doc.nodes:
            raise OpRejected(f"create-node: parent {parent} missing")   # invariant 2
        n = Node(id=nid, type=a.get("type"), kind_hint=a.get("hint", "item"),
                 title=a.get("title", ""), content=a.get("content", ""),
                 properties=dict(a.get("props", {})), parent=parent,
                 order=a.get("order", len(doc.children(parent))),
                 provenance=op.get("provenance"))
        doc.nodes[nid] = n
        doc.touch()
    elif kind == "retract-node":
        doc.nodes[t].status = "retracted"                               # P12: never destroy
        doc.touch()
    elif kind == "set-content":
        doc.nodes[t].content = a["content"]
    elif kind == "set-property":
        obj = doc.nodes.get(t) or doc.edges[t]
        obj.properties[a["key"]] = a["value"]
    elif kind == "unset-property":
        obj = doc.nodes.get(t) or doc.edges[t]
        obj.properties.pop(a["key"], None)
    elif kind == "add-edge":
        eid = a.get("id") or f"e{len(doc.edges) + 1}x"
        if a.get("family") == "containment":
            raise OpRejected("containment is edited only via create-node/move (D-035)")
        for end in (a["source"], a["target"]):
            if end not in doc.nodes:
                raise OpRejected(f"add-edge: endpoint {end} missing")   # invariant 3
        doc.edges[eid] = Edge(id=eid, type=a["type"], source=a["source"],
                              target=a["target"], properties=dict(a.get("props", {})),
                              provenance=op.get("provenance"))
        doc.touch()
    elif kind == "retract-edge":
        doc.edges[t].status = "retracted"       # no touch: adjacency indexes every edge and
                                                # the reader filters on status, as it always did
    elif kind == "move":
        if a["parent"] not in doc.nodes:
            raise OpRejected(f"move: parent {a['parent']} missing")
        p = a["parent"]                                                  # cycle guard (invariant 2)
        while p is not None:
            if p == t:
                raise OpRejected("move: would create containment cycle")
            p = doc.nodes[p].parent
        doc.nodes[t].parent = a["parent"]
        doc.touch()          # the order default counts the moved node itself, so the index
                             # must already see the reparenting (as the old live scan did)
        doc.nodes[t].order = a.get("order", len(doc.children(a["parent"])))
        doc.touch()
    elif kind == "merge":                                                # composite (D-035)
        loser, winner = t, a["into"]
        doc.nodes[loser].status = "retracted"
        doc.edges[f"e-merge-{loser}"] = Edge(id=f"e-merge-{loser}", type="merged-into",
                                             source=loser, target=winner)
        for e in doc.edges.values():
            if e.target == loser and e.type != "merged-into":
                e.target = winner
        doc.touch()
    elif kind == "tag":
        return apply(doc, {**op, "kind": "add-edge",
                           "args": {"type": "tag", "source": t, "target": a["concept"]}})
    else:
        raise OpRejected(f"unknown op kind {kind}")

    obj = doc.nodes.get(t) or doc.edges.get(t) if t else None
    if obj is not None:
        obj.version += 1
    # Still a FULL check per op: measured, narrowing it to the touched ids bought nothing
    # once the cycle check became O(N) amortized, and it would have changed *when* a
    # violation is detected. Per-op cost is O(N+E); see bench/scale-report.md §4 and the
    # two deferred follow-ups in plans/01-scale-remediation.md §10.
    diags = doc.check_invariants()
    if diags:
        raise OpRejected(f"op would break invariants: {diags}")          # RM14: closed op set
    return doc


def fold(doc: Doc, ops: list) -> Doc:
    """State = fold(op-set), order-independent: sort by Lamport ts (counter, replica) then apply.
    Any permutation of `ops` yields the same state (D-037/D-039)."""
    for op in sorted(ops, key=lambda o: (o.get("ts", [0, 0])[1], o.get("ts", [0, 0])[0], o.get("id", ""))):
        apply(doc, op)
    return doc

"""sarib.query — the 7-axis parameterized walk (Stage 6/7, D-026..D-034).
spec = {start, select, direction, order, filter, bound, derivation, projection}
Returns a bounded result subgraph carrying stable ids (D-032). Cycle-safe (D-027).
"""
from __future__ import annotations
from .model import Doc, anchor_owner


def _match(doc: Doc, n, flt) -> bool:
    if not flt:
        return True
    if "type" in flt and (n.type or "") != flt["type"] and not (n.type or "").endswith(":" + flt["type"]):
        return False
    if "status" in flt and n.properties.get("status", n.status) != flt["status"]:
        return False
    for key, op, val in flt.get("prop", []):
        have = n.properties.get(key)
        if op == "=" and str(have) != str(val):
            return False
        if op == "!=" and str(have) == str(val):
            return False
        if op == "exists" and have is None:
            return False
    return True


def query(doc: Doc, spec: dict) -> dict:
    start = spec.get("start", "all")
    select = spec.get("select", "none")
    direction = spec.get("direction", "forward")
    order = spec.get("order", "document")
    flt = spec.get("filter", {})
    bound = spec.get("bound", {"max_nodes": 500})
    proj = spec.get("projection", ["id", "type", "title", "props"])
    maxn = bound.get("max_nodes", 500)
    maxd = bound.get("max_depth", 50)

    result_ids, result_edges, cursor = [], [], None

    if select == "none":                       # pure selection (priority/chronological case)
        pool = [n for n in doc.walk(None) if _match(doc, n, flt)]
        if order.startswith("by-"):
            key = order[3:]
            pool.sort(key=lambda n: (str(n.properties.get(key, "~")), n.id))
        result_ids = [n.id for n in pool[:maxn]]
        cursor = pool[maxn].id if len(pool) > maxn else None
    else:                                      # graph walk
        seeds = [s for s in ([start] if isinstance(start, str) else start) if s in doc.nodes]
        seen, frontier, depth = set(), list(seeds), 0
        while frontier and len(result_ids) < maxn and depth <= maxd:
            nxt = []
            for nid in frontier:
                if nid in seen:                # cycle-safe: emit-once (D-027)
                    continue
                seen.add(nid)
                n = doc.nodes[nid]
                if _match(doc, n, flt):
                    result_ids.append(nid)
                if select in ("contains", "any"):
                    for c in doc.children(nid):
                        nxt.append(c.id)
                if select != "contains":
                    for eid in sorted(doc.edges):        # tie-break cascade (D-029)
                        e = doc.edges[eid]
                        if e.status != "active" or e.target.startswith("?unresolved:"):
                            continue
                        etypes = select if isinstance(select, list) else [select]
                        if select != "any" and e.type not in etypes:
                            continue
                        esrc = anchor_owner(doc, e.source)
                        etgt = anchor_owner(doc, e.target)
                        if direction in ("forward", "both") and esrc == nid:
                            nxt.append(etgt); result_edges.append(eid)
                        if direction in ("backward", "both") and etgt == nid:
                            nxt.append(esrc); result_edges.append(eid)
            frontier = nxt
            depth += 1
        if frontier:
            cursor = frontier[0]

    def project(nid):
        n = doc.nodes[nid]
        rec = {}
        for f in proj:
            if f == "props":
                rec["props"] = {k: v for k, v in n.properties.items() if not k.startswith("_")}
            elif f == "title":
                rec["title"] = n.name()
            else:
                rec[f] = getattr(n, f, None)
        return rec

    return {"nodes": [project(i) for i in result_ids],
            "edges": [{"id": e, "type": doc.edges[e].type,
                       "source": anchor_owner(doc, doc.edges[e].source),
                       "target": anchor_owner(doc, doc.edges[e].target)}
                      for e in dict.fromkeys(result_edges)],
            "cursor": cursor,
            "diagnostics": doc.diagnostics}

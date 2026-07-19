"""sarib.canon — the canonical normal form (Stage 9, D-041).
Line-oriented canonical JSON: one record per line, document-order nodes,
sorted keys, canonical scalars. Exactly one byte-string per model state.
"""
from __future__ import annotations
import json
from .model import Doc


def _clean(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in (None, "", {}, []) and not k.startswith("_")}


def canon(doc: Doc) -> str:
    out = []
    header = {"sarib": doc.meta.get("sarib", "0.1")}
    for k in sorted(doc.meta):
        if k != "sarib":
            header[k] = doc.meta[k]
    out.append(json.dumps(header, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    for n in doc.walk(None):                                # document order (invariant 10)
        rec = _clean({
            "id": n.id, "kind": "node", "type": n.type, "hint": n.kind_hint,
            "title": n.title, "content": n.content, "slug": n.slug,
            "props": {k: v for k, v in sorted(n.properties.items())
                      if not k.startswith("_")
                      and not (isinstance(v, str) and v.startswith("[[") and v.endswith("]]"))},
            "parent": n.parent, "order": n.order,
            "status": None if n.status == "active" else n.status,
            "provenance": n.provenance,
        })
        out.append(json.dumps(rec, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    for eid in sorted(doc.edges):                            # tie-break cascade (D-029)
        e = doc.edges[eid]
        rec = _clean({
            "id": e.id, "kind": "edge", "type": e.type, "source": e.source,
            "target": e.target, "family": None if e.family == "crossref" else e.family,
            "props": dict(sorted(e.properties.items())) or None,
            "status": None if e.status == "active" else e.status,
        })
        out.append(json.dumps(rec, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    return "\n".join(out) + "\n"

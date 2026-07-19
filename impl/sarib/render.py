"""sarib.render — projections (Stage 12, D-052): view = query + template.
document (= fmt, the live canonical surface), outline (+spatial cues, D-047),
board (terminal), mermaid (terminal, D-053).
"""
from __future__ import annotations
from .model import Doc, anchor_owner


def fmt(doc: Doc) -> str:
    """Model -> Candidate-A surface. The document projection; idempotent (D-051)."""
    out = []
    if doc.meta:
        out.append("---")
        for k, v in doc.meta.items():
            out.append(f"{k}: {v}")
        out.append("---\n")
    for n in doc.walk(None):
        if n.kind_hint == "heading":
            level = int(n.properties.get("_level", _depth(doc, n) + 1))
            marks = ""
            attrs = []
            if n.type:
                attrs.append(f".{n.type}")
            if n.slug:
                attrs.append(f"#{n.slug}")
            if attrs:
                marks += " {" + " ".join(attrs) + "}"
            if not n.id.startswith("n") or not n.id[1:].isdigit():
                marks += f" ^{n.id}"
            out.append(f"{'#' * level} {n.title}{marks}")
            for k, v in n.properties.items():
                if not k.startswith("_"):
                    out.append(f"{k}:: {v}")
            out.append("")
        elif n.kind_hint == "item":
            t = f"- {n.title}"
            if n.type:
                t += f" {{.{n.type}}}"
            out.append(t)
        else:
            out.append(n.content + "\n")
    return "\n".join(out).rstrip() + "\n"


def _depth(doc: Doc, n) -> int:
    d, p = 0, n.parent
    while p is not None:
        d, p = d + 1, doc.nodes[p].parent
    return d


def outline(doc: Doc) -> str:
    """Outline view with spatial cues: depth indent, [k/n] task cookies, subtree size (D-047)."""
    out = []
    for n in doc.walk(None):
        if n.kind_hint == "prose":
            continue
        d = _depth(doc, n)
        sub = list(doc.walk(n.id))
        tasks = [m for m in sub if m.type and m.type.endswith("task")]
        cue = ""
        if tasks:
            done = sum(1 for t in tasks if t.properties.get("status") == "done")
            cue = f" [{done}/{len(tasks)}]"
        size = f" ({len(sub)})" if sub else ""
        typ = f" ·{n.type}" if n.type else ""
        out.append(f"{'  ' * d}- {n.title}{typ}{cue}{size}")
    return "\n".join(out) + "\n"


def board(doc: Doc) -> str:
    """Kanban projection of tasks by status (terminal export)."""
    cols: dict = {}
    for n in doc.walk(None):
        if n.type and n.type.endswith("task"):
            cols.setdefault(n.properties.get("status", "todo"), []).append(n)
    out = []
    for status in sorted(cols):
        out.append(f"== {status.upper()} ({len(cols[status])}) ==")
        for n in cols[status]:
            due = f"  (due {n.properties['due']})" if "due" in n.properties else ""
            out.append(f"  • {n.title}{due}   [{n.id}]")
    return "\n".join(out) + "\n"


def mermaid(doc: Doc) -> str:
    """Dependency-graph projection -> Mermaid (terminal export, D-053: self-declared read-only)."""
    out = ["%% terminal export — edits do not flow back (D-053)", "flowchart TD"]
    for e in doc.edges.values():
        if e.status != "active" or e.target.startswith("?unresolved:"):
            continue
        s = doc.nodes.get(anchor_owner(doc, e.source))
        t = doc.nodes.get(anchor_owner(doc, e.target))
        if s and t and s.id != t.id:
            out.append(f'  {s.id}["{s.name()}"] -->|{e.type}| {t.id}["{t.name()}"]')
    return "\n".join(out) + "\n"


VIEWS = {"document": fmt, "outline": outline, "board": board, "mermaid": mermaid}

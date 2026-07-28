"""sarib.render — projections (Stage 12, D-052): view = query + template.
document (= fmt, the live canonical surface), outline (+spatial cues, D-047),
board (terminal), mermaid (terminal, D-053).
"""
from __future__ import annotations
from .model import Doc, anchor_owner


def _stats(doc: Doc):
    """(depth, size, tasks, done) per node id in two linear passes. `size/tasks/done`
    are strictly-below counts. This replaces a `walk(n.id)` inside a `walk(None)` —
    that nesting was super-quadratic. Returned as one tuple rather than two helpers
    to stay inside the G4 LOC budget; callers needing only depth ignore the rest."""
    order = list(doc.walk(None))
    depth, size = {}, {n.id: 0 for n in order}
    tasks, done = dict(size), dict(size)
    for n in order:                               # parents precede children here
        depth[n.id] = depth.get(n.parent, -1) + 1
    for n in reversed(order):                     # children precede parents here
        if n.parent in size:
            task = bool(n.type and n.type.endswith("task"))
            size[n.parent] += size[n.id] + 1
            tasks[n.parent] += tasks[n.id] + (1 if task else 0)
            done[n.parent] += done[n.id] + (
                1 if task and n.properties.get("status") == "done" else 0)
    return depth, size, tasks, done


def fmt(doc: Doc) -> str:
    """Model -> Candidate-A surface. The document projection; idempotent (D-051)."""
    out = []
    if doc.meta:
        out.append("---")
        for k, v in doc.meta.items():
            out.append(f"{k}: {v}")
        out.append("---\n")
    depths = _stats(doc)[0]
    for n in doc.walk(None):
        if n.kind_hint == "heading":
            level = int(n.properties.get("_level", depths[n.id] + 1))
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


def outline(doc: Doc) -> str:
    """Outline view with spatial cues: depth indent, [k/n] task cookies, subtree size (D-047)."""
    out = []
    depths, size, tasks, done = _stats(doc)
    for n in doc.walk(None):
        if n.kind_hint == "prose":
            continue
        cue = f" [{done[n.id]}/{tasks[n.id]}]" if tasks[n.id] else ""
        sz = f" ({size[n.id]})" if size[n.id] else ""
        typ = f" ·{n.type}" if n.type else ""
        out.append(f"{'  ' * depths[n.id]}- {n.title}{typ}{cue}{sz}")
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

"""sarib.model — the core object model (Stage 4). Nodes, edges, invariants."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Node:
    id: str
    type: Optional[str] = None          # None = untyped prose (L0)
    kind_hint: str = "prose"            # heading | item | prose | document  (surface fidelity only)
    title: str = ""                     # heading/item line text (sans marks); "" for prose
    content: str = ""                   # raw inline text (prose body); round-trip faithful
    slug: Optional[str] = None
    properties: dict = field(default_factory=dict)
    status: str = "active"              # active | retracted   (P12)
    provenance: Optional[str] = None    # None = asserted-by-owner (D-019)
    parent: Optional[str] = None        # the single home containment edge (D-016)
    order: int = 0                      # sibling order (invariant 5)
    version: int = 0                    # bumped per op; expect-precondition target (D-038)

    def name(self) -> str:
        return self.title or (self.content[:40] if self.content else self.id)


@dataclass
class Edge:
    id: str
    type: str
    source: str
    target: str                         # node id, or "?unresolved:<name>" (D-024: never guessed)
    family: str = "crossref"
    properties: dict = field(default_factory=dict)
    status: str = "active"
    provenance: Optional[str] = None
    version: int = 0


@dataclass
class Doc:
    meta: dict = field(default_factory=dict)     # front matter (vocab pin, title, ...)
    nodes: dict = field(default_factory=dict)    # id -> Node (insertion = document order)
    edges: dict = field(default_factory=dict)    # id -> Edge
    diagnostics: list = field(default_factory=list)

    # -- containment helpers (the spanning tree, D-016) --
    def children(self, nid: Optional[str]) -> list:
        kids = [n for n in self.nodes.values() if n.parent == nid and n.status == "active"]
        return sorted(kids, key=lambda n: (n.order, n.id))

    def walk(self, nid: Optional[str] = None):
        """inorder(N, E_c): DFS pre-order by sibling order — THE document (Stage 4 §6)."""
        for c in self.children(nid):
            yield c
            yield from self.walk(c.id)

    def node_by_slug(self, slug: str) -> Optional[Node]:
        for n in self.nodes.values():
            if n.slug == slug and n.status == "active":
                return n
        return None

    # -- Tier-1 validation: the 10 invariants (Stage 4 §11) --
    def check_invariants(self) -> list:
        diags = []
        seen_slugs = {}
        for n in self.nodes.values():
            if n.parent is not None and n.parent not in self.nodes:
                diags.append(f"invariant2: node {n.id} has missing parent {n.parent}")
            if n.slug:
                if n.slug in seen_slugs:
                    diags.append(f"duplicate-slug: #{n.slug} on {seen_slugs[n.slug]} and {n.id}")
                seen_slugs[n.slug] = n.id
        # cycle check on containment (must be a tree)
        for n in self.nodes.values():
            hops, p = 0, n.parent
            while p is not None and hops <= len(self.nodes):
                p = self.nodes[p].parent if p in self.nodes else None
                hops += 1
            if hops > len(self.nodes):
                diags.append(f"invariant2: containment cycle at {n.id}")
        for e in self.edges.values():
            if e.source not in self.nodes:
                diags.append(f"invariant3: edge {e.id} dangling source {e.source}")
            if not e.target.startswith("?unresolved:") and e.target not in self.nodes:
                diags.append(f"invariant3: edge {e.id} dangling target {e.target}")
        return diags


def anchor_owner(doc: "Doc", nid: str) -> str:
    """Edges anchored in an untitled prose block bubble up to the nearest titled
    ancestor for traversal/display (Stage 4 §5.3 anchor vs semantic endpoint)."""
    n = doc.nodes.get(nid)
    while n is not None and n.kind_hint == "prose" and n.parent:
        n = doc.nodes.get(n.parent)
    return n.id if n else nid


def normalize_name(s: str) -> str:
    import unicodedata
    return " ".join(unicodedata.normalize("NFC", s).casefold().split())

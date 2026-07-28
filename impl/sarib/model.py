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
    # derived, disposable, never serialized or hashed (P17; the in-memory sibling of D-044)
    _idx: Optional[dict] = field(default=None, repr=False, compare=False)

    # -- derived indexes --
    # Naive scans here were quadratic under walk/query/parse/render; see
    # plans/01-scale-remediation.md. WRITERS MUST CALL touch() after changing
    # parent / order / status / slug, or adding or retargeting an edge.
    # impl/tests/test_index_fuzz.py is the net that catches a forgotten touch().
    def touch(self) -> None:
        self._idx = None

    def _index(self) -> dict:
        if self._idx is None:
            kids, slugs, out, inn = {}, {}, {}, {}
            for n in self.nodes.values():                 # insertion order = document order
                if n.status == "active":
                    kids.setdefault(n.parent, []).append(n)
                    if n.slug and n.slug not in slugs:    # first wins, as the old scan did
                        slugs[n.slug] = n.id
            for sibs in kids.values():
                sibs.sort(key=lambda n: (n.order, n.id))  # invariant 5 + tie-break
            for eid in sorted(self.edges):                # D-029 tie-break cascade, once
                e = self.edges[eid]
                # keyed by the ANCHOR-RESOLVED endpoint (Stage 4 §5.3): an edge anchored in
                # a prose block belongs to its nearest titled ancestor for traversal, which
                # is the identity the traversal in query.py matches on.
                out.setdefault(anchor_owner(self, e.source), []).append(eid)
                inn.setdefault(anchor_owner(self, e.target), []).append(eid)
            self._idx = {"kids": kids, "slugs": slugs, "out": out, "in": inn}
        return self._idx

    # -- containment helpers (the spanning tree, D-016) --
    def children(self, nid: Optional[str]) -> list:
        return self._index()["kids"].get(nid) or ()

    def walk(self, nid: Optional[str] = None):
        """inorder(N, E_c): DFS pre-order by sibling order — THE document (Stage 4 §6).
        Iterative: containment depth is an axis independent of node count, and
        recursion here overflowed the stack on deep outlines regardless of size."""
        kids = self._index()["kids"]
        stack = list(reversed(kids.get(nid) or ()))
        while stack:
            n = stack.pop()
            yield n
            sub = kids.get(n.id)
            if sub:
                stack.extend(reversed(sub))

    def node_by_slug(self, slug: str) -> Optional[Node]:
        nid = self._index()["slugs"].get(slug)
        return self.nodes[nid] if nid is not None else None

    # -- crossref adjacency; both lists are in sorted-edge-id order (D-029) --
    def out_edges(self, nid: str):
        return self._index()["out"].get(nid) or ()

    def in_edges(self, nid: str):
        return self._index()["in"].get(nid) or ()

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
        # cycle check on containment (must be a tree). Memoized on `safe`, so every
        # node's ancestor chain is walked at most once: O(N), not O(N * depth).
        safe = set()
        for start in self.nodes:
            path, on_path, p = [], set(), start
            while p is not None and p in self.nodes and p not in safe:
                if p in on_path:
                    diags.append(f"invariant2: containment cycle at {p}")
                    break
                on_path.add(p)
                path.append(p)
                p = self.nodes[p].parent
            safe.update(path)
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

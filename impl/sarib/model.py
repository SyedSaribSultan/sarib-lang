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
            kids, slugs, out, inn, dups = {}, {}, {}, {}, {}
            for n in self.nodes.values():                 # insertion order = document order
                sid = n.properties.get("_id", n.id)
                if sid != n.id:                           # a repeated ^id, kept (D-066)
                    dups.setdefault(sid, [sid]).append(n.id)
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
            self._idx = {"kids": kids, "slugs": slugs, "out": out, "in": inn, "dups": dups}
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

    def ambiguous_ids(self) -> dict:
        """authored ^id -> [model ids] for every ^id the source declares more than once.
        Such an id names no single node, so ops refuse it and writers refuse the file (D-066)."""
        return self._index()["dups"]

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

    def lint_cycles(self) -> list:
        """cycle-in-acyclic-edge (Stage 11 §5, D-027): a lint, never a traversal precondition.
        One report per back edge found by a DFS in sorted id order, so output is deterministic."""
        diags, by_rel = [], {}
        for eid in sorted(self.edges):
            e = self.edges[eid]
            if e.type in ACYCLIC and e.status == "active" and e.target in self.nodes:
                by_rel.setdefault(e.type, {}).setdefault(anchor_owner(self, e.source), []).append(
                    anchor_owner(self, e.target))              # same endpoints traversal uses
        for rel in sorted(by_rel):
            adj = by_rel[rel]
            state: dict = {}                        # 1 = on the DFS path, 2 = finished
            for root in sorted(adj):
                if root in state:
                    continue
                path, stack = [root], [iter(adj.get(root, ()))]
                state[root] = 1
                while stack:
                    nxt = next(stack[-1], None)
                    if nxt is None:
                        state[path.pop()] = 2
                        stack.pop()
                    elif state.get(nxt) == 1:
                        cyc = path[path.index(nxt):] + [nxt]
                        more = f" -> ... ({len(cyc) - 8} more)" if len(cyc) > 9 else ""
                        diags.append(f"cycle-in-acyclic-edge: {rel} "
                                     + " -> ".join(cyc[:8] if more else cyc) + more)
                    elif nxt not in state:
                        state[nxt] = 1
                        path.append(nxt)
                        stack.append(iter(adj.get(nxt, ())))
        return diags

    # Op-time validation, scoped to the ids one op touched (D-065).
    # WHY LOCAL: a whole-document check after every op meant that a file which already
    # carried ANY unrelated violation — two headings sharing one {#slug}, say — rejected
    # *every* operation, including the one that would repair it. That locked an author out
    # of their own file. Full-document validation stays in check_invariants(), which is what
    # `sarib validate` and load-time run.
    # WHY THIS IS THE WHOLE SURFACE: ops cannot mint a slug (no op takes one), and cannot
    # leave an edge dangling (create-node/move/add-edge/merge each guard their endpoints
    # inline and raise before mutating). That leaves invariant 2 — parent exists, and the
    # ancestor chain terminates — which is what this checks.
    def check_touched(self, ids) -> list:
        diags = []
        for nid in ids:
            n = self.nodes.get(nid)
            if n is None:
                continue
            if n.parent is not None and n.parent not in self.nodes:
                diags.append(f"invariant2: node {n.id} has missing parent {n.parent}")
            hops, p = 0, n.parent
            while p is not None and p in self.nodes and hops <= len(self.nodes):
                p, hops = self.nodes[p].parent, hops + 1
            if hops > len(self.nodes):
                diags.append(f"invariant2: containment cycle at {n.id}")
        return diags


# Edge types whose algebra is declared acyclic (Stage 5 §3.2; `contains` is the tree itself).
ACYCLIC = frozenset({"transcludes", "depends-on", "refines", "part-of", "supersedes",
                     "merged-into", "split-from"})


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

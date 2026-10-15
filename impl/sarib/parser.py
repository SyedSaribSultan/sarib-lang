"""sarib.parser — Candidate-A surface -> model. Tier-0 TOTAL parse (D-049):
every byte string yields a model; unrecognized lines become L0 prose nodes.
Local, line-shaped, no backtracking (D-045). Deterministic ids in document order.
"""
from __future__ import annotations
import re
from .model import Doc, Node, Edge, normalize_name

H_RE = re.compile(r"^(#{1,6})\s+(.*)$")
LI_RE = re.compile(r"^(\s*)[-*]\s+(.*)$")
FIELD_RE = re.compile(r"^([A-Za-z][\w-]*)::\s*(.*)$")
ATTR_RE = re.compile(r"\s*\{([^{}]*)\}\s*$")
BID_RE = re.compile(r"\s*\^([\w-]+)\s*$")
TYPED_REF_RE = re.compile(r"\[([A-Za-z][\w-]*)::\s*\[\[([^\[\]]+)\]\]\]")
WIKI_RE = re.compile(r"\[\[([^\[\]]+)\]\]")
COOKIE_RE = re.compile(r"\s*\[\d+/\d+[^\]]*\]\s*$")  # derived cue: ignored on parse (D-051)


def _strip_marks(text: str):
    """Peel trailing ^id, {attrs}, and derived [k/n] cookies off a title line."""
    nid = slug = ntype = None
    props = {}
    changed = True
    while changed:                      # peel trailing marks in any order until fixed-point
        changed = False
        m = COOKIE_RE.search(text)
        if m:
            text, changed = text[: m.start()], True
            continue
        m = BID_RE.search(text)
        if m:
            nid, text, changed = m.group(1), text[: m.start()], True
            continue
        m = ATTR_RE.search(text)
        if m:
            for tok in m.group(1).split():
                if tok.startswith("."):
                    ntype = tok[1:]
                elif tok.startswith("#"):
                    slug = tok[1:]
                elif "=" in tok:
                    k, v = tok.split("=", 1)
                    props[k] = v.strip('"')
            text, changed = text[: m.start()], True
    return text.strip(), nid, slug, ntype, props


def parse(src: str) -> Doc:
    doc = Doc()
    counter = [0]

    line_of: dict = {}  # node id -> 1-based source line, for located diagnostics

    def place(n: Node, explicit, line: int) -> Node:
        """Give `n` its id and add it. A ^id already in use NEVER overwrites the earlier
        node — that silently deleted it (invariant 1, D-066). The later node keeps its
        authored id in `_id` (so fmt writes it back unchanged), takes the deterministic
        model id `<id>~<k>`, and the collision is reported with both locations."""
        if not explicit:
            while f"n{counter[0] + 1}" in doc.nodes:   # skip ids an explicit ^nK took
                counter[0] += 1
            counter[0] += 1
            n.id = f"n{counter[0]}"
        elif explicit in doc.nodes:
            k = 2
            while f"{explicit}~{k}" in doc.nodes:
                k += 1
            n.id = f"{explicit}~{k}"
            n.properties["_id"] = explicit
            first = f" (line {line_of[explicit]})" if explicit in line_of else ""
            doc.diagnostics.append(f"duplicate-id: ^{explicit} at line {line} is already "
                                   f"node {explicit}{first}; kept as {n.id}")
        else:
            n.id = explicit
            if explicit[:1] == "n" and explicit[1:].isdigit():
                n.properties["_id"] = explicit    # authored, though auto-shaped: fmt keeps it
        if line:
            line_of[n.id] = line
        doc.nodes[n.id] = n
        return n

    lines = src.splitlines()
    i = 0
    # -- front matter --
    if lines and lines[0].strip() == "---":
        j = 1
        while j < len(lines) and lines[j].strip() != "---":
            if ":" in lines[j]:
                k, v = lines[j].split(":", 1)
                doc.meta[k.strip()] = v.strip()
            j += 1
        i = j + 1

    stack = []          # [(heading_level, node_id)]
    current = None      # node fields attach to (last heading/item)
    para: list = []
    pending_edges = []  # (source_id, rel, target_name)
    sib: dict = {}      # container id -> next sibling order

    def container():
        return stack[-1][1] if stack else None

    def next_order(c):
        """Sibling order for the next child of `c`. Equivalent to the old
        len(doc.children(c)) — every node parsed so far is active — but O(1),
        which is what makes parse linear instead of quadratic."""
        sib[c] = sib.get(c, 0) + 1
        return sib[c] - 1

    def scan_inline(source_id: str, text: str):
        for m in TYPED_REF_RE.finditer(text):
            pending_edges.append((source_id, m.group(1), m.group(2)))
        stripped = TYPED_REF_RE.sub("", text)
        for m in WIKI_RE.finditer(stripped):
            pending_edges.append((source_id, "relates-to", m.group(1)))

    def flush_para():
        nonlocal para
        if not para:
            return
        text = "\n".join(para).strip()
        para = []
        if not text or text.startswith("<!--"):
            return
        n = place(Node(id="", kind_hint="prose", content=text, parent=container(),
                       order=next_order(container())), None, 0)
        scan_inline(n.id, text)

    while i < len(lines):
        line = lines[i]
        # multi-line HTML comments: skip wholesale
        if line.lstrip().startswith("<!--"):
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        if not line.strip():
            flush_para()
            i += 1
            continue

        m = H_RE.match(line)
        if m:
            flush_para()
            level = len(m.group(1))
            text, nid, slug, ntype, props = _strip_marks(m.group(2))
            while stack and stack[-1][0] >= level:
                stack.pop()
            n = place(Node(id="", kind_hint="heading", title=text, type=ntype,
                           slug=slug, properties=props, parent=container(),
                           order=next_order(container())), nid, i + 1)
            n.properties["_level"] = level
            scan_inline(n.id, text)
            stack.append((level, n.id))
            current = n
            i += 1
            continue

        m = LI_RE.match(line)
        if m:
            flush_para()
            text, nid, slug, ntype, props = _strip_marks(m.group(2))
            n = place(Node(id="", kind_hint="item", title=text, type=ntype,
                           slug=slug, properties=props, parent=container(),
                           order=next_order(container())), nid, i + 1)
            scan_inline(n.id, text)
            current = n
            i += 1
            continue

        m = FIELD_RE.match(line)
        if m and current is not None:
            key, val = m.group(1), m.group(2).strip()
            wl = WIKI_RE.fullmatch(val)
            if wl:  # field whose value is a wikilink = a typed edge (owner:: [[Alice]])
                pending_edges.append((current.id, key, wl.group(1)))
                current.properties[key] = val   # keep raw for surface round-trip (D-051);
                                                # canon skips wikilink-valued props (edge-represented)
            else:
                current.properties[key] = val
            i += 1
            continue

        para.append(line)
        i += 1
    flush_para()

    # -- reference resolution (D-024: explicit slug -> nearest-in-containment -> global -> unresolved) --
    by_name: dict = {}
    for n in doc.nodes.values():
        if n.title:
            by_name.setdefault(normalize_name(n.title), []).append(n.id)

    def resolve(source_id: str, name: str):
        if name.startswith("#"):
            hit = doc.node_by_slug(name[1:])
            return hit.id if hit else None
        cands = by_name.get(normalize_name(name), [])
        if len(cands) == 1:
            return cands[0]
        if len(cands) > 1:  # nearest-in-containment: walk up source ancestors
            anc, p = [], doc.nodes.get(source_id)
            while p is not None:
                anc.append(p.id)
                p = doc.nodes.get(p.parent) if p.parent else None
            def dist(cid):
                q, d = doc.nodes.get(cid), 0
                while q is not None:
                    if q.id in anc:
                        return d + anc.index(q.id)
                    q = doc.nodes.get(q.parent) if q.parent else None
                    d += 1
                return 10 ** 6
            ranked = sorted(cands, key=lambda c: (dist(c), c))
            if dist(ranked[0]) < dist(ranked[1]):
                return ranked[0]
            doc.diagnostics.append(f"ambiguous-reference: '{name}' from {source_id}")
            return None
        return None

    ec = 0
    for src_id, rel, name in pending_edges:
        tid = resolve(src_id, name)
        ec += 1
        if tid is None:
            doc.diagnostics.append(f"unresolved-reference: '{name}' from {src_id}")
            tid = f"?unresolved:{name}"
        doc.edges[f"e{ec}"] = Edge(id=f"e{ec}", type=rel, source=src_id, target=tid)

    doc.touch()          # edges were added after the slug lookups built the index
    doc.diagnostics.extend(doc.check_invariants())
    doc.diagnostics.extend(doc.lint_cycles())
    return doc

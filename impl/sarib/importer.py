"""sarib.importer — prose/markdown -> a .sarib knowledge graph. The adoption on-ramp.

A CONSUMER of the model (like preview.py and the MCP server); it lives OUTSIDE the
<=1000 LOC parser core (G4), so it does not affect that budget.

Two layers, both emitting valid, round-trippable .sarib:

  skeleton (default)   deterministic. Markdown headings/list-items/paragraphs -> nodes with
                       stable slug ids + the containment tree; existing [[wikilinks]] and
                       [rel:: [[x]]] refs are preserved by the parser. No LLM, no network.

  --extract-edges      constrained + verified edge extraction (research/importer-extraction.md).
                       Boxed so a model can only SELECT, never invent:
                         L1 closed vocab + existing-slug targets   (JSON-schema enum)
                         L2 constrained decoding                    (Ollama `format`=schema)
                         L3 span-grounding                          (quote must be verbatim)
                         L4 entailment verify                       (independent yes/no per edge)
                         L5 abstain                                 (unsupported/ambiguous dropped)
                       Kept edges are written to the surface as `[rel:: [[#slug]]]` with an
                       `inferred` provenance comment (D-019); resolution never guesses (D-024).

Known limitations (documented, not bugs): edges are read from a node's own paragraph text, so
relationships stated only inside sub-bullets or deeper sub-sections are missed (conservative:
fewer edges, never wrong). Obsidian-style block ids (`^id`) on a heading are not preserved
(surface refs use slugs). Import each file singly for maximum fidelity.
"""
from __future__ import annotations
import json, re, urllib.request
from .parser import parse
from .model import anchor_owner

DEFAULT_VOCAB = ["depends-on", "refines", "supersedes", "cites", "part-of"]
VOCAB_DEF = {
    "depends-on": "the source cannot proceed / is blocked until the target.",
    "refines": "the source clarifies, extends, or amends the target.",
    "supersedes": "the source replaces or overrides the target.",
    "cites": "the source references the target as evidence, basis, or grounding.",
    "part-of": "the source is a component or sub-part of the target.",
}
PHRASE = {
    "depends-on": "depends on (is blocked until) ",
    "refines": "refines or amends ",
    "supersedes": "replaces or supersedes ",
    "cites": "cites as evidence ",
    "part-of": "is part of ",
}
_TYPE_RE = re.compile(r"^[A-Za-z][\w-]*$")   # a rel type must survive the parser's TYPED_REF_RE
OLLAMA = "http://localhost:11434/api/chat"


# ---------- deterministic skeleton ----------

def _slug_base(title):
    s = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-") or "node"
    return s[:48].rstrip("-") or "node"


def _dedup(base, used):
    s, i = base, 2
    while s in used:
        s = f"{base}-{i}"; i += 1
    used.add(s)
    return s


def _strip_front_matter(text):
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        j = 1
        while j < len(lines) and lines[j].strip() != "---":
            j += 1
        return "\n".join(lines[j + 1:]).lstrip("\n")
    return text


def _bump_headings(text):
    return re.sub(r"(?m)^(#{1,5})(\s)", r"#\1\2", text)


def _combine(inputs):
    """One file -> as-is (parser lifts its front matter). Many -> each nested under a file
    heading, with its own front matter stripped (else it would become body prose)."""
    if len(inputs) == 1:
        return inputs[0][1]
    return "\n\n".join(f"# {name}\n\n" + _bump_headings(_strip_front_matter(text))
                       for name, text in inputs)


def _assign_slugs(doc):
    """Every titled node gets a UNIQUE slug. Explicit slugs (from `{#id}`) are de-duped too
    (bug fix: a document-authored slug could otherwise collide with an auto one)."""
    used, slug_of = set(), {}
    for n in doc.walk(None):
        if n.title:
            n.slug = _dedup(n.slug or _slug_base(n.title), used)
            slug_of[n.id] = n.slug
    doc.touch()          # slugs changed, so the derived slug index is stale
    return slug_of


def _section_text(doc, node):
    """The node's own prose (its title + direct prose children) — what edges are read from."""
    body = [c.content for c in doc.children(node.id) if c.kind_hint == "prose"]
    return (node.title + "\n" + "\n".join(body)).strip()


# ---------- constrained + verified extraction ----------

def _ollama(endpoint, model, system, user, schema, timeout=120):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "stream": False, "format": schema, "options": {"temperature": 0, "seed": 42},
    }).encode()
    req = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(json.load(r)["message"]["content"])


def _norm(s):
    return re.sub(r"\s+", " ", s or "").strip().lower()


def _extract_schema(vocab, slugs):
    return {"type": "object", "properties": {"edges": {"type": "array", "items": {
        "type": "object",
        "properties": {"type": {"type": "string", "enum": vocab},
                       "target": {"type": "string", "enum": slugs},
                       "span": {"type": "string"}},
        "required": ["type", "target", "span"]}}}, "required": ["edges"]}


_VERIFY_SCHEMA = {"type": "object",
                  "properties": {"answer": {"type": "string", "enum": ["yes", "no"]}},
                  "required": ["answer"]}


def _existing_edges(doc):
    """(src-slug, type, tgt-slug) already present from the surface — for de-dup (#8)."""
    seen = set()
    for e in doc.edges.values():
        if e.status != "active" or e.target.startswith("?"):
            continue
        s = doc.nodes.get(anchor_owner(doc, e.source))
        t = doc.nodes.get(anchor_owner(doc, e.target))
        if s and t and s.slug and t.slug:
            seen.add((s.slug, e.type, t.slug))
    return seen


def _propose(doc, model, endpoint, vocab):
    """One constrained call per titled heading node. Returns (kept, stats). kept: src_id->[edge]."""
    titled = [n for n in doc.walk(None) if n.title and n.kind_hint == "heading"]
    id_of = {n.slug: n.id for n in titled}
    slugs = [n.slug for n in titled]
    already = _existing_edges(doc)
    vdef = "\n".join(f"- {k}: {v}" for k, v in VOCAB_DEF.items() if k in vocab)
    directory = "\n".join(f"{n.slug}: {n.title}" for n in titled)
    system = (
        "You are a STRICT relationship extractor. Output ONLY relationships EXPLICITLY stated "
        "in the given text. Do NOT infer, guess, or use outside knowledge. When in doubt, leave "
        "it out.\n\nAllowed types (use EXACTLY one):\n" + vdef + "\n\n'target' must be the slug "
        "of the OTHER node being referred to. 'span' MUST be the exact verbatim substring of the "
        "text that states the relationship. If the text states no relationship to another node, "
        "return an empty list.")
    stats = {"proposed": 0, "reject_target": 0, "reject_span": 0, "verify_no": 0, "dup": 0, "kept": 0}
    kept = {}
    for n in titled:
        text = _section_text(doc, n)
        others = [s for s in slugs if s != n.slug]
        if not others:
            continue
        user = (f"Current node: {n.slug} — {n.title}\n\nDirectory of other nodes (slug: title):\n"
                f"{directory}\n\nText of the current node:\n{text}\n\n"
                "Return JSON {\"edges\":[{\"type\":..,\"target\":\"<slug>\",\"span\":\"..\"}]}.")
        try:
            res = _ollama(endpoint, model, system, user, _extract_schema(vocab, others))
        except Exception:
            stats["errors"] = stats.get("errors", 0) + 1
            continue
        for e in res.get("edges", []):
            stats["proposed"] += 1
            rel, tgt, span = e.get("type"), e.get("target"), e.get("span", "")
            if rel not in vocab or tgt not in id_of or tgt == n.slug:
                stats["reject_target"] += 1; continue
            if _norm(span) not in _norm(text):                              # L3 span grounding
                stats["reject_span"] += 1; continue
            if (n.slug, rel, tgt) in already:                              # #8 de-dup vs surface
                stats["dup"] += 1; continue
            if not _verify(model, endpoint, n.title, rel, doc.nodes[id_of[tgt]].title, span):  # L4
                stats["verify_no"] += 1; continue
            kept.setdefault(n.id, []).append({"type": rel, "target_slug": tgt, "span": span})
            already.add((n.slug, rel, tgt))                               # de-dup within run too
            stats["kept"] += 1
    return kept, stats


def _verify(model, endpoint, src_title, rel, tgt_title, span):
    """L4: independent entailment check. Few-shot + natural-language claim so a weak model
    actually discriminates (a terse yes/no enum degenerates to 'no' on everything)."""
    system = (
        "Decide whether the SPAN supports the CLAIM. Reply yes if the span states or clearly "
        "implies the claim (in that direction); reply no otherwise.\n"
        "Example 1 SPAN: \"A is blocked until we finish B.\" CLAIM: A depends on B. -> yes\n"
        "Example 2 SPAN: \"B was amended by A.\" CLAIM: A refines B. -> yes\n"
        "Example 3 SPAN: \"B was amended by A.\" CLAIM: A supersedes B. -> no\n"
        "Example 4 SPAN: \"We should water the plants.\" CLAIM: A depends on B. -> no")
    user = (f"SPAN: \"{span}\"\nCLAIM: {src_title} {PHRASE.get(rel, rel + ' ')}{tgt_title}.\n"
            "Answer yes or no.")
    try:
        return _ollama(endpoint, model, system, user, _VERIFY_SCHEMA).get("answer") == "yes"
    except Exception:
        return False


# ---------- emit ----------

def _emit(doc, kept, title, extra_meta):
    out = ["---", "sarib: 0.1", "vocab: std@0.1", f"title: {title}"]
    for k, v in extra_meta.items():                     # #1: carry source front matter through
        out.append(f"{k}: {v}")
    out += ["---",
            "<!-- generated by `sarib import`; edges marked `inferred` were auto-extracted "
            "and verified (see provenance comments). -->", ""]
    for n in doc.walk(None):
        if n.kind_hint == "heading":
            level = int(n.properties.get("_level", 1))
            attrs = ([f".{n.type}"] if n.type else []) + ([f"#{n.slug}"] if n.slug else [])
            mark = (" {" + " ".join(attrs) + "}") if attrs else ""
            out.append(f"{'#' * level} {n.title}{mark}")
            for k, v in n.properties.items():
                if not k.startswith("_"):
                    out.append(f"{k}:: {v}")
            for e in kept.get(n.id, []):
                out.append(f"<!-- inferred: \"{e['span'][:80].strip()}\" -->")
                out.append(f"[{e['type']}:: [[#{e['target_slug']}]]]")
            out.append("")
        elif n.kind_hint == "item":
            attrs = ([f".{n.type}"] if n.type else []) + ([f"#{n.slug}"] if n.slug else [])
            mark = (" {" + " ".join(attrs) + "}") if attrs else ""
            out.append(f"- {n.title}{mark}")
        else:
            out.append(n.content + "\n")
    return "\n".join(out).rstrip() + "\n"


# ---------- structural round-trip verification (#4) ----------

def _pmap(d):
    """slug -> parent-slug (or None), over titled nodes: the containment shape."""
    m = {}
    for n in d.walk(None):
        if n.title:
            p = d.nodes.get(n.parent) if n.parent else None
            m[n.slug] = p.slug if (p and p.title) else None
    return m


# ---------- entry point ----------

def build(inputs, title=None, extract=False,
          model="qwen2.5:7b", endpoint=OLLAMA, vocab=None):
    """inputs: [(name, text)]. Returns (sarib_text, stats, diagnostics)."""
    vocab = vocab or list(DEFAULT_VOCAB)
    warns = [f"ignored invalid edge-type '{v}' (must match {_TYPE_RE.pattern})"
             for v in vocab if not _TYPE_RE.match(v)]                       # #7 vocab guard
    vocab = [v for v in vocab if _TYPE_RE.match(v)]

    if len(inputs) > 1:                                                     # #3 level-6 warning
        for name, txt in inputs:
            if re.search(r"(?m)^######\s", _strip_front_matter(txt)):
                warns.append(f"multi-file: '{name}' has level-6 headings; deep nesting may "
                             "flatten — import it singly for full fidelity")

    doc = parse(_combine(inputs))
    _assign_slugs(doc)
    # #1: prefer an explicit --title, else the source doc's own title, else a default
    eff_title = title or doc.meta.get("title") or "Imported knowledge"
    extra_meta = {k: v for k, v in doc.meta.items() if k not in ("sarib", "vocab", "title")}

    kept, stats = ({}, {})
    if extract:
        if not vocab:
            warns.append("no valid edge types; skipping extraction")
        else:
            kept, stats = _propose(doc, model, endpoint, vocab)

    text = _emit(doc, kept, eff_title, extra_meta)

    check = parse(text)                                                     # #4 structural check
    problems = list(warns)
    di, ci = _pmap(doc), _pmap(check)
    if set(di) != set(ci):
        problems.append(f"structure-drift: {len(di)} titled nodes intended, {len(ci)} after round-trip")
    elif di != ci:
        problems.append("structure-drift: nesting changed on round-trip")
    live_slugs = {n.slug for n in check.walk(None) if n.title}
    for lst in kept.values():
        for e in lst:
            if e["target_slug"] not in live_slugs:
                problems.append(f"inferred edge target #{e['target_slug']} did not resolve")
    unresolved = [d for d in check.diagnostics if d.startswith("unresolved-reference")]
    stats.update(nodes=len([n for n in doc.nodes.values() if n.title]),
                 edges=sum(len(v) for v in kept.values()),
                 unresolved=len(unresolved), problems=len(problems))
    return text, stats, problems + check.diagnostics

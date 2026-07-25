"""G2 corpus builder (bench/g2-g3-protocol.md, Stage 15 §4 gate G2).

ONE fact table -> THREE renditions of the SAME knowledge (cannot drift):
  kb.sarib          Candidate-A surface: types, fields, typed edges
  kb.md             plain Markdown (headings + prose) - the honest baseline
  kb.notypes.sarib  ABLATION: same skeleton/nesting/prose, types+edges stripped

Plus questions.json: 36 questions (12 lookup / 12 multi-hop / 12 aggregate),
each carrying the exact `sarib query` spec + a mechanical extraction rule.
Ground truth is DERIVED by running the query against the parsed kb.sarib and
CROSS-CHECKED against an independent fact-table computation; any mismatch aborts.
No hand-written answer keys; no LLM in the loop.

Run from repo root:  python bench/g2-corpus/build.py
"""
from __future__ import annotations
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "impl"))
from sarib import parse, query as run_query  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent

# ----------------------------------------------------------------------------
# THE fact table (single source of truth for all three corpora)
# ----------------------------------------------------------------------------

AGENTS = [  # (id, slug, name, role, team)
    ("p1", "alice-chen", "Alice Chen", "backend engineer", "Billing"),
    ("p2", "bob-marsh", "Bob Marsh", "data engineer", "Search"),
    ("p3", "carol-diaz", "Carol Diaz", "platform engineer", "Platform"),
    ("p4", "dev-patel", "Dev Patel", "product manager", "Billing"),
    ("p5", "erin-fox", "Erin Fox", "security engineer", "Platform"),
]

SOURCES = [  # (id, slug, title, origin)
    ("s1", "pci-audit", "PCI Compliance Audit 2026", "external audit report, May 2026"),
    ("s2", "latency-report", "Latency Report Q2", "internal measurement, June 2026"),
    ("s3", "user-research", "User Research June", "twelve customer interviews"),
]

DECISIONS = [  # (id, slug, title, status, date, cites_id, rationale)
    ("d1", "choose-stripe", "Choose Stripe as payment provider", "accepted", "2026-05-10", "s1",
     "Lower fees and stronger EU coverage than the incumbent."),
    ("d2", "event-sourcing", "Use event sourcing for the billing ledger", "accepted", "2026-05-22", "s2",
     "Append-only ledger simplifies audit and replay."),
    ("d3", "deprecate-rest", "Deprecate the legacy REST API", "proposed", "2026-06-03", "s3",
     "Interviewees rely on the new endpoints already."),
    ("d4", "eu-first", "Ship the EU region first", "accepted", "2026-06-11", "s3",
     "Largest waitlisted cohort is in the EU."),
    ("d5", "postgres-16", "Adopt Postgres 16 for the ledger store", "superseded", "2026-04-18", "s2",
     "Superseded by the event sourcing decision."),
]

QUESTIONS_KB = [  # (id, slug, title, status, blocks_id_or_None)
    ("q1", "soc2", "Do we need SOC2 certification before launch?", "open", "t15"),
    ("q2", "exporter-schema", "Can the exporter reuse the ledger schema?", "open", "t5"),
    ("q3", "latency-budget", "Is the latency budget 200ms or 300ms?", "resolved", None),
    ("q4", "stripe-contract", "Who signs the Stripe contract?", "open", "t1"),
]

GOALS = [("g1", "eu-launch", "EU Launch", "2026-09-15")]  # (id, slug, title, target)

WORKSTREAMS = [("ws1", "Billing"), ("ws2", "Search"), ("ws3", "Platform")]

TASKS = [  # (id, slug, title, ws, status, priority, due, owner, deps, part_of, note)
    ("t1", "stripe-checkout", "Integrate the Stripe checkout flow", "ws1", "doing", "high", "2026-08-05",
     "p1", ["d1"], None, "Covers hosted checkout and webhook handling."),
    ("t2", "migrate-invoices", "Migrate historical invoices to the ledger", "ws1", "todo", "high", "2026-08-20",
     "p1", ["t1", "d2"], None, "Backfill of roughly forty thousand historical invoices."),
    ("t3", "notify-customers", "Notify customers about the billing change", "ws1", "todo", "med", "2026-09-01",
     "p4", ["t2"], None, "Email plus in-app banner announcement."),
    ("t4", "reconcile-refunds", "Reconcile refunds against the old system", "ws1", "todo", "low", None,
     "p4", ["t2"], None, "Reconciliation window is the last two fiscal years."),
    ("t5", "invoice-exporter", "Build the invoice PDF exporter", "ws1", "todo", "med", None,
     "p1", [], None, "Exports must match the ledger totals exactly."),
    ("t6", "billing-alerts", "Set up billing alerts and dashboards", "ws1", "done", "low", None,
     "p4", [], None, "Dashboards live in the shared observability space."),
    ("t7", "search-indexing", "Rebuild the search indexing pipeline", "ws2", "doing", "high", "2026-08-12",
     "p2", [], None, "Replaces the nightly batch indexer with streaming updates."),
    ("t8", "typo-tolerance", "Add typo tolerance to product search", "ws2", "todo", "med", None,
     "p2", ["t7"], None, "Uses edit-distance matching for product names."),
    ("t9", "latency-benchmark", "Benchmark query latency at ten times load", "ws2", "done", "high", None,
     "p2", [], None, "Load profile mirrors the June traffic snapshot."),
    ("t10", "relevance-ab", "Ship the search relevance A/B test", "ws2", "todo", "med", None,
     "p4", ["t8"], None, "Experiment runs on ten percent of traffic."),
    ("t11", "archive-cluster", "Archive the old search cluster", "ws2", "todo", "low", None,
     "p2", ["t7"], None, "Cluster is kept read-only for thirty days first."),
    ("t12", "edge-cache", "Cache hot queries at the edge", "ws2", "doing", "med", None,
     "p3", ["d4"], None, "Cache keys include region and locale."),
    ("t13", "eu-region", "Provision the EU data region", "ws3", "doing", "high", "2026-08-01",
     "p3", ["d4"], "g1", "Region is provisioned in Frankfurt."),
    ("t14", "gdpr-retention", "Set up GDPR data-retention jobs", "ws3", "todo", "high", "2026-08-25",
     "p5", ["t13"], "g1", "Retention defaults to ninety days for event data."),
    ("t15", "pentest", "Run the penetration test", "ws3", "todo", "high", None,
     "p5", [], "g1", "Scope covers the public API and the admin console."),
    ("t16", "blue-green", "Automate blue-green deploys", "ws3", "done", "med", None,
     "p3", [], None, "Cutover rehearsed in the staging environment."),
    ("t17", "rotate-secrets", "Rotate all production secrets", "ws3", "done", "high", None,
     "p5", [], None, "Rotation includes database and third-party credentials."),
    ("t18", "localize-german", "Localize the checkout UI for German", "ws1", "todo", "med", None,
     "p1", ["t1"], "g1", "Covers currency, date formats, and checkout copy."),
]

TITLE = {x[0]: x[2] for x in AGENTS + SOURCES + DECISIONS + QUESTIONS_KB}
TITLE.update({g[0]: g[2] for g in GOALS})
TITLE.update({t[0]: t[2] for t in TASKS})
OWNER = {t[0]: t[7] for t in TASKS}
DEPS = {t[0]: t[8] for t in TASKS}

# ----------------------------------------------------------------------------
# Emitters — three renditions of the identical facts
# ----------------------------------------------------------------------------

def _dep_phrase(deps):  # shared wording so no rendition gains extra hints
    return " and ".join(TITLE[d] for d in deps)


def emit_sarib() -> str:
    L = ["---", "sarib: 0.1", "vocab: std@0.1", "title: Atlas Program KB", "---", "",
         "# Atlas Program KB {#atlas}", ""]
    L += ["## Goals {.section} ^sec-goals", ""]
    for gid, slug, title, target in GOALS:
        L += [f"### {title} {{.goal #{slug}}} ^{gid}", f"target:: {target}", ""]
    L += ["## Decisions {.section} ^sec-dec", ""]
    for did, slug, title, status, date, cites, why in DECISIONS:
        L += [f"### {title} {{.decision #{slug}}} ^{did}",
              f"status:: {status}", f"date:: {date}",
              f"cites:: [[{TITLE[cites]}]]", "", why, ""]
    L += ["## Open Questions {.section} ^sec-q", ""]
    for qid, slug, title, status, blocks in QUESTIONS_KB:
        L += [f"### {title} {{.question #{slug}}} ^{qid}", f"status:: {status}", ""]
        if blocks:
            L += [f"Until answered this [blocks:: [[{TITLE[blocks]}]]].", ""]
    for wid, wname in WORKSTREAMS:
        L += [f"## Workstream: {wname} {{.section}} ^{wid}", ""]
        for t in TASKS:
            tid, slug, title, ws, status, prio, due, owner, deps, part_of, note = t
            if ws != wid:
                continue
            L += [f"### {title} {{.task #{slug}}} ^{tid}",
                  f"status:: {status}", f"priority:: {prio}"]
            if due:
                L.append(f"due:: {due}")
            L.append(f"owned-by:: [[{TITLE[owner]}]]")
            if part_of:
                L.append(f"part-of:: [[{TITLE[part_of]}]]")
            L.append("")
            prose = note
            if deps:
                prose += " Gated by " + " and ".join(f"[depends-on:: [[{TITLE[d]}]]]" for d in deps) + "."
            L += [prose, ""]
    L += ["## People {.section} ^sec-people", ""]
    for pid, slug, name, role, team in AGENTS:
        L += [f"### {name} {{.agent #{slug}}} ^{pid}", f"role:: {role}", f"team:: {team}", ""]
    L += ["## Sources {.section} ^sec-src", ""]
    for sid, slug, title, origin in SOURCES:
        L += [f"### {title} {{.source #{slug}}} ^{sid}", f"origin:: {origin}", ""]
    return "\n".join(L)


def emit_md() -> str:
    """Honest plain-Markdown baseline: headings + prose, no typed fields/edges."""
    L = ["# Atlas Program KB", ""]
    L += ["## Goals", ""]
    for gid, slug, title, target in GOALS:
        L += [f"**{title}** — target date {target}.", ""]
    L += ["## Decisions", ""]
    for did, slug, title, status, date, cites, why in DECISIONS:
        L += [f"### {title}",
              f"Status: {status} ({date}). Based on {TITLE[cites]}. {why}", ""]
    L += ["## Open Questions", ""]
    for qid, slug, title, status, blocks in QUESTIONS_KB:
        line = f"### {title}", f"Status: {status}."
        L.append(line[0])
        body = line[1]
        if blocks:
            body += f" Until answered this blocks {TITLE[blocks]}."
        L += [body, ""]
    for wid, wname in WORKSTREAMS:
        L += [f"## {wname} workstream", ""]
        for t in TASKS:
            tid, slug, title, ws, status, prio, due, owner, deps, part_of, note = t
            if ws != wid:
                continue
            L.append(f"### {title}")
            body = f"Owned by {TITLE[owner]}. Status: {status}. Priority: {prio}."
            if due:
                body += f" Due {due}."
            if part_of:
                body += f" Part of {TITLE[part_of]}."
            body += f" {note}"
            if deps:
                body += f" Gated by {_dep_phrase(deps)}."
            L += [body, ""]
    L += ["## People", ""]
    for pid, slug, name, role, team in AGENTS:
        L += [f"### {name}", f"Role: {role}. Team: {team}.", ""]
    L += ["## Sources", ""]
    for sid, slug, title, origin in SOURCES:
        L += [f"### {title}", f"Origin: {origin}.", ""]
    return "\n".join(L)


def emit_notypes() -> str:
    """Ablation: kb.sarib's exact skeleton (headings, nesting, field lines, prose
    order) with types, ids, and typed-edge markup stripped. Isolates types+edges
    as the variable vs condition B."""
    L = ["---", "title: Atlas Program KB", "---", "", "# Atlas Program KB", ""]
    L += ["## Goals", ""]
    for gid, slug, title, target in GOALS:
        L += [f"### {title}", f"target: {target}", ""]
    L += ["## Decisions", ""]
    for did, slug, title, status, date, cites, why in DECISIONS:
        L += [f"### {title}", f"status: {status}", f"date: {date}",
              f"cites: {TITLE[cites]}", "", why, ""]
    L += ["## Open Questions", ""]
    for qid, slug, title, status, blocks in QUESTIONS_KB:
        L += [f"### {title}", f"status: {status}", ""]
        if blocks:
            L += [f"Until answered this blocks {TITLE[blocks]}.", ""]
    for wid, wname in WORKSTREAMS:
        L += [f"## Workstream: {wname}", ""]
        for t in TASKS:
            tid, slug, title, ws, status, prio, due, owner, deps, part_of, note = t
            if ws != wid:
                continue
            L += [f"### {title}", f"status: {status}", f"priority: {prio}"]
            if due:
                L.append(f"due: {due}")
            L.append(f"owned by: {TITLE[owner]}")
            if part_of:
                L.append(f"part of: {TITLE[part_of]}")
            L.append("")
            prose = note
            if deps:
                prose += f" Gated by {_dep_phrase(deps)}."
            L += [prose, ""]
    L += ["## People", ""]
    for pid, slug, name, role, team in AGENTS:
        L += [f"### {name}", f"role: {role}", f"team: {team}", ""]
    L += ["## Sources", ""]
    for sid, slug, title, origin in SOURCES:
        L += [f"### {title}", f"origin: {origin}", ""]
    return "\n".join(L)


# ----------------------------------------------------------------------------
# Questions: (query spec, mechanical extraction rule) -> ground truth
# ----------------------------------------------------------------------------

def q_node(nid):  # bounded fetch of one node
    return {"start": nid, "select": "contains", "bound": {"max_nodes": 1, "max_depth": 0}}


def q_walk(nid, select, direction="forward", depth=1, max_nodes=50):
    return {"start": nid, "select": select, "direction": direction,
            "bound": {"max_nodes": max_nodes, "max_depth": depth}}


def q_filter(flt):
    return {"select": "none", "filter": flt, "bound": {"max_nodes": 200}}


def extract(result: dict, rule: dict):
    """Mechanical, deterministic read of a query-result subgraph. No inference."""
    nodes = {n["id"]: n for n in result["nodes"]}
    edges = result["edges"]
    kind = rule["kind"]
    if kind == "prop":
        return nodes[rule["node"]]["props"][rule["key"]]
    if kind == "edge_target_titles":
        ids = [e["target"] for e in edges if e["type"] == rule["edge"] and e["source"] == rule["from"]]
        return sorted(nodes[i]["title"] for i in ids)
    if kind == "edge_source_titles":
        ids = [e["source"] for e in edges if e["type"] == rule["edge"] and e["target"] == rule["to"]]
        return sorted(nodes[i]["title"] for i in ids)
    if kind == "hop2_title":  # start -A-> mid -B-> answer
        mids = [e["target"] for e in edges if e["type"] == rule["edgeA"] and e["source"] == rule["from"]]
        out = [e["target"] for e in edges if e["type"] == rule["edgeB"] and e["source"] in mids]
        return sorted(nodes[i]["title"] for i in out)
    if kind == "closure_titles":  # all reached via edge from start (any depth in result)
        return sorted(nodes[i]["title"] for i in nodes if i != rule["from"])
    if kind == "count_nodes":
        return len(result["nodes"])
    if kind == "count_edges":
        return len([e for e in edges if e["type"] == rule["edge"]
                    and ("to" not in rule or e["target"] == rule["to"])])
    if kind == "count_children_of_type":
        return len([n for n in result["nodes"] if n["type"] == rule["type"]])
    raise ValueError(kind)


def build_questions():
    T = TITLE
    Q = []

    def add(qid, cls, text, spec, rule, atype, expected):
        Q.append({"id": qid, "class": cls, "question": text, "query": spec,
                  "extract": rule, "answer_type": atype, "_expected": expected})

    # --- 12 single-hop lookups ---
    add("L01", "lookup", f'What is the status of the task "{T["t2"]}"?',
        q_node("t2"), {"kind": "prop", "node": "t2", "key": "status"}, "scalar", "todo")
    add("L02", "lookup", f'What is the status of the task "{T["t12"]}"?',
        q_node("t12"), {"kind": "prop", "node": "t12", "key": "status"}, "scalar", "doing")
    add("L03", "lookup", f'What is the status of the task "{T["t17"]}"?',
        q_node("t17"), {"kind": "prop", "node": "t17", "key": "status"}, "scalar", "done")
    add("L04", "lookup", f'Who owns the task "{T["t5"]}"?',
        q_walk("t5", "owned-by"), {"kind": "edge_target_titles", "edge": "owned-by", "from": "t5"},
        "scalar", [T["p1"]])
    add("L05", "lookup", f'Who owns the task "{T["t10"]}"?',
        q_walk("t10", "owned-by"), {"kind": "edge_target_titles", "edge": "owned-by", "from": "t10"},
        "scalar", [T["p4"]])
    add("L06", "lookup", f'What is the due date of the task "{T["t13"]}"?',
        q_node("t13"), {"kind": "prop", "node": "t13", "key": "due"}, "date", "2026-08-01")
    add("L07", "lookup", f'What is the due date of the task "{T["t14"]}"?',
        q_node("t14"), {"kind": "prop", "node": "t14", "key": "due"}, "date", "2026-08-25")
    add("L08", "lookup", f'What is the priority of the task "{T["t11"]}"?',
        q_node("t11"), {"kind": "prop", "node": "t11", "key": "priority"}, "scalar", "low")
    add("L09", "lookup", f'What is the priority of the task "{T["t7"]}"?',
        q_node("t7"), {"kind": "prop", "node": "t7", "key": "priority"}, "scalar", "high")
    add("L10", "lookup", f'What is the status of the decision "{T["d3"]}"?',
        q_node("d3"), {"kind": "prop", "node": "d3", "key": "status"}, "scalar", "proposed")
    add("L11", "lookup", "What is Erin Fox's role?",
        q_node("p5"), {"kind": "prop", "node": "p5", "key": "role"}, "scalar", "security engineer")
    add("L12", "lookup", 'What is the target date of the goal "EU Launch"?',
        q_node("g1"), {"kind": "prop", "node": "g1", "key": "target"}, "date", "2026-09-15")

    # --- 12 multi-hop / relationship ---
    add("M01", "multihop", f'Which items does the task "{T["t3"]}" directly depend on?',
        q_walk("t3", "depends-on"), {"kind": "edge_target_titles", "edge": "depends-on", "from": "t3"},
        "list", sorted([T["t2"]]))
    add("M02", "multihop", f'Which items does the task "{T["t2"]}" directly depend on?',
        q_walk("t2", "depends-on"), {"kind": "edge_target_titles", "edge": "depends-on", "from": "t2"},
        "list", sorted([T["t1"], T["d2"]]))
    add("M03", "multihop", f'Who owns the task that "{T["t3"]}" directly depends on?',
        q_walk("t3", ["depends-on", "owned-by"], depth=2),
        {"kind": "hop2_title", "edgeA": "depends-on", "edgeB": "owned-by", "from": "t3"},
        "scalar", [T["p1"]])
    add("M04", "multihop", f'Who owns the task that "{T["t8"]}" directly depends on?',
        q_walk("t8", ["depends-on", "owned-by"], depth=2),
        {"kind": "hop2_title", "edgeA": "depends-on", "edgeB": "owned-by", "from": "t8"},
        "scalar", [T["p2"]])
    add("M05", "multihop",
        f'Which source does the decision that "{T["t13"]}" depends on cite?',
        q_walk("t13", ["depends-on", "cites"], depth=2),
        {"kind": "hop2_title", "edgeA": "depends-on", "edgeB": "cites", "from": "t13"},
        "scalar", [T["s3"]])
    add("M06", "multihop",
        f'Which source does the decision that "{T["t1"]}" depends on cite?',
        q_walk("t1", ["depends-on", "cites"], depth=2),
        {"kind": "hop2_title", "edgeA": "depends-on", "edgeB": "cites", "from": "t1"},
        "scalar", [T["s1"]])
    add("M07", "multihop", f'Which tasks directly depend on "{T["t7"]}"?',
        q_walk("t7", "depends-on", direction="backward"),
        {"kind": "edge_source_titles", "edge": "depends-on", "to": "t7"},
        "list", sorted([T["t8"], T["t11"]]))
    add("M08", "multihop", f'Which tasks directly depend on the decision "{T["d4"]}"?',
        q_walk("d4", "depends-on", direction="backward"),
        {"kind": "edge_source_titles", "edge": "depends-on", "to": "d4"},
        "list", sorted([T["t12"], T["t13"]]))
    add("M09", "multihop", f'Which task does the question "{T["q1"]}" block?',
        q_walk("q1", "blocks"), {"kind": "edge_target_titles", "edge": "blocks", "from": "q1"},
        "scalar", [T["t15"]])
    add("M10", "multihop", f'Who owns the task blocked by the question "{T["q2"]}"?',
        q_walk("q2", ["blocks", "owned-by"], depth=2),
        {"kind": "hop2_title", "edgeA": "blocks", "edgeB": "owned-by", "from": "q2"},
        "scalar", [T["p1"]])
    add("M11", "multihop",
        f'Which tasks must be completed before "{T["t10"]}", directly or through one intermediate dependency?',
        q_walk("t10", "depends-on", depth=3),
        {"kind": "closure_titles", "from": "t10"},
        "list", sorted([T["t8"], T["t7"]]))
    add("M12", "multihop", 'Which tasks are part of the goal "EU Launch"?',
        q_walk("g1", "part-of", direction="backward"),
        {"kind": "edge_source_titles", "edge": "part-of", "to": "g1"},
        "list", sorted([T["t13"], T["t14"], T["t15"], T["t18"]]))

    # --- 12 aggregate / count ---
    add("A01", "aggregate", 'How many tasks have status "todo"?',
        q_filter({"type": "task", "prop": [["status", "=", "todo"]]}),
        {"kind": "count_nodes"}, "count", 10)
    add("A02", "aggregate", 'How many tasks have status "done"?',
        q_filter({"type": "task", "prop": [["status", "=", "done"]]}),
        {"kind": "count_nodes"}, "count", 4)
    add("A03", "aggregate", 'How many tasks have priority "high"?',
        q_filter({"type": "task", "prop": [["priority", "=", "high"]]}),
        {"kind": "count_nodes"}, "count", 8)
    add("A04", "aggregate", "How many tasks does Alice Chen own?",
        q_walk("p1", "owned-by", direction="backward"),
        {"kind": "count_edges", "edge": "owned-by", "to": "p1"}, "count", 4)
    add("A05", "aggregate", "How many tasks does Dev Patel own?",
        q_walk("p4", "owned-by", direction="backward"),
        {"kind": "count_edges", "edge": "owned-by", "to": "p4"}, "count", 4)
    add("A06", "aggregate", 'How many decisions have status "accepted"?',
        q_filter({"type": "decision", "prop": [["status", "=", "accepted"]]}),
        {"kind": "count_nodes"}, "count", 3)
    add("A07", "aggregate", 'How many questions have status "open"?',
        q_filter({"type": "question", "prop": [["status", "=", "open"]]}),
        {"kind": "count_nodes"}, "count", 3)
    add("A08", "aggregate", "How many tasks does the Billing workstream contain?",
        {"start": "ws1", "select": "contains", "filter": {"type": "task"},
         "bound": {"max_nodes": 50, "max_depth": 1}},
        {"kind": "count_children_of_type", "type": "task"}, "count", 7)
    add("A09", "aggregate", 'How many tasks are part of the goal "EU Launch"?',
        q_walk("g1", "part-of", direction="backward"),
        {"kind": "count_edges", "edge": "part-of", "to": "g1"}, "count", 4)
    add("A10", "aggregate", f'How many tasks directly depend on the decision "{T["d4"]}"?',
        q_walk("d4", "depends-on", direction="backward"),
        {"kind": "count_edges", "edge": "depends-on", "to": "d4"}, "count", 2)
    add("A11", "aggregate", "How many people (agents) are in the knowledge base?",
        q_filter({"type": "agent"}), {"kind": "count_nodes"}, "count", 5)
    add("A12", "aggregate", "How many sources are in the knowledge base?",
        q_filter({"type": "source"}), {"kind": "count_nodes"}, "count", 3)
    return Q


# ----------------------------------------------------------------------------
# Build + verify (correct by construction, cross-checked)
# ----------------------------------------------------------------------------

def main():
    kb_sarib, kb_md, kb_notypes = emit_sarib(), emit_md(), emit_notypes()
    doc = parse(kb_sarib)
    hard = [d for d in doc.diagnostics if "unresolved" in d or "ambiguous" in d or "invariant" in d]
    if hard:
        sys.exit("ABORT — kb.sarib has reference/invariant problems:\n" + "\n".join(hard))

    questions, failures = [], []
    for q in build_questions():
        result = run_query(doc, q["query"])
        derived = extract(result, q["extract"])
        if isinstance(derived, list) and q["answer_type"] == "scalar":
            if len(derived) != 1:
                failures.append(f'{q["id"]}: scalar extraction returned {derived}')
                continue
            derived = derived[0]
        expected = q.pop("_expected")
        if q["answer_type"] == "scalar" and isinstance(expected, list):
            expected = expected[0]
        if isinstance(derived, list):
            derived = sorted(str(x) for x in derived)
            expected = sorted(str(x) for x in expected)
        if str(derived) != str(expected) and derived != expected:
            failures.append(f'{q["id"]}: query-derived {derived!r} != fact-table {expected!r}')
            continue
        q["answer"] = derived
        questions.append(q)

    if failures:
        sys.exit("ABORT — ground-truth cross-check failed:\n" + "\n".join(failures))
    classes = {c: sum(1 for q in questions if q["class"] == c) for c in ("lookup", "multihop", "aggregate")}
    assert classes == {"lookup": 12, "multihop": 12, "aggregate": 12}, classes

    (OUT / "kb.sarib").write_text(kb_sarib, encoding="utf-8", newline="\n")
    (OUT / "kb.md").write_text(kb_md, encoding="utf-8", newline="\n")
    (OUT / "kb.notypes.sarib").write_text(kb_notypes, encoding="utf-8", newline="\n")
    (OUT / "questions.json").write_text(
        json.dumps(questions, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")

    # token accounting (o200k_base; per-run input tokens use the provider-reported count)
    try:
        import tiktoken
        enc = tiktoken.get_encoding("o200k_base")
        tok = lambda s: len(enc.encode(s))
    except Exception:
        tok = lambda s: max(1, len(s) // 4)
    typed = [n for n in doc.nodes.values() if n.type]
    print(f"kb.sarib      : {tok(kb_sarib):5d} tokens (o200k) | {len(doc.nodes)} nodes "
          f"({len(typed)} typed), {len(doc.edges)} edges, {len(doc.diagnostics)} diagnostics")
    print(f"kb.md         : {tok(kb_md):5d} tokens")
    print(f"kb.notypes    : {tok(kb_notypes):5d} tokens")
    print(f"questions     : {len(questions)} (12 lookup / 12 multihop / 12 aggregate), "
          f"ground truth query-derived + cross-checked OK")
    for kb, name in ((kb_sarib, "kb.sarib"), (kb_md, "kb.md"), (kb_notypes, "kb.notypes")):
        if tok(kb) > 6000:
            sys.exit(f"ABORT — {name} exceeds the 6000-token budget")
    print("token budget  : all corpora under 6000 tokens — fits Cerebras 8k context")


if __name__ == "__main__":
    main()

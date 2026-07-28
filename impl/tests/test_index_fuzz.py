"""A stale derived index corrupts query results -- and query results are the SOLE
addressing mechanism for edits (D-033), so a stale index makes an agent edit the
wrong node. This is risk D2 in plans/01-scale-remediation.md and the #1 bug risk
of the whole remediation.

`Doc` caches kids/slugs/out/in and writers must call `doc.touch()`. There is no
single mutation chokepoint (parser.py, ops.py and importer.py all write directly),
so review cannot be the control. This is: fuzz random op sequences, and after every
accepted op assert that the CACHED index equals a from-scratch rebuild, and that
canon/walk are identical either way.

This test caught nothing on the final code; it caught the real bug during the work
(ops.py mutating without touch() left create-node invisible to canon).

Run: python impl/tests/test_index_fuzz.py [--ops N] [--seeds N] [--verbose]
"""
from __future__ import annotations

import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from sarib import canon, fmt, parse                      # noqa: E402
from sarib.ops import OpRejected, apply as apply_op       # noqa: E402
from sarib.render import outline                          # noqa: E402

BASE = """---
sarib: 0.1
title: Fuzz base
---

# Root {#root}

## Alpha {.section} ^a1
status:: todo

Prose under alpha referring to [[Beta]].

### Task one {.task} ^t1
status:: todo
due:: 2026-01-01

### Task two {.task} ^t2
status:: done

## Beta {.section} ^b1

- item one {.task}
- item two

### Task three {.task} ^t3
status:: todo
"""

# Weighted: retract-node and merge each remove an active node, so an even mix drains
# the document within ~30 ops and the rest of the run tests nothing. Structural ops
# (create/move/add-edge) are the ones that can actually invalidate the index, so they
# get the weight; the destructive pair stays represented but rare.
KINDS = (["create-node"] * 4 + ["add-edge"] * 3 + ["move"] * 3 + ["set-property"] * 2
         + ["tag"] * 2 + ["set-content"] + ["unset-property"] + ["retract-edge"]
         + ["retract-node"] + ["merge"])


def snapshot(doc) -> dict:
    """The index as plain comparable data (node objects -> ids)."""
    i = doc._index()
    return {
        "kids": {str(k): [n.id for n in v] for k, v in i["kids"].items()},
        "slugs": dict(i["slugs"]),
        "out": {k: list(v) for k, v in i["out"].items()},
        "in": {k: list(v) for k, v in i["in"].items()},
    }


def random_op(rng, doc, step):
    nids = [n for n, v in doc.nodes.items() if v.status == "active"]
    eids = list(doc.edges)
    if not nids:
        return None
    kind = rng.choice(KINDS)
    t = rng.choice(nids)
    if kind == "create-node":
        return {"kind": kind, "args": {"id": f"f{step}", "title": f"Fuzz {step}",
                                       "type": rng.choice(["task", "note", None]),
                                       "parent": rng.choice(nids + [None]),
                                       "props": {"status": rng.choice(["todo", "done"])}}}
    if kind == "add-edge":
        return {"kind": kind, "args": {"id": f"fe{step}",
                                       "type": rng.choice(["depends-on", "relates-to", "tag"]),
                                       "source": t, "target": rng.choice(nids)}}
    if kind == "retract-edge":
        return {"kind": kind, "target": rng.choice(eids)} if eids else None
    if kind == "move":
        return {"kind": kind, "target": t, "args": {"parent": rng.choice(nids)}}
    if kind == "merge":
        return {"kind": kind, "target": t, "args": {"into": rng.choice(nids)}}
    if kind == "tag":
        return {"kind": kind, "target": t, "args": {"concept": rng.choice(nids)}}
    if kind == "set-content":
        return {"kind": kind, "target": t, "args": {"content": f"body {step}"}}
    if kind == "set-property":
        return {"kind": kind, "target": t,
                "args": {"key": rng.choice(["status", "due", "priority"]),
                         "value": rng.choice(["todo", "done", "high"])}}
    if kind == "unset-property":
        return {"kind": kind, "target": t, "args": {"key": rng.choice(["status", "due"])}}
    return {"kind": kind, "target": t}


def run_seed(seed: int, n_ops: int, verbose: bool):
    rng = random.Random(seed)
    doc = parse(BASE)
    applied = rejected = resets = 0
    for step in range(n_ops):
        if sum(1 for v in doc.nodes.values() if v.status == "active") < 5:
            doc = parse(BASE)          # refill: retractions eventually empty the doc
            resets += 1
        op = random_op(rng, doc, step)
        if op is None:
            continue
        try:
            apply_op(doc, op)
            applied += 1
        except (OpRejected, KeyError, TypeError):
            rejected += 1
            continue

        # what a reader sees through the CACHED index...
        cached_idx = snapshot(doc)
        cached_canon = canon(doc)
        cached_walk = [n.id for n in doc.walk(None)]
        cached_fmt = fmt(doc)
        cached_outline = outline(doc)
        # ...must equal a from-scratch rebuild
        doc.touch()
        fresh_idx = snapshot(doc)
        if cached_idx != fresh_idx:
            where = [k for k in fresh_idx if cached_idx[k] != fresh_idx[k]]
            return (f"seed {seed} step {step}: STALE INDEX after {op['kind']} "
                    f"-> diverged in {where}", applied, rejected, resets)
        for what, before, after in (("canon", cached_canon, canon(doc)),
                                    ("walk", cached_walk, [n.id for n in doc.walk(None)]),
                                    ("fmt", cached_fmt, fmt(doc)),
                                    ("outline", cached_outline, outline(doc))):
            if before != after:
                return (f"seed {seed} step {step}: {what} differs after {op['kind']}",
                        applied, rejected, resets)

        if verbose and step % 100 == 0:
            print(f"    seed {seed} step {step}: {len(doc.nodes)} nodes, {len(doc.edges)} edges")
    return None, applied, rejected, resets


def main() -> int:
    n_ops = int(sys.argv[sys.argv.index("--ops") + 1]) if "--ops" in sys.argv else 250
    seeds = int(sys.argv[sys.argv.index("--seeds") + 1]) if "--seeds" in sys.argv else 8
    verbose = "--verbose" in sys.argv
    total_applied = total_rejected = 0
    print(f"index-coherence fuzz: {seeds} seeds x {n_ops} ops")
    for seed in range(seeds):
        err, applied, rejected, resets = run_seed(seed, n_ops, verbose)
        total_applied += applied
        total_rejected += rejected
        if err:
            print(f"  FAIL {err}")
            print("\nINDEX INCOHERENT — a writer mutated the model without doc.touch()")
            return 1
        print(f"  ok   seed {seed}: {applied} ops applied, {rejected} rejected,"
              f" {resets} refills")
    print(f"\nINDEX COHERENT — {total_applied} ops applied "
          f"({total_rejected} rejected), zero divergence")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())

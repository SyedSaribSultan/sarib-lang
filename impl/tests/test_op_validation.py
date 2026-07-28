"""Op-time validation is scoped to what an op touched (D-065).

The bug this fixes: validation used to run over the WHOLE document after every op and
reject if it found anything. So a file that already carried an unrelated violation — two
headings sharing one `{#slug}` is enough, and that is hand-authorable — rejected *every*
operation, including the one that would repair it. An author could be locked out of their
own file with no way back except a text editor.

This test pins both halves: the pre-existing violation no longer blocks edits, and every
guard that should still reject still rejects.

Run: python impl/tests/test_op_validation.py
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from sarib import parse                                   # noqa: E402
from sarib.model import Doc, Node                          # noqa: E402
from sarib.ops import OpRejected, apply as apply_op        # noqa: E402

# Two headings claim the same slug. Legal to type, caught by validation, and previously
# fatal to every subsequent edit.
BROKEN = """---
sarib: 0.1
---

# Root {#root} ^rt

## First {.task #dup} ^a1
status:: todo

## Second {.task #dup} ^a2
status:: todo
"""

fails = 0


def check(name, cond, detail=""):
    global fails
    print(f"  {'ok  ' if cond else 'FAIL'} {name}{'' if cond else '  <- ' + str(detail)}")
    if not cond:
        fails += 1


def main() -> int:
    print("a pre-existing violation must not block edits (F2)")
    doc = parse(BROKEN)
    diags = doc.check_invariants()
    check("the document really is invalid to begin with",
          any(d.startswith("duplicate-slug") for d in diags), diags)

    # the edit that has nothing to do with the problem
    try:
        apply_op(doc, {"kind": "set-property", "target": "a1",
                       "args": {"key": "status", "value": "done"}})
        check("an unrelated edit is accepted", True)
    except OpRejected as e:
        check("an unrelated edit is accepted", False, e)

    # the edit that REPAIRS the problem must also be possible
    try:
        apply_op(doc, {"kind": "retract-node", "target": "a2"})
        check("the repairing edit is accepted", True)
    except OpRejected as e:
        check("the repairing edit is accepted", False, e)

    check("full validation still reports the violation while it stands",
          any(d.startswith("duplicate-slug") for d in parse(BROKEN).check_invariants()))

    print("\nevery guard that should still reject, still rejects")
    cases = [
        ("duplicate id", {"kind": "create-node", "args": {"id": "a1", "title": "x"}}, "exists"),
        ("missing parent", {"kind": "create-node",
                            "args": {"id": "zz", "parent": "nope"}}, "missing"),
        ("dangling edge endpoint", {"kind": "add-edge",
                                    "args": {"type": "x", "source": "a1", "target": "nope"}},
         "missing"),
        ("containment edited via add-edge", {"kind": "add-edge",
                                             "args": {"type": "x", "source": "a1",
                                                      "target": "rt",
                                                      "family": "containment"}}, "containment"),
        ("move to a missing parent", {"kind": "move", "target": "a1",
                                      "args": {"parent": "nope"}}, "missing"),
        ("move that would cycle", {"kind": "move", "target": "rt",
                                   "args": {"parent": "a1"}}, "cycle"),
        ("merge into a node that does not exist", {"kind": "merge", "target": "a1",
                                                   "args": {"into": "nope"}}, "missing"),
        ("unknown op kind", {"kind": "not-an-op", "target": "a1"}, "unknown"),
        ("stale expect precondition", {"kind": "set-property", "target": "a1",
                                       "args": {"key": "status", "value": "x"},
                                       "expect": {"a1": {"version": 99}}}, "expect"),
    ]
    for name, op, needle in cases:
        d = parse(BROKEN)
        try:
            apply_op(d, op)
            check(name, False, "ACCEPTED — should have been rejected")
        except OpRejected as e:
            check(name, needle in str(e), f"rejected but message lacked '{needle}': {e}")

    print("\nthe local check still detects what it is responsible for")
    d = Doc()
    d.nodes["x"] = Node(id="x", kind_hint="heading", title="X", parent="ghost")
    d.touch()
    check("missing parent is caught",
          any("missing parent" in m for m in d.check_touched(["x"])), d.check_touched(["x"]))
    d2 = Doc()
    d2.nodes["p"] = Node(id="p", kind_hint="heading", title="P", parent="q")
    d2.nodes["q"] = Node(id="q", kind_hint="heading", title="Q", parent="p")
    d2.touch()
    check("a containment cycle is caught",
          any("cycle" in m for m in d2.check_touched(["p"])), d2.check_touched(["p"]))
    check("a healthy node reports nothing", parse(BROKEN).check_touched(["a1", "rt"]) == [])

    print(f"\n{'OP-VALIDATION OK' if fails == 0 else f'{fails} FAILURES'}")
    return 1 if fails else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())

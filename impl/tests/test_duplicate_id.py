"""A repeated ^id must never delete a node (invariant 1, D-066).

The bug: `Doc.nodes` is keyed by id, so the parser's second `^t1` overwrote the first.
`validate` said "OK, 2 nodes" with no diagnostic; `canon`/`fmt` silently lost the first
block, its status and its owner edge; `sarib set dup.sarib t1 status=done` then wrote the
loss back to disk and exited 0. This pins the exact repro from the 2026-10-15 audit:

  * both blocks survive parse, canon and fmt (the later one is model id `t1~2`, and fmt
    writes its AUTHORED `^t1` back, so the duplicate stays visible instead of renamed);
  * a located `duplicate-id` diagnostic is reported;
  * an op addressing the ambiguous id is rejected ("ambiguous id"), wherever it appears
    (target, endpoint, expect);
  * `sarib set` / `sarib apply --write` refuse to write the file (exit 1, file untouched)
    unless --force, and MCP `sarib_apply` refuses with no override;
  * with --force, the unambiguous `t1~2` is editable and both blocks are still on disk.

Run: python impl/tests/test_duplicate_id.py
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile

IMPL = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IMPL))

from sarib import canon, fmt, parse                      # noqa: E402
from sarib.ops import OpRejected, apply as apply_op      # noqa: E402

REPRO = """# Q3

## Migrate invoices {.task} ^t1
status:: todo
owner:: [[Alice]]

## Adopt Stripe {.decision} ^t1
status:: accepted

## Alice ^alice
"""

fails = 0


def check(name, cond, detail=""):
    global fails
    print(f"  {'ok  ' if cond else 'FAIL'} {name}{'' if cond else '  <- ' + str(detail)}")
    if not cond:
        fails += 1


def rejected(doc, op) -> str:
    try:
        apply_op(doc, op)
    except OpRejected as e:
        return str(e)
    return ""


def cli(*args) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONPATH=str(IMPL), NO_COLOR="1")
    return subprocess.run([sys.executable, "-m", "sarib.cli", *args], capture_output=True,
                          text=True, encoding="utf-8", env=env)


def main() -> int:
    print("the model keeps both blocks")
    doc = parse(REPRO)
    check("both nodes present", {"t1", "t1~2"} <= set(doc.nodes), list(doc.nodes))
    check("first block keeps its status", doc.nodes["t1"].properties.get("status") == "todo")
    check("first block keeps its owner edge",
          any(e.source == "t1" and e.type == "owner" for e in doc.edges.values()))
    dup = [d for d in doc.diagnostics if d.startswith("duplicate-id")]
    check("one located duplicate-id diagnostic",
          dup == ["duplicate-id: ^t1 at line 7 is already node t1 (line 3); kept as t1~2"], dup)
    check("ambiguous_ids names both", doc.ambiguous_ids() == {"t1": ["t1", "t1~2"]})

    print("canon and fmt are lossless")
    c = canon(doc)
    check("canon carries both", '"id":"t1"' in c and '"id":"t1~2"' in c)
    out = fmt(doc)
    check("fmt writes ^t1 on both blocks", out.count("^t1") == 2, out)
    check("round-trip: canon(parse(fmt)) == canon", canon(parse(out)) == c)
    check("fmt idempotent", fmt(parse(out)) == out)

    print("ops refuse the ambiguous id")
    for name, op in [
        ("target", {"kind": "set-property", "target": "t1", "args": {"key": "k", "value": "v"}}),
        ("edge endpoint", {"kind": "add-edge", "args": {"type": "x", "source": "alice", "target": "t1"}}),
        ("expect", {"kind": "set-property", "target": "alice", "args": {"key": "k", "value": "v"},
                    "expect": {"t1": {"version": 0}}}),
        ("create-node parent", {"kind": "create-node", "args": {"id": "z", "parent": "t1"}}),
    ]:
        msg = rejected(parse(REPRO), op)
        check(f"{name}: rejected as ambiguous", msg.startswith("ambiguous id t1"), msg or "applied")
    d2 = parse(REPRO)
    check("the kept copy is addressable as t1~2",
          rejected(d2, {"kind": "set-property", "target": "t1~2",
                        "args": {"key": "status", "value": "done"}}) == ""
          and d2.nodes["t1"].properties["status"] == "todo")

    print("CLI refuses to write (the audit repro)")
    with tempfile.TemporaryDirectory() as td:
        f = pathlib.Path(td) / "dup.sarib"
        f.write_text(REPRO, encoding="utf-8")
        r = cli("set", str(f), "t1", "status=done")
        check("set exits 1", r.returncode == 1, r.stdout + r.stderr)
        check("set says REFUSED", "REFUSED" in r.stdout, r.stdout)
        check("file untouched", f.read_text(encoding="utf-8") == REPRO)
        r = cli("apply", str(f), "--write", "--op",
                '{"kind":"set-property","target":"alice","args":{"key":"k","value":"v"}}')
        check("apply --write refuses too", r.returncode == 1 and "REFUSED" in r.stdout, r.stdout)
        check("file still untouched", f.read_text(encoding="utf-8") == REPRO)
        r = cli("set", str(f), "t1", "status=done", "--dry-run")
        check("dry-run still rejects the ambiguous id",
              r.returncode == 1 and "ambiguous id t1" in r.stdout, r.stdout)
        r = cli("set", str(f), "t1~2", "status=done", "--force")
        check("--force edits the unambiguous copy", r.returncode == 0, r.stdout + r.stderr)
        after = parse(f.read_text(encoding="utf-8"))
        check("both blocks still on disk after --force",
              after.nodes["t1"].properties.get("status") == "todo"
              and after.nodes["t1~2"].properties.get("status") == "done"
              and after.nodes["t1~2"].title == "Adopt Stripe")
        check("and still reported", any(d.startswith("duplicate-id") for d in after.diagnostics))

    print("MCP sarib_apply refuses")
    try:
        import mcp.server.fastmcp  # noqa: F401
    except Exception as e:                                           # noqa: BLE001
        print(f"  skip (mcp SDK unavailable: {e.__class__.__name__}; pip install 'sarib[mcp]')")
    else:
        with tempfile.TemporaryDirectory() as td:
            (pathlib.Path(td) / "dup.sarib").write_text(REPRO, encoding="utf-8")
            argv, sys.argv = sys.argv, ["sarib-mcp", td]
            try:
                sys.modules.pop("sarib.mcp_server", None)
                from sarib import mcp_server
            finally:
                sys.argv = argv
            res = mcp_server.sarib_apply(
                "dup.sarib", '{"kind":"set-property","target":"alice","args":{"key":"k","value":"v"}}')
            check("sarib_apply returns REFUSED", res.startswith("REFUSED"), res)
            check("file untouched",
                  (pathlib.Path(td) / "dup.sarib").read_text(encoding="utf-8") == REPRO)

    print(f"\n{'DUPLICATE-ID OK' if not fails else f'{fails} FAILURES'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

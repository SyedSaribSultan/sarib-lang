"""MCP path-containment tests. The MCP server hands an AI agent read AND write access
(`sarib_apply` writes) over a folder, and its `file` argument is untrusted — it can carry
prompt-injected content. These cases pin the escapes that a previous implementation allowed:

  1. `assert` for the check      -> stripped by `python -O`, leaving NO check at all
  2. `str(p).startswith(ROOT)`   -> string prefix, so sibling dir `notes-secret` passed
  3. `ROOT / file` with absolute -> pathlib silently discards ROOT
  4. symlink inside the folder pointing out
  5. `..` traversal

Run:  python impl/tests/test_mcp_containment.py          (must pass)
      python -O impl/tests/test_mcp_containment.py       (must ALSO pass — the -O regression)
"""
from __future__ import annotations
import pathlib, sys, tempfile

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))


def build_fixture():
    base = pathlib.Path(tempfile.mkdtemp())
    notes = base / "notes"; notes.mkdir()
    sibling = base / "notes-secret"; sibling.mkdir()      # shares the ROOT name prefix
    (notes / "ok.sarib").write_text("# Fine\n\n## A task {.task} ^t1\nstatus:: todo\n", encoding="utf-8")
    (sibling / "private.sarib").write_text("# CONFIDENTIAL\n", encoding="utf-8")
    (base / "outside.sarib").write_text("# OUTSIDE\n", encoding="utf-8")
    return base, notes, sibling


def main():
    base, notes, sibling = build_fixture()
    sys.argv = ["sarib-mcp", str(notes)]                 # ROOT is read from argv at import
    try:
        import sarib.mcp_server as srv
    except ImportError as e:                             # mcp extra not installed
        print(f"SKIP: {e} (pip install 'sarib[mcp]' to run these)")
        return 0

    attacks = [
        ("parent traversal", "../outside.sarib"),
        ("sibling prefix bypass", "../notes-secret/private.sarib"),
        ("absolute path (posix)", "/etc/passwd"),
        ("absolute path (windows)", "C:/Windows/System32/drivers/etc/hosts"),
        ("absolute into sibling", str(sibling / "private.sarib")),
        ("nested traversal", "sub/../../notes-secret/private.sarib"),
        ("non-sarib file", "../../.env"),
    ]
    # symlink escape (skipped where unprivileged symlinks are unavailable, e.g. plain Windows)
    try:
        (notes / "link.sarib").symlink_to(sibling / "private.sarib")
        attacks.append(("symlink escape", "link.sarib"))
    except (OSError, NotImplementedError):
        pass

    failures = []
    for name, path in attacks:
        try:
            srv._resolve(path)
            failures.append(f"NOT BLOCKED: {name} -> {path!r}")
        except srv.Denied:
            print(f"  blocked: {name}")
        except Exception as e:                           # any other error is also a bug
            failures.append(f"WRONG ERROR for {name} ({path!r}): {e.__class__.__name__}: {e}")

    # the legitimate path must still work, and the tools must return a readable denial
    try:
        p = srv._resolve("ok.sarib")
        assert p == (notes / "ok.sarib").resolve(), p
        print("  allowed: ok.sarib (legitimate access still works)")
    except Exception as e:
        failures.append(f"legitimate access broke: {e.__class__.__name__}: {e}")

    out = srv.sarib_validate("../notes-secret/private.sarib")
    if not str(out).startswith("DENIED:"):
        failures.append(f"tool did not return a clean denial: {out!r}")
    else:
        print("  tool surface returns a clean 'DENIED:' string, not a crash")

    # sarib_apply must not create or modify anything outside ROOT
    before = (sibling / "private.sarib").read_text(encoding="utf-8")
    srv.sarib_apply("../notes-secret/private.sarib",
                    '{"kind":"set-property","target":"t1","args":{"key":"x","value":"y"}}')
    if (sibling / "private.sarib").read_text(encoding="utf-8") != before:
        failures.append("sarib_apply WROTE outside the managed folder")
    else:
        print("  sarib_apply cannot write outside the managed folder")

    mode = "python -O" if not __debug__ else "python"
    if failures:
        print(f"\nFAIL ({mode}):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"\nCONTAINED ({mode}): {len(attacks)} escape attempts blocked, legitimate access intact")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())

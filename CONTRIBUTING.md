# Contributing to .sarib

Thanks for your interest — contributions are welcome. `.sarib` is an open standard
led by its author (see `GOVERNANCE.md`); these rules keep contribution open while
the project stays coherent and well-owned.

## Ground rules

- The project is led by **[@SyedSaribSultan](https://github.com/SyedSaribSultan)**,
  who has final say on direction and merges.
- **All changes land via pull request** and require maintainer review. Direct pushes
  to `main` are disabled.
- Be respectful — see `CODE_OF_CONDUCT.md`.

## How to contribute

1. **Open an issue first** for anything non-trivial, so we agree on the approach
   before you build.
2. Fork the repo, branch, make your change.
3. Respect the design constraints: the reference parser stays within its
   ≤~1000-LOC budget (see `stages/13`); new capability usually belongs in
   *vocabulary/tooling*, not the core (the "keep the core small" rule).
4. Keep the conformance corpus green: `cd impl && python tests/run_corpus.py`.
5. Open a PR against `main` and fill in the template.

## Sign your commits (DCO) — required

Every commit must be **signed off** using the Developer Certificate of Origin
(<https://developercertificate.org>). It's a lightweight promise that you wrote the
code (or have the right to submit it) and agree to contribute it under the project's
licenses. It is **not** a copyright transfer — you keep authorship of your work.

```bash
git commit -s -m "your message"     # adds a "Signed-off-by:" line
```

Pull requests whose commits are not signed off cannot be merged. (Tip:
`git config format.signOff true` makes it automatic. Note that the pre-v0.1
history predates this requirement, so early commits are unsigned; the rule
applies from here forward.)

## Licensing of contributions

By contributing, you agree your contribution is provided under the project's
licenses: **MIT** for code (`LICENSE`) and **CC-BY-4.0** for the specification/prose
(`LICENSE-SPEC`). You retain copyright to your contribution; it is licensed, not
assigned.

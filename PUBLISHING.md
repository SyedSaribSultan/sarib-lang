# Publishing checklist — sarib-lang

**PUBLISHED 2026-07-20:** https://github.com/SyedSaribSultan/sarib-lang — steps 1–4 done (repo, push, description, topics) plus the v0.1 Release. Remaining from step 5 (optional): pinned G2/G3 issue, MCP community listing, announcement post. The checklist below is kept for provenance.

**LATEST: 0.1.4 / extension 0.3.0 shipped 2026-07-26** — `sarib` 0.1.4 on PyPI, `vscode-sarib-0.3.0.vsix` on the [v0.1.4 Release](https://github.com/SyedSaribSultan/sarib-lang/releases/tag/v0.1.4). Preview now works in any folder. The stale `vscode-sarib-0.2.0.vsix` asset was deleted from the v0.1 Release (its body points forward); the file is still in `editors/vscode-sarib/` locally and rebuildable from the `v0.1` tag.

1. **Create the repo:** github.com → New → `sarib-lang` (public). No template, no auto-README.
2. **Swap the front door:** rename `README.md` → `HISTORY.md` (the session log is valuable — keep it), then `README-public.md` → `README.md`.
3. **Push** from `C:\Users\sarib\Downloads\name.sarib`:
   ```bash
   git init && git add -A
   git commit -m "sarib v0.1 — spec + reference implementation + gates"
   git branch -M main
   git remote add origin https://github.com/<you>/sarib-lang.git
   git push -u origin main
   ```
4. **Repo settings:** description: *"AI-native knowledge language: Markdown-superset surface, property-graph model, atomic id-addressed edits. Spec + ~700-LOC reference impl + benchmarks."* Topics: `knowledge-representation`, `markdown`, `llm`, `agents`, `mcp`, `file-format`, `crdt`.
5. **Post-publish (optional, high-leverage):** create a Release (tag `v0.1`) and attach `editors/vscode-sarib/vscode-sarib-0.2.0.vsix` as an asset so non-Node users can install the editor extension (it's gitignored, so Releases is its only distribution); pin an issue "Run the G2/G3 protocols" inviting benchmark contributions; add the MCP config snippet to the MCP servers community list; a short Show-HN/X post linking the README's measured numbers.

Pre-flight already done: licenses (MIT + CC-BY-4.0), .gitignore, conformance corpus green, gate report committed, no secrets in tree.

## Release runbook — how 0.1.4 shipped (repeat this for the next one)

1. **Commit + tag:** `git tag -a v0.1.X -m "…" && git push origin main --tags`. The tag alone
   publishes nothing — `release.yml` fires on *release published* (or manual dispatch), not on tags.
2. **Build the `.vsix`** if the extension changed: `cd editors/vscode-sarib && npx @vscode/vsce package`.
   It is gitignored, so a Release asset is its only distribution channel.
3. **Publish.** Creating the Release triggers `release.yml` → builds `impl/` → PyPI via Trusted
   Publishing (OIDC, environment `pypi`, no stored token):
   ```bash
   gh release create v0.1.X --title "…" --notes-file notes.md editors/vscode-sarib/vscode-sarib-0.Y.0.vsix
   ```
   **One line, no `\` continuation** — in PowerShell a backslash is an argument, not a line break,
   so `gh` reads it as an asset path, drops into a prompt, and fails the upload (which rolls the
   whole release back). Use a backtick to continue a line, or don't wrap at all.
4. **Verify, don't assume:** `gh run view <id>` conclusion is `success`; PyPI's own API agrees
   (`urllib.request.urlopen('https://pypi.org/pypi/sarib/json')` → `info.version`; `pip index
   versions` reads a cached index and lags); then in a **clean venv**, `pip install "sarib>=0.1.X"`
   and `python -m sarib.preview <f>.sarib --stdout` from a directory that is not a checkout.
5. **Retire superseded assets** so README readers can't install a broken build: delete the old
   `.vsix` from the previous Release and point its body at the new one.

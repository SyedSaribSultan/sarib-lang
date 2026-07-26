# Publishing checklist — sarib-lang

**PUBLISHED 2026-07-20:** https://github.com/SyedSaribSultan/sarib-lang — steps 1–4 done (repo, push, description, topics) plus the v0.1 Release with `vscode-sarib-0.2.0.vsix` attached. Remaining from step 5 (optional): pinned G2/G3 issue, MCP community listing, announcement post. The checklist below is kept for provenance.

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

## Pending release — 0.1.4 / extension 0.3.0 (needed before anyone else gets working preview)

The previewer moved into the package (`sarib.preview`) so preview works in any folder. Both halves
of that fix are only in this working tree; PyPI still serves **0.1.3** (no `sarib.preview`) and the
GitHub Release still carries **`vscode-sarib-0.2.0.vsix`** (old, workspace-scanning resolver). Until
both are republished, a new user who follows the README gets the old broken behavior — the extension
detects that exact case and tells them to upgrade, but it cannot fix it for them.

1. ~~**Commit + tag**~~ — done: `02ea8f9` on `main`, tag `v0.1.4` pushed. The tag alone publishes
   nothing: `release.yml` fires on *release published* (or manual dispatch), not on tags.
2. ~~**Build the `.vsix`**~~ — done: `editors/vscode-sarib/vscode-sarib-0.3.0.vsix` (gitignored, so
   a Release asset is its only distribution channel), installed locally as `sarib.vscode-sarib@0.3.0`.
3. **Publish — the one step left.** Creates the Release, which triggers `release.yml` → builds
   `impl/` → PyPI via Trusted Publishing (OIDC, environment `pypi`, no stored token):
   ```bash
   gh release create v0.1.4 --title "sarib 0.1.4 — preview in any folder" \
     --notes-file <notes.md> editors/vscode-sarib/vscode-sarib-0.3.0.vsix
   ```
   Notes to use: preview runs from any folder via the installed package (`pip install "sarib>=0.1.4"`
   — no checkout, no `sarib.previewScript`); extension 0.3.0 resolves setting → checkout above the
   open file → workspace folder → installed package.
4. **Verify, don't assume:** `gh run list` shows the `release` workflow green; `pip index versions
   sarib` lists 0.1.4; in a clean venv `pip install "sarib>=0.1.4"` then
   `python -m sarib.preview <f>.sarib --stdout` prints HTML from a directory that is not a checkout.
5. **Supersede the stale asset:** the `v0.1` Release still carries `vscode-sarib-0.2.0.vsix`, whose
   resolver only scans workspace folders. Delete it or note in that release's body that 0.3.0 on
   `v0.1.4` replaces it — otherwise README readers can still install the broken one.

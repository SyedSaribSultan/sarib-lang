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

1. **Commit + tag:** `git tag v0.1.4 && git push origin main --tags`.
2. **Publish the package:** create a GitHub Release for `v0.1.4` → `release.yml` builds `impl/` and
   publishes to PyPI via Trusted Publishing (OIDC, environment `pypi`, no stored token). Verify:
   `pip index versions sarib` shows 0.1.4, and in a clean venv
   `pip install sarib && python -m sarib.preview <f>.sarib --stdout` prints HTML.
3. **Attach the extension:** `cd editors/vscode-sarib && npx @vscode/vsce package`, then attach
   `vscode-sarib-0.3.0.vsix` to that same Release (the `.vsix` is gitignored — Releases is its only
   distribution channel). Remove or clearly supersede the 0.2.0 asset so nobody installs it.
4. **Release notes, one line each:** preview runs from any folder via the installed package
   (`pip install sarib`, no checkout, no `sarib.previewScript`); extension 0.3.0 resolves
   setting → checkout above the file → workspace folder → installed package.

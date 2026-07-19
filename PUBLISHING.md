# Publishing checklist — sarib-lang

Everything is staged locally (steps 2–3 through the commit are done — repo initialized on `main`, first commit made). What remains yours: create the GitHub repo (step 1), add the remote and push (end of step 3), settings (step 4).

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

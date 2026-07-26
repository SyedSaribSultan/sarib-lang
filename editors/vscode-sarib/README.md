# sarib — VS Code extension (v0.3)

Syntax highlighting **and live preview** for `.sarib` knowledge files. A `.sarib` file is a Markdown
superset, so this extension colors normal Markdown (via VS Code's built-in grammar)
**plus** the sarib-specific marks:

| Mark | Meaning | Example |
|---|---|---|
| `{.type #slug}` | node type + slug | `## Migrate invoices {.task #migrate}` |
| `key:: value` | a property (fact) | `status:: todo` |
| `[[Target]]` | a plain reference (edge) | `owner:: [[Alice]]` |
| `[rel:: [[Target]]]` | a typed edge in prose | `[depends-on:: [[Adopt provider]]]` |
| `^id` | a stable block id (barcode) | `^t1` |
| `--- … ---` | YAML front matter | file-level metadata |

## Live preview

Open a `.sarib` file and press **Ctrl+Shift+V** (or click the preview icon in the
editor title bar, or run "sarib: Open Preview"). A panel opens beside the editor
showing every projection of the file as tabs — **Document · Outline · Board ·
Graph · Machine** — and re-renders as you type (400 ms debounce, unsaved buffer
included).

The extension holds no rendering logic. It pipes the buffer to the Python
previewer (`sarib.preview`) over stdin, so preview and CLI can never disagree.
Requirements:

- **Python 3** on your PATH (or set `sarib.pythonPath` in Settings).
- The **`sarib` package installed** for that Python: `pip install sarib`. This is
  all you need — preview then works on `.sarib` files in *any* folder, with no
  repo checkout and no configuration.
- The Graph tab draws with mermaid.js from a CDN; offline it shows the copyable source.

How the previewer is resolved, first match wins:

| Order | Source | Use |
|---|---|---|
| 1 | `sarib.previewScript` setting | pin an exact `tools/preview.py` (a `~` prefix is expanded) |
| 2 | a sarib checkout in any parent folder of the open file | working-tree code previews itself |
| 3 | a sarib checkout in a workspace folder | same, for multi-root workspaces |
| 4 | the installed `sarib` package (`python -m sarib.preview`) | any folder, unconfigured — the normal case |

So a repo checkout always wins over the installed package (edit `impl/`, see it in
the preview), and everywhere else the installed package takes over.

## Install

Don't copy the folder into `~/.vscode/extensions` — modern VS Code ignores
unregistered folders. Package and install instead (needs Node.js):

```
pip install sarib                 # the previewer the extension calls
cd editors/vscode-sarib
npx @vscode/vsce package
code --install-extension vscode-sarib-0.3.0.vsix
```

Then reload the window. Open any `.sarib` file — the marks light up and the
bottom-right of the window says **sarib**.

Colors follow your current VS Code theme (types render as type-names, links as
links, ids as constants, etc.), so it looks native to whatever theme you use.

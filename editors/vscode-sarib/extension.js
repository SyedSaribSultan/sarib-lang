// sarib live preview — a thin consumer of tools/preview.py (D-052/D-053).
// The extension holds no rendering logic: it pipes the current buffer to the
// Python previewer over stdin and shows the returned HTML in a webview.
const vscode = require('vscode');
const cp = require('child_process');
const fs = require('fs');
const path = require('path');

let panel = null;
let current = null; // uri string of the document being previewed
let timer = null;

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function message(body) {
  return `<!doctype html><html><body style="font-family:system-ui;padding:2rem;line-height:1.6">${body}</body></html>`;
}

function findScript() {
  const explicit = vscode.workspace.getConfiguration('sarib').get('previewScript');
  if (explicit) return explicit;
  for (const f of vscode.workspace.workspaceFolders || []) {
    const p = path.join(f.uri.fsPath, 'tools', 'preview.py');
    if (fs.existsSync(p)) return p;
  }
  return null;
}

// Remember the selected tab across re-renders (webview state survives html swaps).
const STATE_JS = `<script>(function(){var v=acquireVsCodeApi();var s=v.getState();
if(s&&s.tab){var b=document.querySelector('nav button[data-t="'+s.tab+'"]');if(b)b.click();}
document.querySelectorAll('nav button').forEach(function(b){
  b.addEventListener('click',function(){v.setState({tab:b.dataset.t});});});
})();</script>`;

function render(doc) {
  if (!panel) return;
  const script = findScript();
  if (!script) {
    panel.webview.html = message(
      '<h2>sarib preview</h2><p>Could not find <code>tools/preview.py</code>. ' +
      'Open the sarib repo as a workspace folder, or set <code>sarib.previewScript</code> in Settings.</p>');
    return;
  }
  const py = vscode.workspace.getConfiguration('sarib').get('pythonPath') || 'python';
  const proc = cp.execFile(py, [script, '-', '--stdout'], {
    env: Object.assign({}, process.env, { PYTHONUTF8: '1' }),
    maxBuffer: 32 * 1024 * 1024,
  }, (err, stdout, stderr) => {
    if (!panel) return;
    if (err) {
      panel.webview.html = message(`<h2>preview failed</h2><pre>${esc(stderr || err.message)}</pre>`);
      return;
    }
    panel.title = 'Preview ' + path.basename(doc.fileName);
    panel.webview.html = stdout.replace('</body>', STATE_JS + '</body>');
  });
  proc.stdin.write(doc.getText(), 'utf8');
  proc.stdin.end();
}

function activate(context) {
  context.subscriptions.push(vscode.commands.registerCommand('sarib.preview', () => {
    const ed = vscode.window.activeTextEditor;
    if (!ed || ed.document.languageId !== 'sarib') {
      vscode.window.showInformationMessage('Open a .sarib file first.');
      return;
    }
    if (!panel) {
      panel = vscode.window.createWebviewPanel('saribPreview', 'sarib Preview',
        { viewColumn: vscode.ViewColumn.Beside, preserveFocus: true },
        { enableScripts: true, retainContextWhenHidden: true });
      panel.onDidDispose(() => { panel = null; current = null; });
    } else {
      panel.reveal(undefined, true);
    }
    current = ed.document.uri.toString();
    render(ed.document);
  }));

  vscode.workspace.onDidChangeTextDocument(e => {
    if (panel && e.document.uri.toString() === current) {
      clearTimeout(timer);
      timer = setTimeout(() => render(e.document), 400);
    }
  }, null, context.subscriptions);

  // Preview follows whichever .sarib file is active.
  vscode.window.onDidChangeActiveTextEditor(ed => {
    if (panel && ed && ed.document.languageId === 'sarib'
        && ed.document.uri.toString() !== current) {
      current = ed.document.uri.toString();
      render(ed.document);
    }
  }, null, context.subscriptions);
}

function deactivate() {}

module.exports = { activate, deactivate };

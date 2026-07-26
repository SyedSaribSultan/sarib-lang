// sarib live preview — a thin consumer of sarib.preview (D-052/D-053).
// The extension holds no rendering logic: it pipes the current buffer to the
// Python previewer over stdin and shows the returned HTML in a webview.
const vscode = require('vscode');
const cp = require('child_process');
const fs = require('fs');
const os = require('os');
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

function expand(p) {
  if (!p) return p;
  if (p === '~' || p.startsWith('~/') || p.startsWith('~\\')) {
    return path.join(os.homedir(), p.slice(1));
  }
  return p;
}

// Where to find the previewer, most specific first. A repo checkout wins over the
// installed package so a working tree previews its own impl/; otherwise the
// installed `sarib` package (pip install sarib) works in any folder, unconfigured.
function findRunner(doc) {
  const explicit = expand(vscode.workspace.getConfiguration('sarib').get('previewScript'));
  if (explicit) return { args: [explicit] };

  const roots = [];
  // Walk up from the file itself, so a .sarib file anywhere inside the repo works
  // even when the repo is not the open workspace folder.
  if (doc && doc.uri.scheme === 'file') {
    for (let d = path.dirname(doc.uri.fsPath), prev = null; d !== prev; prev = d, d = path.dirname(d)) {
      roots.push(d);
    }
  }
  for (const f of vscode.workspace.workspaceFolders || []) roots.push(f.uri.fsPath);
  for (const r of roots) {
    // In-package previewer: import it as a module, with impl/ on the path (relative imports).
    if (fs.existsSync(path.join(r, 'impl', 'sarib', 'preview.py'))) {
      return { args: ['-m', 'sarib.preview'], pythonPath: path.join(r, 'impl') };
    }
    // pre-0.1.4 checkouts: previewer in tools/. Require impl/sarib/ too, so an
    // unrelated project's tools/preview.py is never mistaken for ours.
    const shim = path.join(r, 'tools', 'preview.py');
    if (fs.existsSync(shim) && fs.existsSync(path.join(r, 'impl', 'sarib', '__init__.py'))) {
      return { args: [shim] };
    }
  }

  return { args: ['-m', 'sarib.preview'] }; // installed package — folder-independent
}

// Setup problems get an actionable page; anything else shows the raw traceback.
// The three cases are distinct and the fixes differ, so never collapse them:
// no interpreter, no package, package present but older than the previewer (<0.1.4).
function setupHelp(err, stderr, py) {
  const e = esc(py);
  if (err.code === 'ENOENT') {
    return `<p>Could not run Python (<code>${e}</code>). Install Python 3, or set ` +
      '<code>sarib.pythonPath</code> in Settings to the interpreter you use.</p>';
  }
  const s = stderr || '';
  if (/No module named ['"]?sarib\.preview/.test(s)) {
    return '<p>Your <code>sarib</code> package predates the previewer, which moved into the ' +
      'package in <b>0.1.4</b>. Upgrade it:</p>' +
      `<pre>${e} -m pip install -U "sarib>=0.1.4"</pre>` +
      '<p>Until 0.1.4 is on PyPI, install from a checkout (<code>pip install ./impl</code>) or ' +
      'point <code>sarib.previewScript</code> at its <code>tools/preview.py</code>.</p>';
  }
  if (/No module named ['"]?sarib['"]?\r?$/m.test(s)) { // bare `sarib`, not `sarib.<sub>`
    return `<p>The <code>sarib</code> package is not installed for <code>${e}</code>. ` +
      'Install it to preview <code>.sarib</code> files in any folder:</p>' +
      `<pre>${e} -m pip install "sarib>=0.1.4"</pre>`;
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
  const runner = findRunner(doc);
  const py = vscode.workspace.getConfiguration('sarib').get('pythonPath') || 'python';
  const env = Object.assign({}, process.env, { PYTHONUTF8: '1' });
  if (runner.pythonPath) {
    env.PYTHONPATH = [runner.pythonPath, process.env.PYTHONPATH].filter(Boolean).join(path.delimiter);
  }
  const proc = cp.execFile(py, runner.args.concat(['-', '--stdout']), {
    env,
    maxBuffer: 32 * 1024 * 1024,
  }, (err, stdout, stderr) => {
    if (!panel) return;
    if (err) {
      const setup = setupHelp(err, stderr, py);
      panel.webview.html = setup
        ? message(`<h2>sarib preview</h2>${setup}`)
        : message(`<h2>preview failed</h2><pre>${esc(stderr || err.message)}</pre>`);
      return;
    }
    panel.title = 'Preview ' + path.basename(doc.fileName);
    panel.webview.html = stdout.replace('</body>', STATE_JS + '</body>');
  });
  proc.stdin.on('error', () => {}); // a missing interpreter closes stdin before we write
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

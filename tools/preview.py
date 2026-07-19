"""sarib preview — one readable HTML page with every projection of a .sarib file.
A consumer of the reference impl (like bench/ and dogfood/), NOT part of the
core LOC budget (G4). Views are projections (D-052); exports are read-only (D-053).

Run:  python tools/preview.py <file.sarib> [-o out.html] [--no-open]
Writes <file>.preview.html next to the source and opens it in the browser.
The Graph tab draws with mermaid.js from a CDN (internet needed for that tab
only); offline it falls back to the copyable mermaid source.
"""
import argparse, html, json, pathlib, re, sys, webbrowser

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "impl"))
from sarib import parse, canon, fmt
from sarib.render import mermaid, _depth


def esc(s):
    return html.escape(str(s), quote=True)


def inline(text):
    """Escape, then surface the two inline marks readably."""
    t = esc(text)
    t = re.sub(r"\[([\w-]+):: \[\[(.+?)\]\]\]",
               r'<span class="rel"><b>\1</b> → \2</span>', t)
    t = re.sub(r"\[\[(.+?)\]\]", r'<span class="wl">\1</span>', t)
    return t


def badges(n):
    b = ""
    if n.type:
        b += f' <span class="badge">{esc(n.type)}</span>'
    if n.slug:
        b += f' <span class="dim">#{esc(n.slug)}</span>'
    if not (n.id.startswith("n") and n.id[1:].isdigit()):
        b += f' <span class="dim">^{esc(n.id)}</span>'
    return b


def document_html(doc):
    out = []
    for n in doc.walk(None):
        if n.kind_hint == "heading":
            lvl = min(int(n.properties.get("_level", _depth(doc, n) + 1)), 6)
            out.append(f"<h{lvl}>{inline(n.title)}{badges(n)}</h{lvl}>")
            chips = [f'<span class="chip"><b>{esc(k)}</b> {inline(v)}</span>'
                     for k, v in n.properties.items() if not k.startswith("_")]
            if chips:
                out.append(f'<div class="chips">{"".join(chips)}</div>')
        elif n.kind_hint == "item":
            out.append(f'<div class="li">•&nbsp;{inline(n.title)}{badges(n)}</div>')
        elif n.content.strip():
            out.append(f"<p>{inline(n.content)}</p>")
    return "\n".join(out)


def outline_html(doc, parent=None):
    out = []
    for n in doc.children(parent):
        if n.kind_hint == "prose":
            continue
        sub = list(doc.walk(n.id))
        tasks = [m for m in sub if m.type and m.type.endswith("task")]
        cue = ""
        if tasks:
            done = sum(1 for t in tasks if t.properties.get("status") == "done")
            cue = f' <span class="cookie">{done}/{len(tasks)}</span>'
        size = f' <span class="dim">({len(sub)})</span>' if sub else ""
        label = f"{inline(n.title)}{badges(n)}{cue}{size}"
        kids = outline_html(doc, n.id)
        if kids:
            out.append(f"<details open><summary>{label}</summary>{kids}</details>")
        else:
            out.append(f'<div class="leaf">{label}</div>')
    return "".join(out)


def board_html(doc):
    cols = {}
    for n in doc.walk(None):
        if n.type and n.type.endswith("task"):
            cols.setdefault(n.properties.get("status", "todo"), []).append(n)
    if not cols:
        return '<p class="dim">No task nodes in this file — nothing to board.</p>'
    order = {"todo": 0, "doing": 1, "done": 2}
    out = ['<div class="board">']
    for status in sorted(cols, key=lambda s: (order.get(s, 9), s)):
        out.append(f'<div class="col"><h3>{esc(status)} <span class="dim">({len(cols[status])})</span></h3>')
        for n in cols[status]:
            meta = [f'<span class="chip"><b>{esc(k)}</b> {esc(v)}</span>'
                    for k, v in n.properties.items() if k in ("due", "priority", "owner")]
            out.append(f'<div class="card">{inline(n.title)}'
                       f'<div class="chips">{"".join(meta)}<span class="dim">[{esc(n.id)}]</span></div></div>')
        out.append("</div>")
    out.append("</div>")
    return "".join(out)


CSS = """
:root{--bg:#fff;--fg:#202124;--dim:#80868b;--line:#e8eaed;--card:#fff;
  --accent:#1a73e8;--chipbg:#f1f3f4;--relbg:#e8f0fe}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
  font:13.5px/1.55 "Google Sans Flex","Google Sans",system-ui,sans-serif}
main{max-width:820px;margin:0 auto;padding:.8rem 1.5rem 3rem}
header{padding:1rem 0 .3rem}
header h1{margin:0;font-size:1.25rem}header .dim{font-size:.78rem}
nav{display:flex;gap:.3rem;margin:.7rem 0 1rem;flex-wrap:wrap}
nav button{border:1px solid var(--line);background:var(--bg);color:var(--fg);
  padding:.2rem .7rem;border-radius:999px;cursor:pointer;font:inherit;font-size:.78rem}
nav button.on{background:var(--accent);border-color:var(--accent);color:#fff}
section{display:none}section.on{display:block}
.dim{color:var(--dim)}
.badge{background:var(--chipbg);color:var(--dim);font-size:.62rem;font-weight:600;
  padding:.05rem .45rem;border-radius:999px;vertical-align:middle;
  text-transform:uppercase;letter-spacing:.03em}
.chips{display:flex;gap:.35rem;flex-wrap:wrap;margin:.25rem 0 .7rem}
.chip{background:var(--chipbg);border-radius:5px;padding:.02rem .45rem;font-size:.74rem}
.chip b{font-weight:600}
.wl{color:var(--accent)}
.rel{background:var(--relbg);color:var(--accent);border-radius:5px;padding:.02rem .35rem;font-size:.9em}
details{margin:.1rem 0;padding-left:.9rem;border-left:1px solid var(--line)}
summary{cursor:pointer;padding:.1rem 0}.leaf{padding:.1rem 0 .1rem .95rem}
.cookie{background:var(--chipbg);border-radius:5px;font-size:.68rem;padding:0 .35rem}
.board{display:flex;gap:.8rem;align-items:flex-start;overflow-x:auto}
.col{background:var(--chipbg);border-radius:8px;padding:.5rem .7rem;min-width:200px;flex:1}
.col h3{margin:.1rem 0 .4rem;font-size:.72rem;text-transform:uppercase;
  letter-spacing:.05em;color:var(--dim)}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;
  padding:.4rem .6rem;margin:.4rem 0;font-size:.85rem}
pre{background:#f8f9fa;border:1px solid var(--line);border-radius:6px;
  padding:.8rem;overflow-x:auto;font-size:.74rem;line-height:1.5}
.li{padding-left:.9rem}footer{margin-top:2.5rem;font-size:.72rem;color:var(--dim)}
h1,h2,h3,h4,h5,h6{line-height:1.3;font-weight:600}
h1{font-size:1.3rem}h2{font-size:1.1rem}h3{font-size:.95rem}h4{font-size:.85rem}
b,strong{font-weight:600}
a{color:var(--accent)}
"""

JS = """
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('nav button,section').forEach(e=>e.classList.remove('on'));
  b.classList.add('on');document.getElementById(b.dataset.t).classList.add('on');
  if(b.dataset.t==='graph'&&!window._mz){window._mz=1;
    var g=document.getElementById('gout');
    if(!window.mermaid){g.innerHTML='<p class="dim">mermaid.js could not load '+
      '(offline?) — copy the source below into mermaid.live.</p>';return;}
    mermaid.initialize({startOnLoad:false,theme:'default'});
    mermaid.render('mgraph',MMD).then(function(r){g.innerHTML=r.svg;})
      .catch(function(e){g.textContent=String(e);});}
});
"""

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — sarib preview</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Google+Sans+Flex:wght@300..600&display=swap" rel="stylesheet">
<style>{css}</style></head><body><main>
<header><h1>{title}</h1>
<div class="dim">{src} · {nnodes} nodes · {nedges} edges · {ndiag} diagnostics</div></header>
<nav>
<button class="on" data-t="document">Document</button>
<button data-t="outline">Outline</button>
<button data-t="board">Board</button>
<button data-t="graph">Graph</button>
<button data-t="machine">Machine</button>
</nav>
<section id="document" class="on">{document}</section>
<section id="outline">{outline}</section>
<section id="board">{board}</section>
<section id="graph">
<div id="gout"></div>
<details><summary class="dim">mermaid source (for <a href="https://mermaid.live">mermaid.live</a>)</summary>
<pre>{mermaid}</pre></details></section>
<section id="machine"><p class="dim">The canonical form (D-041): one JSON line per
node/edge — what agents and tools address by id.</p><pre>{canon}</pre></section>
<footer>Generated by <code>tools/preview.py</code> — every tab is a projection of the
same source (D-052). Exports are read-only (D-053): edit the <code>.sarib</code> file, not this page.</footer>
</main>
<script>var MMD={mmd};</script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>{js}</script></body></html>
"""


def build_text(text: str, srcname: str) -> str:
    doc = parse(text)
    return PAGE.format(
        title=esc(doc.meta.get("title", srcname.rsplit(".", 1)[0])), src=esc(srcname),
        nnodes=len(doc.nodes), nedges=len(doc.edges), ndiag=len(doc.diagnostics),
        css=CSS, js=JS,
        document=document_html(doc), outline=outline_html(doc),
        board=board_html(doc), mermaid=esc(mermaid(doc)), canon=esc(canon(doc)),
        mmd=json.dumps(mermaid(doc)).replace("</", "<\\/"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render a .sarib file as a tabbed HTML preview of all views.")
    ap.add_argument("file", help="path to a .sarib file, or '-' to read from stdin")
    ap.add_argument("-o", "--out", help="output path (default: <file>.preview.html)")
    ap.add_argument("--stdout", action="store_true", help="print HTML to stdout (no file, no browser)")
    ap.add_argument("--no-open", action="store_true", help="don't open the browser")
    ns = ap.parse_args(argv)
    if ns.file == "-":
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8")
        page = build_text(sys.stdin.read(), "buffer")
    else:
        src = pathlib.Path(ns.file)
        page = build_text(src.read_text(encoding="utf-8"), src.name)
    if ns.stdout:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(page)
        return
    if ns.file == "-" and not ns.out:
        ap.error("reading from stdin requires --stdout or -o")
    out = pathlib.Path(ns.out) if ns.out else src.with_suffix(src.suffix + ".preview.html")
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out}")
    if not ns.no_open:
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()

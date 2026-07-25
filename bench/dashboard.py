"""Live G2 dashboard. Reads bench/g2-corpus/results/*.jsonl on every request and
serves a self-contained auto-refreshing HTML page. Truthful by construction — it
renders only what is on disk; nothing is mocked. Read-only; never writes results.

Run:   python bench/dashboard.py          (serves http://localhost:8765, opens browser)
       python bench/dashboard.py 9000      (custom port)
"""
from __future__ import annotations
import http.server, json, pathlib, socketserver, sys, webbrowser, html

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "impl"))
sys.path.insert(0, str(ROOT / "bench" / "g2-corpus"))
RESULTS = ROOT / "bench" / "g2-corpus" / "results"
FULL = 432
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765

from run_g2 import stats_for, sig_pair, mcnemar_exact, bootstrap_ci, QUESTIONS, CONDS  # noqa: E402

COND_LABEL = {"A": "A · Markdown", "B": "B · .sarib whole", "C": "C · bounded query", "D": "D · no-types"}


def load():
    models = {}
    if not RESULTS.exists():
        return models
    for path in sorted(RESULTS.glob("raw-*.jsonl")):
        meta, rows = {}, []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if "meta" in r:
                meta = r["meta"]
            elif "qid" in r:
                rows.append(r)
        if rows:
            models[(rows[0]["provider"], rows[0]["model"])] = {"meta": meta, "rows": rows}
    return models


def pct(x):
    return f"{100 * x:.1f}%"


def render():
    models = load()
    real = {k: v for k, v in models.items() if k[0] != "mock"}
    parts = []
    # ---- overview cards ----
    complete = sum(1 for v in real.values() if len(v["rows"]) >= 144 * v["meta"].get("runs", 3))
    total_cells = sum(len(v["rows"]) for v in real.values())
    parts.append(f"""<section class=cards>
      <div class=card><div class=k>Models</div><div class=v>{len(real)}</div><div class=s>{complete} complete</div></div>
      <div class=card><div class=k>Cells logged</div><div class=v>{total_cells}</div><div class=s>of {FULL * len(real)} targeted</div></div>
      <div class=card><div class=k>Questions</div><div class=v>{len(QUESTIONS)}</div><div class=s>12 lookup · 12 multihop · 12 aggregate</div></div>
    </section>""")

    # ---- progress bars ----
    rows_html = []
    for (prov, model), v in sorted(real.items()):
        n = len(v["rows"])
        runs = v["meta"].get("runs", 3)
        target = 144 * runs
        p = min(100, 100 * n / target)
        done = n >= target
        bar = f'<div class=bar><div class="fill {"done" if done else ""}" style="width:{p:.0f}%"></div></div>'
        rows_html.append(f'<tr><td class=mono>{html.escape(prov)}/{html.escape(model)}</td>'
                         f'<td style="width:55%">{bar}</td><td class=mono>{n}/{target}</td>'
                         f'<td>{"✓" if done else "…"}</td></tr>')
    parts.append("<h2>Run progress</h2><table class=grid><thead><tr><th>Model</th><th>Progress</th>"
                 "<th>Cells</th><th></th></tr></thead><tbody>" + "".join(rows_html) + "</tbody></table>")

    # ---- accuracy matrix + verdict (complete models only) ----
    done_models = {k: v for k, v in real.items() if len(v["rows"]) >= 144 * v["meta"].get("runs", 3)}
    if done_models:
        mrows = []
        for (prov, model), v in sorted(done_models.items()):
            st = stats_for(v["rows"])
            sg = sig_pair(st)
            s4 = ("C" in st and "A" in st and st["C"]["acc"] > st["A"]["acc"]
                  and st["C"]["tokens"] <= st["A"]["tokens"])
            sig = sg and sg["p"] < 0.05
            cells = []
            for c in CONDS:
                if c in st:
                    s = st[c]
                    hot = "hot" if c == "C" else ""
                    cells.append(f'<td class="{hot}">{pct(s["acc"])}<span class=tok>{s["tokens"]:.0f}t</span></td>')
                else:
                    cells.append("<td>—</td>")
            verdict = (f'<span class="badge {"pass" if s4 and sig else "fail"}">'
                       f'{"PASS" if s4 and sig else "no"}</span>')
            deltacell = (f'{sg["delta"]:+.3f}<br><span class=tok>p={sg["p"]:.3f}</span>' if sg else "—")
            mrows.append(f'<tr><td class=mono>{html.escape(prov)}/{html.escape(model)}</td>'
                         + "".join(cells) + f'<td>{deltacell}</td><td>{verdict}</td></tr>')
        parts.append("<h2>Accuracy matrix — complete models "
                     "<span class=note>(C = the .sarib agent loop; token count under each cell)</span></h2>"
                     "<table class=grid><thead><tr><th>Model</th>"
                     + "".join(f"<th>{COND_LABEL[c]}</th>" for c in CONDS)
                     + "<th>C−A (Δ, p)</th><th>S4</th></tr></thead><tbody>"
                     + "".join(mrows) + "</tbody></table>")

        # pooled
        pooled = []
        for v in done_models.values():
            sg = sig_pair(stats_for(v["rows"]))
            if sg:
                pooled += sg["pairs"]
        if pooled:
            n01 = sum(1 for a, b in pooled if a and not b)
            n10 = sum(1 for a, b in pooled if not a and b)
            lo, hi = bootstrap_ci(pooled)
            d = (sum(b for _, b in pooled) - sum(a for a, _ in pooled)) / len(pooled)
            parts.append(f'<p class=pooled><b>Pooled ({len(pooled)} question-pairs across '
                         f'{len(done_models)} complete models):</b> Δ = {d:+.3f}, '
                         f'McNemar p = {mcnemar_exact(n01, n10):.4f}, '
                         f'bootstrap 95% CI [{lo:+.3f}, {hi:+.3f}]. '
                         f'{"<span class=badge pass>significant</span>" if mcnemar_exact(n01,n10)<0.05 else "<span class=badge fail>not yet significant</span>"}</p>')
    else:
        parts.append("<p class=note>No model has full coverage yet — accuracy matrix appears once "
                     "a model completes all 432 cells.</p>")

    body = "\n".join(parts)
    return f"""<!doctype html><html><head><meta charset=utf-8>
<meta http-equiv=refresh content=10>
<title>.sarib G2 — live</title>
<style>
:root{{--bg:#0b0e14;--panel:#141922;--line:#232a36;--fg:#e6edf3;--dim:#8b98a9;--hot:#1f6feb22;--acc:#58a6ff;--pass:#3fb950;--fail:#f85149}}
*{{box-sizing:border-box}}body{{margin:0;font:14px/1.5 -apple-system,Segoe UI,system-ui,sans-serif;background:var(--bg);color:var(--fg);padding:24px 32px}}
h1{{font-size:20px;margin:0 0 2px}}h2{{font-size:15px;margin:26px 0 8px;color:var(--fg)}}
.sub{{color:var(--dim);margin:0 0 18px;font-size:13px}}
.note{{color:var(--dim);font-weight:400;font-size:12px}}
.cards{{display:flex;gap:14px;flex-wrap:wrap}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 18px;min-width:150px}}
.card .k{{color:var(--dim);font-size:12px}}.card .v{{font-size:26px;font-weight:600}}.card .s{{color:var(--dim);font-size:12px}}
table.grid{{border-collapse:collapse;width:100%;background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow:hidden}}
.grid th{{text-align:left;font-size:12px;color:var(--dim);font-weight:600;padding:9px 12px;border-bottom:1px solid var(--line);background:#0f141c}}
.grid td{{padding:9px 12px;border-bottom:1px solid var(--line)}}
.grid tr:last-child td{{border-bottom:none}}
.mono{{font-family:ui-monospace,Consolas,monospace;font-size:12.5px}}
td.hot{{background:var(--hot)}}
.tok{{color:var(--dim);font-size:11px;margin-left:5px}}
.bar{{background:#0f141c;border:1px solid var(--line);border-radius:6px;height:14px;overflow:hidden}}
.fill{{height:100%;background:linear-gradient(90deg,#2a4a7a,var(--acc));transition:width .4s}}
.fill.done{{background:linear-gradient(90deg,#2d7a45,var(--pass))}}
.badge{{padding:2px 9px;border-radius:20px;font-size:11px;font-weight:600}}
.badge.pass{{background:#3fb95022;color:var(--pass)}}.badge.fail{{background:#f8514922;color:var(--fail)}}
.pooled{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin-top:10px}}
footer{{color:var(--dim);font-size:11px;margin-top:24px}}
</style></head><body>
<h1>.sarib G2 — agent accuracy vs Markdown <span class=note>(success test S4)</span></h1>
<p class=sub>Live from <span class=mono>bench/g2-corpus/results/*.jsonl</span> · auto-refresh 10s · read-only</p>
{body}
<footer>C beats A = the intended agent loop (bounded .sarib query) beats whole-file Markdown, at ≤ token cost.
Grading is pre-registered normalized exact-match; no LLM judge. Partial (rate-capped) models are shown in progress but excluded from the matrix and pooled verdict.</footer>
</body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            page = render().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(page)))
            self.end_headers()
            self.wfile.write(page)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"error: {e}".encode())

    def log_message(self, *a):
        pass


def main():
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as srv:
        url = f"http://localhost:{PORT}"
        print(f"dashboard live at {url}  (Ctrl+C to stop)", flush=True)
        try:
            webbrowser.open(url)
        except Exception:
            pass
        srv.serve_forever()


if __name__ == "__main__":
    main()

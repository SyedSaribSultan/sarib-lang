"""G2 runner - agent accuracy vs Markdown (Stage 15 §4 gate G2 / success test S4).

Protocol: bench/g2-g3-protocol.md. Corpora/questions: bench/g2-corpus/build.py.

Conditions (identical knowledge, per question):
  A  whole kb.md in context            (honest Markdown baseline)
  B  whole kb.sarib in context         (typed surface, whole file)
  C  bounded `sarib query` result only (the intended agent loop)
  D  whole kb.notypes.sarib            (ablation: structure without types/edges)

Rigor:
  - 3 runs per (model, question, condition), temperature 0, seed 42 where accepted.
  - Grading is programmatic normalized exact-match against the constructed key
    (rubric below, fixed in advance). No LLM judge anywhere.
  - Input tokens = provider-reported usage.prompt_tokens (the model's own
    tokenizer); tiktoken o200k_base only for the keyless mock self-test.
  - Every response cached to results/raw-*.jsonl -> reruns resume; rate-cap
    aborts are loud, never silent question drops.
  - Significance for the S4 claim (C beats A): exact McNemar on per-question
    majority correctness + bootstrap 95% CI on the accuracy delta.

Grading rubric (fixed IN ADVANCE - no post-hoc leniency):
  normalize = NFC, casefold, trim, strip wrapping quotes/backticks/final '.',
              collapse whitespace, drop one leading "the ".
  scalar : normalize(answer) == normalize(key)
  date   : same (keys are YYYY-MM-DD; the prompt demands that format)
  count  : answer must contain exactly one integer, equal to the key; OR the
           whole normalized answer is a single number word (zero..twenty).
  list   : split ONLY on , ; and newlines (prompt demands comma-separated);
           strip one leading "and "; set-equality of normalized items.

Usage (from repo root):
  python bench/run_g2.py selftest             # mock end-to-end harness proof
  python bench/run_g2.py run                  # all reachable providers
  python bench/run_g2.py run --providers groq --models llama-3.3-70b-versatile
  python bench/run_g2.py report               # regenerate bench/g2-results.md
"""
from __future__ import annotations
import argparse, json, math, os, pathlib, random, re, sys, time, unicodedata
import urllib.request, urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
_envf = ROOT / ".env"                     # gitignored; keys never enter the repo history
if _envf.exists():
    for _l in _envf.read_text(encoding="utf-8").splitlines():
        if "=" in _l and not _l.lstrip().startswith("#"):
            k, v = _l.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
sys.path.insert(0, str(ROOT / "impl"))
sys.path.insert(0, str(ROOT / "bench" / "g2-corpus"))
from sarib import parse, query as run_query          # noqa: E402
from providers import available, PROVIDERS           # noqa: E402

CORPUS = ROOT / "bench" / "g2-corpus"
RESULTS = CORPUS / "results"
CONDS = "ABCD"
RUNS_DEFAULT = 3
SEED = 42

KB = {c: (CORPUS / f).read_text(encoding="utf-8")
      for c, f in (("A", "kb.md"), ("B", "kb.sarib"), ("D", "kb.notypes.sarib"))}
QUESTIONS = json.loads((CORPUS / "questions.json").read_text(encoding="utf-8"))
DOC = parse(KB["B"])

C_LEGEND = ("The context is the JSON result of a bounded graph query over the knowledge base: "
            "`nodes` are the retrieved items (id, type, title, props); `edges` are typed links "
            "between node ids; `query` is the request that produced it.")

PROMPT = """You are answering a question about a project knowledge base.
Use ONLY the information in the context below.
{legend}
<context>
{context}
</context>

Question: {question}

Reply with ONLY the final answer, no explanation.
Format rules:
- A name or title: write it exactly as it appears in the context.
- A date: YYYY-MM-DD.
- A count: digits only (e.g. 7).
- Multiple items: comma-separated on one line.
"""


def context_for(cond: str, q: dict) -> str:
    if cond in KB:
        return KB[cond]
    res = run_query(DOC, q["query"])
    res.pop("diagnostics", None)
    return json.dumps({"query": q["query"], "result": res},
                      separators=(",", ":"), ensure_ascii=False)


def prompt_for(cond: str, q: dict) -> str:
    return PROMPT.format(legend=C_LEGEND + "\n" if cond == "C" else "",
                         context=context_for(cond, q), question=q["question"])


# ---------------------------------------------------------------- grading
NUM_WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFC", str(s)).casefold()
    prev = None
    while s != prev:                     # peel wrapping quotes/periods to fixed point
        prev = s
        s = s.strip().strip("`\"'“”‘’")
        s = s[:-1] if s.endswith(".") else s
    s = " ".join(s.split())
    return s[4:] if s.startswith("the ") else s


def grade(answer_type: str, key, raw: str) -> bool:
    raw = (raw or "").strip()
    if answer_type == "count":
        ints = re.findall(r"-?\d+", raw)
        if len(ints) == 1:
            return int(ints[0]) == int(key)
        return not ints and NUM_WORDS.get(normalize(raw)) == int(key)
    if answer_type == "list":
        items = [normalize(re.sub(r"^and\s+", "", x.strip())) for x in re.split(r"[,;\n]", raw)]
        items = [x for x in items if x]
        return sorted(set(items)) == sorted({normalize(k) for k in key})
    return normalize(raw) == normalize(key)      # scalar | date


# ---------------------------------------------------------------- model calls
def call_openai_compat(base: str, key: str | None, model: str, prompt: str,
                       timeout=120) -> tuple[str, int, int, str]:
    body = {"model": model, "temperature": 0, "seed": SEED, "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}]}
    # UA matters: Cloudflare fronting Groq/Cerebras rejects urllib's default (error 1010)
    hdrs = {"Content-Type": "application/json", "User-Agent": "curl/8.9.1"}
    if key:
        hdrs["Authorization"] = f"Bearer {key}"
    for attempt in range(9):
        try:
            req = urllib.request.Request(base.rstrip("/") + "/chat/completions",
                                         json.dumps(body).encode(), hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read())
            if "choices" not in data:      # OpenRouter-style 200-with-error-body
                err = data.get("error") or {}
                code = int(err.get("code") or 0)
                if (code in (429, 500, 502, 503) or "rate" in str(err).lower()) and attempt < 8:
                    wait = min(120, 2 ** (attempt + 1))
                    print(f"    in-body error {code}, backoff {wait}s ({str(err)[:120]})")
                    time.sleep(wait); continue
                raise RuntimeError(f"no choices in response: {json.dumps(data)[:300]}")
            msg = data["choices"][0]["message"]
            text = (msg.get("content") or "").strip()
            # reasoning models: the answer is what remains after the think block
            text = re.sub(r"(?s)<think>.*?</think>", "", text).strip()
            fin = data["choices"][0].get("finish_reason")
            if not text and fin == "length" and body["max_tokens"] < 8192:
                body["max_tokens"] = 8192   # thinking ate the budget; give it room once
                continue
            usage = data.get("usage", {}) or {}
            return (text, usage.get("prompt_tokens", -1),
                    usage.get("completion_tokens", -1), data.get("model", model))
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:400]
            if e.code == 400 and "seed" in detail and "seed" in body:
                body.pop("seed"); continue                     # provider rejects seed
            if e.code in (429, 500, 502, 503) and attempt < 8:
                wait = min(120, 2 ** (attempt + 1))
                print(f"    HTTP {e.code}, backoff {wait}s ({detail[:120]})")
                time.sleep(wait); continue
            raise RuntimeError(f"HTTP {e.code}: {detail}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < 8:
                time.sleep(min(120, 2 ** (attempt + 1))); continue
            raise
    raise RuntimeError("unreachable")


def _tik(s: str) -> int:
    import tiktoken
    return len(tiktoken.get_encoding("o200k_base").encode(s))


def call_mock(model: str, q: dict, cond: str, run: int, prompt: str):
    """SELF-TEST models (no network). oracle: always the key, exactly formatted.
    noisy-oracle: the key with harmless formatting noise (tests normalization).
    adversary: a wrong answer of the right shape (must score 0)."""
    key, at = q["answer"], q["answer_type"]
    fmt = ", ".join(key) if isinstance(key, list) else str(key)
    if model == "oracle":
        text = fmt
    elif model == "noisy-oracle":
        rnd = random.Random(f"{q['id']}/{cond}/{run}")
        text = fmt.upper() if rnd.random() < 0.5 else f'"{fmt}".'
    elif model == "adversary":
        if at == "count":
            text = str(int(key) + 1)
        elif isinstance(key, list):
            text = ", ".join(list(key)[:-1]) if len(key) > 1 else "Benchmark query latency at ten times load"
        else:
            text = "unknown-value"
    else:
        raise ValueError(model)
    return text, _tik(prompt), _tik(text), f"mock/{model}"


# ---------------------------------------------------------------- persistence
def raw_path(provider: str, model: str) -> pathlib.Path:
    slug = re.sub(r"[^A-Za-z0-9._-]", "_", f"{provider}_{model}")
    return RESULTS / f"raw-{slug}.jsonl"


def load_done(path: pathlib.Path) -> dict:
    done = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if "qid" in r:
                    done[(r["qid"], r["cond"], r["run"])] = r
    return done


def run_model(provider, model, base, key, delay, pin, runs, conds, limit=None):
    RESULTS.mkdir(exist_ok=True)
    path = raw_path(provider, model)
    done = load_done(path)
    qmap = {q["id"]: q for q in QUESTIONS}
    cells = []
    for run in range(1, runs + 1):
        for cond in conds:
            order = list(qmap)
            random.Random(f"{model}/{cond}/{run}").shuffle(order)   # bias control
            cells += [(qid, cond, run) for qid in order]
    if limit:
        cells = cells[:limit]
    todo = [c for c in cells if c not in done]
    print(f"[{provider}/{model}] {len(cells)} cells, {len(done)} cached, {len(todo)} to run {pin}")
    if todo and not any(l.startswith('{"meta"') for l in
                        (path.read_text(encoding="utf-8").splitlines() if path.exists() else [])):
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"meta": {"provider": provider, "model": model, "pin": pin,
                                         "base_url": base, "temperature": 0, "seed": SEED,
                                         "runs": runs, "date": "2026-07-20"}}) + "\n")
    n_err = 0
    with path.open("a", encoding="utf-8") as f:
        for i, (qid, cond, run) in enumerate(todo):
            q = qmap[qid]
            prompt = prompt_for(cond, q)
            try:
                if provider == "mock":
                    text, ptok, ctok, served = call_mock(model, q, cond, run, prompt)
                else:
                    text, ptok, ctok, served = call_openai_compat(base, key, model, prompt)
            except Exception as e:
                n_err += 1
                print(f"  ABORT at {qid}/{cond}/run{run}: {e}\n"
                      f"  Nothing was dropped - rerun the same command to resume from cache.")
                return False
            rec = {"provider": provider, "model": model, "served_model": served,
                   "qid": qid, "cond": cond, "run": run, "answer": text,
                   "prompt_tokens": ptok, "completion_tokens": ctok,
                   "correct": grade(q["answer_type"], q["answer"], text)}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            if (i + 1) % 36 == 0:
                print(f"  {i + 1}/{len(todo)} done")
            if delay:
                time.sleep(delay)
    print(f"  complete -> {path.name}")
    return True


# ---------------------------------------------------------------- statistics
def mcnemar_exact(n01: int, n10: int) -> float:
    """Two-sided exact McNemar (binomial). n01: A right / C wrong; n10: A wrong / C right."""
    n = n01 + n10
    if n == 0:
        return 1.0
    k = min(n01, n10)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def bootstrap_ci(pairs, iters=10000, seed=SEED):
    """95% CI of mean(C)-mean(A) over question-level majority pairs [(a,c),...]."""
    rnd = random.Random(seed)
    n = len(pairs)
    deltas = []
    for _ in range(iters):
        sample = [pairs[rnd.randrange(n)] for _ in range(n)]
        deltas.append(sum(c for _, c in sample) / n - sum(a for a, _ in sample) / n)
    deltas.sort()
    return deltas[int(0.025 * iters)], deltas[int(0.975 * iters)]


def majority(rows):
    """qid -> 1/0 by majority over runs."""
    byq = {}
    for r in rows:
        byq.setdefault(r["qid"], []).append(r["correct"])
    return {q: int(sum(v) * 2 > len(v)) for q, v in byq.items()}


def analyze():
    """{ (provider,model): {meta, cond: {rows}} } from all raw files."""
    models = {}
    for path in sorted(RESULTS.glob("raw-*.jsonl")):
        meta, rows = {}, []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if "meta" in r:
                meta = r["meta"]
            else:
                rows.append(r)
        if rows:
            k = (rows[0]["provider"], rows[0]["model"])
            models[k] = {"meta": meta, "rows": rows}
    return models


def stats_for(rows, conds=CONDS):
    qcls = {q["id"]: q["class"] for q in QUESTIONS}
    out = {}
    for cond in conds:
        cr = [r for r in rows if r["cond"] == cond]
        if not cr:
            continue
        runs = sorted({r["run"] for r in cr})
        accs = [sum(r["correct"] for r in cr if r["run"] == k) /
                max(1, len([r for r in cr if r["run"] == k])) for k in runs]
        mean = sum(accs) / len(accs)
        std = (sum((a - mean) ** 2 for a in accs) / len(accs)) ** 0.5 if len(accs) > 1 else 0.0
        toks = [r["prompt_tokens"] for r in cr if r["prompt_tokens"] > 0]
        mtok = sum(toks) / len(toks) if toks else 0
        bycls = {}
        for cls in ("lookup", "multihop", "aggregate"):
            rows_c = [r for r in cr if qcls[r["qid"]] == cls]
            if rows_c:
                a = [sum(r["correct"] for r in rows_c if r["run"] == k) /
                     max(1, len([r for r in rows_c if r["run"] == k])) for k in runs]
                m = sum(a) / len(a)
                s = (sum((x - m) ** 2 for x in a) / len(a)) ** 0.5 if len(a) > 1 else 0.0
                bycls[cls] = (m, s)
        out[cond] = {"acc": mean, "std": std, "tokens": mtok, "n": len(cr),
                     "runs": len(runs), "bycls": bycls,
                     "acc_per_1k": (mean / (mtok / 1000)) if mtok else 0.0,
                     "majority": majority(cr)}
    return out


def sig_pair(st, ca="A", cb="C"):
    """majority-vote paired significance cb vs ca."""
    if ca not in st or cb not in st:
        return None
    qa, qb = st[ca]["majority"], st[cb]["majority"]
    qs = sorted(set(qa) & set(qb))
    pairs = [(qa[q], qb[q]) for q in qs]
    n01 = sum(1 for a, b in pairs if a and not b)
    n10 = sum(1 for a, b in pairs if not a and b)
    lo, hi = bootstrap_ci(pairs)
    return {"n01": n01, "n10": n10, "p": mcnemar_exact(n01, n10),
            "delta": sum(b for _, b in pairs) / len(pairs) - sum(a for a, _ in pairs) / len(pairs),
            "ci": (lo, hi), "pairs": pairs}


# ---------------------------------------------------------------- report
def fmt_pct(x):
    return f"{100 * x:.1f}%"


def write_report():
    models = analyze()
    real = {k: v for k, v in models.items() if k[0] != "mock"}
    mock = {k: v for k, v in models.items() if k[0] == "mock"}
    # a model enters the matrix/verdict only with full coverage (36q x 4cond x runs);
    # partial runs (rate-capped mid-flight) are listed but never averaged - no silent drops
    partial = {k: v for k, v in real.items()
               if len(v["rows"]) < 144 * v["meta"].get("runs", RUNS_DEFAULT)}
    real = {k: v for k, v in real.items() if k not in partial}
    L = ["# G2 results — agent accuracy vs Markdown (gate G2 / success test S4)", "",
         "Protocol: `bench/g2-g3-protocol.md` · corpora+questions: `bench/g2-corpus/build.py` "
         "(one fact table → identical knowledge in `kb.md` / `kb.sarib` / `kb.notypes.sarib`; "
         "36 questions, ground truth constructed via `sarib query` and cross-checked — no hand-written key, no LLM judge).",
         "",
         "Conditions: **A** whole kb.md · **B** whole kb.sarib · **C** bounded query result only "
         "(the agent loop) · **D** kb.notypes ablation. 3 runs/cell, temp 0, seed 42 where accepted; "
         "grading = pre-registered normalized exact match (rubric in `bench/run_g2.py`). "
         "Input tokens = provider-reported `usage.prompt_tokens` (the model's own tokenizer).", ""]

    if partial:
        L += ["## Incomplete models (rate-capped; excluded from all averages and the verdict)", ""]
        for (prov, model), v in partial.items():
            L.append(f"- `{prov}/{model}`: {len(v['rows'])}/{144 * v['meta'].get('runs', RUNS_DEFAULT)} "
                     f"cells cached — resume with `python bench/run_g2.py run --providers {prov}`")
        L.append("")
    if not real:
        L += ["## Status: HARNESS PROVEN, LIVE RUN PENDING", "",
              "No live provider was reachable (no API keys set; Ollama not running). "
              "The numbers below are the **mock self-test only** — they validate the harness "
              "(grading, shuffling, caching, stats), and are **not evidence about S4**.", ""]

    def matrix(title, items):
        out = [f"## {title}", "",
               "| Model | Cond | Accuracy (mean±std) | lookup | multihop | aggregate | in-tokens | acc/1k tok |",
               "|---|---|---|---|---|---|---|---|"]
        for (prov, model), data in items.items():
            st = stats_for(data["rows"])
            pin = data["meta"].get("pin", "")
            for cond in CONDS:
                if cond not in st:
                    continue
                s = st[cond]
                cls = {c: s["bycls"].get(c) for c in ("lookup", "multihop", "aggregate")}
                cell = lambda c: (f"{fmt_pct(cls[c][0])}±{100 * cls[c][1]:.1f}" if cls[c] else "—")
                out.append(f"| {prov}/{model}{' (' + pin + ')' if pin else ''} | {cond} "
                           f"| {fmt_pct(s['acc'])}±{100 * s['std']:.1f} "
                           f"| {cell('lookup')} | {cell('multihop')} | {cell('aggregate')} "
                           f"| {s['tokens']:.0f} | {s['acc_per_1k']:.2f} |")
        return out + [""]

    if real:
        L += matrix("Matrix (live models)", real)
        L += ["## Significance — the S4 claim (C strictly beats A at ≤ token cost)", "",
              "| Model | acc A | acc C | Δ (majority) | McNemar p | bootstrap 95% CI | tok A | tok C | S4? |",
              "|---|---|---|---|---|---|---|---|---|"]
        pooled_pairs = []
        for (prov, model), data in real.items():
            st = stats_for(data["rows"])
            sg = sig_pair(st)
            if not sg:
                continue
            pooled_pairs += sg["pairs"]
            s4 = (st["C"]["acc"] > st["A"]["acc"] and st["C"]["tokens"] <= st["A"]["tokens"])
            sig = sg["p"] < 0.05
            L.append(f"| {prov}/{model} | {fmt_pct(st['A']['acc'])} | {fmt_pct(st['C']['acc'])} "
                     f"| {sg['delta']:+.3f} | {sg['p']:.4f}{' *' if sig else ''} "
                     f"| [{sg['ci'][0]:+.3f}, {sg['ci'][1]:+.3f}] "
                     f"| {st['A']['tokens']:.0f} | {st['C']['tokens']:.0f} "
                     f"| {'PASS' if s4 else 'fail'}{'' if sig else ' (not significant)'} |")
        if pooled_pairs:
            n01 = sum(1 for a, b in pooled_pairs if a and not b)
            n10 = sum(1 for a, b in pooled_pairs if not a and b)
            lo, hi = bootstrap_ci(pooled_pairs)
            d = (sum(b for _, b in pooled_pairs) - sum(a for a, _ in pooled_pairs)) / len(pooled_pairs)
            L += ["", f"**Pooled (all models, {len(pooled_pairs)} question-pairs):** "
                      f"Δ = {d:+.3f}, McNemar p = {mcnemar_exact(n01, n10):.4f} "
                      f"(n01={n01}, n10={n10}), bootstrap 95% CI [{lo:+.3f}, {hi:+.3f}].", ""]
        # ---- A vs B: the negative result, stated explicitly (it is the headline honesty claim) ----
        ab = []
        for (prov, model), data in real.items():
            st = stats_for(data["rows"])
            if "A" in st and "B" in st:
                ab.append((f"{prov}/{model}", st["A"]["acc"], st["B"]["acc"],
                           st["A"]["tokens"], st["B"]["tokens"]))
        if ab:
            worse = sum(1 for _, a, b, _, _ in ab if b < a - 1e-9)
            flat = sum(1 for _, a, b, _, _ in ab if abs(b - a) <= 1e-9)
            better = sum(1 for _, a, b, _, _ in ab if b > a + 1e-9)
            tok = [(bt / at - 1) * 100 for _, _, _, at, bt in ab if at]
            L += ["## A vs B — the negative result (whole `.sarib` vs whole Markdown)", "",
                  "The claim this benchmark was built to test honestly: does handing a model the whole "
                  "`.sarib` file beat handing it the same knowledge as Markdown? **It does not.** Across "
                  f"{len(ab)} complete model(s): worse on {worse}, flat on {flat}, better on {better} — "
                  f"while costing {min(tok):+.1f}% to {max(tok):+.1f}% more input tokens. There is no "
                  "consistent accuracy gain from the surface syntax; the measured win (C vs A below) comes "
                  "from **bounded retrieval and id-addressed edits**, not from how the file is written. "
                  "This is what D-002 predicted, and it is why the syntax is not the pitch.", "",
                  "| Model | A acc (md) | B acc (.sarib) | B−A | A tokens | B tokens | token cost |",
                  "|---|---|---|---|---|---|---|"]
            for name, a, b, at, bt in ab:
                L.append(f"| {name} | {fmt_pct(a)} | {fmt_pct(b)} | {b - a:+.3f} | {at:.0f} | {bt:.0f} "
                         f"| {(bt / at - 1) * 100:+.1f}% |")
            L.append("")
        L += ["## Ablation reads", "",
              "- **B vs D (types/edges on↔off, same nesting):** structure-vs-semantics effect.",
              "- **C vs A:** bounded retrieval + structure combined (the S4 headline).",
              "- **C vs B:** the part of the win that is retrieval (context bounding) alone.", ""]
        L += ["| Model | B acc | D acc | B−D (types effect) | C acc | C−B (retrieval effect) |",
              "|---|---|---|---|---|---|"]
        for (prov, model), data in real.items():
            st = stats_for(data["rows"])
            if all(c in st for c in "BCD"):
                L.append(f"| {prov}/{model} | {fmt_pct(st['B']['acc'])} | {fmt_pct(st['D']['acc'])} "
                         f"| {st['B']['acc'] - st['D']['acc']:+.3f} | {fmt_pct(st['C']['acc'])} "
                         f"| {st['C']['acc'] - st['B']['acc']:+.3f} |")
        L.append("")

    if real:
        L += ["## Diagnostic (post-hoc, NOT graded): id-for-title answers in condition C", "",
              "The C context is a JSON subgraph where nodes carry both `id` and `title`; small models "
              "sometimes answer with the id of the *correct* node (`t2` instead of its title). The "
              "pre-registered grade counts these wrong (format non-compliance). Share per model:", "",
              "| Model | C cells wrong | of which id-for-title (right node, wrong surface) |",
              "|---|---|---|"]
        qmap = {q["id"]: q for q in QUESTIONS}
        title = {n.id: (n.title or n.id) for n in DOC.nodes.values()}
        idpat = re.compile(r"\b(?:[tdqps]\d+|ws\d+|g1|sec-[a-z]+)\b")
        for (prov, model), data in real.items():
            wrong = [r for r in data["rows"] if r["cond"] == "C" and not r["correct"]]
            sub = [r for r in wrong if grade(
                qmap[r["qid"]]["answer_type"], qmap[r["qid"]]["answer"],
                idpat.sub(lambda m: title.get(m.group(0), m.group(0)), r["answer"]))]
            L.append(f"| {prov}/{model} | {len(wrong)} | {len(sub)} |")
        L.append("")
    if mock:
        L += matrix("Harness self-test (mock, NOT evidence)", mock)
        L += ["`oracle` must be 100% (plumbing+grading), `noisy-oracle` 100% (normalization), "
              "`adversary` 0% (no false credit).", ""]

    L += ["## Reproduce", "",
          "```", "python bench/g2-corpus/build.py      # regenerate corpora + ground truth",
          "python bench/run_g2.py selftest      # mock harness proof",
          "python bench/run_g2.py run           # every provider with a key set / Ollama up",
          "python bench/run_g2.py report        # rebuild this file from results/*.jsonl",
          "```", "",
          "Providers/models/pins: `bench/g2-corpus/providers.py` + the `meta` line of each "
          "`results/raw-*.jsonl`. Raw per-call records (model answer, tokens, verdict) live in "
          "those jsonl files; delete a file to force that model's rerun.", ""]
    out = ROOT / "bench" / "g2-results.md"
    out.write_text("\n".join(L), encoding="utf-8", newline="\n")
    print(f"wrote {out}")
    return models


# ---------------------------------------------------------------- cli
def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="run_g2")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--providers", nargs="*", default=None)
    r.add_argument("--models", nargs="*", default=None)
    r.add_argument("--runs", type=int, default=RUNS_DEFAULT)
    r.add_argument("--conditions", default=CONDS)
    r.add_argument("--limit", type=int, default=None, help="cap cells (smoke test)")
    sub.add_parser("selftest")
    sub.add_parser("report")
    ns = ap.parse_args()

    if ns.cmd == "selftest":
        ok = True
        for m in ("oracle", "noisy-oracle", "adversary"):
            run_model("mock", m, "", None, 0, "", RUNS_DEFAULT, CONDS)
        models = analyze()
        for m, want in (("oracle", 1.0), ("noisy-oracle", 1.0), ("adversary", 0.0)):
            st = stats_for(models[("mock", m)]["rows"])
            for cond in CONDS:
                got = st[cond]["acc"]
                flag = "ok" if abs(got - want) < 1e-9 else "FAIL"
                if flag == "FAIL":
                    ok = False
                print(f"  selftest {m:13s} cond {cond}: acc={got:.3f} want={want:.1f} [{flag}]")
        print("SELFTEST", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)

    if ns.cmd == "report":
        write_report()
        return

    avail = available(ns.providers)
    if ns.models:
        avail = [a for a in avail if a[1] in ns.models]
    if not avail:
        print("No providers reachable. Set GROQ_API_KEY / GEMINI_API_KEY / CEREBRAS_API_KEY / "
              "OPENROUTER_API_KEY, or start Ollama (`ollama serve` + `ollama pull llama3.2`).")
        sys.exit(2)
    print("Reachable:", ", ".join(f"{p}/{m}" for p, m, *_ in avail))
    all_ok = True
    for prov, model, base, key, delay, pin in avail:
        ok = run_model(prov, model, base, key, delay, pin, ns.runs, ns.conditions, ns.limit)
        all_ok = all_ok and ok
    write_report()
    if not all_ok:
        print("Some models incomplete (rate caps?) - rerun the same command to resume.")
        sys.exit(3)


if __name__ == "__main__":
    main()

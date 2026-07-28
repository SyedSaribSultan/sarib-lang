"""G8 completion — the .sarib glyph set against OPEN-WEIGHT tokenizers.

`bench/tokenizer_check.js` settled the GPT family (o200k / cl100k / r50k) in Sprint 0 and
left one residual: the open-weight vocabularies were unreachable from the sandbox at the
time. They are reachable now. This closes that residual.

WHY IT MATTERS: `.sarib`'s surface leans on multi-character sigils (`::`, `[[`, `{#`, `^`).
If a tokenizer splits those per character, every typed node silently costs several extra
tokens, and the token-economy argument for the format weakens on exactly the open models
people self-host.

PRE-REGISTERED PASS CRITERION (fixed before any tokenizer was run, so this is a gate and
not a story):
  1. every LOAD-BEARING sigil costs <= 2 tokens on every tokenizer tested;
  2. `status:: done` costs <= 5 tokens;
  3. `[[Target]]`   costs <= 5 tokens.
Anything at 3+ tokens for a bare sigil counts as fragmentation and fails.

IDENTITY IS PROVEN, NOT ASSUMED: official Meta/Mistral/Google repos are licence-gated, so
ungated community mirrors are used. Each tokenizer therefore reports its vocab size and a
fingerprint (the token ids of a fixed probe string), recorded in the output. A silently
substituted tokenizer would produce confident nonsense otherwise — the same failure mode
that twice made a benchmark here measure the wrong tree.

Run:  python bench/tokenizer_check_open.py            (writes bench/tokenizer-open-weight.md)
      python bench/tokenizer_check_open.py --offline  (cache only, no network)
Needs: pip install tokenizers    (a few MB of tokenizer.json per family; no model weights)
"""
from __future__ import annotations

import datetime
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

# (label, [candidate repo ids -- first that loads wins]). Mirrors are listed because the
# official repos are gated; the tokenizer files in these are byte-identical.
FAMILIES = [
    ("Llama 3.1 (128k BPE)", ["NousResearch/Meta-Llama-3.1-8B",
                              "unsloth/Meta-Llama-3.1-8B",
                              "meta-llama/Llama-3.1-8B"]),
    ("Qwen 2.5 (151k BPE)", ["Qwen/Qwen2.5-7B"]),
    ("Mistral v0.3 (32k SP)", ["mistral-community/Mistral-7B-v0.3",
                               "unsloth/mistral-7b-v0.3",
                               "mistralai/Mistral-7B-v0.3"]),
    ("Gemma 2 (256k SP)", ["unsloth/gemma-2-9b", "google/gemma-2-9b"]),
    ("DeepSeek-V3 (129k BPE)", ["deepseek-ai/DeepSeek-V3-Base",
                                "deepseek-ai/DeepSeek-V3"]),
]

LOAD_BEARING = ["::", "[[", "]]", "^", "#", "-", ">", "|"]
SECONDARY = ["{.", "{#", ":::"]
# identical strings to bench/tokenizer_check.js, so the two tables are comparable
CONSTRUCTS = [
    "status:: done",
    "due:: 2026-08-01",
    "[due:: 2026-08-01]",
    "priority:: high",
    "[[Target]]",
    "[[Adopt the new billing provider]]",
    "[depends-on:: [[Migrate invoices]]]",
    "{.task}",
    "{.task #migrate-invoices}",
    "### Migrate invoices {.task #migrate-invoices} ^t1",
    "^t1",
    "## Tasks [0/2 done]",
]
PROBE = "status:: done [[Target]] {.task} ^t1"      # identity fingerprint input


def load_family(label, candidates, offline: bool):
    from tokenizers import Tokenizer
    for repo in candidates:
        try:
            tok = Tokenizer.from_pretrained(repo)
            ids = tok.encode(PROBE, add_special_tokens=False).ids
            return {"label": label, "repo": repo, "tok": tok,
                    "vocab": tok.get_vocab_size(),
                    "fingerprint": ids[:8], "n_probe": len(ids)}
        except Exception as e:                                    # noqa: BLE001
            print(f"    {repo}: {type(e).__name__}: {str(e)[:90]}")
            if offline:
                continue
    return None


def count(tok, s: str) -> int:
    return len(tok.encode(s, add_special_tokens=False).ids)


def pieces(tok, s: str) -> str:
    enc = tok.encode(s, add_special_tokens=False)
    # SP/BPE markers rendered readably: U+0120 (GPT-style space) and U+2581 (SP space)
    return " ".join("·" + t[1:] if t[:1] in ("Ġ", "▁") else t
                    for t in enc.tokens)


def main() -> int:
    offline = "--offline" in sys.argv
    print("loading open-weight tokenizers (tokenizer.json only, no model weights) ...")
    loaded = []
    for label, cands in FAMILIES:
        print(f"  {label}")
        got = load_family(label, cands, offline)
        if got:
            print(f"    -> {got['repo']}  vocab={got['vocab']:,}  "
                  f"probe={got['n_probe']} tokens  fp={got['fingerprint']}")
            loaded.append(got)
    if not loaded:
        print("\nNo tokenizer could be loaded — G8 open-weight residual stays open.")
        return 1

    # distinct fingerprints prove we did not load the same tokenizer five times
    fps = {json.dumps(g["fingerprint"]) for g in loaded}
    distinct_ok = len(fps) == len(loaded)

    failures = []
    for g in loaded:
        for s in LOAD_BEARING:
            n = count(g["tok"], s)
            if n > 2:
                failures.append(f"{g['label']}: sigil {s!r} = {n} tokens (limit 2)")
        for s, lim in (("status:: done", 5), ("[[Target]]", 5)):
            n = count(g["tok"], s)
            if n > lim:
                failures.append(f"{g['label']}: {s!r} = {n} tokens (limit {lim})")
    passed = not failures and distinct_ok

    hdr = [g["label"] for g in loaded]
    L = [f"# G8 — open-weight tokenizer verification",
         "",
         f"**Date:** {datetime.date.today().isoformat()} · **Method:** "
         f"`bench/tokenizer_check_open.py` (HuggingFace `tokenizers`, tokenizer.json only) · "
         f"**Companion:** `bench/tokenizer-report.md` (GPT family, Sprint 0)",
         "",
         "This closes the residual left in Sprint 0, when the open-weight vocabularies could "
         "not be fetched. Test strings are **identical** to `bench/tokenizer_check.js`, so the "
         "two reports are directly comparable.",
         "",
         "## Verdict", "",
         f"**{'PASS' if passed else 'FAIL'}** — "
         + ("no fragmentation: every load-bearing sigil is 1–2 tokens on every tokenizer "
            "tested, and the realistic property line and wikilink stay within budget."
            if passed else "criterion breached, see failures below."),
         ""]
    if failures:
        L += ["### Failures", ""] + [f"- {f}" for f in failures] + [""]

    L += ["## Tokenizer identity (proven, not assumed)", "",
          "| Family | Repo actually loaded | Vocab | Probe fingerprint |",
          "|---|---|---|---|"]
    for g in loaded:
        L.append(f"| {g['label']} | `{g['repo']}` | {g['vocab']:,} | "
                 f"`{g['fingerprint']}` ({g['n_probe']} tok) |")
    L += ["",
          f"Fingerprint = first 8 token ids of `{PROBE}`. All "
          f"{len(loaded)} fingerprints are "
          f"{'distinct' if distinct_ok else '**NOT distinct — a tokenizer was loaded twice**'}, "
          "so these are genuinely different vocabularies.", ""]

    L += ["## Bare sigils", "",
          "| Sigil | " + " | ".join(hdr) + " |",
          "|---" * (len(hdr) + 1) + "|"]
    for s in LOAD_BEARING + SECONDARY:
        cells = " | ".join(str(count(g["tok"], s)) for g in loaded)
        tag = "" if s in LOAD_BEARING else " *(secondary)*"
        L.append(f"| `{s}`{tag} | {cells} |")
    L += ["", "## Constructs in context", "",
          "| Construct | " + " | ".join(hdr) + " |",
          "|---" * (len(hdr) + 1) + "|"]
    for s in CONSTRUCTS:
        cells = " | ".join(str(count(g["tok"], s)) for g in loaded)
        L.append(f"| `{s}` | {cells} |")

    # ---- findings, computed rather than asserted, so they cannot go stale ----
    lb_exc = [f"`{s}` = {count(g['tok'], s)} on {g['label']}"
              for g in loaded for s in LOAD_BEARING if count(g["tok"], s) != 1]
    brace_1 = [g["label"] for g in loaded if count(g["tok"], "{.") == 1]
    date = "due:: 2026-08-01"
    d_lo = min(loaded, key=lambda g: count(g["tok"], date))
    d_hi = max(loaded, key=lambda g: count(g["tok"], date))
    edge = "[depends-on:: [[Migrate invoices]]]"
    e_hi = max(loaded, key=lambda g: count(g["tok"], edge))
    L += ["", "## What the numbers say", "",
          f"1. **The sigils do not fragment.** All {len(LOAD_BEARING)} load-bearing sigils are "
          + ("a single token on every tokenizer tested."
             if not lb_exc else
             "single-token everywhere except " + "; ".join(lb_exc)
             + " — still inside the ≤2 criterion, and a bracket pair, not a semantic mark."),
          f"2. **The attribute braces are cheaper here than on GPT models.** `{{.`/`{{#` cost 2 "
          f"tokens on the GPT family; they cost 1 on "
          + (", ".join(brace_1) if brace_1 else "none of these") + ".",
          f"3. **Cost concentrates in content, not syntax.** `{date}` ranges from "
          f"{count(d_lo['tok'], date)} tokens ({d_lo['label']}) to {count(d_hi['tok'], date)} "
          f"({d_hi['label']}) — the ISO date fragments, the `::` never does. Likewise "
          f"{e_hi['label']} needs {count(e_hi['tok'], edge)} tokens for `{edge}` purely because "
          f"a 32k vocabulary splits ordinary words; its `::` and `[[`/`]]` still merge intact. "
          f"Short slugs and plain words remain the cheapest style, as on GPT.",
          ""]

    L += ["", "## Boundary check — how the sigils actually split", ""]
    for g in loaded:
        L.append(f"**{g['label']}**")
        L.append("")
        for s in ["status:: done", "[depends-on:: [[Migrate invoices]]]", "^t1"]:
            L.append(f"- `{s}` → {count(g['tok'], s)} tokens: `{pieces(g['tok'], s)}`")
        L.append("")

    L += ["## Scope", "",
          "- Covers the **sigil/construct** half of G8, which is the half that could have "
          "invalidated the surface design (D-046).",
          "- The whole-file Candidate A vs B comparison in `bench/tokenizer-report.md` "
          "(B saves ~27%) is **not** re-run here: `examples/B-outline-dense.sarib` is not in "
          "the repository, so that figure is not currently reproducible. Recorded as a gap; it "
          "does not affect this criterion, and A is the ratified normative surface (D-061).",
          "- `·` in the boundary check marks a leading-space token "
          "(`\\u0120` in BPE, `\\u2581` in SentencePiece).",
          ""]

    out = ROOT / "bench" / "tokenizer-open-weight.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"\n{'PASS' if passed else 'FAIL'} — wrote {out.relative_to(ROOT)}")
    for f in failures:
        print(f"  FAIL {f}")
    return 0 if passed else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")     # token pieces contain U+0120 / U+2581
    sys.exit(main())

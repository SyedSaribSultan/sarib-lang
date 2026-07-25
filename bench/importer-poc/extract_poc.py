"""Constrained edge-extraction PoC (importer M2 gate rehearsal).

Question: can a WEAK local model (qwen2.5:7b) propose typed edges over a real .sarib
corpus WITHOUT fabricating them, if we constrain it hard? If yes, the safety comes from
the constraints, not the model — which is the whole thesis (research/importer-extraction.md).

Pipeline layers exercised here:
  L1 closed vocab + existing-ids-only : enforced via a JSON-schema `enum` on type AND target
  L2 constrained decoding             : Ollama `format`=schema masks invalid tokens at decode
  L3 span grounding                   : reject any edge whose `span` is not a verbatim quote
  (L4 verify / L5 abstain measured in the report step: precision = correct / surviving)

Source prose : decisions/decision-log.md  (per-decision sections)
Node ids     : dogfood/decision-log.sarib (d-001..d-061)
Extractor    : local Ollama qwen2.5:7b, temperature 0.
Output       : bench/importer-poc/proposals.jsonl  (+ rejects.jsonl)
"""
from __future__ import annotations
import json, re, sys, time, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "decisions" / "decision-log.md"
DOG = ROOT / "dogfood" / "decision-log.sarib"
OUT = pathlib.Path(__file__).resolve().parent
MODEL = "qwen2.5:7b"
VOCAB = ["amends", "supersedes", "cites"]
OLLAMA = "http://localhost:11434/api/chat"

VOCAB_DEF = (
    "amends: the current decision explicitly modifies or refines another decision.\n"
    "supersedes: the current decision explicitly replaces or overrides another decision.\n"
    "cites: the current decision explicitly references another decision as its evidence, "
    "basis, or grounding."
)


def decision_ids():
    return [m.lower() for m in re.findall(r"\^(d-\d+)", DOG.read_text(encoding="utf-8"))]


def sections():
    """Split the source prose into {id, title, text} per decision."""
    txt = SRC.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^## D-(\d+)\b", txt)
    out = []
    # parts = [preamble, num, body, num, body, ...]
    for i in range(1, len(parts), 2):
        num = int(parts[i])
        body = parts[i + 1]
        title = body.splitlines()[0].strip(" ·-\t")
        out.append({"id": f"d-{num:03d}", "title": title, "text": body.strip()})
    return out


def schema(ids):
    return {
        "type": "object",
        "properties": {
            "edges": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": VOCAB},
                        "target": {"type": "string", "enum": ids},
                        "span": {"type": "string"},
                    },
                    "required": ["type", "target", "span"],
                },
            }
        },
        "required": ["edges"],
    }


def ask(section, ids):
    sys_p = (
        "You are a STRICT relationship extractor for a decision log. Output ONLY "
        "relationships EXPLICITLY stated in the provided text. Do NOT infer, guess, or use "
        "outside knowledge. When in doubt, leave it out.\n\n"
        f"Allowed relationship types (use EXACTLY one of these):\n{VOCAB_DEF}\n\n"
        "For every relationship, 'span' MUST be the exact verbatim substring of the text "
        "that states it. 'target' must be the decision id being referred to. If the text "
        "states no relationship to another decision, return an empty list."
    )
    usr = (
        f"Current decision: {section['id']} — {section['title']}\n\n"
        f"Text:\n{section['text']}\n\n"
        "Return JSON {\"edges\":[{\"type\":..,\"target\":\"d-0NN\",\"span\":\"..\"}]}."
    )
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": sys_p}, {"role": "user", "content": usr}],
        "stream": False,
        "format": schema(ids),
        "options": {"temperature": 0, "seed": 42},
    }).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.load(r)
    return json.loads(resp["message"]["content"])


def norm(s):
    return re.sub(r"\s+", " ", s or "").strip().lower()


def main():
    ids = decision_ids()
    idset = set(ids)
    secs = sections()
    print(f"{len(ids)} ids, {len(secs)} decision sections, model={MODEL}", flush=True)
    proposals, rejects = [], []
    for n, sec in enumerate(secs, 1):
        src_norm = norm(sec["text"])
        try:
            res = ask(sec, ids)
        except Exception as e:
            print(f"  [{sec['id']}] ERROR {e!r}", flush=True)
            continue
        for e in res.get("edges", []):
            e = {"source": sec["id"], "type": e.get("type"), "target": e.get("target"),
                 "span": e.get("span", "")}
            # L1/L2 (defense in depth; schema already constrains these)
            if e["type"] not in VOCAB:
                e["reject"] = "bad-type"; rejects.append(e); continue
            if e["target"] not in idset or e["target"] == e["source"]:
                e["reject"] = "bad-target"; rejects.append(e); continue
            # L3 span grounding: the quote must actually be in the source text
            if norm(e["span"]) not in src_norm:
                e["reject"] = "span-not-verbatim"; rejects.append(e); continue
            proposals.append(e)
        print(f"  [{n:2}/{len(secs)}] {sec['id']}: kept {sum(1 for p in proposals if p['source']==sec['id'])}", flush=True)
    (OUT / "proposals.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in proposals), encoding="utf-8")
    (OUT / "rejects.jsonl").write_text(
        "\n".join(json.dumps(p, ensure_ascii=False) for p in rejects), encoding="utf-8")
    print(f"\nDONE: {len(proposals)} surviving proposals, {len(rejects)} auto-rejected "
          f"({sum(1 for r in rejects if r['reject']=='span-not-verbatim')} for fabricated span).")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()

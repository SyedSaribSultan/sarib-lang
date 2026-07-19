# Examples — syntax candidate packages

Phase D has opened (Stage 10), so concrete syntax is now allowed. This folder holds the **two competing author-facing surfaces**, each encoding the *same* knowledge (the "Q3 Planning" graph used throughout the stages) so you can judge them independently.

| File | Candidate | Optimizes | Renders in Markdown tools? |
|---|---|---|---|
| `A-prose-native.sarib` | **A — Prose-native (recommended)** | writability, adoption, formatting | **Yes** (it's a Markdown superset) |
| `B-outline-dense.sarib` | B — Outline-dense | token density, depth-at-a-glance | No (a leaner, non-Markdown outline) |

Both encode the **same knowledge (same nodes and edges)** and normalize to the **same model** (Stage 9) — they are two surfaces over one truth, not two formats. (Byte-identical canonical JSON is not guaranteed across surfaces: A anchors edges inside prose while B uses standalone edge lines, so derived `anchor` metadata can differ. The *knowledge* is identical; the incidental serialization detail need not be.)

## How to judge

Open both. Ask:

1. **Would you rather hand-write this** than the canonical JSON? (If neither, RD6 has bitten.)
2. **Can you feel the shape** — depth, how many tasks, where you are — without reading every line? (spatial legibility, §5)
3. **Does it stay readable** when the type/edge/property marks are present? (writability under structure, RH8)
4. **A only:** paste it into any Markdown viewer — does it still read cleanly, with the extra marks degrading to harmless text?

## The recommendation (Stage 10 §6)

**Candidate A**, augmented with B's spatial cues. Rationale: the priority order is *integrity > human writability > machine efficiency > expressive completeness* — A wins the top three (it renders in every Markdown tool, stays in the LLM pretraining distribution, and is pleasant to write), and closes the density gap through interaction-level efficiency (atomic ops, D-002) rather than surface compression. B is kept as a documented alternative and the basis of a future **compact profile** for token-critical agent-to-agent exchange.

These are illustrative surfaces, not the frozen grammar. The normative artifact is the model (Stages 4–5) and the canonical form (Stage 9); the grammar is specified in Stage 14 and must be tokenizer-verified before freeze (RA11/RP3).

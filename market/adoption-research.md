# Adoption research — the fastest marketable wedge for `.sarib`

*Serves the standardization success-test (adoption), not product-building. This is a
**stance-generating study**, not ratified design: nothing here changes the model, the
spec, or any D-###. It answers one question — "why isn't this flexable/usable in public
yet, and what is the shortest path to changing that?"*

**Method.** A 40-persona simulated user-test across 8 segments (91 agents, 0 errors,
~3.6M tokens). Each persona was given an **honest brief** — including the project's own
falsified claim (whole-file `.sarib` reads *worse* than Markdown, +46% tokens) and the
real onboarding friction (no `pip install`, no importer, clone-a-research-repo) — then
scored adoption, pain, wedge-fit, frictions, and willingness-to-share. A second
**skeptic pass de-biased every score downward** where the persona wouldn't really clear
the friction. **Caveat that bounds every number below: these are LLM-simulated personas,
not real humans.** Treat this as a structured reasoning device and hypothesis generator,
not market validation. Real signal (G3 raters, actual installs) is still owed.

---

## Headline finding

**The *idea* is shareable; the *tool* is not yet adoptable — and the gap is entirely the on-ramp, not the concept.**

- De-biased adoption is **~0 across every segment** (corrected mean **0.53 / 5**; self-reported 1.32 → 0.53 after de-biasing; **9 of 40** evals were flagged as inflated). **Zero personas** scored a corrected adoption ≥ 3.
- Yet **23 of 40 would share it publicly** — but only **2 of those 23** would also adopt it. People would evangelize the *mental model* ("address knowledge by stable id, edit deltas not documents, query bounded subgraphs, keep one canonical value per fact"), explicitly framed as *"interesting research, watch this space,"* **not** *"I run this."*

That split is the answer to your question. The format is flexable **as an idea today**; it is not an easy public utility **because the first 20 minutes are a research-repo obstacle course, and nobody's existing knowledge can get in.**

## The wall, quantified (frictions cited, of 40)

| Friction | Count | Fixable fast? |
|---|---|---|
| No importer / cold-start (my knowledge isn't in `.sarib`) | **40/40** | Partially — the crux (see below) |
| Install/packaging (clone repo, PYTHONPATH, hand-edit MCP JSON) | **37/40** | **Yes — done this session** |
| Unproven on the frontier models the ICP actually runs | 37/40 | No (needs G2 large tier) |
| No GUI / visual tool | 32/40 | Deliberately out of scope |
| Single-author repo, no ecosystem / 2nd implementation | 29/40 | Slow (community) |
| Must maintain a 2nd artifact the agent might let rot | 17/40 | Design risk |
| New syntax surface to learn | 17/40 | Minor |

## Where interest concentrates (best-use-case, of 40)

| Recognized problem | Mentions |
|---|---|
| **U2 — ADR / decisions / risk drift** | **18** |
| **U1 — agent / project memory** | **14** |
| U4 — roadmap/board from one source | 13 |
| "none — not my problem" | 10 |
| U5 runbooks · U6 spec-as-graph · U3 PKB | 3 each |

U2 and U1 bleed into one thing: **a canonical, agent-queryable memory of project facts
and decisions that doesn't silently disagree with itself** — the FitSmart
"premium-source-of-truth" pain, generalized. That is the wedge.

## Segment scan (de-biased)

| Segment | n | corrected adopt | wedge-fit | share% | read |
|---|---|---|---|---|---|
| ai-builders | 7 | 0.71 | **2.71** | 71% | Highest wedge-fit + share. The ICP — but only the *solo, self-provisioning* ones. |
| enterprise | 4 | **1.0** | 1.5 | 75% | Highest adopt/share, but wrong buyer for a solo unfunded repo (procurement, security review, wants Backstage/CI bridges). |
| engineers | 6 | 0.5 | 2.5 | 50% | Warm to ADR/decision drift; team hand-off kills it. |
| tech-knowledge | 5 | 0.6 | 2.0 | 60% | Want lossless Obsidian/docs bridges that don't exist. |
| pkm | 5 | 0.4 | 1.6 | 60% | Vaults too big; want two-way sync; poor fit. |
| founders | 5 | 0.4 | 2.2 | 40% | Real pain, but too busy shipping to maintain a graph. |
| skeptics | 4 | 0.25 | 2.25 | 75% | "Get" the idea, won't touch v0.1 — but would *talk* about it. |
| nontech | 4 | 0.25 | 0.75 | 25% | Confirmed not for them. Correct to ignore. |

---

## Decision: the wedge

**ICP (one):** the **solo, AI-heavy builder** — one person, one repo, Claude Code /
Cursor + MCP open all day, runs a CLI unaided, no team to convince, no client hand-back,
no security review. *Single-player* and *self-provisioning* are the two invariants a
solo maintainer can actually win.

**Problem (one):** *Your coding agent works from stale, self-contradicting project
context. The same fact — what "premium" means, a pricing tier, an architecture invariant
— is restated across `CLAUDE.md`, `.cursorrules`, and scattered notes; they silently
disagree; the agent confidently rebuilds what you already changed.*

**Explicitly rejected:** enterprise (wrong buyer for a solo repo), PKM/Obsidian
(want two-way sync we won't build), non-technical (confirmed dead), and any team/hand-off
story (breaks the self-provisioning invariant).

## Positioning (hold the launch behind M2 — see below)

> **`.sarib` is a queryable memory for your coding agent: store each project fact once,
> edit it as a one-line delta, and let the agent pull the exact subgraph it needs instead
> of re-reading the whole file.**

Sell the **architecture** (measured, model-independent). Never the **surface**.

| Claim | Status |
|---|---|
| "Every mention is an edge to one node, so facts can't silently disagree" | ✅ **The headline — uncontestable.** |
| "One fact = one id-addressed, typed delta" (vs. document regeneration; concede targeted string-edit as the honest baseline) | ✅ Defensible if framed as *addressable + typed*, not a bare "200×". |
| "Agent fetches the subgraph it asks for" (state the benchmark is thin: 36 q, p=0.065; win shrinks on large-context models) | ⚠️ Defensible only with the caveats attached. |
| "AI-native syntax / reads better for AI" · "+28 accuracy points" · bare "200× / 29×" | ⛔ **Banned** — falsified or unsupported by our own data. |

The published *negative* results are the credibility engine. Keep them visible.

---

## The fast plan (mapped to the 6 work items) — split M1 / M2

The one reframing that matters, forced by the board-critique: **the importer is not
packaging, it is the whole bet, and it splits in two.** Its easy half is scaffolding;
its hard half is the gate.

**M1 — ship now, sold honestly as "a starter graph you finish by hand":**
1. **(item 2) `pip` / `uvx` packaging** — ✅ **DONE this session.** `pip install sarib`,
   `sarib` + `sarib-mcp` console scripts, zero-dep core, `mcp` optional extra. Removes the
   most-cited fixable friction (37/40).
2. **(item 4a) heading-level importer** — `sarib import ./CLAUDE.md ./.cursorrules ./docs`
   → a containment *starter* graph, labeled **"edges added by you," never sold as canonical.**
3. **(item 3) killer recipe** — one copy-paste page: import → wire MCP → ask "what is the
   canonical definition of premium?" → edit one node. Ships *with* the importer; neither works alone.
4. **(item 6) visible dogfooding** — run this repo's `decision-log.sarib` /
   `risk-register.sarib` as real working memory, in public. Doubles as the M2 test harness.
5. **(item 1) README** — retitle *"Give your coding agent a memory that doesn't drift,"*
   lead with the U1 recipe + the canonical-fact proof point + one honest "what it is not"
   paragraph. **Hold the wedge announcement + every "canonical graph" claim behind M2.**

**M2 — the gate (blocks the go-to-market narrative):**
6. **(item 4b) semantic edge-extraction** proven on our own dogfood to beat the current
   **2-edge baseline** by a *pre-stated* edge-density + correctness margin — **without**
   violating the integrity priority (determinism / losslessness). If a deterministic
   extractor can't clear the margin, the honest product is *"assisted authoring,"* not
   *"canonical source of truth"* — and we say so.

**DROP:** (item 5) the full hosted-preview build — it serves the browser-living personas
we deliberately ignore. Keep only a **static, zero-backend "see the graph render" link**
(cheapest fuel for the share engine) — but it must not jump the queue ahead of the
importer, and it's meaningless until M2 gives it a real graph to show.

## Top 3 risks

1. **The importer can't extract real edges deterministically.** The easy build = a
   value-free containment tree (confirms every skeptic); the hard build = months,
   non-deterministic, and collides head-on with *integrity > everything*. **This is the
   project's crux, not a chore.** Kill-signal: if deterministic extraction can't clear a
   pre-stated margin, reposition to "assisted authoring."
2. **The wedge selects for the lowest-drift environment.** Single-player + single-repo
   *minimizes* authors × surfaces; the pain is "an hour a week" — vitamin-adjacent against
   a v0.1 format + hand-wired MCP + a graph to maintain. Measure in dogfood whether the
   graph stays current and whether the agent routes through MCP vs. reading whole-file
   (+46% tokens). If edges rot, the value evaporates.
3. **"Share the idea" ≠ "run the tool."** 23/40 would share; 2 would adopt. The whole
   earned-distribution story rests on converting concept-evangelism into installs — asserted,
   not evidenced. The 60-second try-it (M1 pip + importer + recipe) is the only lever;
   instrument installs-from-shares and treat a null result as "research, not market."

## What this does NOT change

The design arc, the spec, the model, and every ratified D-### stand. This study is about
*packaging and reaching* the standard, which the charter's success test explicitly
includes (a conforming parser is a weekend's work; adoption is a stated goal). It does not
propose author-facing syntax changes, does not touch the semantic core, and does not
relax any integrity invariant — indeed the M2 gate exists precisely to protect
determinism/losslessness against a tempting LLM-extraction shortcut.

## Provenance

Simulated 40-persona study, run 2026-07-25 via a 4-phase multi-agent workflow
(generate → evaluate → skeptic-de-bias → synthesize + board-critique). Raw persona data,
the strategist's brief, the board critique, and the reconciled final plan are the study's
artifacts. Simulated personas are a reasoning aid; real-rater validation (G3) remains owed.

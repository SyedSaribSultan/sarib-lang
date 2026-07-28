# CLAUDE.md — operating instructions for the .sarib project

Read this first, every session. It is the anchor that keeps each run linear to the goal. It holds only invariants — mission, discipline, and where to look. Live state (what's done, what's next) lives in `HISTORY.md`'s session log, not here (it was `README.md` before the public swap; `README.md` is now the public front door). Keep this file under ~120 lines; prefer pointers over copies; edit it only when a new invariant emerges or observed drift needs a guardrail.

## North star — do not drift from this

**Mission.** Design an open standard: a plain-text, AI-native knowledge representation language (`.sarib`) that is one canonical semantic source of truth — read/written by humans as naturally as an outline, edited by agents as precisely as a database — from which documents, graphs, boards, timelines, and context windows are all generated projections.

**The vision, in three lines** (every design choice serves these):
- Store knowledge once; render it infinitely.
- Touch knowledge atomically; never regenerate what you can address.
- Semantics are canonical; syntax and every view are projections.

**Success test** (falsifiable; S1–S6 in `stages/01-vision-and-philosophy.md` §5, S7–S8 in `stages/02-prior-art.md` §6, retrospective in `stages/15-v1.0-proposal.md` §7): humans and agents interact with the same knowledge without format translation; a point edit costs a delta, not a regeneration; a conforming parser is a weekend's work; it reads as plain text and queries as a graph.

**This is not** a note app, PKM tool, Markdown alternative, or SaaS. No product ships. If a task starts optimizing a UI or an app, stop — that is drift.

## Resume protocol — start every session here

1. Read `HISTORY.md` → the **session log**'s latest row gives current phase/stage and the exact **"Next session"** entry point. Continue from there.
2. Skim `00-charter.md` (rules + phase map), the tail of `decisions/decision-log.md` (recent D-###), and `risks/risk-register.md` §1 (existential watch list).
3. Use the file map below to pull deeper context on demand — don't preload everything.

## Operating rules (invariant; detail in `00-charter.md` §Operating rules)

- **Critique-first.** Open every stage by critiquing its predecessor; log accepted amendments. Never assume the first design is right.
- **Log decisions.** Record each design choice as `D-###` in the decision log with context, choice, and a **reversal condition**. Amend, never silently overwrite.
- **Semantics before surface.** Keep syntax for Phase D (Stage 10). Before then, work the model/semantics; treat any concrete file syntax as an explicitly-labeled thought experiment only.
- **Evidence rule.** Cite a primary source (in `research/`) for every factual claim; label opinions as stances with reversal conditions. Prefer measuring over asserting — especially anything called "efficient" (benchmark before spec freeze).
- **Kill-criterion.** If an existing stack (JSON-LD profile, property-graph text form, org-mode…) would satisfy ≥90% of ratified requirements, prefer profiling/binding it over inventing. Inventing is the last resort.
- **Keep the core small.** New capability must justify itself against the business-card grammar budget; when in doubt, push it to vocabulary/extension, not the core.

## Priority ordering — the tie-breaker when principles conflict

**integrity > human writability > machine efficiency > expressive completeness.**
Cut completeness and ceremony freely; never cut determinism, losslessness, safety, or the extension mechanism (those cannot be patched later). Detail: `stages/03-design-principles.md` §4.

## Drift self-check — run before finalizing any stage or substantive response

1. **Goal-linear?** Does this serve the north star, or is it scope creep / product-building?
2. **Priority-ordered?** If it adds capability, did it pass the priority rule (justified vs. the small-core budget)?
3. **Critique-first?** Did this stage open by critiquing its predecessor?
4. **Evidence-bound?** Every fact cited; every design choice traced to a principle (P#) or decision (D-###)?
5. **Logged?** New decisions recorded as `D-###` with reversal conditions?
6. **Integrity intact?** Nothing traded determinism / losslessness / safety / mergeability for cleverness or brevity?
7. **Risk-aware?** Did this touch or surface a risk? Update `risks/risk-register.md`; keep the existential watch list (§1) in view.
8. **Verified & handed off?** Ran a consistency + citation check; updated the HISTORY.md session log and the next-step pointer.
9. **Well-formed reply?** Led with the answer, concise, tables for tradeoffs, no filler (Sarib's prefs).

## Red lines (the few hard nevers)

- No author-facing file syntax proposed before Phase D.
- No unsourced factual claim about prior systems.
- No destructive deletion in the model — retraction only (P12); `compact` is the sole explicit exception.
- No positional addressing (line/offset/index) in edges or operations — ids only (P13/D-033/D-036).

## Quality bar — state-of-the-art engineering practice

- **Verify before "done."** Cross-check internal consistency and citations each stage; for high-stakes work, verify with a subagent. A stage isn't finished until its successor could critique it without finding a broken reference.
- **No gate may be validated only at toy scale.** Every programmatic gate passed while the reference impl was quadratic, because the largest artifact any of them measured was 301 nodes (G9/D-062 exists because of this). When asserting a property, ask at what size it was checked. And when a refactor replaces something that *incidentally* supplies ordering or identity, pin the observable behaviour first (`impl/tests/run_golden.py`) — otherwise a correctness regression arrives disguised as a performance change.
- **Determinism & losslessness are non-negotiable.** One canonical normal form; projections may hide fields but never silently drop them.
- **Self-hosting consistency.** Schemas, queries, and (where sensible) operations are expressed in `.sarib` itself; keep the model self-describing.
- **Traceability.** Every principle traces to evidence; every decision to a principle; every stage critiques the last. Preserve that chain.
- **Reproducibility of process.** Persist everything to the repo so any session (or the Monday check-in) resumes from files alone, never from chat memory.

## How to answer Sarib (response style)

Lead with the answer, then support it. Truth-density over volume; causal precision, tradeoffs, second-order effects. Tables for any comparison/decision. Tight headers, short paragraphs, minimal bold. State senior-level assumptions in one italic line when completing gaps. No filler preambles or closing fluff. Full profile: user preferences.

## File map (progressive disclosure — pull on demand)

| Need | Go to |
|---|---|
| Where we are / next step | `HISTORY.md` → session log |
| Mission, rules, phase map, exit criteria | `00-charter.md` |
| Vision, tensions, success tests | `stages/01-vision-and-philosophy.md` |
| Prior-art evidence (cited) | `research/*.md` (index in `research/README.md`) |
| Ratified principles P1–P17 + priority order | `stages/03-design-principles.md` |
| The model, semantics, traversal, query | `stages/04…07-*.md` |
| Operation vocabulary / serialization | `stages/08…09-*.md` |
| Every decision + reversal condition | `decisions/decision-log.md` (D-001…) |
| Every risk + status + early-warning | `risks/risk-register.md` (watch list in §1) |
| Engineering plans (WPs + acceptance criteria) | `plans/` |
| Measured gate + scale results | `bench/gate-report.md`, `bench/scale-report.md` |

If this file and a stage document ever disagree, the stage + decision log win — then fix this file.

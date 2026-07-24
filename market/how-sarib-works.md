# How .sarib works — a general explainer with a sample flow

*General-audience technical explainer. Claims tie to measured gates (G1 edit economy, G2
retrieval); semantics reflect the ratified model (Stages 4–9, D-015…D-044).*

---

**What it is.** `.sarib` is a plain-text format that is two things in the same file at once:
a document a person reads top to bottom, and a graph of facts a machine can query and edit
precisely. You don't pick one or the other — the same bytes are both.

**The core idea (the semantics).** Underneath, everything is one graph. A *node* is any
meaningful unit — a heading, a task, a decision, a paragraph. Each node has four things: a
**stable id** (opaque, and it survives renaming or moving the node), some **content** (the
text you wrote), optional **properties** (`key:: value` facts like `status:: todo`), and
optional **typed edges** to other nodes (like `depends-on` or `owner`). The document you read
is simply this graph's *containment tree* — the nesting of headings and blocks — walked in
order. So the outline you see and the graph the machine sees aren't two copies kept in sync;
they are literally the same structure viewed two ways.

Two properties of the model matter most:

- **Progressive typing.** Plain prose is already valid `.sarib` — zero marks required. You add
  a type or an edge only where structure earns its keep. Nothing forces you to annotate
  everything up front.
- **Deterministic resolution — it never guesses.** When you link `[[Adopt Stripe]]`, the
  resolver follows a fixed order (explicit id → nearest match in the containment →
  document-wide → vocabulary → *unresolved*). If it's ambiguous, it stays unresolved and
  renders as plain text with a lint note — it will *never* silently link the wrong thing. That
  "never guess" rule is what lets you trust the graph.

**A sample flow.** Say you jot this:

```
# Billing revamp

## Migrate invoices {.task} ^t1
status:: todo
owner:: [[Alice]]
Blocked until we [depends-on:: [[Adopt Stripe]]].

## Adopt Stripe {.decision} ^d1
status:: accepted
```

To you it's a readable outline. To a machine it's: node `t1` (a *task*; `status` = todo; an
`owner` edge to Alice; a `depends-on` edge to `d1`) and node `d1` (a *decision*; `status` =
accepted). Now the loop that makes it useful:

1. **Read a slice, not the file.** An agent asks "what's blocking `t1`?" It runs a bounded
   query that walks the `depends-on` edge and gets back a tiny subgraph — just
   `d1: Adopt Stripe, status accepted` — carrying real ids. It never ingests the whole
   document.
2. **Reason.** The blocker is `accepted`, so `t1` can start.
3. **Edit atomically, by id.** The agent applies one operation — `set-property t1 status =
   doing` — about a dozen tokens, not a regeneration of the file. It's *guarded* ("I expect
   status to still be `todo`"), so if something changed underneath, the edit is safely
   rejected instead of clobbering. And the change is logged, not destructive — the operation
   history is kept, so you can see or revert it.
4. **Project.** From that one updated source, every view regenerates for free: the document
   (prose), a kanban board (grouped by `status`), a dependency graph (`t1 → d1`), a timeline,
   or a minimal context window for the next agent. No view holds its own copy; each is a
   query plus a template.

**Why it's built this way.** Three principles drive all of it: store knowledge once and
render it infinitely; touch it atomically and never regenerate what you can address; keep the
*semantics* canonical and treat every surface — syntax, board, graph, even the AI's context
window — as a projection of it. The honest, measured payoff lives in that read-query-edit
loop: a point edit costs a fraction of a percent of rewriting the document (measured ~0.5%,
about 200×), and answering from a bounded slice costs roughly a third of the tokens of dumping
the whole file. The value is the architecture — not a fancy syntax.

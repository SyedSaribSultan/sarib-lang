# Pitch — .sarib for an AI-first ed-tech CEO

*Reusable. Swap [Name]. Every claim here is backed by a measured gate (G1/G2) or stated as
status — no overclaim, so it survives technical scrutiny.*

---

Hi [Name],

Here's the short version of what I've been building and why I think it's relevant to you
specifically.

**The problem.** Every AI-first product accumulates a pile of structured knowledge — in your
case curricula, learning objectives, standards alignments, prerequisite maps, content
metadata, student mastery models. Two things quietly hurt. First, the same fact gets copied
into many places — a curriculum doc, content metadata, the tutor's prompt, your analytics —
and slowly drifts out of sync, so the content says one thing while the tutor believes
another. Second, your AI agents keep shoving whole documents into context to answer one small
question, or regenerating an entire profile just to change one field. The first problem costs
correctness; the second costs money on every call.

**The idea.** `.sarib` is a plain-text format that is two things at once: a document a human
reads top-to-bottom (it looks like Markdown), and, underneath, a graph of identified facts
and typed connections. Because every fact carries a stable id, a human edits it like an
outline and an AI edits it like a database — with no translation layer between them.

**What that buys you, concretely:**

- **One source of truth, many views.** A learning objective is defined once; every lesson,
  assessment item, and the tutor's context references it by id. Change it in one place and the
  document, the prerequisite graph, the planning board, and the agent's context window all
  follow. No more "the content says X but the tutor thinks Y."

- **Agents work in slices, not whole files.** Instead of feeding the full curriculum to a
  tutor to decide "what should this student do next," the agent queries the exact subgraph it
  needs. In my benchmarks that used about a third of the input tokens for the same answers —
  and on smaller, cheaper models it also raised accuracy. At the scale you run agents, that's
  a direct line-item saving and lower latency.

- **Precise, reversible edits.** When an agent records "student mastered fractions," it
  changes one node by id — I measured that at roughly 0.5% of the cost of regenerating the
  document (about 200× cheaper). Edits are reversible and stay consistent even when several
  services write at once.

**Status, honestly.** It's an open standard with a working reference implementation, MIT
-licensed — not a SaaS I'm trying to sell you. It already runs as an MCP server, so an agent
in Claude, Cursor, or your own stack can query and edit `.sarib` knowledge today. The real,
measured advantage is this query-and-edit *architecture* — not any claim that "AI reads the
syntax better." I tested that specific claim and it doesn't hold, so I don't pitch it.

If it's useful, the fastest way to feel it is to point an agent at a small slice of your
curriculum expressed as `.sarib` and watch it answer and edit against a bounded graph instead
of a wall of text. Happy to walk you through it.

— Sarib

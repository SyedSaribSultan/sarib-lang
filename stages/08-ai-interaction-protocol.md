# Stage 8 — AI Interaction Protocol (Operation Vocabulary)

**Status:** Draft v0.1 — open for critique by Stage 9 · **Date:** 2026-07-15
**Input:** Stage 7 (Query Model) §12 brief; principles P1–P17; decisions D-001…D-034
**Decisions logged:** D-035 … D-039 (this stage)
**Phase:** C (Machine Interface), stage 1 of 2 — Phase C opens.
**Scope guard:** Stage 8 defines the *operation vocabulary* — the atomic edits that are the canonical unit of change (P11) and the token-efficiency engine (D-002) — plus their concurrency, convergence, and op-log↔state semantics. It does **not** define the byte/canonical serialization (Stage 9) or syntax (Stage 10). Operations are described as abstract data; no file syntax.

This is the stage that turns the founding vision — *"touch knowledge atomically; never regenerate what you can address"* — from a slogan into a mechanism.

---

## 1. Critique of Stage 7

Stage 7 built the read/write bridge but left the write side entirely undefined. Four things it assumed that Stage 8 must actually deliver.

**C1 — Stage 7 asserted "operations cost tens of tokens" without an operation.** The whole efficiency thesis (D-002) rests on the op shape being O(change), not O(document). Stage 8 must define that shape and show the economy concretely (§2, §10), or the thesis is unproven.

**C2 — RM17 (lost update) was flagged, not solved.** Stage 7 said "Stage 8 must nail this." The read→reason→write loop has a race: the graph moves between query and edit. Unsolved, the bridge silently corrupts data. Stage 8 must give the concurrency guard (§7, D-038).

**C3 — Nothing guaranteed the op set preserves the 10 invariants (RM14).** Stage 4 §11 listed invariants (single home, no dangling edges, …); an arbitrary edit can violate them. The op set must be *closed* under the invariants — every op takes a valid model to a valid model (§3, D-035).

**C4 — Stage 4 promised identity survival across merge/split (§4) with no operation to perform them.** Stage 8 must supply merge/split/promote/demote and show they honor those identity guarantees (§4).

No principle reversed. Stage 8 is where the abstract machine gets a motor.

---

## 2. The operation as the unit of change

Per P11 (ops canonical, state a fold) and D-002 (optimize tokens-per-interaction), the operation — not the document — is what agents emit. An operation is transport-agnostic **data**:

```
Op = (
  id:          Identity          // the op's own id
  ts:          Lamport           // (replica, counter) — ordering & tie-break (D-014)
  kind:        <one of the op kinds below>
  target:      Identity | [Identity]   // node/edge id(s); absent for create-node (mints new)
  args:        { … }             // kind-specific payload
  expect:      Precondition?     // optimistic-concurrency guard (§7, D-038)
  provenance:  Provenance?       // who/what/basis; default = owner (D-019)
)
```

Every op names its targets by **id** (from a query result, D-033) — never a position (P13). Its cost is proportional to `args` (the change), not to the document. That single property is the efficiency thesis.

---

## 3. The primitive operation set (D-035)

Eight primitives. This set is **complete** (every reachable model state is constructible) and **closed under the 10 invariants** (Stage 4 §11) — each op is specified to take a valid model to a valid model, resolving RM14.

| # | Primitive | Effect | Invariant care |
|---|---|---|---|
| 1 | `create-node` | mint a new node (new id, optional type/content) **with its home containment edge** (parent + order) | guarantees single-home from birth (inv. 2); default home = reserved entity container if unspecified (Stage 4 §6) |
| 2 | `retract-node` | set node `status = retracted` (P12) | incident edges become dormant, not dangling (inv. 3); never destroys (inv. 8) |
| 3 | `set-content` | replace a node's inline content | content is self-contained per node; intra-node splicing deferred (RM4/§13) |
| 4 | `set-property` | set `key = value` on a **node or edge** | value-typed per Stage 5 §4 |
| 5 | `unset-property` | remove a property key from a node/edge | — |
| 6 | `add-edge` | create a typed edge (family, source, target, props) | endpoints must exist (inv. 3); a `containment` add is only legal via `move`/`create-node` to preserve single-home |
| 7 | `retract-edge` | set edge `status = retracted` (P12) | for a containment edge, only legal as part of `move` (never orphan a node) |
| 8 | `move` | retarget a node's home containment edge (new parent + order) | atomic retract-old-home + add-new-home, preserving single-home (inv. 2) and id (Stage 4 §4) |

Two closure rules make the set safe:

- **Containment is never edited by raw `add-edge`/`retract-edge`.** The single-home invariant (inv. 2) is protected by routing all containment changes through `create-node` (birth) and `move` (rehoming). Raw edge ops act only on cross-reference edges.
- **Nothing destroys.** Retraction is a status flag (P12); the only destructive operation is `compact` (§4), which is explicit and separate.

Tagging and reordering need no new primitives: **tag = `add-edge`** (type `tag` to a concept), **reorder = `move`** (same parent, new order). Fewer ops, per priority rule 4.

---

## 4. Composite operations and compaction

**Composite ops are atomic macros** — named, single-step-to-the-caller edits that expand to a sequence of primitives. They exist for token economy (one op, not five) and atomicity (all-or-nothing), while keeping the *primitive* core small (S6). Each is defined by its primitive expansion, so the core stays eight.

| Composite | Primitive expansion | Honors |
|---|---|---|
| `merge(A→B)` | retract-node A · add-edge `merged-into` A→B · re-source A's inbound cross-ref edges to B | Stage 4 §4 merge row; P12 (A retracted, not destroyed); inbound refs resolve through the lineage edge |
| `split(A→A,B)` | create-node B · move selected children/edges to B · set-property `split-from` on B → A | Stage 4 §4 split row; A keeps its id |
| `promote(span→node)` | create-node from an inline span · replace the span with an inline reference · add the derived edge | Stage 4 §3.1; the granularity valve (RM2) |
| `demote(node→span)` | inline the node's content into its sole referencer · retract the node | inverse of promote; GC for churn (RM3) |

**Compaction** is the one destructive operation, deliberately outside the normal vocabulary:

- `compact` — physically remove `retracted` objects older than a chosen horizon. Explicit, administrative, never implied by `retract` (P12). It is the only op that loses history, so it is opt-in and separable (a maintenance action, not an edit).

---

## 5. Addressing (D-036)

Every op addresses its targets by **id**, and the only source of ids is a query result (D-033). `create-node` mints a new id (collision-free `(replica,counter)`/ULID, D-014). No op ever references a line, offset, or array index (P13) — the property that makes ops survive concurrent edits (§6) and makes the read→write loop safe.

This closes the addressing story end to end: **query returns ids → ops consume ids → new nodes mint ids → next query returns them.** Positions never enter the loop.

---

## 6. Convergence by design (D-037)

The op set is engineered so that **concurrent operations commute**, giving Strong Eventual Consistency (SEC): any two replicas that have seen the same set of ops fold to the same state, with no central server (D-014; Shapiro et al., [versioning-and-merge.md §3](../research/versioning-and-merge.md)). Each op kind is assigned a convergent semantics:

| Op class | Convergence semantics | CRDT analogue |
|---|---|---|
| `create-node`, `add-edge` | additive — union into a grow-set | G-Set |
| `retract-node`, `retract-edge` | status flag — union into a retracted-set | 2P-Set (retract wins) |
| `set-property`, `set-content`, `move` | last-writer-wins per (target, field), Lamport-ts tie-break | LWW-Register |
| `set-property` on a `list<>` value | optional add/remove-wins set semantics per element | OR-Set (opt-in) |

**The fold (state = f(op-set)):** partition ops by (target, field); for LWW fields take the max-`ts` op; for additive/status classes take set unions; a node/edge is *visible* iff created and not retracted. Because union, max, and idempotent set membership are all commutative-associative-idempotent, **the fold is order-independent** — replaying the same op-set in any order yields the same state (the SEC guarantee). This is the formal discharge of D-014's "concurrent ops commute → server-free merge," and it is why `.sarib` can target clean git 3-way merges now and a live CRDT layer later *without changing the model* (T7).

**v1 honesty (RM18):** `set-content` and `move` are per-target LWW, so two concurrent edits to the *same* node's content converge but the loser is silently dropped. This is safe (convergent) but lossy. Finer intra-node text merge (per-character identity) is deferred (RM4) — v1 keeps nodes block-sized so the blast radius of an LWW loss is one block, and the precondition guard (§7) lets a caller opt into detecting the conflict instead of losing silently.

---

## 7. Optimistic concurrency — solving RM17 (D-038)

Convergence (§6) guarantees replicas *agree*, but the default LWW path can silently lose a concurrent edit (RM18) — unacceptable for edits that must not clobber. So every op may carry an **`expect` precondition**:

- `expect(target, version = v)` — apply only if the target is still at version `v` (each node/edge carries a version = its last op's Lamport counter).
- `expect(target, field OP value)` — apply only if a property/status still holds (the JSON Patch `test`-op pattern, [RFC 6902](https://www.rfc-editor.org/rfc/rfc6902)).

If the precondition fails, the op is **rejected, not applied**, and the caller re-queries and retries. This gives two explicit modes:

| Mode | Behavior | Use |
|---|---|---|
| **Unguarded** (no `expect`) | always applies; LWW converges | fire-and-forget enrichment, non-conflicting edits |
| **Guarded** (`expect …`) | check-and-set; stale write rejected | edits that must not lose a concurrent change |

This directly resolves RM17: the read→reason→write loop (Stage 7 §8) uses a guarded op when correctness matters — the version seen at query time becomes the precondition at write time, so a stale write fails loudly instead of clobbering. The choice of mode is the caller's, per edit.

---

## 8. Op-log ↔ state (P11; Phase C exit criterion)

The **op-log is the canonical journal**; **state is a fold over it** (§6) — event sourcing / Datomic's "database as a value" realized ([versioning-and-merge.md §7–8](../research/versioning-and-merge.md)):

- **Complete rebuild** — discard state, refold the op-log → identical state (order-independent, §6).
- **Temporal query** — fold ops with `ts ≤ T` → the state as of time T (D-019's assertion-time made queryable).
- **Equivalence** — because the fold is a deterministic function of the op-*set*, `state = fold(ops)` and `ops` are two views of one truth; the log can regenerate the state and (with a canonical serialization, Stage 9) the state can be re-expressed as a minimal op-log. Full byte-level demonstration of op-log↔state equivalence is completed in Stage 9 (it needs the canonical form); Stage 8 establishes the semantic equivalence.

This also gives the file-as-truth stance its safety net (register RM8): if a live store is ever needed for throughput, the file becomes an append-only op-log + snapshot with no model change — the fallback D-016/P11 pre-paid for.

---

## 9. Transport-agnostic shape (D-035 corollary)

An op is data (§2), so it rides any channel without reshaping:

- as an **MCP tool call** (the agent-native path): each primitive/composite is a tool; args are the op payload;
- as a **patch file / op-log append** (the git-native path): ops appended to a log, folded on read;
- as an **in-memory edit** (the editor path): the same op applied to a loaded model.

Because ops are self-hosted-expressible (an op *is* describable as a small record, like a query node D-030), the same vocabulary serves human tools, agent runtimes, and sync layers. One protocol, many transports — the adoption-carrier logic (P6) applied to the write path.

---

## 10. Token economy — the thesis made concrete (C1)

The founding claim (D-002, S2) is that editing by operation is orders of magnitude cheaper than regeneration. Concretely, marking one task done in a ~10,000-token knowledge base:

| Approach | What's emitted | Rough cost |
|---|---|---|
| Regenerate the document | the whole edited file | ~10,000 tokens *(estimate)* |
| `set-content` the node | one block's content | ~size of one block, e.g. ~50 tokens |
| `set-property(n5, status, done)` | one op: kind + id + key + value | ~a dozen tokens |

Two-to-three orders of magnitude, and it is *syntax-independent* — it comes from addressing (D-033) plus atomic ops, exactly as Stage 1 C2 argued. The read side is equally lean: the agent queried only `n5`'s id + snippet (Stage 7 §5), not the document. **These numbers are estimates; the benchmark harness (Rule 6, register RP3) must measure them before spec freeze** — but the mechanism that produces the win is now fully specified.

---

## 11. Worked example — the edit loop (over the Stage 4 graph)

Graph recap: tasks n5 (Migrate invoices), n6 (Notify customers); `n6 depends-on n5`, `n5 depends-on n3`; two duplicate concepts c1 (billing), c9 (Billing).

1. **Query** (Stage 7): "open tasks" → returns `[n5, n6]` with ids + snippets (~cheap).
2. **Operate** — mark n5 done, guarded against a concurrent change:
   `set-property(target=n5, key=status, value=done, expect(n5, version=7), provenance=asserted)`
   → applies iff n5 is still at version 7; else rejected, re-query (§7).
3. **Operate** — dedupe the concepts: `merge(c9 → c1)` → c9 retracted, `merged-into c9→c1` added, c9's inbound `tag` edges re-sourced to c1 (§4). Every node that was tagged "Billing" now resolves to the one billing concept; no reference breaks (ids, Stage 4 §4).
4. **Re-query**: "open tasks" now returns `[n6]`; "billing concept" resolves uniquely.

Total emitted across the two edits: a few dozen tokens. No document was re-read or regenerated. This loop *is* the AI-native protocol.

---

## 12. New decisions

Full entries in `../decisions/decision-log.md`:

- **D-035** — Two-layer op set: 8 primitives (create-node, retract-node, set-content, set-property, unset-property, add-edge, retract-edge, move) closed under the 10 invariants; composites (merge, split, promote, demote) are atomic macros = primitive sequences; tag = add-edge, reorder = move; `compact` is the sole destructive op, explicit and separate.
- **D-036** — Ops address targets only by id (from query results, D-033); create-node mints a new id; no positional addressing ever.
- **D-037** — Convergence by design: additive ops = grow-sets, retractions = status flags, set-property/set-content/move = LWW-registers (Lamport tie-break); the state-fold is order-independent → SEC (server-free merge), CRDT-ready without model change.
- **D-038** — Optimistic concurrency: an op may carry an `expect(version/status/value)` precondition; violated → rejected + re-query; default (unguarded) = LWW converge. Resolves RM17.
- **D-039** — Op-log is the canonical journal; state = deterministic fold over the op-set; complete-rebuild and temporal-query follow (event sourcing); semantic op-log↔state equivalence established (byte-level demo completed in Stage 9).

---

## 13. What Stage 9 (Serialization Strategy) must deliver

Phase C closes with serialization. Stage 9 must define, still without committing to author-facing syntax:

1. **The canonical normal form** — the single byte-stable serialization of a model state (determinism inv. 10; RM10) enabling hashing, signing, dedup, and clean diffs (P14; the Rivest/S-expr canonicalization lesson, [standards-adoption.md](../research/standards-adoption.md)).
2. **Op-log serialization** — how the append-only op journal is stored/streamed, and the byte-level op-log↔state equivalence demo (completing the Phase C exit criterion, §8).
3. **Cache-friendly layout** — deterministic order + append bias + no volatile top-of-file fields, so KV-cache prefixes survive edits (P14; [ai-context.md](../research/ai-context.md)).
4. **Partial / streaming load** — sectionable, addressable serialization so an agent loads a subgraph, not the whole file (P14; RM11).
5. **Safety** — no code-execution-on-load, bounded expansion (transclusion-cycle/billion-laughs defense, RS1/RS2), canonical-form attack resistance (RS6).
6. **The `.sarib`⇄JSON isomorphism** — the lossless mapping that lets agents write via structured-output tooling (Stage 4 §7; RA1).

Deferred to Phase D: the author-facing syntax (Stage 10), validation surface (Stage 11), rendering (Stage 12).

## 14. Risks surfaced by this stage

Filed/updated in `../risks/risk-register.md`:

- **RM17 (updated → mitigated)** — query→op lost update: resolved by optimistic-concurrency preconditions (D-038); residual only where callers choose the unguarded path.
- **RM18 (new)** — LWW silently drops the losing side of a concurrent same-node content/move edit (D-037). *Mitigation:* block-sized nodes bound the blast radius; guarded ops (D-038) let callers detect instead of lose; intra-node text CRDT deferred (RM4). Medium.
- **RA10 (new)** — the token-economy win shrinks for large-content nodes: `set-content` replaces a whole node, so a big node costs content-sized tokens. *Mitigation:* keep nodes block-sized; intra-node splicing later (RM4); still far cheaper than document regeneration. Medium/low.
- **RP3 (noted)** — the §10 token figures are estimates; the benchmark harness must measure them before spec freeze (Rule 6).

This document is unratified until Stage 9 critiques it.

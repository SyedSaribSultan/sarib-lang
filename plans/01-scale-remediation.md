# Plan 01 — Scale remediation for the reference implementation

**Status:** planned, not started · **Filed:** 2026-07-27 · **Owner:** next working session
**Trigger:** "How does query performance hold up at tens of thousands of nodes?" — measured, and it does not.
**Scope:** `impl/` only. No spec change expected (see §7 for the one open question).
**Evidence:** `bench/scale_probe.py` (committed with this plan; re-run to reproduce every number below).

---

## 1. The finding

The reference implementation is **quadratic in node count on its core primitive**, and that
primitive sits under parsing, canonicalization, querying, rendering, and every edit op.
It is comfortable at the 301-node dogfood KB and unusable by 10k.

Measured on CPython 3.13, synthetic balanced tree (branching 8, one cross-ref edge per node):

| Nodes | `select:none` filter query | Full `walk()` | Graph walk (default bound) | `check_invariants` |
|---|---|---|---|---|
| 300 | 2 ms | 2 ms | 60 ms | 0.1 ms |
| 1,000 | 22 ms | 22 ms | 397 ms | 0.5 ms |
| 3,000 | 200 ms | 200 ms | 1.7 s | 1.7 ms |
| 10,000 | 2.4–4.2 s | 2.3 s | 6.7 s | 6–11 ms |
| 30,000 | 40–47 s | 39 s | 29 s | 43–48 ms |

100× the nodes costs ~22,000× the time (≈ N^2.2). **Tens of thousands is not slow, it is a wall.**

Indexed prototype, same machine, for the headroom this plan is buying:

| Nodes | Index build | Indexed walk | Current walk |
|---|---|---|---|
| 10,000 | 9 ms | 5 ms | 4,802 ms |
| 30,000 | 61 ms | 11 ms | (too slow to time) |
| 100,000 | 252 ms | 35 ms | (too slow to time) |

### Not yet measured — do these first in WP7, do not assume
- **Parse scaling.** The probe builds `Doc` objects programmatically, so it never exercised
  `parser.py`. Parsing is *also* quadratic (§3, P1) — a real 30k-node file may take minutes
  to merely load, which would make it the worst symptom, not query.
- **Render/preview scaling.** Nested walks there are worse than quadratic (§3, P4); untimed.
- **Memory / RSS** at 30k–100k nodes (RM11's other half).
- Constants are single-run, no warmup, uniform synthetic topology. **The exponent is the
  finding; the constants are soft.** Do not quote the ms figures as benchmarks.

---

## 2. Root causes — two primitives, everything else is a consumer

| # | Primitive | Location | Cost |
|---|---|---|---|
| **C1** | `children()` linear-scans every node in the doc to find one parent's kids. `walk()` calls it once per node. | [`model.py:47-49`](../impl/sarib/model.py#L47-L49), [`model.py:51-55`](../impl/sarib/model.py#L51-L55) | O(N) per call → **O(N²) per full walk** |
| **C2** | `sorted(doc.edges)` sits *inside* the per-frontier-node loop, re-sorting the entire edge table for every node visited. | [`query.py:63`](../impl/sarib/query.py#L63) | **O(V·E log E)**; `max_nodes` bounds V but not E |

Secondary, same character:

| # | Primitive | Location | Cost |
|---|---|---|---|
| C3 | `node_by_slug` linear scan | [`model.py:57-61`](../impl/sarib/model.py#L57-L61) | O(N); called inside an all-nodes loop at [`parser.py:161-167`](../impl/sarib/parser.py#L161-L167) → O(N²) |
| C4 | Containment cycle check walks ancestors for every node, bounded by `len(nodes)` | [`model.py:75-81`](../impl/sarib/model.py#L75-L81) | O(N·depth), O(N²) worst case |
| C5 | `walk()` recurses one frame per containment level | [`model.py:51-55`](../impl/sarib/model.py#L51-L55) | **Stack overflow on deep docs, independent of N.** A 1,000-deep outline breaks before any size limit bites. |

---

## 3. Blast radius — every caller of C1/C2/C3

This is why the fix cannot be scoped to `query.py`.

| P | Where | Call | Consequence |
|---|---|---|---|
| **P1** | [`parser.py:94`](../impl/sarib/parser.py#L94), [`:120`](../impl/sarib/parser.py#L120), [`:135`](../impl/sarib/parser.py#L135) | `order=len(doc.children(container()))` **inside the parse loop** | **Parsing is O(N²).** The quadratic is in the front door — you cannot even load a large file. Likely the worst real-world symptom. |
| **P2** | [`parser.py:161-167`](../impl/sarib/parser.py#L161-L167) | `node_by_slug` per node | Reference resolution O(N²) |
| **P3** | [`canon.py:21`](../impl/sarib/canon.py#L21) | `doc.walk(None)` | **Canonicalization O(N²)** — on the save path, and under G6 (round-trip) / G7 (cache prefix) / hashing / signing |
| **P4** | [`render.py:55-59`](../impl/sarib/render.py#L55-L59), [`preview.py:63-66`](../impl/sarib/preview.py#L63-L66) | `for n in doc.walk(None)` then `list(doc.walk(n.id))` **inside the loop** | **Nested walks — worse than quadratic.** Rendering and the VS Code live preview are the most exposed surfaces. |
| **P5** | [`ops.py:47`](../impl/sarib/ops.py#L47), [`:81`](../impl/sarib/ops.py#L81) | `len(doc.children(parent))` on create/move | Every op pays O(N) |
| **P6** | [`ops.py:99`](../impl/sarib/ops.py#L99) | `check_invariants()` after **every** op | Full-doc revalidation + full edge scan per edit. **This is the one that quietly guts the G1 story** — the *token* economy (0.50%) is untouched, but the *latency* economy is not: a 50-token op costs a full-document validation. |
| **P7** | [`importer.py:93`](../impl/sarib/importer.py#L93), [`:102`](../impl/sarib/importer.py#L102), [`:152`](../impl/sarib/importer.py#L152), [`:224`](../impl/sarib/importer.py#L224), [`:251`](../impl/sarib/importer.py#L251), [`:296`](../impl/sarib/importer.py#L296) | repeated full walks; `children()` inside a walk | `sarib import` on a real vault is the *first* thing a new user runs. The on-ramp built in session 15 is the path most likely to hit this. |
| **P8** | [`query.py:41`](../impl/sarib/query.py#L41) | `pool = [n for n in doc.walk(None) ...]` then `[:maxn]` | Bounded *output*, unbounded *work* — see §5 D3 |
| **P9** | `mcp_server.py` (all tools) | via the above | Agent-facing latency → MCP client timeouts, not just slowness |

---

## 4. Fix — ordered work packages

Land **WP0 first** so there is a failing test before any change, and keep the corpus green after
every WP. Each WP is independently committable.

### WP0 · Add the scale gate (G9) — red before green
- New `bench/gate_scale.py`, wired into `bench/run_gates.py` and CI.
- Assert **empirical sub-quadratic scaling**, not wall-clock thresholds (CI runners vary):
  fit the exponent across ≥3 sizes and require **≤1.3** for parse, canon, full walk, filter
  query, graph walk, and render. Plus one absolute smoke ceiling generous enough not to flake.
- Add fixed sizes 1k / 10k / 30k. Keep 100k out of CI (time), available via a flag.
- **Acceptance:** G9 fails on today's `main` for the documented reasons. Commit it failing
  (or `xfail`-marked with the plan referenced) so the gate report stops implying scale is covered.

### WP1 · `Doc` gains derived indexes — the core primitive (C1, C3)
- Lazily-built, cached on `Doc`: `parent → [Node]` (sorted by `(order, id)`), `slug → id`,
  `source → [edge_id]`, `target → [edge_id]` (both in sorted-edge-id order — see §6 D1).
- `children()` / `node_by_slug()` / new `out_edges()` / `in_edges()` read the index.
- **Invalidation is the #1 bug risk in this plan.** `parser.py` and `ops.py` mutate
  `doc.nodes` / `doc.edges` directly, so there is no single chokepoint. Use explicit
  `doc.touch()` at every mutation site, and back it with the fuzz test in WP5 rather than
  trusting review. Do **not** fingerprint on `len(nodes)`/`len(edges)` — a re-parent changes
  neither and would silently serve a stale index.
- Indexes are **derived and disposable** — consistent with P17 and D-044's framing. Never
  serialized, never part of canonical form, never hashed.
- **Acceptance:** corpus 6/6; canonical output **byte-identical** to pre-change for all
  `examples/` + `dogfood/` files (capture hashes before starting).

### WP2 · Iterative `walk()` (C5)
- Replace recursion with an explicit stack. Preserve DFS pre-order exactly.
- **Acceptance:** a 5,000-deep synthetic doc walks without touching `sys.setrecursionlimit`;
  order identical to the recursive version on every corpus + example file.

### WP3 · `query.py` uses adjacency (C2, P8)
- Hoist the edge scan out of the per-node loop; use `out_edges`/`in_edges`.
- Preserve the D-029 tie-break cascade **exactly** — the emitted node order, edge order, and
  `cursor` must be unchanged. This is a pure performance change with zero observable delta.
- **Acceptance:** golden-output test — for a fixed doc and ≥20 query specs spanning all 7 axes,
  results are identical pre/post, field for field, order included.

### WP4 · `parser.py` (P1, P2)
- Replace `len(doc.children(container()))` with a per-container sibling counter carried in the
  parse state — O(1), and it removes the dependency on a half-built index during parse.
- Slug resolution reads WP1's `slug → id` index.
- **Acceptance:** round-trip byte-identity on all corpus cases; G6 still passes; parse exponent ≤1.3.

### WP5 · `ops.py` (P5, P6) + the invalidation fuzz net
- Sibling-order default via the index; `doc.touch()` on every mutation.
- **Make post-op validation incremental.** Full `check_invariants()` per op is the wrong shape:
  validate the touched nodes/edges and their ancestor chain, and keep the full check available
  for `sarib validate` / load time. Decide explicitly whether "op-time validation is local,
  full validation is a distinct verb" needs a `D-###` — it is arguably an observable
  behavioural narrowing, not just an optimization (§7).
- **Fuzz test (the correctness net for WP1):** generate random op sequences; after each op,
  rebuild every index from scratch and assert equality with the cached index. This is what
  catches a forgotten `touch()`. Lives in `impl/tests/` → **outside the G4 LOC budget**.
- **Acceptance:** G5 unchanged (4 concurrent ops × 24 permutations → 1 distinct state);
  fuzz run of ≥10k ops with zero index divergence.

### WP6 · Consumers: `canon`, `render`, `preview`, `importer` (P3, P4, P7)
- `canon.py`: single indexed walk.
- `render.py` / `preview.py`: **kill the nested walk.** One pass building a subtree map, not
  `walk(n.id)` per node.
- `importer.py`: hoist repeated full walks; `children()` out of the walk loop.
- **Acceptance:** G7 cache-prefix unchanged (99.3% / 1 changed line); preview of every
  `examples/` file byte-identical to pre-change; importer PoC precision/recall unchanged
  (93% / 0 fabrication / 23% recall) — this WP must not perturb extraction.

### WP7 · Measure what §1 could not
- Extend `bench/scale_probe.py` to parse from real generated `.sarib` text, and to time
  canon + render + a full `sarib import`.
- Record peak RSS at 1k / 10k / 30k / 100k → this is the evidence RM11 has never had.
- **Acceptance:** a scaling table in `bench/scale-report.md` covering parse, canon, query,
  render, import, and memory. This is the artifact that closes or re-scopes RM11 and RM8.

### WP8 · Bookkeeping (do not skip — this is how the finding survives)
- `bench/gate-report.md`: add the G9 row and the measured curve.
- `risks/risk-register.md`: **RM11** (🟡 open, "large KBs blow parse/query/memory") gets its
  first hard numbers; **RM8**'s early-warning trigger ("query/write latency unacceptable at
  100k nodes") was silently already met at 10k — record that. Re-rate **RA5** (derived-relation
  query cost) and **RA10** (large-node edit cost) against P6.
- `decisions/decision-log.md`: log the index decision with a reversal condition (see §7).
- `HISTORY.md`: session-log row + next pointer.

---

## 5. Second-order problems this creates or exposes

The user asked for the knock-on issues, not just the fix. These are the ones that will bite.

| ID | Problem | Handling |
|---|---|---|
| **D1** | **Determinism regression.** G5 (merge safety), G6 (round-trip) and G7 (cache prefix) all depend on stable iteration order, currently supplied incidentally by `sorted(doc.edges)` and the `(order, id)` sort in `children()`. Swapping in adjacency lists can silently reorder output → a *correctness* failure wearing a performance change's clothes. | Build every adjacency list in sorted-edge-id order at index time. Golden-output tests in WP3/WP4 before any optimization. Treat byte-identical canonical output as the gate. |
| **D2** | **Stale index served after mutation** — the classic caching bug, and here it corrupts query *results*, which are the sole addressing mechanism for edits (D-033). A stale index means an agent edits the wrong node. | WP5 fuzz test. No `len()`-based fingerprints. |
| **D3** | **"Bounded" queries are only output-bounded.** `select:none` materializes the entire filtered pool, then slices. With an index that is O(N) instead of O(N²) — survivable, but it still contradicts the D-028 minimal-context intent on the work side, and `cursor` pagination semantics currently *depend* on full materialization. | Note it; do not fix opportunistically. Making it lazy changes `cursor` semantics and needs its own decision. Flag for a follow-up plan. |
| **D4** | **G4 LOC budget is nearly exhausted.** Core is **933 / 1000** — only **67 LOC of headroom** for indexes, iterative walk, incremental validation, and invalidation. The "weekend's work / business-card grammar" claim (success test S-implementability) is load-bearing for the whole project thesis. | Budget it explicitly per WP and measure after each. Removed code counts too (the naive `children()` body, the inner edge sort). Estimated net **+20 to +30 LOC**, which fits — but if it does not, **do not quietly raise the budget.** Either tighten, or argue G4 openly in the gate report. Keep tests and `bench/` outside the budget (existing precedent: `importer.py`/`preview.py` are reported separately as consumers). |
| **D5** | **The gates cannot catch this class of bug.** Every programmatic gate passed at 301 nodes. Freeze could have shipped v1.0 with a quadratic reference implementation. | WP0's G9 is the structural fix. Worth a broader look at whether any other gate is size-blind. |
| **D6** | **Deep-nesting stack overflow (C5) is a separate axis from N.** Indexing does not fix it; a deep doc breaks at any size. | WP2, explicitly tested with a deep (not wide) doc. |
| **D7** | **MCP timeouts.** Agent-facing tools inherit every cost above; a slow tool is a *failed* tool once the client gives up, and the failure mode is opaque. | Covered by the fix; add one MCP-path timing assertion in WP7. |
| **D8** | **The on-ramp is the most exposed surface.** `sarib import` over a real vault is a new user's first action, and it is P7. Any adoption attempt at real-note scale hits this before anything else. | WP6 + the import timing in WP7. Prioritize P7 over P8 if forced to choose. |
| **D9** | **Spec vs implementation drift.** D-044 already specifies a derived id→offset index for partial load, and P17 already classes indexes as regenerable derived artifacts. The *spec* never assumed a linear scan — the implementation just never built what the spec presumed. So this is an implementation defect, **not** a design flaw. Say so plainly in the register; do not open a spec revision it does not need. | §7. |

---

## 6. Invariants this work must not break

1. **Byte-identical canonical output** for every `examples/` + `dogfood/` file. Capture hashes
   before the first change; diff after every WP.
2. Corpus **6/6** green after every WP (`python impl/tests/run_corpus.py`).
3. G1, G4, G5, G6, G7 still PASS; G4 re-measured and reported, not assumed.
4. Indexes stay **derived, in-memory, disposable** — never serialized, hashed, or canonical.
5. No positional addressing introduced (P13 / D-033 / D-036). An index is keyed by id; that is
   fine. An index keyed by line/offset **inside the model** is not.
6. Zero observable behaviour change from WP1–WP4 and WP6 (pure performance). WP5's incremental
   validation is the single intentional exception, and it needs a decision.

## 7. Open question for Sarib (decide before WP5)

Does narrowing post-op validation from full-document to local (§WP5, P6) require a `D-###`?

- **Argument no:** it is an optimization; full validation still exists as `sarib validate` and
  at load; the 10 invariants are unchanged.
- **Argument yes:** it changes *when* a violation is detected. A malformed op that previously
  failed immediately could now be caught only at save/validate time — observable, and it
  touches the "forgiving but deterministic" Tier-1 story (D-049..D-051).
- **Recommendation:** log it as a decision with the reversal condition *"if any invariant
  violation is observed escaping op-time detection and reaching a persisted file, revert to
  full validation per op."* Cheap to log, and it keeps the traceability chain intact.

## 8. Reproduce

```
python bench/scale_probe.py              # §1 tables (30k row takes ~2 min pre-fix)
python bench/scale_probe.py 300 1000     # fast sanity run
python impl/tests/run_corpus.py          # must stay 6/6
python bench/run_gates.py                # G1/G4/G5/G6/G7 (+ G9 after WP0)
```

The probe prefers in-repo `impl/` over the installed package. Note this machine currently runs
the **released 0.1.4 build** from PyPI (session 16), so anything invoking `sarib` as a console
script measures the wheel, not the tree — use the probe for the tree.

## 9. Suggested sequencing if credits are tight

WP0 → WP1 → WP3 → WP4 is the smallest set that turns the wall into a slope, and WP1 alone
removes the worst factor. WP6's `render`/`preview` and WP7's measurement are the highest-value
follow-ups. WP8 is small and must not be dropped — without it the next session re-discovers
this from scratch.

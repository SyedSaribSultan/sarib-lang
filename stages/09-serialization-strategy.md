# Stage 9 — Serialization Strategy

**Status:** Draft v0.1 — open for critique by Stage 10 · **Date:** 2026-07-15
**Input:** Stage 8 (AI Interaction Protocol) §13 brief; principles P1–P17; decisions D-001…D-039
**Decisions logged:** D-040 … D-044 (this stage)
**Phase:** C (Machine Interface), stage 2 of 2 — **this stage closes Phase C.**
**Scope guard:** Stage 9 defines how the model is turned into bytes: the canonical normal form, the op-log encoding, partial/streaming load, and load safety. It does **NOT** propose the author-facing `.sarib` text syntax — that is Phase D / Stage 10 (red line). JSON appears here only as a *machine interchange and canonical encoding*, which is a data representation, not the human surface. That distinction is the crux of this stage (§2).

---

## 1. Critique of Stage 8

Stage 8 gave the operation semantics but stopped at bytes. Four gaps.

**C1 — "op-log↔state equivalence" was only semantic.** Stage 8 §8 showed state = fold(ops) as an abstract equivalence and explicitly deferred the byte-level demonstration to here. Stage 9 must complete it, which requires a canonical form (§6).

**C2 — SEC gives same *state*, not same *bytes*.** Stage 8's convergence (D-037) guarantees two replicas with the same op-set reach the same *abstract* state — but two serializers could still emit different byte-strings for it, breaking hashing, dedup, signing, and cache reuse (RM10). SEC is necessary but not sufficient; Stage 9 must add state→bytes determinism via a canonical form (§3, D-041).

**C3 — "op as data, transport-agnostic" had no encoding.** Stage 8 §9 asserted ops ride any channel but never said how they're encoded. Stage 9 specifies the op-log serialization (§5).

**C4 — What actually gets stored, and hashed?** Stage 8 left ambiguous whether the file is the folded state, the op-log, or both — and which is content-addressed. Stage 9 decides: file = snapshot + log; the *canonical state* is hashed for content-addressing/dedup; the log carries history/sync (§5, §6, D-042).

No principle reversed.

---

## 2. Three serializations of one model (D-040)

The model (Stage 4–5) has **three** serializations, each for a different job. Keeping them distinct is what lets Stage 9 do real byte-level work without touching author syntax.

| Serialization | Job | Audience | Stage |
|---|---|---|---|
| **Canonical normal form** | hash / sign / dedup / clean diff — exactly one byte-string per state | tools, VCS | this stage (§3) |
| **Op-log** | append-only journal of edits; sync; cache-stable growth | agents, sync layers | this stage (§5) |
| **Author-facing text** | pleasant to read and hand-write | humans | **Phase D / Stage 10** |

All three encode the *same* model and inter-convert losslessly (P17). This is "write loose, store canonical" (D-003) at the byte level: the human dialect (Phase D) normalizes to the canonical form; the op-log folds to the same state that canonicalizes to the same bytes. JSON is the reference encoding for the first two — a machine interchange, **not** the author surface. The red line holds: no author glyphs are proposed here.

---

## 3. The canonical normal form (D-041; resolves C2)

**Exactly one byte-string per model state.** The canonical form is a deterministic function `canon: State → Bytes`, specified so that any two conforming serializers produce identical output for the same state (closing RM10, satisfying invariant 10). Its construction:

- **Node order:** containment document order — the spanning-tree walk (Stage 4 §6). Deterministic by sibling `order` (D-029).
- **Edge order (per node):** by (edge-type name, target canonical id, edge id) — the traversal tie-break cascade (D-029).
- **Property order:** by key, Unicode codepoint order; fixed field order for intrinsic fields (id, type, status, provenance).
- **Scalar canonicalization:** numbers in canonical form (shortest round-tripping representation, no trailing zeros/exponent games — JCS rules); strings NFC-normalized with canonical escaping; timestamps as canonical ISO-8601 UTC at fixed precision; `quantity` as canonical number + unit token.
- **No non-semantic bytes:** no serialization timestamp, no insertion-order artifacts, deterministic whitespace.
- **Line-oriented layout:** one record (node/edge) per delimited block, fixed indentation — so a small semantic change produces a small *textual* diff (Stage 1 C3 / D-004 diffability), and `hash(canon)` is stable for signing/dedup simultaneously. One form serves both git-diff and content-addressing.

**Reference realization: canonical JSON (RFC 8785 JCS-style).** Rather than invent a canonicalization, `.sarib` adopts JSON Canonicalization Scheme rules (deterministic key ordering, number/string canonicalization) — the "define the canonical form early, don't reinvent it" lesson (Rivest canonical S-expr RFC 9804; JCS RFC 8785; [standards-adoption.md](../research/standards-adoption.md)). The canonical form is therefore canonical JSON over the §4 mapping, pretty-printed line-oriented.

---

## 4. The `.sarib`⇄JSON isomorphism (D-041; satisfies RA1, Stage 4 §7)

A lossless, bidirectional mapping `model ↔ JSON`:

- a **node** → a JSON object `{ id, type?, content, properties?, status?, provenance? }`;
- an **edge** → a JSON object `{ id, type, family, source, target, order?, anchor?, properties?, status?, provenance? }`;
- **content** → an ordered JSON array of inline items (text runs, inline references);
- a **document** → the ordered set of node and edge objects.

Every model element maps to JSON and back with no loss (P17 — hide-never-drop applies byte-level: round-trip is identity). Two payoffs:

- **Agents write through existing tooling.** Constrained decoding against a JSON schema is ~100% syntactically reliable ([ai-context.md](../research/ai-context.md), OpenAI structured outputs), so an agent emits nodes/ops as JSON and the mapping ingests them — the RA1 mitigation made concrete.
- **The canonical form and the isomorphism are the same mapping**, canonicalized (§3). One mapping, two uses.

*Illustrative interchange encoding* (JSON, **not** author-facing `.sarib` syntax — Phase D):

```json
{ "id": "n5", "type": "std:task",
  "content": [{"t":"Migrate invoices"}],
  "properties": {"due": "2026-08-01", "status": "todo"} }
{ "id": "e12", "type": "depends-on", "family": "crossref",
  "source": "n5", "target": "n3" }
```

---

## 5. Op-log serialization; file = snapshot + log (D-042; resolves C3/C4)

**The op-log is an append-only sequence of op records** (Stage 8 §2), each a canonical JSON object `{ id, ts, kind, target, args, expect?, provenance? }`. Append-only means new ops go at the *end* — the leading bytes never move.

**A stored `.sarib` artifact = an optional canonical snapshot + an append-only op-log suffix:**

- reading = load snapshot (canonical state at time T), then fold the op suffix (ops with `ts > T`) → current state (Stage 8 §8);
- writing = append ops to the log (cheap, cache-stable); periodically compact the log into a fresh snapshot;
- the **canonical state** (§3) is what gets **content-addressed/hashed** (for dedup, signing, integrity); the **log** carries history and sync (temporal query, complete rebuild — D-039).

This is the file-as-truth stance realized (RM8): the file *is* a journal + snapshot, so the "demote to live store + journal" fallback needs no model change — it is already the storage model.

---

## 6. Op-log ↔ state equivalence, byte-level (closes Phase C exit criterion; C1)

Stage 8 established the semantic equivalence; the canonical form makes it byte-level:

1. **State → bytes is a function:** `canon(state)` is unique (§3, D-041).
2. **Op-set → state is a function:** `fold(ops)` is order-independent (SEC, D-037).
3. **Therefore op-set → bytes is a function:** `canon(fold(ops))` is unique — any two replicas with the same op-set emit *identical* canonical bytes (C2 closed).
4. **Round-trip both ways:** `fold(log)` → state → `canon` → bytes; and a canonical state expands to a minimal op-log (a create-log) whose fold reproduces the state, whose canon reproduces the bytes. Bytes ⇄ state ⇄ op-set commute.

That is the **byte-level op-log↔state equivalence** the charter's Phase C exit criterion requires, and it is now demonstrated. Combined with Stage 8's closed, invariant-preserving op set (D-035), **Phase C's exit criterion is met** (§11).

---

## 7. Cache-friendly layout and partial/streaming load (D-042/D-044; P14, RM11)

**Cache-friendly (RA4).** The op-log is the cache-optimized artifact: append-only growth keeps the prompt prefix byte-stable, so KV-cache prefixes survive edits (the ~10× input-cost lever; Manus, [ai-context.md](../research/ai-context.md)). No volatile fields sit at the head of file. The canonical snapshot is recomputed off the hot path (integrity/diff, not every edit).

**Partial / streaming load (D-044).** The serialization is **sectionable and addressable**:

- records are independently addressable by id; a **derived, disposable** id→byte-offset index (a derived-layer artifact, P17) gives random access without parsing the whole file;
- containment document order makes a section's subtree a contiguous byte range → load one section (a query result, Stage 7) cheaply;
- **locality** holds (P15): a record's meaning never depends on later bytes, so a parser streams incrementally and an agent loads a bounded subgraph (D-028) instead of the whole file (length-degradation economics; RM11).

---

## 8. Load safety (D-043; RS1/RS2/RS6)

The serialization is designed against the failure modes that cursed prior formats:

- **No code execution on load (RS1).** Pure data — no tags, constructors, macros, or directives that execute. Loading is parse-to-model and nothing else. This is the deliberate avoidance of YAML's `load()`-is-RCE fate ([standards-adoption.md](../research/standards-adoption.md)).
- **Bounded expansion (RS2).** Transclusion is acyclic (Stage 5 §3.2); the loader resolves it with a visited-set (cycle detection, as in traversal D-027) and a depth/size cap → no billion-laughs / K8s-CVE-class amplification.
- **Canonicalization resistance (RS6).** The canonicalizer rejects or normalizes ambiguous encodings — duplicate keys, non-NFC strings, non-canonical numbers — so there is exactly one byte-form per state and no two forms can collide or diverge under signing (the "canonical form on day one" lesson; RFC 8785/9804).
- **Content is data, not instructions.** No serialized field instructs the reader/agent to act; `args`, `provenance`, `content` are inert data. This is the format-level half of the prompt-injection defense (RS3): a loader never interprets `.sarib` content as commands (the Crockford-removed-comments discipline — subtract anything whose misuse is "smuggle directives to a specific reader").

---

## 9. Worked example (interchange encoding — not author syntax)

Marking task n5 done, then reading back, over the Stage 4 graph.

**Op appended to the log** (canonical JSON op record):
```json
{ "id":"op88","ts":[4,17],"kind":"set-property",
  "target":"n5","args":{"key":"status","value":"done"},
  "expect":{"n5":{"version":7}},"provenance":{"class":"asserted"} }
```
- ~a few dozen bytes; leading bytes of the file unchanged (append-only → cache prefix survives, §7).
- `expect` guards the lost-update race (D-038): applied only if n5 is still at version 7.

**Fold → state → canonical form:** folding the log now yields n5 with `status: done`; `canon(state)` re-emits n5's record with the new value, in the same document position (§3) — so the git diff is *one line* (the status field), not the whole file (D-004 diffability). The file's hash changes; two replicas that saw `op88` compute the *same* hash (§6).

**Partial read:** an agent querying "open tasks" loads only the task records via the id→offset index (§7), not the document — the minimal-context read (P14) that pairs with the minimal-context write above.

This is the full machine loop in bytes: append a tiny op, fold, canonicalize for integrity, read back a bounded slice. No regeneration anywhere (D-002).

---

## 10. New decisions

Full entries in `../decisions/decision-log.md`:

- **D-040** — One model, three serializations: canonical normal form (integrity/diff), op-log (edits/sync/cache), author-facing text (Phase D). All lossless inter-conversions; author text normalizes to the canonical form ("write loose, store canonical" byte-level).
- **D-041** — Canonical normal form = line-oriented canonical JSON (RFC 8785 JCS rules) over the `.sarib`⇄JSON isomorphism: document-order nodes, deterministic edge/property order, canonical scalars, NFC strings, fixed fields — exactly one byte-string per state.
- **D-042** — A stored file = optional canonical snapshot + append-only op-log suffix; read = load snapshot + fold suffix; the canonical *state* is content-addressed/hashed, the log carries history/sync. Realizes file-as-truth (RM8).
- **D-043** — Load safety: pure-data load (no code/directives, RS1); acyclic + depth/size-bounded transclusion resolution (RS2); canonicalizer rejects ambiguous encodings (RS6); content is inert data, never instructions (format-level RS3 defense).
- **D-044** — Partial/streaming load: id-addressable records + a derived disposable id→offset index; containment-order sections are contiguous ranges; locality guarantees streaming and bounded-subgraph loads (P14/RM11/P15).

---

## 11. Phase C exit check

Charter exit criterion for Phase C: *"Atomic op set closed under composition; op-log ↔ state equivalence demonstrated."* Status: **met.**

- Stage 8 delivered the closed, invariant-preserving op set (D-035) and semantic op-log↔state equivalence (D-039).
- Stage 9 delivered the canonical form (D-041) and thereby the **byte-level** op-log↔state equivalence (§6): `canon(fold(ops))` is a unique function of the op-set.

The machine interface is complete: **one model → {canonical bytes for integrity, an append-only log for edits, a JSON isomorphism for agents} → the same model.** Every edit is a tiny addressed delta; every state has one hash; every replica converges to the same bytes. Phase D can now give humans a surface over this machine.

Coherence: nothing in Stages 8–9 contradicts the Stage 4 invariants or the priority order; the canonical-form and op-log choices are integrity-first (priority rule 1), with cache/partial-load (efficiency, rule 3) layered on without compromising it.

---

## 12. What Stage 10 (Syntax Proposals) must deliver — Phase D opens

Stage 10 finally designs the **author-facing surface** — the red line lifts. Per the charter's Phase D exit criterion, **at least two competing syntaxes must be designed and tested against the writability criteria before one is chosen.** Requirements it inherits:

1. **Markdown-superset surface** (P6/D-006): renders acceptably in a CommonMark renderer; looks like what humans and LLMs already emit; edges emerge from inline prose links (P4/D-012); containment from nesting (P5/D-013).
2. **Losslessly normalizes to the canonical form** (D-040): the pleasant surface is a third serialization that maps 1:1 to the model and hence to §3's bytes.
3. **Forgiving surface, deterministic parse** (P15): every input parses to a model (prose degrades to L0 nodes); validity is lint-grade.
4. **Identity without ceremony** (P8/D-009): humans write names; ids/slugs are tooling-managed and quarantined.
5. **≥2 candidates, writability-tested** (charter Phase D): compare on cold human readability (S3) and hand-authoring cost before choosing.

Then Stage 11 (validation rules) and Stage 12 (rendering architecture) complete Phase D.

## 13. Risks surfaced by this stage

Filed/updated in `../risks/risk-register.md`:

- **RM10 (→ resolved)** — determinism / two byte-forms per state: closed by the canonical form (D-041).
- **RS1, RS2, RS6 (→ mitigated)** — load-time RCE, expansion DoS, canonicalization attacks: addressed by D-043.
- **RA4 (→ mitigated, reaffirmed)** — KV-cache: append-only op-log keeps prefixes stable (D-042).
- **RM19 (new)** — canonical-form recomputation cost: re-canonicalizing a large file on every change is expensive. *Mitigation:* edits run against the append-only log (cheap); canonicalization is off-hot-path (integrity/diff), with incremental canonicalization possible. Low/medium.
- **RD6 (new)** — JSON-as-the-format temptation: because the interchange/canonical form is JSON, adopters may treat JSON as *the* format and skip the human surface, undermining the human-writable goal (P6). *Mitigation:* the canonical/interchange JSON is explicitly machine-only; Phase D delivers the pleasant author surface; position JSON as the wire/at-rest encoding, never the thing humans write. Low/medium.

This document is unratified until Stage 10 critiques it.

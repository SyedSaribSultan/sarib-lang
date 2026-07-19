# Stage 4 — Core Object Model

**Status:** Draft v0.1 — open for critique by Stage 5 · **Date:** 2026-07-15
**Input:** Stage 3 (Design Principles) §5 brief; ratified principles P1–P17; decisions D-001…D-014
**Decisions logged:** D-015 … D-019 (this stage); amends D-013
**Phase:** B (Semantic Core) — this is the first stage of the abstract machine.
**Scope guard:** This stage defines *what exists* — the abstract objects and the invariants that bind them. It does **not** define how they are written (syntax → Phase D / Stage 10), how they are edited (operation vocabulary → Stage 8), or how they are queried (Stage 7). All notation below is abstract (tuples, tables, graph descriptions) and is explicitly **not** proposed `.sarib` syntax.

---

## 1. Critique of Stage 3

Stage 3 gave a clean constitution, but writing the model against it exposed four places where a principle was underspecified or slightly wrong. Each is resolved below and, where it changes a decision, logged.

**CR1 — D-013 is wrong about storage. "Containment is a DAG (multiple parents)" cannot hold for the canonical file.** If a node had two home parents, it would appear twice in document order and there would be no single answer to "where does this node live" — violating both the Markdown-superset serialization (P6, a file is a linear document) and single-owner-per-state (P17). The multi-parent intuition is real but belongs to a *different* mechanism: transclusion, which is a cross-reference edge, not a second home. **Resolution (D-016, amends D-013):** storage containment is a single-parent spanning tree; effective multi-parent structure is delivered by transclusion edges overlaid on that tree.

**CR2 — P8 ("every atom has identity") never faced the cost of universal identity.** Two unaddressed problems: (a) *granularity* — is a node a whole section, a paragraph, a sentence? (b) *homing* — an entity first mentioned inline ("…met **Alice**…") has no obvious place to "live," yet the single-home invariant (CR1) demands one. Stage 4 fixes granularity at the block (§3) and gives inline-born entities a system home (§6).

**CR3 — Stage 3 called the brief's 28 node kinds "a menu to cut" but gave no cutting principle.** The principle is now explicit and more aggressive than Stage 3 implied: **the core contains no domain types at all.** `task`, `person`, `decision`, `API`, `motion` are *vocabulary*, shipped as an optional standard library, exactly as schema.org is a vocabulary over a generic model rather than baked into a format ([semantic-web.md](../research/semantic-web.md)). The core defines one node, a handful of structural roles, and the extension machinery — nothing else (D-018).

**CR4 — P4 left the source granularity of a link-derived edge undefined.** If "Alice knows Bob" creates a `knows` edge, what is the edge's source — the sentence, the paragraph, the section? Stage 4 rules: the source is the **containing block-node**; finer precision requires promoting the span to its own node (§5.3). This keeps edges anchored to identified nodes, never to character positions (P13).

No principle was reversed. D-013 is amended; the rest are refined.

---

## 2. The model in one paragraph

A `.sarib` knowledge base is a single set of **identified nodes** connected by **identified typed edges**. Edges come in two families. **Containment edges** form a spanning tree over all nodes — each node has exactly one *home parent* and an order among its siblings; walking this tree in order *is* the readable document. **Cross-reference edges** form an arbitrary directed graph over the same nodes — typed, property-bearing, and including transclusion (render-here-too) links. There is not a tree *and* a graph; there is **one graph, and the document is the view you get by walking its containment spanning-tree in order.** That single sentence is the resolution of the containment/graph duality (Stage 3 C1) and the spine of everything below.

---

## 3. The node

**Definition.** A node is the atom of knowledge:

```
Node = (
  id:         Identity          // durable, opaque, system-assigned  (§4)
  type:       TypeRef?          // absent = untyped/prose             (§7)
  content:    InlineSeq         // ordered inline content, may be empty (§3.2)
  properties: {Key: Value}      // may be empty                        (§3.3)
  status:     active | retracted   // default active                  (§8)
  provenance: Provenance?       // absent = file-owner default         (§8)
)
```

Edges are **not** stored inside the node (they are first-class objects, §5); a node's relationships are recovered by querying edges incident to its `id`. This keeps a node a small, stable record and lets an edge be edited without rewriting either endpoint (P14 — small deltas).

**D-015 — one node type, progressively typed.** A paragraph of prose and an entity called "Alice" are the *same kind of object* — a node. The paragraph is a node with no type and rich `content`; Alice is a node with `type = person`, sparse content, and some properties. This unification (proven at scale by Notion's "everything is a block", [Notion](https://www.notion.com/blog/data-model-behind-notion)) is what lets the prose tree and the property graph be one structure. There is no separate "block" and "entity" concept to reconcile.

### 3.1 Granularity (resolves CR2a)

The node is a **block**: the smallest independently-addressable unit of content — a paragraph, a heading, a list item, a code block, a quote, a table row, or a typed entity. This matches the granularity that worked in Notion (blocks) and Portable Text (`_key` per block, [spec](https://www.portabletext.org/specification/)).

- Coarser structure (a section, a document) is a **container node** with children via containment edges — not a special kind, just a node that has children.
- Finer structure (a phrase inside a paragraph) is *not* a node by default. It exists only as inline content. It is **promoted** to a node on demand — when someone needs to attach identity, a type, an edge with sub-block precision, or provenance to it (§5.3). Promotion is the pressure valve that keeps identity cheap for the common case (most prose never needs sub-block IDs) while making it available when required.

### 3.2 Content

`content` is an ordered sequence of inline items:

- **text runs** — spans of characters, optionally carrying presentational marks (emphasis, code, etc.; marks are surface decoration, not knowledge);
- **inline references** — an anchored reference to another node, optionally typed (§5.3). An inline reference is the point in the prose where a cross-reference edge is anchored.

Content may be empty (a pure container, or an entity defined only by properties). Marks are deliberately shallow — they are the one place the model tolerates presentation, because they ride Markdown (P6) and carry no queryable meaning.

### 3.3 Properties

A property is `Key → Value` where `Value` is a scalar (string/number/bool/date), a **list** of values (native lists — the thing RDF lacked, P7 / [Sporny](http://manu.sporny.org/2014/json-ld-origins-2/)), or a **node reference** (an id). Properties hold attributes that are not themselves worth being nodes (a task's `due` date, a person's `email`). When an attribute *is* worth identity, hierarchy, or its own relationships, it becomes a node reached by an edge instead — see tags (§5.4).

---

## 4. Identity (resolves CR2, satisfies P8 / D-009 / D-014)

**Intrinsic id.** Every node and every edge has an `id` that is:

- **Opaque** — carries no meaning; not derived from content (Git's content-addressing is the anti-pattern: because a blob *is* its content, Git cannot track a rename and must re-guess it heuristically, [Pro Git](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)). A `.sarib` id survives arbitrary edits to the thing it names.
- **Durable** — assigned once, never reused, never changed for the life of the object.
- **Position-independent** — not an index, offset, or line number (JSON Patch's positional addressing is the merge anti-pattern, [RFC 6902](https://www.rfc-editor.org/rfc/rfc6902)).
- **Assignable offline without coordination** — so two disconnected replicas never collide. The concrete scheme is deferred (Stage 9/10) but *constrained* to a `(replica, counter)` Lamport pair or an equivalent collision-free token (ULID/UUIDv7), which is what makes the model CRDT-ready per D-014 ([Yjs INTERNALS](https://raw.githubusercontent.com/yjs/yjs/main/INTERNALS.md)).

**Humans never type ids.** Authors refer to nodes by **name** (a human-readable label) and the system resolves name → id. Consistent with every system studied, the more opaque the identifier, the more completely tooling hides it ([versioning-and-merge.md §2](../research/versioning-and-merge.md)).

- **Names are not identity and not unique.** Two nodes may both be named "Apple." Reference resolution is scoped and may be ambiguous; ambiguity is resolved by context (nearest-in-containment, or explicit disambiguation) and surfaced as a lint diagnostic (P15), never by forcing globally-unique names (the IRI ceremony that taxed RDF, P7).
- **Optional human slug.** A node may carry a durable, human-readable **slug** (like org-mode's `CUSTOM_ID`, [versioning-and-merge.md §2](../research/versioning-and-merge.md)) for citation. This is the *only* identifier permitted to appear in prose, and it is quarantined from running text. The slug is a property; the intrinsic id remains the true identity.

**Identity survival — the four transitions.** The model guarantees the following (the *operations* that perform them are Stage 8; here we state only what identity must survive):

| Transition | id behavior | Edges | History |
|---|---|---|---|
| **Rename** (change name/label) | unchanged | all intact — they reference id, not name | name change recorded |
| **Move** (change home parent) | unchanged | home containment edge retargeted; all others intact | move recorded |
| **Merge** (combine A, B → one) | one survivor id; the other is `retracted` with a `merged-into` edge to the survivor; inbound references resolve through it | inbound edges of the retired node forward to the survivor | both lineages preserved (P12 — retract, never destroy) |
| **Split** (one → two) | original id retained by one part; new part gets a new id; both carry `split-from` provenance | edges partitioned per author/agent intent; ambiguous ones flagged | split recorded |

Rename survival is the headline: it is the exact failure Git cannot handle, and solving it is a large part of why `.sarib` needs stable ids at all.

---

## 5. The edge

**D-017 — edges are first-class and identified.** An edge is not a pointer buried in a node; it is an object with its own id, type, properties, status, and provenance. This is the property-graph advantage over RDF triples: a relationship can carry metadata (a `cites` edge with a `page`; a `knows` edge with `since`) without reification's 4–5-triple tax ([semantic-web.md §2](../research/semantic-web.md)). First-class edges are also what let operations (Stage 8) and provenance (§8) address a single relationship precisely.

```
Edge = (
  id:         Identity
  type:       TypeRef?          // absent allowed only for containment (§5.1)
  family:     containment | crossref
  source:     Identity          // a node id
  target:     Identity          // a node id
  order:      Ordinal?          // required for containment; sibling order
  anchor:     InlineAnchor?     // set if derived from an inline reference (§5.3)
  properties: {Key: Value}
  status:     active | retracted
  provenance: Provenance?
)
```

### 5.1 Containment edges — the free tree

Containment edges carry the document's hierarchy and cost nothing to author, because they fall out of structure (a heading contains its subsections; a list contains its items) — the zero-ceremony implicit edge (P5 / D-013 / [KDL](https://kdl.dev/)).

- **Directed** parent → child.
- **Ordered** — siblings have an `order`; this ordinal is how the model represents *authorial sequence* (Stage 1 C5) without privileging it: sequence is just the order attribute on one edge family, and every non-linear traversal ignores it (Stage 7).
- **Single home (the core invariant).** Every node has exactly one active containment edge into it, except the root. This makes the containment subgraph a **spanning tree** and guarantees a unique, deterministic document order (P14 — deterministic serialization; P17 — single owner).
- Untyped by default (the relation is simply "contains"); a container may *also* be semantically typed (a `section`, a `list`) via the node's `type`, but the containment edge itself needs no type.

### 5.2 Cross-reference edges — the graph overlay

Everything that isn't containment. Typed, directed, property-bearing (P7). These are the edges that make the knowledge a graph rather than a document: `depends-on`, `blocks`, `cites`, `knows`, `contradicts`, `refines`. A node may have any number of them, in and out, with no effect on where it lives in the document.

**Transclusion** is a distinguished cross-reference edge type (`transcludes`): it asserts that the target's content may be *rendered inline here as well* (Notion synced blocks, Roam embeds, [tools-for-thought.md](../research/tools-for-thought.md)). It is how the model delivers the multi-parent intuition that D-013 wrongly assigned to containment (CR1): the target still has exactly one home, but appears in additional contexts by reference. Edits through a transclusion flow to the one home node (single owner, P17), so transclusion is edit-consistent by construction.

### 5.3 Inline references and desugaring (resolves CR4)

An **inline reference** in a node's `content` is the anchored surface of a cross-reference edge. When content contains a typed inline reference from node *S* naming relation *r* to a node resolved as *T*, the model holds a cross-reference edge `(type=r, source=S, target=T, anchor=<the span in S>)`. Thus writing a sentence with a typed link *is* asserting an edge (P4 / D-012) — no standalone statement, no edge-writing ceremony ([graphs-and-databases.md](../research/graphs-and-databases.md)).

- **Source is the containing block-node** *S* — not the character span. The `anchor` records where the reference appeared, for round-trip rendering, but the edge's semantic endpoint is the whole node (P13 — endpoints are identified nodes, never positions).
- **Sub-block precision** (CR4): if a relationship must originate from a phrase rather than the whole block, that phrase is **promoted** to its own node (§3.1) with its own id, and becomes the edge source. Promotion is the single, uniform mechanism for "I need finer identity here."
- **Block-form edges** (the P4 fallback) are edges with no `anchor`: relationships asserted without an inline sentence, for the cases prose cannot carry (bulk links, edges between two entities neither of which is "the sentence"). The model treats anchored and unanchored edges identically except for rendering.

### 5.4 Tags as edges (a payoff of D-015)

A tag is modeled as a cross-reference edge of type `tag` to a node (of vocabulary type `concept`/`tag`). Because tags are edges to nodes, they get identity, survive rename, can form hierarchies (a tag node contained under another), and are queryable like any relationship — for free, from the unified model. Projections may *surface* tags as a simple property list for ergonomics, but the canonical form is an edge. (A pure-property tag remains permitted at ladder rung L4 for the lightest case; the edge form is preferred when hierarchy or identity is wanted.)

---

## 6. The containment/graph duality — formal statement (resolves C1)

Let **N** be the set of nodes and **E** the set of edges, partitioned into containment edges **E_c** and cross-reference edges **E_x**.

1. **(N, E_c)** is a rooted, ordered, spanning tree: one root; every non-root node has exactly one active parent edge; siblings are totally ordered.
2. **The document** is `inorder(N, E_c)` — the depth-first, sibling-order walk of the containment tree. This is Stage 1's "linear reading" traversal, and it yields Markdown-compatible prose (P6).
3. **(N, E_c ∪ E_x)** is the full labeled property graph. Every other traversal named in the brief (dependency, priority, semantic, chronological, tag, comparative, AI-selected…) is a query over this graph (Stage 7), not a different stored structure.

**The tree is a subgraph of the graph** — specifically the containment-edge subgraph, which is constrained to be a spanning tree. This is the whole resolution: prose and graph are not two representations to keep in sync (the trap that broke every system in [tools-for-thought.md](../research/tools-for-thought.md)); they are two *readings* of one structure.

**Homing inline-born entities (resolves CR2b).** The spanning-tree invariant requires every node to have a home, including an entity first mentioned inline with no definition site. Rule: such a node is created with its home under a reserved system container (e.g., a root-level entity collection). A projection may hide that container (P17 — hide, never drop). The author or an agent may later *move* it (§4) to a meaningful home; its id is unchanged, so every reference survives. This keeps the single-home invariant absolute without forcing authors to manually file every mentioned entity.

---

## 7. The type ladder (operationalizes P9; resolves CR3)

The six rungs of P9 are model states, not separate formats; a single knowledge base mixes rungs per node.

| L | Rung | Model construct |
|---|---|---|
| 0 | Prose | untyped nodes with `content` |
| 1 | Structured prose | containment edges from nesting (free) |
| 2 | Typed nodes | `node.type` set to a `TypeRef` |
| 3 | Typed edges | cross-reference edges with `type` (incl. inline links, tags) |
| 4 | Properties & tags | `properties` on nodes/edges; tag edges |
| 5 | Schema-checked | schemas constrain types/properties/edges; closed-world validation |

**D-018 — thin core, vocabulary as extension.** The core model defines only:

- one node (§3) and the two edge families (§5);
- a minimal set of **structural roles** needed to serialize any document: `document` (the root container), `section`/`container` (has children), `prose` (default text node), and `list`/`item` for ordered/unordered collections. These are about *document shape*, not *domain meaning*.

Every **semantic type** — `task`, `person`, `decision`, `api`, `bug`, `metric`, `motion`, and the rest of the brief's list — is defined in a **vocabulary**: a schema (rung L5 artifact) shipped as an optional standard library, not hardcoded. This mirrors how schema.org is a vocabulary layered on a generic model and Wikidata's types are community-defined rather than in the data model ([semantic-web.md](../research/semantic-web.md)). It is the aggressive cut priority rule 4 demands: the core stays business-card-sized (S6), and domains extend it without forking (P16).

**TypeRef and extension (P16 / D-011).** A `TypeRef` is namespaced: core structural roles are unprefixed; everything else is namespaced (illustratively `std:task`, `acme:component` — namespacing shown abstractly, not as proposed syntax). An unknown `TypeRef` must:

1. **parse** — the node/edge is still well-formed;
2. **degrade** — it renders and behaves as an untyped node / generic edge (drops to a lower rung, never errors, P15);
3. **round-trip untouched** — unknown types and their properties are preserved byte-faithfully (P17 — hide, never drop).

**Validation (P10 / D-008).** A schema is itself expressible as `.sarib` (schemas are knowledge too) and declares: node kinds, permitted properties and value types, permitted edge types with endpoint-type and cardinality constraints. Validation is **closed-world** (an unknown type/property against an *active* schema is a diagnostic, not silent acceptance) and **lint-grade** (non-fatal — a document with violations still parses and renders, P15). There is no open-world inference (OWL's fatal choice, [TerminusDB](https://terminusdb.com/blog/the-semantic-web-is-dead/)); `.sarib` checks what is stated, it does not infer new truth.

---

## 8. Provenance and status (P10 / P12; keeps the single-author case clean)

**D-019 — provenance is sparse and defaults to the owner.** Attaching author/time/basis to *every* assertion would drown the common single-author file (the C3-class concern). Instead:

- Every assertion (a node, an edge, a property) has an **implicit** provenance of "asserted by the file owner, at edit time." This default is *never materialized* — a single-author file carries no provenance overhead at all.
- Provenance is **materialized only when it differs from the default**: an agent's inference, an imported fact, a second collaborator, a stated evidential basis.
- The materialized `Provenance` carries at minimum an **assertion class** — `asserted` (a human states it), `inferred` (an agent/derivation produced it), or `imported` (from an external source) — plus optional `by`, `at`, and `basis`.

This directly delivers P10's "record claims with provenance, not truth" and "segregate asserted from derived": inferred edges/properties are exactly the ones carrying `inferred` provenance, so they can be filtered, trusted differently, or regenerated, and they never silently contaminate human assertions (OWL's inference-pollution failure, [semantic-web.md §3](../research/semantic-web.md)). It also mirrors Wikidata's plurality model — the store can hold conflicting referenced claims and let the reader (often an LLM) weigh them ([Wikidata CACM](https://iccl.inf.tu-dresden.de/w/images/8/89/Wikidata-CACM-2014.pdf)).

**Status and retraction (P12).** Every node and edge has `status ∈ {active, retracted}`, default `active`. Deletion is a **retraction** — a status assertion, not an erasure ([Datomic](https://docs.datomic.com/transactions/model.html)): the object stays in the model, hidden from default projections but present for history and audit, optionally with a successor edge (`merged-into`, `split-from`, `superseded-by`). Physical removal is a separate, explicit compaction concern (Stage 8/9), never implied by retraction.

---

## 9. The three layers (P17)

The model is stratified by owner and volatility; each layer has exactly one authoritative writer.

| Layer | Contains | Writer | Persistence |
|---|---|---|---|
| **Content** | nodes, containment edges, human/imported edges & properties, `asserted`/`imported` assertions | humans + agents (deliberate edits) | canonical |
| **Derived** | `inferred` edges/properties, computed indexes, materialized projections | derivation processes | regenerable; persisted only by explicit choice, always marked `inferred` |
| **Session** | active view, filters, cursor, selection | the tool/UI | never in the canonical model — excluded by definition |

The canonical `.sarib` model is the content layer plus whatever derived material the author chose to persist (always provenance-marked). Session state is not knowledge and never enters the file — the conflation that destroyed Jupyter-in-git ([fast.ai](https://www.fast.ai/posts/2022-08-25-jupyter-git.html)).

---

## 10. Worked example (abstract — not syntax)

A tiny knowledge base: a project note containing a decision, two tasks, and a person, with cross-references. Shown as the abstract model, deliberately **not** in any proposed file syntax.

**Nodes**

| id | type | content (abridged) |
|---|---|---|
| n1 | `document` | "Q3 Planning" |
| n2 | `section` | "Decisions" |
| n3 | `std:decision` | "Adopt the new billing provider" |
| n4 | `section` | "Tasks" |
| n5 | `std:task` | "Migrate invoices" (props: due=2026-08-01) |
| n6 | `std:task` | "Notify customers" |
| n7 | `std:person` | "Alice" (props: email=…) |

**Containment edges E_c** (the spanning tree = the document)

```
n1 →(order 1) n2      n2 →(order 1) n3
n1 →(order 2) n4      n4 →(order 1) n5    n4 →(order 2) n6
```
n7 (Alice) was born from an inline mention, so her home is the reserved entity container (hidden in the prose projection): `root-entities →(order k) n7`.

**Cross-reference edges E_x** (the graph overlay)

```
n5 —depends-on→ n3         (task depends on the decision)
n6 —depends-on→ n5         (notify after migrate)
n5 —owned-by→   n7         (Alice owns the migration; anchored to an inline "Alice" in n5's content)
n3 —tag→        c1 (concept "billing")
```

**Readings of the one structure:**
- *Linear* (P1/§6): inorder walk of E_c → "Q3 Planning / Decisions / Adopt… / Tasks / Migrate… / Notify…". Reads as ordinary Markdown.
- *Dependency traversal*: follow `depends-on` in E_x → n6 → n5 → n3. A query, not a stored view.
- *By person*: edges incident to n7 → n7 owns n5. A query.
- *Rename* "Alice" → "Alice Chen": n7.name changes; the `owned-by` edge (→ n7) is untouched; the inline mention re-renders from the edge. Nothing breaks (contrast Git).

The example uses `std:`-namespaced types precisely to show they are *vocabulary*, not core (D-018): strip the vocabulary and every node degrades to a titled prose block — still a valid, readable document (P9 rung L0/L1).

---

## 11. Invariants (the model's constitution)

A structure is a valid `.sarib` model iff:

1. **Identity.** Every node and edge has a unique, durable, opaque id (§4).
2. **Single home.** Every node except the root has exactly one active containment edge into it; the containment subgraph is a rooted, ordered spanning tree (§5.1, §6).
3. **Endpoints exist.** Every edge's `source` and `target` reference existing node ids; an edge to a `retracted` node is itself effectively dormant, not dangling.
4. **Endpoints are nodes, never positions.** No edge, reference, or operation addresses a character offset, line, or array index (§4, P13).
5. **Order totality.** Siblings under a common parent are totally ordered (§5.1).
6. **Type openness.** An unknown `TypeRef` parses, degrades gracefully, and round-trips untouched (§7, P16/P17).
7. **Provenance default.** Absent provenance means "asserted by owner"; `inferred`/`imported` material is distinguishable from `asserted` (§8, P10).
8. **Retraction, not deletion.** Removal sets `status = retracted`; the object persists in the model until explicit compaction (§8, P12).
9. **Layer separation.** Session state never appears in the canonical model; derived material is always provenance-marked (§9, P17).
10. **Determinism.** Given the same nodes and edges, the serialized document order is unique (follows from 2 + 5; required by P14).

These invariants are the contract Stage 8 (operations) must preserve on every edit and Stage 10 (syntax) must be able to express.

---

## 12. New decisions

Logged in full in `../decisions/decision-log.md`:

- **D-015** — One node type, progressively typed; prose blocks and entities are the same object.
- **D-016** — Storage containment is a single-parent ordered spanning tree; multi-parent structure is delivered by transclusion cross-reference edges (**amends D-013**).
- **D-017** — Edges are first-class, identified objects carrying type, properties, status, and provenance.
- **D-018** — Thin core (one node, two edge families, a few structural roles, the extension mechanism); all semantic types are optional namespaced vocabulary.
- **D-019** — Provenance is sparse and owner-defaulted; assertion class ∈ {asserted, inferred, imported}; status ∈ {active, retracted}.

---

## 13. What Stage 5 (Abstract Semantic Model) must deliver

Stage 4 fixed the *shape* of knowledge. Stage 5 must fix its *meaning*:

1. **The standard vocabulary, v0.** Which semantic types actually ship in the standard library, defined as schemas — cut from the brief's 28 by the priority rule, with a stated inclusion test. (Candidate spine: `task`, `decision`, `question`, `reference`, `person`, `concept` — justify each; relegate domain sets like software/design to separate optional vocabularies.)
2. **Edge-type semantics.** What `depends-on`, `refines`, `contradicts`, `blocks` *mean*: directionality, declared inverses, transitivity, and which are structural vs. domain.
3. **Schema language.** How a schema constrains nodes/edges/properties, expressed as `.sarib` itself; how cardinality and endpoint-type constraints are stated; how closed-world validation reports (P10/P15).
4. **Property value types.** The scalar set (string/number/bool/date/duration?), lists, node-references; how units and typed literals are handled without RDF's datatype ceremony.
5. **Reference resolution semantics.** The precise rule for name → id under ambiguity and scope (nearest-in-containment vs. explicit), since §4 only sketched it.
6. **Vocabulary evolution.** How a vocabulary versions and how documents pin the vocabulary they were written against (P16 — frozen core, versioned extensions).

Deferred as before: operation vocabulary (Stage 8), concrete syntax (Stage 10), query/traversal execution (Stage 7).

## 14. Open questions and risks

- **OQ1 — promotion churn.** If agents promote inline spans to nodes aggressively (§3.1), node count could explode and ids churn. Stage 5/8 need a promotion policy (when is a span worth a node?) and possibly a demotion (garbage-collect an unreferenced promoted node).
- **OQ2 — anchor stability.** An `anchor` (§5.3) locates a link within content; if the content is edited, the anchor must move with it. This reintroduces a position-tracking problem *inside* a node, below the id boundary. Likely handled the same way CRDTs track intra-text positions (per-character identity) — but that is metadata weight (Stage 8/9 must budget it, [versioning-and-merge.md §6](../research/versioning-and-merge.md)).
- **OQ3 — the entity home convention (§6).** A reserved system container is a pragmatic fix; if it accumulates thousands of auto-homed entities it becomes a dumping ground. Stage 5 should decide whether vocabularies can declare canonical homes (e.g., all `person` nodes home under a `people` collection).
- **R-new-3 — the block-granularity bet.** Fixing the atom at the block (§3.1) assumes most knowledge work happens at paragraph granularity and sub-block identity is rare. If real `.sarib` corpora need sentence- or phrase-level structure routinely, promotion stops being an exception and the cost model (OQ1) dominates. Testable once a reference implementation exists.

This document is unratified until Stage 5 critiques it.

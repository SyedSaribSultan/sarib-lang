# Scaling report — reference implementation

Generated 2026-07-28 by `python bench/scale_probe.py --report` · python 3.13.7 · single machine, best-of-3.

This is the evidence RM11 ("large KBs blow parse/query/memory") never had, and the answer to RM8's early-warning trigger ("query/write latency unacceptable at 100k nodes"). The pass/fail gate is **G9** in `bench/gate-report.md`; this report is the detail behind it.

Times are milliseconds. `slope` is the least-squares exponent of log(time) vs log(nodes): ~1.0 is linear, ~2.0 is quadratic. **The exponent is the finding; the absolute constants are machine- and noise-dependent.**

## After — current tree, 1,000 to 100,000 nodes

| path | 1,211n | 12,450n | 37,370n | 124,841n | slope |
|---|---|---|---|---|---|
| parse | 11.0 | 110.5 | 378.1 | 1,408.2 | **1.05** |
| canon | 9.5 | 98.9 | 291.7 | 1,052.9 | **1.01** |
| fmt | 1.9 | 24.0 | 87.6 | 351.1 | **1.13** |
| outline | 1.3 | 15.7 | 64.6 | 272.2 | **1.15** |
| board | 0.5 | 5.0 | 19.3 | 66.1 | **1.06** |
| mermaid | 0.2 | 2.0 | 7.8 | 30.6 | **1.14** |
| query-filter | 0.5 | 3.9 | 13.6 | 45.6 | **0.99** |
| query-graph | 2.2 | 26.7 | 101.7 | 443.2 | **1.14** |
| walk | 0.2 | 1.8 | 5.5 | 21.6 | **1.05** |
| validate | 0.5 | 5.4 | 22.0 | 76.8 | **1.08** |
| op-set-property | 0.5 | 5.6 | 22.8 | 82.3 | **1.10** |
| op-create-node | 0.7 | 6.3 | 21.9 | 91.3 | **1.06** |

| | 1,211n | 12,450n | 37,370n | 124,841n |
|---|---|---|---|---|
| surface bytes | 0.1 MB | 0.7 MB | 2.1 MB | 7.2 MB |
| model memory | 0.9 MB | 9.2 MB | 27.3 MB | 92.4 MB |
| derived index | 0.1 MB | 0.9 MB | 2.9 MB | 10.7 MB |

## `sarib import` (markdown → graph skeleton, no model extraction)

| nodes | time | output |
|---|---|---|
| 1,000 | 25.0 ms | 0.1 MB |
| 10,000 | 252.4 ms | 0.5 MB |
| 30,000 | 888.8 ms | 1.7 MB |
| 100,000 | 3,638.2 ms | 5.9 MB |
| _slope_ | **1.08** | |

## Before — `0e8010f`, measured in a worktree on the same machine

Small sizes only: the pre-remediation code cannot reach the sizes above in reasonable time. That is the finding, not a gap in the method.

| path | 603n | 1,211n | 2,477n | 4,922n | slope |
|---|---|---|---|---|---|
| parse | 13.9 | 42.4 | 228.9 | 540.6 | **1.81** |
| canon | 18.1 | 65.2 | 267.3 | 892.7 | **1.87** |
| fmt | 13.7 | 53.2 | 280.8 | 821.9 | **1.99** |
| outline | 52.4 | 213.5 | 1,006.6 | 3,316.6 | **2.00** |
| board | 13.4 | 52.8 | 226.0 | 821.5 | **1.97** |
| mermaid | 0.1 | 0.2 | 0.6 | 0.8 | **1.03** |
| query-filter | 13.6 | 55.4 | 216.6 | 840.5 | **1.96** |
| query-graph | 46.7 | 186.2 | 815.8 | 3,236.8 | **2.02** |
| walk | 12.6 | 74.9 | 225.3 | 828.9 | **1.95** |
| validate | 0.2 | 0.5 | 1.0 | 2.0 | **1.02** |
| op-set-property | 0.2 | 0.5 | 0.9 | 1.8 | **0.99** |
| op-create-node | 0.2 | 0.6 | 1.0 | 1.8 | **0.94** |

### Same size, both trees (~1,000 nodes)

| path | before | after | factor |
|---|---|---|---|
| parse | 42.4 ms | 11.0 ms | **4x** |
| canon | 65.2 ms | 9.5 ms | **7x** |
| fmt | 53.2 ms | 1.9 ms | **28x** |
| outline | 213.5 ms | 1.3 ms | **161x** |
| board | 52.8 ms | 0.5 ms | **105x** |
| mermaid | 0.2 ms | 0.2 ms | **1x** |
| query-filter | 55.4 ms | 0.5 ms | **119x** |
| query-graph | 186.2 ms | 2.2 ms | **83x** |
| walk | 74.9 ms | 0.2 ms | **470x** |
| validate | 0.5 ms | 0.5 ms | **1x** |
| op-set-property | 0.5 ms | 0.5 ms | **1x** |
| op-create-node | 0.6 ms | 0.7 ms | **1x** |

(before at 1,211 nodes vs after at 1,211 nodes)

## Reading this

- **Parse was the worst symptom, not query.** `order=len(doc.children(...))` sat inside the parse loop, so a large file could not be *loaded*, let alone queried.
- **Per-op edit cost is still O(N+E)** (`op-set-property` / `op-create-node` above): every op runs a full-document `check_invariants()`. That is unchanged from before this work and is a known, filed follow-up — narrowing it to the touched ids measured as no better once the cycle check became O(N) amortized, and it would have changed *when* a violation is detected. See `plans/01-scale-remediation.md` §10.
- **The derived index is memory the file does not pay for.** It is rebuilt on demand and never serialized (P17), so it costs RAM, not bytes on disk.
- `sarib import` is the on-ramp a new user hits first, which is why it is measured separately from the core paths.
- **The same-size factors below are a floor, not a headline.** They compare at ~1,000 nodes because that is where both trees can be measured; the gap is the difference between a ~2.0 and a ~1.1 exponent, so it widens with every doubling.
- **`validate` and the two `op-*` rows were already linear before this work** and are unchanged (factor ~1x). Nothing here regressed; the wins are concentrated in the paths that walked or re-sorted the whole document.

# Scaling report — reference implementation

Generated 2026-07-28 by `python bench/scale_probe.py --report` · python 3.13.7 · single machine, best-of-3.

This is the evidence RM11 ("large KBs blow parse/query/memory") never had, and the answer to RM8's early-warning trigger ("query/write latency unacceptable at 100k nodes"). The pass/fail gate is **G9** in `bench/gate-report.md`; this report is the detail behind it.

Times are milliseconds. `slope` is the least-squares exponent of log(time) vs log(nodes): ~1.0 is linear, ~2.0 is quadratic. **The exponent is the finding; the absolute constants are machine- and noise-dependent.**

## After — current tree, 1,000 to 100,000 nodes

| path | 1,211n | 12,450n | 37,370n | 124,841n | slope |
|---|---|---|---|---|---|
| parse | 6.9 | 77.3 | 233.7 | 1,077.0 | **1.08** |
| canon | 5.7 | 68.8 | 192.0 | 796.0 | **1.06** |
| fmt | 1.3 | 16.7 | 53.4 | 245.9 | **1.12** |
| outline | 0.8 | 11.9 | 35.8 | 192.4 | **1.16** |
| board | 0.3 | 3.8 | 13.8 | 54.8 | **1.11** |
| mermaid | 0.1 | 1.3 | 5.0 | 25.3 | **1.18** |
| query-filter | 0.3 | 3.0 | 8.2 | 37.1 | **1.03** |
| query-graph | 1.4 | 19.9 | 62.2 | 367.6 | **1.19** |
| walk | 0.092 | 1.0 | 3.6 | 17.2 | **1.12** |
| validate | 0.3 | 3.8 | 13.4 | 65.1 | **1.13** |
| op-set-property | 0.001 | 0.001 | 0.001 | 0.001 | **0.05** |
| op-create-node | 0.3 | 3.4 | 15.3 | 90.6 | **1.23** |

| | 1,211n | 12,450n | 37,370n | 124,841n |
|---|---|---|---|---|
| surface bytes | 0.1 MB | 0.7 MB | 2.1 MB | 7.2 MB |
| model memory | 0.9 MB | 9.2 MB | 27.3 MB | 92.4 MB |
| derived index | 0.1 MB | 0.9 MB | 2.9 MB | 10.7 MB |

## `sarib import` (markdown → graph skeleton, no model extraction)

| nodes | time | output |
|---|---|---|
| 1,000 | 35.7 ms | 0.1 MB |
| 10,000 | 335.7 ms | 0.5 MB |
| 30,000 | 1,143.1 ms | 1.7 MB |
| 100,000 | 4,621.4 ms | 5.9 MB |
| _slope_ | **1.05** | |

## Before — `0e8010f`, measured in a worktree on the same machine

Small sizes only: the pre-remediation code cannot reach the sizes above in reasonable time. That is the finding, not a gap in the method.

| path | 603n | 1,211n | 2,477n | 4,922n | slope |
|---|---|---|---|---|---|
| parse | 9.4 | 31.5 | 108.3 | 532.1 | **1.90** |
| canon | 12.6 | 48.5 | 163.0 | 996.7 | **2.04** |
| fmt | 9.4 | 43.3 | 156.7 | 867.7 | **2.12** |
| outline | 35.7 | 147.4 | 624.1 | 3,505.3 | **2.17** |
| board | 9.0 | 36.7 | 158.3 | 854.3 | **2.16** |
| mermaid | 0.071 | 0.1 | 0.3 | 1.3 | **1.35** |
| query-filter | 9.2 | 39.2 | 151.9 | 820.0 | **2.11** |
| query-graph | 34.2 | 123.6 | 797.8 | 4,246.6 | **2.33** |
| walk | 8.9 | 38.4 | 149.4 | 827.9 | **2.13** |
| validate | 0.2 | 0.4 | 0.7 | 2.2 | **1.19** |
| op-set-property | 0.2 | 0.3 | 1.1 | 2.4 | **1.27** |
| op-create-node | 0.2 | 0.4 | 1.2 | 2.6 | **1.19** |

### Same size, both trees (~1,000 nodes)

| path | before | after | factor |
|---|---|---|---|
| parse | 31.5 ms | 6.9 ms | **5x** |
| canon | 48.5 ms | 5.7 ms | **9x** |
| fmt | 43.3 ms | 1.3 ms | **33x** |
| outline | 147.4 ms | 0.8 ms | **176x** |
| board | 36.7 ms | 0.3 ms | **116x** |
| mermaid | 0.1 ms | 0.1 ms | **1x** |
| query-filter | 39.2 ms | 0.3 ms | **132x** |
| query-graph | 123.6 ms | 1.4 ms | **91x** |
| walk | 38.4 ms | 0.1 ms | **416x** |
| validate | 0.4 ms | 0.3 ms | **1x** |
| op-set-property | 0.3 ms | 0.0 ms | **528x** |
| op-create-node | 0.4 ms | 0.3 ms | **1x** |

(before at 1,211 nodes vs after at 1,211 nodes)

## Reading this

- **Parse was the worst symptom, not query.** `order=len(doc.children(...))` sat inside the parse loop, so a large file could not be *loaded*, let alone queried.
- **A point edit is now effectively free** (`op-set-property` above, flat across every size): op-time validation is scoped to the ids the op touched (D-065), so a 50-token edit no longer re-checks the whole document. It was ~82ms at 125k nodes before that change. **Structural ops are still O(N)** (`op-create-node`): they invalidate the derived index, and the next read rebuilds it. Incremental index maintenance is the open follow-up — see `plans/01-scale-remediation.md` §10 F1.
- **The derived index is memory the file does not pay for.** It is rebuilt on demand and never serialized (P17), so it costs RAM, not bytes on disk.
- `sarib import` is the on-ramp a new user hits first, which is why it is measured separately from the core paths.
- **The same-size factors below are a floor, not a headline.** They compare at ~1,000 nodes because that is where both trees can be measured; the gap is the difference between a ~2.0 and a ~1.1 exponent, so it widens with every doubling.
- **`validate` and the two `op-*` rows were already linear before this work** and are unchanged (factor ~1x). Nothing here regressed; the wins are concentrated in the paths that walked or re-sorted the whole document.

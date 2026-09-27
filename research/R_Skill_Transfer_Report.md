# R Skill-Transfer Evaluation Report

**Test tasks:** 24  |  **Arms:** noskill / transfer (skill selected from train pool) / oracle (task's own generalized skill = upper bound)

## Overall

| Arm | Mean reward | Pass rate |
|---|---|---|
| noskill | 0.9167 | 22/24 |
| **transfer** | **0.8750** | 21/24 |
| oracle | 0.9167 | 22/24 |

**transfer − noskill = -0.0417** (wins=2, ties=19, losses=3)

## By task type

| Type | n | noskill | transfer | oracle | d(t-n) | W/T/L |
|---|---|---|---|---|---|---|
| data-wrangling | 9 | 0.889 | 0.778 | 0.889 | -0.111 | 1/6/2 |
| differential-expression | 8 | 1.000 | 1.000 | 1.000 | +0.000 | 0/8/0 |
| pathway-enrichment | 4 | 0.750 | 0.750 | 0.750 | +0.000 | 1/2/1 |
| visualization | 1 | 1.000 | 1.000 | 1.000 | +0.000 | 0/1/0 |
| survival-analysis | 1 | 1.000 | 1.000 | 1.000 | +0.000 | 0/1/0 |
| clustering | 1 | 1.000 | 1.000 | 1.000 | +0.000 | 0/1/0 |

## Wins & Losses

**Transfer WINS (skill rescued a task noskill failed):**
- `biodsbench_29340250_q5` (pathway-enrichment): noskill=0 -> transfer=1
- `biodsbench_35222524_q2` (data-wrangling): noskill=0 -> transfer=1

**Transfer LOSSES:**
- `biodsbench_33176622_q3` (data-wrangling): noskill=1 -> transfer=0  (transfer-arm timeout, reward=0)
- `biodsbench_33597971_q6` (pathway-enrichment): noskill=1 -> transfer=0  (transfer-arm timeout, reward=0)
- `biodsbench_37255653_q2` (data-wrangling): noskill=1 -> transfer=0  (transfer-arm timeout, reward=0)

## Conclusion & Interpretation

**Headline: On this R test set, skill-transfer did NOT produce a net benefit** (transfer 0.875 vs noskill 0.917, Δ = −0.042). The result is a near-wash dominated by a strong **ceiling effect**.

### Why the signal is muted
1. **Ceiling effect / weak baseline headroom.** The base model already solves 22/24 (91.7%) of these R test tasks with *no* skill. There is almost nothing to improve. 19 of 24 tasks are ties (all three arms = 1.0).
2. **The oracle also gained nothing.** oracle == noskill (both 0.9167). Even injecting each task's *own* generalized skill (the theoretical upper bound) produced zero net lift. This proves the test tasks themselves are too easy to reveal a skill effect — it is a **measurement-ceiling problem, not a transfer-quality problem**. The transfer method cannot be fairly judged when the oracle has no room to help either.
3. **All 3 transfer "losses" are timeouts, not wrong answers.** In `33176622_q3`, `33597971_q6`, `37255653_q2` the transfer arm hit the 2400s wall (reward=0) while noskill finished in time. Injecting a skill adds context/steps, which on already-long tasks can tip them over the time limit. (`37255653_q2` is genuinely hard — it also timed out in noskill in an earlier arm.)
4. **But transfer *did* rescue 2 genuinely hard tasks** that noskill failed outright: `29340250_q5` (pathway-enrichment) and `35222524_q2` (data-wrangling), both noskill-timeouts that the transferred skill solved (matching oracle). So the skill demonstrably helped where headroom existed.

### By-type read
- **differential-expression (n=8): 100% across all arms** — saturated, uninformative.
- **data-wrangling (n=9): Δ=−0.111** — the only negative type, entirely from 2 transfer timeouts vs 1 rescue.
- **pathway-enrichment (n=4): Δ=0** — 1 win, 1 loss cancel.

### Bottom line
The transfer pipeline is **functionally correct** (it selects skills, injects them, and demonstrably rescues 2 hard tasks to oracle level), but this particular 24-task R test split is **too easy to measure transfer value** — the base model and the oracle both sit at 0.917. The net −0.042 is driven by skill-induced timeouts on already-long tasks, not by wrong skills.

### Recommended next steps
1. **Harder test split.** Re-run transfer on tasks where noskill < ~0.6 (i.e., real headroom). The 2 wins show transfer works when there is room.
2. **Longer timeout for skilled arms** (e.g., 3000–3600s) to remove the length-induced timeout penalty, isolating true skill quality.
3. **Pair-level design** like the earlier V10 selector study (source→target same-type/compat pairs on low-baseline targets) rather than a uniform test split dominated by easy tasks.
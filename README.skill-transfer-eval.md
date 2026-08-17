# BioMniBench Skill Transfer Evaluation

## Directory Structure

```
/data/yjh/skill-transfer-eval/
├── baseline/              # No-skill baseline runs (DeepSeek-V4-Flash)
├── with-skill/            # With-skill runs (DeepSeek-V4-Flash + skill bundles)
├── skills/                # Generalized-transfer skills (for cross-task transfer)
├── generalized/           # Generalized-skill evaluation runs
├── summary/               # Collected results summaries
│   ├── all_results.json   # Machine-readable JSON
│   ├── results_table.txt  # Human-readable table
│   └── missing_tasks.txt  # Tasks still missing results
├── logs/                  # Run logs (organized by batch timestamp)
├── collect_results.py     # Standalone results collector
├── run_all_biomnibench.sh # Batch runner for all 50 tasks
└── README.md              # This file
```

## Key Facts

| Asset | Count | Location |
|---|---|---|
| Total tasks | 50 | `/data/yjh/biomnibench-organized/` |
| Skill bundles (DeepSeek-V4) | 50 | `/data/yjh/biomnibench-skill-bundles/` |
| Harness | patched | `/tmp/my_claude_biomnibench_fixed/` |
| Bun runtime | v1.3.14 | `/tmp/bun_extract/bun-linux-x64/bun` |
| Judge model | Gemini 3.1 Pro (`Vendor2/Gemini-3.1-pro`) | via gpugeek API |
| Solver model | DeepSeek-V4-Flash | via gpugeek API |

## Running

```bash
# Full batch: all 50 tasks, baseline + with-skill, 3 reps each, 4 concurrent
bash /data/yjh/skill-transfer-eval/run_all_biomnibench.sh 4 3

# Collect results
python3 /data/yjh/skill-transfer-eval/collect_results.py

# Watch for missing tasks
python3 /data/yjh/skill-transfer-eval/collect_results.py --watch
```

## History

- **2026-06-26**: First baseline/skill runs with Claude-4.7-opus (6 tasks only)
- **2026-07-02**: Skill bundles generated with DeepSeek-V4-Flash (50 tasks)
- **2026-07-21**: Full evaluation with DeepSeek-V4-Flash (baseline + with-skill, all 50 tasks)
- **2026-08-04**: Fixed feedback leakage bug (judge no longer passes reasoning text to model)

---

## 📊 Results Quick Reference

### Result Types

| 类型 | 含义 | 来源 | 评分尺度 |
|:--|:--|:--|:--:|
| **Baseline** | 无 skill 辅助的 agent 直接完成任务 | `baseline/` 目录, `summary/gemini_results.json` | Gemini: 0-100, DeepSeek: 0-1 |
| **Oracle** | 带 oracle skill 的 agent 完成任务 | `with-skill/` 目录, `summary/gemini_results.json` | Gemini: 0-100, DeepSeek: 0-1 |
| **Pruned** | 由 generalized skill 裁剪后部署到目标任务的 skill | `skills/<task>/skills/generalized-pruned-transfer/` | 无评分，纯 skill 文件 |
| **Transfered** | 使用 generalized skill 进行技能迁移的结果 | `generalized/` 和 `transfer/` 目录 | Gemini: 0-100, DeepSeek: 0-1 |

### 查看结果

```bash
# 1. Gemini 基线/oracle (0-100, 推荐参考)
cat /data/yjh/skill-transfer-eval/summary/gemini_results.json

# 2. DeepSeek 基线/oracle (0-1)
cat /data/yjh/skill-transfer-eval/summary/all_results.json

# 3. 所有实验结果索引 (自动生成，包含全部4类结果)
cat /data/yjh/skill-transfer-eval/results_index.json

# 4. 重新生成索引 (新增实验后运行)
python3 /data/yjh/skill-transfer-eval/index_results.py
```

### 实验结果索引文件结构

`results_index.json` 包含 4 个顶层字段:

```json
{
  "baselines": { "da-1-3": { "gemini": 92, "deepseek": 0.95 }, ... },
  "oracles":   { "da-1-3": { "gemini": 100, "deepseek": 0.92 }, ... },
  "pruned_skills": { "da-1-3": [{ "skill_name": "generalized-pruned-transfer", ... }], ... },
  "transfers": [ { "type": "expand-cross", "source": "da-4-1", "target": "da-15-7", "reward": 0.60, ... }, ... ],
  "summary": { "baseline_avg_gemini": 76.94, "by_type": { "expand-within": { "avg_reward": 76.7, ... } } }
}
```

### 实验类型速查

| 实验类型 | 日期 | 说明 | 平均分 |
|:--|:--:|:--|:--:|
| generalized-transfer | 08-04 | 初版 generalized skill transfer | 72 |
| generalized-cross | 08-05 | 跨类别 generalized | 57 |
| raw-cross | 08-06 | 无 generalized 的跨类别对照 | 43 |
| generalized-within | 08-06 | 同类 generalized 新设计 | 25 |
| raw-within | 08-06 | 同类 raw 对照 | 23 |
| expand-within | 08-09~10 | 主实验: 扩展同类迁移 (22 pairs) | 76.7 |
| expand-cross | 08-09~10 | 主实验: 扩展跨类迁移 (22 pairs) | 77.1 |

### 本地报告

- `expand_gemini_experiment_report.md` — 仅 expand 实验 (22+22 pairs)
- `all_august_experiments_report.md` — 所有 2026年8月实验综合报告
- **2026-08-04**: Fixed collect_results.py (reads from .judge_private/ judge results instead of run_summary.json)

## Known Issues

### 1. Judge Feedback Leakage (Fixed)

**Problem**: In multi-round runs, the judge's `overall_reasoning` text was passed to the agent as feedback, leaking rubric details. This meant the model received hints about what it did wrong, artificially inflating multi-round improvements.

**Fix** (`judgeRunner.ts`): The `mapBioMniBenchJudgeResult()` function now only returns `"Score: X/100"` — no reasoning text.

**See**: `FEEDBACK_LEAKAGE_FIX.md` for full details.

### 2. `run_summary.json` reward = 0.0 (Workaround in collect_results.py)

**Problem**: The `reward` field in `run_summary.json` is always `0.0` because the file is overwritten by a later re-judging process (Gemini 3.1 Pro) that writes `{ total_score: 0, criteria: {} }`.

**Workaround** (`collect_results.py`): The script now reads from `.judge_private/` directory's `judge_result_round_*.json` files instead of `run_summary.json`. For runs with API errors, it falls forward to the first successful round.

### 3. Judge API Retry Mechanism (Fixed)

**Problem**: No retry logic in `llm_judge_qwen.py`. API errors (429 rate limit, 400 overloaded) caused complete round waste — agent's work was never evaluated but received `"Score: 0/100"`.

**Fix** (`llm_judge_qwen.py`): Added exponential backoff retry with jitter:
- Up to 5 retries per judge call
- Initial delay: 5s, doubled each retry (5s → 10s → 20s → 40s → 80s)
- Random jitter (0.5-1.5x) to avoid thundering herd
- Retries on: 429, 400, 5xx, timeout, connection errors

### 4. Limited Repetitions

Most tasks have only 1 rep (7 baseline tasks have 2-3 reps, 8 with-skill tasks have 2-3 reps). This limits statistical reliability.

## Transfer-Skill Test Plan

See `TRANSFER_SKILL_TEST_PLAN.md` for the complete experimental design, including:

- **Within-Domain Transfer** (da-x-a → da-x-b): Verify skill extraction improves same-domain tasks
- **Cross-Domain Transfer** (da-x-a → da-y-b): Verify generalized skills transfer across domains
- **Judge retry**: Exponential backoff for API errors to prevent wasted rounds

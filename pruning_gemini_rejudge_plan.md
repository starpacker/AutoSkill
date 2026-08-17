# BioDSBench Pruning & Gemini Re-Judge Plan

## 概述

本文档规划了三个主要工作流的执行方案，包括对应的数据路径、脚本位置和执行顺序。

---

## Workflow 1: Gemini Re-Judge — 所有任务的 Baseline 与 Oracle Skill

### 目标
将所有 50 个 BioDSBench 任务的 **baseline** 和 **oracle-skill** 评估结果，使用 `Gemini 3.1 Pro`（`Vendor2/Gemini-3.1-pro`）作为 judge 模型重新评分。

### 原理
现有评估使用 `Vendor3/qwen3.5-plus` 作为 judge。论文原文使用 Gemini 3.1 Pro。需要切换 judge 模型以获得与论文可比的结果。**Agent 的输出（answer.txt + trace.md）保持不变**，只需要重新运行 judge 步骤。

### 具体路径

| 项目 | 路径 |
|:--|:--|
| Harness 代码 | `/tmp/my_claude_biomnibench_fixed/` |
| Judge 脚本 | `/tmp/my_claude_biomnibench_fixed/llm_judge_qwen.py` |
| 模型配置 | `/tmp/my_claude_biomnibench_fixed/config/eval-model-profiles.local.json` |
| 任务数据 | `/data/yjh/biomnibench-organized/` |
| Baseline 结果 | `/data/yjh/skill-transfer-eval/baseline/` |
| Oracle 结果 | `/data/yjh/skill-transfer-eval/with-skill/` |
| 汇总结果 | `/data/yjh/skill-transfer-eval/summary/` |
| 收集脚本 | `/data/yjh/skill-transfer-eval/collect_results.py` |

### 数据量

- **Baseline**: 50 个任务，每个有 `answer.txt` + `trace.md`
- **Oracle skill**: 50 个任务，每个有 `answer.txt` + `trace.md`
- **总计**: 100 次 judge 调用

### 执行方案

**方案 A（推荐）: 利用现有 eval 框架，仅切换 QWEN_MODEL**

```bash
cd /tmp/my_claude_biomnibench_fixed

# 对单个任务重新 judge:
QWEN_MODEL=Vendor2/Gemini-3.1-pro \
  python3 llm_judge_qwen.py \
    <trace_path> \
    <answer_path> \
    <rubric_path> \
    <output_path>
```

**方案 B: 批量 re-judge 脚本**

需要批量 re-judge 所有 baseline 和 oracle 任务的输出。judge 的输入文件：
- `outputs/trace.md` — agent 的分析轨迹
- `outputs/answer.txt` — agent 的最终答案

Rubric 文件位置：每个任务目录下的 `private/evaluation/judge_rubric.txt`（需要从任务数据目录确认）

**关键环境变量**:
- `QWEN_MODEL=Vendor2/Gemini-3.1-pro` — judge 模型
- `QWEN_API_KEY=00gcclg9l39y9p01000dhjzolag1q2hk00901kh1` — API key
- `QWEN_BASE_URL=https://api.gpugeek.com/v1` — API 端点

### 预期输出

- 每个 re-judge 调用产生一个 `judge_result.json` 文件
- 汇总后得到完整的 **50-task baseline × oracle 结果表**（Gemini 评分版）
- 与当前 qwen3.5 评分结果对比

---

## Workflow 2: Pruning — 所有 50 个 Oracle Skill 的剪枝

### 目标
对每个任务的 oracle skill bundle，逐步剪掉操作（operations），找到**在 source task 上效果不降的 min-core skill**。

### 判断标准
剪掉一个操作后，对 source task 重新评估，如果：
- 分数 **比 baseline 好**（即有 skill 比无 skill 好）
- **且** 分数 ≥ **oracle_score - 0.1**（与完整 oracle skill 相比下降不超过 0.1）

→ 则该剪枝可接受，继续尝试剪下一个。

### 数据路径

| 项目 | 路径 |
|:--|:--|
| Oracle skill bundles | `/data/yjh/biomnibench-skill-bundles/{task}/` |
| 技能清单 | `{bundle}/oracle_skill_manifest.json` |
| 技能内容 | `{bundle}/skills/{skill_name}/SKILL.md` |
| 操作资源文件 | `{bundle}/skills/{skill_name}/resources/op_*.md` |
| 任务数据 | `/data/yjh/biomnibench-organized/{task}/` |
| Ablation 输出 | `/data/yjh/skill-transfer-eval/ablations/{task}/` |
| Ablation 日志 | `/data/yjh/skill-transfer-eval/logs/ablation_{task}.log` |

### 框架已有工具

Harness 内置了完整的 ablation 框架：

| 文件 | 功能 |
|:--|:--|
| `src/oracle-skills/ablate.ts` | 优先级贪心剪枝算法 |
| `src/oracle-skills/lifecyclePrune.ts` | 生命周期剪枝管理 |
| `src/oracle-skills/cli.ts` | CLI 入口（`ablate` 子命令） |
| `src/oracle-skills/lifecycleConfig.ts` | 剪枝配置 |

### 现有 Ablation 候选顺序

已有 3 个任务的 ablation 配置（来自 `candidate_order.json`）：

**da-5-1**（目标优先排序）:
```
op_070_solver_rank_targets (priority=80)  → 最优先尝试剪掉
op_090_postprocess_limitations (priority=80)
op_060_parameter_estimation_pan_essential (priority=70)
op_050_domain_model_tier_stratification (priority=60)
op_080_domain_model_biological_rationale (priority=60)
op_040_feature_extraction_tier_merge (priority=50)
op_030_preprocessing_filter_pdac (priority=40)
op_020_data_loading (priority=30)
op_100_validation (priority=20)
op_010_contract (priority=10)              → 最后尝试剪掉
```

**da-18-5**:
```
op_090_results_reporting (80)
op_080_mutual_exclusivity_test (70)
op_070_frequency_calculation (60)
op_050_mapk_gene_set (50)
op_060_alteration_identification (50)
op_030_cohort_selection (40)
op_020_data_loading_clinical (30)
op_040_data_loading_cna_mutations (30)
op_100_validation (20)
op_010_contract (10)
```

**da-19-4**:
```
op_090_interpretation (60)
op_030_union_peaks (50)
op_020_data_loading (40)
op_070_enhancer_anchors (40)
op_040_quantification (30)
op_060_reduced_regions (30)
op_080_enhancer_evaluation (30)
op_050_diff_analysis (20)
op_100_validation (20)
op_010_contract (10)
```

### 执行方案

**Step 1: 对每个任务运行 ablation**

```bash
cd /tmp/my_claude_biomnibench_fixed

export QWEN_MODEL=Vendor2/Gemini-3.1-pro   # 使用 Gemini 作为 judge

bun src/oracle-skills/cli.ts ablate \
  --bundle /data/yjh/biomnibench-skill-bundles/{task} \
  --out /data/yjh/skill-transfer-eval/ablations/{task} \
  --task {task} \
  --tasks-dir /data/yjh/biomnibench-organized \
  --model-profile gpugeek-deepseek-v4-flash \
  --model-config config/eval-model-profiles.local.json
```

**Step 2: 收集 ablation 结果**

每个 ablation 运行输出到 `{out_dir}/eval/` 下，包含：
- `run_summary.json` — 每轮评估的 reward
- `records.jsonl` — 完整的 ablation 记录（含每个变体的 pass/fail 判断）

**Step 3: 确定 min-core skill**

基于 ablation 记录，找到所有可通过剪枝的 operations，构建 min-core 变体：

```python
# 剪枝判断逻辑
def should_accept_prune(pruned_score, baseline_score, oracle_score):
    """Prune accepted if skill still beats baseline and doesn't drop too much."""
    return (pruned_score >= baseline_score and 
            pruned_score >= oracle_score - 0.1)
```

**Step 4: 生成 min-core skill bundle**

Ablation 框架自动生成 variant 目录，包含渲染后的 SKILL.md。如果框架没有自动产生，则手动从 `ablate.ts` 取 `renderOracleSkillVariant()` 的结果。

### 预期输出

- 每个任务一个 `min-core` skill bundle
- 结构：`/data/yjh/skill-transfer-eval/pruned_bundles/{task}/skills/min-core-{task}/`
- 包含：`oracle_skill_manifest.json`（pruned manifest）、`SKILL.md`（min-core 版）、`resources/`（保留的操作资源文件）

---

## Workflow 3: Transfer — 用 Pruned Skills 做迁移测试

### 目标
对 8 个源任务（da-5-1, da-8-1, da-13-5, da-17-1, da-18-5, da-19-3, da-19-4, da-26-2），使用 **pruned min-core skill** 做泛化，然后在目标任务上测试迁移效果。

### 三类对比

| 条件 | 说明 | 状态 |
|:--|:--|:--:|
| **Baseline** | 无 skill，纯 agent 能力 | ✅ 已有（需 Gemini re-judge） |
| **Oracle transfer** | 完整 oracle skill 泛化后迁移 | ✅ 已有 8 对（需 Gemini re-judge） |
| **Pruned transfer** | min-core skill 泛化后迁移 | 🔄 待执行 |

### 数据路径

| 项目 | 路径 |
|:--|:--|
| 泛化脚本 | `/data/yjh/skill-transfer-eval/generalize_skill.py` |
| 现有泛化结果 | `/data/yjh/skill-transfer-eval/generalized_skills/{source}/SKILL.md` |
| 迁移结果（现有） | `/data/yjh/skill-transfer-eval/transfer/` |
| 迁移结果（pruned） | `/data/yjh/skill-transfer-eval/transfer_pruned/` |
| 部署脚本 | `/data/yjh/skill-transfer-eval/deploy_expanded.sh` |
| 迁移启动脚本 | `/data/yjh/skill-transfer-eval/launch_transfer_24.sh` |

### 执行方案

**Step 1: 泛化 min-core skill**

```bash
cd /data/yjh/skill-transfer-eval

# 修改 generalize_skill.py 以从 pruned_bundles 读取
SKILL_BUNDLES_DIR=/data/yjh/skill-transfer-eval/pruned_bundles \
  python3 generalize_skill.py --source da-5-1
```

**Step 2: 部署到目标任务**

```bash
# 复制 generalized pruned skill 到目标任务的 skills 目录
mkdir -p skills/{target}/skills/generalized-transfer-pruned
cp generalized_skills_pruned/{source}/SKILL.md skills/{target}/skills/generalized-transfer-pruned/
```

**Step 3: 运行迁移评估**

```bash
cd /tmp/my_claude_biomnibench_fixed

export QWEN_MODEL=Vendor2/Gemini-3.1-pro

bun src/harness/evaluation/cli.ts \
  --task {target} \
  --tasks-dir /data/yjh/biomnibench-organized \
  --runs-dir /data/yjh/skill-transfer-eval/transfer_pruned \
  --max-rounds 5 --timeout-seconds 7200 \
  --concurrency 1 --temperature 1 --thinking disabled \
  --timestamp transfer_pruned_{source}_to_{target}
```

### 8 个源任务对应的迁移目标

| 源任务 | 源任务描述 | 目标任务（Oracle 测试过的） | 目标任务（L1 扩展待测） |
|:--|:--|:--|:--|
| da-5-1 | PDAC 靶点优先级排序 | da-5-3 | da-26-2, da-25-1, da-1-3 |
| da-8-1 | Bread-spiker 分类 | da-8-3 | da-8-2, da-1-4, da-13-6 |
| da-13-5 | 性别关联重叠分析 | da-13-6 | da-13-3, da-13-1, da-6-5 |
| da-17-1 | SLE 祖先成分分析 | da-17-5 | da-17-3, da-14-3, da-12-2 |
| da-18-5 | MAPK/ESR1 互斥性 | da-18-7 | da-18-1, da-10-1, da-1-3 |
| da-19-3 | RUNX1 峰分析 | da-19-4 | da-19-1, da-19-6, da-8-2 |
| da-19-4 | H3K27ac ChIP-seq | da-19-6 | da-19-3, da-19-1, da-20-3 |
| da-26-2 | 生物标志物识别 | da-26-4 | da-1-3, da-14-1, da-14-8 |

### 预期输出

- 每个源任务 × 目标任务对产生一个 `run_summary.json`（含 Gemini judge 评分）
- 汇总表：baseline vs oracle_transfer vs pruned_transfer

---

## 执行顺序与依赖

```
Workflow 1: Gemini Re-Judge (Baseline + Oracle)
  │
  ├── 依赖: 已有 50×2 个 agent 输出（answer.txt + trace.md）
  │
  ├── 输出: 100 个 Gemini-scored judge_result.json
  │
  └── 耗时: ~100 次 API 调用，每次 ~30s → ~50 分钟
       (可批量并行)

Workflow 2: Pruning (50 tasks)
  │
  ├── 依赖: Workflow 1 完成（因为 judge 需要 Gemini）
  │
  ├── 每任务: 1 baseline eval + N 个 ablation eval（N=操作数, 8-10）
  ├── 总耗时: 50 × (1 + 8) × ~10min = ~4500 分钟
  │    → 需要分批并行（4-8 并发）
  │
  └── 输出: 50 个 min-core skill bundles

Workflow 3: Transfer (Pruned Skills)
  │
  ├── 依赖: Workflow 2 完成（min-core skills 就绪）
  │
  ├── 8 源任务 × 4 目标任务 = 32 个迁移测试
  ├── 每测试: ~10-15 分钟
  ├── 总耗时: 32 × 12min = ~384 分钟
  │    → 可 4-8 并发，约 1-2 小时
  │
  └── 输出: 32 个 Gemini-scored transfer results
```

---

## 附录：关键文件参考

### Harness CLI 用法

```bash
# 标准评估
bun src/harness/evaluation/cli.ts \
  --task <task_id> \
  --tasks-dir <tasks_dir> \
  --runs-dir <runs_dir> \
  --max-rounds 5 --timeout-seconds 7200 \
  --concurrency 1 --temperature 1 --thinking disabled \
  --timestamp <timestamp>

# 带 skill 的评估
# 技能放在 runs-dir 同级 ../skills/{task}/skills/{skill_name}/SKILL.md
# 或者在 run 目录下使用 skills/ 子目录

# Ablation
bun src/oracle-skills/cli.ts ablate \
  --bundle <bundle_dir> \
  --out <ablations_dir> \
  --task <task_id> \
  --tasks-dir <tasks_dir> \
  --model-profile <profile> \
  --model-config <config_path>
```

### Judge 模型配置

当前 `eval-model-profiles.local.json` 中已定义：
```json
{
  "defaultProfile": "gpugeek-deepseek-v4-flash",
  "profiles": {
    "gpugeek-deepseek-v4-flash": {
      "provider": "anthropic-compatible",
      "baseUrl": "https://api.gpugeek.com",
      "apiKeyEnv": "ANTHROPIC_API_KEY",
      "model": "Vendor3/DeepSeek-V4-Flash"
    }
  }
}
```

**需要添加 Gemini profile** 或直接通过环境变量 `QWEN_MODEL` 覆盖：
```bash
export QWEN_MODEL=Vendor2/Gemini-3.1-pro
```

### 环境变量汇总

| 变量 | 当前值 | 说明 |
|:--|:--|:--|
| `ANTHROPIC_API_KEY` | `00gcclg9l39y9p01000dhjzolag1q2hk00901kh1` | Solver API key |
| `ANTHROPIC_BASE_URL` | `https://api.gpugeek.com` | Solver API 端点 |
| `ANTHROPIC_MODEL` | `Vendor3/DeepSeek-V4-Flash` | Solver 模型 |
| `QWEN_API_KEY` | `00gcclg9l39y9p01000dhjzolag1q2hk00901kh1` | Judge API key |
| `QWEN_BASE_URL` | `https://api.gpugeek.com/v1` | Judge API 端点 |
| `QWEN_MODEL` | `Vendor3/qwen3.5-plus` → **改为 `Vendor2/Gemini-3.1-pro`** | Judge 模型 |
| `BUN` | `/tmp/bun_extract/bun-linux-x64/bun` | Bun 运行时 |
| `HARNESS` | `/tmp/my_claude_biomnibench_fixed` | Harness 代码根目录 |
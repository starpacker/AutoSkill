# R 语言任务 5 指标对比实验计划

## 1. 背景

已完成的 Python 任务（da-*）对比实验：

| 指标 | BL-RAW | WSKILL | V10 Sel | SkillOpt | Base3(GT) |
|------|--------|--------|---------|----------|-----------|
| AVG  | 0.533  | 0.875  | 0.803   | 0.495    | 0.655     |

现需对 **R 语言任务** 做同样的 5 列对比，覆盖 BL-RAW、WSKILL、V10 SEL、BASE3(GT)、SkillOpt。

---

## 2. R 任务数据概况

### 数据来源

`/data/yjh/BioDSBench_hf/`（HuggingFace 上的 BioDSBench benchmark）

- **R 任务**: 165 个（来自 25 个 unique studies），JSONL 格式
- **Python 任务**: 118 个（独立于 da-* 任务），JSONL 格式
- **格式**: 每个任务包含 `queries`、`reference_answer`（R 代码）、`test_cases`（R 断言）、`tables`、`study_data_configs` 等

### 分析类型分布（R 任务）

| 分析类型 | 任务数 | 占比 |
|---------|--------|------|
| Gene Expression & Differential Analysis | 121 | 73.3% |
| Descriptive Statistics | 80 | 48.5% |
| Enrichment & Pathway Analysis | 46 | 27.9% |
| Data Integration & Transformation | 41 | 24.8% |
| Survival Outcome Analysis | 23 | 13.9% |
| Clinical Feature Engineering | 12 | 7.3% |
| Treatment Response Visualization & Quantification | 2 | 1.2% |

> 注：一个任务可能属于多个分析类型，因此合计 > 100%。

### 评估方式差异

| 特性 | da-* 任务（现有） | R 任务（BioDSBench） |
|-----|-----------------|-------------------|
| 格式 | `task.toml` + `instruction.md` + `environment/` + `tests/` | JSONL（一行一个 task） |
| 评估方式 | LLM Judge（rubric 打分 0-1） | `test_cases` 断言（R 代码，bool 判断） |
| 运行环境 | Docker（Ubuntu + Python/R） | 需要 R 运行时 |
| 任务类型 | 端到端数据分析（agent 多轮交互） | 代码补全（单轮生成 R 代码） |
| 数据 | `environment/data/` 内嵌 | 通过 `study_data_configs` 引用外部数据 |

---

## 3. 核心挑战：R 任务适配

### 3.1 格式转换

R 任务的 JSONL 格式与现有 `da-*` 格式完全不同，需要做适配。方案有 3 个：

**方案 A（推荐）: 将 R 任务转换为 da-* 格式**

为每个选中的 R 任务生成：
- `instruction.md`：从 `queries` 提取
- `environment/Dockerfile`：标准 R 环境 Dockerfile
- `tests/`：基于 `test_cases` 生成 LLM judge rubric

**方案 B: 直接修改 harness，增加 JSONL 支持**

在 `biomnibenchAdapter.ts` 中增加对 BioDSBench JSONL 格式的检测和处理。

**方案 C: 独立脚本评估**

不经过 harness，直接写 Python 脚本：调用 LLM → 生成 R 代码 → 运行 test_cases 检查 → 记录结果。

**建议采用方案 C + 方案 A 混合**：先用独立脚本快速验证，评估可行后再做完整的 harness 适配。

### 3.2 数据依赖

R 任务的数据存储在 `/data/yjh/BioDSBench_hf/data_files/datasets/{study_id}/`。每个任务需要挂载对应的数据目录。有两种处理方式：

1. 在 Docker 中挂载数据卷
2. 将数据复制到任务目录的 `environment/data/` 下

### 3.3 评估指标

R 任务的 `test_cases` 是布尔断言，因此 reward 计算方式为：
```
reward = passed_test_cases / total_test_cases
```
这与 da-* 的 LLM judge 打分（0-1 连续值）不同，但可以作为统一的 soft score。

---

## 4. 任务选择策略：20 个 R 任务

### 4.1 分层抽样原则

从 165 个 R 任务中选取 ~20 个，按以下原则分层：

1. **分析类型覆盖**：7 种分析类型都覆盖
2. **研究来源覆盖**：从不同 study 中选取（避免同一 study 任务过多）
3. **难度分布**：参考 `test_cases` 数量（多的通常更复杂）
4. **数据可用性**：确保对应 study 的数据已下载

### 4.2 建议分配方案

| 分析类型 | 建议任务数 | 说明 |
|---------|-----------|------|
| Gene Expression & Differential Analysis | 5 | 占比最大，适当多选 |
| Descriptive Statistics | 4 | 第二大类型 |
| Enrichment & Pathway Analysis | 3 | 中等规模 |
| Data Integration & Transformation | 3 | 中等规模 |
| Survival Outcome Analysis | 2 | 少量 |
| Clinical Feature Engineering | 2 | 少量 |
| Treatment Response Visualization & Quantification | 1 | 极少 |
| **合计** | **20** | |

### 4.3 训练/测试划分

参考 da-* 任务的划分方式：

| 用途 | 任务数 | 说明 |
|-----|--------|------|
| 训练集（skill 构建） | 14 | 用于 skill-opt 训练和 skill-transfer 构建 |
| 测试集（评估） | 6 | 仅用于最终评估，不参与训练 |

> 注：BL-RAW、WSKILL、V10 SEL、BASE3(GT) 这四个指标在训练集和测试集上都需要评估。
> SkillOpt 只在测试集上评估（因为训练集就是 skill-opt 的训练数据）。

---

## 5. 5 个指标的获取方法

### 5.1 BL-RAW（基线，无 skill）

**方法**: 直接用 harness 评估，不加 system prompt（或给空 system prompt）

**命令**:
```bash
bun src/harness/evaluation/cli.ts \
  --task <task_id> \
  --tasks-dir <r_tasks_dir> \
  --runs-dir <runs_dir>/bl_raw \
  --max-rounds 3 \
  --timeout-seconds 1200 \
  --concurrency 1 \
  --temperature 1.0 \
  --thinking disabled \
  --quiet
```

**数据来源**: 运行结果中的 `run_summary.json` → `reward`

### 5.2 WSKILL（带 skill 推理）

**方法**: 使用 `skill-transfer-eval/skills/` 中对应任务的 skill 作为 system prompt

**数据来源**: 同 BL-RAW，但加上 `--system-prompt <skill_file>` 参数

### 5.3 V10 SEL（V10 selector 选择的最佳 skill）

**方法**: 使用 `skill-transfer-eval/generalized/` 中 V10 版本的 skill 作为 system prompt

**数据来源**: `generalized/{run_id}/logs/run_summary.json` → `reward`

### 5.4 BASE3(GT)（Ground Truth few-shot）

**方法**: 使用 `skill-transfer-eval/gt_fewshot_transfer/` 中的 GT fewshot 结果

**数据来源**: `gt_fewshot_transfer/{tid}_*/logs/run_summary.json` → `reward`

### 5.5 SkillOpt（skill-opt 优化后的 skill）

**方法**: 使用 skill-opt 训练产出的 best_skill.md 作为 system prompt

**命令**: 同 `evaluate_test_10tasks.py` 的方式

**数据来源**: `test_eval_{tid}_*/harness.log` 中解析 `reward`

---

## 6. 实施步骤

### 阶段 1：数据准备（1-2 天）

1. **分析 R 任务详细内容**
   - 读取 165 个 R 任务的 `queries`、`test_cases`、`reference_answer`
   - 确定每个任务的难度和复杂度
   - 筛选出 ~20 个候选任务

2. **转换任务格式**
   - 为每个 R 任务生成 `instruction.md`（从 `queries` 提取）
   - 生成标准的 R 环境 `Dockerfile`
   - 生成 `tests/rubric.txt`（基于 `test_cases` 转为 LLM judge 格式）
   - 复制数据文件到 `environment/data/` 下

3. **验证**：手动测试 1-2 个转换后的 R 任务能否在 harness 中正确运行

### 阶段 2：基线评估（2-3 天）

4. **运行 BL-RAW**：20 个任务 × 1 rep
5. **运行 WSKILL**：20 个任务 × 1 rep（需要先构建 R 任务的 skill 库）
6. **运行 BASE3(GT)**：20 个任务 × 1 rep（需要 fewshot 示例）

### 阶段 3：Skill-based 评估（3-5 天）

7. **V10 SEL**：用 V10 selector 为每个 R 任务选择最佳 skill，然后评估
8. **SkillOpt**：在 14 个训练集 R 任务上运行 skill-opt，产出 best_skill.md，然后在 6 个测试集任务上评估

### 阶段 4：汇总分析（1 天）

9. 收集所有 5 个指标的数据
10. 生成对比表格
11. 分析 R 任务 vs Python 任务的结果差异

---

## 7. 预估 Token 消耗

| 指标 | 任务数 | 每次调用 token 估算 | 总 token |
|-----|--------|-------------------|---------|
| BL-RAW | 20 | ~100K (输入) + ~10K (输出) | ~2.2M |
| WSKILL | 20 | ~120K (技能+输入) + ~10K (输出) | ~2.6M |
| V10 SEL | 20 | ~120K + ~10K | ~2.6M |
| BASE3(GT) | 20 | ~150K (fewshot+输入) + ~10K | ~3.2M |
| SkillOpt | 14 (训练) | 取决于 skill-opt 配置 | 较大 |
| SkillOpt 评估 | 6 (测试) | ~120K + ~10K | ~0.8M |
| **合计** | | | **~11.4M+** |

> SkillOpt 训练的 token 消耗取决于训练轮数（rounds），可能会显著增加总消耗。

---

## 8. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|-----|------|---------|
| R 任务格式与 harness 不兼容 | 高 | 先做 1-2 个任务的 PoC 验证 |
| R 环境依赖安装复杂 | 中 | 使用标准 R 镜像 + 逐任务安装必要包 |
| test_cases 无法直接转为 LLM judge rubric | 中 | 可以用 R 代码直接执行 test_cases 来算 reward |
| R 任务数据文件较大 | 中 | 检查数据大小，必要时只选数据量小的任务 |
| skill-opt 训练 R 任务上的 skill 效果未知 | 中 | 参考 Python 任务的优化经验 |

---

## 9. 下一步

1. **你确认这个计划是否符合预期**，特别是：
   - 20 个任务的数量是否合适
   - 14 训练 / 6 测试的划分比例是否合理
   - 是否需要优先做 PoC 验证 R 任务兼容性
2. 确认后我立即开始实施阶段 1（数据准备和格式转换）
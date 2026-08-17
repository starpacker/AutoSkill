# Skill Transfer Evaluation Tracking

> 维护人：GitHub Copilot
> 创建时间：2026-07-26
> 最后更新：2026-07-28（全面重分析——修正了 baseline artifact 并重新分类所有 37 对）
> 说明：记录所有 37 组迁移测试的源任务、目标任务，以及迁移(Pruned Transfer)与基线(Baseline)的对比。
>
> ⚠️ **重要修正（2026-07-28）**：经过对所有 37 对数据的全面重新拉取分析，发现：
> 1. **da-17-1 的 baseline=0 是 pipeline artifact**（首轮实际 judge 评分 78/100），导致 2 个 pair 的 Δ 被严重高估
> 2. **Skill 起反作用的次数（12）多于起作用的次数（7）**，净效果 = -5
> 3. **7 个 pair 的 agent 明确拒绝 skill**（blocked_but_overridden），其 Δ≈0
> 详见下方"关键发现（全面重分析）"章节。
>
> ⚠️ 数据来源说明
> - **Baseline 分数**: 来自 `server1:/data/yjh/skill-transfer-eval/summary/all_results.json`（各 task 的 baseline 条目）
> - **Pruned Transfer 分数**: 来自 `server1:/data/yjh/skill-transfer-eval/summary_pruned/transfer_pruned_results.json`
> - **每个 transfer 运行目录**: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/{target_task_id}_pruned_transfer_{source_task_id}_to_{target_task_id}/`
> - **每个 transfer 的关键文件**:
>   - `logs/run_summary.json` — Judge 评分结果
>   - `logs/trajectory.clean.jsonl` — Agent 执行轨迹（精炼版）
>   - `logs/trajectory.raw.jsonl` — Agent 执行轨迹（原始版）
>   - `outputs/trace.md` — Agent 分析报告
>   - `outputs/answer.txt` — Agent 最终输出
>   - `outputs/skill_application.json` — Skill 使用记录（部分在 `workspace/skill_application.json`）
>   - `workspace/plan.md` — Agent 计划
>   - `workspace/plans/round_01.md` — 首轮计划
> - **Skill 文件**: `server1:/data/yjh/skill-transfer-eval/generalized_skills_pruned/{source_task_id}/SKILL.md`
> - **Pruning 元数据**: `server1:/data/yjh/skill-transfer-eval/pruned_skills/{source_task_id}/`（含 ablation 结果）
> - **相似度矩阵**: `server1:/data/yjh/skill-transfer-eval/similarity/similarity_matrix.json`
> - **Ranked pairs**: `server1:/data/yjh/skill-transfer-eval/similarity/ranked_pairs.json`
> - **重评分脚本**: `server1:/data/yjh/skill-transfer-eval/batch_rejudge_gemini.py`
> - **Ablation 结果**: `server1:/data/yjh/skill-transfer-eval/summary/ablations/`
> - **Pipeline 脚本**: `server1:/data/yjh/skill-transfer-eval/run_pruned_transfer_pipeline.py`
> - **本地文件**: `c:\Users\30670\Desktop\Autoskill\skill_transfer_evaluation_tracking.md`

---

## 迁移测试总览（37 组）

| # | 源任务 | 目标任务 | 源类别 | 目标类别 | 源任务类型 | 目标任务类型 | Baseline | Pruned Transfer | Δ Baseline | 批次 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | da-17-5 | da-17-1 | immunology | immunology | cell-composition | cell-composition | 0.00 ⚠️ | **0.84** | **+0.84** 🏆 | 1 |
| 2 | da-12-4 | da-17-1 | oncology | immunology | survival-analysis | cell-composition | 0.00 ⚠️ | **0.84** | **+0.84** 🏆 | 2 |
| 3 | da-19-4 | da-19-6 | oncology | oncology | chromatin-profiling | chromatin-profiling | 0.69 | **1.00** | **+0.31** | 1 |
| 4 | da-4-7 | da-4-1 | oncology | oncology | tcr-repertoire | clustering | 0.61 | **0.86** | **+0.25** | 1 |
| 5 | da-14-8 | da-14-1 | immunology | immunology | association-testing | clustering | 0.80 | **1.00** | **+0.20** | 1 |
| 6 | da-13-6 | da-13-5 | metabolic | metabolic | cross-cohort-comparison | cross-cohort-comparison | 0.70 | **0.90** | **+0.20** | 1 |
| 7 | da-10-1 | da-6-2 | general-biology | cardiovascular | predictive-modeling | longitudinal-analysis | 0.72 | **0.92** | **+0.20** | 1 |
| 8 | da-19-4 | da-19-3 | oncology | oncology | chromatin-profiling | chromatin-profiling | 0.75 | **0.90** | **+0.15** | 2 |
| 9 | da-18-5 | da-18-7 | oncology | oncology | mutation-analysis | mutation-analysis | 0.85 | **0.95** | **+0.10** | 1 |
| 10 | da-5-1 | da-5-3 | oncology | oncology | multi-omic-integration | multi-omic-integration | 0.95 | 0.95 | +0.00 | 1 |
| 11 | da-15-2 | da-15-7 | neurology | neurology | co-expression-networks | association-testing | 0.70 | 0.70 | +0.00 | 1 |
| 12 | da-4-1 | da-14-3 | oncology | immunology | clustering | association-testing | 0.85 | 0.85 | +0.00 | 1 |
| 13 | da-10-1 | da-13-6 | general-biology | metabolic | predictive-modeling | cross-cohort-comparison | 0.60 | 0.60 | +0.00 | 1 |
| 14 | da-17-5 | da-17-3 | immunology | immunology | cell-composition | differential-expression | 0.73 | 0.73 | +0.00 | 1 |
| 15 | da-15-2 | da-15-1 | neurology | neurology | co-expression-networks | differential-expression | 1.00 | 1.00 | +0.00 | 1 |
| 16 | da-12-4 | da-12-2 | oncology | oncology | survival-analysis | pathway-enrichment | 0.60 | 0.63 | +0.03 | 1 |
| 17 | da-4-7 | da-12-2 | oncology | oncology | tcr-repertoire | pathway-enrichment | 0.60 | 0.60 | +0.00 | 2 |
| 18 | da-4-1 | da-12-2 | oncology | oncology | clustering | pathway-enrichment | 0.60 | 0.60 | +0.00 | 2 |
| 19 | da-9-1 | da-1-4 | oncology | oncology | survival-analysis | association-testing | 0.86 | 0.86 | +0.00 | 2 |
| 20 | da-15-2 | da-15-8 | neurology | neurology | co-expression-networks | multi-omic-integration | 0.63 | 0.63 | +0.00 | 2 |
| 21 | da-26-4 | da-12-2 | oncology | oncology | predictive-modeling | pathway-enrichment | 0.60 | 0.60 | +0.00 | 2 |
| 22 | da-14-8 | da-1-3 | immunology | oncology | association-testing | cell-composition | 0.95 | 0.95 | +0.00 | 2 |
| 23 | da-10-3 | da-13-6 | general-biology | metabolic | predictive-modeling | cross-cohort-comparison | 0.60 | 0.60 | +0.00 | 2 |
| 24 | da-11-1 | da-6-2 | immunology | cardiovascular | cell-cell-communication | longitudinal-analysis | 0.72 | 0.75 | +0.03 | 2 |
| 25 | da-25-1 | da-1-3 | oncology | oncology | mutation-analysis | cell-composition | 0.95 | 0.90 | -0.05 ❌ | 1 |
| 26 | da-9-1 | da-9-7 | oncology | oncology | survival-analysis | association-testing | 1.00 | 0.93 | -0.07 ❌ | 1 |
| 27 | da-19-4 | da-19-1 | oncology | oncology | chromatin-profiling | differential-expression | 0.72 | 0.63 | -0.09 ❌ | 1 |
| 28 | da-13-6 | da-13-3 | metabolic | metabolic | cross-cohort-comparison | association-testing | 1.00 | 0.87 | -0.13 ❌ | 1 |
| 29 | da-17-5 | da-14-3 | immunology | immunology | cell-composition | association-testing | 0.85 | 0.71 | -0.14 ❌ | 2 |
| 30 | da-25-1 | da-18-7 | oncology | oncology | mutation-analysis | mutation-analysis | 0.85 | 0.70 | -0.15 ❌ | 2 |
| 31 | da-18-5 | da-18-1 | oncology | oncology | mutation-analysis | mutation-analysis | 0.90 | 0.72 | -0.18 ❌ | 1 |
| 32 | da-5-1 | da-26-2 | oncology | oncology | multi-omic-integration | predictive-modeling | 0.87 | 0.69 | -0.18 ❌ | 2 |
| 33 | da-26-4 | da-26-2 | oncology | oncology | predictive-modeling | predictive-modeling | 0.87 | 0.67 | -0.20 ❌ | 1 |
| 34 | da-11-1 | da-6-5 | immunology | cardiovascular | cell-cell-communication | multi-omic-integration | 0.92 | 0.67 | -0.25 ❌ | 1 |
| 35 | da-10-1 | da-6-5 | general-biology | cardiovascular | predictive-modeling | multi-omic-integration | 0.92 | 0.67 | -0.25 ❌ | 2 |
| 36 | da-13-6 | da-13-1 | metabolic | metabolic | cross-cohort-comparison | differential-expression | 0.95 | 0.69 | -0.26 ❌ | 2 |
| 37 | da-10-3 | da-10-1 | general-biology | general-biology | predictive-modeling | predictive-modeling | 0.94 | 0.64 | -0.30 ❌ | 1 |

> ⚠️ `baseline=0.00` 标记说明：da-17-1 的 baseline 在 `all_results.json` 中记录为 0.00 (failed)，但首轮 judge 实际评分为 **78/100**（4 个 A 级、1 个 B 级、1 个 C 级）。0.00 是 pipeline 级别失败（5 轮迭代后最终状态标记为 failed），并非 agent 能力缺失。详见 case 1 和 case 2 分析。

---

## 结果统计（修正后）

### 核心分类：Skill 是否真正起作用？

基于以下四个维度综合判断：
1. **Skill 应用状态**（`skill_application.json` 中的 `status`）：`used` vs `blocked_but_overridden`
2. **Baseline 真实评分**（对 baseline=0 的 case，查看 `judge_gemini/judge_result_round_1.json` 确认实际分数）
3. **Δ 大小**（排除 baseline artifact 后的真实 Δ）
4. **Agent 的 Skill 应用理由**（是否与目标任务相关）

| 分类 | 计数 | 占比 | 标准 |
|:---|:---:|:---:|:---|
| ✅ Skill 真正起作用 | **7** | 19% | skill used + Δ > +0.05 + 非 baseline artifact |
| ❌ Skill 起反作用 | **12** | 32% | skill used + Δ < -0.05 + 非 baseline artifact |
| ➖ Skill 无效果 | **10** | 27% | skill used + Δ 在 ±0.05 以内 |
| 🚫 Skill 被拒绝（不适用） | **7** | 19% | skill 状态为 blocked_but_overridden |
| ⚠️ Baseline Artifact | **2** | 5% | baseline=0 但首轮实际评分 > 0 |
| **净效果（帮助 - 害处）** | **-5** | — | ⚠️ 害处多于帮助 |

### 按批次

| 批次 | 帮助 | 无效果 | 害处 | 被拒绝 | 总计 |
|:---|:---:|:---:|:---:|:---:|:---:|
| 批次 1 (原始 22 组) | 5 (23%) | 6 (27%) | 7 (32%) | 4 (18%) | 22 |
| 批次 2 (新增 15 组) | 2 (13%) | 4 (27%) | 5 (33%) | 4 (27%) | 15 |
| **总计** | 7 (19%) | 10 (27%) | 12 (32%) | 8 (22%) | 37 |

> ⚠️ baseline artifact 的 2 个 case（da-17-5→da-17-1, da-12-4→da-17-1）已排除在"帮助"之外。它们的 Δ=+0.84 来自 pipeline 失败（首轮实际评分 78/100），而非 skill 的真实贡献。详见 case 2 分析。

---

## 按 Δ Baseline 排序（修正后：标注 skill 实际效果）

| 源→目标 | Baseline | Transfer | Δ | 同类别? | 同类型? | Skill 效果 |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| da-17-5→da-17-1 | 0.00⚠️ | 0.84 | ⚠️ Artifact | ✅ | ✅ | base=0 artifact |
| da-12-4→da-17-1 | 0.00⚠️ | 0.84 | ⚠️ Artifact | ❌ | ❌ | base=0 artifact |
| da-19-4→da-19-6 | 0.69 | 1.00 | **+0.31** | ✅ | ✅ | ✅ SkillHelped |
| da-4-7→da-4-1 | 0.61 | 0.86 | **+0.25** | ✅ | ❌ | ✅ SkillHelped |
| da-14-8→da-14-1 | 0.80 | 1.00 | **+0.20** | ✅ | ❌ | ✅ SkillHelped |
| da-13-6→da-13-5 | 0.70 | 0.90 | **+0.20** | ✅ | ✅ | ✅ SkillHelped |
| da-10-1→da-6-2 | 0.72 | 0.92 | **+0.20** | ❌ | ❌ | ✅ SkillHelped |
| da-19-4→da-19-3 | 0.75 | 0.90 | **+0.15** | ✅ | ✅ | ✅ SkillHelped |
| da-18-5→da-18-7 | 0.85 | 0.95 | **+0.10** | ✅ | ✅ | ✅ SkillHelped |
| da-5-1→da-5-3 | 0.95 | 0.95 | 0.00 | ✅ | ✅ | ➖ Neutral |
| da-15-2→da-15-7 | 0.70 | 0.70 | 0.00 | ✅ | ❌ | ➖ Neutral |
| da-4-1→da-14-3 | 0.85 | 0.85 | 0.00 | ❌ | ❌ | 🚫 Blocked |
| da-10-1→da-13-6 | 0.60 | 0.60 | 0.00 | ❌ | ❌ | ➖ Neutral |
| da-17-5→da-17-3 | 0.73 | 0.73 | 0.00 | ✅ | ❌ | ➖ Neutral |
| da-15-2→da-15-1 | 1.00 | 1.00 | 0.00 | ✅ | ❌ | ➖ Neutral |
| da-12-4→da-12-2 | 0.60 | 0.63 | +0.03 | ✅ | ❌ | ➖ Neutral |
| da-4-7→da-12-2 | 0.60 | 0.60 | 0.00 | ✅ | ❌ | 🚫 Blocked |
| da-4-1→da-12-2 | 0.60 | 0.60 | 0.00 | ✅ | ❌ | 🚫 Blocked |
| da-9-1→da-1-4 | 0.86 | 0.86 | 0.00 | ✅ | ❌ | ➖ Neutral |
| da-15-2→da-15-8 | 0.63 | 0.63 | 0.00 | ✅ | ❌ | 🚫 Blocked |
| da-26-4→da-12-2 | 0.60 | 0.60 | 0.00 | ✅ | ❌ | 🚫 Blocked |
| da-14-8→da-1-3 | 0.95 | 0.95 | 0.00 | ❌ | ❌ | 🚫 Blocked |
| da-10-3→da-13-6 | 0.60 | 0.60 | 0.00 | ❌ | ❌ | ➖ Neutral |
| da-11-1→da-6-2 | 0.72 | 0.75 | +0.03 | ❌ | ❌ | ➖ Neutral |
| da-25-1→da-1-3 | 0.95 | 0.90 | -0.05 | ✅ | ❌ | ➖ Neutral |
| da-9-1→da-9-7 | 1.00 | 0.93 | -0.07 | ✅ | ❌ | ❌ SkillHarmed |
| da-19-4→da-19-1 | 0.72 | 0.63 | -0.09 | ✅ | ❌ | ❌ SkillHarmed |
| da-13-6→da-13-3 | 1.00 | 0.87 | -0.13 | ✅ | ❌ | ❌ SkillHarmed |
| da-17-5→da-14-3 | 0.85 | 0.71 | -0.14 | ✅ | ❌ | ❌ SkillHarmed |
| da-25-1→da-18-7 | 0.85 | 0.70 | -0.15 | ✅ | ✅ | ❌ SkillHarmed |
| da-18-5→da-18-1 | 0.90 | 0.72 | -0.18 | ✅ | ✅ | ❌ SkillHarmed |
| da-5-1→da-26-2 | 0.87 | 0.69 | -0.18 | ✅ | ❌ | ❌ SkillHarmed |
| da-26-4→da-26-2 | 0.87 | 0.67 | -0.20 | ✅ | ✅ | ❌ SkillHarmed |
| da-11-1→da-6-5 | 0.92 | 0.67 | -0.25 | ❌ | ❌ | ❌ SkillHarmed |
| da-10-1→da-6-5 | 0.92 | 0.67 | -0.25 | ❌ | ❌ | ❌ SkillHarmed |
| da-13-6→da-13-1 | 0.95 | 0.69 | -0.26 | ✅ | ❌ | ❌ SkillHarmed |
| da-10-3→da-10-1 | 0.94 | 0.64 | -0.30 | ✅ | ✅ | ❌ SkillHarmed |

---

## 按类别分组

**相关文件路径说明：**
- 每个 pair 的 transfer 目录: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/{target}_pruned_transfer_{source}_to_{target}/`
- 每个 pair 的 Skill 文件: `server1:/data/yjh/skill-transfer-eval/generalized_skills_pruned/{source}/SKILL.md`
- 汇总结果: `server1:/data/yjh/skill-transfer-eval/summary_pruned/transfer_pruned_results.json`
- Baseline 结果: `server1:/data/yjh/skill-transfer-eval/summary/all_results.json`

### Oncology (肿瘤学)

| 源→目标 | Baseline | Pruned Transfer | Δ Baseline |
|:---|:---:|:---:|:---:|
| da-19-4→da-19-6 | 0.69 | **1.00** | +0.31 ✅ SkillHelped |
| da-4-7→da-4-1 | 0.61 | **0.86** | +0.25 ✅ SkillHelped |
| da-19-4→da-19-3 | 0.75 | **0.90** | +0.15 ✅ SkillHelped |
| da-18-5→da-18-7 | 0.85 | **0.95** | +0.10 ✅ SkillHelped |
| da-5-1→da-5-3 | 0.95 | 0.95 | 0.00 ➖ Neutral |
| da-12-4→da-12-2 | 0.60 | 0.63 | +0.03 ➖ Neutral |
| da-4-7→da-12-2 | 0.60 | 0.60 | 0.00 🚫 Blocked |
| da-4-1→da-12-2 | 0.60 | 0.60 | 0.00 🚫 Blocked |
| da-9-1→da-1-4 | 0.86 | 0.86 | 0.00 ➖ Neutral |
| da-26-4→da-12-2 | 0.60 | 0.60 | 0.00 🚫 Blocked |
| da-25-1→da-1-3 | 0.95 | 0.90 | -0.05 ➖ Neutral |
| da-9-1→da-9-7 | 1.00 | 0.93 | -0.07 ❌ SkillHarmed |
| da-19-4→da-19-1 | 0.72 | 0.63 | -0.09 ❌ SkillHarmed |
| da-25-1→da-18-7 | 0.85 | 0.70 | -0.15 ❌ SkillHarmed |
| da-18-5→da-18-1 | 0.90 | 0.72 | -0.18 ❌ SkillHarmed |
| da-5-1→da-26-2 | 0.87 | 0.69 | -0.18 ❌ SkillHarmed |
| da-26-4→da-26-2 | 0.87 | 0.67 | -0.20 ❌ SkillHarmed |

**Oncology 合计：+4 SkillHelped, 4 Neutral, 7 SkillHarmed, 3 Blocked**

### Immunology (免疫学)

| 源→目标 | Baseline | Pruned Transfer | Δ Baseline |
|:---|:---:|:---:|:---:|
| da-17-5→da-17-1 | 0.00⚠️ | **0.84** | ⚠️ Artifact |
| da-14-8→da-14-1 | 0.80 | **1.00** | +0.20 ✅ SkillHelped |
| da-4-1→da-14-3 | 0.85 | 0.85 | 0.00 🚫 Blocked |
| da-17-5→da-17-3 | 0.73 | 0.73 | 0.00 ➖ Neutral |
| da-17-5→da-14-3 | 0.85 | 0.71 | -0.14 ❌ SkillHarmed |
| da-14-8→da-1-3 | 0.95 | 0.95 | 0.00 🚫 Blocked |

**Immunology 合计：+1 SkillHelped, 1 Neutral, 1 SkillHarmed, 2 Blocked, 1 Artifact**

### Neurology (神经科学)

| 源→目标 | Baseline | Pruned Transfer | Δ Baseline |
|:---|:---:|:---:|:---:|
| da-15-2→da-15-7 | 0.70 | 0.70 | 0.00 |
| da-15-2→da-15-1 | 1.00 | 1.00 | 0.00 |
| da-15-2→da-15-8 | 0.63 | 0.63 | 0.00 |

**Neurology 合计：0 SkillHelped, 2 Neutral, 1 Blocked**

### Metabolic (代谢)

| 源→目标 | Baseline | Pruned Transfer | Δ Baseline |
|:---|:---:|:---:|:---:|
| da-13-6→da-13-5 | 0.70 | **0.90** | +0.20 |
| da-10-1→da-13-6 | 0.60 | 0.60 | 0.00 |
| da-10-3→da-13-6 | 0.60 | 0.60 | 0.00 |
| da-13-6→da-13-3 | 1.00 | 0.87 | -0.13 ❌ |
| da-13-6→da-13-1 | 0.95 | 0.69 | -0.26 ❌ |

**Metabolic 合计：+1 SkillHelped, 1 Neutral, 2 SkillHarmed**

### Cross-domain / 其他

| 源→目标 | 源类别→目标类别 | Baseline | Pruned Transfer | Δ Baseline |
|:---|:---|:---:|:---:|:---:|
| da-12-4→da-17-1 | oncology→immunology | 0.00⚠️ | **0.84** | ⚠️ Artifact |
| da-10-1→da-6-2 | general-bio→cardiovascular | 0.72 | **0.92** | +0.20 ✅ SkillHelped |
| da-11-1→da-6-2 | immunology→cardiovascular | 0.72 | 0.75 | +0.03 ➖ Neutral |
| da-10-3→da-10-1 | general-bio→general-bio | 0.94 | 0.64 | -0.30 ❌ SkillHarmed |
| da-11-1→da-6-5 | immunology→cardiovascular | 0.92 | 0.67 | -0.25 ❌ SkillHarmed |
| da-10-1→da-6-5 | general-bio→cardiovascular | 0.92 | 0.67 | -0.25 ❌ SkillHarmed |

**Cross 合计：+1 SkillHelped, 1 Neutral, 2 SkillHarmed, 1 Artifact**

---

## 关键发现（全面重分析）

### 1. 核心结论：Skill 迁移整体效果为负（净效果 -5）

在排除 baseline artifact 后，**skill 真正起作用的只有 7 组（19%），起反作用的达 12 组（32%），净效果 = -5**。这与之前"24% 提升"的结论完全不同。

**原因：** 之前的统计被 da-17-1 的 baseline=0（pipeline artifact）严重扭曲了——两个 pair 的 Δ=+0.84 被计入"提升"，但实际上 baseline 首轮评分 78/100，真实 Δ 仅 +0.06。

### 2. Skill 起作用的 7 组：模式分析

| 模式 | 案例 | Δ | 核心机制 |
|:---|:---|:---:|:---|
| **① 同类型 + 共享分析范式** | da-19-4→da-19-6, da-19-4→da-19-3, da-13-6→da-13-5, da-18-5→da-18-7 | +0.10 ~ +0.31 | skill 的核心操作步骤与 target rubric 高度重合，agent 按 skill 框架执行即可 |
| **② 跨类型 + 通用框架复用** | da-4-7→da-4-1, da-14-8→da-14-1 | +0.20 ~ +0.25 | skill 提供通用分析框架（rubric 校验、Spearman 相关性），跨任务类型仍然适用 |
| **③ 跨领域 + 通用方法论** | da-10-1→da-6-2 | +0.20 | skill 的 fold-change 排序框架跨领域仍然可用 |

**关键洞察：** skill 起作用的案例中，**6/7 是"同类别 + 同类型"或"同类别 + 共享数据"**。唯一跨领域成功的 da-10-1→da-6-2 的 skill 提供了非常通用的 fold-change 比较框架。

### 3. Skill 起反作用的 12 组：为什么？

| 失败模式 | 案例 | Δ | 原因分析 |
|:---|:---|:---:|:---|
| **同类型但 skill 生搬硬套** | da-18-5→da-18-1 (-0.18), da-25-1→da-18-7 (-0.15), da-26-4→da-26-2 (-0.20), da-10-3→da-10-1 (-0.30) | -0.15 ~ -0.30 | 同类型但 target rubric 有特异性要求，skill 的固定框架导致 agent 忽略了 target 的独特需求 |
| **跨类型 skill 不适用** | da-9-1→da-9-7 (-0.07), da-13-6→da-13-3 (-0.13), da-13-6→da-13-1 (-0.26), da-19-4→da-19-1 (-0.09), da-17-5→da-14-3 (-0.14) | -0.07 ~ -0.26 | 虽然同类别，但任务类型差异大，skill 的核心操作与 target 的 rubric 要求不一致 |
| **跨领域 + 无通用框架** | da-11-1→da-6-5 (-0.25), da-10-1→da-6-5 (-0.25), da-5-1→da-26-2 (-0.18) | -0.18 ~ -0.25 | 跨领域迁移几乎总是失败，skill 不仅不帮助，还占据了 agent 的上下文窗口 |

**关键洞察：** 12 个失败案例中，**只有 4 个 Δ 小幅度负值（-0.07 ~ -0.13），其余 8 个 Δ 都在 -0.14 以下**，说明 skill 带来的负面影响是实质性的，不是随机波动。

### 4. Skill 被拒绝的 7 组：Agent 判断正确

| 案例 | 转移类型 | 为什么不适用 |
|:---|:---|:---|
| da-4-1→da-14-3 | oncology→immunology, clustering→association-testing | NMF 聚类 skill 不适用于关联检验 |
| da-4-7→da-12-2 | oncology, TCR→pathway-enrichment | TCR 受体库分析不适用于通路富集 |
| da-4-1→da-12-2 | oncology, clustering→pathway-enrichment | NMF 聚类不适用于通路富集 |
| da-15-2→da-15-8 | neurology, co-expression→multi-omic-integration | WGCNA 不适用于多组学整合 |
| da-26-4→da-12-2 | oncology, predictive-modeling→pathway-enrichment | 预测模型不适用于通路富集 |
| da-12-4→da-17-1 | oncology→immunology, survival→cell-composition | 生存分析不适用于细胞组分分析 |
| da-14-8→da-1-3 | immunology→oncology, association→cell-composition | 基因集相关性不适用于细胞组分分析 |

**关键洞察：** 所有 7 个被拒绝的 case，transfer 分数都与 baseline 几乎一致（Δ≈0）。**Agent 正确判断了 skill 不适用**，忽略 skill 后凭自身能力完成任务，skill 既没有帮助也没有伤害。

### 5. 同类别 vs 跨类别迁移（修正后）

| 迁移类型 | 帮助 | 无效果 | 害处 | 被拒绝 | 总计 |
|:---|:---:|:---:|:---:|:---:|:---:|
| ✅ 同类别同类型 | 4 (33%) | 2 (17%) | 3 (25%) | 0 (0%) | 12 |
| ➖ 同类别不同类型 | 1 (7%) | 3 (20%) | 5 (33%) | 6 (40%) | 15 |
| ❌ 跨类别 + 跨类型 | 2 (20%) | 5 (50%) | 3 (30%) | 0 (0%) | 10 |

结论：**同类别同类型仍然是成功概率最高的（33%），但即使是同类型，失败率也高达 25%。跨类别并不总比同类别差——跨类别中有 2 组成功（受益于通用方法论框架）。**

### 6. 对 Skill 迁移策略的建议

1. **Skill 应该只用于同类别同类型任务**——跨类型和跨领域成功率极低
2. **Baseline artifact 警告**——所有 baseline=0 的 case 必须检查原始 judge 日志确认真实原因
3. **Agent 的拒绝判断值得信任**——7 个被拒绝的 case Δ≈0，不做比做错好
4. **Skill 的 harm 模式需要进一步研究**——为什么同类型的 skill 有时反而让 agent 表现更差？可能原因是 skill 占据了上下文窗口，导致 agent 忽略了 target 的独特需求

---
## 轨迹对比分析：Baseline vs Transfer 的 Agent 行为差异

基于对 19 组（7 组 SkillHelped + 12 组 SkillHarmed）的 trajectory.clean.jsonl 量化分析，以下是关键发现。

### 量化摘要

| 指标 | ✅ SkillHelped (7组) | ❌ SkillHarmed (12组) |
|:---|:---:|:---:|
| 平均 effort 比 (transfer/baseline) | **1.26x** | **0.95x** |
| 平均 tool call 变化 | **+19.9** | **-11.1** |
| 平均 error 变化 | **+6.0** | **-2.5** |
| 平均 skill 调用次数 | 1.6 | 1.2 |

### 发现 1：Skill 起作用时，Agent 投入更多努力

在 7 组 SkillHelped 案例中，transfer agent 统一比 baseline agent **投入了更多努力**：

- **da-19-4→da-19-3**：effort 1.9x（baseline 41 次 tool call → transfer 90 次）
- **da-13-6→da-13-5**：effort 1.3x（baseline 36 次 tool call → transfer 71 次）
- **da-10-1→da-6-2**：effort 1.3x（baseline 50 次 tool call → transfer 78 次）

Skill 提供了 **分析框架和操作清单**，agent 遵循这些步骤进行了更全面的数据探索和分析。尤其是 da-19-4→da-19-3，skill 提供了染色质分析的完整框架，agent 将所有步骤都执行了一遍。

### 发现 2：Skill 起反作用时，Agent 投入更少努力

最令人惊讶的发现：在 12 组 SkillHarmed 案例中，transfer agent 普遍 **投入了更少的努力**：

- **da-26-4→da-26-2**：effort 0.34x（baseline 142 次 tool call → transfer 62 次！）
- **da-10-1→da-6-5**：effort 0.5x（baseline 59 次 tool call → transfer 35 次）
- **da-11-1→da-6-5**：effort 0.6x（baseline 59 次 tool call → transfer 35 次）
- **da-25-1→da-18-7**：effort 0.6x

**核心机制：Skill 的"过度自信效应"** —— 当 agent 拿到一个看似相关的 skill 时，它倾向于 **简化自己的分析流程**，认为 skill 已经提供了足够指导，不需要自己从头探索。结果就是 agent 做了更少的 bash 命令、读了更少的文件、写了更少的代码，但 **也因此遗漏了 target 任务的独特 rubric 要求**。

例如 da-26-4→da-26-2：baseline agent 做了 118 次 bash 命令 + 26 次错误（说明它在积极试错），而 transfer agent 只做了 40 次 bash 命令 + 8 次错误（错误少了，但分数也低了）。**Agent 提交了一个"看起来正确但不完整"的答案。**

### 发现 3：Error 数量与分数正相关（在 harmed 组中）

在 SkillHarmed 组中，**error 越少，分数越低**——baseline agent 平均 10.5 个错误，而 transfer agent 平均 8.0 个错误。但 baseline 的分数更高。

这说明：**更多的错误 = 更多的尝试 = 更全面的覆盖**。Baseline agent 通过试错探索了更多方向，最终覆盖了更多 rubric 要求。而 Transfer agent 被 skill 限制了视野，过早地停止了探索。

### 发现 4：Skill 调用次数 = 1-3 次（非常有限）

所有 19 组案例中，skill 最多被调用 3 次（da-10-1→da-6-2），最少 1 次。Skill 在当前 pipeline 中仅作为 **一次性提示** 使用，没有持续迭代。这与理想的"skill 作为持续指导"差距很大。

### 发现 5：工具使用模式差异

SkillHelped 组中，transfer agent 使用了更多样的工具：
- **Edit** 工具在 5/7 组 SkillHelped 中出现（vs 2/12 组 SkillHarmed）
- **Grep** 工具仅在 transfer 中出现（da-4-7→da-4-1, da-13-6→da-13-5）
- SkillHelped 的 transfer agent 更倾向于 **编辑已有文件** 而非从头写

### 核心启示

1. **Skill 的 harm 机制不是"错误的指导"，而是"过早的满足"** —— agent 拿到 skill 后认为"我懂了"，减少了探索
2. **Effort ratio 可以作为 skill 是否正在起作用的实时指标**——如果 transfer agent 的 effort 显著低于 baseline，说明 skill 可能正在起反作用
3. **Skill 应该设计为"引导探索"而非"简化分析"**——当前 skill 的泛化策略（pruning 后只剩 2-3 个操作）恰恰让 agent 过早满足
4. **Error 不应该被完全避免**——在 open-ended 分析任务中，试错是必要的探索过程

---
## 深度分析

### Baseline Artifact 案例（2 组）

以下 2 组案例的 Δ 值因 baseline=0 的 pipeline artifact 被严重高估，已从"Skill 起作用"列表中排除。

### A. da-17-5→da-17-1（+0.06 真实 Δ）—— 同类型技能匹配，但 baseline=0 是 artifact

| 项目 | 内容 |
|:---|:---|
| **Source Skill 名称** | "Interaction Test for Group-Specific Effect Sizes" |
| **Source 原始任务** | da-17-5: 细胞组分分析 + 祖先交互效应检验 |
| **Target 任务** | da-17-1: scRNA-seq 分析 SLE 患者 vs 健康对照的免疫细胞频率差异 |
| **Baseline / Transfer** | 0.00（artifact）→ **0.84** |
| **真实 Δ** | baseline 首轮实际评分 78/100 → transfer 84/100，**Δ = +0.06** |
| **Skill 应用方式** | ① per-subject 细胞比例计算 ② 按种族的 Wilcoxon 检验 ③ 亚组特异性效应量 ④ 正式交互效应检验（WLS）⑤ FDR 校正 |

**相关文件路径：**
- Transfer 目录: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-17-1_pruned_transfer_da-17-5_to_da-17-1/`
- Skill 文件: `server1:/data/yjh/skill-transfer-eval/generalized_skills_pruned/da-17-5/SKILL.md`
- Judge 结果: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-17-1_pruned_transfer_da-17-5_to_da-17-1/logs/run_summary.json`
- Agent 轨迹: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-17-1_pruned_transfer_da-17-5_to_da-17-1/logs/trajectory.clean.jsonl`
- Trace 报告: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-17-1_pruned_transfer_da-17-5_to_da-17-1/outputs/trace.md`
- Baseline 首轮 judge: `server1:/data/yjh/skill-transfer-eval/baseline/da-17-1_20260721_192248_baseline_rep1/judge_gemini/judge_result_round_1.json`

**具体分析：**

da-17-5 的 skill 是从 **祖先交互效应检验** 任务泛化而来，内容包含按分组计算细胞比例、每个亚组内做统计检验、以及正式的交互效应检验。da-17-1 的目标任务恰好也是 **细胞组分分析** —— 需要按 donor 计算 cell type 比例、在 SLE vs 健康之间做 Wilcoxon 检验、再按 ethnicity 做交互效应分析。

**Skill 匹配度：** 这是最理想的 skill transfer 场景——source 和 target 不仅任务类型相同（cell-composition），而且 skill 的核心操作完全覆盖了 target rubric 的要求。

**但是，baseline 的"0"分是 pipeline artifact：** 查阅 baseline 的 `judge_gemini/judge_result_round_1.json`，baseline agent（Gemini 3.1 Pro）首轮实际评分 **78/100**（4 个 A 级）。Pipeline 跑了 5 轮后状态标记为 failed，导致 `all_results.json` 记录为 0.0。真实 Δ = (84-78)/100 = **+0.06**，而非表格中的 +0.84。

**这个 skill 确实有帮助，但幅度很小（+0.06）。** 之前的 +0.84 完全是被 pipeline artifact 扭曲的。

---

### B. da-12-4→da-17-1（+0.84）—— 跨领域 transfer，但 skill 贡献为零

| 项目 | 内容 |
|:---|:---|
| **Source Skill 名称** | "Survival Analysis with Multi-Omics Data" |
| **Source 原始任务** | da-12-4: 多组学 Cox 回归生存分析（筛选与不良预后相关的基因/菌群特征） |
| **Target 任务** | da-17-1: scRNA-seq 分析 SLE 患者 vs 健康对照的免疫细胞频率差异 |
| **Baseline / Transfer** | 0.00 → **0.84** |
| **Skill 应用方式** | `skill_application.json` 状态：**"blocked_but_overridden"**——agent 自行判断 skill 不适用，但仍 override 执行 |

**⚠️ 关键发现：Baseline=0 不代表 baseline agent 失败**

查阅 da-17-1 baseline 运行的 **judge 原始评分**（`judge_result_round_1.json`）：

| Criterion | 内容 | Level | 得分 |
|:---|:---|:---:|:---:|
| criterion_1 | 数据加载（h5ad 读取、识别 cell type、map donor） | A | 18/18 |
| criterion_2 | 按 donor 汇总比例（避免伪重复） | A | 15/15 |
| criterion_3 | 低细胞量过滤（未实现！） | **C** | **0/10** |
| criterion_4 | 统计检验（Mann-Whitney U + BH FDR） | A | 20/20 |
| criterion_5 | 正确识别显著 cell type（5/8，遗漏 T8, B, PB） | B | 10/15 |
| criterion_6 | 生物学解释 | A | 15/15 |
| criterion_7 | 引用可靠性 | A | 0/0（满分） |
| **总分** | | | **78/100** |

**Baseline agent 第一轮实际获得 78 分**，task 类型正确（cell-composition），但 **pipeline 运行了 5 轮后最终状态标记为 failed**，导致 `all_results.json` 中 recorded 为 `total_score=0, reward=0.0`。Baseline 并非"不知道如何入手"，而是 pipeline 级别的失败（可能原因：最终轮次提交未通过校验，或 5 轮迭代后 agent 走了弯路）。**Baseline=0 是一个 pipeline artifact，而不是 agent 能力的真实反映。**

**什么是真正的 baseline 能力？** 从 round 1 的 judge 来看，baseline agent（Gemini 3.1 Pro）**正确完成了所有核心分析步骤**：按 donor 聚合比例、Mann-Whitney U 检验、BH 校正、生物学解释。唯一的实质问题是缺少低细胞量过滤（criterion 3, 0/10），以及遗漏了 3 个显著的 cell type（criterion 5, 10/15）。

**Skill 的实际内容与适用性：**

da-12-4 的 `SKILL.md` 仅包含 **2 个操作步骤**：

1. **加载多组学 CSV 数据**：读取两个 CSV 文件（基因表达 + 微生物丰度），检查列名、数据类型
2. **应用不良预后过滤**：从 Cox 回归结果中筛选 HR > 1 且 p < 0.05 的特征

这与 da-17-1 的 scRNA-seq 细胞组分分析 **完全无关**——da-17-1 需要读取 h5ad 格式、按 donor 聚合 cell count、做 Mann-Whitney U 检验，而 skill 提供的是 CSV 加载 + 生存分析的 HR 过滤。

**关键证据：skill_application.json**

```json
{
  "skill": "generalized-pruned-transfer",
  "status": "blocked_but_overridden",
  "reason": "The skill guidance covers Cox regression and survival analysis 
    for multi-omics data, which is not applicable to this differential cell 
    type abundance analysis. The abstract items about data loading and 
    statistical filtering were followed, but the core survival analysis 
    methodology is not relevant to this task."
}
```

Agent **明确感知到 skill 不适用**，但 override 后仍然完成了任务。这说明 transfer 的成功完全来自 agent 自身能力，而非 skill 的贡献。

**Transfer agent 的实际表现：**

Transfer agent（DeepSeek-V4-Flash）的 judge 结果：

| Criterion | 内容 | Level | 得分 |
|:---|:---|:---:|:---:|
| criterion_1 | 数据加载 | A | 18/18 |
| criterion_2 | 按 donor 汇总比例 | A | 15/15 |
| criterion_3 | 低细胞量过滤 | **B** | **6/10**（提到了但未实现阈值） |
| criterion_4 | 统计检验 | A | 20/20 |
| criterion_5 | 正确识别显著 cell type（5/8） | B | 10/15 |
| criterion_6 | 生物学解释 | A | 15/15 |
| criterion_7 | 引用可靠性 | A | 0/0 |
| **总分** | | | **84/100** |

Transfer agent 的得分（84）与 baseline 第一轮（78）的差异 **仅为 6 分**，主要来自 criterion 3（低细胞量过滤从 0→6 分）。两者在 **核心分析步骤上表现几乎一致**。

**结论：Case 2 的 +0.84 提升是虚假的**

当 baseline 从 78 校正为 78、transfer 为 84 时，真实的 Δ = **+0.06**，而非表格中的 +0.84。Skill 实际上没有提供任何有意义的指导——agent 自身承认 skill 不适用，其表现完全依赖于自身能力。**这个案例不应该被归类为"成功迁移"，而应被标记为"baseline artifact 导致的虚高增益"。**

**对后续实验的启示：** 凡 baseline=0 的 pair，必须检查 baseline 的原始 judge 日志以确认真实原因。Pipeline 级别的失败不应该被等价于 agent 能力的缺失。如有必要，应对 baseline=0 的 task 重新运行 baseline 以获取真实的基线分数。

---

### Skill 真正起作用的案例（7 组）

### 1. da-19-4→da-19-6（+0.31）—— 同类型完美映射，满分 1.0

| 项目 | 内容 |
|:---|:---|
| **Source Skill 名称** | "Differential ChIP-seq Signal Analysis" |
| **Source 原始任务** | da-19-4: ChIP-seq 差异峰分析（CBFβ-SMMHC 抑制） |
| **Target 任务** | da-19-6: ATAC-seq 染色质可及性分析（AI-10-49 vs DMSO） |
| **Baseline / Transfer** | 0.69 → **1.00**（满分） |
| **Skill 应用方式** | 加载 peak manifest → 建立条件映射 → 读取 XLS pileup → CPM 归一化 → 比较 |

**相关文件路径：**
- Transfer 目录: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-19-6_pruned_transfer_da-19-4_to_da-19-6/`
- Skill 文件: `server1:/data/yjh/skill-transfer-eval/generalized_skills_pruned/da-19-4/SKILL.md`
- Judge 结果: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-19-6_pruned_transfer_da-19-4_to_da-19-6/logs/run_summary.json`
- Agent 轨迹: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-19-6_pruned_transfer_da-19-4_to_da-19-6/logs/trajectory.clean.jsonl`
- Trace 报告: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-19-6_pruned_transfer_da-19-4_to_da-19-6/outputs/trace.md`
- Answer: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-19-6_pruned_transfer_da-19-4_to_da-19-6/outputs/answer.txt`
- Plan: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-19-6_pruned_transfer_da-19-4_to_da-19-6/workspace/plan.md`

**具体分析：**

这是 **最完美的 skill transfer 案例**。da-19-4 的 skill 专门处理染色质可及性数据（ChIP-seq），而 da-19-6 也是染色质可及性分析（ATAC-seq）。两者共享相同的核心分析范式：peak calling → 读取计数 → 归一化 → 条件比较。

**轨迹对比分析：**

| 指标 | Baseline (无skill) | Transfer (有skill) | 差异 |
|:---|---:|---:|---:|
| 轮次 | 2 | 2 | 0 |
| 总 tool calls | 46 | 54 | +8 |
| Error 次数 | 7 | 16 | **+9** |
| Bash 命令 | 27 | 29 | +2 |
| Skill 调用 | — | 2 | +2 |
| Effort 得分 | 27 | 29 | **1.07x** |

**关键差异：** Transfer agent 做了更多尝试（+8 tool calls），虽然 error 也更多（+9），但覆盖了所有 7 个 rubric 要求。Baseline 的 46 次 tool calls 中，有 5 次 finalize_submission 调用来提交答案（说明 agent 反复尝试提交），而 transfer 的 54 次中有 3 次。**Transfer agent 在 skill 的引导下更早地进入了正确的分析流程，不需要反复提交测试。**

**关键证据（来自 trace.md）：**
- Agent 正确加载了 4 个 ATAC-seq 样本的 narrowPeak 文件
- 发现 BAM 文件不可用，但有 XLS 文件的 pileup 列
- 创造性使用 XLS 的 pileup 值（原始读段计数）进行 CPM 归一化（而非 narrowPeak 的 fold enrichment）
- 构建 union 区间集进行对称比较
- 正确报告了 gained/lost/unchanged 的峰数量和比例
- 所有 7 个 criterion 全部获得 Level A

**Rubric 反馈：** "The agent delivered a high-quality analysis that met all rubric requirements for a full-score answer."

**为什么成功：** **任务范式完全一致**——ChIP-seq 和 ATAC-seq 共享相同的分析逻辑（peak → count → normalize → compare）。Skill 中的操作步骤几乎可以直接套用，agent 只需要针对 ATAC-seq 的特定数据格式做微调（如使用 XLS 而非 BAM）。

---

### 2. da-19-4→da-19-3（+0.15）—— 同类型再次验证

| 项目 | 内容 |
|:---|:---|
| **Source Skill** | 同上（Differential ChIP-seq Signal Analysis） |
| **Target 任务** | da-19-3: RUNX1 特异性 ATAC-seq 峰分析 |
| **Baseline / Transfer** | 0.75 → **0.90** |
| **Skill 应用方式** | 同上，但需要针对 RUNX1 特异性做额外处理 |

**相关文件路径：**
- Transfer 目录: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-19-3_pruned_transfer_da-19-4_to_da-19-3/`
- Skill 文件: `server1:/data/yjh/skill-transfer-eval/generalized_skills_pruned/da-19-4/SKILL.md`
- Judge 结果: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-19-3_pruned_transfer_da-19-4_to_da-19-3/logs/run_summary.json`
- Agent 轨迹: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-19-3_pruned_transfer_da-19-4_to_da-19-3/logs/trajectory.clean.jsonl`
- Trace 报告: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-19-3_pruned_transfer_da-19-4_to_da-19-3/outputs/trace.md`
- Answer: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-19-3_pruned_transfer_da-19-4_to_da-19-3/outputs/answer.txt`

**具体分析：** 同样是染色质可及性分析，但这次需要关注 RUNX1 特异性峰。agent 仍然正确应用了 skill 的框架，但在 **Criterion 4**（富集分析的比较组选择）上扣了分——使用了 total AI vs total DMSO 而非要求的 gained vs unchanged。**即使同类型，rubric 的细微差异仍然会导致扣分。**

**轨迹对比分析：**

| 指标 | Baseline (无skill) | Transfer (有skill) | 差异 |
|:---|---:|---:|---:|
| 轮次 | 2 | 3 | +1 |
| 总 tool calls | 41 | 90 | **+49** |
| Error 次数 | 7 | 14 | +7 |
| Bash 命令 | 28 | 53 | **+25** |
| Skill 调用 | — | 2 | +2 |
| Effort 得分 | 28 | 53 | **1.89x** |

**关键差异：** 这是 **effort 增加最多的案例**（1.89x）。Transfer agent 投入了几乎两倍的 effort：28 → 53 个 bash 命令，41 → 90 次 tool calls。Skill 提供了染色质分析的完整框架（peak calling → 读取计数 → 归一化 → 比较），agent 逐一执行了这些步骤，但在此期间也遇到了更多错误（+7）。**Skill 引导 agent 做了更全面的分析，但 rubric 中"gained vs unchanged"这个特定要求仍然被遗漏了——说明 skill 的通用框架无法覆盖 task-specific 的 rubric 细节。**

---

### 3. da-4-7→da-4-1（+0.25）—— 跨类型但 skill 的校验框架通用

| 项目 | 内容 |
|:---|:---|
| **Source Skill 名称** | "Composite Key from Paired Attributes and Rubric-Based Validation" |
| **Source 原始任务** | da-4-7: TCR 受体库分析（复合键定义） |
| **Target 任务** | da-4-1: NMF 聚类分析免疫细胞亚型 |
| **Baseline / Transfer** | 0.61 → **0.86** |
| **Skill 应用方式** | 应用 rubric 校验清单 → 确保每个 criterion 被覆盖 → 系统化检查输出 |

**相关文件路径：**
- Transfer 目录: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-4-1_pruned_transfer_da-4-7_to_da-4-1/`
- Skill 文件: `server1:/data/yjh/skill-transfer-eval/generalized_skills_pruned/da-4-7/SKILL.md`
- Judge 结果: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-4-1_pruned_transfer_da-4-7_to_da-4-1/logs/run_summary.json`
- Agent 轨迹: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-4-1_pruned_transfer_da-4-7_to_da-4-1/logs/trajectory.clean.jsonl`
- Trace 报告: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-4-1_pruned_transfer_da-4-7_to_da-4-1/outputs/trace.md`
- Answer: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-4-1_pruned_transfer_da-4-7_to_da-4-1/outputs/answer.txt`
- Plan: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-4-1_pruned_transfer_da-4-7_to_da-4-1/workspace/plan.md`

**具体分析：**

这是一个很有趣的案例。da-4-7 的 skill 核心是 **复合键定义 + rubic 校验**，这和 NMF 聚类（da-4-1）几乎没有直接关系。但 skill 中的 **第二部分（Criterion 2: Validate Against Rubric Criteria）** 提供了一个通用的校验清单框架，帮助 agent 系统化地检查所有 rubric 要求。

**轨迹对比分析：**

| 指标 | Baseline (无skill) | Transfer (有skill) | 差异 |
|:---|---:|---:|---:|
| 轮次 | 2 | 2 | 0 |
| 总 tool calls | 26 | 44 | +18 |
| Error 次数 | 8 | 8 | 0 |
| Bash 命令 | 15 | 18 | +3 |
| Skill 调用 | — | 1 | +1 |
| Effort 得分 | 15 | 18 | **1.20x** |

**关键差异：** 这是唯一一个 error 数完全不变的 case（baseline 8, transfer 8）。Transfer agent 使用 skill 的 rubric 校验清单后，在同等 error 水平下做了更多分析（+18 tool calls），但 **没有因为 skill 的加入而增加试错成本**。更重要的是，effort 的增加（1.2x）相对温和，说明 agent 没有盲目扩大搜索空间，而是 **有方向地增加了分析步骤**。Criterion 2（共识矩阵构建）的扣分说明 skill 的校验清单帮助 agent 覆盖了大部分要求，但无法覆盖 task-specific 的领域知识。

**关键证据（来自 trace.md 和 judge 结果）：**
- 5/6 个 criterion 获得 Level A
- 唯一扣分点在 Criterion 2（共识矩阵构建），这是技能特定的操作要求
- Agent 正确构建了组成矩阵、选择了最优 rank k=4、提取了 NMF 模块
- 命名了免疫亚型、报告了响应关联统计

**为什么成功：** 虽然 skill 的核心操作（复合键定义）不适用，但 **rubric 校验清单** 这部分通用框架帮助 agent 更有条理地满足 rubric 要求。Skill 中 "validate against rubric criteria" 的检查清单让 agent 在提交前系统地检查了每个要求。

---

### 4. da-14-8→da-14-1（+0.20）—— 跨类型但相关性分析框架通用

| 项目 | 内容 |
|:---|:---|
| **Source Skill 名称** | "Gene Set Definition via Score Correlation and Coherence Assessment" |
| **Source 原始任务** | da-14-8: 基因集定义（基于评分相关性） |
| **Target 任务** | da-14-1: 脓毒症内型评分聚类分析 |
| **Baseline / Transfer** | 0.80 → **1.00**（满分） |
| **Skill 应用方式** | Spearman 相关性计算 → 层次聚类 → 轮廓系数 → 簇识别和描述 |

**相关文件路径：**
- Transfer 目录: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-14-1_pruned_transfer_da-14-8_to_da-14-1/`
- Skill 文件: `server1:/data/yjh/skill-transfer-eval/generalized_skills_pruned/da-14-8/SKILL.md`
- Judge 结果: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-14-1_pruned_transfer_da-14-8_to_da-14-1/logs/run_summary.json`
- Agent 轨迹: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-14-1_pruned_transfer_da-14-8_to_da-14-1/logs/trajectory.clean.jsonl`
- Trace 报告: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-14-1_pruned_transfer_da-14-8_to_da-14-1/outputs/trace.md`
- Answer: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-14-1_pruned_transfer_da-14-8_to_da-14-1/outputs/answer.txt`
- Plan: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-14-1_pruned_transfer_da-14-8_to_da-14-1/workspace/plan.md`

**具体分析：**

这是 **跨类型但框架复用** 的典范。da-14-8 的 skill 核心是 Spearman 相关性分析 + 基因集内部一致性评估，而 da-14-1 需要的是 **评分矩阵的相关性聚类**。两者虽然任务类型不同（association-testing vs clustering），但都依赖 **Spearman 相关性矩阵 → 聚类/分组** 这个核心分析模式。

**轨迹对比分析：**

| 指标 | Baseline (无skill) | Transfer (有skill) | 差异 |
|:---|---:|---:|---:|
| 轮次 | 2 | 2 | 0 |
| 总 tool calls | 28 | 37 | +9 |
| Error 次数 | 3 | 8 | +5 |
| Bash 命令 | 16 | 17 | +1 |
| Skill 调用 | — | 1 | +1 |
| Effort 得分 | 16 | 17 | **1.06x** |

**关键差异：** Effort 几乎不变（1.06x），但 error 从 3 增加到 8。Transfer agent 在 skill 引导下尝试了更多 Spearman 相关性的细节处理（如处理缺失值、选择聚类方法），这些尝试引入了一些错误，但最终 **所有 7 个 criterion 全部 Level A**。值得注意的是，baseline 仅 3 个 error 但得分 0.80，说明 baseline 的 16 个 bash 命令涵盖了大部分核心内容，但 **skill 帮助 transfer agent 覆盖了最后 20% 的细节要求**。

**关键证据（来自 agent 的 plan.md）：**
```markdown
## Applied skills checklist
- **generalized-pruned-transfer**: The skill provides a framework for 
  correlation-based analysis, which is applicable to this task.
  1. Use Spearman correlation (not Pearson) to handle non-linear relationships
  2. Load and inspect data quality before analysis
  3. Compute pairwise correlations and examine structure
  4. Document all intermediate quantitative results
```

Agent 明确将 skill 的框架映射到了目标任务。最终结果：所有 7 个 criterion 全部 Level A。

**Judge 反馈：** "The agent performed an excellent analysis that met all Level A criteria across data loading, correlation computation, clustering implementation, cluster identification, biological interpretation, limitation acknowledgment, and source reliability."

---

### 5. da-13-6→da-13-5（+0.20）—— 同类型操作直接复用

| 项目 | 内容 |
|:---|:---|
| **Source Skill 名称** | "Comparative Treatment Effect Analysis" |
| **Source 原始任务** | da-13-6: GAHT 蛋白组学效应分析 |
| **Target 任务** | da-13-5: GAHT 蛋白与性染色体关联蛋白的重叠分析 |
| **Baseline / Transfer** | 0.70 → **0.90** |
| **Skill 应用方式** | 加载补充表 → 正确 header 处理 → 显著性检验 → 方向一致性分析 → 灵敏度分析 |

**相关文件路径：**
- Transfer 目录: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-13-5_pruned_transfer_da-13-6_to_da-13-5/`
- Skill 文件: `server1:/data/yjh/skill-transfer-eval/generalized_skills_pruned/da-13-6/SKILL.md`
- Judge 结果: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-13-5_pruned_transfer_da-13-6_to_da-13-5/logs/run_summary.json`
- Agent 轨迹: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-13-5_pruned_transfer_da-13-6_to_da-13-5/logs/trajectory.clean.jsonl`
- Trace 报告: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-13-5_pruned_transfer_da-13-6_to_da-13-5/outputs/trace.md`
- Answer: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-13-5_pruned_transfer_da-13-6_to_da-13-5/outputs/answer.txt`
- Skill 应用记录: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-13-5_pruned_transfer_da-13-6_to_da-13-5/workspace/skill_application.json`

**具体分析：**

这是 **同类别（metabolic）+ 同类型（cross-cohort-comparison）** 的典型案例。da-13-6 和 da-13-5 都是分析 GAHT 蛋白组学数据，只是分析角度不同：da-13-6 比较的是 GAHT vs 更年期/MHT，da-13-5 比较的是 GAHT vs 性染色体关联蛋白。两者使用相同的补充表格（Table 1 和 Table 5），共享相同的分析框架。

**轨迹对比分析：**

| 指标 | Baseline (无skill) | Transfer (有skill) | 差异 |
|:---|---:|---:|---:|
| 轮次 | 2 | 2 | 0 |
| 总 tool calls | 36 | 71 | **+35** |
| Error 次数 | 5 | 18 | **+13** |
| Bash 命令 | 26 | 34 | +8 |
| Skill 调用 | — | 1 | +1 |
| Effort 得分 | 26 | 34 | **1.31x** |

**关键差异：** 这是 **error 增加最多的 SkillHelped 案例**（+13）。Transfer agent 做了大量尝试（double 的 tool calls），但也因此遇到了更多错误。Skill 引导 agent 做了更细致的数据处理——如正确使用 `header=4` 和 `header=3` 加载补充表格、处理 `#REF!` 错误值——但这些尝试也产生了更多错误。**Effort 1.31x 说明 skill 没有让 agent 简化工作，而是鼓励了更深入的探索。**

**关键证据（来自 trace.md）：**
- 正确使用 `header=4` 和 `header=3` 加载两个补充表格
- 成功处理了 `Beta__females` 列的 "#REF!" 错误值
- 计算了 Fisher's exact test 的重叠富集
- 做了方向一致性分析（binomial test）
- 唯一的扣分点：富集分析在 union 上做而非分别对 CPA 和 SPIRO

**Skill_application.json 记录：** "Applied the generalized comparative treatment effect analysis skill. Used the guidance to load supplementary tables with correct header handling."

**为什么成功：** 源和目标任务不仅共享相同的任务类型，还共享 **相同的数据集** 和 **相同的分析背景**（GAHT 蛋白组学）。Skill 中的操作步骤几乎可以直接复用，agent 只需要调整分析的角度。

---

### 6. da-18-5→da-18-7（+0.10）—— 同类型框架正确，细节稍有缺失

| 项目 | 内容 |
|:---|:---|
| **Source Skill 名称** | "Cohort Genomic Analysis" |
| **Source 原始任务** | da-18-5: 乳腺癌队列基因组分析 |
| **Target 任务** | da-18-7: HR+/HER2- 转移性乳腺癌的 ESR1/MAPK 互斥性分析 |
| **Baseline / Transfer** | 0.85 → **0.95** |
| **Skill 应用方式** | 定义队列 → 加载突变/拷贝数数据 → 定义基因集 → 计算频率 → 统计检验 |

**相关文件路径：**
- Transfer 目录: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-18-7_pruned_transfer_da-18-5_to_da-18-7/`
- Skill 文件: `server1:/data/yjh/skill-transfer-eval/generalized_skills_pruned/da-18-5/SKILL.md`
- Judge 结果: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-18-7_pruned_transfer_da-18-5_to_da-18-7/logs/run_summary.json`
- Agent 轨迹: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-18-7_pruned_transfer_da-18-5_to_da-18-7/logs/trajectory.clean.jsonl`
- Trace 报告: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-18-7_pruned_transfer_da-18-5_to_da-18-7/outputs/trace.md`
- Answer: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-18-7_pruned_transfer_da-18-5_to_da-18-7/outputs/answer.txt`

**具体分析：**

同类型（mutation-analysis）transfer，但 target 是更具体的子问题（ESR1 LBD 突变 vs MAPK 通路改变的互斥性）。Skill 的通用框架（定义队列→加载突变→计算频率→统计检验）完全适用。

**轨迹对比分析：**

| 指标 | Baseline (无skill) | Transfer (有skill) | 差异 |
|:---|---:|---:|---:|
| 轮次 | 3 | 3 | 0 |
| 总 tool calls | 70 | 62 | **-8** |
| Error 次数 | 12 | 9 | **-3** |
| Bash 命令 | 41 | 38 | -3 |
| Skill 调用 | — | 1 | +1 |
| Effort 得分 | 41 | 38 | **0.93x** |

**关键差异：** 这是唯一一个 **effort 下降但分数提升** 的 SkillHelped 案例（effort 0.93x, Δ=+0.10）。Transfer agent 使用更少的 tool calls（62 vs 70）和更少的 bash 命令（38 vs 41）获得了更高的分数。**这说明 skill 帮助 agent 减少了无效探索，更有针对性地完成了分析。** Baseline 的 effort 更高但分数更低，说明 baseline 的 41 个 bash 命令中有相当一部分是重复尝试或错误方向。

**关键证据（来自 judge 结果）：**
- 6/7 个 criterion 获得 Level A
- 唯一扣分点：遗漏了"治疗意义讨论"（Criterion 6, Level B）
- 正确定义了 ESR1 LBD 突变（304-554 位氨基酸）、正确构建了 2x2 列联表
- 使用 one-sided Fisher's exact test 评估互斥性

**为什么成功：** 同类型 + 同一类别（oncology），skill 的框架完全覆盖了 target 的需求。唯一的缺失是 rubric 特定要求（治疗意义讨论），这不是 skill 的覆盖范围。

---

### 7. da-10-1→da-6-2（+0.20）—— 跨领域但通用"分组比较"框架奏效

| 项目 | 内容 |
|:---|:---|
| **Source Skill 名称** | "Comparative Frequency Analysis with Fold-Change and Validation" |
| **Source 原始任务** | da-10-1: 氨基酸组成频率比较 |
| **Target 任务** | da-6-2: 运动反应的性别差异模式分析（MoTrPAC） |
| **Baseline / Transfer** | 0.72 → **0.92** |
| **Skill 应用方式** | 按 assay/tissue 过滤 → 时间点完整性筛选 → 方向编码 → 分类为共享/性别特异性 → 统计检验 |

**相关文件路径：**
- Transfer 目录: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-6-2_pruned_transfer_da-10-1_to_da-6-2/`
- Skill 文件: `server1:/data/yjh/skill-transfer-eval/generalized_skills_pruned/da-10-1/SKILL.md`
- Judge 结果: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-6-2_pruned_transfer_da-10-1_to_da-6-2/logs/run_summary.json`
- Agent 轨迹: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-6-2_pruned_transfer_da-10-1_to_da-6-2/logs/trajectory.clean.jsonl`
- Trace 报告: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-6-2_pruned_transfer_da-10-1_to_da-6-2/outputs/trace.md`
- Answer: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/da-6-2_pruned_transfer_da-10-1_to_da-6-2/outputs/answer.txt`

**具体分析：**

这是 **跨类别（general-biology→cardiovascular）+ 跨类型（predictive-modeling→longitudinal-analysis）** 的 transfer，但获得了 +0.20 的提升。da-10-1 的 skill 核心是 **比较两组之间的频率差异**，而 da-6-2 需要 **比较男女之间的运动反应模式差异**。虽然数据和应用场景完全不同，但 "分组→比较→统计" 的通用方法论是相同的。

**轨迹对比分析：**

| 指标 | Baseline (无skill) | Transfer (有skill) | 差异 |
|:---|---:|---:|---:|
| 轮次 | 4 | 4 | 0 |
| 总 tool calls | 50 | 78 | **+28** |
| Error 次数 | 3 | 14 | **+11** |
| Bash 命令 | 24 | 32 | +8 |
| Skill 调用 | — | 3 | +3 |
| Effort 得分 | 24 | 32 | **1.33x** |

**关键差异：** 这是跨类别跨类型 transfer 中 effort 增加最显著的案例（1.33x）。Transfer agent 调用了 3 次 skill，做了更多 bash 命令，但也因此 error 从 3 激增到 14。**Skill 的"分组比较"框架虽然提供了方向，但 agent 需要大量试错才能将通用框架适配到具体的 MoTrPAC 数据集上。** Baseline 仅 3 个 error 加上 50 个 tool calls 已经覆盖了大部分内容（0.72），transfer 虽然增加了 28 个 tool calls 但从中获得了 0.20 的提升——**说明 skill 引导 agent 覆盖了额外 20% 的 rubric 要求，但代价是 4.7x 的 error 增加。**

**关键证据（来自 judge 结果）：**
- 6/7 个 criterion 获得 Level A
- 唯一扣分点：模式频率报告在性别分层集合中而非互斥类别中（Criterion 5, Level B）
- 正确筛选了转录组学 + vastus lateralis 组织的数据
- 实现了 4 时间点完整性筛选 + 方向编码
- 实现了三个互斥类别（shared, female-specific, male-specific）

**为什么成功：** 这里的 **"比较频率"的核心概念**（两组间的差异分析和分类）是跨领域通用的。da-10-1 的 skill 虽然来自氨基酸分析，但泛化后的"分组比较"框架完全可以应用于任何需要比较两组间频率差异的场景。

---

## SkillHarmed 轨迹分析：为什么 skill 起反作用？

基于对 12 组 SkillHarmed 案例的 trajectory 量化分析，我们发现 **skill 起反作用的核心机制不是"错误的指导"，而是"过早的满足"**。

### 三类典型失败模式

#### 模式一：Effort 大幅下降（"偷懒"模式）—— 4 组

以下案例中 transfer agent 的 effort 显著低于 baseline，agent 拿到 skill 后认为"我懂了"，过早停止了探索：

| 案例 | Δ | Effort 比 | Baseline bash | Transfer bash | 现象 |
|:---|:---:|:---:|:---:|:---:|:---|
| da-26-4→da-26-2 | -0.20 | **0.34x** | 118 | 40 | 142 次 tool calls → 62 次，大幅缩水 |
| da-10-1→da-6-5 | -0.25 | **0.47x** | 36 | 17 | 59 次 tool calls → 32 次 |
| da-5-1→da-26-2 | -0.18 | **0.59x** | 118 | 70 | 共享相同 target (da-26-2)，同样大幅缩水 |
| da-11-1→da-6-5 | -0.25 | **0.56x** | 36 | 20 | 与 da-10-1→da-6-5 共享 target (da-6-5)，模式一致 |
| da-25-1→da-18-7 | -0.15 | **0.63x** | 41 | 26 | 70 次 tool calls → 45 次 |

**典型例子：da-26-4→da-26-2（effort 0.34x）**

这是最极端的 case。Baseline agent 做了 **142 次 tool calls、118 次 bash 命令、26 次错误**——它非常努力地探索数据、试错、迭代。而 Transfer agent 拿到 skill 后，只做了 **62 次 tool calls、40 次 bash 命令、8 次错误**。虽然错误少了，但分数从 0.97 降到了 0.77。

**baseline 做了什么而 transfer 没做的：** Baseline agent 的 118 次 bash 命令覆盖了 5 个不同的分析方向（数据加载、质量过滤、统计检验、可视化、结果汇总），而 transfer agent 的 40 次 bash 命令只覆盖了 3 个方向。Skill 让 agent 以为"我已经知道重点了"，导致它跳过了探索性数据分析步骤。

#### 模式二：Effort 增加但方向错误（"迷失"模式）—— 5 组

以下案例中 transfer agent 投入了更多 effort，但 **努力的方向与 rubric 要求不匹配**：

| 案例 | Δ | Effort 比 | Baseline tool_calls | Transfer tool_calls | 现象 |
|:---|:---:|:---:|:---:|:---:|:---|
| da-13-6→da-13-1 | -0.26 | **1.52x** | 33 | 62 | 大量 effort 但方向错误 |
| da-10-3→da-10-1 | -0.30 | **1.21x** | 39 | 47 | 同类型但 skill 误导 |
| da-9-1→da-9-7 | -0.07 | **1.59x** | 55 | 62 | 最大 effort 比但 Δ 最小 |
| da-18-5→da-18-1 | -0.18 | **1.20x** | 31 | 41 | 同类型但 target 不同 |
| da-13-6→da-13-3 | -0.13 | **1.14x** | 24 | 32 | 同源 skill 但方向错误 |

**典型例子：da-13-6→da-13-1（effort 1.52x, Δ=-0.26）**

这是 **最严重的 harm 案例**（Δ=-0.26）。Transfer agent 做了 62 次 tool calls（baseline 33），但 **分数反而更低**。da-13-6 的 skill 是"Comparative Treatment Effect Analysis"，而 da-13-1 是"Cross-cohort differential expression analysis"。两者虽然同属 metabolic 类别，但 **skill 的"比较效应"框架误导 agent 去关注治疗效应的比较，而非差异表达的分析**。Agent 在 skill 的引导下投入了大量 effort 做相关性分析，却忽略了 rubric 要求的差异表达统计检验。

#### 模式三：Effort 相当但质量下降（"生搬硬套"模式）—— 3 组

以下案例中 effort 与 baseline 相当，但 transfer 的分数更低：

| 案例 | Δ | Effort 比 | Baseline errors | Transfer errors | 现象 |
|:---|:---:|:---:|:---:|:---:|:---|
| da-19-4→da-19-1 | -0.09 | 0.95x | 7 | 8 | 同类型但 skill 不适合 |
| da-17-5→da-14-3 | -0.14 | 1.13x | 3 | 6 | 跨类别生搬硬套 |
| da-13-6→da-13-3 | -0.13 | 1.14x | 5 | 7 | 同类别但类型不同 |

**典型例子：da-19-4→da-19-1（effort 0.95x, Δ=-0.09）**

与 da-19-4→da-19-6（+0.31，满分）和 da-19-4→da-19-3（+0.15）共享同一个 source skill，但 **target 任务 da-19-1 是 RNA-seq 分析而非染色质分析**。Effort 相当（0.95x），但 skill 的"染色质峰分析"框架与此完全无关。Agent 花了与 baseline 相当的努力，但因为 skill 占据了上下文窗口，**反而挤占了 agent 用于 RNA-seq 分析的工作记忆**。

### 失败模式总结

| 模式 | 案例数 | 核心机制 | 典型 Effort 比 |
|:---|:---:|:---|:---:|
| ① 偷懒（过早满足） | 4 | Skill 让 agent 认为"我懂了"，减少探索 | **0.34-0.63x** |
| ② 迷失（方向错误） | 5 | Skill 误导 agent 关注错误的分析方向 | **1.14-1.59x** |
| ③ 生搬硬套（质量下降） | 3 | Skill 不相关但 agent 仍尝试应用，占用上下文 | **0.95-1.14x** |

---

**相关文件路径：**
- 各 transfer 运行目录: `server1:/data/yjh/skill-transfer-eval/transfer_pruned/*/`
- 汇总结果: `server1:/data/yjh/skill-transfer-eval/summary_pruned/transfer_pruned_results.json`
- Baseline 结果: `server1:/data/yjh/skill-transfer-eval/summary/all_results.json`
- Pipeline 脚本: `server1:/data/yjh/skill-transfer-eval/run_pruned_transfer_pipeline.py`
- 本地运行脚本: `c:\Users\30670\Desktop\Autoskill\data\yjh\skill-transfer-eval\run_skill_transfer_pipeline.py`
- 重评分脚本: `server1:/data/yjh/skill-transfer-eval/batch_rejudge_gemini.py`
- Ablation 结果: `server1:/data/yjh/skill-transfer-eval/summary/ablations/`
- Pruning 元数据: `server1:/data/yjh/skill-transfer-eval/pruned_skills/`
- 任务定义: `server1:/tmp/biodsbench/python_task_table_schemas.jsonl`
- 任务分类: `server1:/tmp/biodsbench/python_tasks_with_class.jsonl`
- 本地评估工具: `c:\Users\30670\Desktop\Autoskill\25303977_0_as_an_example\evaluation\judge.py`
- 本地测试用例: `c:\Users\30670\Desktop\Autoskill\25303977_0_as_an_example\evaluation\test_cases.py`

> ⚠️ **重要提示**: Baseline 的 `run_summary.json` 文件曾被 Gemini-3.1-pro 重评分脚本覆盖（所有分数变为 0.0，judge reason 为 "400: model is overloaded"）。正确的 Baseline 分数保存在 `all_results.json`（由 qwen3.5-plus 评分）。Transfer 的 `run_summary.json` 是 qwen3.5-plus 评分，是正确的。

### 核心结论：Skill 迁移的净效果为负

在排除 baseline artifact 后，**skill 起反作用的次数（12）多于起作用的次数（7）**，净效果 = -5。这意味着**当前泛化 skill 的质量和迁移策略存在问题**，大多数情况下 agent 不带 skill 反而表现更好。

### 成功 vs 失败模式对比

| 维度 | ✅ 成功（7 组） | ❌ 失败（12 组） |
|:---|:---|:---|
| **同类型比例** | 4/7 (57%) | 4/12 (33%) |
| **同类别比例** | 6/7 (86%) | 9/12 (75%) |
| **Skill 操作数（平均）** | 4.6 | 3.8 |
| **Skill 被 agent 评价** | 都认定为"适用" | 都认定为"适用"（但实际不适用） |
| **典型模式** | 共享分析范式或通用框架 | 核心操作不匹配 / 跨领域生搬硬套 |

### 成功口诀（修正后）

| 条件 | 成功概率 | 典型案例 |
|:---|:---:|:---|
| 同类别 + 同类型 + 核心操作一致 | 中高 (4/12=33%) | da-19-4→da-19-6（满分）、da-13-6→da-13-5（0.90） |
| 同类别 + 不同类型 + 框架通用 | 低 (1/15=7%) | da-14-8→da-14-1（满分，唯一成功） |
| 跨类别 + 通用方法论 | 低 (2/10=20%) | da-10-1→da-6-2（0.92） |
| **Baseline=0（伪提升）** | **虚假** | 2 个 case 均为 pipeline artifact |

### 核心启示

1. **Skill 迁移的净效果为负（-5）**——当前策略需要重新思考
2. **同类型 + 同操作范式是最可靠的转移路径**，但成功率也仅 33%
3. **Agent 拒绝 skill 的判断值得信任**——7 个被拒绝的 case Δ≈0，不做比做错好
4. **Baseline=0 的"抢救"是虚假的**——da-17-1 的 baseline 首轮实际评分 78/100，pipeline 失败不等于 agent 失败
5. **Skill 的 harm 机制核心是"过早的满足"而非"错误指导"**——4/12 的 harmed 案例中 transfer agent 的 effort 不到 baseline 的 60%，agent 拿到 skill 后认为"我懂了"就停止了探索。另外 5 组虽然 effort 增加但方向错误，被 skill 误导到不相关的分析路径。
6. **当前泛化 skill 可能过于抽象**——pruning 后只剩 2-3 个操作，丢失了太多领域特定知识，导致"太通用而无法帮助"
7. **Effort ratio 可以作为 skill 是否正在起作用的实时指标**——如果 transfer agent 的 effort 显著低于 baseline（<0.8x），说明 skill 可能正在起反作用（过度自信效应）
8. **Error 数量与分数正相关（在 harmed 案例中）**——Baseline agent 平均 10.5 个错误比 transfer 的 8.0 个更多，但分数更高。更多的错误 = 更多的尝试 = 更全面的 rubric 覆盖

---

## 附录：各任务元数据

**相关数据来源：**
- BioDSBench 任务定义: `server1:/data/yjh/skill-transfer-eval/summary/all_results.json`（含任务类别/类型/难度）
- 任务 Schema: `server1:/tmp/biodsbench/python_task_table_schemas.jsonl`
- 任务分类: `server1:/tmp/biodsbench/python_tasks_with_class.jsonl`
- 本地副本: `c:\Users\30670\Desktop\Autoskill\tmp\biodsbench\python_task_table_schemas.jsonl`
- 本地副本: `c:\Users\30670\Desktop\Autoskill\tmp\biodsbench\python_tasks_with_class.jsonl`
- 源数据 BioDSBench: `server1:/tmp/biodsbench/`
- 本地 BioDSBench 数据: `c:\Users\30670\Desktop\Autoskill\BioDSBench\`
- 本地 BioDSA 数据: `c:\Users\30670\Desktop\Autoskill\BioDSA\`
- 本地 BioDSA 仓库: `c:\Users\30670\Desktop\Autoskill\tmp\BioDSA_repo\`
- 本地 example 任务: `c:\Users\30670\Desktop\Autoskill\25303977_0_as_an_example\`

| 任务 ID | 类别 | 任务类型 | 难度 |
|:---|:---|:---|:---:|
| da-1-3 | oncology | cell-composition | easy |
| da-1-4 | oncology | association-testing | — |
| da-10-1 | general-biology | predictive-modeling | easy |
| da-10-3 | general-biology | predictive-modeling | easy |
| da-11-1 | immunology | cell-cell-communication | easy |
| da-12-2 | oncology | pathway-enrichment | medium |
| da-12-4 | oncology | survival-analysis | medium |
| da-13-1 | metabolic | differential-expression | — |
| da-13-3 | metabolic | association-testing | easy |
| da-13-5 | metabolic | cross-cohort-comparison | medium |
| da-13-6 | metabolic | cross-cohort-comparison | medium |
| da-14-1 | immunology | clustering | easy |
| da-14-3 | immunology | association-testing | medium |
| da-14-8 | immunology | association-testing | medium |
| da-15-1 | neurology | differential-expression | easy |
| da-15-2 | neurology | co-expression-networks | medium |
| da-15-7 | neurology | association-testing | medium |
| da-15-8 | neurology | multi-omic-integration | — |
| da-17-1 | immunology | cell-composition | medium |
| da-17-3 | immunology | differential-expression | easy |
| da-17-5 | immunology | cell-composition | easy |
| da-18-1 | oncology | mutation-analysis | easy |
| da-18-5 | oncology | mutation-analysis | hard |
| da-18-7 | oncology | mutation-analysis | medium |
| da-19-1 | oncology | differential-expression | easy |
| da-19-3 | oncology | chromatin-profiling | — |
| da-19-4 | oncology | chromatin-profiling | hard |
| da-19-6 | oncology | chromatin-profiling | medium |
| da-25-1 | oncology | mutation-analysis | medium |
| da-26-2 | oncology | predictive-modeling | hard |
| da-26-4 | oncology | predictive-modeling | hard |
| da-4-1 | oncology | clustering | easy |
| da-4-7 | oncology | tcr-repertoire | hard |
| da-5-1 | oncology | multi-omic-integration | medium |
| da-5-3 | oncology | multi-omic-integration | easy |
| da-6-2 | cardiovascular | longitudinal-analysis | hard |
| da-6-5 | cardiovascular | multi-omic-integration | medium |
| da-9-1 | oncology | survival-analysis | medium |
| da-9-7 | oncology | association-testing | medium |
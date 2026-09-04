# 综合实验计划：统一任务集上的三种方法评估

## 概述

本计划定义了一个统一的实验框架，让 **三种方法**（1A raw trajectory few-shot、1B trajectory+skill few-shot、skill-opt）在 **同一组任务** 上进行评估，基于 V10 SmartSelector 实验设计中的 23-27 分类。

---

## 1. 任务划分：23 个 Source Tasks + 27 个 Target Tasks

### 1.1 23 个 Source Tasks（训练集 / 来源任务）

这些是 V10 实验设计中作为"源"的任务，skill-opt 用它们作为训练数据，baselines 用它们的 trajectory/skill 做 few-shot 注入。

| # | Source Task | 出现批次 | 用途 |
|:--:|:--|:--:|:--|
| 1 | da-26-2 | B1 | 源 |
| 2 | da-20-3 | B1, B1 | 源 |
| 3 | da-13-5 | B1 | 源 |
| 4 | da-14-3 | B1, B2 | 源 |
| 5 | da-5-1 | B1 | 源 |
| 6 | da-19-4 | B1 | 源 |
| 7 | da-13-3 | B1 | 源 |
| 8 | da-18-5 | B1 | 源 |
| 9 | da-19-3 | B1, B2 | 源 |
| 10 | da-4-6 | B1 | 源 |
| 11 | da-18-1 | B2, B3 | 源 |
| 12 | da-13-1 | B2 | 源 |
| 13 | da-15-1 | B2 | 源 |
| 14 | da-8-1 | B2, B3 | 源 |
| 15 | da-8-2 | B3 | 源 |
| 16 | da-19-1 | B3 | 源 |
| 17 | da-6-2 | B3 | 源 |

> **注**: 23 个 pair 中有 17 个唯一源任务。部分任务（如 da-20-3、da-19-3、da-8-1）出现在多个 pair 中，对应不同的目标任务。

### 1.2 27 个 Target Tasks（测试集 / 目标任务）

这些是用于评估 **所有三种方法** 迁移效果的 27 个目标任务。Baselines 已经在 23 个 pair 上跑了这些目标的一部分，skill-opt 也需要在同样的目标集上评估。

| # | Target Task | 来源 | 出现在 V10 Pair |
|:--:|:--|:--|:--:|
| 1 | da-10-1 | B1 | ✅ B1 (←da-26-2) |
| 2 | da-12-2 | B1 | ✅ B1 (←da-20-3) |
| 3 | da-13-6 | B1 | ✅ B1 (←da-13-5) |
| 4 | da-15-7 | B1, B3 | ✅ B1 (←da-14-3), B3 (←da-8-1, da-8-2) |
| 5 | da-15-8 | B1 | ✅ B1 (←da-5-1) |
| 6 | da-19-6 | B1, B2 | ✅ B1 (←da-19-4), B2 (←da-19-3) |
| 7 | da-20-4 | B1 | ✅ B1 (←da-20-3) |
| 8 | da-24-3 | B1, B2 | ✅ B1 (←da-13-3), B2 (←da-14-3, da-8-1) |
| 9 | da-25-1 | B1, B2 | ✅ B1 (←da-18-5), B2 (←da-18-1) |
| 10 | da-26-4 | B1 | ✅ B1 (←da-26-2) |
| 11 | da-8-3 | B1, B2, B3 | ✅ B1 (←da-19-3), B2 (←da-13-1, da-15-1), B3 (←da-19-1) |
| 12 | da-9-1 | B1, B3 | ✅ B1 (←da-4-6), B3 (←da-6-2) |
| 13 | da-4-7 | B3 | ✅ B3 (←da-18-1) |
| 14 | da-10-3 | 剩余 | 未出现在 V10 pairs |
| 15 | da-11-1 | 剩余 | 未出现在 V10 pairs |
| 16 | da-12-4 | 剩余 | 未出现在 V10 pairs |
| 17 | da-1-3 | 剩余 | 未出现在 V10 pairs |
| 18 | da-1-4 | 剩余 | 未出现在 V10 pairs |
| 19 | da-14-1 | 剩余 | 未出现在 V10 pairs |
| 20 | da-14-8 | 剩余 | 未出现在 V10 pairs |
| 21 | da-15-2 | 剩余 | 未出现在 V10 pairs |
| 22 | da-16-1 | 剩余 | 未出现在 V10 pairs |
| 23 | da-17-1 | 剩余 | 未出现在 V10 pairs |
| 24 | da-17-3 | 剩余 | 未出现在 V10 pairs |
| 25 | da-17-5 | 剩余 | 未出现在 V10 pairs |
| 26 | da-18-7 | 剩余 | 未出现在 V10 pairs |
| 27 | da-20-1 | 剩余 | 未出现在 V10 pairs |
| 28 | da-3-4 | 剩余 | 未出现在 V10 pairs |
| 29 | da-3-5 | 剩余 | 未出现在 V10 pairs |
| 30 | da-4-1 | 剩余 | 未出现在 V10 pairs |
| 31 | da-5-3 | 剩余 | 未出现在 V10 pairs |
| 32 | da-6-5 | 剩余 | 未出现在 V10 pairs |
| 33 | da-9-7 | 剩余 | 未出现在 V10 pairs |

> **注**: 27 个 target tasks 包含 13 个 V10 pair 中出现的目标 + 20 个未出现在任何 pair 中的任务。实际共 **33 个"目标"任务**，但我们可以根据用户需求精确定义 27 个。

---

## 2. 三种方法的实验设计

### 2.1 方法 A: Raw Trajectory Few-Shot (Baseline 1A)

| 项目 | 说明 |
|:--|:--|
| **状态** | ✅ **正在运行中** |
| **Runner** | `/tmp/run_fewshot_baseline.sh` (tmux: `fewshot_baseline`) |
| **实验数量** | 23 个 pair × 1 变体 = 23 个实验 |
| **Prompt 来源** | 源任务的 raw trajectory → markdown 格式 |
| **Prompt 文件** | `/data/yjh/skill-transfer-eval/fewshot_prompts/*_1A_raw_traj.md` |
| **进度** | Batch 18/25, ~25/46 completed |
| **评估方式** | 直接在目标任务上运行 harness，注入 trajectory 作为 system prompt |

### 2.2 方法 B: Trajectory + Skill Few-Shot (Baseline 1B)

| 项目 | 说明 |
|:--|:--|
| **状态** | ✅ **正在运行中**（与 1A 一起在同一个 runner 中） |
| **Runner** | `/tmp/run_fewshot_baseline.sh` (tmux: `fewshot_baseline`) |
| **实验数量** | 23 个 pair × 1 变体 = 23 个实验 |
| **Prompt 来源** | 源任务的 raw trajectory + 源任务的 skill bundle (SKILL.md) |
| **Prompt 文件** | `/data/yjh/skill-transfer-eval/fewshot_prompts/*_1B_traj_plus_skill.md` |
| **进度** | Batch 18/25, ~25/46 completed |
| **评估方式** | 在目标任务上运行 harness，注入 trajectory + skill 作为 system prompt |

### 2.3 方法 C: Skill-Opt 强化学习训练

| 项目 | 说明 |
|:--|:--|
| **状态** | 🔴 **待启动**（需要修复 timeout + 创建初始 skill） |
| **框架** | Microsoft SkillOpt v0.2.0 |
| **位置** | `/data/yjh/skill-opt/` |
| **Adapter** | `BioMNIBenchAdapter` (已部署，已验证) |
| **训练数据** | 23 个 source tasks（V10 源任务集） |
| **测试数据** | 27 个 target tasks（同 baselines 的目标集） |
| **训练算法** | Skill-opt 的强化学习循环（rollout → judge → reflect → update） |
| **初始 Skill** | 需要从已有的 skill bundles 构建（51 个 bundles 可用） |

---

## 3. Skill-Opt 详细配置

### 3.1 Dataloader 配置

```yaml
dataloader:
  type: biomnibench
  split_mode: ratio
  split_ratio: "2:1:7"  # 23 source → 10 train : 5 val : 8 test
  # 或者使用 explicit split:
  # split_mode: explicit
  # train: [da-26-2, da-20-3, ...]  # 23 source tasks
  # val: [da-13-5, da-14-3, ...]
  # test: [da-10-1, da-12-2, ...]   # 27 target tasks
```

### 3.2 Rollout 超时修复

**当前问题**: `rollout.py` 传 `timeout_seconds=300` 但实际 harness 的 `run_events.jsonl` 显示 `timeoutSeconds: 120`。

**修复方案**:
1. 在 `rollout.py` 的 `_run_harness()` 中，确保 `--timeout-seconds` 参数正确传递
2. 设置 `timeout_seconds = 600`（10 分钟）给每个任务，避免超时
3. 在 `run_batch()` 中设置 `exec_timeout = 600`

### 3.3 初始 Skill 构建

从 51 个 skill bundles 中提取通用 skill 内容作为初始 skill。每个 bundle 包含 `SKILL.md`，描述该任务的 bioinformatics 最佳实践。

**构建策略**: 从 17 个唯一源任务对应的 skill bundles 中提取公共 pattern，合并为一个通用的初始 skill。

### 3.4 训练循环参数

| 参数 | 值 | 说明 |
|:--|:--:|:--|
| RL 步数 | 20-50 | 根据收敛情况调整 |
| 每步 rollout 任务数 | 4-8 | 从 23 个 source tasks 中采样 |
| 每任务 max_rounds | 3 | 同 baseline 配置 |
| 超时 | 600s/任务 | 避免 API 超时 |
| Judge 模型 | Vendor2/Gemini-3.1-pro | 同 baseline |
| Solver 模型 | Vendor3/DeepSeek-V4-Flash | 同 baseline |
| 并发数 | 2 | 避免 API 限流 |

---

## 4. 执行时间线

### Phase 1: Baseline Runs（进行中）
| 步骤 | 状态 | 预计完成 |
|:--|:--:|:--:|
| 1A Raw trajectory few-shot (23 个实验) | 🟡 运行中 | ~10-12 小时 |
| 1B Trajectory+skill few-shot (23 个实验) | 🟡 运行中 | ~10-12 小时 |
| 收集 1A/1B 结果 | ❌ 未开始 | Baseline 完成后 |

### Phase 2: Skill-Opt 准备
| 步骤 | 状态 | 预计耗时 |
|:--|:--:|:--:|
| 修复 rollout.py 超时问题 | 🔴 待修复 | ~30 分钟 |
| 构建有意义的初始 skill | 🔴 待创建 | ~1 小时 |
| 配置 23-27 任务划分 | 🔴 待配置 | ~30 分钟 |
| 测试单步 rollout 验证 | 🔴 待测试 | ~1 小时 |

### Phase 3: Skill-Opt 训练
| 步骤 | 状态 | 预计耗时 |
|:--|:--:|:--:|
| 启动 skill-opt 训练（20-50 步） | 🔴 未启动 | ~24-48 小时 |
| 监控训练进度 | 🔴 未启动 | 持续 |
| 导出最终 skill | 🔴 未启动 | 训练完成后 |

### Phase 4: 评估
| 步骤 | 状态 | 预计耗时 |
|:--|:--:|:--:|
| 用最终 skill 在 27 个 target tasks 上 rollout | 🔴 未启动 | ~6-12 小时 |
| 收集所有三种方法的结果 | 🔴 未启动 | ~1 小时 |
| 汇总对比分析 | 🔴 未启动 | ~2 小时 |

---

## 5. 结果对比矩阵

| 实验 ID | Source | Target | 1A Raw Traj | 1B Traj+Skill | Skill-Opt |
|:--|:--|:--:|:--:|:--:|:--:|
| B1-pair-01 | da-26-2 | da-10-1 | 🟡 | 🟡 | ❌ |
| B1-pair-02 | da-20-3 | da-12-2 | 🟡 | 🟡 | ❌ |
| B1-pair-03 | da-13-5 | da-13-6 | 🟡 | 🟡 | ❌ |
| B1-pair-04 | da-14-3 | da-15-7 | 🟡 | 🟡 | ❌ |
| B1-pair-05 | da-5-1 | da-15-8 | 🟡 | 🟡 | ❌ |
| B1-pair-06 | da-19-4 | da-19-6 | 🟡 | 🟡 | ❌ |
| B1-pair-07 | da-20-3 | da-20-4 | 🟡 | 🟡 | ❌ |
| B1-pair-08 | da-13-3 | da-24-3 | 🟡 | 🟡 | ❌ |
| B1-pair-09 | da-18-5 | da-25-1 | 🟡 | 🟡 | ❌ |
| B1-pair-10 | da-26-2 | da-26-4 | 🟡 | 🟡 | ❌ |
| B1-pair-11 | da-19-3 | da-8-3 | 🟡 | 🟡 | ❌ |
| B1-pair-12 | da-4-6 | da-9-1 | 🟡 | 🟡 | ❌ |
| B2-pair-01 | da-18-1 | da-25-1 | 🟡 | 🟡 | ❌ |
| B2-pair-02 | da-13-1 | da-8-3 | 🟡 | 🟡 | ❌ |
| B2-pair-03 | da-15-1 | da-8-3 | 🟡 | 🟡 | ❌ |
| B2-pair-04 | da-19-3 | da-19-6 | 🟡 | 🟡 | ❌ |
| B2-pair-05 | da-14-3 | da-24-3 | 🟡 | 🟡 | ❌ |
| B2-pair-06 | da-8-1 | da-24-3 | 🟡 | 🟡 | ❌ |
| B3-pair-01 | da-8-1 | da-15-7 | 🟡 | 🟡 | ❌ |
| B3-pair-02 | da-8-2 | da-15-7 | 🟡 | 🟡 | ❌ |
| B3-pair-03 | da-19-1 | da-8-3 | 🟡 | 🟡 | ❌ |
| B3-pair-04 | da-18-1 | da-4-7 | 🟡 | 🟡 | ❌ |
| B3-pair-05 | da-6-2 | da-9-1 | 🟡 | 🟡 | ❌ |

> **图例**: 🟡 = 运行中 / ✅ = 已完成 / ❌ = 未开始 / 🔴 = 有问题

---

## 6. 关键差异：Few-Shot vs Skill-Opt

| 维度 | Few-Shot (1A/1B) | Skill-Opt |
|:--|:--|:--|
| **学习方式** | 一次性 prompt 注入 | 多步 RL 迭代优化 |
| **源任务利用** | 每个 pair 独立使用 | 所有 23 个 source tasks 联合训练 |
| **Skill 形式** | 静态文本（trajectory +/- skill bundle） | 动态优化 text skill |
| **泛化能力** | 每个 pair 独立评估 | 产出通用 skill，可用于任何 target |
| **计算开销** | 23 × 1 次 harness 调用 | 20-50 步 × 每步 4-8 次 rollout |
| **结果可比性** | 同任务集上直接对比 | 最终 skill 在 27 个 targets 上评估 |

---

## 7. 下一步行动清单

### 立即执行（优先级 1）
- [ ] **修复 rollout.py 超时**: 确认 `--timeout-seconds` 参数正确传递，设为 600s
- [ ] **创建初始 skill**: 从 51 个 skill bundles 中提取公共 pattern
- [ ] **配置 23-27 split**: 在 dataloader 中明确划分训练/测试集

### 监控中（优先级 2）
- [ ] **等待 baseline 完成**: 检查 tmux `fewshot_baseline` 进度
- [ ] **收集 baseline 结果**: 完成后运行 `collect_results.py`

### 后续执行（优先级 3）
- [ ] **启动 skill-opt 训练**: 在 tmux 中运行完整训练循环
- [ ] **监控训练进度**: 检查 reward 收敛情况
- [ ] **最终评估**: 用最优 skill 在 27 个 targets 上 rollout
- [ ] **汇总对比**: 生成三种方法的对比报告
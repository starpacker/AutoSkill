# SmartSelector v7 设计文档（已验证版）
## v7.1 更新

**核心变更**: 从"仅 Gemini 数据"升级到"全部数据 + 迁移类型感知"，大幅提升数据量和泛化能力。

| 变更 | v7 (原版) | v7.1 (当前) |
|:--|:--|:--|
| 数据源 | 仅 Gemini judge (216 条) | 全部 judge (Gemini+DeepSeek) |
| 样本量 | 216 条 | **231 条** |
| 打分公式 | f(bl) + shrink | f(bl) + shrink + **type_offset** |
| 收缩强度 k | 15 (保守) | **8** (LOTOCV-optimal) |
| 迁移类型感知 | 无 | 每种 transfer type 有独立 offset |
| 默认类型 | — | generalized-transfer |
| 最小分数阈值 | 无 | **0.03** (过滤噪声推荐) |

### 关键发现

1. **type_offset 效果显著**: generalized-transfer 比其他类型高约+0.12，expand-within 低约-0.15
2. **k=8 LOTOCV-optimal**: 比 k=3 有更好的 gate accuracy (96.15% vs 87.82%) 和更低的 RMSE (0.3312 vs 0.3389)
3. **数据量增加 7%**: 231 条 vs 216 条，因为 DeepSeek baseline 数据不完整，新增有效记录有限
4. **最小分数阈值 0.03**: 过滤了 13 个噪声级推荐 (score 0.007-0.009)，将 selection 从 29/50 降至 14/50

下面详细说明 v7.1 的四项核心变更。`

---

## v7.1 变更一：数据加载（去除 only_gemini 限制）

### 背景

原版 v7 只使用 Gemini judge 的 216 条记录。这导致：
- 训练数据严重不足（LOTOCV 28 folds，每个 fold 平均 <8 条记录）
- 无法捕捉不同 judge 的行为差异
- 收缩强度需要很大（k=15）来补偿数据稀疏

### 变更

`v7_data.py` 的 `load_records()` 函数：
- `only_gemini` 默认值从 `True` 改为 `False`
- 自动为每条记录匹配正确的 baseline（Gemini 记录用 Gemini baseline，DeepSeek 记录用 DeepSeek baseline）
- 仍然排除 infra 类错误（timeout, infra_error），保留 `failed` 状态

### 效果

| 指标 | v7 (仅 Gemini) | v7.1 (全部数据) |
|:--|:--:|:--:|
| 有效样本 | 216 | **~1000+** |
| 唯一 Source | 22 | 全部 |
| 唯一 Target | 28 | 全部 |
| LOTOCV folds | 28 | 更多 |

---

## v7.1 变更二：Per-Type Offset 信号

### 动机

不同 transfer 类型的平均结果差异巨大：

| 类型 | avg_delta | % helpful |
|:--|:--:|:--:|
| generalized-transfer | +0.03 | 52% |
| generalized-cross | -0.10 | 20% |
| expand-cross | -0.15 | 22% |
| expand-within | -0.34 | 13% |
| generalized-within | -0.37 | 19% |
| raw-cross | -0.21 | 17% |
| raw-within | -0.40 | 18% |

**generalized-transfer 是唯一平均为正的类型**，差距高达 0.37（vs expand-within）。这个信号不应该被忽略。

### 做法

`compute_type_offsets()` 在 `v7_model.py` 中：

1. 对每条记录计算 `residual = delta - (f_hat(baseline) + shrink_residual_source)`
2. 按 `tx_type` 分组，取均值
3. 每个 type 的 offset 相当于"在 baseline 和 source 效应之后，这种类型本身还有多少额外偏移"

### 在新打分公式中的角色

```
score(t, s, type) = f_hat(baseline_t) + shrink_residual_s + type_offset[type]
```

- type_offset 是**加在整个类型上的固定偏移**，不区分具体 source
- 这意味着：当选择 generalized-transfer 时，所有候选 skill 的 score 都统一上移
- expand-within 的负 offset 会自动降低所有候选 score，使"不迁移"更容易获胜

### 实际 offset 值（已验证）

| 类型 | offset | 含义 |
|:--|:--:|:--|
| generalized-transfer | **+0.1218** | 泛化迁移是最好的类型 |
| expand-cross | +0.0427 | 跨类别扩展微正 |
| expand-within | +0.0049 | 同类别扩展接近中性 |
| generalized-cross | -0.0146 | 跨类别泛化接近中性 |
| raw-cross | -0.0509 | 原生 skill 跨类别略负 |
| generalized-within | -0.0984 | 同类别泛化较差 |
| raw-within | -0.1108 | 同类别原生最差 |

---

## v7.1 变更三：LOTOCV 确定的收缩强度 k=8

### 为什么需要调整

原版 v7 的 k=15 是基于 216 条 Gemini 数据用 LOTOCV 确定的。在 v7.1 全部 231 条数据上重跑 LOTOCV 网格搜索，结果如下：

| k | Top-1 | Gate | RMSE |
|:--:|:--:|:--:|:--:|
| 1 | 88.46% | 82.05% | 0.3483 |
| 2 | 88.46% | 87.82% | 0.3425 |
| 3 | 88.46% | 87.82% | 0.3389 |
| 5 | 88.46% | 87.82% | 0.3346 |
| **8** | **88.46%** | **96.15%** | **0.3312** |
| 10 | 88.46% | 96.15% | 0.3298 |
| 15 | 84.62% | 96.15% | 0.3277 |
| 20 | 80.77% | 96.15% | 0.3266 |
| 30 | 73.08% | 96.15% | 0.3253 |

**k=8 是最优选择**: 与 k=3 相同 Top-1 (88.46%)，但 Gate 更好 (96.15% vs 87.82%)，RMSE 更低 (0.3312 vs 0.3389)。k=8 在保持召回率的同时大幅减少了误报。

### 与原始 v7 对比

| 方法 | Top-1 | Gate | RMSE |
|:--|:--:|:--:|:--:|
| v7 (k=15, 216 条) | 62.50% | 100% | 0.3389 |
| **v7.1 (k=8, 231 条)** | **88.46%** | **96.15%** | **0.3312** |
| v7.1 无 type offset | 84.62% | 86.54% | 0.3584 |
| global-best | 73.08% | 96.15% | 0.3225 |

**Top-1 从 62.50% 提升到 88.46%** — 主要因为全部 231 条数据让 isotonic regression 曲线更稳定，建模更准确。Type offset 贡献了 3.84% 的 Top-1 提升（消融验证）。

---

## v7.1 变更四：最小分数阈值 0.03

### 动机

原始 dry-run 显示 29/50 被选，其中 13 个选择的 score 在 0.007-0.009 范围内（噪声水平）。训练数据中最小有意义正 delta 是 +0.03（第 178 个排序后 delta 值）。

### 做法

在 `select_best_skill()` 中增加 `min_score_threshold=0.03` 参数。如果最佳 score 低于阈值，返回"不迁移"。

### 效果

- 29/50 → 14/50 被选（减少 15 个噪声推荐）
- 所有保留的推荐 score ≥ 0.0338，具有实际意义
- 被过滤的 target 都是 baseline ≥ 0.68 的任务，type_offset + f(bl) 太小不足以产生有意义信号

---

## v7.1 完整打分流程`

## v7.1 完整打分流程

```
输入: target_task (task_id), 23 skill candidates, baselines dict, transfer_type

1. 加载 data
   - 从 results_index.json 加载所有 transfer 记录
   - 包含全部 judge（Gemini + DeepSeek），自动匹配正确 baseline
   - 过滤：排除 infra 类错误（timeout, infra_error）

2. 拟合 f_hat(bl)  ← isotonic regression on 全部记录（可缓存）

3. **HIERARCHY**: 
   - 计算 per-source raw residual (delta - f(bl))
   - 计算 per-type offset (delta - f(bl) - source_raw, shrunk + centered, k_type=15)
   - 计算 skill residual (delta - f(bl) - type_offset)
   - 收缩 (James-Stein, k=8)

4. 计算每个 transfer type 的 type_offset（可缓存，不依赖 target）

5. 对当前 target_task:
   a. 获取 baseline_t
   b. 获取 type_offset 根据 transfer_type
   c. 计算 f_hat(baseline_t)
   d. 对每个 skill s:
      score = f_hat(baseline_t) + shrink(residual_s) + type_offset[type]
   e. 候选集 = [score(t,s,type) for all s] + [0]  ← "不迁移"
   f. 选 argmax

输出: (selected_source, score)
      selected_source 可能为 None（表示"不迁移"）
```

---

## 服务器验证新模型效果

### 验证步骤

1. 在服务器上更新代码（已经部署 v7.1 代码）
2. 运行 `SmartSelectorV7` 的 dry-run 观察 selection 变化
3. 对比 v7 (k=15, 仅 Gemini) 和 v7.1 (k=3, 全部数据, type_offset) 的推荐差异
4. 运行 LOTOCV 评估确认指标提升

### 预期变化

- 更多 low-baseline target 会收到迁移推荐（因为数据更多，信号更可靠）
- generalized-transfer 类型的推荐更自信（type_offset 是正数）
- expand-within 类型几乎不会推荐迁移（type_offset 是负数，f(bl) 也是负数）

---

## 当前代码结构

```
skill_selector/
├── v7_data.py              # 数据加载、过滤、LOTOCV split（v7.1: 去除 only_gemini 限制）
├── v7_model.py              # 核心模型（v7.1: 新增 compute_type_offsets, k=3）
├── evaluate_v7.py           # LOTOCV 评估 + 网格搜索（v7.1: 支持 --no-type-offset 消融）
├── smart_selector_v7.py     # SmartSelectorV7 类（v7.1: 默认 use_type_offsets=True）
├── ablation_v7.py           # 消融实验脚本
├── run_remote.py            # 远程执行客户端（含 --v7 支持）
└── __init__.py              # 导出 SmartSelectorV7
```

### v7_model.py 核心函数（v7.1 更新）

| 函数 | 说明 | v7.1 变更 |
|:--|:--|:--|
| `fit_baseline_curve(records)` | PAVA isotonic regression | 使用全部数据，曲线更稳定 |
| `compute_skill_residuals(records, f_hat)` | 计算基线调整残差 | 无变化 |
| `shrink_estimates(skill_stats, k=8)` | James-Stein 收缩 | **k 默认从 15 改为 8 (LOTOCV-optimal)** |
| `compute_type_offsets(records, f_hat, source_raw_residuals)` | **新增** 计算迁移类型偏移（含 source_raw 抵消） | 全新函数 |
| `select_best_skill(..., min_score_threshold=0.03)` | 选择最佳 skill | 新增 min_score_threshold 过滤噪声 |
| `predict_score(baseline_t, f_hat, shrink, type_offset=0)` | 打分 | **新增 type_offset 参数** |
| `select_best_skill(...)` | 选最佳 skill vs 不迁移 | **新增 type_offset 参数** |
| `model_to_json` / `model_from_json` | 序列化 | **新增 type_offsets 字段** |

### 超参（v7.1 更新）

| 参数 | v7 默认值 | v7.1 默认值 | 说明 |
|:--|:--:|:--:|:--|
| k | 15.0 | **3.0** | 收缩强度（数据更多 → 不需要强收缩） |
| n_bins | 10 | 10 | isotonic regression 预处理 bin 数 |
| use_type_offsets | — | **True** | 是否启用迁移类型偏移 |
| default_type | — | **generalized-transfer** | 默认迁移类型 |

---

## 批量泛化剩余 27 个任务的 skill

### 背景

当前只有 23 个 generalized skills（对应 23 个 source task）。剩余 27 个 task 没有 generalized skill，只能作为 target 接收 skill，不能作为 source 提供 skill。

### 目标

为剩余 27 个 task 生成 generalized skill，使 **所有 50 个 task 都有 skill**。

### 所需步骤

1. 找到 27 个没有 generalized skill 的 task
2. 获取它们的 oracle skill（从 ablation results 中提取）
3. 用 LLM 泛化为 task-agnostic 版本
4. 部署到 generalized_skills/ 目录
5. 更新 results_index 使其可以被 selector 识别

### 验证

- 泛化完成后，`SmartSelectorV7` 的可用 skill 从 23 个增加到 50 个
- 重新运行 LOTOCV 评估，确认指标变化
- 对 low-baseline target 做额外的迁移实验验证

## 核心思路

**从"手工分档 + 启发式权重"升级到"数据驱动的统计建模"**。

v6 的所有权重（pair_score 分档边界、rep_bonus 分档、semantic_score 权重 0.50、归一化分母 1.60、bl_factor 分段线性函数、confidence 公式）都是**拍脑袋定的**，没有任何数据验证。v7 的核心改进是：

1. **用数据拟合代替手工分档**（isotonic regression → baseline 效应曲线）
2. **用收缩估计代替手工加分**（James-Stein shrinkage → skill 残差估计）
3. **用 Leave-One-Task-Out CV 调参**（替代手工调权重）
4. **消除"不迁移"的概念错误**（v6 的硬门控 `if bl>0.85: return None` 应被自然涌现的门控替代）

---

## 一、基础数据准备

### 数据来源

从 `results_index.json` 获取全部 transfer 记录，每条数据结构：

```json
{
    "source": "da-13-5",
    "target": "da-25-1",
    "reward": 0.75,
    "baseline": 0.50,
    "delta": 0.25,
    "status": "success",
    "type": "generalized-transfer",
}
```

### 数据过滤

- **只保留 Gemini judge 的样本**（排除 33 条非 Gemini）
- **只排除 infra 错误**（timeout=5, infra_error=1），**保留 status="failed"**
  - 关键区别：`failed` 表示 **skill 导致 agent 能力下降**（真实信号），不是 infra 错误
  - 排除 infra 类错误共 2 条
- 有效样本量：**216 条**

### 关键统计量

| 指标 | 值 |
|:--|:--:|
| 有效样本 | 216 |
| 唯一 Source | 22 个（从 transfer 中提取） |
| 唯一 Target | 28 个（有 transfer 记录的） |
| Generalized Skills | 23 个（在 `generalized_skills/` 目录下） |
| 总 Task 数 | 50（BioDSBench） |
| LOTOCV folds | 28 |

### 为什么只有 23 个 skills 而不是 50 个？

**不是每个 task 都有 generalized skill。** 只有被选为 **source task** 的 task 才有 generalized skill（即它们的 skill 被 generalization 并 transfer 到其他 task）。其他 27 个 task 只作为 **target**（接收 skill），不作为 **source**（提供 skill）。

23 个 generalized skills 中，22 个在 transfer 记录中实际出现过。`da-19-4` 有 generalized skill 但从未实际作为 source 被 transfer 过。

---

## 二、打分公式（消融验证版）

```
score(t, s) = f_hat(baseline_t)    # baseline 效应曲线
            + shrink(residual_s)   # skill 残差收缩估计

score(t, ∅) = 0                    # "不迁移"固定为 0
```

### 已验证：什么不起作用

基于 LOTOCV 消融实验（216 条记录，28 folds）：

| 组件 | 验证结果 | 证据 |
|:--|:--|:--|
| **compat_tag** (操作标签匹配) | ❌ 零贡献 | 所有 λ∈{0,0.1,0.2,0.3,0.5} 结果完全相同 |
| **pair_boost** (贝叶斯融合) | ❌ 零贡献 | 所有 τ∈{1,2,3,5,8} 结果完全相同 |
| 两者皆移除 | ✅ 不影响 | 62.50% Top-1, 0.3389 RMSE |

**结论**：这两个组件被完全移除，v7 简化为 `f(bl) + shrinkage(k)`。

### 对比 v6 的核心变化

| 方面 | v6 | v7 |
|:--|:--|:--|
| Baseline 门控 | 硬编码 if-else 分档 + 手工 bl_factor | isotonic regression 拟合连续曲线 |
| Source reputation | 手工分档加分 (0.30/0.20/0.10/...) | James-Stein 收缩估计（自动处理 n 和方差） |
| Pair history | 分档打分 (0.90/0.70/0.50/...) | ❌ 移除（消融验证无效） |
| Semantic match | 权重 0.50（硬编码） | ❌ 移除（消融验证无效） |
| Similarity | 权重 0.10（弱信号） | **移除**（已被证伪，r=0.016） |
| 风险惩罚 | 无 | 内置在收缩估计中 |
| 置信度 | 手工公式 | 不单独算置信度，直接由 score 排序 |
| 不迁移门控 | 硬编码 if-else | 自然涌现：score(t,∅)=0 vs score(t,s)=f(bl)+shrink |
| 调参 | 全手工 | Leave-One-Task-Out CV 网格搜索 |

---

## 三、Stage 1: Baseline 效应曲线 f_hat(bl)

### 为什么需要

直接用 skill 的全局 avg_delta 来比较技能，存在 **Simpson's paradox 风险**：如果某个技能恰好大多被拿去测高 baseline 的任务，它的全局均值会偏低，但这不代表这个技能本身差。

### 做法

用全部有效样本的 `(baseline, delta)` 点，拟合一条与具体技能无关的曲线：

```
f(bl) = E[delta | baseline = bl]
```

**用 isotonic regression（PAVA 算法）**：
- 1 维、216 个点，数据量足够
- 天然符合"baseline 越高，平均 delta 越低"的先验单调性假设
- 不会过拟合

### 10-bin 预处理

1. 按 baseline 升序排序，分成 10 等频 bin
2. 每个 bin 内计算 `mean(baseline)` 和 `mean(delta)`
3. 对 10 个 bin 均值做 isotonic regression

### 拟合结果（实际数据）

```
f(0.0) = -0.0705    ← 即使 baseline 为零，平均转移也会降低表现
f(0.1) = -0.0705
f(0.2) = -0.0705
f(0.3) = -0.0705
f(0.4) = -0.0705
f(0.5) = -0.1185    ← 拐点：baseline 超过 0.5 后转移伤害加速
f(0.6) = -0.2047
f(0.7) = -0.2401
f(0.8) = -0.3038
f(0.9) = -0.4070
f(1.0) = -0.4815    ← baseline 满时，转移最有害
```

**关键发现：f(bl) 在所有 baseline 水平上都是负的。** 这意味着**平均而言，任何 skill 转移都会降低 agent 表现**。这是合理的——baseline 已经是"让 agent 自己解决"，引入外部 skill 大概率干扰。

### 在打分公式中的角色

- `f(bl_t)` 是**加在每一个技能候选上的固定偏移**
- 技能之间互相比较时，`f(bl_t)` 完全抵消——真正决定技能排名的只有 `shrink(residual_s)`
- `f(bl_t)` 唯一的作用是 **"技能 vs 不迁移" 的门控判断**：
  - 高 baseline 时 f(bl) 很负 → 所有技能 score 都低于 0 → "不迁移"自动获胜
  - 低 baseline 时 f(bl) 接近 0 → 技能有机会赢"不迁移"
- **R² = 0.1245**：f(bl) 解释了 12.5% 的 delta 方差

---

## 四、Stage 2: Skill 残差收缩估计

### 残差计算

对每条记录，计算**去 baseline 效应后的残差**：

```
residual_i = delta_i - f_hat(baseline_i)
```

### 对每个 skill 聚合

```
raw_residual_s = mean(residual_i for i where skill == s)
n_s            = 该 skill 的样本数
```

### James-Stein 收缩

```
shrink(residual_s, n_s) = (n_s · raw_residual_s + k · 0) / (n_s + k)
```

- 收缩目标为 0（中性先验："平均 skill 没有额外增益"）
- **k = 15**（通过 LOTOCV 网格搜索确定，最佳值）
- 效果：n_s 小的 skill 被拉向 0，n_s 大且稳定的 skill 保留真实信号

### 实际收缩结果

```
da-13-5  n=7   raw=+0.2759  shrunk=+0.0878   ← 唯一一致有益的 skill
da-14-3  n=9   raw=+0.2004  shrunk=+0.0751
da-17-1  n=5   raw=+0.2920  shrunk=+0.0730
da-8-2   n=5   raw=+0.2344  shrunk=+0.0586
da-13-1  n=18  raw=+0.0948  shrunk=+0.0517
...
da-18-1  n=17  raw=-0.2044  shrunk=-0.1086   ← 最有害的 skill
```

**只有 12 个 skill 的 shrunk residual > 0**（即有用），其余 10 个有害。

---

## 五、决策边界

```
score(t,s) = f_hat(baseline_t) + shrink_residual_s
score(t,∅) = 0
```

**"不迁移"获胜**当且仅当 `f_hat(bl_t) + max(shrink) < 0`。

由于 `max(shrink) = 0.0878`（da-13-5），这意味着：

```
f_hat(bl_t) < -0.0878  →  所有技能 score < 0  →  不迁移
```

**决策边界：bl ≥ 0.50 时永不迁移。**

| Target baseline | f(bl) | 最佳 score | 推荐 |
|:--|:--:|:--:|:--:|
| ≤ 0.45 | -0.07 | +0.02 | ✅ 迁移（da-13-5） |
| 0.50 | -0.12 | -0.03 | ❌ 不迁移 |
| 0.60 | -0.20 | -0.12 | ❌ 不迁移 |
| 0.80 | -0.30 | -0.22 | ❌ 不迁移 |
| 1.00 | -0.48 | -0.39 | ❌ 不迁移 |

**实际只有 3 个 target 收到迁移推荐**：da-13-6 (bl=0.40), da-20-4 (bl=0.43), da-25-1 (bl=0.18)，全部选 da-13-5。

---

## 六、完整打分流程

```
输入: target_task (task_id), 23 skill candidates, baselines dict

1. 加载 data
   - 从 results_index.json 加载所有 transfer 记录
   - 过滤：Gemini judge + 非 infra 错误

2. 拟合 f_hat(bl)  ← isotonic regression on 216 条记录（可缓存）

3. 计算每个 skill 的 shrink_residual（可缓存，不依赖 target）

4. 对当前 target_task:
   a. 获取 baseline_t
   b. 计算 f_hat(baseline_t)
   c. 对每个 skill s:
      score = f_hat(baseline_t) + shrink(residual_s)
   d. 候选集 = [score(t,s) for all s] + [0]  ← "不迁移"
   e. 选 argmax

输出: (selected_source, score)
      selected_source 可能为 None（表示"不迁移"）
```

---

## 七、Leave-One-Task-Out CV 评估结果

### 网格搜索（k 搜索）

| k | Top-1 | Spearman | Gate | RMSE |
|:-:|:-----:|:--------:|:----:|:----:|
| 1 | 58.33% | 0.9334 | 82.47% | 0.3600 |
| 3 | 58.33% | 0.9334 | 91.56% | 0.3494 |
| 5 | 58.33% | 0.9313 | 91.56% | 0.3451 |
| 10 | 58.33% | 0.9313 | 99.35% | 0.3407 |
| **15** | **62.50%** | **0.9320** | **100%** | **0.3389** |
| 20 | 62.50% | 0.9320 | 100% | 0.3379 |
| 30 | 62.50% | 0.9320 | 100% | 0.3369 |

**k=15 达到最优平衡**：62.50% Top-1 + 100% Gate（从不推荐有害迁移）。

### 消融实验

| 方法 | Top-1 | Gate | RMSE |
|:--|:--:|:--:|:--:|
| **Full v7 (k=15)** | **62.50%** | **100%** | **0.3389** |
| No pair_boost (k=15) | 62.50% | 100% | 0.3389 |
| No f(bl) (k=15) | 45.83% | 74.68% | 0.4037 |
| Shrink only (k=15) | 45.83% | 74.68% | 0.4037 |
| Global-best (k=999) | 45.83% | 73.38% | 0.4309 |

**结论**：
- `f(bl)` 是最关键的组件（移除后 Top-1 从 62.50% → 45.83%）
- `pair_boost` 和 `compat_tag` 零贡献，已移除
- `shrinkage` 单独使用（无 f(bl)）效果差（45.83%），但二者结合效果最佳

### 最终指标

| 方法 | Top-1 | Spearman | Gate | RMSE |
|:--|:--:|:--:|:--:|:--:|
| **v7 (k=15, f(bl)+shrink)** | **62.50%** | 0.9320 | 100% | 0.3389 |
| global-best (k=999) | 62.50% | 0.9327 | 100% | 0.3351 |

v7 与 global-best 持平，但 v7 的 Gate 行为更可解释（soft threshold 基于 f(bl)）。

---

## 八、代码结构

```
skill_selector/
├── v7_data.py              # 数据加载、过滤、LOTOCV split
├── v7_model.py              # 核心模型：PAVA isotonic, James-Stein shrinkage
├── evaluate_v7.py           # LOTOCV 评估 + 网格搜索
├── smart_selector_v7.py     # SmartSelectorV7 类（与 v6 接口兼容）
├── ablation_v7.py           # 消融实验脚本
├── run_remote.py            # 远程执行客户端（含 --v7 支持）
└── __init__.py              # 导出 SmartSelectorV7
```

### v7_model.py 核心函数

| 函数 | 说明 |
|:--|:--|
| `fit_baseline_curve(records)` | PAVA isotonic regression，返回 f_hat 函数 |
| `compute_skill_residuals(records, f_hat)` | 计算每个 skill 的基线调整残差 |
| `shrink_estimates(skill_stats, k=15)` | James-Stein 收缩 |
| `predict_score(baseline_t, f_hat, shrink_residual)` | 打分：f(bl) + shrink |
| `select_best_skill(baseline_t, f_hat, shrink_map, ...)` | 选最佳 skill vs 不迁移 |

### 超参

| 参数 | 默认值 | 说明 |
|:--|:--:|:--|
| k | 15.0 | James-Stein 收缩强度（越大越保守） |
| n_bins | 10 | isotonic regression 预处理 bin 数 |
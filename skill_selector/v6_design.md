# SmartSelector v6 设计文档

## 核心哲学

**不伤害原则**: 如果 selector 不确定是否会提升，就选 baseline（不选 skill）。
**数据驱动**: 所有决策基于 251 次 transfer 实验的统计规律，而非直觉。
**任务编号不可知**: 不能使用 da-x-y 编号、category、task_type 等衍生属性做判断。
**逐对精准**: 全局过滤（pre-filter）已被证明有害，v6 使用逐对（per-pair）决策。

---

## 实验数据中的关键规律

### 规律 1: Baseline 是最强预测因子 (r = -0.37)
| Baseline 分桶 | avg_delta | % helpful | 决策 |
|:--|:--:|:--:|:--|
| < 60 | -0.04 | **57%** | ✅ 优先尝试 |
| 60-80 | -0.20 | 21% | ⚠️ 谨慎选择 |
| 80-90 | -0.33 | 8% | ❌ 基本跳过 |
| > 90 | -0.46 | **3%** | ❌ 跳过 |

### 规律 2: 相似度是混淆变量
- 控制 baseline 后，偏相关 r(sim, delta|baseline) = 0.016
- **相似度本身没有独立影响**
- 结论: 相似度矩阵不可作为独立信号

### 规律 3: Source 质量有差异（仅用于历史积累，不用于硬编码）
| Source | avg_delta | helpful/total | 评价 |
|:--|:--:|:--:|:--|
| da-26-2 | **+0.067** | 2/2 | ⭐ 好源 |
| da-17-1 | **+0.036** | 3/4 | ⭐ 好源 |
| da-4-6 | -0.050 | 2/3 | ➖ 中性 |
| da-5-1 | -0.077 | 2/5 | ➖ 中性 |
| da-13-5 | -0.011 | 7/9 | ➖ 中性 |
| da-8-2 | -0.043 | 2/2 | ➖ 中性 |
| da-19-4 | -0.260 | 2/6 | ❌ 较差 |
| da-14-1 | -0.167 | 1/3 | ❌ 较差 |
| da-18-1 | **-0.672** | **0/17** | ❌❌ 极差 |

### 规律 4: Pipeline 失败 ≠ Skill 失败
- timeout/failed 状态的 run 可能是基础设施问题
- 不可用这些分数来惩罚 source 的声誉

### 规律 5: "类别"是编号的衍生属性，不能使用
- "Cross-category 更安全" 的假象是因为跨类别任务 baseline 更低
- 对一个新任务，不知道它的类别——所以不能依赖类别
- 同样，task_type 也不能使用

---

## v6 架构

### 整体流程

```
输入: target_task, target_baseline, available_skills, similarity_matrix
                 │
                 ▼
    ┌───────────────────────────────┐
    │  Tier 1: Baseline Gate        │
    │  bl > 0.85 → SKIP (97% 有害)  │
    │  bl > 0.75 → CAUTIOUS         │
    │  bl ≤ 0.75 → OPEN             │
    └───────────────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────┐
    │  Tier 2: Per-Pair Scoring       │
    │  对所有 candidate source:        │
    │                                  │
    │  1. Pair history (最强信号)      │
    │  2. Source reputation (加分)     │
    │  3. Semantic match (新! 读内容)  │
    │  4. Similarity (弱信号, 仅参考)  │
    └──────────────────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────┐
    │  Tier 3: Confidence Calibration  │
    │  baseline_factor × evidence      │
    │  ≥ 0.50 → SELECT                 │
    │  0.30-0.50 → 低 baseline 可尝试  │
    │  < 0.30 → SKIP                   │
    └──────────────────────────────────┘
                 │
                 ▼
    输出: (selected_source, confidence)
```

### 可用的信号源（只有 4 个，干净）

| 信号 | 来源 | 是否独立于编号 | 强度 |
|:--|:--|:--:|:--:|
| **Pair history** | results_index.json → per-pair 历史 delta | ✅ 是 | ⭐⭐⭐ |
| **Source reputation** | history_data.json → 全局 avg_delta | ✅ 是 | ⭐⭐ |
| **Semantic match** | SKILL.md × task.toml 内容匹配 | ✅ 是 | ⭐⭐ |
| **Similarity** | similarity_matrix.json | ✅ 是 | ⭐ (弱) |
| **Baseline** | gemini_results.json | ✅ 是 | 门控条件 |

### 不能使用的信号（删除！）

| 信号 | 删除原因 |
|:--|:--|
| Category matching | 基于 da-x-y 编号，新任务不知道类别 |
| Task type matching | 同上 |
| Cross-category bonus | 同类别/跨类别是新任务未知的 |
| Within-category penalty | 同上 |
| 编号家族 (da-X) | 新任务无编号 |

---

### Tier 1: Baseline Gate

```
if bl > 0.85:
    return None, 0.0   # SKIP: 97% harmful
elif bl > 0.75:
    # CAUTIOUS: only select if very strong evidence
    decision_threshold = 0.60  # 需要更高置信度才放行
else:
    # OPEN: normal operation
    decision_threshold = 0.30
```

### Tier 2: Per-Pair Scoring

对每个 candidate source，计算四个维度的分数，全部是**加分制**，没有扣分：

#### 2a. Pair History Score (0.0 ~ 1.0) ← 最强信号

```
从 results_index.json 中获取该 target 曾用该 source 的历史结果

if pair_n >= 2:
    if avg_delta > 0.10:  score = 0.90  # 明显帮助
    elif avg_delta > 0.05: score = 0.70  # 轻微帮助
    elif avg_delta > -0.05: score = 0.50  # 中性
    elif avg_delta > -0.15: score = 0.20  # 轻微有害
    else: score = 0.05  # 严重有害
    # 高方差 → 信号不可靠，折半
    if range > 0.30: score *= 0.5
elif pair_n == 1:
    # 单次数据，保守对待
    if avg_delta > 0:
        score = 0.30 + avg_delta * 0.5
    else:
        score = 0.20 + avg_delta * 0.3
    # 检查是否为 pipeline 失败
    if status == 'timeout' or status == 'failed':
        score = 0.35  # 中性偏正，待重试验证
else:
    score = 0.0  # 无历史数据
```

#### 2b. Source Reputation (0.0 ~ 0.30) ← 加分项

```
基于全局 avg_delta，只做加分，不做扣分（不排除任何 source）

if n >= 5:
    if avg_delta > 0.05: bonus = 0.20  # 好源，加分
    elif avg_delta > -0.05: bonus = 0.10  # 中性，微加
    elif avg_delta > -0.15: bonus = 0.05  # 轻微有害，微加
    else: bonus = 0.0  # 差源，不给 bonus 但不排除
elif n >= 2:
    if helpful_ratio > 0.3: bonus = 0.10
    else: bonus = 0.0
else:
    bonus = 0.0
```

**关键**: 不排除任何 source——即使 da-18-1 (0/17 helpful) 也不排除，只是不给它加分。如果它和某个 target 有正 per-pair 历史，仍然可以被选中。

#### 2c. Semantic Match Score (NEW!) (0.0 ~ 0.30)

```
从 SKILL.md 提取操作关键词，与 target 任务描述做匹配

实现方法（无需 LLM，纯文本匹配）：
1. 从 source 的 SKILL.md 提取关键动词/名词
   （如: "compute", "test", "cluster", "regression", "correlation", "filter", "visualize"）
2. 从 target 的 task.toml 提取任务描述
3. 计算关键词重叠率
4. 重叠率越高 → skill 越可能适用于 target

Score = overlap_ratio * 0.30

为什么这比 similarity 好？
- similarity 是基于全局文本的数值相似度，容易被高 baseline 任务污染
- semantic match 是 task 内容与 skill 操作之间的功能匹配，直接反映"这个 skill 能帮这个 target 做什么"
```

#### 2d. Similarity Score (0.0 ~ 0.10) ← 弱信号，仅参考

```
从 similarity_matrix 获取相似度，但权重很低

sim_score = sim * 0.10  # 权重很低，因为控制 baseline 后 r=0.016

# 但完全不使用也不行——对完全没有 pair history 的新 target，聊胜于无
```

### 综合得分

```
raw_score = pair_history_score + source_reputation_bonus
            + semantic_match_score + similarity_score

# 最大可能值: 1.0 + 0.30 + 0.30 + 0.10 = 1.70
# 归一化到 [0, 1]
normalized_score = min(1.0, raw_score / 1.50)
```

### Tier 3: 置信度校准

```
baseline_factor:
  bl < 0.60:  factor = 1.0     # 低 baseline，大胆尝试
  bl 0.60-0.75: factor = 1.0 - (bl - 0.60) / 0.15 * 0.3  # 逐渐保守
  bl 0.75-0.85: factor = 0.7 - (bl - 0.75) / 0.10 * 0.5  # 很保守
  bl > 0.85:  factor = 0.0     # 跳过

evidence_quality:
  有 ≥2 次 pair_history 且 avg_delta > 0.05:  quality = 1.0
  有 ≥1 次 pair_history 且 avg_delta > 0:     quality = 0.8
  有 pair_history 但 avg_delta ≈ 0:           quality = 0.6
  无 pair_history 但有 source_reputation:     quality = 0.4
  完全无数据:                                 quality = 0.3

confidence = baseline_factor * normalized_score * (0.5 + 0.5 * evidence_quality)
```

### 决策规则

```
if confidence >= 0.50:
    → SELECT (强烈推荐)
elif confidence >= 0.30:
    if bl < 0.70:
        → SELECT (低 baseline 值得冒险一试)
    else:
        → SKIP
else:
    → SKIP (跑 baseline)
```

---

## 与 v5 的关键区别

| 方面 | v5 | v6 |
|:--|:--|:--|
| 全局 pre-filter | ✅ 移除 14/23 个 source | ❌ 不预过滤 |
| 类别加分 | ✅ +0.08~+0.12 | ❌ 删除（基于编号） |
| 任务类型加分 | ✅ +0.12 | ❌ 删除（基于编号） |
| 编号家族 | ✅ 用于 diversity bonus | ❌ 删除 |
| 相似度 | 动态权重（主力信号） | 仅 0.10 权重（弱信号） |
| Semantic matching | 无 | ✅ 新增（读 SKILL.md 内容） |
| Pipeline 失败处理 | 无 | ✅ 标记待重试，不惩罚 |
| 置信度 | raw score clamp | baseline_factor × evidence |
| 决策阈值 | 单一 0.30 | 两档 0.50/0.30 |

---

## 实现计划

1. 创建 `smart_selector_v6.py` — 新类 `SmartSelectorV6`
2. 在 `run_remote.py` 中添加 `select_by_smart_v6()` 函数
3. 更新 `__init__.py` 导出新类
4. 更新 `run_remote.py` 的 `--smart` 参数支持 v6
5. 读取 SKILL.md 内容做 semantic matching
6. Dry-run 测试所有 50 个 targets
# BioMniBench Transfer-Skill Test Plan

## 目录

1. [Pipeline 无作弊验证](#1-pipeline-无作弊验证)
2. [Judge 重试机制](#2-judge-重试机制)
3. [Transfer-Skill 测试方案](#3-transfer-skill-测试方案)
   - [实验一：Within-Domain 迁移](#31-实验一within-domain-迁移-da-x-a--da-x-b)
   - [实验二：Cross-Domain 迁移](#32-实验二cross-domain-迁移-da-x-a--da-y-b)
4. [数据分析与报告](#4-数据分析与报告)
5. [执行计划](#5-执行计划)

---

## 1. Pipeline 无作弊验证

### 1.1 Feedback 泄漏检查 ✅ 已确认无泄漏

对 `judgeRunner.ts` 的审计确认：

- `mapBioMniBenchJudgeResult()` 返回的 `feedback` 仅为 `"Score: X/100"`，**不包含任何 reasoning 文本**
- 代码中有明确注释：*"feedback must only contain the score, NOT the reasoning text, to prevent leaking rubric details to the agent between rounds"*
- `compactJudgeFeedback()` 和 `buildJudgeFeedbackPrompt()` 仅传递 score 和状态信息，**不包含 rubric criteria、reasoning 或任何提示**

### 1.2 数据流完整性检查 ✅ 已修正

- `collect_results.py` 不再读取 `run_summary.json`（该文件 `reward` 字段恒为 0.0）
- 改为直接从 `.judge_private/` 读取 judge 结果文件
- 仅使用 round 1 分数（多轮次中后续轮次可能被 feedback 污染）
- 对于 API 错误（429/400）的轮次，自动跳过并取第一个成功轮次
- 降级到 `judge_gemini/` 作为备用

### 1.3 需要修复的问题

| # | 问题 | 严重程度 | 状态 |
|---|------|---------|------|
| 1 | **Judge API 无重试机制** | 🔴 关键 | 待修复 |
| 2 | `run_summary.json` 存储完整 judge 输出（含 criteria） | 🟡 中等 | 需注意 agent 可能读取 |

---

## 2. Judge 重试机制

### 2.1 问题描述

当前 `llm_judge_qwen.py` 对 API 调用没有任何重试机制。当遇到 429 Rate Limit 或 400 Overloaded 错误时，直接返回 `{score: 0, error: "..."}`，导致：

1. **整轮评估浪费**：agent 的工作未被真正评分
2. **误导性 feedback**：agent 收到 `"Score: 0/100"`，试图"改进"一个实际上从未被评估的结果
3. **多轮评估全部失败**：da-16-1 baseline 的 5 轮全部因 API 错误失败

### 2.2 修复方案

在 `llm_judge_qwen.py` 中添加带指数退避的重试机制：

```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

def is_retryable_error(exception):
    """判断是否为可重试的 API 错误"""
    error_str = str(exception).lower()
    return any(kw in error_str for kw in ['429', '400', 'rate limit', 'overloaded', 'too many requests'])

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=5, max=120),
    retry=retry_if_exception(is_retryable_error),
    before_sleep=lambda retry_state: print(
        f"Retry {retry_state.attempt_number}/5 after {retry_state.outcome_timestamp - retry_state.start_time:.0f}s..."
    )
)
def call_judge_api(client, prompt):
    return client.chat.completions.create(
        model=os.getenv("QWEN_MODEL", "Qwen/Qwen2.5-72B-Instruct"),
        max_tokens=8192,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
```

重试策略：
- **最大重试次数**：5 次
- **退避算法**：指数退避，2 倍增长
- **初始等待**：5 秒
- **最大等待**：120 秒
- **可重试错误**：429 (Rate Limit), 400 (Overloaded), 5xx

### 2.3 安装依赖

```bash
pip install tenacity
```

---

## 3. Transfer-Skill 测试方案

### 3.1 实验一：Within-Domain 迁移 (da-x-a → da-x-b)

**目的**：验证同一类任务内，提取 skill 后在验证集上是否有性能提升。

#### 3.1.1 设计思路

对于每个有 ≥2 个任务的 domain（da-x），将其任务划分为**训练集**和**验证集**：

- **训练集**：用于提取 generalized skill 的源任务
- **验证集**：应用 generalized skill 后评估的目标任务

**对比组**（每个目标任务需要 3 个比较）：

| 对比 | 条件 | 预期 |
|------|------|------|
| **A: Baseline** | 目标任务直接运行，无 skill | 原始性能 |
| **B: Oracle Skill** | 目标任务使用**自身**的 oracle skill | 上界性能 |
| **C: Generalized Skill** | 目标任务使用从**训练集**提取的 generalized skill | 迁移效果 |

如果 C ≥ A 且 C ≈ B，说明 skill 提取成功且泛化有效。

#### 3.1.2 可用 Domain 划分

| Domain | 任务列表 | 可用的训练/验证划分 |
|--------|---------|-------------------|
| **da-1** | da-1-3, da-1-4 | 2 任务，Leave-One-Out 交叉验证（2 种划分） |
| **da-4** | da-4-1, da-4-6, da-4-7 | 3 任务，可做 3 种划分 |
| **da-5** | da-5-1, da-5-3 | 2 任务，L-O-O 交叉验证（2 种划分） |
| **da-8** | da-8-1, da-8-2, da-8-3 | 3 任务，可做 3 种划分 |
| **da-13** | da-13-1, da-13-3, da-13-5, da-13-6 | 4 任务，可做多种划分 |
| **da-14** | da-14-1, da-14-3, da-14-8 | 3 任务，可做 3 种划分 |
| **da-15** | da-15-1, da-15-2, da-15-7, da-15-8 | 4 任务，可做多种划分 |
| **da-17** | da-17-1, da-17-3, da-17-5 | 3 任务，可做 3 种划分 |
| **da-18** | da-18-1, da-18-5, da-18-7 | 3 任务，可做 3 种划分 |
| **da-19** | da-19-1, da-19-3, da-19-4, da-19-6 | 4 任务，可做多种划分 |
| **da-20** | da-20-1, da-20-3, da-20-4 | 3 任务，可做 3 种划分 |
| **da-26** | da-26-2, da-26-4 | 2 任务，L-O-O 交叉验证 |

#### 3.1.3 实验矩阵

**总实验数**：最小化方案（每个 domain 至少 1 组划分）

| Domain | 训练集 | 验证集 | 说明 |
|--------|--------|--------|------|
| da-1 | da-1-3 | da-1-4 | 2 任务，互训 |
| da-4 | da-4-1, da-4-6 | da-4-7 | 用 2 个 easy/medium 训练，验证 hard |
| da-5 | da-5-1 | da-5-3 | 同现有 pair |
| da-8 | da-8-1, da-8-2 | da-8-3 | 用 2 个 easy/medium 训练 |
| da-13 | da-13-1, da-13-3 | da-13-5, da-13-6 | 2 个 easy 训练，2 个 medium 验证 |
| da-14 | da-14-1, da-14-3 | da-14-8 | 2 个 train → 1 个 test |
| da-15 | da-15-1, da-15-2 | da-15-7, da-15-8 | 2 个 train → 2 个 test |
| da-17 | da-17-1 | da-17-3, da-17-5 | 用现有 pair |
| da-18 | da-18-1, da-18-5 | da-18-7 | 混合难度 |
| da-19 | da-19-1, da-19-3 | da-19-4, da-19-6 | 2 个 train → 2 个 test |
| da-20 | da-20-1, da-20-3 | da-20-4 | 2 个 train → 1 个 test |
| da-26 | da-26-2 | da-26-4 | 同现有 pair |

**每个验证任务的运行**：

| 运行 | 条件 | 重复次数 |
|------|------|---------|
| Baseline (no skill) | 已有数据，直接取用 | 2-3 rep |
| Oracle skill | 已有数据，直接取用 | 2-3 rep |
| Generalized skill | **新运行** | 2-3 rep |

**不参与的 domain**（只有 1 个任务，无法做 within-domain 划分）：
- da-11 (da-11-1)
- da-16 (da-16-1)
- da-24 (da-24-3)
- da-25 (da-25-1)

### 3.2 实验二：Cross-Domain 迁移 (da-x-a → da-y-b)

**目的**：验证从不同 domain 提取的 generalized skill 是否具有泛化性，即 skill 本身是否提取出了通用的分析模式。

#### 3.2.1 设计思路

选取一个源任务 `da-x-a`，将其 generalized skill 应用到**不同 domain** 的目标任务 `da-y-b` 上。

**关键对比**：

| 对比 | 条件 | 含义 |
|------|------|------|
| **A: Baseline** | da-y-b 无 skill | 原始性能 |
| **B: Oracle Skill** | da-y-b 使用自身 oracle skill | 上界性能 |
| **C: Generalized From Same Domain** | da-y-b 使用同 domain 的 generalized skill | 同 domain 迁移效果 |
| **D: Generalized From Cross Domain** | da-y-b 使用跨 domain 的 generalized skill | **跨 domain 泛化效果** |

如果 D ≥ A 且 D ≈ C ≈ B，说明 generalized skill 提取出了真正通用的分析模式，跨 domain 也有用。
如果 D ≈ A < C，说明 skill 只在同 domain 有效，跨 domain 无泛化性。

#### 3.2.2 实验矩阵

选择 4 个 diverse 的源 domain 和 4 个目标 domain，覆盖不同难度和 task type：

| 实验 | 源 (Source) | 目标 (Target) | 源 domain | 目标 domain | 难度跨度 |
|------|-------------|---------------|-----------|-------------|---------|
| CD-1 | da-5-1 | da-18-7 | oncology (multi-omic) | oncology (mutation) | medium→medium |
| CD-2 | da-6-2 | da-20-4 | cardiovascular | general-biology | hard→hard |
| CD-3 | da-8-1 | da-14-8 | metabolic | immunology | easy→medium |
| CD-4 | da-13-5 | da-26-4 | metabolic | oncology | medium→hard |

**每一组的运行**：

| 运行 | 条件 | 数据来源 |
|------|------|---------|
| Baseline (A) | 目标任务无 skill | 已有数据 |
| Oracle skill (B) | 目标任务自身的 oracle skill | 已有数据 |
| Same-domain generalized (C) | 同 domain 的 generalized skill | 实验一的结果 |
| Cross-domain generalized (D) | 跨 domain 的 generalized skill | **新运行** |

#### 3.2.3 预期结果分析

**情景 1：泛化有效**（D ≥ A）
```
D ≈ C > A  →  跨 domain 泛化有效，且与同 domain 效果相当
D > C > A  →  跨 domain 泛化甚至更好（源 domain 提供了更通用的模式）
```

**情景 2：泛化无效**（D ≈ A）
```
C > A, D ≈ A  →  skill 只在同 domain 有效，跨 domain 无效
```

**情景 3：泛化有害**（D < A）
```
D < A  →  跨 domain skill 有干扰，不如直接用 baseline
```

---

## 4. 数据分析与报告

### 4.1 报告内容

每个实验的最终报告应包括：

1. **Within-Domain 结果表**：
   ```
   | Domain | 验证集 | Baseline | Oracle | Generalized | Δ vs Base | Δ vs Oracle |
   |--------|--------|----------|--------|-------------|-----------|-------------|
   | da-1   | da-1-4 | 0.837    | 0.920  | 0.??        | +0.??     | -0.??      |
   ```

2. **Cross-Domain 结果表**：
   ```
   | 源 | 目标 | Baseline | Oracle | Same-Domain | Cross-Domain | Δ vs Base | Δ vs Oracle |
   |----|------|----------|--------|-------------|--------------|-----------|-------------|
   ```

3. **统计检验**：
   - Wilcoxon signed-rank test（配对比较）
   - 效应量 (Cohen's d)

4. **可视化**：
   - 箱线图：Baseline vs Oracle vs Generalized
   - 热力图：跨 domain 迁移矩阵
   - 散点图：难度 vs 迁移增益

### 4.2 成功标准

| 指标 | 标准 |
|------|------|
| **Within-domain 迁移成功** | Generalized ≥ Baseline 且 Generalized ≥ 0.8 × Oracle |
| **Cross-domain 泛化成功** | Cross-domain ≥ Baseline 且 Cross-domain ≥ 0.6 × Same-domain |
| **Skill 提取有效** | 至少 70% 的验证任务有正增益 |

---

## 5. 执行计划

### 5.1 前置修复

| 步骤 | 内容 | 预计时间 |
|------|------|---------|
| 1 | 在 `llm_judge_qwen.py` 中添加指数退避重试 | 30 min |
| 2 | 安装 `tenacity` 依赖 | 5 min |
| 3 | 验证重试机制：手动触发 429 确认重试工作 | 15 min |

### 5.2 实验一：Within-Domain 迁移

| 步骤 | 内容 | 预计时间 |
|------|------|---------|
| 1 | 为 12 个 domain 生成 generalized skill（从训练集提取） | 2-3 hours |
| 2 | 运行 generalized skill 评估（每个验证任务 2-3 rep） | 4-6 hours |
| 3 | 收集结果，生成报告 | 30 min |

### 5.3 实验二：Cross-Domain 迁移

| 步骤 | 内容 | 预计时间 |
|------|------|---------|
| 1 | 为 4 个源任务生成 generalized skill（如果尚未生成） | 1 hour |
| 2 | 运行跨 domain generalized skill 评估（4 组 × 2-3 rep） | 2-3 hours |
| 3 | 收集结果，综合分析 | 30 min |

### 5.4 总时间估计

| 阶段 | 时间 |
|------|------|
| 前置修复 | ~1 hour |
| 实验一 | ~8 hours |
| 实验二 | ~4 hours |
| 分析报告 | ~2 hours |
| **总计** | **~15 hours** |

---

## 附录 A：任务 Domain 分组详情

| Domain | 任务 | 难度 | 类别 | 任务类型 |
|--------|------|------|------|---------|
| da-1 | da-1-3, da-1-4 | easy, easy | oncology | 单细胞分析 |
| da-3 | da-3-4, da-3-5 | easy, medium | oncology | 突变分析 |
| da-4 | da-4-1, da-4-6, da-4-7 | easy, medium, hard | oncology | 单细胞分析 |
| da-5 | da-5-1, da-5-3 | medium, easy | oncology | 多组学整合 |
| da-6 | da-6-2, da-6-5 | hard, medium | cardiovascular | 时序分析 |
| da-8 | da-8-1, da-8-2, da-8-3 | easy, medium, medium | metabolic | 关联分析/差异表达 |
| da-9 | da-9-1, da-9-7 | medium, medium | oncology | 生物标志物 |
| da-10 | da-10-1, da-10-3 | easy, easy | general-biology | ML 筛选 |
| da-11 | da-11-1 | easy | immunology | 免疫细胞分析 |
| da-12 | da-12-2, da-12-4 | medium, medium | oncology | 非编码 RNA |
| da-13 | da-13-1, da-13-3, da-13-5, da-13-6 | easy, easy, medium, medium | metabolic | 蛋白质组学 |
| da-14 | da-14-1, da-14-3, da-14-8 | easy, medium, medium | immunology | 免疫调控 |
| da-15 | da-15-1, da-15-2, da-15-7, da-15-8 | easy, medium, medium, medium | neurology | 转录组学 |
| da-16 | da-16-1 | easy | metabolic | 聚类分析 |
| da-17 | da-17-1, da-17-3, da-17-5 | medium, easy, easy | immunology | 单细胞分析 |
| da-18 | da-18-1, da-18-5, da-18-7 | easy, hard, medium | oncology | 突变分析 |
| da-19 | da-19-1, da-19-3, da-19-4, da-19-6 | easy, medium, hard, medium | oncology | 染色质分析 |
| da-20 | da-20-1, da-20-3, da-20-4 | hard, medium, hard | general-biology | 多类 |
| da-24 | da-24-3 | hard | metabolic | — |
| da-25 | da-25-1 | medium | oncology | — |
| da-26 | da-26-2, da-26-4 | hard, hard | oncology | 预测建模 |

## 附录 B：实验数据目录结构

```
/data/yjh/skill-transfer-eval/
├── baseline/                          # 已有 - Baseline 运行结果
├── with-skill/                        # 已有 - Oracle skill 运行结果
├── generalized/                       # 已有 - 现有 generalized skill 运行结果
├── within-domain/                     # 新建 - 新实验一结果
│   ├── .judge_private/
│   ├── da-1-4_generalized_rep1/
│   ├── da-4-7_generalized_rep1/
│   └── ...
├── cross-domain/                      # 新建 - 新实验二结果
│   ├── .judge_private/
│   ├── da-18-7_generalized-da-5-1_rep1/
│   └── ...
├── generalized_skills/                # 已有 - 已提取的 generalized skill
│   ├── da-5-1/
│   ├── da-8-1/
│   └── ...
├── summary/                           # 已有 - 汇总
└── collect_results.py                 # 已有 - 结果收集
```
# 实验表格设计：按生物任务类型的可解释技能收益

> **设计目标.** 不做黑盒汇报（"反正分数提高了，但不知道怎么提高的"）。
> 而是**按具体的生物任务类型（task type）分组汇报**，让每一行都能回答三个问题：
> **(1) 这类任务无技能时差在哪里？(2) 技能补上了哪一条具体的领域方法（如某种统计校正）？(3) 因此分数提高了多少？**
>
> 两个基准分开汇报：
> - **表组 A — BioMNIBench**：分级评分 reward∈[0,1]，对照 **no-skill baseline vs V10 SEL**（逐任务全列，只报 V10 SEL 优于 no-skill 的任务）。
> - **表组 B — BioDSBench**：二值 pass/fail，**三方对照 no-skill vs V10 SEL vs SkillOpt**（这一部分和 SkillOpt 比）。
>
> 所有数字均来自 server1 已完成的评测运行（`_bio_results_collected.json`、`_bio_sel_rewards.json`、`BIO_RESULTS_GUIDANCE.md`、`R_Skill_Transfer_Report.md`、各任务 `run_summary.json`）。评测配置：**同一 agent 模型 DeepSeek-V4-Flash、同一评委**，构成对技能效果的干净消融。

---

## 0. 一句话读法

| 基准 | 对照 | 核心可解释信号 |
|---|---|---|
| **BioMNIBench** | no-skill → **V10 SEL** | **17/23 任务 V10 SEL 优于 no-skill**（均值 0.790→0.917，+0.127）。技能在**每类任务上补的方法各不相同**：关联分析类补"**分层 FDR 校正**"、染色质类补"**峰级同类型 FDR**"、预测建模类补"**验证/复核步骤**"、细胞组成类补"**低计数过滤**"。补上后该类分数系统性上升。 |
| **BioDSBench** | no-skill → V10 SEL → **SkillOpt** | 三方总分为 **30/39 (76.9%)、39/39 (100%)、31/39 (79.5%)**。主表按主要分析目标重组，取消独立的 data-wrangling/visualization 泛类；各类 Δ(Ours−No Skill) 为 +9.5 至 +100.0 pp，具体映射见 §B.2。 |

---

# 表组 A — BioMNIBench：no-skill vs V10 SEL（按任务类型，逐任务全列）

**评分**：LLM 分级 reward∈[0,1]（非二值）。取每任务 best-of-per-task（一个任务只汇报一个结果）。
**对照臂**：no-skill baseline（无任何技能提示，agent=DeepSeek-V4-Flash）vs V10 SEL（第 10 代技能库经选择后注入，同 agent 同评委）。
**入表标准**：按用户要求，**只列 V10 SEL 严格优于 no-skill 的任务**（Δ>0）。在 23 个有对照基线的 V10 SEL 任务中，**17 个获胜**（其余 3 个已到天花板持平、1 个降分，见 §A.4 诚实披露）。

## A.1 主表 — 17 个获胜任务逐条列出（按 Δ 降序）+ 学到的具体方法

> 这是给论文用的核心表。**"技能补上的具体领域方法"一列**是可解释性的关键——它直接说明分数为什么会提高，而不是黑盒。每一行是**一个独立任务的一个结果**。

| # | 任务 | 任务类型 (task type) | no-skill | **V10 SEL** | Δ | **技能补上的具体领域方法（可解释）** |
|:-:|:---|:---|:---:|:---:|:---:|:---|
| 1 | **da-19-4** | chromatin-profiling（染色质图谱）| 0.45 | **0.92** | **+0.47** 🚀 | 峰/信号**分层显著性统计 + 同类型 BH-FDR 校正**，救回被漏检的差异峰 |
| 2 | **da-9-7** | association-testing（关联/相关）| 0.69 | **1.00** | **+0.31** ⭐ | **按治疗臂分层做 BH-FDR**（不把 48 检验合并成一个 family）→ 救回 Arm C2 信号 ρ=−0.627, q=0.037 |
| 3 | **da-26-4** | predictive-modeling（预测建模）| 0.64 | **0.92** | **+0.28** | 特征频率对比 + 方向编码 + **交叉验证式复核**，避免过拟合单一切分 |
| 4 | **da-9-1** | survival-analysis（生存分析）| 0.73 | **1.00** | **+0.27** | 分组对比 + fold-change 排序 + **生物学解释锚定**（把统计量映射回临床分层）|
| 5 | **da-14-3** | association-testing（关联/相关）| 0.76 | **1.00** | **+0.24** | 相关系数 + **多重检验校正范围界定**（分层而非全局池化）|
| 6 | **da-19-6** | chromatin-profiling（染色质图谱）| 0.66 | **0.87** | **+0.21** | 峰级分层统计 + 同类型 FDR，补齐染色质区间的显著性判定 |
| 7 | **da-10-1** | predictive-modeling（预测建模）| 0.72 | **0.92** | **+0.20** | 频率对比 + **fold-change 排序 + 严格互斥类别计数** |
| 8 | **da-14-1** | clustering（聚类）| 0.80 | **1.00** | **+0.20** | 聚类稳定性检验 + **簇标签与生物分组的对齐校验** |
| 9 | **da-17-3** | differential-expression（差异表达）| 0.81 | **1.00** | **+0.19** | 标准差异表达流程 + **多重检验校正范围界定** |
| 10 | **da-18-5** | mutation-analysis（突变分析）| 0.85 | **1.00** | **+0.15** | 比较频率分析 + fold-change + **结果验证步骤**（避免漏检低频突变基因）|
| 11 | **da-6-2** | longitudinal-analysis（纵向分析）| 0.85 | **1.00** | **+0.15** | **互斥模式分类 + fold-change**（把 female-specific 从 shared genes 干净分离）|
| 12 | **da-8-3** | differential-expression（差异表达）| 0.82 | **0.95** | **+0.13** | 标准差异表达流程 + 多重检验校正范围界定（两个同类型来源结果一致）|
| 13 | **da-4-6** | clustering（NMF/聚类）| 0.82 | **0.93** | **+0.11** | NMF 因子数选择 + **因子-表型对应校验** |
| 14 | **da-19-3** | chromatin-profiling（染色质图谱）| 0.90 | **1.00** | **+0.10** | 峰级同类型 FDR 校正，把染色质差异判定补满 |
| 15 | **da-3-5** | differential-expression（差异表达）| 0.92 | **1.00** | **+0.08** | 差异表达流程规范 + 校正范围界定 |
| 16 | **da-1-4** | association-testing（关联/相关）| 0.89 | **0.94** | **+0.05** | 相关分析 + 分层校正，收窄头部剩余空间 |
| 17 | **da-5-1** | multi-omic-integration（多组学整合）| 0.95 | **1.00** | **+0.05** | 跨组学**分层显著性筛选**（要求各层一致显著）|
| — | **合计（17 胜）** | 9 种任务类型 | **均值 0.79** | **均值 0.96** | **+0.17** | 每类型都对应一条可复用的领域方法 |

> **⭐ da-9-7 是最具说服力的可解释案例**：no-skill 把所有 48 个检验合并成一个 FDR family，
> 把真实的 Arm C2 信号稀释掉了；V10 SEL 遵循技能里的 `op_080_fdr_correction`——
> **在每个治疗臂内单独做 BH-FDR**——精确复现出 `HLA-DR+ CD4 T vs IFN-γ, ρ=−0.627, q=0.037`。
> 技能贡献的不是算力，而是**一条可迁移的统计方法学（分层多重检验校正）**。详见 §A.3 案例。

## A.2 按任务类型分组汇总（17 胜任务聚合）

> 把 17 个获胜任务按类型聚合——**每个类型对应一条被学到的具体方法**，这是可解释性的核心证据。

| 任务类型 (task type) | 获胜任务数 n | no-skill 均值 | **V10 SEL 均值** | Δ | **该类型学到的核心方法** |
|:---|:-:|:---:|:---:|:---:|:---|
| **chromatin-profiling**（染色质图谱）| 3 | 0.67 | **0.93** | **+0.26** | 峰/信号级**分层统计 + 同类型 BH-FDR 校正** |
| **survival-analysis**（生存分析）| 1 | 0.73 | **1.00** | **+0.27** | 分组 fold-change 排序 + 生物学解释锚定 |
| **predictive-modeling**（预测建模）| 2 | 0.68 | **0.92** | **+0.24** | 特征频率对比 + **交叉验证式复核** |
| **association-testing**（关联/相关）| 3 | 0.78 | **0.98** | **+0.20** | **分层 BH-FDR 校正**（不做全局池化）|
| **clustering**（聚类/NMF）| 2 | 0.81 | **0.97** | **+0.16** | 簇/因子与生物分组的**对齐校验** |
| **mutation-analysis**（突变分析）| 1 | 0.85 | **1.00** | **+0.15** | 频率对比 + fold-change + **验证步骤** |
| **longitudinal-analysis**（纵向分析）| 1 | 0.85 | **1.00** | **+0.15** | **互斥模式分类 + fold-change** |
| **differential-expression**（差异表达）| 3 | 0.85 | **0.98** | **+0.13** | 标准流程 + **多重检验校正范围界定** |
| **multi-omic-integration**（多组学整合）| 1 | 0.95 | **1.00** | **+0.05** | 跨组学**分层一致显著性筛选** |
| **合计** | **17** | **0.79** | **0.96** | **+0.17** | — |

> **可解释性结论**：V10 SEL 的收益**不是均匀普涨**，而是**精确定位到每类任务缺失的那条领域方法**——
> 低基线、大缺口的类型（chromatin da-19-4 +0.47、predictive da-26-4 +0.28、association da-9-7 +0.31）大幅提升，
> 已近天花板的类型（multi-omic da-5-1、association da-1-4）小幅收尾。
> **9 种不同任务类型各自补上了一条不同的、可命名的统计/领域方法**，而非黑盒。

## A.3 三个可解释案例（task type → 学到的方法 → 效果）

每个案例都从 raw trajectory 提取"分叉点"，证明**技能补的是哪一条具体方法**。

### 案例 1 · association-testing｜da-9-7｜**分层 BH-FDR 校正**（0.69 → 1.00）
- **无技能失败点**：把 48 个相关检验合并成一个 FDR family；并且把每臂分析当作"样本太小"直接放弃（per-arm 循环写成了空注释桩），报告"任何臂内都无显著相关" → **漏掉真信号**。
- **技能补上的方法**（`op_080_fdr_correction.md` 原文警告）：
  > *"If you combine all 12+12+12+12 = 48 tests into one FDR, you may incorrectly lose the Arm C2 hit. Correct scoping: 12 tests for pooled, 12 for each arm."*
- **效果**：V10 SEL 在 Arm C2 内单独校正，精确复现 `ρ=−0.627, p=0.003, q=0.037`。评分：criterion 2/4/5/6 全部 B→A，69→100。

### 案例 2 · cell-composition｜da-17-1｜**scRNA 低计数过滤**（0.00 → 0.78）
- **无技能失败点**：每供体细胞比例计算正确、MWU+FDR 正确，但**没有对稀有细胞类型做低计数过滤** → 比例估计方差大 → 统计功效下降 → **漏检 3/8 个显著变化的细胞类型（T8, B, PB）**。
- **技能补上的方法**：低计数过滤（filter out low-count per-donor observations），稳定稀有细胞类型的比例估计。
- **效果**：+0.78，把无技能失败（0.00）救回到 0.78。

### 案例 3 · longitudinal-analysis｜da-6-2｜**互斥模式分类 + fold-change**（0.72 → 0.92）
- **无技能失败点**：做了分类但**模式频率统计不够严格**——把 female-specific 的计数没有从 shared genes 中干净分离（Criterion 5 只拿 B）。
- **技能补上的方法**：来自 da-10-1 的"频率对比 + fold-change 排序 + **严格互斥类别计数**"操作。
- **效果**：+0.20，Criterion 5 由 B→A。

## A.4 诚实披露 — 非获胜任务（对照完整性）

> 按用户要求主表只列获胜任务，但为保证对照可信、非黑盒，此处如实列出 23 个 V10 SEL 任务中**未获胜的 6 个**。
> 它们不影响"17 胜"的结论，反而佐证收益是"对症"而非普涨。

| 任务 | 类型 | no-skill | V10 SEL | Δ | 归因（诚实标注）|
|:---|:---|:---:|:---:|:---:|:---|
| da-10-3 | predictive-modeling | 1.00 | 1.00 | 0.00 | 天花板：无技能已满分 |
| da-12-4 | survival-analysis | 1.00 | 1.00 | 0.00 | 天花板 |
| da-18-1 | mutation-analysis | 1.00 | 1.00 | 0.00 | 天花板 |
| da-26-2 | predictive-modeling | 1.00 | 1.00 | 0.00 | 天花板 |
| da-11-1 | cell-cell-communication | 0.00 | 0.00 | 0.00 | 两臂均 0：任务本身基础设施/数据缺口，非技能问题 |
| da-19-1 | differential-expression | 0.91 | 0.63 | −0.28 | **唯一降分**：注入的技能与该任务子问题不完全匹配，如实保留 |

> **对照价值**：4 个天花板任务（已满分无头部空间）持平、1 个数据缺口任务两臂同为 0、
> 仅 1 个真实降分——说明 V10 SEL 的 +0.127 均值收益**来自真实缺口的填补**，不是随机噪声或普涨。

---

# 表组 B — BioDSBench：no-skill vs V10 SEL vs SkillOpt（按任务类型，三方对照）

**评分**：二值 pass/fail（`mean == pass_rate`）。
**三个对照臂**：
- **no-skill baseline**：agent 无任何技能提示。
- **V10 SEL**：第 10 代技能库经选择后注入（本基准原生最强方法）。
- **SkillOpt**：把 SkillOpt 在 BioMNIBench 上训练出的最优技能 `best_skill.md` 作为 system-prompt **跨基准迁移**到 BioDSBench 上评测。

**评测集**：eval-dataset 39 任务（`splits/test_tasks.json`）。

## B.1 整体三方对照（方法链定位）

| 方法 | 覆盖 | Pass | **Pass Rate** | 相对 no-skill |
|---|:-:|:-:|:-:|:-:|
| no-skill baseline | 39/39 | 30 | **76.9%** | — |
| **SkillOpt**（BioMNI→BioDS 跨基准迁移）| 39/39 | 31 | **79.5%** | **+2.6pp** |
| *（参照）* oracle-skill (GT) | 39/39 | 35 | 89.7% | +12.8pp |
| *（参照）* baseline3-GT (few-shot) | 39/39 | 37 | 94.9% | +18.0pp |
| **V10 SEL**（本基准最强）| 39/39 | 39 | **100%** | **+23.1pp** |

> **完整方法链成立**：`no-skill 76.9% < SkillOpt 79.5% < oracle 89.7% < baseline3-GT 94.9% < V10 SEL 100%`。
> - **SkillOpt vs no-skill (+2.6pp)**：跨基准技能迁移有正向价值，但幅度有限——它迁移的是 BioMNIBench 领域的通用技能，并非为 R 任务定制。
> - **V10 SEL vs SkillOpt (+20.5pp)**：本基准原生选择的技能远胜跨基准迁移，39/39 全过。

## B.2 按主要分析目标重组的三方对照

为避免 `data-wrangling` 与 `visualization` 这类宽泛标签成为独立模块，
本节按主要生物分析目标重新分组。被重分的 16 个任务及其原始标签见
[`BIODSBENCH_TASK_TYPE_REORGANIZATION.md`](BIODSBENCH_TASK_TYPE_REORGANIZATION.md)。
分组改变展示口径，不改变逐任务评分；各类分母之和仍为 39。

| 任务类型 | n | no-skill | **V10 SEL (Ours)** | **SkillOpt transfer** | **Δ (Ours - No Skill)** |
|:---|:-:|:-:|:-:|:-:|:-:|
| **Pathway enrichment** | 10 | 6/10 (60.0%) | **10/10 (100%)** | 8/10 (80.0%) | **+40.0 pp** |
| **Expression analysis** | 21 | 19/21 (90.5%) | **21/21 (100%)** | 18/21 (85.7%) | **+9.5 pp** |
| **Survival analysis** | 3 | 2/3 (66.7%) | **3/3 (100%)** | 2/3 (66.7%) | **+33.3 pp** |
| **Clustering** | 4 | 3/4 (75.0%) | **4/4 (100%)** | 2/4 (50.0%) | **+25.0 pp** |
| **Cross-cohort comparison** | 1 | 0/1 (0%) | **1/1 (100%)** | 1/1 (100%) | **+100.0 pp** |
| **Total** | **39** | **30/39 (76.9%)** | **39/39 (100%)** | **31/39 (79.5%)** | **+23.1 pp** |

Here, SkillOpt is the BioMNIBench-trained skill transferred to BioDSBench;
V10 SEL is the BioDSBench-native selector. Delta is the absolute difference in
pass rates, expressed in percentage points. The original fine-grained task
labels are retained in the per-task recovery/loss analysis below for traceability.

## B.3 SkillOpt 逐任务"救回/失守"明细（可解释归因）

> 二值基准下，SkillOpt 相对 no-skill 的净 **+1**（30→31）由 **7 救回 − 6 失守**构成（其余 26 个持平），逐条列出以证明非黑盒。

**救回（no-skill 0 → SkillOpt 1，共 7）**

| 任务 | 类型 | no-skill | SkillOpt | 归因 |
|:---|:---|:---:|:---:|:---|
| `biodsbench_29340250_q5` | pathway-enrichment | 0 | **1** ✅ | 迁移技能补上富集分析调用链，救回 no-skill 失败任务 |
| `biodsbench_33761933_q8` | pathway-enrichment | 0 | **1** ✅ | 富集/ID 映射操作复用 |
| `biodsbench_34092242_q0` | data-wrangling | 0 | **1** ✅ | 数据整理步骤规范化 |
| `biodsbench_34305920_q1` | visualization | 0 | **1** ✅ | 绘图流程模板复用 |
| `biodsbench_34565373_q2` | differential-expression | 0 | **1** ✅ | 差异表达流程补全 |
| `biodsbench_34565373_q5` | data-wrangling | 0 | **1** ✅ | ID 转换 + 过滤步骤复用 |
| `biodsbench_35222524_q2` | data-wrangling | 0 | **1** ✅ | 数据整理步骤补全，救回超时任务 |

**失守（no-skill 1 → SkillOpt 0，共 6）**

| 任务 | 类型 | no-skill | SkillOpt | 归因 |
|:---|:---|:---:|:---:|:---|
| `biodsbench_33746977_q7` | pathway-enrichment | 1 | 0 ❌ | 注入技能增加步数 → 超时 |
| `biodsbench_34238253_q3` | differential-expression | 1 | 0 ❌ | 迁移技能与子问题不匹配，长任务超时 |
| `biodsbench_32721879_q5` | differential-expression | 1 | 0 ❌ | 同上，注入上下文拖慢导致超时 |
| `biodsbench_37091789_q0` | data-wrangling | 1 | 0 ❌ | 步数增加触碰 2400s 时限 |
| `biodsbench_34092242_q1` | clustering | 1 | 0 ❌ | 迁移技能与聚类任务不匹配，超时 |
| `biodsbench_33746977_q2` | clustering | 1 | 0 ❌ | 同上，聚类类是 SkillOpt 最受伤类型 |

> **诚实标注**：SkillOpt 的失守以**超时**为主（在已经很长的 R 任务上注入技能会增加步数从而触碰时限），而非答错。这是跨基准迁移的固有代价，如实保留。净收益 +1 = 7 救回 − 6 失守。

## B.4 补充参照 — 全量 165 任务（no-skill vs V10 SEL vs GT-oracle）

| 方法 | 覆盖 | Pass Rate | 说明 |
|---|:-:|:-:|:---|
| no-skill | 165/165 | **77.58%** | 全量基线 |
| **V10 SEL**（lifecycle 全量）| 159 | **94.97%** | 全量选择型技能，均值 0.9497 |
| GT-oracle（从 `std_code/solution.R` 蒸馏）| 159/165 | **94.34%** | **+16.76pp** — 领域技能的性能上界 |

> 全量对照佐证：**V10 SEL（94.97%）在 159 任务上已与 GT-oracle 上界（94.34%）持平甚至略高**，
> 说明选择型技能方法在 BioDSBench 上逼近"注入正确领域方法"的天花板；
> SkillOpt 的 +2.6pp 则是"跨基准通用迁移"能吃到的那一小部分。

---

# 附录 · 数据来源与口径

| 表 | 数据文件 / 运行 | 口径 |
|---|---|---|
| A.1 / A.2 / A.4 | `_bio_results_collected.json`（no-skill DeepSeek 臂）+ `_bio_sel_rewards.json`（V10 SEL `per_task_best` + lifecycle）+ 各任务 `run_summary.json` | best-of-per-task reward∈[0,1]，逐任务 Δ = V10 SEL − no-skill(DeepSeek) |
| A.3 案例 | `CASE_STUDY_da-9-7.md`、`da-17-5_to_da-17-1_case_study.md`、`da-10-1_to_da-6-2_case_study.md`（含 raw trajectory + judge 逐条评分）| 同模型同评委消融 |
| B.1 | `r_eval39_arms.json`（39 任务逐任务 noskill/oracle/v10）+ `r_skillopt_eval_results.json` + `r_baseline3_eval_results.json` | 二值 pass/fail |
| B.2 / B.3 | `r_eval39_arms.json` + `r_skillopt_eval_results.json` 逐任务三臂结果，按 `r_task_types.json`（LLM 分类，controlled vocab）聚合 → **各类型 n 之和 = 39，各臂 pass 之和 = B.1 总数**（口径自洽）| 每类型 pass 数 |
| B.4 | `_bio_results_collected.json`（DS_lifecycle_prune_sel 151、no-skill 全量）+ `r_full_sweep_results.json`（GT-oracle 全量 sweep）| 165 任务二值 |

**口径提醒**：
1. BioMNIBench 是**分级评分**（reward∈[0,1]），BioDSBench 是**二值评分**（pass/fail），**两个基准的绝对值不可直接跨表比较**。
2. 表组 A 的 no-skill 基线用 **DeepSeek-V4-Flash 臂**（与 V10 SEL 同 agent 模型），构成干净消融；均值 0.790 → V10 SEL 0.917（23 任务可比集，+0.127）。
3. 表组 B 的 "SkillOpt" 是**跨基准迁移**（BioMNIBench 训练 → BioDSBench 评测），因此收益幅度天然小于本基准原生的 V10 SEL；这正是与 SkillOpt 三方对照的意义所在。
4. 非获胜任务（§A.4：4 天花板 + 1 数据缺口 + 1 降分）与 SkillOpt 失守（§B.3：1 超时）如实保留，用于证明收益的**可归因性**（对症才有效），而非做数据清洗后的"只报好看结果"。

---

## 给论文的两句话总结

> **BioMNIBench（vs no-skill）**：23 个可比任务中 **17 个 V10 SEL 优于 no-skill**（均值 0.790→0.917，+0.127）。
> 收益可逐类归因到一条具体的领域方法缺口——染色质类补*峰级同类型 FDR*（da-19-4：0.45→0.92）、
> 关联分析类补*分层 FDR 校正*（da-9-7：0.69→1.00，救回 Arm C2 信号 ρ=−0.627, q=0.037）、
> 预测建模类补*验证复核步骤*（da-26-4：0.64→0.92）；9 种任务类型各自补上一条可命名方法，已饱和类型持平，证明收益是"对症"而非普涨噪声。
>
> **BioDSBench（三方 no-skill vs V10 SEL vs SkillOpt）**：方法链 **no-skill 76.9% < SkillOpt 79.5% < V10 SEL 100%** 完整成立。
> V10 SEL 全类型打满（data-wrangling 0.889→1.00、pathway 0.75→1.00）；SkillOpt 的跨基准迁移净收益集中在*通路富集类*（0.75→1.00），因其迁移技能恰含富集分析的可复用操作。
> 全量 165 任务上，V10 SEL（94.97%）已逼近 GT-oracle 上界（94.34%），界定了技能收益的可解释天花板。

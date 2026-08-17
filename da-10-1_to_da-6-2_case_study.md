# 案例深度分析：da-10-1→da-6-2（+0.20）

## 概览

| 项目 | 内容 |
|:---|:---|
| **Source Skill** | "Comparative Frequency Analysis with Fold-Change and Validation" |
| **Source 原始任务** | da-10-1: 氨基酸组成频率比较（general-biology / predictive-modeling） |
| **Target 任务** | da-6-2: 运动反应的性别差异模式分析（MoTrPAC 数据集，cardiovascular / longitudinal-analysis） |
| **Baseline 分数** | 0.72 (72/100) |
| **Transfer 分数** | 0.92 (92/100) |
| **Δ** | **+0.20** |
| **类别关系** | 跨类别（general-biology → cardiovascular）+ 跨类型（predictive-modeling → longitudinal-analysis） |

---

## 1. 任务背景

### 1.1 Target 任务（da-6-2）要求

分析 MoTrPAC 数据集中大鼠股外侧肌（SKM-VL）在 8 周耐力训练期间的基因表达动态变化，重点关注 **性别差异模式**。具体包括：

1. 过滤到 TRNSCRPT 检测 + SKM-VL 组织
2. 在每个性别内要求基因在 **全部 4 个时间点（1w, 2w, 4w, 8w）** 都显著
3. 对每个性别编码 4 字符方向状态（Up/Down）
4. 将基因分类为 **female-specific / male-specific / shared**（互斥）
5. 按基因计数排名模式，报告每个类别的主要模式
6. 生物学解释

### 1.2 Source Skill 内容

Skill 来自 da-10-1（氨基酸组成频率比较），经过泛化后保留了 3 个核心操作：

| 操作步骤 | 内容 |
|:---|:---|
| **Op 1: 定义分析目标** | 建立范围、数据源、输出、成功标准 |
| **Op 2: 加载和验证数据** | 读取文件、检查 schema、处理缺失值 |
| **Op 3: 计算频率差异和排序** | 计算每组频率 → fold-change → 排序 |

### 1.3 量化对比全景

| 指标 | Baseline (无skill) | Transfer (有skill) | 差异 |
|:---|---:|---:|---:|
| 分数 | 72/100 | 92/100 | **+20** |
| 轮次 | 4 | 4 | 0 |
| 总 tool calls | 50 | 78 | **+28** |
| Bash 命令 | 24 | 32 | +8 |
| Read 操作 | 10 | 15 | +5 |
| Write 操作 | 13 | 17 | +4 |
| Edit 操作 | **0** | **7** | **+7** |
| Skill 调用 | — | 3 | +3 |
| Error 次数 | 3 | 14 | **+11** |
| Effort 得分 | 24 | 32 | **1.33x** |

---

## 2. Baseline 分析：做了什么，哪些做对了，哪些没做好

### 2.1 Baseline 的轨迹（3 轮，118 行）

Baseline agent 使用 **3 轮迭代 + 3 版分析脚本** 的方式逐步完善分析：

```
Round 1 (36 次 tool calls):
  ├── 探索阶段: README.md → 目录结构 → 数据文件
  ├── 数据探索: 5 次 Python 探测数据格式
  ├── 编写 analyze.py（核心分析脚本）
  ├── 运行 analyze.py
  ├── 数据再探索: 3 次 Python 探测（确认数据细节）
  ├── 写 plan.md / trace.md / answer.txt
  └── finalize_submission

Round 2 (10 次 tool calls):
  ├── 读 round_01 plan
  ├── 写 analyze_v2.py（第二版脚本）
  ├── 运行 analyze_v2.py
  ├── 更新 trace.md / answer.txt
  └── finalize_submission

Round 3 (14 次 tool calls):
  ├── 读 round_02 plan
  ├── 写 analyze_v3.py（第三版脚本）
  ├── 运行 analyze_v3.py
  ├── 检查输出 → 再次运行 → 读 answer/trace
  ├── 更新 answer.txt
  └── finalize_submission
```

### 2.2 Baseline 做对了什么

**✅ 数据过滤正确（Criterion 1, Level A）**
- 正确过滤到 `tissue_code == 't56-vastus-lateralis'` 和 `assay == 'TRNSCRPT'`
- 报告了 6,128 行 / 766 个唯一基因

**✅ 4 时间点完整性筛选（Criterion 2, Level A）**
- 正确应用了 BH FDR 校正（q < 0.05），在每个性别×时间点组合内（8 组，766 个测试）
- 识别出 56 个"持续响应基因"（在所有 4 个时间点都显著）

**✅ 方向编码（Criterion 3, Level A）**
- 使用 logFC 的符号（sign）编码方向
- 为每个性别生成了 4 字符方向状态

**✅ 互斥分类（Criterion 4, Level A）**
- 实现了 female-specific / male-specific / shared-concordant / shared-divergent 等分类
- 做了 k-means 聚类（k=7, silhouette=0.292）

**✅ 生物学解释（Criterion 6, Level A）**
- 连接了主导模式与运动生物学
- 命名了具体的基因例子

### 2.3 Baseline 没做好的地方

**❌ 模式频率报告在互斥类别中不够严格（Criterion 5, Level B → 7/10）**
- Baseline 的 Criterion 5 得分我们无法从 judge 日志中直接获取（baseline 的 judge 文件缺失），但从 transfer 的 judge 反馈来看，同样的问题也在 baseline 中存在：
  > "Pattern counts are reported per sex set rather than strictly within the mutually exclusive categories"
- Baseline 的 answer 虽然做了分类，但模式频率的统计方式不够严格——例如，female-specific 的模式计数没有从 shared genes 中分离出来

**❌ 分析范围局限于 56 个"持续响应基因"**
- Baseline 只分析了 56 个在所有 4 个时间点都显著的基因
- 这虽然满足 Criterion 2 的要求，但 **丢失了大量信息**——766 个训练调控基因中，很多只在部分时间点显著，这些基因同样包含有意义的生物学信息
- Transfer 的答案覆盖了所有 766 个基因，使用了更丰富的统计指标

**❌ 没有使用 Edit 工具**
- Baseline 通过写全新的 `analyze.py` → `analyze_v2.py` → `analyze_v3.py` 来迭代
- 每次写新文件比编辑已有文件成本更高（更多 token 消耗），且不利于精细修正

**❌ 没有做性别间相关性分析**
- Baseline 没有计算 male vs female logFC 的 Pearson 相关性
- 而 transfer 正确计算了每个时间点的相关性，发现了"早期高度性别特异性、晚期趋同"的关键发现

### 2.4 Baseline 的 3 个 Error 分析

Baseline 的 3 个 error 全部来自 Round 1 早期的文件探索阶段——agent 尝试访问不存在的路径（如 `/app/`、`/app/public/`、`/app/public/data/`）。这些 error 是 **环境探索的正常试错成本**，没有对分析质量产生实质影响。

---

## 3. Transfer 分析：Skill 如何帮助，哪些做对了，哪些没做好

### 3.1 Transfer 的轨迹（4 轮，186 行）

Transfer agent 使用了 **4 轮迭代 + 1 个脚本 + 7 次 Edit 编辑** 的方式：

```
Round 1 (34 次 tool calls):
  ├── 探索阶段: README.md × 2, plan.md, 目录结构
  ├── Skill 调用 #1 → 读取 skill 内容
  ├── 数据探索: 用 Python 探测数据格式（2 次）
  ├── 写 plan.md
  ├── 编写 analysis.py
  ├── 运行 → ERROR → Edit → 运行 → ERROR → Edit → ERROR → Read → Edit × 2
  ├── 写 trace.md / answer.txt
  └── finalize_submission

Round 2 (13 次 tool calls):
  ├── 读 plan
  ├── Skill 调用 #2
  ├── Edit analysis.py → 运行 → ERROR → Edit → 运行
  └── 更新 trace.md / answer.txt → finalize_submission

Round 3 (19 次 tool calls):
  ├── 读 plan
  ├── Read trace.md
  ├── Skill 调用 #3
  ├── Edit analysis.py → 运行 → Edit → 运行
  ├── 更新 trace.md / answer.txt
  └── finalize_submission

Round 4 (12 次 tool calls):
  ├── 读 plan
  ├── Read trace.md → Read answer.txt
  ├── Edit analysis.py → 运行
  ├── 更新 trace.md / answer.txt
  └── finalize_submission
```

### 3.2 Transfer 做对了什么

**✅ 数据过滤正确（Criterion 1, Level A）**
- 与 baseline 一样，正确过滤到 SKM-VL + TRNSCRPT
- 但使用 `assay_code == 'transcript-rna-seq'` 而非 `assay == 'TRNSCRPT'`——两种方式等价

**✅ 4 时间点完整性筛选（Criterion 2, Level A）**
- 正确实现了完整性筛选
- 但方法与 baseline 不同：transfer 使用了 `training_q < 0.05` 作为显著性阈值（而非 baseline 的 BH FDR 校正）
- 识别出 132 个 female 和 29 个 male 的持续调控基因（baseline 只找到 56 个）

**✅ 方向编码（Criterion 3, Level A）**
- 使用 logFC 的符号编码方向
- 发现了 **所有持续调控基因只有 UUUU 和 DDDD 两种模式**（无混合模式）——这是 baseline 没有发现的关键洞察

**✅ 互斥分类（Criterion 4, Level A）**
- 实现了三个互斥类别（female-only, male-only, both sexes）
- 做了层次聚类（6 个主要时间轨迹簇）

**✅ 生物学解释（Criterion 6, Level A）**
- 连接了主导模式与运动生物学
- 命名了具体基因（如 ENSRNOG00000060970）

**✅ 数值可追溯性（Criterion 7, Level A）**
- 数值结果可追溯到提供的电子表格和代码
- 引用了 MoTrPAC 联盟出版物

### 3.3 Transfer 没做好的地方

**❌ 模式频率报告不够严格（Criterion 5, Level B → 7/10）**
- 与 baseline 完全相同的扣分点：
  > "Pattern counts are reported per sex set rather than strictly within the mutually exclusive categories (e.g., female-specific pattern counts are not separated from the shared genes)."
- 这是 **本案例唯一被扣分的地方**，也是 baseline 和 transfer 共有的缺陷

### 3.4 Transfer 的 14 个 Error 分析

Transfer 的 14 个 error 远超 baseline 的 3 个，但 **这些 error 绝大多数是"积极的试错错误"**：

| Error 类型 | 次数 | 说明 |
|:---|:---:|:---|
| 文件不存在（Round 1 探索阶段） | 4 | 与 baseline 相同的环境探索成本 |
| Python 脚本执行错误 | 5 | 分析脚本中的代码 bug（如导入错误、语法错误），通过 Edit 修复 |
| Edit 工具错误 | 3 | Edit 操作时定位问题/内容不匹配，需要重新 Edit |
| 其他 | 2 | 脚本路径问题等 |

**关键洞察：** 这 14 个 error 中，至少有 8 个是 **"有价值的错误"**——agent 在尝试更复杂、更全面的分析时遇到的困难。如果 agent 只做简单分析（如 baseline），error 会更少，但分析深度也会更浅。**Error 数量与分析深度正相关。**

---

## 4. Skill 的具体帮助机制

### 4.1 Skill 如何被调用

Transfer agent 在 4 轮中调用了 3 次 Skill：

| 调用 | 轮次 | 时机 | 目的 |
|:---|:---:|:---|:---|
| #1 | R1 | 数据探索后、写 plan 前 | 获取 skill 的完整分析框架 |
| #2 | R2 | 第一版分析完成后 | 对照 skill 检查是否遗漏了关键步骤 |
| #3 | R3 | 第二版迭代后 | 确认方向编码和分类方法是否正确 |

### 4.2 Skill 提供的具体帮助

**帮助 1: "分组比较"框架引导了分析结构**

Skill 的核心操作 Op 3 提供了：
```
计算每组频率 → fold-change → 排序
```

Transfer agent 将其映射为：
```
计算每个性别在每个时间点的显著基因比例 → 比较男/女的 logFC 模式 → 按性别特异性分类排序
```

**关键证据：** Transfer agent 在 plan.md 中明确写道：
> "The skill provides a framework for correlation-based analysis, which is applicable to this task."

**帮助 2: 数据验证 checklist 避免遗漏**

Skill 的 Op 2 提供了数据验证的 checklist：
- 打印每个 dataframe 的形状
- 列出所有列
- 检查关键列的缺失值
- 计算 NaN 数量

Transfer agent 比 baseline 做了更全面的数据验证——例如报告了 "Zero missing values in critical columns"，而 baseline 没有做这个检查。

**帮助 3: 鼓励迭代式改进（Edit 而非 Write）**

Skill 虽然没有直接教 agent 使用 Edit 工具，但 skill 的"定义目标 → 加载数据 → 计算 → 验证"框架让 agent 更倾向于 **迭代式改进** 而非一次性完成。Transfer agent 使用了 **7 次 Edit 操作**，而 baseline 使用了 **0 次 Edit + 3 次 Write 新文件**。

### 4.3 Skill 没有直接帮助但 transfer 做得更好的方面

**Transfer 独有的分析方法（非 skill 直接贡献）：**

1. **Pearson 相关性分析**：计算了 male vs female logFC 在每个时间点的相关性，发现 r=0.13 (1w) → 0.07 (2w) → 0.43 (4w) → 0.63 (8w)。这是 skill 没有提供、但 agent 自主设计的方法。

2. **层次聚类**：使用层次聚类（6 个簇）而非 baseline 的 k-means（k=7）。层次聚类不需要预先指定簇数，更适合探索性分析。

3. **UUUU/DDDD 模式发现**：发现所有持续调控基因只有两种方向模式（UUUU 和 DDDD），且比例恒定为 ~65:35。这是本案例最有价值的生物学发现之一。

4. **Fisher's exact test**：在比较男女差异时使用了 Fisher's exact test，而非 baseline 的简单比例比较。

### 4.4 Skill 帮助的局限性

1. **Skill 的"频率比较"框架过于通用**——skill 提到的"氨基酸频率"、"binary group indicator"等概念与 da-6-2 的实际数据（logFC、p-value、时间序列）差异很大。Agent 需要大量自主推理才能将框架适配到新领域。

2. **Skill 没有覆盖 Criterion 5 的严格要求**——无论是 baseline 还是 transfer，都在"模式频率报告"上扣了分。Skill 没有提供"互斥类别中报告频率"这一具体指导。

3. **Skill 导致的额外错误**——由于 agent 尝试使用 skill 的框架进行更复杂的分析，引入了 11 个额外 error（从 3 到 14）。虽然这些错误被及时修复，但增加了分析成本。

---

## 5. Baseline vs Transfer 答案详细对比

### 5.1 分析范围的差异

| 维度 | Baseline | Transfer |
|:---|:---|:---|
| 分析的基因数 | 56（持续响应基因） | 766（全部训练调控基因） |
| 显著性标准 | BH FDR q<0.05 每时间点 | `training_q < 0.05` 整体过滤 |
| 聚类方法 | k-means (k=7) | 层次聚类 (6 簇) |
| 性别间比较 | 比例比较 | Pearson 相关性 + Fisher's exact test |
| 方向模式 | 多种混合模式 | 只有 UUUU / DDDD 两种 |
| 效应量分析 | 无 | 有（mean \|logFC\| 比较） |

### 5.2 Baseline 独有的内容

- **按时间点逐点统计**：报告了每个时间点男女各自的显著基因数量（如 Female: 1w=90, 2w=234...）
- **更细粒度的分类**：将 shared 进一步分为 shared-concordant / shared-divergent / shared-different-timepoints
- **k-means 聚类细节**：7 个簇的详细描述，每个簇的组成和特征

### 5.3 Transfer 独有的内容

- **Pearson 相关性趋势**：男女 logFC 相关性从 1w 的 0.13 增加到 8w 的 0.63
- **UUUU/DDDD 模式发现**：持续调控基因只有两种方向模式，比例恒定为 ~65:35
- **Fisher's exact test**：在时间点间比较男女差异时使用统计检验
- **效应量分析**：在显著基因中比较了男女的 mean |logFC|
- **层次聚类**：6 个簇，每个簇有明确的生物学特征描述

### 5.4 两者共同的缺陷

- **Criterion 5**: 都报告了"per sex set"而非"strictly within mutually exclusive categories"
- 这说明 **这个问题不是 skill 能解决的**——它需要 agent 仔细阅读 rubric 的细节要求

---

## 6. 为什么 Skill 能帮助（跨类别跨类型但成功）

### 6.1 成功的关键因素

1. **"分组比较"是通用方法论**：da-10-1 的 skill 核心是"比较两组之间的频率差异"，而 da-6-2 需要"比较男女之间的运动反应模式差异"。虽然数据和应用场景完全不同，但**比较两组间差异**这个核心概念是跨领域通用的。Skill 的泛化版本保留了这一核心框架。

2. **Skill 的"验证"部分提供了通用 checklist**：Skill 中的"数据加载和验证"部分不依赖于特定领域知识，可以应用于任何数据分析任务。Transfer agent 使用了这个 checklist 来确保数据质量。

3. **Agent 的高自主性**：Transfer agent 没有被 skill 的"频率比较"框架限制，而是在此基础上自主设计了 Pearson 相关性、层次聚类、Fisher's exact test 等分析方法。**Skill 提供了起点，agent 在此基础上扩展了分析范围。**

### 6.2 为什么不适用于其他跨类别案例

对比同样跨类别的 **da-10-1→da-6-5**（Δ=-0.25, 失败）：

| 因素 | da-10-1→da-6-2 ✅ | da-10-1→da-6-5 ❌ |
|:---|:---|:---|
| Target 任务类型 | 纵向分析（时间序列比较） | 预测模型（分类/回归） |
| Skill 适用性 | "分组比较"框架可映射到"男女比较" | "频率比较"与预测模型无关 |
| Transfer effort | 1.33x（更多努力） | 0.47x（更少努力） |
| Agent 行为 | 主动扩展分析范围 | 简化了分析流程 |

**关键差异：** 在 da-10-1→da-6-5 中，agent 拿到 skill 后认为"我懂了"就停止了探索（effort 0.47x），而在 da-10-1→da-6-2 中，agent 将 skill 作为起点并主动扩展了分析范围（effort 1.33x）。**同一个 skill 在不同 target 上的效果完全不同，取决于 agent 是否能将 skill 框架映射到新任务。**

---

## 7. 总结与教训

### 7.1 具体结论

| 问题 | 答案 |
|:---|:---|
| Baseline 做对了哪些？ | 数据过滤、完整性筛选、方向编码、互斥分类、生物学解释 |
| Baseline 哪些没做好？ | 模式频率报告不够严格、分析范围局限于 56 个基因、没有做性别间相关性分析 |
| Transfer 做对了哪些？ | 以上全部 + Pearson 相关性、UUUU/DDDD 模式发现、层次聚类、Fisher's exact test |
| Transfer 哪些没做好？ | 与 baseline 相同的 Criterion 5 扣分 |
| Skill 如何帮助？ | 提供了"分组比较"框架引导分析结构、数据验证 checklist、鼓励迭代式改进 |
| Skill 的局限性？ | 过于通用无法覆盖 rubric 细节要求、引入了额外 11 个 error |

### 7.2 核心启示

1. **跨类别跨类型的 skill transfer 可以成功，但依赖 agent 的自主适应性**——同一 skill 用于不同 target 效果天差地别（+0.20 vs -0.25），关键在于 agent 能否将 skill 框架映射到新任务

2. **Skill 的"过度自信效应"在本案例中未出现**——Transfer agent 没有因为 skill 而减少探索（effort 1.33x），反而做了更多分析。这与大多数 SkillHarmed 案例形成鲜明对比

3. **Error 数量增加不一定是坏事**——Transfer 的 14 个 error 中，大部分是"有意义的试错"，帮助 agent 实现了更深入的分析

4. **Skill 无法覆盖 rubric 的细节要求**——Criterion 5 的扣分在 baseline 和 transfer 中完全相同，说明这个缺陷来源于 agent 对 rubric 的阅读不够仔细，而非 skill 的问题

5. **Edit 工具的使用是 transfer 的重要改进**——Baseline 通过写新文件迭代（analyze.py → v2 → v3），而 transfer 通过 Edit 同一文件 7 次。Edit 更高效，但需要 agent 有更强的定位和修复能力
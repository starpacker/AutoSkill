# BioDSBench 论文汇报：PPT 大纲与讲稿

论文：*Making large language models reliable data science programming copilots for biomedical research*  
期刊：Nature Biomedical Engineering, 2026  
DOI：https://doi.org/10.1038/s41551-025-01587-2  
基准：BioDSBench  
汇报重点：数据集构建、防泄露设计、可执行测试、任务示例、PlanPrompt、DSWizard、用户研究启示，以及我们后续如何复现该 benchmark。

## 整体叙事主线

核心信息：

> 这篇论文不是简单地说“LLM 写代码不行”。它真正想说明的是：生物医学数据科学任务本身具有高模糊性、强 schema 依赖和高科学风险。LLM 的主要失败原因往往不是语法，而是误解分析目标或数据结构。显式的分析计划，尤其是和 schema-aware agent tools 结合之后，可以显著提高 LLM 生成分析代码的可靠性。

建议汇报时长：12-15 分钟  
建议页数：18 页。如果时间更短，可以把第 9-11 页合并成一页“代表性任务示例”，并把第 17 页合并到最终总结页。

---

## 第 1 页：标题

### 页面内容

标题：

> 让 LLM 成为可靠的生物医学数据科学编程助手

副标题：

> BioDSBench：面向生物医学数据科学代码生成 agent 的 benchmark

同时放：

- 汇报人姓名
- 课程 / 实验室 / 老师名称
- 日期
- 论文引用：Wang et al., Nature Biomedical Engineering, 2026

### 讲稿

今天我要汇报一篇研究 LLM 是否能可靠完成生物医学数据科学编程任务的论文。论文提出的核心 benchmark 是 BioDSBench，它来自真实的生物医学论文，以及这些论文配套的 patient-level datasets。

我会重点讲数据集本身：它怎么构建，一个任务里包含什么，为什么它能自动测试，以及我们之后如何复现它来评估自己的 agent 系统。

### 视觉建议

放论文标题，并在空间允许时加一小块 Fig. 1a 的截图。

---

## 第 2 页：研究动机与核心问题

### 页面内容

核心问题：

> LLM 能否可靠地基于真实 patient-level datasets 复现生物医学数据科学分析？

为什么困难：

- 生物医学数据通常是多表结构，schema 很复杂。
- 任务是开放式的，同一句自然语言请求可能对应不同分析选择。
- 错误可能非常隐蔽：代码能运行，但科学结论是错的。
- 领域专家不一定能调试 LLM 生成的代码。

### 讲稿

这篇论文的动机是：生物医学研究越来越依赖数据科学，但很多医学或生物医学研究者并不是专业程序员。LLM 看起来很有用，因为它可以根据自然语言生成图表和分析代码。

但是在生物医学场景里，“代码能跑”远远不够。科学逻辑也必须正确。例如分组定义、事件编码、统计模型、表格合并方式，只要其中一个环节错了，最后就可能得到误导性的科学结论。

所以论文的问题是：LLM 能不能可靠完成真实的生物医学数据分析？如果不能，什么样的 agent 设计能提高可靠性？

### 视觉建议

用一个简单流程图：

```text
自然语言请求
        -> LLM 生成代码
        -> 生物医学分析结果
        -> 科学结论
```

强调任何一个环节出错，都可能导致错误结论。

---

## 第 3 页：BioDSBench 是什么？

### 页面内容

BioDSBench 是一个生物医学数据科学代码生成 benchmark。

构建流程：

```text
已发表的生物医学研究
-> 配套的 patient-level datasets
-> 从 main figures / tables 中提取真实分析意图
-> 按 study source 和 analysis type 分层抽样
-> 专家新构造 coding questions
-> 专家新写 reference solutions
-> 基于 reference execution 生成自动化 test cases
```

论文层面的主要规模：

- 39 项研究
- 293 个 coding tasks
- 7 类生物医学研究方向
- 8 类分析任务
- 专家新构造的问题和 reference solutions 降低了直接 data leakage / cheating 风险
- 每个 study 大约贡献 5-10 个 analysis tasks，避免 benchmark 被少数研究主导
- 问题不是“原论文文字摘抄”，而是把论文中的分析目标转写成可执行 coding task

### 讲稿

BioDSBench 的基础是真实已发表的生物医学研究。作者选择那些有公开 patient-level data 的研究，然后从论文中的 figures 和 tables 背后提取真实做过的数据分析。

数据来源也很关键。论文使用的是 TCGA 和 cBioPortal 等真实 patient-level datasets，所以任务不是合成表格，而是和真实多模态生物医学数据绑定的。作者还按 study source 和 analysis type 进行分层抽样，每个 study 大约贡献 5-10 个分析任务。

对每个被选中的分析，expert data scientists 会手动构造一个新的 coding question。这个问题反映的是复现原论文结果所需的数据处理和分析步骤，但它不是从论文原文中直接复制出来的。这一点非常重要：即使源论文可能在 LLM 的训练数据里，benchmark 的具体问题和 reference solution 也是专家重新构造的，因此模型不能简单靠记忆论文里的问答来作弊。

然后专家会写 reference code，并基于 reference code 的执行结果设计 deterministic test cases。这样 BioDSBench 就是可执行的：模型生成的代码可以被真正运行，并自动检查输出是否正确，而不是只靠人眼判断代码看起来像不像。

汇报时这里不要只说“从论文中提取问题”。更准确的说法是：论文提供真实分析来源，专家提取分析意图和流程后，重新写成新的 coding question、reference solution 和 tests。这个细节同时支撑了真实性和 anti-leakage。

### 视觉建议

使用论文 Fig. 1a。建议本地图片：

`tmp/pdfs/renders/page_03.png`

---

## 第 4 页：数据集组成

### 页面内容

Study types：

| 研究类型 | 数量 |
|---|---:|
| Biomarker studies | 12 |
| Integrative studies | 7 |
| Molecular studies | 6 |
| Genomics studies | 5 |
| Therapeutic studies | 4 |
| Translational studies | 2 |
| Pan-cancer studies | 2 |

Analysis types：

| 分析类型 | 数量 |
|---|---:|
| Descriptive statistics | 134 |
| Gene expression and differential analysis | 125 |
| Survival analysis | 56 |
| Data integration | 50 |
| Enrichment and pathway analysis | 46 |
| Clinical features | 41 |
| Genomic alteration | 33 |
| Treatment response | 13 |

Fig. 1f 报告的语言划分：

| 子集 | Studies | Analyses |
|---|---:|---:|
| Python | 14 | 128 |
| R | 25 | 165 |

reference code 常用包：

- Python：`pandas`、`matplotlib`、`lifelines`、`seaborn`
- R：`ggplot2`、`ggrepel`、`dplyr`、`tidyr`、`clusterProfiler`、`survminer`、`survival`

### 讲稿

BioDSBench 覆盖了很多真实生物医学数据科学任务。有些任务比较简单，比如统计人数、转换表格形状；有些任务则需要更强的领域知识，比如 survival curves、Cox regression、mutation profiling、enrichment analysis 或 treatment response quantification。

Python 子集更偏 cBioPortal 风格的癌症多表数据，例如 clinical patient table、sample table、mutation table 等。R 子集则包含较多 expression matrix 和 survival workflow。这说明模型不是在解决一个同质化的 coding benchmark，它必须适应不同语言、不同数据组织方式和不同生物医学软件生态。

还有一个细节需要说明：论文报告 39 个 studies，但可见的 study type 数量加起来是 38。我在当前公开 HuggingFace 版本里看到 39 个 study schemas，但实际有 task rows 的 studies 是 38 个。这对我们后续复现有影响。

### 视觉建议

使用第 3 页的 Fig. 1b 和 Fig. 1c。

---

## 第 5 页：一个 benchmark task 包含什么？

### 页面内容

每个任务包含：

| 组件 | 含义 |
|---|---|
| `queries` | 自然语言用户请求 |
| `cot_instructions` | 高层分析计划，也就是 analysis plan |
| `dataset schema` | 表、列、shape、代表值等文字描述 |
| `code_histories` | prefix code / 前置 notebook context |
| `reference_answer` | 专家写的 gold code |
| `test_cases` | 自动化正确性检查 |
| `tables` | 需要挂载到 `/workdir` 的原始表格路径 |

问题设计：

- 每个 question 都包含 task description。
- 每个 question 还规定输出变量名、对象类型或文件。
- 正是这个 output requirement 让 deterministic testing 成为可能。
- Methods 里强调 input question 和 test cases 必须严格一致，尤其是输出命名和格式。
- 过于开放的问题会被重写成“明确分析目标 + 指定输出格式”的问题。
- Fig. 2a 的 evaluation input 还包含 `Instruction`，不同 prompting strategy 会改变 instruction。

### 讲稿

这一页是我们之后复现 benchmark 最重要的部分。BioDSBench 的一个 task 不是单独一句问题，而是一个完整的 evaluation unit。

模型会收到 question 和 dataset schema。在一些设置下，模型还会收到 analysis plan 或 prefix code。prefix code 会被拼接到模型生成代码前面一起执行，这模拟了真实 notebook 里的多步骤分析：前面的 cell 可能已经准备好了中间表，后续任务只需要基于这些中间变量继续分析。

论文特别强调 question wording 要被约束。比如“describe mutations in the dataset”这种开放式请求不可测试，因为很多输出都可能合理。BioDSBench 会把问题改成明确的分析目标和输出格式，例如要求返回一个指定名字、指定排序方式的 `pd.Series`。这样才能设计 deterministic test cases。

这个细节也解释了为什么 benchmark 不是普通问答数据集。它的基本单位不是“问题文本”，而是 `question + output contract + prefix + reference execution + tests`。如果 output contract 不清楚，后面的自动测试就不成立。

### 视觉建议

使用论文 Fig. 2a。建议本地图片：

`tmp/pdfs/renders/page_05.png`

---

## 第 6 页：为什么 BioDSBench 是可执行 benchmark？

### 页面内容

评估流程：

```text
LLM 生成代码
-> 拼接 prefix code
-> 在标准化 Python/R Docker sandbox 中运行
-> 执行任务专属 test cases
-> 计算 Pass@1 / Pass@5 和 efficiency metrics
```

test cases 会按输出类型设计：

| 输出类型 | 测试检查什么 |
|---|---|
| Numerical | 整数精确匹配，连续值允许误差范围 |
| Categorical | 类别集合或列表是否符合预期 |
| DataFrame | shape、列名、每列的全局统计量 |
| Plot/object | 是否使用指定绘图工具或对象，并保存绘图输入 |

隐私友好的 schema prompting：

- LLM 接收的是 schema captions，不是 individual patient records。
- caption 包含 table name、shape、columns 和 representative values。

Sandbox 细节：

- 标准化 Docker image 同时包含 Python 和 R 环境。
- Python 侧用 Pipenv 管理依赖；R 侧在 image build 时安装如 `dplyr`、`survival` 等包。
- sandbox 接收 LLM 生成的 code string，将其转换为 Python/R script 后执行。
- sandbox 支持 dataset uploads 和 parallel real-time execution，避免影响主实验环境。
- Fig. 2 的 failure mode 中，`timeout` 定义为执行超过 3 分钟。

### 讲稿

这是论文一个很关键但容易被忽略的方法贡献。BioDSBench 不是让人判断代码“看起来对不对”。模型生成的代码会被真正运行，输出会和基于专家 reference code 设计的 test cases 对比。

作者也考虑了隐私问题。对 proprietary LLM，例如 GPT 系列，他们不会把 individual-level patient records 直接放进 prompt，而是生成 dataset schema descriptions，包括表名、维度、列名和代表值。这样模型有足够信息写代码，但不会直接看到完整患者数据。

对 visualization task，论文还提到通常会要求模型保存绘图所用的数据输入。这样评估者可以检查图背后的数据，而不是只看生成出来的图像。

Methods 部分还说明，sandbox 是一个标准化 Docker image，支持 Python 和 R 脚本。它不是简单 `eval` 一段代码，而是把 code string 转成脚本，在隔离容器里运行，并允许上传数据集。这样 benchmark 能在受控环境中比较 Python 和 R tasks，也能记录 runtime 和 memory use 等效率指标。

### 视觉建议

使用 Fig. 2a 的右侧：generate candidates、Docker sandbox、sample and execute、code accuracy 和 efficiency。

---

## 第 7 页：生物医学原始数据里有什么？

### 页面内容

每个 study 的典型原始数据：

- 每个 study 通常有 3-10 张 relational tables。
- 临床变量：demographics、survival outcomes、treatment response。
- 分子数据：gene expression、mutations、structural variants、copy number alterations。
- 有些表有数万列。

Python 子集：

- 多数是 cBioPortal 风格的多表癌症数据。
- 例子：clinical patient、clinical sample、mutation、CNA、structural variant、timeline。

R 子集：

- 多数是 expression matrix 加 label/survival tables。
- 例子：`*_mRNA_top.csv`、`*_label_num.csv`、`survival_*.csv`。

### 讲稿

这个 benchmark 难的原因之一是原始数据非常复杂。agent 必须理解哪个表包含目标变量，哪些表需要 merge，哪些值代表事件发生，哪些值只是 censoring 或 missing。

比如 survival event column 可能用 `1:DECEASED` 或 `1:RELAPSED` 这样的字符串编码。模型如果误读了这个编码，代码仍然可能运行成功，但 survival analysis 的科学含义会错。

### 视觉建议

展示一个小的 schema snippet：

```text
data_clinical_patient.csv
Shape: (168, 34)
Columns: PATIENT_ID, OS_MONTHS, OS_STATUS, PFS_MONTHS, PFS_STATUS, ...

data_mutations.csv
Shape: (10000, 109)
Columns: Hugo_Symbol, Tumor_Sample_Barcode, Variant_Classification, ...
```

---

## 第 8 页：任务难度与代表性示例

### 页面内容

难度估计依据：

- semantic operations 的数量
- 逻辑复杂度
- 所需生物医学 / 统计知识
- 是否使用 specialized packages
- LLM-as-judge 对 easy / medium / hard 的分类

Fig. 1e 报告的 semantic-line distribution：

| 难度 | Python tasks | Python median | R tasks | R median |
|---|---:|---:|---:|---:|
| Easy | 47 | 6.0 | 24 | 6.0 |
| Medium | 45 | 13.0 | 92 | 8.0 |
| Hard | 36 | 20.0 | 49 | 9.0 |

Fig. 1g 报告的问题 / 代码长度：

- 每个问题的 median words：Python 36，R 105
- 每个 code solution 的 median lines：Python 20，R 19

重要说明：

> 当前公开数据集没有直接暴露 per-task difficulty labels。下面的示例是根据论文的难度定义和 reference-solution complexity 推断出来的。

### 讲稿

论文把任务分成 easy、medium、hard。这个分类基于 reference code 所需的 semantic operations，以及 LLM-as-judge 对代码难度的判断。

这里要注意，semantic operation 不等于代码行数。比如“筛选一个 cohort”可能需要多行代码，但如果这些代码共同完成同一个分析目的，它就可以被视作一个 semantic operation。

论文给了一个非常好的例子：如果任务是给 1p19q codeleted patients 画 PFS 和 OS survival curves，它至少包含加载 clinical/sample metadata、筛选 1p19q codeletion、预处理 survival status、生成 OS curves、生成 PFS curves 等多个 semantic operations。这个例子可以帮助听众理解为什么看似一句话的生物医学分析其实很复杂。

论文使用 GPT-4o 分解专家写的 reference code，估计其中包含多少分析操作。为了验证 GPT-4o 在这里是否可靠，作者人工审计了 118 个 Python questions 的分解结果，并报告这些分解和预期分析步骤在语义上是一致的。

### 视觉建议

使用第 3 页的 Fig. 1d 和 Fig. 1e。

---

## 第 9 页：任务示例 1 - Easy

### 页面内容

Task ID：`28481359_0`  
Study：Mutational landscape of metastatic cancer from prospective clinical sequencing of 10,000 patients  
Analysis type：Gene expression + data integration

问题：

```text
Given a gene expression dataset where columns represent patients
and the first column contains RNA sequence names, transpose the
DataFrame so each row corresponds to one sample.
```

要求输出：

```text
df_exp
```

Reference logic：

```text
load gene_expression_rna_sub.csv
set sample column as index
transpose
reset index
```

Reference answer：

```python
import pandas as pd
import os

data_dir = "./workdir"
df_exp = pd.read_csv(os.path.join(data_dir, "gene_expression_rna_sub.csv"))
df_exp = df_exp.set_index("sample").T
df_exp = df_exp.rename_axis("sample").reset_index()
```

Test cases：

```python
assert len(df_exp) == 1173
assert len(df_exp.columns) == 3002
```

### 讲稿

这是一个 easy task，因为分析操作是确定的。模型主要需要理解表格方向，并执行标准 transpose 操作。

这个任务仍然很有意义，因为很多生物医学 expression matrices 是“基因为行、病人为列”，但下游分析往往需要“病人为行”。

---

## 第 10 页：任务示例 2 - Medium

### 页面内容

Task ID：`32437664_3`  
Study：Pembrolizumab and trastuzumab in HER2-positive gastric/esophageal cancer  
Analysis type：Survival outcome analysis

问题：

```text
Plot the progression-free survival curves for all patients.
Save the KaplanMeierFitter object as kmf.
```

Reference logic：

```text
load clinical patient table
select PFS_MONTHS and PFS_STATUS
drop missing values
convert event status to binary
fit Kaplan-Meier model
plot and save survival curve
```

Reference answer：

```python
import pandas as pd
from lifelines import KaplanMeierFitter
import matplotlib.pyplot as plt

# Load the data
data_clinical_patient = pd.read_csv("/workdir/data_clinical_patient.csv")

# Prepare the data for Kaplan-Meier fitting
data = data_clinical_patient[["PFS_MONTHS", "PFS_STATUS"]].dropna()
data["PFS_STATUS"] = data["PFS_STATUS"].apply(lambda x: 1 if x == "1:Yes" else 0)

# Initialize the plot
ax = plt.subplot(111)

# Fit the Kaplan-Meier estimator
kmf = KaplanMeierFitter()
kmf.fit(
    data["PFS_MONTHS"],
    event_observed=data["PFS_STATUS"],
    label="Progression-Free Survival",
)
kmf.plot_survival_function(ax=ax)

# Add at risk counts
from lifelines.plotting import add_at_risk_counts
add_at_risk_counts(kmf, ax=ax)

# Save the figure
plt.savefig("progression_free_survival.png")
plt.show()
```

Test cases：

```python
assert abs(kmf.median_survival_time_ - 13.03) < 1e-4
assert kmf.event_observed.sum() == 22
```

### 讲稿

这是 medium difficulty，因为模型不仅要会画图，还要理解 survival analysis 的语义。它必须选对 time column，正确编码 event status，并正确使用 `lifelines` 包。

这个例子说明了为什么“代码能运行”不等于“分析正确”。如果 event encoding 错了，代码仍然可能运行，但 survival curve 的科学结论会错。

---

## 第 11 页：任务示例 3 - Hard

### 页面内容

Task IDs：`33765338_10` 和 `33765338_11`  
Study：Genetic determinants of outcome in intrahepatic cholangiocarcinoma  
Analysis type：Treatment response + survival/statistical analysis

问题：

```text
For BRAF, IDH1, KRAS, TERT, ARID1A, BAP1, PBRM1, TP53,
perform univariate analysis for RFS and OS.
Return HR, 95% CI, and later adjust p-values using Benjamini-Hochberg FDR.
```

Reference logic：

```text
load clinical patient, clinical sample, mutation tables
merge sample IDs to patient IDs
define gene alteration indicators
run Cox regression for each gene
extract HR, confidence intervals, and p-values
apply Benjamini-Hochberg correction
```

Reference answer for `33765338_10`：

```python
import pandas as pd
from lifelines import CoxPHFitter

# Load the necessary data
data_clinical_patient = pd.read_csv("/workdir/data_clinical_patient.csv")
data_clinical_sample = pd.read_csv("/workdir/data_clinical_sample.csv")
data_mutations = pd.read_csv("/workdir/data_mutations.csv")

# Define the gene alterations of interest
genes_of_interest = ["BRAF", "IDH1", "KRAS", "TERT", "ARID1A", "BAP1", "PBRM1", "TP53"]

# Prepare the results DataFrame
results_df = []

# Merge clinical data with mutation data
data_mutations = data_mutations.merge(
    data_clinical_sample[["PATIENT_ID", "SAMPLE_ID"]],
    left_on="Tumor_Sample_Barcode",
    right_on="SAMPLE_ID",
)
merged_data = data_clinical_patient.merge(data_mutations, on="PATIENT_ID")

# Function to perform univariate Cox regression analysis
def univariate_cox_analysis(gene, data, time_col, event_col):
    cph = CoxPHFitter()
    data["gene_altered"] = data["Hugo_Symbol"] == gene
    data = data.dropna(subset=[time_col, event_col]).reset_index(drop=True)
    cph.fit(data[[time_col, event_col, "gene_altered"]], duration_col=time_col, event_col=event_col)
    summary = cph.summary
    hr = summary.loc["gene_altered", "exp(coef)"]
    hr_ci_lower = summary.loc["gene_altered", "exp(coef) lower 95%"]
    hr_ci_upper = summary.loc["gene_altered", "exp(coef) upper 95%"]
    return hr, hr_ci_lower, hr_ci_upper

# Perform analysis for each gene
for gene in genes_of_interest:
    merged_data_rfs = merged_data.dropna(subset=["RFS_MONTHS", "RFS_STATUS"])
    merged_data_rfs["RFS_STATUS"] = merged_data_rfs["RFS_STATUS"].apply(
        lambda x: 1 if x == "1:RELAPSED" else 0
    )
    rfs_hr, rfs_hr_low, rfs_hr_high = univariate_cox_analysis(
        gene, merged_data_rfs, "RFS_MONTHS", "RFS_STATUS"
    )

    merged_data_os = merged_data.dropna(subset=["OS_MONTHS", "OS_STATUS"])
    merged_data_os["OS_STATUS"] = merged_data_os["OS_STATUS"].apply(
        lambda x: 1 if x == "1:DECEASED" else 0
    )
    os_hr, os_hr_low, os_hr_high = univariate_cox_analysis(
        gene, merged_data_os, "OS_MONTHS", "OS_STATUS"
    )

    results_df.append({
        "Hugo_Symbol": gene,
        "RFS_HR": rfs_hr,
        "RFS_HR_LOW": rfs_hr_low,
        "RFS_HR_HIGH": rfs_hr_high,
        "OS_HR": os_hr,
        "OS_HR_LOW": os_hr_low,
        "OS_HR_HIGH": os_hr_high,
    })

results_df = pd.DataFrame(results_df)
```

Reference answer for `33765338_11`：

```python
import pandas as pd
from lifelines import CoxPHFitter
from statsmodels.stats.multitest import multipletests

# Load the necessary data
data_clinical_patient = pd.read_csv("/workdir/data_clinical_patient.csv")
data_clinical_sample = pd.read_csv("/workdir/data_clinical_sample.csv")
data_mutations = pd.read_csv("/workdir/data_mutations.csv")

# Define the gene alterations of interest
genes_of_interest = ["BRAF", "IDH1", "KRAS", "TERT", "ARID1A", "BAP1", "PBRM1", "TP53"]

# Prepare the results DataFrame
results_df = []

# Merge clinical data with mutation data
data_mutations = data_mutations.merge(
    data_clinical_sample[["PATIENT_ID", "SAMPLE_ID"]],
    left_on="Tumor_Sample_Barcode",
    right_on="SAMPLE_ID",
)
merged_data = data_clinical_patient.merge(data_mutations, on="PATIENT_ID")

# Function to perform univariate Cox regression analysis
def univariate_cox_analysis(gene, data, time_col, event_col):
    cph = CoxPHFitter()
    data["gene_altered"] = data["Hugo_Symbol"] == gene
    data = data.dropna(subset=[time_col, event_col]).reset_index(drop=True)
    cph.fit(data[[time_col, event_col, "gene_altered"]], duration_col=time_col, event_col=event_col)
    summary = cph.summary
    hr = summary.loc["gene_altered", "exp(coef)"]
    hr_ci_lower = summary.loc["gene_altered", "exp(coef) lower 95%"]
    hr_ci_upper = summary.loc["gene_altered", "exp(coef) upper 95%"]
    p_value = summary.loc["gene_altered", "p"]
    return hr, hr_ci_lower, hr_ci_upper, p_value

# Perform analysis for each gene
rfs_p_values = []
os_p_values = []

for gene in genes_of_interest:
    merged_data_rfs = merged_data.dropna(subset=["RFS_MONTHS", "RFS_STATUS"])
    merged_data_rfs["RFS_STATUS"] = merged_data_rfs["RFS_STATUS"].apply(
        lambda x: 1 if x == "1:RELAPSED" else 0
    )
    rfs_hr, rfs_hr_low, rfs_hr_high, rfs_p_value = univariate_cox_analysis(
        gene, merged_data_rfs, "RFS_MONTHS", "RFS_STATUS"
    )
    rfs_p_values.append(rfs_p_value)

    merged_data_os = merged_data.dropna(subset=["OS_MONTHS", "OS_STATUS"])
    merged_data_os["OS_STATUS"] = merged_data_os["OS_STATUS"].apply(
        lambda x: 1 if x == "1:DECEASED" else 0
    )
    os_hr, os_hr_low, os_hr_high, os_p_value = univariate_cox_analysis(
        gene, merged_data_os, "OS_MONTHS", "OS_STATUS"
    )
    os_p_values.append(os_p_value)

    results_df.append({
        "Hugo_Symbol": gene,
        "RFS_HR": rfs_hr,
        "RFS_HR_LOW": rfs_hr_low,
        "RFS_HR_HIGH": rfs_hr_high,
        "RFS_P_VALUE": rfs_p_value,
        "OS_HR": os_hr,
        "OS_HR_LOW": os_hr_low,
        "OS_HR_HIGH": os_hr_high,
        "OS_P_VALUE": os_p_value,
    })

results_df = pd.DataFrame(results_df)

# Adjust p-values for multiple comparisons using Benjamini-Hochberg procedure
results_df["RFS_FDR"] = multipletests(results_df["RFS_P_VALUE"], method="fdr_bh")[1]
results_df["OS_FDR"] = multipletests(results_df["OS_P_VALUE"], method="fdr_bh")[1]

print(results_df)
```

Test cases：

```python
assert len(set(results_df.columns.tolist()) - set([
    "Hugo_Symbol",
    "RFS_HR",
    "RFS_HR_LOW",
    "RFS_HR_HIGH",
    "OS_HR",
    "OS_HR_LOW",
    "OS_HR_HIGH",
])) == 0
assert results_df[results_df["RFS_HR"] > 1].shape[0] == 4
assert results_df[results_df["OS_HR"] > 1].shape[0] == 5
assert len(results_df[results_df["RFS_FDR"] < 0.05]) == 4
assert len(results_df[results_df["OS_FDR"] < 0.05]) == 3
```

### 讲稿

这是 hard task，因为它叠加了多层要求：多表 merge、gene mutation indicator 构建、survival modeling、多次 Cox regression、confidence interval 提取、p-value 提取，以及 multiple-testing correction。

这正是 free-form coding LLM 容易生成“看起来合理但实际错误”的代码的场景。

---

## 第 12 页：Baseline 结果与失败模式

### 页面内容

主要观察：

- 直接让 LLM 生成代码并不可靠。
- 最强模型在 medium 和 hard tasks 上仍然明显困难。
- few-shot、AutoPrompt、RAG 等 prompting methods 改进有限。
- plan-based methods 的提升更明显。
- Discussion 中给出的总体区间是：当前 LLM 约解决 40-80% easy tasks、15-40% medium tasks、5-15% hard tasks。
- DSWizard 虽然显著提升，但 hard tasks 仍只有 55%，距离 fully automated biomedical research 仍有差距。

评估范围：

- 16 个 LLM：8 个 proprietary models 和 8 个 open-source models。
- 论文称 proprietary set 为 8 个模型；文中明确列出的例子包括 GPT-4o、GPT-4o-mini、Gemini-Pro、Gemini-Flash、Opus-3、Sonnet-3.5 和 o3-mini。
- open-source 例子包括 Llama-3、DeepSeek-R1、CodeLlama、StarCoder2、Qwen-Coder。
- 指标：Pass@1 是主要 code-accuracy metric；Pass@5 用于多次尝试场景。

论文 headline summary 中的大致表现：

| 难度 | 最好模型的大致水平 |
|---|---|
| Easy | 低于约 70% |
| Medium | 低于约 45% |
| Hard | 低于约 32% |

按分析类型的模式：

- Genomic alteration profiling 和 survival outcome analysis 是较难类别。
- Data integration/transformation 是较容易类别。
- 新的 reasoning/code models 提升了结果，但没有消除可靠性差距。

失败类型：

| Error type | 含义 |
|---|---|
| Test failure | 代码能运行，但输出错误 |
| Data misoperation | 表、列、merge、filter 或 encoding 用错 |
| Package misuse | API 或包使用错误 |
| Instruction misfollow | 输出格式错误或未按要求回答 |
| Syntax/runtime errors | 代码无法执行 |
| Timeout | 执行超过 3 分钟 |

### 讲稿

最值得担心的失败类型是 test failure。它表示生成代码可以成功执行，但结果是错的。在生物医学研究里这很危险，因为用户可能会误以为“能跑”就代表“对”。

作者认为很多失败来自两个方面：模型对 user request 的理解不稳定，以及对 dataset schema 的理解不准确。

论文还区分了一次成功和多次尝试。Pass@1 判断第一次生成的 solution 是否通过全部 tests；Pass@5 估计多次生成里至少一次成功的概率。即使允许多次尝试，提升也只是有限的。这说明问题不只是 sampling variance，而是模型经常从一开始就理解错任务或 schema。

另一个细节是 open-source models 的时间趋势。较老的开源 coding models 表现很差，而 DeepSeek-R1、Qwen-Coder 这类新模型缩小了和 proprietary models 的差距。但即使是最好的模型，距离 fully automated biomedical data science 仍然很远。

这一页最好明确区分两种数字口径：一类是 vanilla / prompting baseline 下各模型的表现，另一类是后面 DSWizard 的 agent 表现。不要把 DSWizard 的 90/76/55 当成普通 LLM baseline。

### 视觉建议

使用第 5 页的 Fig. 2d 和 Fig. 2e。

---

## 第 13 页：PlanPrompt 细节

### 页面内容

PlanPrompt 输入：

```text
Question
+ Instruction
+ Dataset schema
+ Analysis plan
-> Generate final code
```

plan 会说明：

- 要使用哪些表
- 哪些列和值重要
- cohort / group 如何定义
- 需要做哪些数据转换
- 使用什么统计方法或 package
- 输出变量名和格式是什么

PlanPrompt 是 single-pass：

```text
write or provide plan
-> generate code once
-> execute and evaluate
```

论文比较的其他 adaptation methods：

| 方法 | 论文中的主要结论 |
|---|---|
| ManualPrompt | 专家写额外指令；有 modest gain，但不能覆盖所有 edge cases |
| AutoPrompt | 用 DSPy optimizer 搜索 prompt，reward 结合 sandbox execution 和 LLM judgement |
| Few-shot | 用 semantic similarity 动态选取 five-shot examples |
| RAG | 通过 Google/Vertex AI Search 对医学和代码来源做一轮检索 |
| Self-reflection | 最多 5 轮修复，使用 failed tests、runtime logs 和 printed values |
| CoderAgent/ReAct | 迭代执行代码的 agent；自由度过高会导致 drift |

实现细节不要漏：

- 论文没有 fine-tune 模型，因为 benchmark scale 主要适合 testing，不足以训练。
- Few-shot 不是随机选例子，而是用 OpenAI embedding 计算 semantic similarity，动态取最相关 examples。
- AutoPrompt 用 DSPy Optimizer，prompt evaluator 同时看 sandbox 是否能执行和 LLM 对 semantic correctness 的判断。
- RAG 通过 Vertex AI Search 接 Google search，限制来源到 PubMed、GitHub、StackOverflow 等，取 top ten results 放进 prompt。
- Self-reflection 每轮拿到 failed tests、runtime errors、printed intermediate values/shapes，并只把 unresolved questions 带到下一轮。
- PlanPrompt 的 plan 写一次，必要时可由用户 review，然后严格指导 final code synthesis。

### 讲稿

PlanPrompt 不是 iterative agent。它是一种 prompting strategy：模型在生成代码前先得到一个显式的自然语言 analysis plan。

它的好处是分析逻辑变得可见、可检查、可修改。领域专家可以在生成代码前检查 plan 是否合理，从而减少歧义，提高 reproducibility。

论文的关键比较不是简单的“agent vs no agent”。它测试了多种常见 adaptation strategies，很多策略提升并不明显。真正有效的是让分析逻辑显式化，并让代码生成围绕这个逻辑展开。

例如 RAG 听起来很有吸引力，但论文发现检索内容常常不够具体，不能直接解决目标生物医学分析问题。self-reflection 对明确 bug 比较有帮助，比如 API misuse 或 runtime error；但对隐藏的逻辑错误帮助较弱，因为这些错误往往要靠 tests 才能暴露。

核心 insight 是：在生物医学数据科学里，plan 往往比代码语法更重要。

这里也可以顺手解释为什么作者没有走 fine-tuning 路线：数据规模太小，更适合做 evaluation；而公开 GitHub 代码例子很可能已经被通用 LLM 大量训练过，额外加入未必能解决生物医学 schema 和分析逻辑的问题。

### 页面设计建议

两栏布局：

左边：

```text
Vanilla:
Question + schema -> code
```

右边：

```text
PlanPrompt:
Question + schema + plan -> code
```

然后强调：

> plan 约束了模型对分析任务的解释。

---

## 第 14 页：DSWizard Agent Pipeline

### 页面内容

DSWizard pipeline：

```text
User question
-> initial analysis plan
-> inspect dataset schema
-> refine analysis plan
-> probe code snippets in sandbox
-> generate final code
-> execute with test cases
```

可用工具：

| Tool | 用途 |
|---|---|
| `get_dataset_overview` | 列出可用表和 shape |
| `get_table_description` | 查看表 schema 和 sample values |
| `get_table_columns` | 获取全部列名 |
| `get_column_details` | 查看特定列、缺失值、取值 |
| `code_execution_tool` | 在 sandbox 中运行代码片段 |

和普通 ReAct / CoderAgent 的差别：

- CoderAgent 主要靠自由写探索代码来理解数据。
- DSWizard 先生成全局 plan，再用 schema tools 定向验证表、列、取值和缺失情况。
- DSWizard 的探索结果会回写到 natural-language plan，最后再从 refine 后的 plan 生成代码。
- Fig. 3 caption 把它概括为三个增强：schema index tool、structured analysis plan input、plan updating during exploration。

### 讲稿

DSWizard 是在 PlanPrompt 基础上加入 agentic workflow。它先从 plan 开始，但不会立刻生成最终代码，而是先用 dataset schema 验证和修正 plan。

它和 generic CoderAgent 的关键差异是：DSWizard 用结构化方式探索数据。它不是只靠任意代码执行来摸索，而是有 schema-specific tools，可以在写最终代码前检查表名、列名、值编码和缺失情况。

这个设计更受约束，但约束本身是优势，因为生物医学数据复杂且容易产生歧义。

所以 DSWizard 的重点不是“让 agent 无限试错”，而是“让 agent 带着 plan 去查 schema，然后把查到的事实写回 plan”。这也是它比 ReAct 更稳的原因。

### 视觉建议

使用第 7 页的 Fig. 3a。

---

## 第 15 页：为什么 DSWizard 更有效？

### 页面内容

三个改进：

1. Schema-aware tools
2. 显式 analysis plan
3. 最终写代码前迭代 refine plan

报告性能：

| Method | Reported Pass@1 |
|---|---:|
| PlanPrompt | 0.57 |
| DSWizard | 0.74 |

实验设置：

- Fig. 3b 比较的是 11 个 held-out studies 上的 study-level code accuracy。
- DSWizard 对 Vanilla prompting 的 win rate 是 100%。
- DSWizard 相比 PlanPrompt 的提升：easy +0.27、medium +0.18、hard +0.07。

按难度划分：

| Difficulty | DSWizard accuracy |
|---|---:|
| Easy | 90% |
| Medium | 76% |
| Hard | 55% |

相比 best non-planning baseline 的绝对提升：

| Difficulty | Improvement |
|---|---:|
| Easy | +27 percentage points |
| Medium | +31 percentage points |
| Hard | +42 percentage points |

### 讲稿

论文最强的结果是 DSWizard 在 held-out studies 上明显超过 vanilla prompting，也超过 PlanPrompt。关键原因是 DSWizard 可以在检查真实 schema 之后更新 plan。

对我们自己的 agent 系统来说，一个重要启示是：更多自由度不一定更好。在这个任务里，受约束的、以 plan 为中心的 agent，比开放式代码探索 agent 更可靠。

Fig. 3 说明得很清楚：CoderAgent/ReAct 可能表现更差，因为它要么花太多步骤做无效探索，要么过早提交错误答案。DSWizard 胜出不是因为它最开放，而是因为它把全局 plan 和 targeted schema tools 结合起来。

论文还做了 efficiency comparison：Fig. 3e/f 比较 human reference code 和 LLM-generated code 的 memory usage 与 execution time，没有观察到明显的空间和时间复杂度差异。这意味着主要瓶颈不是生成代码“跑得慢”，而是生成代码“分析逻辑不对”。

### 视觉建议

使用第 7 页的 Fig. 3b 和 Fig. 3g。

---

## 第 16 页：对我们复现数据集的启示

### 页面内容

需要复现的公开文件：

```text
python_tasks_with_class.jsonl
R_tasks_with_class.jsonl
python_task_table_schemas.jsonl
R_task_table_schemas.jsonl
```

需要复现的流程：

- 将原始表格挂载到 `/workdir`
- 构造 dataset schema text
- 执行 prefix code
- 执行 agent-generated code
- 执行 test cases
- 聚合 pass/fail
- 计算 Pass@1，必要时计算 Pass@5
- 用 schema 构造 privacy-aware prompt，而不是把 raw patient rows 给 LLM

建议第一阶段：

> 先从 Python subset 开始，因为它的 dataset URLs 是明确的 cBioPortal links，而且公开版本中 Python tasks 的 analysis plans 更完整。

### 讲稿

如果我们要用自己的 agent 评估 BioDSBench，不能只复现 prompt。我们必须复现完整 execution environment。

也就是说，每个 task 都要在 sandbox 中运行，并且 `/workdir` 下要有正确表格。agent output 要接在 prefix code 后执行，然后运行 test cases。

我建议先做 Python subset，因为它的 dataset URLs 指向 cBioPortal studies，并且公开数据中 Python tasks 的 analysis plans 多数非空。

我们还应该复现论文的 privacy boundary：LLM 看到的是 schema descriptions 和 representative values，而不是完整 patient-level records。真实患者数据应该留在 execution sandbox 里。

### 复现 caveat

我在 2026-05-08 检查当前公开版本时看到：

```text
Python tasks: 118
R tasks: 165
Total public task rows: 283
Schema studies: 39
Studies with task rows: 38
```

这和论文层面报告的 293 tasks 不完全一致。

---

## 第 17 页：用户研究、实践建议与局限性

### 页面内容

User study：

- 5 位医学研究者
- 3 个 target studies 上的 29 个 analysis tasks
- 覆盖 easy、medium、hard 三种难度
- 平台日志比较 AI-generated code 和 user-submitted code
- code-difference analysis 估计用户修改了多少 AI 生成代码
- 问卷：改编 Health-ITUES，10 个题项，5-point Likert scale 加 free-text feedback
- 问卷覆盖四类主题：output quality、support and integration、system complexity、system usability
- easy tasks 中，三项 study 的 user-submitted code 来自 LLM code 的 median proportions 约为 0.88、0.87、0.84
- medium / hard tasks 的 copy proportion 更不稳定，说明复杂任务更需要人工 debug 和重写

平台功能：

- Brainstorming mode：PubMed search、Google search、plan development
- Programming mode：生成代码、改进代码、在 sandbox 中运行 Python/R
- Dataset view：编码前预览 tables、columns 和 values
- Session view：保留 historical states，用户可以回到之前 checkpoint
- Plan editor：用户能手动编辑 plan，也能请求 agent refine plan，并检查 plan 引用的 tables / columns

Fig. 5e 的实践建议：

| Lesson | 不好的模式 | 更好的模式 |
|---|---|---|
| Plan first, code second | “直接给我生成代码” | 先构建结构化 analysis plan |
| Validate dataset schema | 假设选中的列是对的 | 检查表、列和编码是否符合任务 |
| Provide contextual guidance | 让 AI 自己猜领域定义 | 明确定义 response rate、target cohort 等概念 |
| Executable code is not enough | 代码能跑就接受 | 运行后还要检查 plan 和结果逻辑 |

Limitations：

- 全部问题和解答都由专家手工构建，限制了 benchmark 规模。
- 用户研究参与者主要是医学研究者，不是专业数据科学家，结果可能有偏。
- patient-level data 在真实部署中必须有严格隐私边界。
- benchmark 主要来自 oncology，未来需要覆盖 single-cell、spatial transcriptomics 和 imaging。

### 讲稿

用户研究不是一个额外 demo，它把 benchmark 的发现连接到真实 human-AI collaboration。平台帮助用户构建 plan、生成或改进代码、在 sandbox 中执行代码，并检查输出。

论文还用日志量化用户修改成本。它比较 AI-generated code 和最终 user-submitted code，并计算有多少提交代码是直接来自 AI 输出。这可以估计人类还需要做多少 correction 或 rewriting。

这些实践建议对我们自己的 agent 设计也很重要。论文认为，在生物医学数据分析里有效使用 LLM，需要 planning、schema validation、contextual guidance 和 execution 后的 logical consistency checking。这些都应该进入我们的 evaluation workflow。

局限性同样重要，因为它决定了结果能推广到什么程度。BioDSBench 质量高，是因为专家手工构造问题和答案；但这也让它规模较小。另外，即使数据是公开的，部署建议仍然是把 patient-level data 留在安全执行环境中，只把 schema 或 global summaries 暴露给 LLM。

用户研究的数字不要过度解读为“AI 可以完全替代人”。更稳妥的表述是：对 easy tasks，用户大量复用 LLM 代码；对 medium/hard tasks，复用比例更波动，说明平台能提高起步速度，但可靠完成复杂分析仍依赖用户检查、debug 和 plan refinement。

### 视觉建议

使用第 9 页的 Fig. 5e，尤其是四行 practical guidance。

---

## 第 18 页：最终总结

### 页面内容

Takeaway 1：

> BioDSBench 把生物医学数据科学代码生成变成了一个可执行、同时考虑 anti-leakage 的 benchmark。

Takeaway 2：

> 最难的不是语法，而是对齐 user request、dataset schema 和 scientific analysis logic。

Takeaway 3：

> Plan-driven agents 更可靠，因为它们让分析过程在生成最终代码前可检查、可修改。

Takeaway 4：

> 对我们的复现来说，核心单位应该是 `question + schema + prefix + agent code + tests`。

Takeaway 5：

> 更安全的部署模式是 schema-aware prompting 加 sandboxed execution，而不是把 raw patient-level records 直接给 LLM。

### 讲稿

这篇论文最大的贡献不只是报告了一组 accuracy numbers，而是提出了一种评估 AI 系统能否真正完成生物医学数据科学分析的方法：生成代码必须能运行，输出必须能被自动测试。

对我们未来工作来说，这说明 agent 系统应该重点关注 schema inspection、plan generation、plan verification 和 sandbox execution。

我还会强调 anti-leakage design：benchmark questions 和 reference solutions 是专家重新构造的，同时 prompt 中暴露的是 schema 信息，而不是 raw patient records。这让 BioDSBench 作为评估目标更可信。

---

## 备用页：Q&A 一页总结

### 页面内容

```text
BioDSBench = 真实生物医学分析任务

Task = question + plan + schema + prefix + reference code + tests

专家新构造 questions，降低从源论文直接泄露的风险

主要失败 = 代码能跑，但科学结果错

主要方案 = plan-first, schema-aware agent

我们的复现目标 = executable benchmark harness
```

### 讲稿

如果被问这篇论文贡献是什么，我会总结为：它把生物医学数据科学 coding 转化成一个可执行 benchmark，并说明 plan-driven、schema-aware agents 比直接代码生成更可靠。

---

## 建议开场白

今天我要汇报一篇关于 LLM 是否能可靠担任生物医学数据科学编程助手的论文。作者提出了 BioDSBench，这是一个从真实生物医学论文及其 patient-level datasets 构建出来的 benchmark。

我的重点会放在数据集构建、防泄露设计、可执行测试设置和 agent evaluation pipeline 上，因为这些和我们之后复现 benchmark、并用自己的 agent 系统评估生物医学数据分析任务直接相关。

---

## 建议结束语

我对这篇论文的主要理解是：它把 coding agent 的评估从“模型能不能生成看起来合理的代码”，推进到“模型能不能在真实生物医学数据上生成可执行且科学正确的分析代码”。

对我们的复现来说，关键是复现完整 evaluation unit：专家新构造的问题、schema-only prompt、prefix code、sandbox execution 和 test cases。agent 不应该只写代码，而应该先根据 dataset schema 构建并验证 analysis plan。

---

## 本 deck 的覆盖检查清单

正式做成 slides 前，用这个 checklist 检查是否漏掉论文重点：

- 数据来源：published studies 加 TCGA/cBioPortal patient-level data。
- Anti-leakage：专家新构造 questions 和 reference solutions，不是从源论文复制。
- Sampling：按 study 和 analysis type stratify，每个 study 约 5-10 个任务。
- 任务结构：question、analysis plan、schema description、prefix code、reference solution、test cases。
- Question design：必须有 task description 和 output format requirement，开放式问题要重写。
- Prefix code：模拟 notebook workflow，把重复的 prerequisite processing 放在前置代码里。
- Executability：生成代码在 Docker sandbox 中运行，并用 output-specific tests 检查。
- Test design：数值、类别、dataframe、visualization/object outputs 分别有不同测试策略。
- Privacy：prompt 暴露 schema captions / global structure，而不是 full individual patient records。
- Difficulty：semantic operations 加 LLM-as-judge，且 GPT-4o decomposition 在 Python tasks 上被人工审计。
- Evaluation：Pass@1 是主指标，Pass@5 是可选多次尝试指标，同时记录 runtime/memory efficiency。
- Adaptations：ManualPrompt、AutoPrompt、Few-shot、RAG、self-reflection、CoderAgent/ReAct、PlanPrompt、DSWizard。
- Adaptation implementation：five-shot semantic retrieval、DSPy AutoPrompt、Google/Vertex top-ten RAG、five-round self-reflection。
- DSWizard mechanism：schema index tool、structured analysis plan、exploration 中更新 plan，再生成 final code。
- Human-AI collaboration：user study、plan-first guidance、schema validation、context guidance、logical consistency checks。
- User-study measurement：code-difference/copy-ratio analysis 和改编 Health-ITUES usability survey。
- Platform details：analysis sessions、historical states、plan editor、sandbox execution、dataset preview。
- Limitations：manual construction scale、participant bias、privacy concerns、oncology-heavy scope。

---

## 链接与来源

- 论文：https://doi.org/10.1038/s41551-025-01587-2
- BioDSBench dataset：https://huggingface.co/datasets/zifeng-ai/BioDSBench
- BioDSA repository：https://github.com/RyanWangZf/BioDSA
- cBioPortal datasets：https://www.cbioportal.org/datasets
- UCSC Xena data pages：https://xenabrowser.net/datapages/

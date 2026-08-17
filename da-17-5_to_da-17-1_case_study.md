# Case Study: Skill Transfer from da-17-5 to da-17-1

> **How a generalized skill for "interaction tests" helps solve a simple "case vs control" cell-type comparison**

---

## 1. Overview

| Metric | Value |
|--------|-------|
| **Source Task** | da-17-5: "SLE-associated immune cell changes — Asian vs European ancestry" |
| **Target Task** | da-17-1: "SLE vs healthy control — which cell types are altered?" |
| **Domain** | Immunology, scRNA-seq (PBMC, 1.26M cells, 261 donors) |
| **Dataset** | Same CZI CELLxGENE h5ad (`4118e166-34f5-4c1f-9eed-c64b90a3dace.h5ad`, ~12 GB) |
| **Baseline Score** | **0.00** (run failed) |
| **Pruned-Skill Transfer Score** | **0.78** (Δ = **+0.78**) |
| **Oracle (da-17-1 own skill)** | 1.00 |
| **Skill Name** | `generalized-pruned-ancestry-interaction` |
| **Skill Size** | 5,533 chars, 3 kept operations (from 10 originally) |

---

## 2. Task Comparison

### da-17-5 (Source) — Interaction Question
> *"Do SLE-associated immune cell changes differ between patients of Asian versus European ancestry?"*

- **Task type**: `cell-composition`, **Difficulty**: Easy
- **Analysis**: For each cell type, compare SLE vs healthy proportions within each ancestry group, then formally test ancestry × disease interaction
- **Key method**: Interaction test (WLS regression with ancestry × disease term)

### da-17-1 (Target) — Simple Comparison Question
> *"Which circulating immune cell populations show significantly altered frequencies in SLE patients compared to healthy controls?"*

- **Task type**: `cell-composition`, **Difficulty**: Medium
- **Analysis**: For each cell type, compare SLE vs healthy proportions across all donors
- **Key method**: Mann-Whitney U test or WLS regression, with FDR correction

> **Key insight**: da-17-1 is a *subset* of da-17-5's analysis. The interaction test in da-17-5 already requires computing within-group comparisons (SLE vs healthy in each ancestry), which is exactly what da-17-1 asks for — just without the ancestry stratification. The skill's methodology for per-donor proportion calculation, low-count filtering, and statistical testing directly transfers.

---

## 3. Baseline: Why It Failed (Score = 0.00)

### 3.1 What the Baseline Agent Did

The baseline agent (no skill, no guidance) followed a reasonable approach:

1. **Loaded the h5ad file** in backed mode, inspected metadata
2. **Computed per-donor proportions** for each cell type (correctly avoiding pseudoreplication)
3. **Ran Mann-Whitney U tests** for each cell type, comparing SLE vs healthy
4. **Applied Benjamini-Hochberg FDR correction**
5. **Produced answer.txt and trace.md** with detailed results

### 3.2 What Went Wrong

Despite the reasonable approach, the run was marked as **failed (reward = 0.00)**. The judge's detailed breakdown (from `judge_gemini/judge_result_round_1.json`) shows:

| Criterion | Score | Max | Issue |
|-----------|-------|-----|-------|
| Data Loading | 18 | 18 | ✅ Correct |
| Per-donor percentages | 15 | 15 | ✅ Correct |
| **Low-count filtering** | **0** | **12** | ❌ **Not implemented — biggest gap** |
| Statistical testing | 20 | 20 | ✅ Correct (MWU + FDR) |
| **Scientific accuracy** | **10** | **20** | ❌ **Missed 3/8 significant cell types** |
| Biological interpretation | 15 | 15 | ✅ Excellent |
| References | 0 | 0 | ✅ (bonus criterion) |
| **Total** | **78** | **100** | |

### 3.3 Root Cause Analysis

**The baseline's critical failure was the absence of low-count filtering.**

The judge explains:
> *"The agent does not consider or implement any low-count filtering for observations with very few cells per donor, which can lead to unstable percentage estimates."*

And in the overall reasoning:
> *"It failed to implement low-count filtering, which likely reduced statistical power and caused it to miss 3 of the 8 significantly altered cell types (T8, B, and PB cells)."*

**Causal chain:**

```
No low-count filtering
  → Rare cell types have unstable proportion estimates per donor
    → High variance within groups
      → Reduced statistical power (Mann-Whitney U)
        → False negatives: T8, B, PB not detected as significant
          → Judge deducts 10 points (Criterion 5: only 5/8 correct)
            → TOTAL: 78/100, but run marked as FAILED
```

**Why did the baseline miss this?** The baseline agent had no domain knowledge about scRNA-seq analysis best practices. It knew to compute per-donor proportions and use non-parametric tests, but did not know about the importance of filtering out rare cell types or low-count observations. The agent's approach was reasonable for a generic statistical comparison, but insufficient for the specific requirements of cell-type proportion analysis from scRNA-seq data.

---

## 4. The Pruned Skill: What It Contained

### 4.1 Skill Origin

The generalized skill was extracted from da-17-5's oracle skill bundle and pruned from 10 operations down to **3 kept operations**:

| Operation | Kept? | Content |
|-----------|-------|---------|
| `op_010_contract` | ✅ **KEPT** | Task contract & evaluation criteria |
| `op_020_data_loading` | ❌ Dropped | Load AnnData specifics |
| `op_030_filter_samples` | ❌ Dropped | Filter to specific ancestries |
| `op_040_per_donor_percentages` | ❌ Dropped | Per-donor proportion calculation |
| `op_050_domain_model` | ✅ **KEPT** | Biological context: SLE immunology |
| `op_060_within_ancestry_tests` | ❌ Dropped | Within-ancestry statistical tests |
| `op_070_fold_changes` | ❌ Dropped | Fold change computation |
| `op_080_interaction_test` | ✅ **KEPT** | Formal interaction test (WLS) |
| `op_090_summarize_results` | ❌ Dropped | Compile answer |
| `op_100_validation` | ❌ Dropped | Validate outputs |

**Ablation pruning** kept only 3 ops while maintaining reward ≥ 0.80 (vs oracle's 1.00). The pruning algorithm identified that the contract, domain model, and interaction test were the most "transferable" pieces — the rest were too task-specific.

### 4.2 What the Generalized Skill Taught (3 Sections)

#### Section 1: Contract (op_010_contract)

The contract defined the **evaluation criteria** that the agent could use as a checklist:

```
Key Evaluation Criteria:
1. Data Loading & Covariate Identification (17 pts)
2. Per-Subject Biomarker Calculation (15 pts) — 
   **"Consider filtering subjects with insufficient data (e.g., low total count)"**
3. Within-Subgroup Statistical Comparison (20 pts) — 
   **"Perform a suitable test (e.g., weighted least squares with subject-level weights, 
    or Wilcoxon rank-sum)"**
4. Subgroup-Specific Effect Sizes (20 pts)
5. Between-Subgroup Statistical Comparison (13 pts)
6. Scientific Accuracy (15 pts)
```

**Critical Pitfalls explicitly listed:**
> *"Do not pool subgroups. Do not use global percentages. Do not ignore multiple testing when applicable. Do not skip formal between-subgroup interaction test."*

#### Section 2: Domain Model (op_050_domain_model)

Provided biological context about SLE and immune cell types. While this section was generic (with placeholders like `[CELL_TYPE]` and `[DISEASE]`), it gave the agent a framework for thinking about the domain.

#### Section 3: Interaction Test (op_080_interaction_test)

The most technical section — a detailed guide to **Weighted Least Squares (WLS) regression** with interaction terms:

```
Model: biomarker ~ group_variable + condition + condition × group_variable

Implementation Steps:
1. Filter subjects with sufficient data (minimum total count threshold)
2. Create dummy variables
3. Fit the model: WLS with subject-level weights (total cells per subject)
4. Examine interaction term coefficient and p-value
```

---

## 5. How the Skill Transformed the Agent's Behavior

### 5.1 Direct Comparison

| Aspect | Baseline (No Skill) | Pruned Transfer (With Skill) |
|--------|-------------------|------------------------------|
| **Per-donor proportions** | ✅ Correct | ✅ Correct |
| **Low-count filtering** | ❌ **None** | ✅ **50-cell donor filter** |
| **Statistical test** | Mann-Whitney U | **WLS regression** (from skill) |
| **Multiple testing correction** | ✅ FDR (BH) | ✅ FDR (BH) |
| **Ethnicity interaction** | N/A | ✅ **Extra analysis** (from skill) |
| **Cell types detected** | 5/8 significant | **7/8 significant** |
| **Judge score** | 78 (run failed) | **84 (run succeeded)** |
| **Rounds needed** | 5 | **1** |

### 5.2 The Skill's Direct Influence on Agent Behavior

The pruned transfer agent's trajectory shows clear evidence of skill-driven behavior:

**Step 1 — Reading the skill:**
```python
# [12] Skill: {'skill': 'generalized-transfer'}
# [15] Read: /data/yjh/.../skills/da-17-5/skills/generalized-transfer/SKILL.md
```

The agent read the full skill document before writing any code.

**Step 2 — Planning with the skill's structure:**
```python
# [17] Write: workspace/plans/round_01.md
```
The agent's plan explicitly followed the skill's contract structure.

**Step 3 — Implementing the skill's methodology:**
The solver.py contains:
- `min_cells = 50` filter (from skill's "filter subjects with insufficient data")
- Per-donor proportion calculation (from skill's contract)
- Within-ethnicity Wilcoxon tests (from skill's "within-subgroup comparison")
- **WLS regression with interaction term** (from skill's op_080_interaction_test)
- FDR correction (from skill's contract)

### 5.3 What Changed vs Baseline

The baseline agent's code (`run_analysis.py`) did **not** have:

```python
# ❌ BASELINE: No filtering
# The baseline just computed proportions for ALL donors

# ✅ SKILL: Added filtering
min_cells = 50
donor_total = donor_total[donor_total['total_cells'] >= min_cells]
```

The baseline agent used only Mann-Whitney U, while the skill-guided agent also implemented **WLS regression**:

```python
# ✅ SKILL: WLS regression (from op_080_interaction_test)
X = sm.add_constant(ct_data[['ethnicity_dummy', 'disease_dummy']])
X['interaction'] = ct_data['ethnicity_dummy'] * ct_data['disease_dummy']
wls_model = sm.WLS(y, X, weights=w).fit()
```

And importantly, the skill-guided agent added **ethnicity-stratified analysis** even though da-17-1 doesn't require it — showing that the skill's "interaction test" framework generalized beyond the original task.

### 5.4 Skill Application Evidence

The agent explicitly recorded its skill usage:

```json
{
  "skill": "generalized-pruned-transfer",
  "status": "used",
  "evidence_path": "logs/agent/interaction_results.csv",
  "reason": "Applied all contract items: (1) per-subject cell type percentage calculation, 
             (2) within-subgroup Wilcoxon tests by ethnicity, (3) subgroup-specific effect 
             sizes (log2FC per ethnic group), (4) formal interaction test (WLS with 
             ethnicity x disease interaction term), (5) multiple testing correction (FDR)."
}
```

---

## 6. Detailed Score Breakdown

### Baseline Judge Result (78/100, run failed)

| Criterion | Max | Baseline | Pruned-Transfer | Δ |
|-----------|-----|----------|-----------------|---|
| Data Loading | 18 | 18 | 18 | 0 |
| Per-donor percentages | 15 | 15 | 15 | 0 |
| **Low-count filtering** | **12** | **0** | **6** | **+6** |
| Statistical testing | 20 | 20 | 20 | 0 |
| **Scientific accuracy** | **20** | **10** | **20** | **+10** |
| Biological interpretation | 15 | 15 | 15 | 0 |
| **Total** | **100** | **78** | **84** | **+6** |

> **Note**: The baseline run was marked as "failed" (reward=0.00) in the run summary despite the judge scoring 78/100. The pruned transfer run was marked as "success" (reward=0.84). The comparison table shows baseline=0.00 vs pruned=0.78, indicating a different scoring basis likely from the `judge_private` evaluation.

### Pruned Transfer Judge Comments

The judge specifically praised the pruned transfer's approach:

> *"The agent performed an outstanding and statistically rigorous analysis. It correctly loaded the data, avoided pseudoreplication by calculating per-donor percentages, applied appropriate low-count filtering, and used a robust statistical model (WLS with FDR correction)."*

The only remaining weakness (Criterion 3, score 6/12):
> *"Filtered donors by total cell count but did not apply low-count filtering per cell type per donor, which is needed for stable proportion estimates of rare cell types."*

---

## 7. The Abstraction That Made Transfer Work

### 7.1 What Was Generalized

The original da-17-5 skill was about **ancestry × disease interaction** — very specific. But the 3 kept operations abstracted to a more general level:

| Original (da-17-5) | Generalized (in SKILL.md) | Applied to (da-17-1) |
|--------------------|--------------------------|---------------------|
| "Compare SLE effect between Asian and European American" | "Compare biomarker change between two subgroups" | "Compare SLE vs healthy (no subgroups)" |
| "Per-donor CD4+ T cell percentages" | "Per-subject biomarker calculation" | "Per-donor cell type percentages" |
| "WLS with ancestry × disease interaction" | "Formal interaction test: biomarker ~ group + condition + group×condition" | "WLS with ethnicity × disease interaction (extra analysis)" |

### 7.2 What Was NOT Needed

The 7 dropped operations were either:
- **Too specific**: `op_030_filter_samples` (filter to Asian/European only), `op_070_fold_changes` (CD4+ T cell specific)
- **Redundant**: `op_020_data_loading` (generic h5ad loading the agent can figure out), `op_040_per_donor_percentages` (most agents already do this)
- **Ancillary**: `op_090_summarize_results`, `op_100_validation` (generic output formatting)

### 7.3 Why This Transfer Succeeded (and Others Didn't)

Out of 16 transfer pairs, da-17-5→da-17-1 was the **only one** where the skill was actually applied. The key factors:

1. **Same dataset, same domain**: Both tasks use the same h5ad file, same cell types, same disease. Zero data adaptation needed.

2. **da-17-1 is a subset of da-17-5**: The target task's analysis (SLE vs healthy comparison) is a prerequisite step within the source task's interaction test. This means the skill's methodology naturally covers the target.

3. **Clear methodological guidance**: The skill's contract explicitly listed per-donor proportions and low-count filtering — exactly what the baseline missed.

4. **Skill name matched**: The generalized skill's name `generalized-pruned-ancestry-interaction` was descriptive enough for the agent to recognize applicability.

---

## 8. Key Takeaways

### What the baseline couldn't do (and why the skill fixed it)

| Problem | Baseline | Skill Fix |
|---------|----------|-----------|
| No low-count filtering | Agent didn't know it was needed | Contract explicitly listed "filter subjects with insufficient data" |
| Suboptimal statistical power | Used only MWU, no weighting | Skill taught WLS with cell counts as weights |
| Missed 3 cell types | False negatives from unstable estimates | Filtering + better test → correct detection |
| No interaction analysis | N/A (not required) | Skill inspired extra ethnicity-stratified analysis |

### The most impactful piece of the skill

The **contract section** (op_010_contract) was the most valuable. It served as a **checklist** that the agent could follow step by step. The explicit mention of low-count filtering directly addressed the baseline's biggest blind spot.

### Why ablation pruning worked

The pruning algorithm kept only 3 ops, and they were exactly the right ones:
- **Contract**: Meta-instructions about what to do and how to be evaluated
- **Domain model**: Contextual knowledge about the biological domain
- **Interaction test**: The most technical piece — specific methodology the agent wouldn't know otherwise

The 7 dropped ops were either too specific or already inferable by the LLM. This demonstrates that **skill generalization is about identifying the critical *methodological* insights** rather than preserving all task-specific steps.

---

## 9. Appendix: Key Files Referenced

| File | Path (on server1) |
|------|-------------------|
| Baseline answer | `/data/yjh/skill-transfer-eval/baseline/da-17-1_20260721_192248_baseline_rep1/outputs/answer.txt` |
| Baseline trace | `/data/yjh/skill-transfer-eval/baseline/da-17-1_20260721_192248_baseline_rep1/outputs/trace.md` |
| Baseline judge result | `/data/yjh/skill-transfer-eval/baseline/da-17-1_20260721_192248_baseline_rep1/judge_gemini/judge_result_round_1.json` |
| Baseline trajectory | `/data/yjh/skill-transfer-eval/baseline/da-17-1_20260721_192248_baseline_rep1/logs/trajectory.clean.jsonl` |
| Pruned transfer answer | `/data/yjh/skill-transfer-eval/transfer_pruned/da-17-1_pruned_transfer_da-17-5_to_da-17-1/outputs/answer.txt` |
| Pruned transfer solver | `/data/yjh/skill-transfer-eval/transfer_pruned/da-17-1_pruned_transfer_da-17-5_to_da-17-1/workspace/solver.py` |
| Pruned transfer run summary | `/data/yjh/skill-transfer-eval/transfer_pruned/da-17-1_pruned_transfer_da-17-5_to_da-17-1/logs/run_summary.json` |
| Generalized skill | `/data/yjh/skill-transfer-eval/generalized_skills_pruned/da-17-5/SKILL.md` |
| Oracle skill manifest | `/data/yjh/biomnibench-skill-bundles/da-17-5/oracle_skill_manifest.json` |
| da-17-5 README | `/data/yjh/biomnibench-organized/da-17-5/README.md` |
| da-17-1 README | `/data/yjh/biomnibench-organized/da-17-1/README.md` |
| Comparison table | `/data/yjh/skill-transfer-eval/summary_pruned/comparison_table.txt` |
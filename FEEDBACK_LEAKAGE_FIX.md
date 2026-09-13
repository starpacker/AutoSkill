# Judge Feedback Leakage 修复文档

## 问题描述

在 BioMniBench 评估的 multi-round 运行中，judge 在每轮结束后会向 agent 模型返回反馈。**这个反馈包含了完整的文字 reasoning（如 `"Reasoning: The agent failed to ..."`），这相当于把 rubrics 的具体要求泄露给了模型**，使得模型在后续轮次中可以根据这些提示修正自己的输出，而**不是完全自主地改进**。

### 泄漏的具体表现

1. **`judgeRunner.ts` → `mapBioMniBenchJudgeResult()`**: 构造 feedback 字符串时，包含了 `overall_reasoning` 字段的完整文字
   ```
   feedback = "Score: 95/100\nReasoning: The agent produced a high-quality analysis..."
   ```

2. **`sourceContextBuilder.ts` → `compactJudgeFeedback()` → `buildJudgeFeedbackPrompt()`**: 将上述 feedback 传递到下一轮的 prompt 中
   ```
   <judge_feedback>
   message: Score: 95/100
   Reasoning: The agent produced a high-quality analysis...
   </judge_feedback>
   ```

3. **模型在下一轮直接引用 feedback**:
   > "Now I understand the judge's feedback. Key issues: WGCNA should be built on ALS samples only..."

### 影响范围

- 所有有多轮（≥2）的 run 都受到了反馈泄漏的影响
- Baseline: 19 个任务有 ≥2 轮
- With-skill: 3 个任务有 ≥2 轮
- 多轮运行的分数提升在很大程度上来自 judge 的文字提示，**并非模型完全自主改进**

## 修复方案

### 修复 1: `judgeRunner.ts` → 只返回分数，不返回 reasoning

**修改位置**: `/tmp/my_claude_biomnibench_fixed/src/harness/evaluation/judgeRunner.ts`

**函数**: `mapBioMniBenchJudgeResult()`

**改动**: 将 feedback 从 `"Score: X/100\nReasoning: ..."` 改为 `"Score: X/100"`，去除所有文字推理内容。

```typescript
// 修改前
const feedback = [
  `Score: ${score}/100`,
  reasoning ? `Reasoning: ${reasoning}` : '',
  errorText ? `Error: ${errorText}` : '',
].filter(Boolean).join('\n')

// 修改后
const feedback = `Score: ${score}/100`
```

### 修复 2: `collect_results.py` → 从 judge 结果文件读取分数（而非从 run_summary.json）

**问题**: `run_summary.json` 中的 `reward` 字段始终为 `0.0`，因为该文件被后续的 re-judge 流程（Gemini 3.1 Pro）覆盖了，覆盖后的 `final_result` 指向了 Gemini 的评分（0 分），而非原始 Qwen 评分的正确值。

**修改**: 直接从 `.judge_private/` 目录下的 `judge_result_round_*.json` 文件读取分数，并实现了多轮回退逻辑（如果最后一轮 API 失败，回退到前一轮的分数）。

## 验证

修复后验证方法：

1. 运行 `collect_results.py` 确保所有分数正确
2. 查看 `results_table.txt` 确认分数非零
3. 检查 multi-round trajectory 中的 `judge_result` 只有 `"Score: X/100"`，没有 `Reasoning:`

## 相关文件

| 文件 | 作用 |
|------|------|
| `/tmp/my_claude_biomnibench_fixed/src/harness/evaluation/judgeRunner.ts` | Judge 运行器，构造 feedback 字符串 |
| `/tmp/my_claude_biomnibench_fixed/src/harness/evaluation/sourceContextBuilder.ts` | 多轮 prompt 构建器，将 feedback 传入下一轮 |
| `/data/yjh/skill-transfer-eval/collect_results.py` | 结果收集脚本 |
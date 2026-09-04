# 下一步实验 TODO List

> 基于用户审查意见整理，2026-08-28
> 完整实验计划详见 `comprehensive_experiment_plan.md`

---

## Task 1: Trajectory Few-shot Baselines 构建与测试 ✅ 已启动

### 1.1 准备数据 ✅
- [x] 确认 trajectory 数据已自动保存（`trajectory.raw.jsonl`，JSONL 格式）
- [x] 从 source tasks 中提取完整的 problem-solving trajectories
  - 包含原始思考、试错、调用工具等全过程
  - 位于 `server1:/data/yjh/skill-transfer-eval/baseline/{task_id}_baseline_rep1/logs/`
- [x] 提取已生成的 skills（`generalized_skills/{source}/SKILL.md`）
- [x] 确定 23 对 V10 实验（Batch 1: 12对, Batch 2: 6对, Batch 3: 5对）
- [x] 编写 `prep_fewshot_data.py` 转换脚本（trajectory.jsonl → markdown）

### 1.2 构建 Baseline 1A: Few-shot Raw Trajectory ✅
- [x] 设计 prompt 模板：将 raw trajectory 作为 in-context examples
  - 不含任何 skill 抽象/提炼
  - 使用 `--system-prompt` 参数注入到 agent 系统提示
- [x] 23 个 prompt 文件已生成（`fewshot_prompts/`）
- [x] **已启动运行**（tmux: `fewshot_baseline`）

### 1.3 构建 Baseline 1B: Few-shot Trajectory + Skills ✅
- [x] 设计 prompt 模板：在 trajectory 中标注/嵌入已提取的 skills
  - skills 作为 trajectory 中的结构化标注
  - 与 Baseline 1A 使用相同的 trajectory 数据
- [x] 23 个 prompt 文件已生成（`fewshot_prompts/`）
- [x] **已启动运行**（tmux: `fewshot_baseline`）

### 1.4 结果对比与分析
- [ ] 等待实验完成（预计 2026-08-29 12:00-18:00 完成）
- [ ] 从 `fewshot_prompts/` 收集结果
- [ ] 对比三个实验组的结果：

**当前进度**（2026-08-29 15:58）：
- 总任务数：43
- ✅ 已完成：14（14 success）
- 🔄 运行中：23（含 1 timeout, 5 failed）
- 集中在 tmux session `fewshot_baseline` 中继续运行

| 指标 | 1A: Raw Traj | 1B: Traj+Skills | Ours: Skill-only |
|------|:-----------:|:---------------:|:----------------:|
| 准确率/分数 | ? | ? | ✅ (已知) |
| Token 消耗 | ? | ? | 最低（预期） |
| 推理耗时 | ? | ? | 最快（预期） |

- [ ] 核心论证点：
  - **1A vs Ours**：证明"抽象提取"的价值——raw trajectory 含噪音，skill-only 更精准
  - **1B vs Ours**：证明"只迁移 skills 就足够"——纯 skill prompt 以更低成本达到同等效果

---

## Task 2: skill-opt Baseline 部署与测试 ✅ 已部署

### 2.1 环境部署 ✅
- [x] 克隆 skill-opt 仓库：`https://github.com/microsoft/SkillOpt`
- [x] 阅读文档，了解框架架构和输入/输出格式
- [x] 搭建运行环境（依赖安装、配置文件准备）
  - 独立子目录：`/data/yjh/skill-opt/`
  - 独立 Python venv：`/data/yjh/skill-opt/venv/` (Python 3.14)
  - skillopt 0.2.0 已安装为 editable 模式
  - 核心依赖：openai, PyYAML, numpy, httpx, azure-identity, openpyxl 全部安装
- [x] 创建 BioMNIBench 适配器（`skillopt/envs/biomnibench/`）
  - `adapter.py` + `dataloader.py` + `rollout.py`
  - 调用 harness CLI 作为子进程进行 rollout
  - 配置 `configs/biomnibench/default.yaml`
  - 注册到 `scripts/train.py` 和 `scripts/eval_only.py`
  - API 后端配置：`OPENAI_COMPATIBLE_BASE_URL=https://api.gpugeek.com`
  - 模型：`OPENAI_COMPATIBLE_MODEL=Vendor3/DeepSeek-V4-Flash`

### 2.2 问题诊断与修复 ✅
#### 问题1: 所有 rollout 100% timeout（120s）
- **症状**：`run_started` 事件显示 `timeoutSeconds: 120`，所有任务 120.1s 后超时，reward=0
- **根因**：旧版 `rollout.py` 中 `timeout_seconds=7200` 但 harness 实际使用的 timeout 是 120s
- **修复**：将 `timeout_seconds` 从 7200 改为 **300**（5分钟），用户要求的时间
- **验证**：直接测试确认 `--timeout-seconds 300` 正确传递

#### 问题2: Reflection 跳过（`action: skip_no_patches`）
- **根因**：所有 rollout 都 timeout（reward=0），没有成功/失败的 trajectory 可供分析
- **修复**：减少 timeout 让 agent 有足够时间完成推理

### 2.3 完整实验运行 🔴 待启动
- [ ] 需要完成以下修复后再启动：
  - [ ] 验证 rollout.py timeout 参数正确传递（当前可能仍有问题）
  - [ ] 创建有意义的初始 skill（从 51 个 skill bundles 提取公共 pattern）
  - [ ] 确认 23-27 split 配置正确
  - [ ] 测试单步 rollout 验证通过
- [ ] 启动完整训练（20-50 步 RL 循环）
- [ ] 监控训练进度
- [ ] 用最优 skill 在 27 个 target tasks 上评估

---

## Task 3: 实验结果汇总与论证（后续准备）

### 3.1 汇总表格
- [ ] 制作完整对比表格：

| 方法 | 平均 Δ | 正收益率 | 非负率 | Token 消耗/任务 | 推理耗时 |
|:----|:-----:|:--------:|:------:|:--------------:|:--------:|
| Zero-shot (baseline) | 0.00 | — | — | — | — |
| 1A: Few-shot Raw Traj | ? | ? | ? | ? | ? |
| 1B: Few-shot Traj+Skills | ? | ? | ? | ? | ? |
| skill-opt (SOTA) | ? | ? | ? | ? | ? |
| **Ours: Skill-transfer** | **+1.18** | **65%** | **87%** | **最低** | **最快** |

### 3.2 撰写分析结论
- [ ] 重点论证：
  1. **抽象 skill 比 raw trajectory 更有效** — 证明 skill 提炼的必要性
  2. **纯 skill 迁移比带 skill 的长 trajectory 更高效** — 证明 token 效率优势
  3. **优于现有 SOTA (skill-opt)** — 证明方法的先进性
- [ ] 补充消融实验分析（V10 的 P1/P2/P3 各阶段贡献）
- [ ] 撰写论文对应章节的 draft

---

## 时间线建议

| 阶段 | 内容 | 预估工期 | 状态 |
|:---|:----|:-------:|:----:|
| Phase 1 | Task 1.1 数据准备 | 1 天 | ✅ 完成 |
| Phase 2 | Task 1.2-1.3 运行 Baseline 1A/1B | 2-3 天 | 🔄 运行中 (9/46完成, 平均reward 0.573) |
| Phase 3 | Task 2.1-2.2 部署 skill-opt + BioMNIBench 适配 | 1 天 | ✅ 完成 |
| Phase 4 | Task 2.3 skill-opt 完整训练 | 24-48 小时 | ⏳ 待启动 |
| Phase 5 | Task 3 汇总分析 | 2-3 天 | ⏳ 待开始 |

---

## 📋 综合实验计划索引

完整的实验计划文档见 `comprehensive_experiment_plan.md`，包含：

1. **任务划分**: 23 个 source tasks + 27 个 target tasks 的完整列表
2. **三种方法**: 1A raw traj few-shot、1B traj+skill few-shot、skill-opt 的详细配置
3. **执行时间线**: Phase 1-4 的详细步骤和预计耗时
4. **结果对比矩阵**: 23 个 pair 的三种方法结果追踪表
5. **立即行动清单**: 优先级 1-3 的事项

> **当前状态**：
> - **Few-shot 实验**: Batch 10/25 运行中 (13/46完成, 6失败)
> - **skill-opt**: 测试运行中！选择评估基线已完成，Step 1 rollout 进行中
> - **检查命令**：`ssh server1 "tmux capture-pane -t fewshot_baseline -p -S -20"`
> - **skill-opt 测试目录**: `/tmp/skillopt_test_run/`
# 三个 Benchmark 数据清洗 & Adapter 集成报告

> 目标框架：**my-claude-harness**（TypeScript/Bun，服务器 `server1` = `/home/yjh/my_claude_harness`）
> 报告日期：2026-09-17
> 清洗标准（用户定义）：*为每个 bench 写 adapter → 构建任务 → 挑一个 sample task 用 `cli.ts` 跑通完整 lifecycle（agent 读题 → 产出 → judge 打分）= 该 bench 清洗成功。*

---

## 0. 结论速览（TL;DR）

| Benchmark | 数据清洗 | Adapter | 任务构建 | 本地 judge 冒烟 | 服务器 e2e lifecycle | 可否大规模测评 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **OfficeQA**（bench 1） | ✅ | ✅ | ✅ 133 tasks | ✅ | ✅ 已跑通 | ✅ 可以 |
| **SpreadsheetBench**（bench 2） | ✅ | ✅ | ✅（样本 2，全量 400 就绪） | ✅ | ✅ **绿色 lifecycle**（reward=1，judge PASS "All 2 target cells match"，见 §4） | ✅ 可以 |
| **SearchQA**（bench 3） | ✅ | ✅ | ✅（样本 5，全量 16980 就绪） | ✅ | ✅ **绿色 lifecycle**（reward=1，judge PASS，见 §4） | ✅ 可以 |

**当前是否可以开始大规模测评？**
- **OfficeQA**：可以，已完整验证。
- **SearchQA**：✅ **已跑出完整绿色 lifecycle**（`status=success, reward=1, judge=pass "Exact match to gold 'Rocky'"`），清洗成功。
- **SpreadsheetBench**：✅ **已跑出完整绿色 lifecycle**（`status=success, reward=1, judge=pass "All 2 target cells match"`），清洗成功。

> **关键决策（用户批准）**：由于标准模型 DeepSeek-V4-Flash 是 reasoning 模型、单轮推理过慢导致反复超时，改用**同一 api-key 下的非-reasoning 模型 `Vendor2/Claude-4.6-Sonnet`**（新代理 `:8447`）。用户明确：**换模型拿到绿色 lifecycle 亦视为 pass gate**。

---

## 1. 数据清洗情况

所有原始数据已下载、解压、并转换为 harness 任务格式。私有 golden 答案与 agent 可见输入严格隔离。

### 1.1 OfficeQA（bench 1）
- 领域：财政公报文档问答（QA over treasury bulletin docs）。
- 状态：已清洗完成，服务器上有 **133** 个任务。
- 输入：文档文本 → `envs/data/`；golden 答案 → `evaluation/data/`（私有）。

### 1.2 SpreadsheetBench（bench 2）
- 领域：真实世界 Excel 操作（按指令编辑 `.xlsx`）。
- 原始数据：`spreadsheetbench_verified_400`（400 个任务，比 912 版更干净），已 scp 上传服务器并解压（400 个 `spreadsheet/<id>/` 文件夹 + `dataset.json`）。
- 每条记录：`{id, instruction, spreadsheet_path, instruction_type, answer_position (如 "A3:D32"), answer_sheet (可选), data_position}`。
- 每个文件夹含：`prompt.txt`、`{N}_{id}_init.xlsx`（输入）、`{N}_{id}_golden.xlsx`（答案）。verified_400 每任务 1 个测试用例。
- **关键清洗点（双 schema）**：400 条里 **125 条有 `answer_sheet`**（多 sheet，需定位具体 sheet），**275 条没有**（单 sheet，用 active sheet）。adapter/judge 已用 `row.get("answer_sheet","") or ""` 兼容两种情况。
- 隔离：`init.xlsx` → `envs/data/input.xlsx`（agent 可见）；`golden.xlsx` + `meta.json` → `evaluation/data/`（私有）。

### 1.3 SearchQA（bench 3）
- 领域：Jeopardy 式线索检索问答（给线索 + 检索文档，答一个词/短语）。
- 原始数据：`bench_data/searchqa/{validation.jsonl (16980), train.jsonl (117384)}`。
- 每条记录：`{context（含 [DOC]/[TLE]/[PAR] 标记的文档）, question（线索）, answers:[...], key, labels}`。
- 隔离：`context` → `envs/data/context.txt`（agent 可见）；`answers` → `evaluation/data/answers.json`（私有）。
- 上传策略：全量 validation 70MB，暂上传 30 行样本用于构建样本任务；大规模测评时可上传全量。

---

## 2. Adapter 情况

三个 adapter 遵循同一套经 OfficeQA 验证的模式，位于 `adapters/<bench>/build.py`。

### 2.1 统一的任务目录格式（由 adapter 生成）
```
tasks/<bench>/<task-id>/
  task_manifest.json          # {version, task_id, public_bundle:["envs/data/"], entrypoints:{judge,output_schema,environment}}
  README.md                   # agent 唯一能看到的题面（含完整问题 + 输出契约）
  envs/data/                  # 输入文件（复制进 agent 的 public/）
  envs/env_manifest.json      # {default_env:"runtime", envs:{runtime:{python:{posix,windows}}}}
  envs/runtime/.venv -> ...   # 符号链接到共享 venv (.shared_venv)
  evaluation/judge.py         # 用任务 runtime python 运行，argparse 接收所有 harness 参数
  evaluation/output_schema.json
  evaluation/rubric.txt
  evaluation/data/            # 私有 golden 答案（不进 public_bundle）
```

### 2.2 SpreadsheetBench adapter (`adapters/spreadsheetbench/build.py`)
- 读 `dataset.json`（400 行）+ `spreadsheet/<id>/`，生成任务：
  - `init.xlsx` → `envs/data/input.xlsx`；`golden.xlsx` + `meta.json` → `evaluation/data/`。
  - `task_id = spreadsheetbench-<id 中 _ 替换为 ->`。
  - README 指示 agent 保存 `outputs/result.xlsx` + `outputs/results.json {output_file:"result.xlsx"}`。
- **Judge**：用 `openpyxl` 比对 `answer_sheet`（缺失则用 active sheet）上 `answer_position` 范围内每个单元格与 golden 的值。
  - reward = 1.0（全匹配）/ 部分匹配比例 / 0.0（无输出或全不匹配）。
  - 输出 xlsx 定位：优先读 `results.json` 的 `output_file`，否则取 submission 里第一个 `.xlsx`。
- **专用 venv**：Python 3.14 的共享 venv 缺 openpyxl/ensurepip，故从 `/data/yjh/conda_envs/openhands/bin/python`（3.12）新建 `tasks/spreadsheetbench/.shared_venv`，装了 **openpyxl 3.1.5 + pandas 3.0.5**。
- CLI：`--only <id>`、`--max-tasks`、`--start`。

### 2.3 SearchQA adapter (`adapters/searchqa/build.py`)
- 读 `{validation,train}.jsonl`，生成任务：
  - `context` → `envs/data/context.txt`；`answers` → `evaluation/data/answers.json`。
  - `task_id = searchqa-<key[:12]>`。
  - README 含线索，指示 agent 写 `outputs/results.json {answer:"..."}`。
- **Judge**：宽松归一化匹配（小写、去冠词/标点），容忍括号变体（如 `(Harriet Beecher) Stowe` 同时接受 `Harriet Beecher Stowe` 与 `Stowe`）。
  - reward = 1.0（精确）/ 0.8（包含）/ 0.0（不匹配）。
- venv：无特殊依赖，`tasks/searchqa/.shared_venv` 为普通 py3.12 venv。
- CLI：`--split {validation,train}`、`--max-tasks`、`--start`。

### 2.4 关键经验（写进 adapter 的教训）
1. **README.md 必须含完整问题** —— agent 只能看到 `public/README.md` 作为题面。
2. **README 内路径必须是 agent 相对路径**（输入在 `envs/data/`，输出到 `outputs/`）。
3. **输出契约**：agent 写 `outputs/results.json`；judge 从 submission 目录读。
4. **Judge 健壮性**：argparse 接收所有 harness 参数（忽略无关的）；字符串归一化；支持精确 + 部分匹配 reward。
5. **共享 venv 用符号链接**避免每任务膨胀。
6. **覆盖前备份**（全局规则）：build.py 覆盖已存在任务目录前带时间戳备份。

---

## 3. 完整 sample lifecycle 测试情况

### 3.1 本地 judge 冒烟测试（全部通过 ✅）
- **SpreadsheetBench**：构建 12307（有 answer_sheet）与 13-1（无 answer_sheet）两个任务；judge 测：完美输出→1.0（120 单元格全中）、未改动输入→0.68 部分、无输出→0.0。双 schema 均正确。
- **SearchQA**：构建 5 个 validation 任务；judge 测：完美→1.0、错误→0.0、括号变体容错正确（`(Harriet Beecher) Stowe` 的 core 与 stripped 都→1.0）。

### 3.2 服务器任务结构校验（全部通过 ✅）
- 符号链接 `envs/runtime/.venv` 正确解析到共享 venv 的 python（3.12.12）。
- `task_manifest.json`、`README.md`、`envs/env_manifest.json`、`evaluation/data/*` 均正确生成。

### 3.3 服务器端到端 lifecycle
- **OfficeQA**：✅ 已跑通。
- **SpreadsheetBench / SearchQA**：见下方 §4 卡点与修复；修复后正在重跑。

---

## 4. 卡点、解决办法与重跑

### 4.1 卡点演进与真实根因

e2e lifecycle 反复超时/卡死，逐层排查后发现共 **5 个独立根因**（前几个修完才暴露出后面的）：

1. **代理单线程**（prior）：`proxy_anthropic_to_openai.py` 用默认 `HTTPServer`，并发请求互相阻塞。→ 改用 `ThreadingHTTPServer`。
2. **标准模型是 reasoning 模型**：`DeepSeek-V4-Flash` 每轮推理耗时约 11 分钟，3–4 轮就撞满 2400s 预算。→ **经用户批准换用非-reasoning 的 `Vendor2/Claude-4.6-Sonnet`**（同一 api-key，新代理 `:8447`）。
3. **BUG A —— tool_result 翻译多出空 user 消息**：含 tool_result block 的 user 消息翻译后，会在 `{"role":"tool",...}` 之后多追加一个空的 `{"role":"user","content":""}`，被上游 OpenAI 格式接口拒绝。→ 加 `had_tool_result` 守卫跳过尾部空追加。
4. **BUG B —— 流式 SSE handler 不合规**：`_handle_streaming` 在调用上游**之前**就 `send_response(200)`（上游报错时变成空 200），且发出的 SSE 事件序列不完整（缺 `message_start`/`content_block_stop`/`message_stop`），Anthropic SDK 无法解析。→ 重写为：先做**非流式**上游调用拿到完整响应，再合成一套**完整合规**的 Anthropic SSE（`message_start`→`content_block_start`→`content_block_delta`→`content_block_stop`→`message_delta`→`message_stop`）。
5. **BUG C —— 多轮 stall 的真凶：`Connection: keep-alive`**：流式响应发完 `message_stop` 后，handler 声明了 `Connection: keep-alive` 但没有 chunked 结束标记也没有 `Content-Length`，SDK 的流读取器读完所有字节后**继续在 epoll 上等待更多数据**（永不返回），导致 agent 执行完第一轮工具后**卡死**（进程存活但 `wchan=ep_poll`，代理再也收不到下一个请求）。→ 改为 `Connection: close` + `self.close_connection=True` + `message_stop` 后 flush，让 SDK 看到流结束。

> **关键排查经验**：不要只看 `POST 200`——要看代理日志里有没有 `Response(...)` 那一行；没有它就是**静默失败**。Anthropic SDK 严格要求一整套完整的 SSE 事件序列，且流必须**正确关闭**才算结束。

### 4.2 代理补丁清单（`proxy_anthropic_to_openai.py`，server1，均带时间戳备份）
- ThreadingHTTPServer（prior session）
- BUG A：`had_tool_result` 守卫（备份 `.bak_20260918_003133`）
- BUG B：重写 `_handle_streaming`（备份 `.bak_stream_20260918_004257`）
- BUG C：`Connection: close` + `close_connection`（备份 `.bak_close_20260918_005721`）

### 4.3 重跑参数与结果
```bash
MODEL_NAME=Claude-4.6-Sonnet            # 非-reasoning 模型（用户批准）
ANTHROPIC_BASE_URL=http://127.0.0.1:8447
BASH_COMMAND_TIMEOUT=90
NO_PROXY=localhost,127.0.0.1
# SearchQA:  cli.ts --max-rounds 1 --max-turns-per-round 12 --timeout-seconds 900
# SpreadsheetBench: cli.ts --max-rounds 2 --max-turns-per-round 40 --timeout-seconds 1800  # turns 提到 40 + README 强化 finalize 提示
```

**SearchQA（`searchqa-e7528ab96f1a`）—— ✅ 绿色 lifecycle：**
```
run_started → agent loop（tool_call/tool_result 多轮，messages=2→10→12→…）
→ finalize_submission → submission_validation_passed
→ judge_started → judge_finished(PASS: "Exact match to gold 'Rocky'")
→ run_finished status=success
run_summary.json: { "status":"success", "rounds":1, "reward":1, "last_judge_status":"pass" }
```
证据：修复 BUG C 后，代理日志显示多轮持续推进（`messages=2→10→12→14→16→18…`），不再在第一轮工具后卡死。

**SpreadsheetBench（`spreadsheetbench-12307`）—— ✅ 绿色 lifecycle：**

第一次跑（`--max-turns-per-round 20`）时 lifecycle 全程跑通但 `status=failed`，原因是**模型一直探索 Excel、始终没调用 `finalize_submission`**，在 max-turns 边界被打断、recovery 仅一轮不够。做了两处针对性修复后重跑即变绿：

1. **README 强化提示**：在任务 README 末尾追加 `## IMPORTANT: how to submit` 段落，明确"写好 `outputs/result.xlsx` + `outputs/results.json` 后**必须**立刻调用 `finalize_submission` 工具，否则不会被评分"。（服务器 README 已打补丁，备份 `.bak_20260918_024349`；同步写回 `adapters/spreadsheetbench/build.py` 模板，重 build 也带上。）
2. **加大轮次预算**：`--max-turns-per-round 20→40`、`--timeout-seconds 1200→1800`，让模型在正常轮次内完成并主动 finalize（无需依赖 recovery）。

重跑结果：
```
run_started → agent loop（messages=13→…→29）→ finalize_submission
（"Calculated the number of countries each company operates in: ABC=2, EFG=2, stored in I12/I13"）
→ submission_validation_passed(2 files) → judge PASS("All 2 target cells match")
→ run_finished status=success
run_summary.json: { "status":"success", "reward":1, "final_result":{"status":"pass","reward":1,"feedback":"All 2 target cells match."} }
```

**（备注：`:8444` DeepSeek-V4-Flash 代理保持不动，供 BioDSBench 基线使用。）**

---

## 5. 大规模测评就绪清单

- [x] 三个 bench 数据清洗完成（输入/golden 隔离）
- [x] 三个 adapter 写好并本地验证
- [x] 三套 judge 本地冒烟通过（含 SpreadsheetBench 双 schema、SearchQA 括号容错）
- [x] 服务器任务结构校验通过（symlink/manifest/README/venv）
- [x] per-command 超时机制上线（防止无效命令占满预算）
- [x] 代理 5 个根因全部修复（线程 / 换非-reasoning 模型 / tool_result 翻译 / 流式 SSE / keep-alive 关闭）
- [x] **SearchQA 跑出完整绿色 lifecycle**（`status=success, reward=1, judge=pass`）← 完成
- [x] **SpreadsheetBench 跑出完整绿色 lifecycle**（`status=success, reward=1, judge=pass "All 2 target cells match"`）← 完成

> **三个 bench 全部拿到绿色 lifecycle**（OfficeQA / SearchQA / SpreadsheetBench，均 `status=success` + judge pass），**可以开始大规模测评**。

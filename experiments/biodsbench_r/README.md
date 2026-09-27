# BioDSBench-R Evaluation Drivers

These scripts use the external harness to evaluate BioDSBench-R tasks. The
benchmark bundles, source R dataset, SkillOpt artifacts, and full trajectories
are not included here.

## Required inputs

- `HARNESS_DIR`: checkout containing `src/harness/evaluation/cli.ts`.
- `R_TASKS_DIR`: generated BioDSBench-R task bundles.
- `SKILL_TRANSFER_DIR`: split files and result JSON location.
- `ANTHROPIC_API_KEY` (or `API_KEY`): model API credential.
- `ANTHROPIC_BASE_URL`, `ANTHROPIC_MODEL`: provider endpoint and model.
- `BEST_SKILL`: required by SkillOpt evaluation runners.
- Bun executable, optionally configured with `BUN_BIN`.

`QWEN_API_KEY`, `QWEN_BASE_URL`, and `QWEN_MODEL` configure an optional
separate Qwen-compatible service. `EVAL_TIMEOUT` sets the per-task timeout.
No credential is embedded in these scripts.

## Drivers

| Script | Purpose |
| --- | --- |
| `run_r_noskill_baseline.py` | Collect no-skill rewards for the configured task set |
| `run_r_transfer_eval.py` | Run no-skill, transfer-skill, and oracle arms |
| `run_r_v10_eval.py` | Run V10 selection/rejection, no-skill, and oracle arms |
| `run_skillopt_eval.py` | Evaluate a BioMNIBench-trained SkillOpt skill on BioDSBench |
| `run_native_disksafe_par.py` | Resumable, disk-aware parallel native SkillOpt evaluation |
| `baseline3_r_transfer.py` | Few-shot evaluation using matched source reference solutions |
| `label_task_types.py` | Assign controlled-vocabulary task-type metadata |
| `proxy_anthropic_to_openai.py` | Translate Anthropic Messages requests to OpenAI-compatible chat completions |

Use `--help` for each command's exact options. Before a full run, verify the
selected split, model, judge, timeout, and output directory. Do not reuse results
across different model or judge configurations as if they were one controlled
arm.

## Disk-safe native run

The native runner defaults to three workers and checks free space before each
task. It writes results incrementally to `r_native_disksafe_results.json`, so
restarting with the same `--tag` resumes tasks that are incomplete or failed
with a retryable status. Completed per-task workspaces are deleted after the
reward is saved. Set `MIN_FREE_MB` in the source only when changing the disk
policy deliberately; do not run multiple copies against the same result file.

## API compatibility proxy

When the harness expects Anthropic Messages but the provider exposes OpenAI
Chat Completions, start the proxy with credentials already in the environment:

```bash
export OPENAI_API_KEY="$ANTHROPIC_API_KEY"
python experiments/biodsbench_r/proxy_anthropic_to_openai.py \
  --host 127.0.0.1 --port 8444 \
  --target-url https://api.deepseek.com \
  --target-model deepseek-flash \
  --target-chat-path /chat/completions
export ANTHROPIC_BASE_URL=http://127.0.0.1:8444
```

The proxy is a local compatibility layer; it does not alter the evaluation
rubric or results. Avoid exposing it on a public interface unless authentication
and network controls are added.

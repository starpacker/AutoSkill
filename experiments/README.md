# Experiment Runners

The scripts here reproduce selected benchmark runs reported by AutoSkill. They
are experiment drivers, not a replacement for the benchmark harness or datasets.
The full task collections, private reference answers, generated workspaces, and
run trajectories are intentionally not included.

## BioDSBench-R

See [`biodsbench_r/`](biodsbench_r/) for:

- no-skill baseline, BioMNIBench-to-BioDSBench SkillOpt transfer, and V10 SEL
  evaluation runners;
- baseline3 ground-truth few-shot evaluation;
- task-type labeling;
- disk-safe native SkillOpt evaluation and its Anthropic-to-OpenAI-compatible
  proxy.

## External prerequisites

- Python 3.10 or newer for the runners.
- The benchmark's Bun/TypeScript harness, installed separately.
- BioDSBench-R task bundles and the corresponding split/result inputs.
- The source skill(s) required by the selected arm.
- A compatible model endpoint and a credential supplied only through the
  environment.

The R evaluation drivers accept these environment variables:

```text
SKILL_TRANSFER_DIR  directory containing splits and result inputs/outputs
HARNESS_DIR         external harness checkout
R_TASKS_DIR         BioDSBench-R task bundle directory
BUN_BIN             optional Bun executable path
BEST_SKILL          SkillOpt best-skill Markdown file
ANTHROPIC_API_KEY   model credential (or API_KEY)
ANTHROPIC_BASE_URL  model API base URL
ANTHROPIC_MODEL     model identifier
QWEN_API_KEY        optional separate Qwen-compatible credential
QWEN_BASE_URL       Qwen-compatible endpoint
QWEN_MODEL          Qwen-compatible model identifier
EVAL_TIMEOUT        per-task timeout in seconds
```

Never commit `.env`, credentials, raw task data, private judges, or full run
traces. Set credentials in the process environment or a local secret manager.

## Example

On an already provisioned evaluation host, configure the variables above and
run a dry-run first where supported. The resumable native runner uses the same
result JSON across restarts:

```bash
python experiments/biodsbench_r/run_native_disksafe_par.py \
  --tag native39 --workers 3
python experiments/biodsbench_r/run_native_disksafe_par.py \
  --tag native39 --collect-only
```

The runner checks available space before starting each task and removes that
task's workspace after recording its result. It still requires the external
harness, task data, and `BEST_SKILL` to exist.

For a direct runner's supported options, use `python <script> --help`. Results
are only comparable when the model, endpoint, split, timeout, harness, and judge
are held constant.

"""Write the correct biomebench config with exec_timeout."""
cfg_path = "/data/yjh/skill-opt/repo/configs/biomnibench/default.yaml"
content = """\
_base_: ../_base_/default.yaml

env:
  name: biomnibench
  skill_init: skillopt/envs/biomnibench/skills/initial.md
  data_path: /data/yjh/biomnibench-organized
  split_dir: ""
  split_mode: ratio
  split_ratio: "23:2:27"
  workers: 2
  exec_timeout: 300
  max_completion_tokens: 16384
  limit: 0

train:
  num_epochs: 5
  batch_size: 4
  accumulation: 1
  seed: 42

gradient:
  analyst_workers: 8
  minibatch_size: 4
  merge_batch_size: 4

optimizer:
  learning_rate: 4
  lr_scheduler: cosine
  use_slow_update: true
  use_meta_skill: true

evaluation:
  use_gate: true
  eval_test: true

model:
  backend: openai_compatible
  optimizer_backend: openai_compatible
  target_backend: openai_chat
  reasoning_effort: medium
"""
with open(cfg_path, "w") as f:
    f.write(content)
print("Config written successfully")
# Verify
with open(cfg_path) as f:
    print(f.read())
import yaml, sys

path = '/data/yjh/skill-opt/repo/configs/biomnibench/default.yaml'
with open(path) as f:
    cfg = yaml.safe_load(f)

cfg['model']['optimizer'] = 'Vendor3/DeepSeek-V4-Flash'
cfg['model']['target'] = 'Vendor3/DeepSeek-V4-Flash'

with open(path, 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

with open(path) as f:
    print(f.read())
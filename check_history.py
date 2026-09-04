import json

h = json.load(open("/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_gpt-5.5_20260830_015834/history.json"))
print(json.dumps(h[-10:], indent=2))
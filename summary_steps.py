import json, glob, os

base = '/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_gpt-5.5_20260830_015834'
steps = sorted(glob.glob(os.path.join(base, 'steps/step_*/step_record.json')),
               key=lambda x: int(x.split('step_')[1].split('/')[0]))

print('Step  | Ep | Epi | Action              | Score | Best | Wall(s) | Skill_Size')
print('-' * 90)
for s in steps:
    r = json.load(open(s))
    print(f"{r['step']:>5} | {r['epoch']:>2} | {r['step_in_epoch']:>3} | {r['action']:>20} | {r['current_score']:>5} | {r['best_score']:>4} | {int(r['wall_time_s']):>6} | {r['skill_len']}")

print()
n_skills = len(glob.glob(os.path.join(base, 'skills/skill_v*.md')))
print(f'Total skills: {n_skills}')
print(f'Total steps: {len(steps)}')
print(f'Total epochs: {len(glob.glob(os.path.join(base, "meta_skill/epoch_*/")))}')
#!/usr/bin/env python3
import json, os, glob

base = '/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260831_131414/steps'
steps = sorted(glob.glob(os.path.join(base, 'step_*')))

for s in steps:
    name = os.path.basename(s)
    rollout_dir = os.path.join(s, 'rollout')
    rollout_info = 'no_rollout'
    
    if os.path.isdir(rollout_dir):
        runs_dir = os.path.join(rollout_dir, 'runs')
        if os.path.isdir(runs_dir):
            tasks = os.listdir(runs_dir)
            done_count = 0
            for t in tasks:
                td = os.path.join(runs_dir, t)
                if os.path.isdir(td):
                    files = os.listdir(td)
                    if any('score' in x or 'reward' in x or 'result' in x for x in files):
                        done_count += 1
            rollout_info = f'rollout({done_count}/{len(tasks)} done)'
        else:
            rollout_info = 'rollout(no_runs)'
    
    reflect_dir = os.path.join(s, 'reflect')
    reflect_info = 'no_reflect'
    if os.path.isdir(reflect_dir):
        rfiles = [x for x in os.listdir(reflect_dir) if x.endswith('.json')]
        reflect_info = f'reflect({len(rfiles)} files)'
    
    train_dir = os.path.join(s, 'train')
    train_info = 'no_train'
    if os.path.isdir(train_dir):
        tf = os.listdir(train_dir)
        train_info = f'train({len(tf)} files)'
    
    print(f'{name}: {rollout_info} | {reflect_info} | {train_info}')
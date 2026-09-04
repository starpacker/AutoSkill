#!/usr/bin/env python3
"""
dry_run_v9.py — Dry-run SmartSelectorV9 on all targets.

Shows what V9 would select/reject for each target with detailed logging.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from skill_selector.smart_selector_v9 import SmartSelectorV9

RESULTS_INDEX = "/data/yjh/skill-transfer-eval/results_index.json"
SIMILARITY_PATH = "/data/yjh/skill-transfer-eval/similarity/similarity_matrix.json"
V7_MODEL_PATH = "/data/yjh/skill-transfer-eval/skill_selector/v7_model.json"
GENERALIZED_DIR = "/data/yjh/skill-transfer-eval/generalized_skills"

def main():
    print("=" * 70)
    print("  SmartSelectorV9 — Dry Run")
    print("=" * 70)

    # Load selector
    selector = SmartSelectorV9(
        results_index_path=RESULTS_INDEX,
        similarity_path=SIMILARITY_PATH,
        v7_model_path=V7_MODEL_PATH,
        min_score=0.05,
        bl_max=0.80,
        verbose=True,
    )

    # Discover available skills (generalized skills)
    available_skills = {}
    if os.path.isdir(GENERALIZED_DIR):
        for task_id in sorted(os.listdir(GENERALIZED_DIR)):
            skill_path = os.path.join(GENERALIZED_DIR, task_id, "SKILL.md")
            if os.path.isfile(skill_path):
                available_skills[task_id] = skill_path
    print(f"\nAvailable skills: {len(available_skills)} sources")
    print(f"  {', '.join(sorted(available_skills.keys()))}")

    # Load baselines
    idx = json.load(open(RESULTS_INDEX))
    baselines = {}
    for task, judges in idx.get('baselines', {}).items():
        if isinstance(judges, dict):
            baselines[task] = judges.get('gemini', list(judges.values())[0]) / 100.0
        elif isinstance(judges, (int, float)):
            baselines[task] = judges / 100.0

    # All targets (50 tasks)
    all_tasks = sorted(baselines.keys())
    source_tasks = set(available_skills.keys())
    targets = [t for t in all_tasks if t not in source_tasks]

    print(f"\nTargets: {len(targets)}")
    print(f"Baseline range: {min(baselines[t] for t in targets):.2f} - {max(baselines[t] for t in targets):.2f}")

    # Run selection for each target
    results = []
    print(f"\n{'='*70}")
    print("  Selection Results")
    print(f"{'='*70}")

    for target in targets:
        source, confidence = selector.select_skill(target, available_skills)

        bl = baselines.get(target, 0.5)
        src_type = selector.get_task_type(source) if source else "N/A"
        tgt_type = selector.get_task_type(target)

        if source:
            result_str = f"  ✅ {target} (bl={bl:.2f}, type={tgt_type}) → {source} ({src_type}) conf={confidence:.4f}"
        else:
            result_str = f"  ❌ {target} (bl={bl:.2f}, type={tgt_type}) → REJECTED"

        results.append({
            'target': target,
            'baseline': bl,
            'target_type': tgt_type,
            'source': source,
            'source_type': src_type if source else None,
            'confidence': confidence,
        })
        print(result_str)

    # Summary
    selected = [r for r in results if r['source']]
    rejected = [r for r in results if not r['source']]

    print(f"\n{'='*70}")
    print(f"  Summary")
    print(f"{'='*70}")
    print(f"  Selected: {len(selected)}/{len(targets)}")
    print(f"  Rejected: {len(rejected)}/{len(targets)}")

    if selected:
        print(f"\n  Selected targets:")
        sel_sorted = sorted(selected, key=lambda x: -x['confidence'])
        for r in sel_sorted:
            print(f"    {r['target']} (bl={r['baseline']:.2f}, {r['target_type']}) "
                  f"→ {r['source']} ({r['source_type']}) conf={r['confidence']:.4f}")

    if rejected:
        print(f"\n  Rejected targets (bl > 0.80 or low score):")
        rej_sorted = sorted(rejected, key=lambda x: x['baseline'])
        for r in rej_sorted:
            print(f"    {r['target']} (bl={r['baseline']:.2f}, {r['target_type']})")

    # Focus: previously harmed tasks
    print(f"\n{'='*70}")
    print("  Previously Harmed Tasks — Did V9 Save Them?")
    print(f"{'='*70}")

    # Known harmed tasks from v7.1 Batch 3
    harmed_tasks = {
        'da-24-3': 'gwas-eqtl',
        'da-19-4': 'chromatin-profiling',
        'da-8-2': 'cell-composition',
        'da-26-4': 'pathway-enrichment',
        'da-15-7': 'clustering',
        'da-10-1': 'differential-expression',
        'da-18-1': 'mutation-analysis',
        'da-17-3': 'survival-analysis',
    }

    for task, ttype in harmed_tasks.items():
        r = next((x for x in results if x['target'] == task), None)
        if r:
            if r['source']:
                verdict = "⚠️ Still selected (might still be harmed)"
            else:
                verdict = "✅ REJECTED — protected by V9!"
            print(f"  {task} (bl={r['baseline']:.2f}, {ttype}): {verdict}")

    print(f"\n{'='*70}")
    print("  Done.")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
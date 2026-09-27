#!/usr/bin/env python3
"""
run_skill_transfer_pipeline.py

Complete skill transfer pipeline for BioMniBench:
  1. Compute pairwise similarity between all 50 skill bundles
  2. Generalize source skills into task-agnostic abstract skills (via LLM)
  3. Match generalized skills to target tasks (via similarity)
  4. Deploy matched skills for evaluation

Usage:
  python3 run_skill_transfer_pipeline.py --step similarity
  python3 run_skill_transfer_pipeline.py --step generalize [--source da-17-1]
  python3 run_skill_transfer_pipeline.py --step deploy
  python3 run_skill_transfer_pipeline.py --all
"""

import json, os, sys, time, subprocess
from pathlib import Path

BASE_DIR = Path("/data/yjh/skill-transfer-eval")
SIMILARITY_DIR = BASE_DIR / "similarity"
GENERALIZED_DIR = BASE_DIR / "generalized_skills"
DEPLOY_DIR = BASE_DIR / "skills"

# Known source→target pairs (from skill-transfer planning)
KNOWN_PAIRS = [
    ("da-5-1", "da-5-3"),
    ("da-8-1", "da-8-3"),
    ("da-13-5", "da-13-6"),
    ("da-17-1", "da-17-5"),
    ("da-18-5", "da-18-7"),
    ("da-19-3", "da-19-4"),
    ("da-19-4", "da-19-6"),
    ("da-26-2", "da-26-4"),
]


def step_similarity():
    """Step 1: Compute pairwise similarity matrix."""
    print("=" * 60)
    print("Step 1: Computing Skill Similarity")
    print("=" * 60)

    script = BASE_DIR / "compute_skill_similarity.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, cwd=str(BASE_DIR)
    )
    print(result.stdout[-2000:])
    if result.stderr:
        print("STDERR:", result.stderr[:500])

    return result.returncode == 0


def step_generalize(source_task=None):
    """Step 2: Generalize source skills into task-agnostic skills."""
    print("=" * 60)
    print("Step 2: Generalizing Skills (task-agnostic)")
    print("=" * 60)

    script = BASE_DIR / "generalize_skill.py"
    cmd = [sys.executable, str(script)]
    if source_task:
        cmd += ["--source", source_task]
    else:
        cmd += ["--all"]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE_DIR))
    print(result.stdout[-2000:])
    if result.stderr:
        print("STDERR:", result.stderr[:500])

    return result.returncode == 0


def step_deploy():
    """Step 3: Deploy generalized skills to target tasks via similarity matching."""
    print("=" * 60)
    print("Step 3: Deploying Generalized Skills to Target Tasks")
    print("=" * 60)

    if not GENERALIZED_DIR.exists():
        print("❌ No generalized skills found in", GENERALIZED_DIR)
        return False

    # Load similarity matrix to find best source→target matches
    pairs_path = SIMILARITY_DIR / "ranked_pairs.json"
    if pairs_path.exists():
        all_pairs = json.loads(pairs_path.read_text())
        pair_map = {(p["source"], p["target"]): p["similarity"] for p in all_pairs}
    else:
        print("⚠ No similarity matrix — using known pairs only")
        pair_map = {}

    # Deploy each generalized skill to its known target tasks
    n_deployed = 0
    for s, t in KNOWN_PAIRS:
        gen_dir = GENERALIZED_DIR / s
        skill_path = gen_dir / "SKILL.md"
        if not skill_path.exists():
            print(f"  ⚠ No generalized skill for {s}, skipping {s}→{t}")
            continue

        # Get similarity score
        sim = pair_map.get((s, t), 0.5)

        # Deploy to target
        deploy_target = DEPLOY_DIR / t / "skills" / "generalized-transfer"
        deploy_target.mkdir(parents=True, exist_ok=True)
        (deploy_target / "SKILL.md").write_text(skill_path.read_text())

        # Save metadata
        meta = {
            "source_task": s,
            "target_task": t,
            "similarity": sim,
            "deployed_at": time.strftime("%Y%m%d_%H%M%S"),
            "generalized_skill_source": str(gen_dir),
        }
        (deploy_target / "metadata.json").write_text(json.dumps(meta, indent=2))

        n_deployed += 1
        print(f"  ✅ {s} → {t} (sim={sim:.3f})")

    print(f"\nDeployed: {n_deployed}/{len(KNOWN_PAIRS)} skills")
    return n_deployed > 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Skill Transfer Pipeline")
    parser.add_argument("--step", choices=["similarity", "generalize", "deploy"], help="Which step to run")
    parser.add_argument("--source", type=str, help="Source task (for generalize step)")
    parser.add_argument("--all", action="store_true", help="Run all steps")

    args = parser.parse_args()

    if args.all:
        step_similarity()
        step_generalize()
        step_deploy()
    elif args.step == "similarity":
        step_similarity()
    elif args.step == "generalize":
        step_generalize(source_task=args.source)
    elif args.step == "deploy":
        step_deploy()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

"""
Skill Selector Pipeline.

Orchestrates the full flow:
1. Load skill library, similarity matrix, baselines
2. Use a SkillSelector to pick the best skill for a target task
3. Deploy the selected skill to the target
4. Run evaluation
5. Collect and compare results
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .base import SkillSelector
from .similarity_selector import SimilaritySelector


# ── Server Paths ──────────────────────────────────────────────────────────
REMOTE_BASE = "/data/yjh/skill-transfer-eval"
GENERALIZED_SKILLS_DIR = f"{REMOTE_BASE}/generalized_skills"
SKILLS_DIR = f"{REMOTE_BASE}/skills"
SIMILARITY_PATH = f"{REMOTE_BASE}/similarity/similarity_matrix.json"
RESULTS_INDEX_PATH = f"{REMOTE_BASE}/results_index.json"
BIO_DIR = "/data/yjh/biomnibench-organized"
RUNS_DIR = f"{REMOTE_BASE}/generalized"

# ── Local paths (for the server-side script) ──────────────────────────────
# These are used when the script is deployed to the server
SERVER_SCRIPT_DIR = "/tmp/skill_selector"


class SkillTransferPipeline:
    """Orchestrates skill selection, deployment, and evaluation."""

    def __init__(self, selector: SkillSelector, remote: bool = True):
        """Initialize the pipeline.

        Args:
            selector: A SkillSelector instance.
            remote: Whether to run on the remote server.
        """
        self.selector = selector
        self.remote = remote

        # Load data
        self.similarity_matrix = self._load_json(SIMILARITY_PATH)
        self.results_index = self._load_json(RESULTS_INDEX_PATH)
        self.baselines = {
            t: v['gemini'] / 100.0
            for t, v in self.results_index.get('baselines', {}).items()
        }
        self.oracles = {
            t: v['gemini'] / 100.0
            for t, v in self.results_index.get('oracles', {}).items()
        }

        # Discover available skills
        self.available_skills = self._discover_skills()

    def _load_json(self, path: str) -> dict:
        """Load a JSON file from the server."""
        if self.remote:
            import subprocess
            result = subprocess.run(
                ["ssh", "server1", f"cat {path}"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                print(f"Warning: Could not load {path}: {result.stderr}")
                return {}
            return json.loads(result.stdout)
        else:
            with open(path) as f:
                return json.load(f)

    def _discover_skills(self) -> Dict[str, str]:
        """Discover all available generalized skills.

        Returns:
            Dict mapping source_task_id -> path to SKILL.md
        """
        if self.remote:
            result = subprocess.run(
                ["ssh", "server1",
                 f"for d in {GENERALIZED_SKILLS_DIR}/*/; do "
                 f"  task=$(basename $d); "
                 f"  if [ -f \"{GENERALIZED_SKILLS_DIR}/$task/SKILL.md\" ]; then "
                 f"    echo \"$task\"; "
                 f"  fi; "
                 f"done"],
                capture_output=True, text=True, timeout=30
            )
            skills = {}
            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if line:
                    skills[line] = f"{GENERALIZED_SKILLS_DIR}/{line}/SKILL.md"
            return skills
        else:
            # Local mode
            skills = {}
            base = Path(GENERALIZED_SKILLS_DIR)
            if base.exists():
                for d in base.iterdir():
                    if d.is_dir():
                        skill_file = d / "SKILL.md"
                        if skill_file.exists():
                            skills[d.name] = str(skill_file)
            return skills

    def list_available_skills(self) -> List[str]:
        """List all available source tasks with skills."""
        return sorted(self.available_skills.keys())

    def select_skill(self, target_task: str) -> Tuple[Optional[str], float]:
        """Select the best skill for a target task.

        Args:
            target_task: The target task ID.

        Returns:
            (selected_source, confidence)
        """
        return self.selector.select_skill(
            target_task=target_task,
            available_skills=self.available_skills,
            similarity_matrix=self.similarity_matrix,
        )

    def deploy_skill(self, source_task: str, target_task: str,
                     experiment_tag: str = "skill-selector") -> str:
        """Deploy a skill from source to target.

        Args:
            source_task: Source task with the skill.
            target_task: Target task to deploy to.
            experiment_tag: Tag for the experiment.

        Returns:
            The skill name that was deployed.
        """
        skill_name = f"{experiment_tag}-{source_task}"
        src_dir = f"{GENERALIZED_SKILLS_DIR}/{source_task}"
        dst_dir = f"{SKILLS_DIR}/{target_task}/skills/{skill_name}"

        if self.remote:
            cmd = (
                f"mkdir -p {SKILLS_DIR}/{target_task}/skills && "
                f"rm -rf {dst_dir} && "
                f"cp -r {src_dir} {dst_dir} && "
                f"echo 'Deployed: {source_task} -> {target_task} as {skill_name}'"
            )
            result = subprocess.run(
                ["ssh", "server1", cmd],
                capture_output=True, text=True, timeout=30
            )
            print(result.stdout.strip())
            if result.returncode != 0:
                print(f"Deploy error: {result.stderr}")
        else:
            shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
            print(f"Deployed: {source_task} -> {target_task} as {skill_name}")

        return skill_name

    def run_evaluation(self, target_task: str, skill_name: str,
                       reps: int = 1) -> str:
        """Run evaluation on the target task with the deployed skill.

        Args:
            target_task: Target task ID.
            skill_name: The deployed skill name.
            reps: Number of repetitions.

        Returns:
            The run tag for this evaluation.
        """
        run_tag = f"skill-selector-{target_task}-{int(time.time())}"

        cmd = (
            f"cd /data/yjh/skill-transfer-eval && "
            f"bun src/harness/evaluation/cli.ts "
            f"  --task {target_task} "
            f"  --tasks-dir {BIO_DIR} "
            f"  --runs-dir {RUNS_DIR} "
            f"  --max-rounds 5 "
            f"  --timeout-seconds 7200 "
            f"  --concurrency 1 "
            f"  --temperature 1 "
            f"  --thinking disabled "
            f"  --timestamp {run_tag} "
            f"  --quiet "
            f"  --enable-skills "
            f"  --skills-dir {SKILLS_DIR}/{target_task}/skills/ "
            f"  --skill-name {skill_name} "
            f"  --max-active-skills 1 "
            f"  --repetitions {reps}"
        )

        if self.remote:
            print(f"Running evaluation for {target_task} with skill '{skill_name}'...")
            result = subprocess.run(
                ["ssh", "server1", cmd],
                capture_output=True, text=True, timeout=7200 * reps + 300
            )
            print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
            if result.returncode != 0:
                print(f"Evaluation error: {result.stderr[-1000:]}")
        else:
            print(f"Would run: {cmd}")

        return run_tag

    def collect_result(self, target_task: str, run_tag: str) -> Optional[dict]:
        """Collect the evaluation result for a run.

        Args:
            target_task: Target task ID.
            run_tag: The run tag from run_evaluation.

        Returns:
            Dict with reward, baseline, delta, or None if not found.
        """
        # Try to find the result in the results_index
        if self.remote:
            result = subprocess.run(
                ["ssh", "server1",
                 f"for d in {RUNS_DIR}/{target_task}_{run_tag}_*/logs/run_summary.json; do "
                 f"  if [ -f \"$d\" ]; then cat \"$d\"; break; fi; "
                 f"done"],
                capture_output=True, text=True, timeout=30
            )
            if result.stdout.strip():
                summary = json.loads(result.stdout)
                reward = summary.get('reward', 0) / 100.0
                baseline = self.baselines.get(target_task, 0)
                return {
                    'reward': reward,
                    'baseline': baseline,
                    'delta': reward - baseline,
                    'status': summary.get('status', 'unknown'),
                    'rounds': summary.get('rounds', 0),
                }
        return None

    def run_single(self, target_task: str, dry_run: bool = False,
                   reps: int = 1) -> dict:
        """Run the full pipeline for a single target task.

        Args:
            target_task: Target task ID.
            dry_run: If True, only show what would be done.
            reps: Number of evaluation repetitions.

        Returns:
            Dict with selection and evaluation results.
        """
        print(f"\n{'='*60}")
        print(f"Target: {target_task}")
        print(f"Selector: {self.selector.get_name()}")
        print(f"{'='*60}")

        # Step 1: Select skill
        source, confidence = self.select_skill(target_task)
        print(self.selector.describe_selection(target_task, source, confidence))

        result = {
            'target': target_task,
            'selector': self.selector.get_name(),
            'selected_source': source,
            'confidence': confidence,
            'baseline': self.baselines.get(target_task),
            'oracle': self.oracles.get(target_task),
        }

        if source is None:
            print("No suitable skill found. Skipping.")
            return result

        if dry_run:
            print(f"[DRY RUN] Would deploy '{source}' -> '{target_task}'")
            print(f"[DRY RUN] Would evaluate with skill 'skill-selector-{source}'")
            return result

        # Step 2: Deploy
        print(f"\nDeploying skill from '{source}' to '{target_task}'...")
        skill_name = self.deploy_skill(source, target_task)

        # Step 3: Evaluate
        print(f"\nEvaluating {target_task} with skill '{skill_name}' (reps={reps})...")
        run_tag = self.run_evaluation(target_task, skill_name, reps=reps)

        # Step 4: Collect result
        print(f"\nCollecting result...")
        eval_result = self.collect_result(target_task, run_tag)
        if eval_result:
            result['evaluation'] = eval_result
            delta = eval_result['delta']
            if delta > 0.05:
                result['verdict'] = 'HELPFUL'
            elif delta < -0.05:
                result['verdict'] = 'HARMFUL'
            else:
                result['verdict'] = 'NEUTRAL'
            print(f"  Reward: {eval_result['reward']:.3f}")
            print(f"  Baseline: {eval_result['baseline']:.3f}")
            print(f"  Delta: {eval_result['delta']:+.3f}")
            print(f"  Verdict: {result['verdict']}")
        else:
            print("  Could not collect result (evaluation may still be running)")

        return result

    def run_batch(self, target_tasks: List[str], dry_run: bool = False,
                  reps: int = 1) -> List[dict]:
        """Run the full pipeline for multiple target tasks.

        Args:
            target_tasks: List of target task IDs.
            dry_run: If True, only show what would be done.
            reps: Number of evaluation repetitions.

        Returns:
            List of result dicts.
        """
        results = []
        for task in target_tasks:
            r = self.run_single(task, dry_run=dry_run, reps=reps)
            results.append(r)
            print()  # blank line between tasks
        return results

    def print_summary(self, results: List[dict]):
        """Print a summary table of results."""
        print(f"\n{'='*70}")
        print(f"SUMMARY: {self.selector.get_name()}")
        print(f"{'='*70}")
        print(f"{'Target':>10s} | {'Source':>10s} | {'Conf':>5s} | {'Baseline':>8s} | {'Delta':>7s} | {'Verdict':>10s}")
        print(f"{'-'*10}-+-{'-'*10}-+-{'-'*5}-+-{'-'*8}-+-{'-'*7}-+-{'-'*10}")

        for r in results:
            src = r.get('selected_source', 'N/A') or 'N/A'
            conf = f"{r['confidence']:.2f}" if r.get('confidence') else 'N/A'
            bl = f"{r.get('baseline', 0):.3f}" if r.get('baseline') is not None else 'N/A'
            ev = r.get('evaluation')
            delta = f"{ev['delta']:+.3f}" if ev else 'N/A'
            verdict = r.get('verdict', 'N/A')
            print(f"{r['target']:>10s} | {src:>10s} | {conf:>5s} | {bl:>8s} | {delta:>7s} | {verdict:>10s}")

        # Aggregate stats
        helpful = sum(1 for r in results if r.get('verdict') == 'HELPFUL')
        harmful = sum(1 for r in results if r.get('verdict') == 'HARMFUL')
        neutral = sum(1 for r in results if r.get('verdict') == 'NEUTRAL')
        total = helpful + harmful + neutral
        if total > 0:
            print(f"\n  Helpful: {helpful}/{total} ({helpful/total*100:.0f}%)")
            print(f"  Harmful: {harmful}/{total} ({harmful/total*100:.0f}%)")
            print(f"  Neutral: {neutral}/{total} ({neutral/total*100:.0f}%)")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Skill Selector Pipeline")
    parser.add_argument("--target", nargs="+", help="Target task(s) to evaluate")
    parser.add_argument("--all-targets", action="store_true",
                       help="Run on all targets with available skills")
    parser.add_argument("--selector", default="similarity",
                       choices=["similarity"],
                       help="Skill selector strategy")
    parser.add_argument("--min-similarity", type=float, default=0.0,
                       help="Minimum similarity threshold")
    parser.add_argument("--dry-run", action="store_true",
                       help="Only show selections, don't run evaluations")
    parser.add_argument("--reps", type=int, default=1,
                       help="Number of evaluation repetitions")
    parser.add_argument("--local", action="store_true",
                       help="Run locally (for testing)")

    args = parser.parse_args()

    # Create selector
    if args.selector == "similarity":
        selector = SimilaritySelector(min_similarity=args.min_similarity)
    else:
        print(f"Unknown selector: {args.selector}")
        sys.exit(1)

    pipeline = SkillTransferPipeline(selector, remote=not args.local)

    # Determine targets
    if args.target:
        targets = args.target
    elif args.all_targets:
        # Use all tasks that have a baseline (excluding the ones that are sources)
        all_tasks = set(pipeline.baselines.keys())
        source_tasks = set(pipeline.available_skills.keys())
        targets = sorted(all_tasks - source_tasks)
        print(f"Auto-selected {len(targets)} targets (all tasks minus source tasks)")
    else:
        # Interactive mode: show available skills and let user pick
        print(f"Available skills ({len(pipeline.available_skills)} sources):")
        for src in pipeline.list_available_skills():
            print(f"  {src}")
        print(f"\nAll tasks with baselines: {len(pipeline.baselines)}")
        parser.print_help()
        sys.exit(1)

    print(f"Pipeline: {pipeline.selector.get_name()}")
    print(f"Targets: {len(targets)}")
    print(f"Dry run: {args.dry_run}")
    print(f"Reps: {args.reps}")
    print()

    results = pipeline.run_batch(targets, dry_run=args.dry_run, reps=args.reps)
    pipeline.print_summary(results)


if __name__ == "__main__":
    main()
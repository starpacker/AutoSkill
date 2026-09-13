#!/usr/bin/env python3
"""
extract_min_core_skills.py — Extract min-core skill bundles from ablation results.

For each task with completed ablation, reads the ablation_summary.json and
uses the accepted_drop_ops to generate a pruned skill bundle using the
render command.

Usage:
  python3 extract_min_core_skills.py [--task da-5-1] [--dry-run]
  python3 extract_min_core_skills.py --all
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

HARNESS = Path(os.environ.get("BIOMNIBENCH_HARNESS_DIR", "/tmp/my_claude_biomnibench_fixed"))
BUN = Path(os.environ.get("BUN_BIN", "/tmp/bun_extract/bun-linux-x64/bun"))
BUNDLES = Path(os.environ.get("ORACLE_BUNDLES_DIR", "/data/yjh/biomnibench-skill-bundles"))
TRANSFER_ROOT = Path(os.environ.get("SKILL_TRANSFER_ROOT", "/data/yjh/skill-transfer-eval"))
ABLATIONS = TRANSFER_ROOT / "ablations"
PRUNED_BUNDLES = TRANSFER_ROOT / "pruned_bundles"
TASKS_DIR = Path(os.environ.get("BIOMNIBENCH_TASKS_DIR", "/data/yjh/biomnibench-organized"))

ALL_TASKS = [
    "da-1-3","da-1-4","da-10-1","da-10-3","da-11-1",
    "da-12-2","da-12-4","da-13-1","da-13-3","da-13-5",
    "da-13-6","da-14-1","da-14-3","da-14-8","da-15-1",
    "da-15-2","da-15-7","da-15-8","da-16-1","da-17-1",
    "da-17-3","da-17-5","da-18-1","da-18-5","da-18-7",
    "da-19-1","da-19-3","da-19-4","da-19-6","da-20-1",
    "da-20-3","da-20-4","da-24-3","da-25-1","da-26-2",
    "da-26-4","da-3-4","da-3-5","da-4-1","da-4-6",
    "da-4-7","da-5-1","da-5-3","da-6-2","da-6-5",
    "da-8-1","da-8-2","da-8-3","da-9-1","da-9-7",
]


def load_ablation_summary(task: str) -> dict | None:
    path = ABLATIONS / task / "ablation_summary.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def get_accepted_drop_ops(ablation: dict) -> list[str]:
    """Get the list of operations that were successfully pruned."""
    return ablation.get("accepted_drop_ops", [])


def get_enabled_ops(task: str, drop_ops: list[str]) -> list[str] | None:
    """Get the full list of operations, then filter out drop_ops."""
    manifest_path = BUNDLES / task / "oracle_skill_manifest.json"
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text())
    all_ops = [op["id"] for op in manifest["operations"] if op.get("enabled_by_default", True)]
    return [op for op in all_ops if op not in drop_ops]


def render_pruned_bundle(task: str, drop_ops: list[str], dry_run: bool = False) -> bool:
    """Use the render command to create a pruned bundle."""
    bundle_dir = BUNDLES / task
    out_dir = PRUNED_BUNDLES / task
    # The renderer deliberately scans every file below ``out_dir`` for
    # solver-facing metadata. Keep the control-plane manifest beside the
    # rendered skill, not inside it, otherwise its ``enabled_ops`` field is
    # correctly rejected as a metadata leak.
    variant_manifest_path = PRUNED_BUNDLES / f"{task}_variant_manifest.json"

    if not drop_ops:
        print(f"  [SKIP] {task}: no ops to prune")
        return False

    if dry_run:
        enabled_ops = get_enabled_ops(task, drop_ops)
        print(f"  [DRY-RUN] {task}: drop {len(drop_ops)} ops, keep {len(enabled_ops)} ops")
        print(f"    drop: {drop_ops}")
        print(f"    keep: {enabled_ops}")
        return True

    out_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    cmd = [
        str(BUN),
        "src/oracle-skills/cli.ts", "render",
        "--bundle", str(bundle_dir),
        "--out", str(out_dir),
        "--drop-ops", ",".join(drop_ops),
        "--variant-manifest-out", str(variant_manifest_path),
    ]

    result = subprocess.run(cmd, cwd=str(HARNESS), env=env, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"  [FAIL] {task}: render failed: {result.stderr[:500]}")
        return False

    print(f"  [DONE] {task}: pruned bundle at {out_dir}")
    print(f"    manifest: {variant_manifest_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Extract min-core skill bundles")
    parser.add_argument("--task", type=str, help="Specific task to process")
    parser.add_argument("--all", action="store_true", help="Process all completed ablations")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()

    tasks = []
    if args.task:
        tasks = [args.task]
    elif args.all:
        tasks = ALL_TASKS
    else:
        parser.print_help()
        return

    success = 0
    skip = 0
    fail = 0
    for task in tasks:
        ablation = load_ablation_summary(task)
        if ablation is None:
            print(f"  [SKIP] {task}: no ablation summary found")
            skip += 1
            continue

        status = ablation.get("status", "?")
        if status not in ("completed_all_candidates", "baseline_failed"):
            print(f"  [SKIP] {task}: ablation not completed (status={status})")
            skip += 1
            continue

        if status == "baseline_failed":
            print(f"  [SKIP] {task}: baseline failed (oracle skill doesn't beat baseline)")
            skip += 1
            continue

        drop_ops = get_accepted_drop_ops(ablation)
        if not drop_ops:
            print(f"  [SKIP] {task}: no ops pruned (min-core = full oracle skill)")
            skip += 1
            continue

        if render_pruned_bundle(task, drop_ops, args.dry_run):
            success += 1
        else:
            fail += 1

    print(f"\nResults: {success} done, {skip} skipped, {fail} failed")


if __name__ == "__main__":
    main()

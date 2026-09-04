"""
v7_data — Data loading, filtering, and cross-validation split for SmartSelector v7.

Loads results_index.json, extracts clean (baseline, delta, source, target) records,
and provides LOTOCV split.

Now includes ALL transfer types (not just Gemini-judged) to avoid data bias.
Uses the correct baseline per judge: Gemini baselines for Gemini records,
DeepSeek baselines for DeepSeek records.

All stdlib — no external dependencies.
"""

import json
import os
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

# ── Default paths (server-side) ──────────────────────────────────────────
RESULTS_INDEX_PATH = "/data/yjh/skill-transfer-eval/results_index.json"
BIO_DIR = "/data/yjh/biomnibench-organized"
GENERALIZED_SKILLS_DIR = "/data/yjh/skill-transfer-eval/generalized_skills"


# ── Record type ──────────────────────────────────────────────────────────

class TransferRecord:
    """A single cleaned transfer record."""

    __slots__ = ('source', 'target', 'baseline', 'reward', 'delta',
                 'status', 'tx_type', 'judge')

    def __init__(self, source: str, target: str,
                 baseline: float, reward: float,
                 status: str = 'success', tx_type: str = 'other',
                 judge: str = 'gemini'):
        self.source = source
        self.target = target
        self.baseline = baseline
        self.reward = reward
        self.delta = reward - baseline
        self.status = status
        self.tx_type = tx_type
        self.judge = judge

    def __repr__(self):
        return (f"TransferRecord({self.source}->{self.target}: "
                f"bl={self.baseline:.3f} r={self.reward:.3f} "
                f"d={self.delta:+.3f} [{self.status}] judge={self.judge})")


# ── Source extraction from dir name ──────────────────────────────────────

def _extract_source_from_dir(dname: str) -> Optional[str]:
    """Extract source task name from directory name.

    Handles patterns like:
      - "da-13-5_20260804_232757_generalized-transfer-da-13-1_rep1" -> "da-13-1"
      - "da-1-4_20260804_200157_generalized-transfer_rep1" -> None
    """
    parts = dname.split('_')
    for part in parts:
        if part.startswith('generalized-transfer-da-'):
            return part[len('generalized-transfer-'):]
        elif part.startswith('generalized-transfer-'):
            src = part[len('generalized-transfer-'):]
            # Make sure it looks like a task ID
            if src.startswith('da-') or src.startswith('task-'):
                return src
    return None


# ── Data loading ─────────────────────────────────────────────────────────

def load_results_index(path: str = RESULTS_INDEX_PATH) -> dict:
    """Load the results_index.json file."""
    with open(path) as f:
        return json.load(f)


def load_records(path: str = RESULTS_INDEX_PATH,
                 only_gemini: bool = False,
                 only_success: bool = False,
                 require_source: bool = True) -> List[TransferRecord]:
    """Load and clean transfer records from results_index.json.

    Args:
        path: Path to results_index.json.
        only_gemini: If True, only keep records with Gemini judge.
                      Default False: include ALL judges (DeepSeek too).
                      The correct baseline (Gemini or DeepSeek) is used per record.
        only_success: If True, only keep status='success' records.
                      Default False: keep 'failed' too (failed != infra error).
        require_source: If True, skip records where source can't be identified.

    Returns:
        List of TransferRecord objects.
    """
    data = load_results_index(path)

    baselines_raw = data.get('baselines', {})
    transfers = data.get('transfers', [])

    # Normalize baselines to 0-1 scale, store both gemini and deepseek
    gemini_baselines: Dict[str, float] = {}
    deepseek_baselines: Dict[str, float] = {}
    for task, bl_data in baselines_raw.items():
        if isinstance(bl_data, dict):
            gemini_baselines[task] = (bl_data.get('gemini', 0)) / 100.0
            deepseek_baselines[task] = (bl_data.get('deepseek', 0)) / 100.0
        else:
            bl = bl_data / 100.0 if bl_data > 1 else bl_data
            gemini_baselines[task] = bl
            deepseek_baselines[task] = bl

    records: List[TransferRecord] = []
    skipped_stats = defaultdict(int)

    # Statuses that indicate pipeline/infra failure (not skill failure)
    INFRA_STATUSES = {'timeout', 'infra_error'}

    for tx in transfers:
        src = tx.get('source')
        tgt = tx.get('target')
        reward = tx.get('reward')
        status = tx.get('status', 'unknown')
        tx_type = tx.get('type', 'other')
        dname = tx.get('dir', '')

        if not tgt or reward is None:
            skipped_stats['no_target_or_reward'] += 1
            continue

        # Detect judge model from dir name
        has_gemini = 'gemini' in dname

        # Filter: Gemini judge only if explicitly requested
        if only_gemini and not has_gemini:
            skipped_stats['non_gemini'] += 1
            continue

        # Filter: skip infra/timeout failures (not real skill outcomes)
        if status in INFRA_STATUSES:
            skipped_stats['infra_timeout'] += 1
            continue

        # Filter: only success if explicitly requested
        if only_success and status not in ('success', 'completed'):
            skipped_stats['non_success'] += 1
            continue

        # Normalize reward
        reward = reward / 100.0 if reward > 1 else reward

        # Get baseline: use gemini baseline for gemini records, deepseek for deepseek
        judge = 'gemini' if has_gemini else 'deepseek'
        if has_gemini:
            baseline = gemini_baselines.get(tgt, 0.5)
        else:
            baseline = deepseek_baselines.get(tgt, 0.5)

        # Extract source from dir name if null
        if src is None:
            src = _extract_source_from_dir(dname)

        if src is None:
            if require_source:
                skipped_stats['no_source'] += 1
                continue
            else:
                src = 'unknown'

        records.append(TransferRecord(
            source=src, target=tgt,
            baseline=baseline, reward=reward,
            status=status, tx_type=tx_type,
            judge=judge,
        ))

    return records


def get_baselines(path: str = RESULTS_INDEX_PATH,
                  judge: str = 'gemini') -> Dict[str, float]:
    """Get all baselines in 0-1 scale for a specific judge.

    Args:
        path: Path to results_index.json.
        judge: 'gemini' or 'deepseek'. Default 'gemini'.

    Returns:
        Dict mapping task_id -> baseline (0-1 scale).
    """
    data = load_results_index(path)
    baselines_raw = data.get('baselines', {})
    baselines = {}
    for task, bl_data in baselines_raw.items():
        if isinstance(bl_data, dict):
            bl = bl_data.get(judge, 0)
        else:
            bl = bl_data
        baselines[task] = bl / 100.0 if bl > 1 else bl
    return baselines


def get_all_targets(path: str = RESULTS_INDEX_PATH) -> List[str]:
    """Get all target task IDs from baselines."""
    return sorted(get_baselines(path).keys())


# ── LOTOCV split ─────────────────────────────────────────────────────────

def lotocv_split(records: List[TransferRecord],
                 ) -> List[Tuple[str, List[TransferRecord], List[TransferRecord]]]:
    """Generate Leave-One-Task-Out cross-validation folds.

    Each fold: hold out one target task, train on the rest.

    Returns:
        List of (held_out_target, train_records, test_records) tuples.
    """
    # Group records by target
    target_to_records: Dict[str, List[TransferRecord]] = defaultdict(list)
    for r in records:
        target_to_records[r.target].append(r)

    folds = []
    for target, test_records in sorted(target_to_records.items()):
        train_records = [
            r for r in records if r.target != target
        ]
        folds.append((target, train_records, test_records))

    return folds


# ── Statistics ───────────────────────────────────────────────────────────

def print_data_summary(records: List[TransferRecord]):
    """Print a summary of the loaded records."""
    if not records:
        print("[v7_data] No records loaded")
        return

    sources = set(r.source for r in records)
    targets = set(r.target for r in records)
    pairs = set((r.source, r.target) for r in records)

    deltas = [r.delta for r in records]
    baselines = [r.baseline for r in records]

    helpful = sum(1 for r in records if r.delta > 0.05)
    harmful = sum(1 for r in records if r.delta < -0.05)
    neutral = len(records) - helpful - harmful

    print(f"[v7_data] Records: {len(records)}")
    print(f"  Sources: {len(sources)}")
    print(f"  Targets: {len(targets)}")
    print(f"  Unique pairs: {len(pairs)}")
    print(f"  Delta range: [{min(deltas):.3f}, {max(deltas):.3f}]")
    print(f"  Avg delta: {sum(deltas)/len(deltas):.4f}")
    print(f"  Baseline range: [{min(baselines):.3f}, {max(baselines):.3f}]")
    print(f"  Helpful: {helpful} ({helpful/len(records)*100:.0f}%)")
    print(f"  Harmful: {harmful} ({harmful/len(records)*100:.0f}%)")
    print(f"  Neutral: {neutral} ({neutral/len(records)*100:.0f}%)")

    # Per-source stats
    print(f"\n  Per-source:")
    src_stats = defaultdict(list)
    for r in records:
        src_stats[r.source].append(r.delta)
    for src in sorted(src_stats):
        ds = src_stats[src]
        h = sum(1 for d in ds if d > 0.05)
        hm = sum(1 for d in ds if d < -0.05)
        print(f"    {src:>12s}: n={len(ds):2d} avg_delta={sum(ds)/len(ds):+.4f} "
              f"helpful={h} harmful={hm}")


# ── Main (for testing) ───────────────────────────────────────────────────

if __name__ == '__main__':
    records = load_records()
    print_data_summary(records)
    print(f"\nLOTOCV folds: {len(lotocv_split(records))}")
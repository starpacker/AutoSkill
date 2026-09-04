#!/usr/bin/env python3
"""
Transfer Matrix Generator & Viewer
===================================
Builds/updates a source-target matrix from results_index.json.
All data is Gemini judge + DeepSeek-V4-Flash worker.

"""

import json
import os
import sys
from collections import defaultdict

MATRIX_PATH = "/data/yjh/skill-transfer-eval/transfer_matrix.json"
RESULTS_INDEX_PATH = "/data/yjh/skill-transfer-eval/results_index.json"

# Tasks sorted by number (for consistent display)
TASK_ORDER = [
    "da-1-3", "da-1-4", "da-3-4", "da-3-5", "da-4-1", "da-4-6", "da-4-7",
    "da-5-1", "da-5-3", "da-6-2", "da-6-5", "da-8-1", "da-8-2", "da-8-3",
    "da-9-1", "da-9-7", "da-10-1", "da-10-3", "da-11-1", "da-12-2", "da-12-4",
    "da-13-1", "da-13-3", "da-13-5", "da-13-6", "da-14-1", "da-14-3", "da-14-8",
    "da-15-1", "da-15-2", "da-15-7", "da-15-8", "da-16-1", "da-17-1", "da-17-3",
    "da-17-5", "da-18-1", "da-18-5", "da-18-7", "da-19-1", "da-19-3", "da-19-4",
    "da-19-6", "da-20-1", "da-20-3", "da-20-4", "da-24-3", "da-25-1", "da-26-2",
    "da-26-4",
]

# Type weight for averaging: generalize-within/expand-within trusted more
TYPE_WEIGHTS = {
    "expand-within": 1.5,
    "generalized-within": 1.5,
    "raw-within": 1.0,
    "expand-cross": 1.2,
    "generalized-cross": 1.2,
    "raw-cross": 1.0,
    "generalized-transfer": 1.0,
    "other": 0.8,
}


def load_json(path):
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"  Saved {path}")


def is_gemini_judge(transfer):
    """Check if this transfer used Gemini judge based on dir name."""
    dname = transfer.get('dir', '')
    return 'gemini' in dname


def build_matrix():
    """Build transfer matrix from results_index.json."""
    print(f"Loading {RESULTS_INDEX_PATH}...")
    data = load_json(RESULTS_INDEX_PATH)

    baselines_raw = data.get('baselines', {})
    transfers = data.get('transfers', [])

    # Normalize baselines to 0-1 scale
    baselines = {}
    for task, bl_data in baselines_raw.items():
        if isinstance(bl_data, dict):
            bl = bl_data.get('gemini', 0)
        else:
            bl = bl_data
        baselines[task] = bl / 100.0 if bl > 1 else bl

    # Build matrix
    matrix = {}
    valid_count = 0
    skipped_count = 0

    for tx in transfers:
        src = tx.get('source')
        tgt = tx.get('target')
        reward = tx.get('reward')
        status = tx.get('status', 'unknown')
        tx_type = tx.get('type', 'other')

        if not tgt or reward is None:
            continue

        # Normalize reward
        reward = reward / 100.0 if reward > 1 else reward

        # Use source from dir name if null (generalized-transfer type)
        if src is None:
            dname = tx.get('dir', '')
            # Try to extract source from dir name patterns
            # e.g. "da-1-4_20260804_200157_generalized-transfer_rep1" -> no source
            # e.g. "da-13-5_20260804_232757_generalized-transfer-da-13-1_rep1" -> da-13-1
            parts = dname.split('_')
            for part in parts:
                if part.startswith('generalized-transfer-da-'):
                    # Keep "da-" prefix: generalized-transfer-da-13-1 -> da-13-1
                    src = part[len('generalized-transfer-'):]
                    break
                elif part.startswith('generalized-transfer-'):
                    src = part[len('generalized-transfer-'):]
                    break

        if src is None:
            # Still no source -- skip for matrix (can't place in a cell)
            skipped_count += 1
            continue

        # Initialize cell
        key = (src, tgt)
        if key not in matrix:
            matrix[key] = {
                'rewards': [],
                'statuses': [],
                'types': [],
                'n': 0,
            }

        cell = matrix[key]
        cell['rewards'].append(reward)
        cell['statuses'].append(status)
        cell['types'].append(tx_type)
        cell['n'] += 1
        valid_count += 1

    # Compute aggregated stats per cell
    for (src, tgt), cell in matrix.items():
        rewards = cell['rewards']
        types = cell['types']
        statuses = cell['statuses']

        # Weighted average by type weight
        weighted_sum = 0.0
        weight_sum = 0.0
        for r, t, s in zip(rewards, types, statuses):
            w = TYPE_WEIGHTS.get(t, 1.0)
            if s == 'failed' or s == 'timeout':
                w *= 0.5  # penalize failures/timeouts
            weighted_sum += r * w
            weight_sum += w

        cell['avg_reward'] = round(weighted_sum / weight_sum, 3) if weight_sum > 0 else 0.0
        cell['avg_reward_simple'] = round(sum(rewards) / len(rewards), 3)
        cell['n'] = len(rewards)
        cell['n_success'] = sum(1 for s in statuses if s == 'success')
        cell['n_failed'] = sum(1 for s in statuses if s in ('failed', 'timeout'))
        cell['best_reward'] = max(rewards)
        cell['worst_reward'] = min(rewards)
        cell['reward_std'] = round(
            (sum((r - cell['avg_reward_simple']) ** 2 for r in rewards) / len(rewards)) ** 0.5,
            3
        )

        # Delta vs baseline
        bl = baselines.get(tgt, 0.0)
        cell['delta'] = round(cell['avg_reward'] - bl, 3)
        cell['delta_simple'] = round(cell['avg_reward_simple'] - bl, 3)

        # Most common type
        type_counts = defaultdict(int)
        for t in types:
            type_counts[t] += 1
        cell['primary_type'] = max(type_counts, key=type_counts.get)

        # Remove raw data arrays to keep file compact
        del cell['rewards']
        del cell['statuses']
        del cell['types']

    # Build output
    output = {
        'meta': {
            'generated': __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S'),
            'description': 'Source-Target transfer matrix for BioDSBench (Gemini judge, DeepSeek-V4-Flash worker)',
            'judge_model': 'gemini',
            'worker_model': 'deepseek-v4-flash',
            'n_tasks': len(baselines),
            'n_cells': len(matrix),
            'n_records': valid_count,
            'n_skipped_no_source': skipped_count,
        },
        'baselines': baselines,
        'matrix': {},
    }

    # Structure matrix as {target: {source: cell_data}}
    for (src, tgt), cell in sorted(matrix.items()):
        if tgt not in output['matrix']:
            output['matrix'][tgt] = {}
        output['matrix'][tgt][src] = cell

    return output


def update_matrix():
    """Build or update the transfer matrix."""
    old_matrix = None
    if os.path.exists(MATRIX_PATH):
        print(f"Loading existing matrix from {MATRIX_PATH}...")
        old_matrix = load_json(MATRIX_PATH)

    new_matrix = build_matrix()

    if old_matrix:
        # Merge: keep old cells that don't conflict
        old_cells = old_matrix.get('matrix', {})
        new_cells = new_matrix.get('matrix', {})

        for tgt, src_dict in old_cells.items():
            if tgt not in new_cells:
                new_cells[tgt] = src_dict
            else:
                for src, cell in src_dict.items():
                    if src not in new_cells[tgt]:
                        new_cells[tgt][src] = cell

        new_matrix['matrix'] = new_cells
        new_matrix['meta']['n_cells'] = sum(len(v) for v in new_cells.values())

        # Merge baselines (old baselines may have been overwritten by new ones)
        old_bl = old_matrix.get('baselines', {})
        new_bl = new_matrix.get('baselines', {})
        for task, bl in old_bl.items():
            if task not in new_bl:
                new_bl[task] = bl
        new_matrix['baselines'] = new_bl

        print(f"  Merged: {len(new_cells)} targets, "
              f"{sum(len(v) for v in new_cells.values())} cells")

    save_json(MATRIX_PATH, new_matrix)
    print(f"\nMatrix summary:")
    print(f"  Tasks: {len(new_matrix['baselines'])}")
    print(f"  Cells (source->target pairs): {new_matrix['meta']['n_cells']}")
    print(f"  Records: {new_matrix['meta']['n_records']}")
    return new_matrix


def view_matrix(matrix=None):
    """Display a compact ASCII matrix view."""
    if matrix is None:
        if not os.path.exists(MATRIX_PATH):
            print("No matrix file found. Run --build first.")
            return
        matrix = load_json(MATRIX_PATH)

    baselines = matrix['baselines']
    cells = matrix['matrix']

    # Show baselines
    print("=" * 80)
    print("  BASELINES (Gemini judge)")
    print("=" * 80)
    for i in range(0, len(TASK_ORDER), 10):
        group = TASK_ORDER[i:i + 10]
        line = "  "
        for t in group:
            bl = baselines.get(t, 0)
            line += f"{t:10s} {bl:.2f}  "
        print(line)

    print()
    print("=" * 80)
    print("  TRANSFER MATRIX -- Delta (reward - baseline)")
    print("  Each cell: D = avg_reward - baseline")
    print("  Color: green=positive, red=negative, gray=neutral")
    print("=" * 80)

    # For each source task, show which targets it's been tested on
    # Build reverse index: source -> [(target, delta, n)]
    source_to_targets = defaultdict(list)
    for tgt, src_dict in cells.items():
        for src, cell in src_dict.items():
            source_to_targets[src].append((tgt, cell['delta'], cell['n'],
                                           cell['avg_reward'], baselines.get(tgt, 0)))

    for src in sorted(source_to_targets.keys()):
        targets = sorted(source_to_targets[src], key=lambda x: x[0])
        print(f"\n  Source: {src}  ({len(targets)} targets)")
        print(f"  {'Target':>12s}  {'D':>7s}  {'Reward':>7s}  {'BL':>5s}  {'n':>3s}  {'Verdict':>10s}")
        print(f"  {'-'*12}  {'-'*7}  {'-'*7}  {'-'*5}  {'-'*3}  {'-'*10}")
        for tgt, delta, n, avg, bl in targets:
            if delta > 0.05:
                verdict = "HELP [+]"
            elif delta < -0.05:
                verdict = "HARM [-]"
            else:
                verdict = "NEUTRAL"
            print(f"  {tgt:>12s}  {delta:>+7.3f}  {avg:>7.3f}  {bl:>5.2f}  {n:>3d}  {verdict:>10s}")

    # Summary stats
    all_deltas = []
    for tgt, src_dict in cells.items():
        for src, cell in src_dict.items():
            all_deltas.append(cell['delta'])

    if all_deltas:
        helpful = sum(1 for d in all_deltas if d > 0.05)
        harmful = sum(1 for d in all_deltas if d < -0.05)
        neutral = sum(1 for d in all_deltas if -0.05 <= d <= 0.05)
        avg_delta = sum(all_deltas) / len(all_deltas)
        print(f"\n  Total cells: {len(all_deltas)}")
        print(f"  HELPFUL: {helpful} ({helpful*100//len(all_deltas)}%)")
        print(f"  HARMFUL: {harmful} ({harmful*100//len(all_deltas)}%)")
        print(f"  NEUTRAL: {neutral} ({neutral*100//len(all_deltas)}%)")
        print(f"  Avg D: {avg_delta:+.3f}")


def view_delta_table(matrix=None):
    """Display a source x target delta table (compact)."""
    if matrix is None:
        if not os.path.exists(MATRIX_PATH):
            print("No matrix file found. Run --build first.")
            return
        matrix = load_json(MATRIX_PATH)

    cells = matrix['matrix']
    baselines = matrix['baselines']

    # Collect all sources that have data
    all_sources = set()
    for tgt, src_dict in cells.items():
        for src in src_dict:
            all_sources.add(src)

    # Only show tasks that have data as either source or target
    active_tasks = sorted(set(
        list(all_sources) + [t for t in cells.keys() if cells[t]]
    ), key=lambda t: TASK_ORDER.index(t) if t in TASK_ORDER else 999)

    if not active_tasks:
        print("No data in matrix.")
        return

    print(f"  Delta Table: row=source, column=target")
    print(f"  Legend: +0.12=helpful, -0.12=harmful, ..=no data, BL=baseline")
    print()

    # Print header
    header = f"{'Source':>12s} |"
    for tgt in active_tasks:
        header += f" {tgt:>8s}"
    print(header)
    print(f"{'='*12}-+-{'='*9*len(active_tasks)}")

    for src in active_tasks:
        # Check if source has any data as source
        has_data = False
        for tgt, src_dict in cells.items():
            if src in src_dict:
                has_data = True
                break
        if not has_data:
            continue

        row = f"{src:>12s} |"
        for tgt in active_tasks:
            cell_data = cells.get(tgt, {}).get(src)
            if cell_data:
                delta = cell_data['delta']
                n = cell_data['n']
                if delta > 0.05:
                    row += f" \033[32m{delta:>+7.3f}\033[0m"  # green
                elif delta < -0.05:
                    row += f" \033[31m{delta:>+7.3f}\033[0m"  # red
                else:
                    row += f" \033[90m{delta:>+7.3f}\033[0m"  # gray
            else:
                row += f" {'..':>8s}"
        print(row)


def view_delta_table_compact(matrix=None):
    """Display a super compact delta table -- no ANSI codes for server."""
    if matrix is None:
        if not os.path.exists(MATRIX_PATH):
            print("No matrix file found. Run --build first.")
            return
        matrix = load_json(MATRIX_PATH)

    cells = matrix['matrix']
    baselines = matrix['baselines']

    # Collect all sources
    all_sources = set()
    for tgt, src_dict in cells.items():
        for src in src_dict:
            all_sources.add(src)

    active_tasks = sorted(set(
        list(all_sources) + [t for t in cells.keys() if cells[t]]
    ), key=lambda t: TASK_ORDER.index(t) if t in TASK_ORDER else 999)

    if not active_tasks:
        print("No data.")
        return

    print(f"  Source\\Target | " + " | ".join(f"{t:>8s}" for t in active_tasks))
    print(f"  " + "-" * (14 + 11 * len(active_tasks)))

    for src in active_tasks:
        has_data = any(src in src_dict for src_dict in cells.values())
        if not has_data:
            continue
        row = f"  {src:>12s} |"
        for tgt in active_tasks:
            cell_data = cells.get(tgt, {}).get(src)
            if cell_data:
                d = cell_data['delta']
                n = cell_data['n']
                if d > 0.05:
                    marker = "+"
                elif d < -0.05:
                    marker = "-"
                else:
                    marker = "~"
                row += f" {marker}{abs(d):.2f}({n:2d}) |"
            else:
                row += f" {'..':>8s} |"
        print(row)


def view_detail(matrix=None):
    """Show detailed per-cell stats."""
    if matrix is None:
        if not os.path.exists(MATRIX_PATH):
            print("No matrix file found. Run --build first.")
            return
        matrix = load_json(MATRIX_PATH)

    cells = matrix['matrix']
    baselines = matrix['baselines']

    for tgt in sorted(cells.keys()):
        src_dict = cells[tgt]
        for src in sorted(src_dict.keys()):
            c = src_dict[src]
            bl = baselines.get(tgt, 0)
            print(f"  {src:>12s} -> {tgt:>12s}  "
                  f"D={c['delta']:+.3f}  "
                  f"avg={c['avg_reward']:.3f}  "
                  f"BL={bl:.2f}  "
                  f"n={c['n']:2d}  "
                  f"best={c['best_reward']:.2f}  "
                  f"worst={c['worst_reward']:.2f}  "
                  f"std={c['reward_std']:.3f}  "
                  f"type={c['primary_type']:>20s}  "
                  f"ok={c['n_success']}/{c['n']}")


def add_transfer(source, target, reward, status="success", tx_type="expand-within"):
    """Add a new transfer result to the matrix (incremental update)."""
    if not os.path.exists(MATRIX_PATH):
        print("No matrix file. Run --build first.")
        return

    matrix = load_json(MATRIX_PATH)
    baselines = matrix['baselines']
    cells = matrix['matrix']

    # Normalize reward
    reward = reward / 100.0 if reward > 1 else reward

    if target not in cells:
        cells[target] = {}
    if source not in cells[target]:
        # Need full cell data from scratch
        cells[target][source] = {
            'avg_reward': reward,
            'avg_reward_simple': reward,
            'n': 1,
            'n_success': 1 if status == 'success' else 0,
            'n_failed': 1 if status in ('failed', 'timeout') else 0,
            'best_reward': reward,
            'worst_reward': reward,
            'reward_std': 0.0,
            'delta': reward - baselines.get(target, 0),
            'delta_simple': reward - baselines.get(target, 0),
            'primary_type': tx_type,
        }
    else:
        cell = cells[target][source]
        # Update with weighted average
        old_n = cell['n']
        old_avg = cell['avg_reward_simple']
        cell['n'] = old_n + 1
        cell['avg_reward_simple'] = round((old_avg * old_n + reward) / cell['n'], 3)
        cell['best_reward'] = max(cell['best_reward'], reward)
        cell['worst_reward'] = min(cell['worst_reward'], reward)
        if status == 'success':
            cell['n_success'] = cell.get('n_success', 0) + 1
        else:
            cell['n_failed'] = cell.get('n_failed', 0) + 1
        cell['avg_reward'] = cell['avg_reward_simple']  # simplified
        cell['delta'] = cell['avg_reward'] - baselines.get(target, 0)
        cell['delta_simple'] = cell['delta']

    matrix['meta']['generated'] = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
    matrix['meta']['n_cells'] = sum(len(v) for v in cells.values())

    save_json(MATRIX_PATH, matrix)
    print(f"  Added: {source} -> {target}: reward={reward:.3f}, status={status}")
    cell = cells[target][source]
    print(f"  Now: n={cell['n']}, avg={cell['avg_reward']:.3f}, D={cell['delta']:+.3f}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 transfer_matrix.py --build           # Build/update matrix")
        print("  python3 transfer_matrix.py --view            # Show per-source view")
        print("  python3 transfer_matrix.py --view-table      # Show delta table")
        print("  python3 transfer_matrix.py --view-detail     # Show detailed stats")
        print("  python3 transfer_matrix.py --add <src> <tgt> <reward> [status] [type]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == '--build':
        m = update_matrix()
    elif cmd == '--view':
        view_matrix()
    elif cmd == '--view-table':
        view_delta_table_compact()
    elif cmd == '--view-detail':
        view_detail()
    elif cmd == '--add' and len(sys.argv) >= 4:
        add_transfer(sys.argv[2], sys.argv[3],
                     float(sys.argv[4]),
                     sys.argv[5] if len(sys.argv) > 5 else 'success',
                     sys.argv[6] if len(sys.argv) > 6 else 'expand-within')
    else:
        print(f"Unknown command: {cmd}")
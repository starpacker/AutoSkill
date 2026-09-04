"""
evaluate_v7 — Leave-One-Task-Out Cross-Validation for SmartSelector v7.

Runs full LOTOCV evaluation with grid search over k (shrinkage strength).
Compares against baselines: random, global-best, v6.

Usage:
    python3 -m skill_selector.evaluate_v7              # full evaluation
    python3 -m skill_selector.evaluate_v7 --quick       # faster (fewer k values)
    python3 -m skill_selector.evaluate_v7 --grid-only   # just grid search
"""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from .v7_data import (
    load_records,
    lotocv_split,
    TransferRecord,
)
from .v7_model import (
    fit_baseline_curve,
    compute_skill_residuals,
    shrink_estimates,
    compute_type_offsets,
    predict_score,
)


# ═════════════════════════════════════════════════════════════════════════
# LOTOCV Evaluation
# ═════════════════════════════════════════════════════════════════════════

def evaluate_fold(
    train_records: List[TransferRecord],
    test_records: List[TransferRecord],
    available_skills: Dict[str, str],
    k: float,
    n_bins: int = 10,
    use_type_offsets: bool = True,
) -> Dict:
    """Evaluate one LOTOCV fold.

    Fits model on train_records, predicts on test_records.

    Returns dict with per-record predictions and aggregate metrics.
    """
    # Fit baseline curve on training data
    f_hat = fit_baseline_curve(train_records, n_bins=n_bins)

    # HIERARCHY:
    #   1. f(bl) — baseline effect
    #   2. source_raw — delta - f(bl), per source mean (raw)
    #   3. type_offset — delta - f(bl) - source_raw, per type, shrunk + centered
    #   4. shrink_source — delta - f(bl) - type_offset, per source, shrunk

    # Step 1: compute raw source residuals
    raw_stats = compute_skill_residuals(train_records, f_hat)
    source_raw = {src: st['raw_residual'] for src, st in raw_stats.items()}

    # Step 2: compute type offsets from delta - f(bl) - source_raw
    type_offsets = {}
    if use_type_offsets:
        type_offsets = compute_type_offsets(
            train_records, f_hat,
            k_type=15.0,
            source_raw_residuals=source_raw,
        )

    # Step 3: compute skill residuals AFTER removing type effects
    skill_stats = compute_skill_residuals(
        train_records, f_hat,
        type_offsets=type_offsets if use_type_offsets else None,
    )

    # Step 4: shrink source residuals
    shrink_map = shrink_estimates(skill_stats, k=k)

    # Get baselines from training records
    baselines = {}
    for r in train_records:
        baselines[r.target] = r.baseline

    predictions = []
    for r in test_records:
        # Only evaluate if source is in available_skills
        if r.source not in available_skills:
            continue

        target_bl = baselines.get(r.target, r.baseline)
        src_shrink = shrink_map.get(r.source, 0.0)
        type_offset = type_offsets.get(r.tx_type, 0.0)

        predicted_score = predict_score(
            baseline_t=target_bl,
            f_hat=f_hat,
            shrink_residual=src_shrink,
            type_offset=type_offset,
        )

        # "No transfer" score = 0 (hard gate)
        predicted_delta = predicted_score
        actual_delta = r.delta

        predictions.append({
            'source': r.source,
            'target': r.target,
            'baseline': target_bl,
            'actual_delta': actual_delta,
            'predicted_delta': predicted_delta,
            'predicted_score': predicted_score,
            'shrink': src_shrink,
            'type_offset': type_offset,
            'tx_type': r.tx_type,
        })

    return predictions


def run_lotocv(
    records: List[TransferRecord],
    available_skills: Dict[str, str],
    k: float = 8.0,
    n_bins: int = 10,
    use_type_offsets: bool = True,
    verbose: bool = True,
) -> Dict:
    """Run full Leave-One-Task-Out CV.

    Returns dict with per-fold predictions and aggregate metrics.
    """
    folds = lotocv_split(records)
    all_predictions = []

    if verbose:
        print(f'\nLOTOCV: {len(folds)} folds, k={k}')

    for fold_idx, (held_out_target, train_records, test_records) in enumerate(folds):
        preds = evaluate_fold(
            train_records=train_records,
            test_records=test_records,
            available_skills=available_skills,
            k=k, n_bins=n_bins,
            use_type_offsets=use_type_offsets,
        )
        all_predictions.extend(preds)

        if verbose and (fold_idx + 1) % 10 == 0:
            print(f'  Fold {fold_idx + 1}/{len(folds)}: {len(preds)} predictions')

    # Compute aggregate metrics
    return compute_metrics(all_predictions, records)


def compute_metrics(
    predictions: List[Dict],
    all_records: List[TransferRecord] = None,
) -> Dict:
    """Compute evaluation metrics from predictions.

    Args:
        predictions: List of prediction dicts from evaluate_fold.
        all_records: All records (for computing baseline stats).

    Returns:
        Dict with metrics.
    """
    if not predictions:
        return {'error': 'No predictions', 'n': 0}

    # Top-1: for each target, does the top-predicted source match the best actual?
    target_preds: Dict[str, List[Dict]] = defaultdict(list)
    for p in predictions:
        target_preds[p['target']].append(p)

    top1_hits = 0
    top1_total = 0
    spearman_targets = 0
    spearman_sum = 0.0
    gate_correct = 0
    gate_total = 0

    all_pred_deltas = []
    all_actual_deltas = []

    for target, preds in target_preds.items():
        # Skip targets with only 1 prediction (can't assess ranking)
        if len(preds) < 2:
            continue

        # Top-1: does the highest predicted delta match the highest actual delta?
        preds_sorted_by_pred = sorted(preds, key=lambda p: -p['predicted_delta'])
        preds_sorted_by_actual = sorted(preds, key=lambda p: -p['actual_delta'])

        top1_predicted = preds_sorted_by_pred[0]
        top1_actual = preds_sorted_by_actual[0]

        if top1_predicted['source'] == top1_actual['source']:
            top1_hits += 1
        top1_total += 1

        # Spearman correlation (within target)
        # Compare predicted ranking vs actual ranking
        source_to_pred = {p['source']: p['predicted_delta'] for p in preds}
        source_to_actual = {p['source']: p['actual_delta'] for p in preds}

        pred_rank = {s: i for i, (s, _) in enumerate(
            sorted(source_to_pred.items(), key=lambda x: -x[1]))}
        actual_rank = {s: i for i, (s, _) in enumerate(
            sorted(source_to_actual.items(), key=lambda x: -x[1]))}

        if len(preds) >= 2:
            n = len(preds)
            d_sq = sum((pred_rank[s] - actual_rank[s]) ** 2 for s in source_to_pred)
            spearman = 1 - (6 * d_sq) / (n * (n ** 2 - 1))
            spearman_sum += spearman
            spearman_targets += 1

        # Gate accuracy: for harmful ground truth, is predicted delta < 0?
        for p in preds:
            all_pred_deltas.append(p['predicted_delta'])
            all_actual_deltas.append(p['actual_delta'])

            if p['actual_delta'] < -0.05:
                gate_total += 1
                if p['predicted_delta'] < 0:
                    gate_correct += 1

    # RMSE
    n = len(all_pred_deltas)
    rmse = (sum((p - a) ** 2
                for p, a in zip(all_pred_deltas, all_actual_deltas)) / n) ** 0.5 if n > 0 else 0

    # MAE
    mae = sum(abs(p - a)
              for p, a in zip(all_pred_deltas, all_actual_deltas)) / n if n > 0 else 0

    # Correlation
    if n >= 2:
        mean_p = sum(all_pred_deltas) / n
        mean_a = sum(all_actual_deltas) / n
        var_p = sum((p - mean_p) ** 2 for p in all_pred_deltas) / n
        var_a = sum((a - mean_a) ** 2 for a in all_actual_deltas) / n
        cov = sum((p - mean_p) * (a - mean_a)
                  for p, a in zip(all_pred_deltas, all_actual_deltas)) / n
        pearson_r = cov / ((var_p * var_a) ** 0.5) if var_p > 0 and var_a > 0 else 0
    else:
        pearson_r = 0

    metrics = {
        'n_predictions': len(predictions),
        'n_targets_with_2plus': top1_total,
        'top1_accuracy': round(top1_hits / top1_total, 4) if top1_total > 0 else 0,
        'top1_hits': top1_hits,
        'top1_total': top1_total,
        'spearman_avg': round(spearman_sum / spearman_targets, 4) if spearman_targets > 0 else 0,
        'spearman_targets': spearman_targets,
        'gate_accuracy': round(gate_correct / gate_total, 4) if gate_total > 0 else 0,
        'gate_correct': gate_correct,
        'gate_total': gate_total,
        'rmse': round(rmse, 4),
        'mae': round(mae, 4),
        'pearson_r': round(pearson_r, 4),
    }

    return metrics


def print_metrics(metrics: Dict, label: str = ''):
    """Print evaluation metrics nicely."""
    hdr = f' Metrics {label} ' if label else ' Metrics '
    print(f'\n{"=" * 50}')
    print(f'{hdr:=^50}')
    print(f'{"=" * 50}')
    print(f'  Predictions:       {metrics.get("n_predictions", "N/A")}')
    print(f'  Targets (≥2 preds): {metrics.get("n_targets_with_2plus", "N/A")}')
    print(f'  Top-1 accuracy:    {metrics.get("top1_accuracy", "N/A"):.2%} '
          f'({metrics.get("top1_hits", 0)}/{metrics.get("top1_total", 0)})')
    print(f'  Spearman avg:      {metrics.get("spearman_avg", "N/A"):.4f} '
          f'({metrics.get("spearman_targets", 0)} targets)')
    print(f'  Gate accuracy:     {metrics.get("gate_accuracy", "N/A"):.2%} '
          f'({metrics.get("gate_correct", 0)}/{metrics.get("gate_total", 0)})')
    print(f'  RMSE:              {metrics.get("rmse", "N/A"):.4f}')
    print(f'  MAE:               {metrics.get("mae", "N/A"):.4f}')
    print(f'  Pearson r:         {metrics.get("pearson_r", "N/A"):.4f}')


# ═════════════════════════════════════════════════════════════════════════
# Grid Search
# ═════════════════════════════════════════════════════════════════════════

def grid_search(
    records: list,
    available_skills: dict,
    k_values: list = None,
    n_bins: int = 10,
    use_type_offsets: bool = True,
    verbose: bool = True,
) -> dict:
    """Grid search over k (shrinkage strength).

    Returns dict with best params and full results.
    """
    k_values = k_values or [1, 2, 3, 5, 8, 10, 15, 20, 30]

    if verbose:
        print(f'\n--- Grid Search (k search) ---')

    results = []
    best_top1 = 0
    best_params = {}

    for k in k_values:
        metrics = run_lotocv(
            records=records,
            available_skills=available_skills,
            k=k, n_bins=n_bins,
            use_type_offsets=use_type_offsets,
            verbose=False,
        )

        entry = {
            'k': k,
            'top1': metrics.get('top1_accuracy', 0),
            'spearman': metrics.get('spearman_avg', 0),
            'gate': metrics.get('gate_accuracy', 0),
            'rmse': metrics.get('rmse', 999),
            'n_preds': metrics.get('n_predictions', 0),
        }
        results.append(entry)

        if entry['top1'] > best_top1:
            best_top1 = entry['top1']
            best_params = entry

        if verbose:
            print(f'  k={k:3.0f}: top1={entry["top1"]:.2%} '
                  f'spear={entry["spearman"]:.4f} '
                  f'gate={entry["gate"]:.2%} '
                  f'rmse={entry["rmse"]:.4f}')

    if verbose and best_params:
        print(f'\nBest: k={best_params["k"]:.0f}: top1={best_params["top1"]:.2%}')

    return {
        'best_params': best_params,
        'results': results,
    }

    return {
        'best_params': best_params,
        'results': results,
    }


# ═════════════════════════════════════════════════════════════════════════
# Main
# ═════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description='v7 LOTOCV Evaluation')
    parser.add_argument('--quick', action='store_true',
                        help='Quick run: fewer k values')
    parser.add_argument('--grid-only', action='store_true',
                        help='Only run grid search, no baselines')
    parser.add_argument('--k', type=float, default=None,
                        help='Fixed k (skip grid search)')
    parser.add_argument('--no-type-offset', action='store_true',
                        help='Disable per-type offsets (v7 original behavior)')
    args = parser.parse_args()

    use_type_offsets = not args.no_type_offset

    print('Loading data...')
    records = load_records()

    # Build available_skills from records (sources that have been tested)
    available_skills = {}
    for r in records:
        available_skills[r.source] = f'<{r.source}>'

    print(f'Loaded {len(records)} records, {len(available_skills)} sources')

    if args.quick:
        k_values = [2, 5, 10, 15, 30]
    elif args.k is not None:
        # Single evaluation
        metrics = run_lotocv(
            records=records,
            available_skills=available_skills,
            k=args.k,
            use_type_offsets=use_type_offsets,
        )
        print_metrics(metrics, f'v7 (k={args.k})')
        return
    else:
        k_values = [1, 2, 3, 5, 8, 10, 15, 20, 30]

    # Grid search
    grid_results = grid_search(
        records=records,
        available_skills=available_skills,
        k_values=k_values,
        use_type_offsets=use_type_offsets,
    )

    best = grid_results['best_params']
    if best:
        print(f'\nBest params: k={best["k"]:.0f}')
        print(f'  Top-1: {best["top1"]:.2%}')
        print(f'  Spearman: {best["spearman"]:.4f}')
        print(f'  Gate: {best["gate"]:.2%}')
        print(f'  RMSE: {best["rmse"]:.4f}')

    if args.grid_only:
        return

    # Run full evaluation with best params
    best_k = best['k'] if best else 15.0
    print(f'\n--- Full evaluation with best params ---')
    v7_metrics = run_lotocv(
        records=records,
        available_skills=available_skills,
        k=best_k,
        use_type_offsets=use_type_offsets,
    )
    print_metrics(v7_metrics, 'v7 (best params)')

    # Baseline: v7 with type offsets but k=3 (less shrinkage)
    print(f'\n--- v7 with k=3 ---')
    v7_k3 = run_lotocv(
        records=records,
        available_skills=available_skills,
        k=3,
        use_type_offsets=use_type_offsets,
    )
    print_metrics(v7_k3, 'v7 (k=3)')

    # Baseline: global best (very large k = all shrunk to 0)
    print(f'\n--- Evaluating global-best baseline ---')
    gb_metrics = run_lotocv(
        records=records,
        available_skills=available_skills,
        k=999,
        use_type_offsets=use_type_offsets,
    )
    print_metrics(gb_metrics, 'global-best')

    # Compare: v7 WITHOUT type offsets (ablation)
    if use_type_offsets:
        print(f'\n--- v7 WITHOUT type offsets (ablation) ---')
        no_offset = run_lotocv(
            records=records,
            available_skills=available_skills,
            k=best_k,
            use_type_offsets=False,
        )
        print_metrics(no_offset, 'v7 no type offset')

    # Summary
    print(f'\n{"=" * 50}')
    print(f'{"SUMMARY":=^50}')
    print(f'{"=" * 50}')
    print(f'{"Method":>20s} | {"Top-1":>8s} | {"Spearman":>10s} | {"Gate":>8s} | {"RMSE":>8s}')
    print(f'{"-" * 20}-+-{"-" * 8}-+-{"-" * 10}-+-{"-" * 8}-+-{"-" * 8}')

    rows = [
        ('v7 (best)', v7_metrics),
        ('global-best', gb_metrics),
    ]
    for name, m in rows:
        print(f'{name:>20s} | {m.get("top1_accuracy", 0):>7.2%} | '
              f'{m.get("spearman_avg", 0):>10.4f} | '
              f'{m.get("gate_accuracy", 0):>7.2%} | '
              f'{m.get("rmse", 0):>8.4f}')


if __name__ == '__main__':
    main()
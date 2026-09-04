"""
SmartSelectorV7 — data-driven skill selector with isotonic baseline curve
and James-Stein shrinkage.

Ablation-verified: only f(bl) + shrinkage(k) contribute.
compat_tag and pair_boost removed (zero marginal benefit in LOTOCV).

Inherits the same interface as v6 for easy swapping.

Usage:
    selector = SmartSelectorV7()
    source, confidence = selector.select_skill(
        target_task='da-13-6',
        available_skills={'da-13-5': '/path/to/skill'},
        similarity_matrix=None,  # unused in v7
    )
"""

import json
import os
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from .v7_data import (
    load_records,
    get_baselines,
    TransferRecord,
)
from .v7_model import (
    fit_baseline_curve,
    compute_skill_residuals,
    shrink_estimates,
    compute_type_offsets,
    predict_score,
    select_best_skill,
    model_to_json,
    model_from_json,
    sample_f_hat,
)

# ── Default paths (server-side) ──────────────────────────────────────────
RESULTS_INDEX_PATH = "/data/yjh/skill-transfer-eval/results_index.json"
BIO_DIR = "/data/yjh/biomnibench-organized"
GENERALIZED_SKILLS_DIR = "/data/yjh/skill-transfer-eval/generalized_skills"
MODEL_CACHE_PATH = "/data/yjh/skill-transfer-eval/v7_model_cache.json"


class SmartSelectorV7:
    """SmartSelector v7 — statistically grounded, ablation-verified skill selector.

    Core:
      - Isotonic regression baseline effect curve (no more hand-coded bins)
      - James-Stein shrinkage for per-skill estimates (no more hand-coded tiers)
      - "No transfer" as a natural candidate with score = 0

    Signal: score(t,s) = f_hat(baseline_t) + shrink_residual(s)

    Based on LOTOCV ablation: pair_boost and compat_tag contributed zero
    marginal benefit. Only f(bl) + shrinkage(k) matter.
    """

    def __init__(self,
                 results_index_path: Optional[str] = None,
                 bio_dir: Optional[str] = None,
                 generalized_skills_dir: Optional[str] = None,
                 model_cache_path: Optional[str] = None,
                 k: float = 8.0,
                 n_bins: int = 10,
                 use_type_offsets: bool = True,
                 default_type: str = 'generalized-transfer',
                 auto_fit: bool = True,
                 min_score_threshold: float = 0.05):
        """Initialize SmartSelectorV7.

        Args:
            results_index_path: Path to results_index.json.
            bio_dir: Path to BioDSBench tasks directory.
            generalized_skills_dir: Path to generalized skills directory.
            model_cache_path: Path to cache fitted model.
            k: Shrinkage strength (James-Stein k parameter). Default 8
               (LOTOCV-optimal: top-1=88.46%, gate=96.15%).
            n_bins: Number of bins for isotonic regression preprocessing.
            use_type_offsets: If True, apply per-transfer-type offsets.
            default_type: Default transfer type when selecting a skill.
            auto_fit: If True, automatically fit model on init.
            min_score_threshold: Minimum score to recommend a skill.
                             Default 0.05 (hard rejection).
        """
        self.results_index_path = results_index_path or RESULTS_INDEX_PATH
        self.bio_dir = bio_dir or BIO_DIR
        self.generalized_skills_dir = generalized_skills_dir or GENERALIZED_SKILLS_DIR
        self.model_cache_path = model_cache_path or MODEL_CACHE_PATH

        self.k = k
        self.n_bins = n_bins
        self.use_type_offsets = use_type_offsets
        self.default_type = default_type
        self.min_score_threshold = min_score_threshold

        # Fitted model
        self.f_hat = None
        self.shrink_map: Dict[str, float] = {}
        self.skill_stats: Dict[str, dict] = {}
        self.type_offsets: Dict[str, float] = {}
        self.baselines: Dict[str, float] = {}
        self.records: List[TransferRecord] = []

        # Fitted flag
        self._fitted = False

        if auto_fit:
            self.fit()

    # ── Model Fitting ────────────────────────────────────────────────────

    def fit(self) -> None:
        """Load data and fit the v7 model.

        Tries to load from cache first. If cache is missing or stale,
        refits from scratch.
        """
        # Try cache
        if os.path.exists(self.model_cache_path):
            try:
                self._load_cache()
                print(f'[SmartSelector v7] Loaded model from cache '
                      f'({self.model_cache_path})')
                return
            except Exception as e:
                print(f'[SmartSelector v7] Cache load failed: {e}, refitting')

        # Load data
        self.records = load_records(self.results_index_path)
        self.baselines = get_baselines(self.results_index_path)

        if not self.records:
            print('[SmartSelector v7] WARNING: No records loaded, model will be empty')
            self._fitted = True
            return

        # Fit baseline effect curve
        self.f_hat = fit_baseline_curve(self.records, n_bins=self.n_bins)

        # HIERARCHY:
        #   1. f(bl) — baseline effect
        #   2. source_raw — delta - f(bl), per source mean (raw, no shrinkage)
        #   3. type_offset — delta - f(bl) - source_raw, per type, shrunk + centered
        #   4. shrink_source — delta - f(bl) - type_offset, per source, shrunk

        # Step 1: compute raw source residuals (delta - f(bl))
        raw_stats = compute_skill_residuals(self.records, self.f_hat)
        source_raw = {src: st['raw_residual'] for src, st in raw_stats.items()}

        # Step 2: compute type offsets from delta - f(bl) - source_raw
        if self.use_type_offsets:
            self.type_offsets = compute_type_offsets(
                self.records, self.f_hat,
                k_type=15.0,
                source_raw_residuals=source_raw,
            )
            print(f'[SmartSelector v7] Type offsets: {self.type_offsets}')
        else:
            self.type_offsets = {}

        # Step 3: compute skill residuals AFTER removing type effects
        self.skill_stats = compute_skill_residuals(
            self.records, self.f_hat,
            type_offsets=self.type_offsets if self.use_type_offsets else None,
        )

        # Step 4: shrink source residuals
        self.shrink_map = shrink_estimates(self.skill_stats, k=self.k)

        # Cache
        self._save_cache()

        self._fitted = True

        n_src = len(self.shrink_map)
        n_tgt = len(self.baselines)
        print(f'[SmartSelector v7] Fitted: {len(self.records)} records, '
              f'{n_src} sources, {n_tgt} targets, k={self.k}')

    def _save_cache(self) -> None:
        """Save fitted model to cache JSON."""
        if self.f_hat is None:
            return
        points = sample_f_hat(self.f_hat)
        data = model_to_json(
            f_hat_points=points,
            shrink_map=self.shrink_map,
            skill_stats=self.skill_stats,
            baselines=self.baselines,
            params={
                'k': self.k,
                'n_bins': self.n_bins,
                'n_records': len(self.records),
            },
            type_offsets=self.type_offsets if self.use_type_offsets else None,
        )
        try:
            with open(self.model_cache_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f'[SmartSelector v7] WARNING: Could not save cache: {e}')

    def _load_cache(self) -> None:
        """Load fitted model from cache JSON."""
        with open(self.model_cache_path) as f:
            data = json.load(f)

        # Restore model components
        f_hat, shrink_map, skill_stats, baselines, params, type_offsets = model_from_json(data)
        self.f_hat = f_hat
        self.shrink_map = shrink_map
        self.skill_stats = skill_stats
        self.baselines = baselines
        self.type_offsets = type_offsets or {}

        # Restore params
        self.k = params.get('k', self.k)
        self.n_bins = params.get('n_bins', self.n_bins)

        # Reload records
        self.records = load_records(self.results_index_path)

        self._fitted = True

    # ── Selection ────────────────────────────────────────────────────────

    def select_skill(
        self,
        target_task: str,
        available_skills: Dict[str, str],
        similarity_matrix: Optional[Dict[str, Dict[str, float]]] = None,
        target_baseline: Optional[float] = None,
        transfer_type: Optional[str] = None,
    ) -> Tuple[Optional[str], float]:
        """Select the best skill for a target task using v7 strategy.

        Args:
            target_task: Target task ID.
            available_skills: Dict mapping source_id -> path to SKILL.md.
            similarity_matrix: Unused in v7 (kept for interface compatibility).
            target_baseline: Optional override for baseline. If None, uses
                             stored baselines.
            transfer_type: Transfer type. If None, uses default_type.
                           Affects the type offset applied to scores.

        Returns:
            Tuple of (selected_source, score).
            selected_source may be None (meaning "no transfer").
            score is the v7 score of the selected source (or 0 for none).
        """
        if not self._fitted:
            raise RuntimeError('SmartSelectorV7 not fitted. Call fit() first.')

        if self.f_hat is None:
            # No data, fall back to no transfer
            print(f'[SmartSelector v7] No fitted model, recommending no transfer')
            return None, 0.0

        target_bl = (target_baseline if target_baseline is not None
                     else self.baselines.get(target_task, 0.5))

        tx_type = transfer_type or self.default_type
        type_offset = self.type_offsets.get(tx_type, 0.0)

        # Select best skill
        best_source, best_score, no_transfer_score = select_best_skill(
            baseline_t=target_bl,
            f_hat=self.f_hat,
            shrink_map=self.shrink_map,
            available_skills=available_skills,
            type_offset=type_offset,
            min_score_threshold=self.min_score_threshold,
        )

        # Print ranking
        print(f'[SmartSelector v7] Target={target_task} (bl={target_bl:.2f}, type={tx_type})')
        print(f'  f_hat({target_bl:.2f}) = {self.f_hat(target_bl):+.4f}')
        print(f'  type_offset({tx_type}) = {type_offset:+.4f}')

        # Score all candidates for display
        candidates = []
        for src_name in available_skills:
            score = predict_score(
                baseline_t=target_bl,
                f_hat=self.f_hat,
                shrink_residual=self.shrink_map.get(src_name, 0.0),
                type_offset=type_offset,
            )
            candidates.append({
                'source': src_name,
                'score': score,
                'shrink': self.shrink_map.get(src_name, 0.0),
            })

        candidates.sort(key=lambda c: -c['score'])
        for c in candidates[:5]:
            print(f'  {c["source"]:>12s}: score={c["score"]:.4f} '
                  f'(shrink={c["shrink"]:+.4f})')

        if best_source is None:
            print(f'[SmartSelector v7] No skill beats "no transfer" (score=0)')
            return None, 0.0

        print(f'[SmartSelector v7] WINNER: {best_source} (score={best_score:.4f})')
        return best_source, best_score


# ── CLI test ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys

    # Discover skills
    skills_dir = GENERALIZED_SKILLS_DIR
    available = {}
    if os.path.isdir(skills_dir):
        for d in os.listdir(skills_dir):
            dpath = os.path.join(skills_dir, d)
            skill_file = os.path.join(dpath, 'SKILL.md')
            if os.path.isdir(dpath) and os.path.isfile(skill_file):
                available[d] = skill_file

    if not available:
        print(f'[SmartSelector v7] No skills found at {skills_dir}')
        print('  (This is expected if running locally without server data)')

    selector = SmartSelectorV7()

    # If a target is given on CLI, run selection
    if len(sys.argv) > 1:
        target = sys.argv[1]
        print(f'\n--- Selecting skill for {target} ---')
        source, confidence = selector.select_skill(target, available)
        print(f'\nResult: source={source}, confidence={confidence:.4f}')
    else:
        # Dry-run on all targets
        print(f'\n--- Dry-run on all targets ---')
        targets = sorted(selector.baselines.keys())
        results = []
        for t in targets:
            source, score = selector.select_skill(t, available)
            results.append((t, source, score))
            bl = selector.baselines.get(t, 0)
            src_str = source or 'NONE'
            print(f'  {t:>10s}: bl={bl:.2f} -> {src_str} (score={score:.4f})')

        # Summary
        n_selected = sum(1 for _, s, _ in results if s is not None)
        print(f'\nSelected: {n_selected}/{len(results)}')
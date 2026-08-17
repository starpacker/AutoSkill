"""SmartSelector v5 - tightened gate, multi-source, pre-filter harmful.

Strategy: similarity + per-pair history + reputation + category + timeout + baseline gating  
  1. Load ALL historical transfer data (results_index.json transfers)
     to find per-pair (source->target) historical results.
  2. Load task categories from task.toml (category + task_type).
  3. Load timeout history from results_index.json transfers.
  4. Score each candidate source:
     - similarity (dynamic weight based on target baseline)
     - per-pair history (variance-aware: penalize inconsistent results)
     - reputation (graduated tier system, not binary)
     - category matching bonus (+0.08 same category, +0.12 same category+type)
     - timeout penalty (-0.10 per timeout, max -0.30) + diversity bonus
     - baseline gating: bl>0.80 → skip all, bl>0.65 → dynamic penalty
     - pre-filter: exclude sources with avg_delta < -0.10
  5. For targets with rich pair history (>=2), heavily weight per-pair data
     but adjust for variance (inconsistent pairs get lower weight).
  6. Low-confidence fallback: if confidence < 0.30, suggest no-skill baseline.
  7. Multi-source fallback: if confidence 0.30-0.50, try top-2 sources.
  8. Variance-aware: high-variance pairs (range > 0.30) are treated as
     unreliable, their pair_avg weight is reduced.
  9. Timeout diversity: when a target has timeout history, prefer sources
     from different families to avoid repeating failures.
"""
import json
import os
import statistics
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from .base import SkillSelector


class SmartSelector(SkillSelector):
    """Skill selector that learns from historical transfer results.

    Loads both per-source stats (history_data.json) and per-pair transfer
    data (results_index.json) to make better selections. Per-pair data
    is the strongest signal: if source X has been tried on target Y and
    worked well, strongly prefer it.
    """

    def __init__(self, history_data_path: Optional[str] = None,
                 results_index_path: Optional[str] = None):
        self.history_data_path: Optional[str] = None
        self.results_index_path: Optional[str] = None
        self.history_data: Dict[str, dict] = {}
        self.baselines: Dict[str, float] = {}
        self.available_skills: Dict[str, str] = {}

        # Per-pair transfer history: {target: {source: [rewards]}}
        self.pair_history: Dict[str, Dict[str, List[float]]] = {}
        # Task categories: {task_id: {'category': str, 'task_type': str}}
        self.task_categories: Dict[str, Dict[str, str]] = {}
        # Timeout tracking: {target: [source1, source2, ...]}
        self.timeout_pairs: Dict[str, List[str]] = {}
        self._load_history(history_data_path)
        self._load_transfer_data(results_index_path)
        self._load_task_categories()
        self._load_timeout_data()

    def _load_history(self, path: Optional[str] = None) -> None:
        """Load historical transfer data from JSON file."""
        if path is None:
            candidates = [
                '/data/yjh/skill-transfer-eval/history_data.json',
                os.path.join(os.path.dirname(__file__), 'history_data.json'),
                'history_data.json',
            ]
            for c in candidates:
                if os.path.exists(c):
                    path = c
                    break

        self.history_data_path = path
        if path and os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            self.history_data = data.get('per_source_stats', {})
            self.baselines = data.get('baselines', {})
            print(f'[SmartSelector] Loaded history: {len(self.history_data)} sources, '
                  f'{len(self.baselines)} baselines from {path}')
        else:
            print(f'[SmartSelector] No history data found at {path}, starting fresh')

    def _load_transfer_data(self, path: Optional[str] = None) -> None:
        """Load per-pair transfer results from results_index.json."""
        if path is None:
            candidates = [
                '/data/yjh/skill-transfer-eval/results_index.json',
                os.path.join(os.path.dirname(__file__), 'results_index.json'),
                '../results_index.json',
            ]
            for c in candidates:
                if os.path.exists(c):
                    path = c
                    break

        self.results_index_path = path
        if not path or not os.path.exists(path):
            print(f'[SmartSelector] No results_index found at {path}')
            return

        with open(path) as f:
            data = json.load(f)

        transfers = data.get('transfers', [])
        for tx in transfers:
            src = tx.get('source')
            tgt = tx.get('target')
            rew = tx.get('reward')
            if src and tgt and rew is not None:
                self.pair_history.setdefault(tgt, {})
                self.pair_history[tgt].setdefault(src, [])
                self.pair_history[tgt][src].append(rew)

        # Also load baselines from all_results.json if available
        if not self.baselines:
            all_results_path = path.replace('results_index.json',
                                            'summary/all_results.json')
            if os.path.exists(all_results_path):
                try:
                    with open(all_results_path) as f:
                        ad = json.load(f)
                    for t_entry in ad.get('tasks', []):
                        tid = t_entry.get('task_id', '')
                        bl = [r.get('reward', 0)
                              for r in t_entry.get('baseline', [])]
                        if bl:
                            import statistics
                            self.baselines[tid] = statistics.mean(bl)
                except Exception as e:
                    print(f'[SmartSelector] Failed to load all_results.json: {e}')

        print(f'[SmartSelector] Loaded pair history: {len(self.pair_history)} targets, '
              f'{sum(len(v) for v in self.pair_history.values())} source-target pairs')

    def _load_task_categories(self, bio_dir: str = '/data/yjh/biomnibench-organized') -> None:
        """Load task category and type from task.toml files."""
        if not os.path.isdir(bio_dir):
            print(f'[SmartSelector] No bio directory at {bio_dir}, skipping categories')
            return
        for task_id in os.listdir(bio_dir):
            toml_path = os.path.join(bio_dir, task_id, 'task.toml')
            if os.path.isfile(toml_path):
                with open(toml_path) as f:
                    content = f.read()
                cat = None
                ttype = None
                for line in content.split('\n'):
                    line_stripped = line.strip()
                    if line_stripped.startswith('category '):
                        cat = line_stripped.split('=')[1].strip().strip('"')
                    elif line_stripped.startswith('task_type '):
                        ttype = line_stripped.split('=')[1].strip().strip('"')
                if cat or ttype:
                    self.task_categories[task_id] = {
                        'category': cat or '',
                        'task_type': ttype or '',
                    }
        if self.task_categories:
            print(f'[SmartSelector] Loaded categories for {len(self.task_categories)} tasks')

    def _load_timeout_data(self) -> None:
        """Load timeout history from results_index.json transfers."""
        if not self.results_index_path or not os.path.exists(self.results_index_path):
            return
        try:
            with open(self.results_index_path) as f:
                data = json.load(f)
            for tx in data.get('transfers', []):
                if tx.get('status') == 'timeout':
                    src = tx.get('source')
                    tgt = tx.get('target')
                    if src and tgt:
                        self.timeout_pairs.setdefault(tgt, {})
                        self.timeout_pairs[tgt][src] = self.timeout_pairs[tgt].get(src, 0) + 1
            if self.timeout_pairs:
                total = sum(len(v) for v in self.timeout_pairs.values())
                print(f'[SmartSelector] Loaded timeout data: {total} timeout pairs')
        except Exception as e:
            print(f'[SmartSelector] Failed to load timeout data: {e}')

    def _save_history(self) -> None:
        """Persist current history data to disk."""
        if not self.history_data_path:
            print('[SmartSelector] No history path set, cannot save')
            return
        try:
            data = {
                'per_source_stats': self.history_data,
                'baselines': self.baselines,
            }
            with open(self.history_data_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f'[SmartSelector] Saved history to {self.history_data_path}')
        except Exception as e:
            print(f'[SmartSelector] Failed to save history: {e}')

    def update_history(self, source: str, target: str, reward: float,
                       baseline: float, save: bool = True) -> None:
        """Record the result of a skill transfer evaluation.

        This updates the source skill's historical statistics so that
        future selections benefit from this experience.

        Args:
            source: The source task whose skill was used.
            target: The target task that was evaluated.
            reward: The reward obtained (0-1).
            baseline: The target's baseline score (0-1).
            save: Whether to persist to disk immediately.
        """
        delta = round(reward - baseline, 3)
        if delta > 0.05:
            verdict = 'helpful'
        elif delta < -0.05:
            verdict = 'harmful'
        else:
            verdict = 'neutral'

        stats = self.history_data.setdefault(source, {
            'helpful': 0, 'harmful': 0, 'neutral': 0, 'n': 0,
            'avg_delta': 0.0, 'helpful_ratio': 0.0,
        })
        stats[verdict] += 1
        stats['n'] += 1
        old_avg = stats.get('avg_delta', 0.0)
        old_n = stats['n'] - 1
        if old_n > 0:
            stats['avg_delta'] = round((old_avg * old_n + delta) / stats['n'], 3)
        else:
            stats['avg_delta'] = delta
        stats['helpful_ratio'] = round(stats['helpful'] / stats['n'], 3)

        # Also update pair history
        self.pair_history.setdefault(target, {})
        self.pair_history[target].setdefault(source, [])
        self.pair_history[target][source].append(reward)

        print(f'[SmartSelector] Feedback: {source} -> {target} '
              f'reward={reward:.3f} baseline={baseline:.3f} '
              f'delta={delta:+.3f} [{verdict.upper()}]')
        print(f'[SmartSelector] Source "{source}" now: '
              f'n={stats["n"]} helpful={stats["helpful"]} '
              f'harms={stats["harmful"]} neut={stats["neutral"]} '
              f'avg_delta={stats["avg_delta"]:+.3f}')

        if save:
            self._save_history()

    def _get_pair_score(self, target: str, source: str) -> Tuple[float, int]:
        """Get the historical score for this specific source-target pair.

        Returns:
            Tuple of (avg_reward, count). If no history, (0.0, 0).
        """
        target_history = self.pair_history.get(target, {})
        rewards = target_history.get(source, [])
        if not rewards:
            return 0.0, 0
        return sum(rewards) / len(rewards), len(rewards)

    def select_skill(
        self,
        target_task: str,
        available_skills: Dict[str, str],
        similarity_matrix: Dict[str, Dict[str, float]],
    ) -> Tuple[Optional[str], float]:
        """Select the best skill using v5 strategy: tightened gate, pre-filter harmful, multi-source fallback."""
        self.available_skills = available_skills
        target_bl = self.baselines.get(target_task, 0.5)
        target_sims = similarity_matrix.get(target_task, {})

        # ── Improvement v5.1: Tighter baseline gating ──
        # bl>0.80 → skip (was 0.85 in v4, v4 had 2 harmful at bl=0.80 and 0.85)
        if target_bl > 0.80:
            print(f'[SmartSelector v5] Target={target_task} bl={target_bl:.3f} > 0.80, '
                  f'skipping skill transfer (no room for improvement)')
            return None, 0.0

        # Get target category info
        target_cat = self.task_categories.get(target_task, {})

        # Check if target has timeout history
        target_timeouts = self.timeout_pairs.get(target_task, {})

        # Check if we have per-pair history for this target
        has_pair_history = target_task in self.pair_history and \
            any(s in available_skills for s in self.pair_history[target_task])

        candidates = []
        for src_name, src_path in available_skills.items():
            sim = target_sims.get(src_name, 0.0)
            src_stats = self.history_data.get(src_name, {})
            n = src_stats.get('n', 0)
            avg_delta = src_stats.get('avg_delta', 0.0)
            helpful_ratio = src_stats.get('helpful_ratio', 0.0)
            harmful_count = src_stats.get('harmful', 0)

            # ── Component 1: Similarity (always available) ──
            sim_score = sim

            # ── Component 2: Per-pair history (variance-aware) ──
            pair_avg, pair_n = self._get_pair_score(target_task, src_name)

            # ── Improvement 3: Variance awareness ──
            pair_variance_penalty = 0.0
            if pair_n >= 2:
                target_history = self.pair_history.get(target_task, {})
                rewards = target_history.get(src_name, [])
                if len(rewards) >= 2:
                    r_min = min(rewards)
                    r_max = max(rewards)
                    r_range = r_max - r_min
                    # High variance → unreliable signal, reduce effective pair_avg weight
                    if r_range > 0.30:
                        # Inconsistent results: treat as weaker signal
                        pair_variance_penalty = -0.08
                        print(f'    [v5] {src_name}->{target_task}: high variance '
                              f'range={r_range:.2f}, penalty={pair_variance_penalty:.2f}')
                    elif r_range > 0.15:
                        pair_variance_penalty = -0.03

            pair_score = pair_avg + pair_variance_penalty  # 0.0 if no history

            # ── Component 3: Reputation (graduated tier system) ──
            # ── Improvement 2: Graduated reputation ──
            rep_score = 0.0
            if n >= 5:
                # Lots of data: use reliable avg_delta scaled
                if avg_delta > 0.10:
                    rep_score = 0.10  # Excellent source
                elif avg_delta > 0.05:
                    rep_score = 0.06  # Good source
                elif avg_delta > -0.05:
                    rep_score = 0.0   # Neutral source
                elif avg_delta > -0.15:
                    rep_score = -0.08  # Mildly harmful
                else:
                    rep_score = -0.15  # Bad source
            elif n >= 3:
                # Moderate data: use with caution
                harmful_ratio = harmful_count / n
                if harmful_ratio > 0.4 and avg_delta < -0.05:
                    rep_score = -0.12
                elif helpful_ratio > 0.3 and avg_delta > 0.05:
                    rep_score = 0.06
                else:
                    rep_score = 0.0
            elif n >= 1:
                # Limited data: small signal
                rep_score = min(0.05, avg_delta * 0.1)

            # ── Component 4: Category matching bonus ──
            cat_bonus = 0.0
            src_cat = self.task_categories.get(src_name, {})
            if target_cat and src_cat:
                if target_cat.get('category') and src_cat.get('category') == target_cat['category']:
                    cat_bonus = 0.08
                    if target_cat.get('task_type') and src_cat.get('task_type') == target_cat['task_type']:
                        cat_bonus = 0.12

            # ── Component 5: Timeout penalty + diversity bonus ──
            timeout_penalty = 0.0
            if src_name in target_timeouts:
                timeout_count = target_timeouts[src_name]
                timeout_penalty = -0.10 * min(timeout_count, 3)

            # ── Improvement 4: Timeout diversity bonus ──
            # When a target has timeout history, prefer sources from different families
            diversity_bonus = 0.0
            if target_timeouts:
                src_family = src_name.split('-')[0] if '-' in src_name else src_name
                timeout_families = set()
                for to_src in target_timeouts:
                    fam = to_src.split('-')[0] if '-' in to_src else to_src
                    timeout_families.add(fam)
                if src_family not in timeout_families:
                    diversity_bonus = 0.05  # Prefer fresh family

            # ── Improvement v5.3: Pre-filter harmful sources ──
            # Exclude sources with avg_delta < -0.10 (proven harmful)
            pre_filtered = list(candidates)
            harmful_sources = []
            for src in list(candidates):
                historical = self.pair_history.get(target_task, {}).get(src, [])
                if historical and len(historical) >= 1:
                    avg_delta = statistics.mean(historical)
                    if avg_delta < -0.10:
                        harmful_sources.append((src, avg_delta))
                        pre_filtered.remove(src)
            if harmful_sources:
                print(f'[SmartSelector v5] Pre-filtered {len(harmful_sources)} harmful sources: '
                      f'{", ".join(f"{s}(d={d:.3f})" for s, d in harmful_sources)}')
            candidates = pre_filtered
            if not candidates:
                print(f'[SmartSelector v5] All sources pre-filtered as harmful, '
                      f'skipping skill transfer')
                return None, 0.0

            # ── Baseline gating penalty ──
            # ── Improvement v5.2: Tightened baseline penalty ──
            baseline_penalty = 0.0
            if target_bl > 0.65:
                penalty_strength = (target_bl - 0.65) / 0.15 * 0.15  # 0 to -0.15 (was 0.70/0.10)
                baseline_penalty = -min(0.15, penalty_strength)

            # ── Dynamic weight based on target baseline ──
            # Low baseline: trust similarity more (exploration)
            # Medium baseline: trust pair history more (exploitation)
            if target_bl < 0.60:
                sim_weight, pair_weight, rep_weight = 0.70, 0.20, 0.10
            elif target_bl < 0.75:
                sim_weight, pair_weight, rep_weight = 0.50, 0.35, 0.15
            else:
                sim_weight, pair_weight, rep_weight = 0.25, 0.55, 0.20

            # ── Combined score ──
            if has_pair_history and pair_n >= 2:
                score = (sim_score * sim_weight +
                         pair_score * pair_weight +
                         rep_score * rep_weight)
                # Add extra boost for proven pairs
                if pair_avg > 0.60 and pair_variance_penalty == 0:
                    score += 0.10
                elif pair_avg > 0.40 and pair_variance_penalty == 0:
                    score += 0.05
            elif pair_n == 1:
                score = (sim_score * 0.40 +
                         pair_score * 0.30 +
                         rep_score * 0.30)
            else:
                score = (sim_score * 0.70 +
                         rep_score * 0.30)

            # Apply all modifiers
            score += cat_bonus
            score += timeout_penalty
            score += diversity_bonus
            score += baseline_penalty

            # Baseline bonus: for low-baseline targets, prefer proven sources
            if target_bl < 0.50 and pair_n >= 2 and pair_avg > target_bl:
                score += 0.05 * (1.0 - target_bl)

            candidates.append((
                src_name, score, sim_score, pair_score, pair_n,
                rep_score, n, avg_delta, src_stats, cat_bonus, timeout_penalty,
                diversity_bonus, baseline_penalty, pair_variance_penalty
            ))

        if not candidates:
            return None, 0.0

        candidates.sort(key=lambda x: -x[1])
        best = candidates[0]

        # Print top 5 candidates
        print(f'[SmartSelector v5] Target={target_task} (bl={target_bl:.2f}) '
              f'pair_history={has_pair_history} cat={target_cat.get("category","")} '
              f'bl_penalty={baseline_penalty:.2f}')
        for name, score, sim_s, pair_s, pn, rep_s, gn, gd, _, cb, tp, db, bp, vp in candidates[:5]:
            pair_str = f'pair_avg={pair_s:.2f}(n={pn})' if pn > 0 else 'no-pair'
            rep_str = f'rep={rep_s:+.2f}' if gn >= 2 else ''
            cat_str = f'cat={cb:+.2f}' if cb != 0 else ''
            to_str = f'to={tp:+.2f}' if tp != 0 else ''
            div_str = f'div={db:+.2f}' if db != 0 else ''
            var_str = f'var={vp:+.2f}' if vp != 0 else ''
            print(f'  {name:>12s}: score={score:.3f} (sim={sim_s:.2f} '
                  f'{pair_str} {rep_str} {cat_str} {to_str} {div_str} {var_str})')
        print(f'[SmartSelector v5] WINNER: {best[0]} (score={best[1]:.3f})')

        # ── Confidence calibration ──
        confidence = max(0.0, min(1.0, best[1]))
        # Boost confidence when multiple strong signals align
        if best[12] >= 0:  # baseline_penalty >= 0 (i.e., target_bl <= 0.65)
            if best[9] > 0 and best[4] >= 2 and best[3] > 0.60:
                confidence = min(1.0, confidence + 0.10)
            if best[10] < 0:
                confidence = max(0.0, confidence - 0.15)
        if best[13] < 0:  # high variance penalty
            confidence = max(0.0, confidence - 0.10)
        # Low confidence floor for low similarity
        if best[2] < 0.30:
            confidence = min(confidence, 0.40)

        # ── Improvement v5.4: Multi-source fallback ──
        # If confidence is moderate (0.30-0.50), try top-2 sources
        # If confidence is very low (<0.30), suggest no-skill baseline
        if confidence < 0.30:
            print(f'[SmartSelector v5] Confidence={confidence:.3f} < 0.30, '
                  f'falling back to no-skill baseline')
            return None, 0.0
        elif confidence < 0.50 and len(candidates) >= 2:
            # Check if top-2 candidates both have positive pair history
            src1 = candidates[0]
            src2 = candidates[1]
            pair1_avg, pair1_n = src1[3], src1[4]  # pair_score, pair_n
            pair2_avg, pair2_n = src2[3], src2[4]
            if pair1_avg > 0 and pair2_avg > 0 and pair1_n >= 1 and pair2_n >= 1:
                print(f'[SmartSelector v5] Multi-source fallback: '
                      f'{src1[0]}(p={pair1_avg:.3f},n={pair1_n}) + '
                      f'{src2[0]}(p={pair2_avg:.3f},n={pair2_n}) '
                      f'for confidence={confidence:.3f}')
                return best[0], confidence + 0.10  # Boost confidence for ensemble

        return best[0], confidence

    def get_name(self) -> str:
        return 'SmartSelector'

    def describe_selection(self, target_task: str, selected_source: Optional[str],
                          confidence: float) -> str:
        if selected_source is None:
            bl = self.baselines.get(target_task, '?')
            if bl != '?' and bl > 0.80:
                return (f'[SmartSelector v5] Skipped "{target_task}" '
                        f'(baseline={bl:.3f} > 0.80, no room for improvement)')
            return (f'[SmartSelector v5] No suitable skill found for "{target_task}" '
                    f'(confidence too low)')
        bl = self.baselines.get(target_task, '?')
        src_stats = self.history_data.get(selected_source, {})
        n = src_stats.get('n', 0)
        avg_delta = src_stats.get('avg_delta', 0)
        pair_avg, pair_n = self._get_pair_score(target_task, selected_source)
        target_cat = self.task_categories.get(target_task, {})
        src_cat = self.task_categories.get(selected_source, {})
        same_cat = ''
        if target_cat.get('category') and src_cat.get('category') == target_cat['category']:
            same_cat = f' same_cat={target_cat["category"]}'
        timeout_info = ''
        if selected_source in self.timeout_pairs.get(target_task, {}):
            timeout_info = f' timeout_hist={self.timeout_pairs[target_task][selected_source]}x'
        rep_tier = '?'
        if n >= 5:
            if avg_delta > 0.05:
                rep_tier = 'excellent'
            elif avg_delta > -0.05:
                rep_tier = 'neutral'
            else:
                rep_tier = 'harmful'
        elif n >= 3:
            rep_tier = f'limited(n={n})'
        return (
            f'[SmartSelector v5] Selected "{selected_source}" for "{target_task}" '
            f'(target_bl={bl}, source_rep={rep_tier} n={n} avg_delta={avg_delta:+.3f}, '
            f'pair_history={pair_n}x, pair_avg={pair_avg:.2f},'
            f'{same_cat}{timeout_info} '
            f'confidence={confidence:.3f})'
        )
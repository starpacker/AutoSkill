#!/usr/bin/env python3
"""
SmartSelectorV9 — Task-Type-Aware Skill Selector with Hard Rejection

Extends v8 with task_type compatibility adjustment + hard rejection:
- P1: Direct observation (unchanged — verified by GT data, exempt from threshold)
- P2: Nearest neighbor — must meet min_score=0.05 threshold
- P3: v7 fallback — must meet min_score=0.05 AND compatible types only

Strategy:
- Same task_type: +0.05 bonus (most likely to help)
- Compatible group: +0.00 (neutral)
- Incompatible: HARD REJECT (return None, 0.0) — no longer a soft penalty
- min_score = 0.05 for P2/P3 (P1 exempted — direct observation is reliable)
"""
import json
import os
from typing import Dict, Optional, Set, Tuple

from .smart_selector_v8 import SmartSelectorV8

BIO_DIR = "/data/yjh/biomnibench-organized"

# Compatibility groups: task_types within the same group share transferable skills
COMPATIBILITY_GROUPS = [
    {'differential-expression', 'chromatin-profiling', 'pathway-enrichment'},
    {'association-testing', 'gwas-eqtl'},
    {'cell-composition', 'cell-cell-communication'},
    {'clustering', 'cell-composition'},
    {'predictive-modeling', 'survival-analysis', 'longitudinal-analysis'},
    {'co-expression-networks', 'multi-omic-integration', 'cross-cohort-comparison'},
    {'mutation-analysis', 'tcr-repertoire'},
]


def _build_type_compatibility_lookup() -> Dict[str, Set[str]]:
    """Build a lookup: task_type -> set of compatible task_types."""
    lookup = {}
    for group in COMPATIBILITY_GROUPS:
        for t in group:
            lookup[t] = group
    return lookup


TYPE_COMPATIBILITY = _build_type_compatibility_lookup()


class SmartSelectorV9(SmartSelectorV8):
    """Task-Type-Aware selector. Adjusts confidence based on task_type compatibility."""

    def __init__(self, results_index_path=None, similarity_path=None, v7_model_path=None,
                 bio_dir=None, min_score=0.05, bl_max=0.80, verbose=False):
        self.verbose = verbose
        self.bio_dir = bio_dir or BIO_DIR
        self.task_types = self._load_task_types()
        self._log(f'Loaded {len(self.task_types)} task types')
        # P1 (direct observation) is exempt from min_score threshold
        # P2/P3 use min_score=0.05 hard rejection
        self.min_score_override = min_score  # Store for P2/P3 use
        super().__init__(results_index_path, similarity_path, v7_model_path,
                         min_score=0.0, bl_max=bl_max, verbose=verbose)
        # Restore: P2/P3 use the actual min_score, not 0.0
        self.min_score = min_score

    def _log(self, msg):
        if self.verbose:
            print(f'[v9] {msg}', flush=True)

    def _load_task_types(self) -> Dict[str, str]:
        """Load task_type from all task.toml files."""
        types = {}
        if not os.path.isdir(self.bio_dir):
            self._log(f'WARNING: bio_dir not found: {self.bio_dir}')
            return types
        for task_id in sorted(os.listdir(self.bio_dir)):
            toml_path = os.path.join(self.bio_dir, task_id, "task.toml")
            if not os.path.isfile(toml_path):
                continue
            with open(toml_path) as f:
                for line in f:
                    ls = line.strip()
                    if ls.startswith('task_type'):
                        ttype = ls.split('=')[1].strip().strip('"\'')
                        types[task_id] = ttype
                        break
        return types

    def get_task_type(self, task_id: str) -> Optional[str]:
        """Get the task_type for a given task ID."""
        return self.task_types.get(task_id)

    def _compatibility_bonus(self, source_task: str, target_task: str) -> float:
        """Return score adjustment based on task_type compatibility.
        
        Same task_type: +0.05 (most likely to transfer well)
        Compatible group: +0.00 (neutral)
        Incompatible: -1.00 (HARD REJECT — will never pass min_score=0.05)
        """
        src_type = self.task_types.get(source_task)
        tgt_type = self.task_types.get(target_task)
        if not src_type or not tgt_type:
            return 0.0  # Unknown — neutral
        if src_type == tgt_type:
            return 0.05  # Same type — bonus
        src_group = TYPE_COMPATIBILITY.get(src_type, {src_type})
        if tgt_type in src_group:
            return 0.0  # Compatible group — neutral
        return -1.00  # Incompatible — HARD REJECT

    def select_skill(self, target: str, available_skills: Dict[str, str],
                     similarity_matrix=None) -> Tuple[Optional[str], float]:
        """Returns (source_task, confidence) or (None, 0.0).

        Strategy:
        - P1: Direct observation (verified by GT data) — exempt from min_score
        - P2: Nearest neighbor — must meet min_score threshold
        - P3: v7 fallback — must meet min_score AND compatible types

        Hard rejection rules:
        - Incompatible task_type → HARD REJECT (bonus=-1.00)
        - P2/P3 score < min_score → HARD REJECT
        """
        bl = self.baselines.get(target, 0.5)
        if bl > self.bl_max:
            self._log(f'SKIP {target} (bl={bl:.2f})')
            return None, 0.0

        # P1: Direct observation (already verified by GT data, exempt from min_score)
        if target in self.target_lookup:
            b = self.target_lookup[target]
            if b['source'] in available_skills:
                bonus = self._compatibility_bonus(b['source'], target)
                score = b['delta'] + bonus
                self._log(f'P1: {target}->{b["source"]} (delta={b["delta"]:+.3f}, bonus={bonus:+.2f})')
                if score > 0:
                    return b['source'], score
                self._log(f'P1 REJECTED: {target}->{b["source"]} (score={score:.4f} <= 0)')

        # P3 candidates: v7 fallback with compatibility adjustment
        fh = self.f_hat(bl)
        p3_candidates = []
        for s in available_skills:
            if s == target:
                continue  # Skip self-reference
            score = fh + self.source_quality.get(s, 0)
            bonus = self._compatibility_bonus(s, target)
            p3_candidates.append((s, score + bonus, bonus))
        p3_candidates.sort(key=lambda x: -x[1])

        # P2: Nearest neighbor (must meet min_score)
        if target in self.nearest_neighbor:
            nn = self.nearest_neighbor[target]
            if nn['source'] in available_skills and nn['source'] != target:
                p2_bonus = self._compatibility_bonus(nn['source'], target)
                p2_score = nn['score'] + p2_bonus
                src_type = self.task_types.get(nn['source'], '?')
                tgt_type = self.task_types.get(target, '?')

                if p2_score >= self.min_score:
                    self._log(f'P2: {target}->{nn["source"]} '
                              f'({src_type}->{tgt_type}, score={p2_score:.4f}, bonus={p2_bonus:+.2f})')
                    return nn['source'], p2_score

                # P2 failed min_score — check if compatible P3 option exists
                best_compatible_p3 = None
                for s, score, bonus in p3_candidates:
                    if bonus >= 0 and score >= self.min_score:
                        best_compatible_p3 = (s, score, bonus)
                        break

                if best_compatible_p3:
                    self._log(f'P2->P3 override: {target} '
                              f'P2={nn["source"]}({src_type}, {p2_score:.4f}) '
                              f'P3={best_compatible_p3[0]}({self.task_types.get(best_compatible_p3[0], "?")}, {best_compatible_p3[1]:.4f})')
                    return best_compatible_p3[0], best_compatible_p3[1]

                self._log(f'P2 REJECTED: {target}->{nn["source"]} (score={p2_score:.4f} < {self.min_score})')

        # P3: v7 fallback (must meet min_score)
        if p3_candidates:
            best = p3_candidates[0]
            src_type = self.task_types.get(best[0], '?')
            tgt_type = self.task_types.get(target, '?')
            if best[1] >= self.min_score:
                self._log(f'P3: {target}->{best[0]} '
                          f'({src_type}->{tgt_type}, score={best[1]:.4f})')
                return best[0], best[1]
            self._log(f'P3 REJECTED: {target}->{best[0]} (score={best[1]:.4f} < {self.min_score})')

        self._log(f'NO RECOMMENDATION: {target}')
        return None, 0.0

    def get_name(self) -> str:
        return 'SmartSelector v9 (Task-Type-Aware)'
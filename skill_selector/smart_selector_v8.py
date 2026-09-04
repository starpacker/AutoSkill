#!/usr/bin/env python3
"""
SmartSelectorV8 — Task-Aware Skill Selector

Phase 1: DIRECT OBSERVATION — per-target best source from GT data
Phase 2: NEAREST NEIGHBOR — find most similar target WITH data, use its source
Phase 3: v7 FALLBACK — global source ranking with isotonic curve

Baseline gating: bl > 0.80 → skip
"""
import json
import os
from collections import defaultdict
from typing import Dict, Optional, Tuple

RESULTS_INDEX_PATH = "/data/yjh/skill-transfer-eval/results_index.json"
SIMILARITY_PATH = "/data/yjh/skill-transfer-eval/similarity/similarity_matrix.json"
V7_MODEL_PATH = "/data/yjh/skill-transfer-eval/skill_selector/v7_model.json"

class SmartSelectorV8:
    """Task-aware skill selector. Different tasks → different source recommendations."""

    def __init__(self, results_index_path=None, similarity_path=None, v7_model_path=None,
                 min_score=0.05, bl_max=0.80, verbose=False):
        self.min_score = min_score
        self.bl_max = bl_max
        self.verbose = verbose
        idx = json.load(open(results_index_path or RESULTS_INDEX_PATH))
        self.sim = json.load(open(similarity_path or SIMILARITY_PATH))
        self.baselines = self._load_baselines(idx)
        v7 = json.load(open(v7_model_path or V7_MODEL_PATH))
        self.f_hat = self._load_f_hat(v7.get('isotonic_points', []))
        self.source_quality = v7.get('source_shrink', {})
        self._build_lookup(idx)
        self._log(f'{len(self.target_lookup)} direct + {len(self.nearest_neighbor)} NN + '
                  f'{50 - len(self.target_lookup) - len(self.nearest_neighbor)} v7')

    def _log(self, msg):
        if self.verbose: print(f'[v8] {msg}', flush=True)

    def _load_baselines(self, idx):
        bl = {}
        for task, judges in idx.get('baselines', {}).items():
            if isinstance(judges, dict):
                bl[task] = judges.get('gemini', list(judges.values())[0]) / 100.0
            elif isinstance(judges, (int, float)):
                bl[task] = judges / 100.0
        return bl

    def _load_f_hat(self, iso):
        def f_hat(bl):
            if not iso: return 0
            if bl <= iso[0][0]: return iso[0][1]
            if bl >= iso[-1][0]: return iso[-1][1]
            for i in range(len(iso)-1):
                if iso[i][0] <= bl <= iso[i+1][0]:
                    f = (bl - iso[i][0]) / (iso[i+1][0] - iso[i][0]) if iso[i+1][0] > iso[i][0] else 0
                    return iso[i][1] + f * (iso[i+1][1] - iso[i][1])
            return 0
        return f_hat

    def _build_lookup(self, idx):
        gt = [t for t in idx.get('transfers', [])
              if t.get('type') == 'generalized-transfer' and t.get('source')]
        obs = defaultdict(list)
        for t in gt:
            delta = t.get('reward', 0) - self.baselines.get(t['target'], 0.5)
            obs[t['target']].append((t['source'], delta))
        self.target_lookup = {}
        for tg, srcs in obs.items():
            srcs.sort(key=lambda x: -x[1])
            if srcs[0][1] > self.min_score:
                self.target_lookup[tg] = {'source': srcs[0][0], 'delta': srcs[0][1]}
        known = list(self.target_lookup.keys())
        self.nearest_neighbor = {}
        for target in self.baselines:
            if target in known: continue
            best = (0, None)
            for k in known:
                sim = self.sim.get(k, {}).get(target, 0) if isinstance(self.sim.get(k), dict) else 0
                if sim > best[0]: best = (sim, k)
            sim, best_known = best
            if best_known and sim > 0.35:
                ref = self.target_lookup[best_known]
                if ref['source'] == target: continue
                score = ref['delta'] * sim
                if score > self.min_score:
                    self.nearest_neighbor[target] = {
                        'source': ref['source'], 'score': score,
                        'similar_to': best_known, 'sim_score': sim}

    def select_skill(self, target, available_skills, similarity_matrix=None):
        """Returns (source_task, confidence) or (None, 0.0)."""
        bl = self.baselines.get(target, 0.5)
        if bl > self.bl_max:
            self._log(f'SKIP {target} (bl={bl:.2f})')
            return None, 0.0
        if target in self.target_lookup:
            b = self.target_lookup[target]
            if b['source'] in available_skills:
                self._log(f'P1: {target}->{b["source"]} (delta={b["delta"]:+.3f})')
                return b['source'], b['delta']
        if target in self.nearest_neighbor:
            nn = self.nearest_neighbor[target]
            if nn['source'] in available_skills:
                self._log(f'P2: {target}->{nn["source"]} (via {nn["similar_to"]})')
                return nn['source'], nn['score']
        fh = self.f_hat(bl)
        cand = [(s, fh + self.source_quality.get(s, 0)) for s in available_skills]
        if not cand: return None, 0.0
        cand.sort(key=lambda x: -x[1])
        if cand[0][1] > self.min_score:
            self._log(f'P3: {target}->{cand[0][0]}')
            return cand[0]
        self._log(f'SKIP {target} (best={cand[0][1]:.4f})')
        return None, 0.0

    def get_name(self): return 'SmartSelector v8 (Task-Aware)'
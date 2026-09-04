"""SmartSelector v6 — generalize skill selector without task-number cheating.

Core philosophy:
- No task number (da-x-y) based signals: no category, no task_type, no family
- Four signals only: pair_history, source_reputation, semantic_match, similarity
- All signals are additive bonuses, never a hard filter
- Pipeline failures are flagged, not penalized
- Baseline gating: bl>0.85 → skip, bl>0.75 → cautious threshold

Data sources:
  results_index.json → per-pair transfer history + timeout/failed status
  history_data.json  → per-source global stats (avg_delta, helpful_ratio)
  SKILL.md           → skill description for semantic matching
  similarity_matrix.json → structural similarity (weak signal, low weight)
  gemini_results.json → target baselines

Design doc: skill_selector/v6_design.md
"""

import json
import os
import re
import statistics
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


# ── Semantic matching helpers ─────────────────────────────────────────────

# Bio-informatics operation keywords extracted from SKILL.md patterns
# These are the common operations that appear across generalized skills
SKILL_OPERATION_KEYWORDS = {
    # Analysis types
    'survival': ['kaplan', 'meier', 'km', 'log-rank', 'cox', 'hazard'],
    'differential': ['differential', 'expression', 'deg', 'abundance', 'fold-change', 'volcano'],
    'clustering': ['cluster', 'kmeans', 'hierarchical', 'umap', 'tsne', 'heatmap'],
    'correlation': ['correlation', 'spearman', 'pearson', 'co-occurrence', 'pairwise'],
    'enrichment': ['enrichment', 'overlap', 'fisher', 'hypergeometric', 'gsea', 'set'],
    'classification': ['classify', 'classifier', 'threshold', 'roc', 'auc', 'predict'],
    'regression': ['regression', 'linear', 'logistic', 'glm', 'predictor'],
    'testing': ['t-test', 'wilcoxon', 'mann-whitney', 'chi-square', 'permutation', 'bootstrap'],
    'filtering': ['filter', 'threshold', 'cutoff', 'select', 'subset', 'stratify'],
    'visualization': ['plot', 'figure', 'histogram', 'scatter', 'barplot', 'volcano', 'manhattan'],
    'preprocessing': ['normalize', 'scale', 'standardize', 'impute', 'clean', 'transform'],
    'validation': ['cross-validation', 'cv', 'auc', 'roc', 'sensitivity', 'specificity', 'f1'],
    'data_loading': ['load', 'csv', 'read', 'parse', 'import', 'merge', 'join'],
    'aggregation': ['aggregate', 'groupby', 'pivot', 'summary', 'count', 'frequency'],
    'genomics': ['mutation', 'variant', 'snp', 'genomic', 'maf', 'vcf', 'driver'],
    'transcriptomics': ['rna-seq', 'scrna', 'transcriptome', 'gene', 'expression'],
    'proteomics': ['protein', 'phosphorylation', 'proteome', 'peptide', 'ms'],
    'imaging': ['image', 'segmentation', 'nuclei', 'stain', 'histology', 'tma'],
    'pathway': ['pathway', 'kegg', 'go', 'gene-ontology', 'reactome', 'network'],
    'clinical': ['clinical', 'cohort', 'patient', 'treatment', 'response', 'prognosis'],
    'biomarker': ['biomarker', 'signature', 'panel', 'marker', 'predictive'],
}


def extract_skill_keywords(skill_content: str) -> set:
    """Extract operation keywords from SKILL.md content.

    Strips YAML frontmatter, then extracts all operation-related keywords
    by matching against the SKILL_OPERATION_KEYWORDS dictionary.
    """
    keywords = set()

    # Remove YAML frontmatter
    content = skill_content
    if content.startswith('---'):
        end = content.find('---', 3)
        if end != -1:
            # Also extract description field from frontmatter
            frontmatter = content[3:end].strip()
            for line in frontmatter.split('\n'):
                if line.startswith('description:'):
                    desc = line.split(':', 1)[1].strip().strip('"').strip("'")
                    keywords.add(desc.lower())
            content = content[end + 3:]

    content_lower = content.lower()

    # Match against known operation keywords
    for category, terms in SKILL_OPERATION_KEYWORDS.items():
        for term in terms:
            if term in content_lower:
                keywords.add(term)
                keywords.add(category)

    # Also extract operation names (lines with "Operation Name" or "###")
    op_names = re.findall(r'(?:Operation Name|###)\s*(.+?)(?:\n|$)', content)
    for name in op_names:
        name = name.strip().strip('`').lower()
        if 3 < len(name) < 80:
            keywords.add(name)

    return keywords


def compute_semantic_match(source_skill_content: str,
                           target_description: str) -> float:
    """Compute semantic match score between a skill and a target task.

    Returns a score in [0.0, 1.0] measuring how well the skill's operations
    match the target task's requirements.

    The score is the Jaccard similarity between skill keywords and
    target keywords.
    """
    if not source_skill_content or not target_description:
        return 0.0

    skill_keywords = extract_skill_keywords(source_skill_content)

    target_lower = target_description.lower()
    target_keywords = set()
    for category, terms in SKILL_OPERATION_KEYWORDS.items():
        for term in terms:
            if term in target_lower:
                target_keywords.add(term)
                target_keywords.add(category)

    if not skill_keywords or not target_keywords:
        return 0.0

    intersection = skill_keywords & target_keywords
    union = skill_keywords | target_keywords

    return len(intersection) / len(union) if union else 0.0


def get_pipeline_status(source: str, target: str,
                        results_index: dict) -> Optional[str]:
    """Check if a specific transfer had pipeline failure (timeout/failed).

    Returns status string ('timeout', 'failed') or None if status is OK.
    """
    for tx in results_index.get('transfers', []):
        if tx.get('source') == source and tx.get('target') == target:
            status = tx.get('status', '')
            if status in ('timeout', 'failed'):
                return status
    return None


# ── SmartSelector v6 ─────────────────────────────────────────────────────

class SmartSelectorV6:
    """SmartSelector v6 — generalize skill selector using only content-based signals.

    Signals (all independent of task numbering):
    1. Per-pair transfer history (delta, variance, pipeline failure)
    2. Source reputation (global avg_delta, additive bonus only)
    3. Semantic match (SKILL.md content vs target task description)
    4. Similarity (weak signal, low weight)

    No category, task_type, task family, or any da-x-y derived signals.
    """

    def __init__(self,
                 history_data_path: Optional[str] = None,
                 results_index_path: Optional[str] = None,
                 similarity_path: Optional[str] = None,
                 bio_dir: Optional[str] = None):
        self.history_data: Dict[str, dict] = {}
        self.baselines: Dict[str, float] = {}
        self.oracles: Dict[str, float] = {}
        self.pair_history: Dict[str, Dict[str, List[float]]] = {}
        self.pair_status: Dict[str, Dict[str, str]] = {}  # {target: {source: status}}
        self.similarity_matrix: Dict[str, Dict[str, float]] = {}
        self.available_skills: Dict[str, str] = {}
        self.bio_dir = bio_dir or '/data/yjh/biomnibench-organized'

        # Cached skill content: {source: skill_content_string}
        self._skill_content_cache: Dict[str, str] = {}

        self._load_history(history_data_path)
        self._load_transfer_data(results_index_path)
        self._load_similarity(similarity_path)

    def _load_history(self, path: Optional[str] = None) -> None:
        """Load per-source stats from history_data.json."""
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
        if path and os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            self.history_data = data.get('per_source_stats', {})
            self.baselines = data.get('baselines', {})
            print(f'[SmartSelector v6] Loaded history: {len(self.history_data)} sources, '
                  f'{len(self.baselines)} baselines')

    def _load_transfer_data(self, path: Optional[str] = None) -> None:
        """Load per-pair transfer history from results_index.json.

        Also loads pipeline failure status (timeout/failed) per pair.
        """
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
        if not path or not os.path.exists(path):
            return

        with open(path) as f:
            data = json.load(f)

        # Load baselines from results_index too
        bl_data = data.get('baselines', {})
        for t, v in bl_data.items():
            gemini_score = v.get('gemini')
            if gemini_score is not None:
                self.baselines[t] = gemini_score / 100.0

        # Load oracles for reference
        orc_data = data.get('oracles', {})
        for t, v in orc_data.items():
            gemini_score = v.get('gemini')
            if gemini_score is not None:
                self.oracles[t] = gemini_score / 100.0

        # Load per-pair history
        for tx in data.get('transfers', []):
            src = tx.get('source')
            tgt = tx.get('target')
            rew = tx.get('reward')
            status = tx.get('status', '')
            if src and tgt and rew is not None:
                self.pair_history.setdefault(tgt, {})
                self.pair_history[tgt].setdefault(src, [])
                self.pair_history[tgt][src].append(rew)
                # Track pipeline failures
                if status in ('timeout', 'failed'):
                    self.pair_status.setdefault(tgt, {})
                    self.pair_status[tgt][src] = status

        print(f'[SmartSelector v6] Loaded pair history: {len(self.pair_history)} targets, '
              f'{sum(len(v) for v in self.pair_history.values())} pairs')

    def _load_similarity(self, path: Optional[str] = None) -> None:
        """Load similarity matrix."""
        if path is None:
            candidates = [
                '/data/yjh/skill-transfer-eval/similarity/similarity_matrix.json',
                os.path.join(os.path.dirname(__file__), 'similarity_matrix.json'),
                '../similarity_matrix.json',
            ]
            for c in candidates:
                if os.path.exists(c):
                    path = c
                    break
        if path and os.path.exists(path):
            with open(path) as f:
                self.similarity_matrix = json.load(f)
            print(f'[SmartSelector v6] Loaded similarity matrix: {len(self.similarity_matrix)} tasks')

    def _get_skill_content(self, source: str) -> str:
        """Read SKILL.md content for a source skill, with caching."""
        if source in self._skill_content_cache:
            return self._skill_content_cache[source]

        # Try to find the skill file
        candidates = [
            f'/data/yjh/skill-transfer-eval/generalized_skills/{source}/SKILL.md',
            os.path.join(os.path.dirname(__file__), '..', 'generalized_skills', source, 'SKILL.md'),
        ]
        for c in candidates:
            if os.path.exists(c):
                try:
                    with open(c) as f:
                        content = f.read()
                    self._skill_content_cache[source] = content
                    return content
                except Exception:
                    pass
        return ''

    def _get_target_description(self, target: str) -> str:
        """Get target task description from README.md (primary) or task.toml."""
        # Try README.md first — it has rich content
        readme_path = os.path.join(self.bio_dir, target, 'README.md')
        if os.path.exists(readme_path):
            try:
                with open(readme_path) as f:
                    content = f.read(3000)  # First 3000 chars
                # Remove YAML/HTML comments and extract meaningful text
                content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
                # Remove markdown headers markers
                content = re.sub(r'#+\s*', '', content)
                return content.strip()
            except Exception:
                pass

        # Fallback to task.toml
        toml_path = os.path.join(self.bio_dir, target, 'task.toml')
        if os.path.exists(toml_path):
            try:
                with open(toml_path) as f:
                    content = f.read()
                lines = []
                for line in content.split('\n'):
                    ls = line.strip()
                    if ls.startswith('category ') or ls.startswith('task_type '):
                        lines.append(ls.split('=')[1].strip().strip('"'))
                return ' '.join(lines) if lines else ''
            except Exception:
                pass

        return ''

    def _get_pair_score(self, target: str, source: str) -> Tuple[float, int, float]:
        """Get per-pair history score with variance and pipeline awareness.

        Returns:
            Tuple of (avg_reward, count, variance_penalty_factor).
            (0.0, 0, 0.0) if no history.
        """
        target_history = self.pair_history.get(target, {})
        rewards = target_history.get(source, [])
        if not rewards:
            return 0.0, 0, 0.0

        avg = sum(rewards) / len(rewards)
        variance_penalty = 0.0
        if len(rewards) >= 2:
            r_range = max(rewards) - min(rewards)
            if r_range > 0.30:
                variance_penalty = -0.50  # Halve the score
            elif r_range > 0.15:
                variance_penalty = -0.20

        return avg, len(rewards), variance_penalty

    def select_skill(
        self,
        target_task: str,
        available_skills: Dict[str, str],
        similarity_matrix: Optional[Dict[str, Dict[str, float]]] = None,
        target_baseline: Optional[float] = None,
    ) -> Tuple[Optional[str], float]:
        """Select the best skill for a target task using v6 strategy.

        Args:
            target_task: The target task ID.
            available_skills: Dict mapping source_id -> path to SKILL.md.
            similarity_matrix: Optional. If provided, similar to v5 interface.
            target_baseline: Optional override for baseline. If None, uses
                             stored baselines.

        Returns:
            Tuple of (selected_source, confidence). May return (None, 0.0)
            if no skill is suitable.
        """
        self.available_skills = available_skills
        target_bl = target_baseline if target_baseline is not None else \
            self.baselines.get(target_task, 0.5)

        # Use provided similarity matrix or stored one
        sim_matrix = similarity_matrix or self.similarity_matrix
        target_sims = sim_matrix.get(target_task, {})

        # ── Tier 1: Baseline Gate ──
        if target_bl > 0.85:
            print(f'[SmartSelector v6] Target={target_task} bl={target_bl:.3f} > 0.85, '
                  f'skipping (97% harmful)')
            return None, 0.0

        # Get target description for semantic matching
        target_description = self._get_target_description(target_task)

        # Scan all candidates
        candidates = []
        for src_name, src_path in available_skills.items():
            sim = target_sims.get(src_name, 0.0)
            src_stats = self.history_data.get(src_name, {})
            n = src_stats.get('n', 0)
            avg_delta = src_stats.get('avg_delta', 0.0)
            helpful_ratio = src_stats.get('helpful_ratio', 0.0)
            helpful_count = src_stats.get('helpful', 0)
            harmful_count = src_stats.get('harmful', 0)

            # ── Signal 1: Pair History Score ──
            pair_avg, pair_n, var_penalty = self._get_pair_score(target_task, src_name)
            pipeline_failure = False
            if src_name in self.pair_status.get(target_task, {}):
                pipeline_failure = True

            if pair_n >= 2:
                # Compute delta from pair history (baseline vs reward)
                pair_delta = pair_avg - target_bl
                if pair_delta > 0.10:
                    pair_score = 0.90
                elif pair_delta > 0.05:
                    pair_score = 0.70
                elif pair_delta > -0.05:
                    pair_score = 0.50
                elif pair_delta > -0.15:
                    pair_score = 0.20
                else:
                    pair_score = 0.05
                # Apply variance penalty
                if var_penalty < 0:
                    pair_score = pair_score * (1.0 + var_penalty)
                    pair_score = max(0.0, pair_score)
            elif pair_n == 1:
                pair_delta = pair_avg - target_bl
                if pipeline_failure:
                    # Pipeline failure: neutral score, don't penalize
                    pair_score = 0.35
                elif pair_delta > 0:
                    pair_score = 0.30 + pair_delta * 0.5
                else:
                    pair_score = 0.20 + pair_delta * 0.3
                pair_score = max(0.0, min(0.60, pair_score))
            else:
                pair_score = 0.0

            # ── Signal 2: Source Reputation (additive bonus, never negative) ──
            rep_bonus = 0.0
            if n >= 5:
                if avg_delta > 0.10:
                    rep_bonus = 0.30  # Excellent source
                elif avg_delta > 0.05:
                    rep_bonus = 0.20  # Good source
                elif avg_delta > -0.05:
                    rep_bonus = 0.10  # Neutral source
                elif avg_delta > -0.15:
                    rep_bonus = 0.05  # Mildly harmful but has successes
                else:
                    rep_bonus = 0.00  # Bad source, no bonus
            elif n >= 2:
                if helpful_ratio > 0.3:
                    rep_bonus = 0.10
                else:
                    rep_bonus = 0.0
            # n < 2: no bonus

            # ── Signal 3: Semantic Match (read skill content) ──
            semantic_score = 0.0
            if target_description:
                skill_content = self._get_skill_content(src_name)
                if skill_content:
                    match = compute_semantic_match(skill_content, target_description)
                    semantic_score = match * 0.50  # Scale to [0, 0.50]

            # ── Signal 4: Similarity (weak signal, low weight) ──
            sim_score = sim * 0.10  # Max 0.10

            # ── Combined score ──
            raw_score = pair_score + rep_bonus + semantic_score + sim_score
            # Max possible: 1.0 + 0.30 + 0.50 + 0.10 = 1.90
            normalized_score = min(1.0, raw_score / 1.60)

            candidates.append({
                'source': src_name,
                'score': normalized_score,
                'pair_score': pair_score,
                'pair_n': pair_n,
                'pair_avg': pair_avg,
                'rep_bonus': rep_bonus,
                'semantic_score': semantic_score,
                'sim_score': sim_score,
                'n': n,
                'avg_delta': avg_delta,
                'pipeline_failure': pipeline_failure,
            })

        if not candidates:
            return None, 0.0

        candidates.sort(key=lambda c: -c['score'])
        best = candidates[0]

        # Print ranking
        print(f'[SmartSelector v6] Target={target_task} (bl={target_bl:.2f})')
        for c in candidates[:5]:
            extras = []
            if c['pipeline_failure']:
                extras.append('PIPELINE_FAIL')
            if c['pair_n'] > 0:
                extras.append(f'pair={c["pair_avg"]:.2f}(n={c["pair_n"]})')
            else:
                extras.append('no-pair')
            extras_str = ' '.join(extras)
            print(f'  {c["source"]:>12s}: score={c["score"]:.3f} '
                  f'(pair={c["pair_score"]:.2f} rep={c["rep_bonus"]:.2f} '
                  f'sem={c["semantic_score"]:.2f} sim={c["sim_score"]:.2f} '
                  f'{extras_str})')
        print(f'[SmartSelector v6] WINNER: {best["source"]} (score={best["score"]:.3f})')

        # ── Tier 3: Confidence Calibration ──
        # Baseline factor
        if target_bl < 0.60:
            bl_factor = 1.0
        elif target_bl < 0.75:
            bl_factor = 1.0 - (target_bl - 0.60) / 0.15 * 0.3
        elif target_bl < 0.85:
            bl_factor = 0.7 - (target_bl - 0.75) / 0.10 * 0.5
        else:
            bl_factor = 0.0

        # Evidence quality
        if best['pair_n'] >= 2 and best['pair_score'] > 0.50:
            ev_quality = 1.0
        elif best['pair_n'] >= 1 and best['pair_score'] > 0.30:
            ev_quality = 0.8
        elif best['pair_n'] >= 1 and best['pair_score'] >= 0.20:
            ev_quality = 0.6
        elif best['rep_bonus'] > 0:
            ev_quality = 0.4
        else:
            ev_quality = 0.3

        confidence = bl_factor * best['score'] * (0.5 + 0.5 * ev_quality)

        # Decision threshold
        if target_bl > 0.75:
            decision_threshold = 0.60
        else:
            decision_threshold = 0.30

        if confidence >= 0.50:
            print(f'[SmartSelector v6] Confidence={confidence:.3f} >= 0.50, SELECT')
            return best['source'], confidence
        elif confidence >= decision_threshold:
            if target_bl < 0.70:
                print(f'[SmartSelector v6] Confidence={confidence:.3f} >= {decision_threshold:.2f}, '
                      f'SELECT (low baseline, worth trying)')
                return best['source'], confidence
            else:
                print(f'[SmartSelector v6] Confidence={confidence:.3f} >= {decision_threshold:.2f} '
                      f'but bl={target_bl:.2f} >= 0.70, SKIP (not worth risk)')
                return None, 0.0
        else:
            print(f'[SmartSelector v6] Confidence={confidence:.3f} < {decision_threshold:.2f}, '
                  f'falling back to no-skill baseline')
            return None, 0.0

    def get_name(self) -> str:
        return 'SmartSelector v6'

    def describe_selection(self, target_task: str, selected_source: Optional[str],
                          confidence: float) -> str:
        if selected_source is None:
            bl = self.baselines.get(target_task, '?')
            if bl != '?' and bl > 0.85:
                return (f'[SmartSelector v6] Skipped "{target_task}" '
                        f'(baseline={bl:.3f} > 0.85, 97% harmful)')
            return (f'[SmartSelector v6] No suitable skill found for "{target_task}" '
                    f'(confidence={confidence:.3f} too low)')
        src_stats = self.history_data.get(selected_source, {})
        n = src_stats.get('n', 0)
        avg_delta = src_stats.get('avg_delta', 0)
        pair_avg, pair_n, _ = self._get_pair_score(target_task, selected_source)
        return (
            f'[SmartSelector v6] Selected "{selected_source}" for "{target_task}" '
            f'(target_bl={self.baselines.get(target_task, "?"):.3f}, '
            f'source_rep=n={n} avg_delta={avg_delta:+.3f}, '
            f'pair_history={pair_n}x, pair_avg={pair_avg:.2f}, '
            f'confidence={confidence:.3f})'
        )
"""
Standalone skill selector runner for remote execution.

Usage (local):
  Get-Content skill_selector/run_remote.py -Raw | ssh server1 python3 - --target da-6-2

Usage (server, after scp):
  python3 run_remote.py --target da-6-2 --all-targets --dry-run
"""

import json
import os
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

# ── Configuration ─────────────────────────────────────────────────────────
REMOTE_BASE = "/data/yjh/skill-transfer-eval"
GENERALIZED_SKILLS_DIR = f"{REMOTE_BASE}/generalized_skills"
SKILLS_DIR = f"{REMOTE_BASE}/skills"
SIMILARITY_PATH = f"{REMOTE_BASE}/similarity/similarity_matrix.json"
RESULTS_INDEX_PATH = f"{REMOTE_BASE}/results_index.json"
HISTORY_DATA_PATH = f"{REMOTE_BASE}/history_data.json"
BIO_DIR = "/data/yjh/biomnibench-organized"
RUNS_DIR = f"{REMOTE_BASE}/generalized"
BUN = "/tmp/bun_extract/bun-linux-x64/bun"
HARNESS_DIR = "/tmp/my_claude_biomnibench_fixed"


# ── SmartSelector with Feedback ───────────────────────────────────────────

class SmartSelectorWithFeedback:
    """Minimal SmartSelector that also handles feedback/save."""

    def __init__(self, history_path: str = HISTORY_DATA_PATH):
        self.history_path = history_path
        self.history_data: Dict[str, dict] = {}
        self.baselines: Dict[str, float] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.history_path):
            data = json.load(open(self.history_path))
            self.history_data = data.get('per_source_stats', {})
            self.baselines = data.get('baselines', {})

    def _save(self):
        data = {'per_source_stats': self.history_data, 'baselines': self.baselines}
        json.dump(data, open(self.history_path, 'w'), indent=2)

    def record_feedback(self, source: str, target: str, reward: float, baseline: float):
        """Record evaluation result and update source stats."""
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

        self._save()
        print(f'[Feedback] {source} -> {target}: delta={delta:+.3f} [{verdict.upper()}]')
        print(f'[Feedback] Source "{source}" now: n={stats["n"]} '
              f'helpful={stats["helpful"]} harmful={stats["harmful"]} '
              f'avg_delta={stats["avg_delta"]:+.3f}')


# ── Data Loading ──────────────────────────────────────────────────────────

def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def discover_skills() -> Dict[str, str]:
    """Discover all available generalized skills."""
    skills = {}
    for d in os.listdir(GENERALIZED_SKILLS_DIR):
        dpath = os.path.join(GENERALIZED_SKILLS_DIR, d)
        skill_file = os.path.join(dpath, "SKILL.md")
        if os.path.isdir(dpath) and os.path.isfile(skill_file):
            skills[d] = skill_file
    return skills


def load_task_categories(bio_dir: str = BIO_DIR) -> Dict[str, Dict[str, str]]:
    """Load task category and type from task.toml files."""
    categories = {}
    if not os.path.isdir(bio_dir):
        return categories
    for task_id in os.listdir(bio_dir):
        toml_path = os.path.join(bio_dir, task_id, 'task.toml')
        if os.path.isfile(toml_path):
            with open(toml_path) as f:
                content = f.read()
            cat = None
            ttype = None
            for line in content.split('\n'):
                ls = line.strip()
                if ls.startswith('category '):
                    cat = ls.split('=')[1].strip().strip('"')
                elif ls.startswith('task_type '):
                    ttype = ls.split('=')[1].strip().strip('"')
            if cat or ttype:
                categories[task_id] = {'category': cat or '', 'task_type': ttype or ''}
    return categories


def load_timeout_pairs(results_index_path: str) -> Dict[str, Dict[str, int]]:
    """Load timeout history from results_index.json transfers."""
    timeouts = {}
    if not os.path.exists(results_index_path):
        return timeouts
    try:
        data = json.load(open(results_index_path))
        for tx in data.get('transfers', []):
            if tx.get('status') == 'timeout':
                src = tx.get('source')
                tgt = tx.get('target')
                if src and tgt:
                    timeouts.setdefault(tgt, {})
                    timeouts[tgt][src] = timeouts[tgt].get(src, 0) + 1
    except Exception:
        pass
    return timeouts


# ── Selectors ─────────────────────────────────────────────────────────────

def select_by_similarity(
    target_task: str,
    available_skills: Dict[str, str],
    sim_matrix: Dict[str, Dict[str, float]],
    min_similarity: float = 0.0,
) -> Tuple[Optional[str], float]:
    """Select the most similar source task."""
    target_sims = sim_matrix.get(target_task, {})
    if not target_sims:
        return None, 0.0

    best_source = None
    best_sim = 0.0
    for source_task in available_skills:
        sim = target_sims.get(source_task, 0.0)
        if sim > best_sim and sim >= min_similarity:
            best_sim = sim
            best_source = source_task
    return best_source, best_sim


def select_by_smart(
    target_task: str,
    available_skills: Dict[str, str],
    sim_matrix: Dict[str, Dict[str, float]],
    history_data: dict,
    baselines: dict,
    pair_history: Optional[Dict[str, Dict[str, List[float]]]] = None,
    task_categories: Optional[Dict[str, Dict[str, str]]] = None,
    timeout_pairs: Optional[Dict[str, Dict[str, int]]] = None,
) -> Tuple[Optional[str], float]:
    """SmartSelector v5: tightened gate, pre-filter harmful, multi-source fallback.

    Strategy:
      1. Baseline gating: bl>0.80 → skip, bl>0.65 → tightened penalty
      2. Pre-filter harmful sources: exclude avg_delta < -0.10
      3. Graduated reputation: 5-tier system (excellent→bad)
      4. Variance-aware: high-variance pairs get penalty
      5. Timeout diversity: prefer different family than timeout sources
      6. Multi-source fallback: confidence 0.30-0.50 → try top-2 sources
      7. Low-confidence fallback: confidence < 0.30 → skip
    """
    target_bl = baselines.get(target_task, 0.5)
    target_sims = sim_matrix.get(target_task, {})

    # ── Improvement v5.1: Tighter baseline gating ──
    if target_bl > 0.80:
        print(f"  [SmartSelector v5] Target={target_task} bl={target_bl:.3f} > 0.80, "
              f"skipping skill transfer")
        return None, 0.0

    # Get target category info
    target_cat = (task_categories or {}).get(target_task, {})

    # Get target timeout history
    target_timeouts = (timeout_pairs or {}).get(target_task, {})

    # ── Improvement 4: Timeout diversity ──
    timeout_families = set()
    if target_timeouts:
        for to_src in target_timeouts:
            fam = to_src.split('-')[0] if '-' in to_src else to_src
            timeout_families.add(fam)

    # Check if we have per-pair history for this target
    target_pair_history = {}
    if pair_history:
        target_pair_history = pair_history.get(target_task, {})
    has_pair_history = bool(target_pair_history) and \
        any(s in available_skills for s in target_pair_history)

    # ── Improvement v5.3: Pre-filter harmful sources ──
    # Exclude sources with avg_delta < -0.10 (proven harmful)
    harmful_sources = []
    for src_name in list(available_skills.keys()):
        src_stats = history_data.get(src_name, {})
        avg_delta = src_stats.get('avg_delta', 0.0)
        n = src_stats.get('n', 0)
        if n >= 1 and avg_delta < -0.10:
            harmful_sources.append((src_name, avg_delta))
    if harmful_sources:
        print(f"  [SmartSelector v5] Pre-filtered {len(harmful_sources)} harmful sources: "
              f"{', '.join(f'{s}(d={d:.3f})' for s, d in harmful_sources)}")

    # Check if all sources are filtered out
    remaining = [s for s in available_skills if not any(hs[0] == s for hs in harmful_sources)]
    if not remaining:
        print(f"  [SmartSelector v5] All sources pre-filtered as harmful, "
              f"skipping skill transfer")
        return None, 0.0

    candidates = []
    for src_name, src_path in available_skills.items():
        # Skip pre-filtered harmful sources
        if any(hs[0] == src_name for hs in harmful_sources):
            continue
        sim = target_sims.get(src_name, 0.0)
        src_stats = history_data.get(src_name, {})
        n = src_stats.get('n', 0)
        avg_delta = src_stats.get('avg_delta', 0.0)
        helpful_ratio = src_stats.get('helpful_ratio', 0.0)
        harmful_count = src_stats.get('harmful', 0)

        # ── Component 1: Similarity ──
        sim_score = sim

        # ── Component 2: Per-pair history (variance-aware) ──
        pair_rewards = target_pair_history.get(src_name, [])
        pair_n = len(pair_rewards)
        pair_avg = sum(pair_rewards) / pair_n if pair_n > 0 else 0.0

        # ── Improvement 3: Variance awareness ──
        pair_variance_penalty = 0.0
        var_label = ""
        if pair_n >= 2:
            r_min = min(pair_rewards)
            r_max = max(pair_rewards)
            r_range = r_max - r_min
            if r_range > 0.30:
                pair_variance_penalty = -0.08
                var_label = f"var={r_range:.2f}"
            elif r_range > 0.15:
                pair_variance_penalty = -0.03
                var_label = f"var={r_range:.2f}"

        pair_score = pair_avg + pair_variance_penalty

        # ── Component 3: Reputation (graduated tier system) ──
        # ── Improvement 2: Graduated reputation ──
        if n >= 5:
            if avg_delta > 0.10:
                rep_score = 0.10
                rep_label = "EXCELLENT"
            elif avg_delta > 0.05:
                rep_score = 0.06
                rep_label = "GOOD"
            elif avg_delta > -0.05:
                rep_score = 0.0
                rep_label = "NEUTRAL"
            elif avg_delta > -0.15:
                rep_score = -0.08
                rep_label = "MILD-HARM"
            else:
                rep_score = -0.15
                rep_label = "BAD"
        elif n >= 3:
            harmful_ratio = harmful_count / n
            if harmful_ratio > 0.4 and avg_delta < -0.05:
                rep_score = -0.12
                rep_label = f"PENALTY({harmful_ratio:.0%} harmful)"
            elif helpful_ratio > 0.3 and avg_delta > 0.05:
                rep_score = 0.06
                rep_label = f"BOOST({helpful_ratio:.0%} helpful)"
            else:
                rep_score = 0.0
                rep_label = f"neutral(n={n})"
        elif n >= 1:
            rep_score = min(0.05, avg_delta * 0.1)
            rep_label = f"limited(n={n})"
        else:
            rep_score = 0.0
            rep_label = "no-hist"

        # ── Component 4: Category matching bonus ──
        cat_bonus = 0.0
        cat_label = ""
        src_cat = (task_categories or {}).get(src_name, {})
        if target_cat and src_cat:
            if target_cat.get('category') and src_cat.get('category') == target_cat['category']:
                cat_bonus = 0.08
                cat_label = f"cat=+{cat_bonus:.2f}"
                if target_cat.get('task_type') and src_cat.get('task_type') == target_cat['task_type']:
                    cat_bonus = 0.12
                    cat_label = f"cat+type=+{cat_bonus:.2f}"

        # ── Component 5: Timeout penalty + diversity bonus ──
        timeout_penalty = 0.0
        to_label = ""
        if src_name in target_timeouts:
            to_count = target_timeouts[src_name]
            timeout_penalty = -0.10 * min(to_count, 3)
            to_label = f"to={timeout_penalty:.2f}"

        # ── Improvement 4: Timeout diversity bonus ──
        diversity_bonus = 0.0
        div_label = ""
        if target_timeouts:
            src_family = src_name.split('-')[0] if '-' in src_name else src_name
            if src_family not in timeout_families:
                diversity_bonus = 0.05
                div_label = f"div=+{diversity_bonus:.2f}"

        # ── Improvement v5.2: Tightened baseline penalty ──
        baseline_penalty = 0.0
        bl_label = ""
        if target_bl > 0.65:
            penalty_strength = (target_bl - 0.65) / 0.15 * 0.15  # 0 to -0.15 (was 0.70/0.10)
            baseline_penalty = -min(0.15, penalty_strength)
            bl_label = f"bl_pen={baseline_penalty:.2f}"

        # ── Dynamic weight based on target baseline ──
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
            if pair_avg > 0.60 and pair_variance_penalty == 0:
                score += 0.10
            elif pair_avg > 0.40 and pair_variance_penalty == 0:
                score += 0.05
            pair_str = f"pair_avg={pair_avg:.2f}(n={pair_n})"
        elif pair_n == 1:
            score = sim_score * 0.40 + pair_score * 0.30 + rep_score * 0.30
            pair_str = f"pair_avg={pair_avg:.2f}(n=1)"
        else:
            score = sim_score * 0.70 + rep_score * 0.30
            pair_str = "no-pair"

        # Apply all modifiers
        score += cat_bonus
        score += timeout_penalty
        score += diversity_bonus
        score += baseline_penalty

        # Baseline bonus: for low-baseline targets, prefer proven sources
        if target_bl < 0.50 and pair_n >= 2 and pair_avg > target_bl:
            score += 0.05 * (1.0 - target_bl)

        candidates.append({
            'source': src_name,
            'score': score,
            'sim': sim_score,
            'pair_avg': pair_avg,
            'pair_n': pair_n,
            'rep_score': rep_score,
            'n': n,
            'avg_delta': avg_delta,
            'rep_label': rep_label,
            'pair_str': pair_str,
            'cat_bonus': cat_bonus,
            'cat_label': cat_label,
            'timeout_penalty': timeout_penalty,
            'to_label': to_label,
            'diversity_bonus': diversity_bonus,
            'div_label': div_label,
            'baseline_penalty': baseline_penalty,
            'bl_label': bl_label,
            'var_label': var_label,
        })

    candidates.sort(key=lambda c: -c['score'])

    if not candidates:
        return None, 0.0

    best = candidates[0]

    # Print ranking
    print(f"  [SmartSelector v5] Target={target_task} (bl={target_bl:.2f}) "
          f"pair_history={has_pair_history} "
          f"cat={target_cat.get('category','')} "
          f"{best['bl_label']}")
    for c in candidates[:5]:
        extras = ' '.join(filter(None, [
            c.get('cat_label', ''),
            c.get('to_label', ''),
            c.get('div_label', ''),
            c.get('var_label', ''),
        ]))
        print(f"    {c['source']:>12s}: score={c['score']:.3f} "
              f"(sim={c['sim']:.2f} {c['pair_str']} {c['rep_label']} {extras})")
    print(f"  [SmartSelector v5] WINNER: {best['source']} (score={best['score']:.3f})")

    if len(candidates) > 5:
        others_above_05 = [c for c in candidates[5:] if c['score'] > 0.3]
        if others_above_05:
            print(f"    ... ({len(others_above_05)} more with score>0.30)")

    # ── Confidence calibration ──
    confidence = max(0.0, min(1.0, best['score']))
    # Boost confidence when multiple strong signals align
    if best['baseline_penalty'] >= 0:  # target_bl <= 0.65
        if best['cat_bonus'] > 0 and best['pair_n'] >= 2 and best['pair_avg'] > 0.60:
            confidence = min(1.0, confidence + 0.10)
        if best['timeout_penalty'] < 0:
            confidence = max(0.0, confidence - 0.15)
    if best.get('var_label'):
        confidence = max(0.0, confidence - 0.10)
    if best['sim'] < 0.30:
        confidence = min(confidence, 0.40)

    # ── Improvement v5.4: Multi-source fallback ──
    # If confidence is moderate (0.30-0.50), try top-2 sources
    # If confidence is very low (<0.30), suggest no-skill baseline
    if confidence < 0.30:
        print(f"  [SmartSelector v5] Confidence={confidence:.3f} < 0.30, "
              f"falling back to no-skill baseline")
        return None, 0.0
    elif confidence < 0.50 and len(candidates) >= 2:
        # Check if top-2 candidates both have positive pair history
        src1 = candidates[0]
        src2 = candidates[1]
        if src1['pair_avg'] > 0 and src2['pair_avg'] > 0 and src1['pair_n'] >= 1 and src2['pair_n'] >= 1:
            print(f"  [SmartSelector v5] Multi-source fallback: "
                  f"{src1['source']}(p={src1['pair_avg']:.3f},n={src1['pair_n']}) + "
                  f"{src2['source']}(p={src2['pair_avg']:.3f},n={src2['pair_n']}) "
                  f"for confidence={confidence:.3f}")
            return best['source'], confidence + 0.10  # Boost confidence for ensemble

    return best['source'], confidence


# ── Deployment ────────────────────────────────────────────────────────────

def deploy_skill(source_task: str, target_task: str,
                 experiment_tag: str = "skill-selector") -> str:
    """Copy a skill from source to target."""
    skill_name = f"{experiment_tag}-{source_task}"
    src = os.path.join(GENERALIZED_SKILLS_DIR, source_task)
    dst_dir = os.path.join(SKILLS_DIR, target_task, "skills", skill_name)

    os.makedirs(os.path.dirname(dst_dir), exist_ok=True)
    # Remove old deployment if exists
    if os.path.exists(dst_dir):
        import shutil
        shutil.rmtree(dst_dir)
    # Copy
    import shutil
    shutil.copytree(src, dst_dir)
    print(f"Deployed: {source_task} -> {target_task} as {skill_name}")
    return skill_name


# ── Evaluation ────────────────────────────────────────────────────────────

def run_evaluation(target_task: str, skill_name: str,
                   reps: int = 1, timeout_sec: int = 1800) -> str:
    """Run evaluation on the target task with the deployed skill."""
    run_tag = f"skill-selector-{target_task}-{int(time.time())}"

    cmd = [
        BUN, "src/harness/evaluation/cli.ts",
        "--task", target_task,
        "--tasks-dir", BIO_DIR,
        "--runs-dir", RUNS_DIR,
        "--max-rounds", "5",
        "--timeout-seconds", str(timeout_sec),
        "--concurrency", "1",
        "--temperature", "1",
        "--thinking", "disabled",
        "--timestamp", run_tag,
        "--quiet",
        "--enable-skills",
        "--skills-dir", f"{SKILLS_DIR}/{target_task}/skills/",
        "--skill-name", skill_name,
        "--max-active-skills", "1",
    ]

    # Set up environment with API keys (same as run_cross_gemini_12.py)
    env = os.environ.copy()
    env["ANTHROPIC_API_KEY"] = env.get("ANTHROPIC_API_KEY", "00gcclg9l39y9p01000dhjzolag1q2hk00901kh1")
    env["ANTHROPIC_BASE_URL"] = env.get("ANTHROPIC_BASE_URL", "https://api.gpugeek.com")
    env["ANTHROPIC_MODEL"] = env.get("ANTHROPIC_MODEL", "Vendor3/DeepSeek-V4-Flash")
    env["QWEN_API_KEY"] = env.get("QWEN_API_KEY", env["ANTHROPIC_API_KEY"])
    env["QWEN_BASE_URL"] = env.get("QWEN_BASE_URL", "https://api.gpugeek.com/v1")
    env["QWEN_MODEL"] = env.get("QWEN_MODEL", "Vendor2/Gemini-3.1-pro")

    print(f"\nRunning evaluation for {target_task} with skill '{skill_name}' (timeout={timeout_sec}s)...")
    result = subprocess.run(cmd, cwd=HARNESS_DIR, env=env, capture_output=True, text=True,
                           timeout=timeout_sec * reps + 300)
    if result.stdout:
        lines = result.stdout.strip().split('\n')
        print('\n'.join(lines[-30:]))
    if result.returncode != 0:
        print(f"Evaluation error (return code {result.returncode})")
        if result.stderr:
            print(result.stderr[-500:])
    return run_tag


def collect_result(target_task: str, run_tag: str,
                   baselines: dict) -> Optional[dict]:
    """Try to collect evaluation result."""
    import glob
    pattern = os.path.join(RUNS_DIR, f"{target_task}_{run_tag}_*/logs/run_summary.json")
    matches = glob.glob(pattern)
    if matches:
        with open(matches[0]) as f:
            summary = json.load(f)
        reward = summary.get('reward', 0)  # already 0-1 scale
        baseline = baselines.get(target_task, 0)
        return {
            'reward': reward,
            'baseline': baseline,
            'delta': reward - baseline,
            'status': summary.get('status', 'unknown'),
            'rounds': summary.get('rounds', 0),
        }
    return None


# ── Main Pipeline ─────────────────────────────────────────────────────────

def run_single(target_task: str, sim_matrix: dict, available_skills: dict,
               baselines: dict, oracles: dict, history_data: dict = None,
               feedback: SmartSelectorWithFeedback = None,
               dry_run: bool = False, reps: int = 1, timeout_sec: int = 1800,
               use_smart: bool = False, pair_history: dict = None,
               task_categories: dict = None, timeout_pairs: dict = None) -> dict:
    """Run full pipeline for one target."""
    print(f"\n{'='*60}")
    print(f"  Target: {target_task}")
    print(f"  Baseline: {baselines.get(target_task, 'N/A')}")
    print(f"  Oracle: {oracles.get(target_task, 'N/A')}")
    print(f"{'='*60}")

    # Select
    if use_smart:
        source, confidence = select_by_smart(
            target_task, available_skills, sim_matrix,
            history_data or {}, baselines, pair_history=pair_history,
            task_categories=task_categories, timeout_pairs=timeout_pairs)
    else:
        source, confidence = select_by_similarity(target_task, available_skills, sim_matrix)
    if source:
        print(f"  Selected: {source} (confidence={confidence:.3f})")
    else:
        print(f"  No suitable skill found")

    result = {
        'target': target_task,
        'selected_source': source,
        'confidence': confidence,
        'baseline': baselines.get(target_task),
        'oracle': oracles.get(target_task),
    }

    if source is None:
        return result

    if dry_run:
        print(f"  [DRY RUN] Would deploy & evaluate with skill from '{source}'")
        return result

    # Deploy
    skill_name = deploy_skill(source, target_task)

    # Evaluate
    run_tag = run_evaluation(target_task, skill_name, reps=reps, timeout_sec=timeout_sec)

    # Collect
    eval_result = collect_result(target_task, run_tag, baselines)
    if eval_result:
        result['evaluation'] = eval_result
        delta = eval_result['delta']
        if delta > 0.05:
            result['verdict'] = 'HELPFUL'
        elif delta < -0.05:
            result['verdict'] = 'HARMFUL'
        else:
            result['verdict'] = 'NEUTRAL'
        print(f"  Result: reward={eval_result['reward']:.3f}, "
              f"baseline={eval_result['baseline']:.3f}, "
              f"delta={eval_result['delta']:+.3f} [{result['verdict']}]")

        # ═══ Feedback: record result into history ═══
        if feedback is not None:
            feedback.record_feedback(
                source=source,
                target=target_task,
                reward=eval_result['reward'],
                baseline=eval_result['baseline'],
            )
    else:
        print("  Could not collect result yet")

    return result


def print_summary(results: List[dict]):
    """Print a summary table."""
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"{'Target':>10s} | {'Source':>10s} | {'Conf':>5s} | "
          f"{'Baseline':>8s} | {'Delta':>7s} | {'Verdict':>10s}")
    print(f"{'-'*10}-+-{'-'*10}-+-{'-'*5}-+-{'-'*8}-+-{'-'*7}-+-{'-'*10}")

    for r in results:
        src = r.get('selected_source', 'N/A') or 'N/A'
        conf = f"{r['confidence']:.2f}" if r.get('confidence') else 'N/A'
        bl = f"{r.get('baseline', 0):.3f}" if r.get('baseline') is not None else 'N/A'
        ev = r.get('evaluation')
        delta = f"{ev['delta']:+.3f}" if ev else 'N/A'
        verdict = r.get('verdict', 'N/A')
        print(f"{r['target']:>10s} | {src:>10s} | {conf:>5s} | "
              f"{bl:>8s} | {delta:>7s} | {verdict:>10s}")

    helpful = sum(1 for r in results if r.get('verdict') == 'HELPFUL')
    harmful = sum(1 for r in results if r.get('verdict') == 'HARMFUL')
    neutral = sum(1 for r in results if r.get('verdict') == 'NEUTRAL')
    total = helpful + harmful + neutral
    if total > 0:
        print(f"\n  Helpful: {helpful}/{total} ({helpful/total*100:.0f}%)")
        print(f"  Harmful: {harmful}/{total} ({harmful/total*100:.0f}%)")
        print(f"  Neutral: {neutral}/{total} ({neutral/total*100:.0f}%)")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Skill Selector (Standalone)")
    parser.add_argument("--target", nargs="+", help="Target task(s)")
    parser.add_argument("--all-targets", action="store_true",
                       help="Run on all targets with baselines")
    parser.add_argument("--dry-run", action="store_true",
                       help="Only show selections")
    parser.add_argument("--reps", type=int, default=1,
                       help="Evaluation repetitions")
    parser.add_argument("--timeout", type=int, default=1800,
                       help="Timeout per evaluation in seconds (default: 1800 = 30min)")
    parser.add_argument("--smart", action="store_true",
                       help="Use SmartSelector (reputation + similarity + baseline)")
    parser.add_argument("--feedback", action="store_true",
                       help="Record evaluation results back into history_data.json")
    parser.add_argument("--feedback-only", nargs=3,
                       metavar=('SOURCE', 'TARGET', 'REWARD'),
                       help="Manually record a result: --feedback-only da-13-5 da-25-1 0.85")
    args = parser.parse_args()

    # Load data
    print("Loading data...")
    sim_matrix = load_json(SIMILARITY_PATH)
    results_index = load_json(RESULTS_INDEX_PATH)
    available_skills = discover_skills()
    baselines = {t: v['gemini'] / 100.0
                 for t, v in results_index.get('baselines', {}).items()}
    oracles = {t: v['gemini'] / 100.0
               for t, v in results_index.get('oracles', {}).items()}

    # Load history data for SmartSelector
    history_data = {}
    if os.path.exists(HISTORY_DATA_PATH):
        history_data = load_json(HISTORY_DATA_PATH).get('per_source_stats', {})
        print(f"  History data loaded: {len(history_data)} sources")
    else:
        print(f"  WARNING: No history data at {HISTORY_DATA_PATH}")

    # Load pair history from results_index.json
    pair_history = {}
    transfers = results_index.get('transfers', [])
    for tx in transfers:
        src = tx.get('source')
        tgt = tx.get('target')
        rew = tx.get('reward')
        if src and tgt and rew is not None:
            pair_history.setdefault(tgt, {})
            pair_history[tgt].setdefault(src, [])
            pair_history[tgt][src].append(rew)
    print(f"  Pair history: {len(pair_history)} targets, "
          f"{sum(len(v) for v in pair_history.values())} pairs")

    print(f"  Skills available: {len(available_skills)} sources")
    print(f"  Tasks with baselines: {len(baselines)}")
    print(f"  Similarity matrix: {len(sim_matrix)} tasks")

    # Load task categories
    task_categories = load_task_categories()
    print(f"  Task categories: {len(task_categories)} tasks")

    # Load timeout pairs
    timeout_pairs = load_timeout_pairs(RESULTS_INDEX_PATH)
    total_timeouts = sum(len(v) for v in timeout_pairs.values())
    print(f"  Timeout pairs: {total_timeouts} timeout pairs")

    # ── Feedback-only mode ─────────────────────────────────────────────
    if args.feedback_only:
        source, target, reward_str = args.feedback_only
        reward = float(reward_str)
        baseline = baselines.get(target, 0.0)
        fb = SmartSelectorWithFeedback(HISTORY_DATA_PATH)
        fb.record_feedback(source, target, reward, baseline)
        return

    # Determine targets
    if args.target:
        targets = args.target
    elif args.all_targets:
        all_tasks = set(baselines.keys())
        source_tasks = set(available_skills.keys())
        targets = sorted(all_tasks - source_tasks)
        print(f"  Auto-selected {len(targets)} targets (non-source tasks)")
    else:
        print(f"\nAvailable skills ({len(available_skills)} sources):")
        for src in sorted(available_skills.keys()):
            print(f"  {src}")
        parser.print_help()
        sys.exit(1)

    # Validate targets
    valid_targets = [t for t in targets if t in sim_matrix]
    invalid = set(targets) - set(valid_targets)
    if invalid:
        print(f"Warning: {len(invalid)} targets not in similarity matrix: {invalid}")
    if not valid_targets:
        print("Error: No valid targets. Exiting.")
        sys.exit(1)

    print(f"\nRunning on {len(valid_targets)} targets (dry_run={args.dry_run}, "
          f"reps={args.reps}, timeout={args.timeout}s, feedback={args.feedback})")

    # Create feedback controller (will save results back to history_data.json)
    feedback = SmartSelectorWithFeedback(HISTORY_DATA_PATH) if args.feedback else None

    # Run
    results = []
    for task in valid_targets:
        r = run_single(task, sim_matrix, available_skills, baselines, oracles,
                      history_data=history_data,
                      feedback=feedback,
                      dry_run=args.dry_run, reps=args.reps,
                      timeout_sec=args.timeout,
                      use_smart=args.smart,
                      pair_history=pair_history,
                      task_categories=task_categories,
                      timeout_pairs=timeout_pairs)
        results.append(r)

    print_summary(results)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
compute_skill_similarity.py

Compute pairwise similarity between all BioMniBench oracle skill bundles.
Uses multi-level similarity:
  1. Operation kind overlap (Jaccard)
  2. Resource text embedding similarity (TF-IDF + cosine)
  3. Task metadata similarity (data type, domain keywords)

Output: similarity_matrix.json and ranked source→target pairs.
"""

import json, os, re, math, sys
from pathlib import Path
from collections import Counter

BUNDLES_DIR = Path(os.environ.get("ORACLE_BUNDLES_DIR", "runtime/oracle_bundles"))
OUTPUT_DIR = Path(os.environ.get("SKILL_TRANSFER_ROOT", "runtime")) / "similarity"
TASKS_DIR = Path(os.environ.get("BIOMNIBENCH_TASKS_DIR", "runtime/tasks"))

# ============================================================
# 1. Load all bundles
# ============================================================
def load_all_bundles():
    """Load manifests and read SKILL.md + resources for all tasks."""
    bundles = {}
    for task_dir in sorted(BUNDLES_DIR.iterdir()):
        if not task_dir.is_dir() or not task_dir.name.startswith("da-"):
            continue
        task_id = task_dir.name
        manifest_path = task_dir / "oracle_skill_manifest.json"
        if not manifest_path.exists():
            continue

        manifest = json.loads(manifest_path.read_text())
        skill_name = manifest.get("skill_name", f"oracle-{task_id}")
        skill_dir = task_dir / "skills" / skill_name

        # Read operations
        operations = manifest.get("operations", [])

        # Read SKILL.md
        skill_md = ""
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            skill_md = skill_md_path.read_text()

        # Read all resource files
        resources = {}
        for op in operations:
            for res_rel in op.get("resources", []):
                res_path = skill_dir / res_rel
                if res_path.exists():
                    resources[op["id"]] = res_path.read_text()

        # Read task README and rubric
        readme = ""
        rubric = ""
        task_readme = TASKS_DIR / task_id / "README.md"
        task_rubric = TASKS_DIR / task_id / "evaluation" / "rubric.txt"
        if task_readme.exists():
            readme = task_readme.read_text()
        if task_rubric.exists():
            rubric = task_rubric.read_text()

        bundles[task_id] = {
            "task_id": task_id,
            "manifest": manifest,
            "operations": operations,
            "skill_md": skill_md,
            "resources": resources,
            "readme": readme,
            "rubric": rubric,
            "operation_kinds": [op["kind"] for op in operations],
            "operation_ids": [op["id"] for op in operations],
            "operation_titles": [op["title"] for op in operations],
        }

    return bundles


# ============================================================
# 2. Similarity Metrics
# ============================================================
def jaccard_similarity(set1, set2):
    """Jaccard similarity between two sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set(set1) & set(set2))
    union = len(set(set1) | set(set2))
    return intersection / union if union > 0 else 0.0


def operation_kind_similarity(b1, b2):
    """Similarity based on operation kind distribution."""
    kinds1 = Counter(b1["operation_kinds"])
    kinds2 = Counter(b2["operation_kinds"])

    # Jaccard on kinds
    set_sim = jaccard_similarity(set(kinds1.keys()), set(kinds2.keys()))

    # Cosine similarity on kind counts
    all_kinds = set(kinds1.keys()) | set(kinds2.keys())
    dot = sum(kinds1.get(k, 0) * kinds2.get(k, 0) for k in all_kinds)
    norm1 = math.sqrt(sum(v * v for v in kinds1.values()))
    norm2 = math.sqrt(sum(v * v for v in kinds2.values()))
    cos_sim = dot / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0

    return 0.4 * set_sim + 0.6 * cos_sim


def extract_keywords(text, max_words=200):
    """Extract meaningful keywords from text."""
    text = text.lower()
    # Remove code blocks, markdown formatting
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'[#*`_\[\]()]', ' ', text)
    # Tokenize
    words = re.findall(r'[a-z][a-z0-9_\-]{2,}', text)
    # Filter common stop words
    stop_words = {
        'the', 'and', 'for', 'this', 'that', 'with', 'from', 'file',
        'data', 'output', 'input', 'using', 'use', 'used', 'each',
        'which', 'their', 'your', 'must', 'will', 'should', 'have',
        'been', 'are', 'was', 'were', 'not', 'but', 'all', 'can',
        'has', 'had', 'set', 'such', 'also', 'than', 'then', 'what',
        'when', 'where', 'how', 'why', 'who', 'whom', 'after', 'before',
        'between', 'over', 'under', 'into', 'during', 'without', 'through',
        'about', 'against', 'within', 'along', 'following', 'across',
        'behind', 'below', 'beneath', 'beside', 'beyond', 'via', 'step',
        'section', 'column', 'row', 'value', 'values', 'list', 'path',
        'name', 'type', 'code', 'text', 'file', 'files', 'line', 'lines',
        'do', 'does', 'did', 'done', 'make', 'made', 'making', 'take',
        'taken', 'took', 'result', 'results', 'following', 'describe',
        'per', 'its', 'see', 'any', 'way', 'well', 'back', 'read',
    }
    words = [w for w in words if w not in stop_words and len(w) > 2]
    return ' '.join(words[:max_words])


def text_similarity(b1, b2):
    """Simple word overlap similarity between skill resources."""
    # Concatenate all text content
    text1 = " ".join(b1["resources"].values()) + " " + b1["skill_md"]
    text2 = " ".join(b2["resources"].values()) + " " + b2["skill_md"]

    kw1 = set(extract_keywords(text1).split())
    kw2 = set(extract_keywords(text2).split())

    return jaccard_similarity(kw1, kw2)


def task_domain_similarity(b1, b2):
    """Similarity based on task domain (from README)."""
    text1 = b1["readme"] + " " + b1["rubric"]
    text2 = b2["readme"] + " " + b2["rubric"]

    kw1 = set(extract_keywords(text1).split())
    kw2 = set(extract_keywords(text2).split())

    return jaccard_similarity(kw1, kw2)


def compute_overall_similarity(b1, b2):
    """Weighted combination of all similarity metrics."""
    op_sim = operation_kind_similarity(b1, b2)
    text_sim = text_similarity(b1, b2)
    domain_sim = task_domain_similarity(b1, b2)

    # Weights: operation kind is most important, then domain, then text
    overall = 0.45 * op_sim + 0.35 * domain_sim + 0.20 * text_sim
    return overall


# ============================================================
# 3. Main
# ============================================================
def main():
    print("=" * 60)
    print("BioMniBench Skill Similarity Computation")
    print("=" * 60)

    print("\nLoading all skill bundles...")
    bundles = load_all_bundles()
    task_ids = sorted(bundles.keys())
    print(f"Loaded {len(bundles)} bundles")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Compute pairwise similarity matrix
    print("\nComputing pairwise similarity matrix...")
    similarity_matrix = {}
    pairs = []

    for i, t1 in enumerate(task_ids):
        similarity_matrix[t1] = {}
        for j, t2 in enumerate(task_ids):
            if i == j:
                similarity_matrix[t1][t2] = 1.0
                continue
            sim = compute_overall_similarity(bundles[t1], bundles[t2])
            similarity_matrix[t1][t2] = sim

            if t1 != t2:
                pairs.append({
                    "source": t1,
                    "target": t2,
                    "similarity": round(sim, 4),
                })

    # Sort by similarity (descending)
    pairs.sort(key=lambda x: x["similarity"], reverse=True)

    # Save full matrix
    matrix_path = OUTPUT_DIR / "similarity_matrix.json"
    with open(matrix_path, "w") as f:
        json.dump(similarity_matrix, f, indent=2)
    print(f"Saved matrix: {matrix_path}")

    # Save ranked pairs
    pairs_path = OUTPUT_DIR / "ranked_pairs.json"
    with open(pairs_path, "w") as f:
        json.dump(pairs, f, indent=2)
    print(f"Saved pairs: {pairs_path}")

    # Print top-20 cross-task pairs (different tasks)
    print("\n" + "=" * 60)
    print("Top-20 Cross-Task Transfer Pairs (source → target)")
    print("=" * 60)
    print(f"{'Rank':<5} {'Source':<10} {'Target':<10} {'Similarity':<12}")
    print("-" * 40)

    # Filter out same-task pairs
    cross_pairs = [p for p in pairs if p["source"] != p["target"]]
    for rank, p in enumerate(cross_pairs[:20], 1):
        print(f"{rank:<5} {p['source']:<10} {p['target']:<10} {p['similarity']:<12.4f}")

    # Print similarity stats
    sims = [p["similarity"] for p in pairs if p["source"] != p["target"]]
    print(f"\nStatistics:")
    print(f"  Mean similarity: {sum(sims)/len(sims):.4f}")
    print(f"  Median similarity: {sorted(sims)[len(sims)//2]:.4f}")
    print(f"  Min: {min(sims):.4f}")
    print(f"  Max: {max(sims):.4f}")

    # For each source task, show top-5 targets
    print("\n" + "=" * 60)
    print("Per-Source Top-5 Transfer Targets")
    print("=" * 60)
    for src in task_ids[:10]:  # show first 10 sources
        src_pairs = [p for p in pairs if p["source"] == src and p["target"] != src][:5]
        targets = ", ".join(f"{p['target']}({p['similarity']:.3f})" for p in src_pairs)
        print(f"  {src} → {targets}")

    if len(task_ids) > 10:
        print(f"  ... and {len(task_ids)-10} more sources")

    print("\nDone!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
compute_task_similarity.py

Compute semantic similarity between a source task and candidate target tasks.
Both structural keyword-based and LLM-based similarity are supported.

Usage:
  # Single pair
  python3 compute_task_similarity.py --source da-10-1 --target da-13-6

  # All 16 transfer pairs
  python3 compute_task_similarity.py --all-pairs

  # Source against ALL available tasks
  python3 compute_task_similarity.py --source da-10-1 --all-targets

  # Structural only (no LLM API call)
  python3 compute_task_similarity.py --all-pairs --no-llm
"""

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

# ============================================================
# Configuration
# ============================================================
TASKS_DIR = Path(os.environ.get("BIOMNIBENCH_TASKS_DIR", "runtime/tasks"))
TRANSFER_PAIRS_FILE = Path(os.environ.get("SKILL_TRANSFER_ROOT", "runtime")) / "summary_pruned" / "transfer_pruned_results.json"
OUTPUT_DIR = Path(os.environ.get("SKILL_TRANSFER_ROOT", "runtime")) / "similarity"

API_KEY = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("SKILL_TRANSFER_API_KEY", "")
API_URL = "https://api.gpugeek.com"
MODEL = "Vendor3/DeepSeek-V4-Flash"

# ============================================================
# Task domain knowledge base
# ============================================================
TASK_DOMAINS = {
    "da-17-1": "scRNA-seq: cell type composition (SLE vs healthy)",
    "da-17-5": "scRNA-seq: cell type composition (disease vs control, ancestry interaction)",
    "da-17-3": "scRNA-seq: cell type annotation and composition",
    "da-12-2": "scRNA-seq: pseudotime/trajectory analysis",
    "da-12-4": "scRNA-seq: differential expression / trajectory",
    "da-11-1": "scRNA-seq: cell-cell communication / ligand-receptor",
    "da-6-5":  "scRNA-seq: cluster annotation and marker finding",
    "da-15-2": "Bulk RNA-seq: differential expression",
    "da-15-7": "Bulk RNA-seq: differential expression with batch correction",
    "da-15-8": "Bulk RNA-seq: time-series DE analysis",
    "da-15-1": "Bulk RNA-seq: gene set enrichment analysis",
    "da-13-6": "Proteomics: association analysis (GAHT vs menopause protein changes)",
    "da-13-5": "Proteomics: comparative frequency / fold-change analysis",
    "da-13-3": "Proteomics: differential protein abundance",
    "da-13-1": "Proteomics: protein-protein interaction",
    "da-10-1": "ML: binary classification performance evaluation (ROC-AUC for phase-sep predictors)",
    "da-10-3": "ML: classifier comparison / AUC evaluation",
    "da-25-1": "ML: regression / prediction model building",
    "da-18-5": "Genomics: cohort genomic alteration analysis (mutations, CNA)",
    "da-18-7": "Genomics: mutual exclusivity / co-occurrence (ESR1 vs MAPK)",
    "da-18-1": "Genomics: somatic mutation analysis",
    "da-19-1": "Genomics: GWAS / variant association",
    "da-19-3": "Genomics: polygenic risk score",
    "da-19-4": "Genomics: variant prioritization / rare variant analysis",
    "da-19-6": "Genomics: variant annotation and filtering",
    "da-4-1":  "Immunology: TCR repertoire composite key and clonotype validation",
    "da-4-7":  "Immunology: TCR repertoire diversity and sharing analysis",
    "da-14-1": "Immunology: BCR repertoire analysis",
    "da-14-3": "Immunology: B cell clonality / somatic hypermutation",
    "da-14-8": "Immunology: antibody sequence analysis",
    "da-9-1":  "Epigenomics: ATAC-seq peak calling / chromatin accessibility",
    "da-9-7":  "Epigenomics: motif enrichment / TF footprinting",
    "da-26-2": "Spatial transcriptomics: spot-based analysis",
    "da-26-4": "Spatial transcriptomics: spatial clustering / domain detection",
    "da-1-3":  "General: composite key + rubric-based validation",
    "da-1-4":  "General: data transformation / standardization",
    "da-20-3": "Microbiome: 16S rRNA amplicon analysis",
    "da-8-2":  "Metabolomics: association study with stimulus-response phenotype",
    "da-8-3":  "Metabolomics: metabolite set enrichment",
    "da-5-1":  "General: foundational data analysis",
    "da-5-3":  "General: foundational data analysis",
}


def extract_task_features(text):
    """Extract structured features from README text."""
    text_lower = text.lower()
    features = {"data_types": [], "analysis_methods": [], "biological_domain": []}

    data_type_patterns = [
        ("scRNA-seq", ["scrna-seq", "single-cell", "single cell", "10x", "h5ad", "anndata", "pbmc"]),
        ("Bulk RNA-seq", ["bulk rna-seq", "rna-seq", "transcriptom", "gene expression", "count matrix"]),
        ("Proteomics", ["proteom", "protein", "olink", "mass spec"]),
        ("Genomics", ["mutation", "cna", "copy number", "somatic", "maf", "vcf"]),
        ("Epigenomics", ["atac-seq", "chip-seq", "chromatin", "histone", "methylation"]),
        ("Immunology (TCR/BCR)", ["tcr", "bcr", "t cell receptor", "b cell receptor", "clonotype", "cdr3"]),
        ("Spatial", ["spatial transcriptom", "spatial", "visium", "merfish"]),
        ("ML / Prediction", ["predictor", "classifier", "roc-auc", "machine learning", "auc"]),
        ("Metabolomics", ["metabolit", "metabolom"]),
        ("Microbiome", ["microbiome", "16s", "rrna", "amplicon"]),
        ("GWAS / Genetics", ["gwas", "genome-wide", "variant", "snp", "polygenic"]),
        ("Clinical / Cohort", ["clinical", "cohort", "patient", "survival"]),
    ]
    for dtype, patterns in data_type_patterns:
        if any(p in text_lower for p in patterns):
            features["data_types"].append(dtype)

    method_patterns = [
        ("Differential expression", ["differential expression", "deg", "deseq2", "edger", "limma"]),
        ("Cell type composition", ["cell type", "cell proportion", "composition", "pseudobulk"]),
        ("Correlation", ["correlation", "spearman", "pearson", "concordance"]),
        ("ROC-AUC", ["roc-auc", "roc_auc", "auc", "roc curve"]),
        ("Fisher exact test", ["fisher", "enrichment", "hypergeometric"]),
        ("Regression", ["regression", "linear model", "mixed model", "lmm"]),
        ("Clustering", ["cluster", "k-means", "umap", "tsne", "leiden", "louvain"]),
        ("Trajectory", ["pseudotime", "trajectory", "monocle", "diffusion map"]),
        ("Mutual exclusivity", ["mutual exclusivity", "co-occur"]),
        ("Survival analysis", ["survival", "kaplan", "cox", "hazard"]),
        ("Validation", ["validation", "rubric", "composite key", "clonotype"]),
        ("Gene set enrichment", ["enrichment", "gsea", "pathway", "ontology", "kegg"]),
    ]
    for mname, patterns in method_patterns:
        if any(p in text_lower for p in patterns):
            features["analysis_methods"].append(mname)

    bio_patterns = [
        ("Cancer / Oncology", ["cancer", "tumor", "oncology", "malignanc", "metasta"]),
        ("Immunology", ["immune", "lupus", "autoimmune", "inflammation", "t cell", "b cell"]),
        ("Hormone / Endocrine", ["hormone", "estrogen", "estradiol", "testosterone", "menopause", "gaht"]),
        ("Neuroscience", ["brain", "neuron", "synapse", "neuro"]),
        ("Development", ["development", "differentiation", "embryo", "stem cell"]),
        ("Infectious disease", ["infection", "virus", "bacteria", "pathogen", "covid"]),
        ("Cardiovascular", ["cardio", "heart", "vascular", "blood pressure"]),
        ("Aging", ["aging", "senescen", "longevity"]),
    ]
    for bname, patterns in bio_patterns:
        if any(p in text_lower for p in patterns):
            features["biological_domain"].append(bname)

    # Deduplicate
    for k in features:
        features[k] = list(set(features[k]))
    return features


def read_task_readme(task_id):
    path = TASKS_DIR / task_id / "README.md"
    if not path.exists():
        return ""
    return path.read_text()


def jaccard(a, b):
    """Jaccard similarity between two sets."""
    a, b = set(a), set(b)
    return len(a & b) / max(len(a | b), 1)


def compute_structural_similarity(f1, f2):
    """Compute similarity based on structured features."""
    data_j = jaccard(f1["data_types"], f2["data_types"])
    method_j = jaccard(f1["analysis_methods"], f2["analysis_methods"])
    bio_j = jaccard(f1["biological_domain"], f2["biological_domain"])
    structural = 0.40 * data_j + 0.35 * method_j + 0.25 * bio_j
    return {
        "data_type_jaccard": round(data_j, 4),
        "method_jaccard": round(method_j, 4),
        "bio_domain_jaccard": round(bio_j, 4),
        "structural_score": round(structural, 4),
    }


def compute_llm_similarity(src_text, target_text, src_id, tgt_id):
    """Use LLM to compute semantic similarity."""
    import urllib.request
    import urllib.error

    prompt = f"""You are an expert in biomedical data science. Evaluate the SIMILARITY between two computational biology tasks.

TASK A ({src_id}):
{src_text[:1500]}

TASK B ({tgt_id}):
{target_text[:1500]}

Rate the similarity between these two tasks on a scale from 0.0 to 1.0, considering:
1. Data type: Do they use the same type of data?
2. Analysis approach: Do they use similar statistical/ML methods?
3. Biological question: Do they ask similar types of questions?
4. Output format: Do they require similar deliverables?

Output ONLY a single float number between 0.0 and 1.0. No explanation, no markdown, just the number."""

    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 10,
    }).encode()

    req = urllib.request.Request(
        f"{API_URL}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        method="POST",
    )

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())
                content = result["choices"][0]["message"]["content"].strip()
                match = re.search(r"(\d+\.?\d*)", content)
                if match:
                    return min(max(float(match.group(1)), 0.0), 1.0)
                return 0.5
        except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
            if attempt < 2:
                time.sleep(3)
            else:
                print(f"  [WARN] LLM similarity failed for {src_id} -> {tgt_id}: {e}")
                return 0.5


def compute_similarity(src_id, tgt_id, use_llm=True):
    """Compute similarity between two tasks."""
    src_text = read_task_readme(src_id)
    tgt_text = read_task_readme(tgt_id)
    if not src_text or not tgt_text:
        return {"error": f"Cannot read README for {src_id} or {tgt_id}"}

    src_features = extract_task_features(src_text)
    tgt_features = extract_task_features(tgt_text)
    structural = compute_structural_similarity(src_features, tgt_features)

    result = {
        "source": src_id,
        "target": tgt_id,
        "src_domain": TASK_DOMAINS.get(src_id, "unknown"),
        "tgt_domain": TASK_DOMAINS.get(tgt_id, "unknown"),
        "src_data_types": src_features["data_types"],
        "tgt_data_types": tgt_features["data_types"],
        "src_methods": src_features["analysis_methods"],
        "tgt_methods": tgt_features["analysis_methods"],
        **structural,
    }

    if use_llm:
        llm_score = compute_llm_similarity(src_text, tgt_text, src_id, tgt_id)
        result["llm_similarity"] = llm_score
        result["combined_score"] = round(0.3 * result["structural_score"] + 0.7 * llm_score, 4)
    else:
        result["combined_score"] = result["structural_score"]

    return result


def main():
    parser = argparse.ArgumentParser(description="Compute task similarity")
    parser.add_argument("--source", type=str, help="Source task ID")
    parser.add_argument("--target", type=str, help="Target task ID")
    parser.add_argument("--all-pairs", action="store_true", help="Compute for all 16 transfer pairs")
    parser.add_argument("--all-targets", action="store_true", help="Source against ALL available tasks")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM similarity (structural only)")
    parser.add_argument("--threshold", type=float, default=0.4, help="Similarity threshold for go/no-go")
    parser.add_argument("--output", type=str, help="Output file path")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    use_llm = not args.no_llm
    results = []

    def fmt_score(val):
        if isinstance(val, float):
            return f"{val:.3f}"
        return str(val)

    if args.all_pairs:
        with open(TRANSFER_PAIRS_FILE) as f:
            data = json.load(f)
        pairs = [(p["source"], p["target"]) for p in data["pairs"]]
        print(f"Computing similarity for {len(pairs)} pairs...")
        for i, (src, tgt) in enumerate(pairs):
            print(f"  [{i+1}/{len(pairs)}] {src} -> {tgt}...", end=" ", flush=True)
            sim = compute_similarity(src, tgt, use_llm=use_llm)
            cs = sim.get("combined_score", 0)
            verdict = "GO" if isinstance(cs, float) and cs >= args.threshold else "NO-GO"
            sim["verdict"] = verdict
            results.append(sim)
            print(f"struct={fmt_score(sim.get('structural_score'))} "
                  f"llm={fmt_score(sim.get('llm_similarity', 'N/A'))} "
                  f"combined={fmt_score(cs)} -> {verdict}")
            if use_llm:
                time.sleep(1)

    elif args.source and args.target:
        sim = compute_similarity(args.source, args.target, use_llm=use_llm)
        cs = sim.get("combined_score", 0)
        verdict = "GO" if isinstance(cs, float) and cs >= args.threshold else "NO-GO"
        sim["verdict"] = verdict
        results.append(sim)
        print(f"\nSimilarity: {args.source} -> {args.target}")
        print(f"  Data type overlap:   {fmt_score(sim.get('data_type_jaccard'))}")
        print(f"  Method overlap:      {fmt_score(sim.get('method_jaccard'))}")
        print(f"  Bio domain overlap:  {fmt_score(sim.get('bio_domain_jaccard'))}")
        print(f"  Structural score:    {fmt_score(sim.get('structural_score'))}")
        if use_llm:
            print(f"  LLM similarity:      {fmt_score(sim.get('llm_similarity', 'N/A'))}")
        print(f"  Combined score:      {fmt_score(cs)}")
        print(f"  Verdict:             {verdict}")

    elif args.source and args.all_targets:
        task_ids = sorted([d.name for d in TASKS_DIR.iterdir() if d.is_dir() and d.name.startswith("da-")])
        print(f"Computing similarity for {args.source} against {len(task_ids)} tasks...")
        for tgt in task_ids:
            if tgt == args.source:
                continue
            print(f"  {args.source} -> {tgt}...", end=" ", flush=True)
            sim = compute_similarity(args.source, tgt, use_llm=use_llm)
            cs = sim.get("combined_score", 0)
            sim["verdict"] = "GO" if isinstance(cs, float) and cs >= args.threshold else "NO-GO"
            results.append(sim)
            print(f"combined={fmt_score(cs)} -> {sim['verdict']}")
            if use_llm:
                time.sleep(1)
    else:
        parser.print_help()
        return

    # Sort by combined score descending
    results.sort(key=lambda x: x.get("combined_score", 0) if isinstance(x.get("combined_score"), (int, float)) else 0, reverse=True)

    # Output path
    output_path = args.output
    if not output_path:
        if args.all_pairs:
            output_path = str(OUTPUT_DIR / "pairwise_similarity.json")
        elif args.source and args.target:
            output_path = str(OUTPUT_DIR / f"{args.source}_to_{args.target}_similarity.json")
        elif args.source and args.all_targets:
            output_path = str(OUTPUT_DIR / f"{args.source}_similarity.json")

    with open(output_path, "w") as f:
        json.dump({"threshold": args.threshold, "use_llm": use_llm, "results": results}, f, indent=2)
    print(f"\nResults saved to: {output_path}")

    # Summary table
    print(f"\n{'='*100}")
    print(f"SIMILARITY SUMMARY (threshold={args.threshold})")
    print(f"{'='*100}")
    print(f"  {'Source':12s} {'Target':12s}  {'Data':8s} {'Method':8s} {'Bio':8s} {'Struct':8s} {'LLM':8s} {'Combined':8s} Verdict")
    print(f"  {'-'*12} {'-'*12}  {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
    for r in results:
        dt = fmt_score(r.get("data_type_jaccard", 0))
        mt = fmt_score(r.get("method_jaccard", 0))
        bd = fmt_score(r.get("bio_domain_jaccard", 0))
        ss = fmt_score(r.get("structural_score", 0))
        ls = fmt_score(r.get("llm_similarity", "N/A"))
        cs = fmt_score(r.get("combined_score", 0))
        vs = r.get("verdict", "?")
        print(f"  {r['source']:12s} {r['target']:12s}  {dt:>8s} {mt:>8s} {bd:>8s} {ss:>8s} {ls:>8s} {cs:>8s} {vs:>8s}")

    go_count = sum(1 for r in results if r.get("verdict") == "GO")
    nog_count = sum(1 for r in results if r.get("verdict") == "NO-GO")
    print(f"\n  GO: {go_count}  |  NO-GO: {nog_count}")


if __name__ == "__main__":
    main()

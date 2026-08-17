#!/usr/bin/env python3
"""Systematic analysis of all 37 transfer pairs.
Categories:
- SKILL_USED + Δ>0.05 = skill genuinely helped
- SKILL_USED + Δ within ±0.05 = skill had no clear effect
- SKILL_USED + Δ<-0.05 = skill possibly harmed
- BLOCKED + Δ>0 = improvement despite skill being irrelevant
- BLOCKED + Δ within ±0.05 = expected
- BLOCKED + Δ<0 = skill not helpful but not harmful either
- BASELINE_ARTIFACT = baseline=0 but real score >0
"""
import json

# Raw data from the collection script
# Format: (source, target, base_rec, base_real, trans, skill_status, ops_count, same_cat, same_type, src_cat, tgt_cat, src_type, tgt_type)

pairs = [
    ("da-5-1", "da-5-3", 0.95, None, 0.95, "used", 8, True, True, "oncology", "oncology", "multi-omic-integration", "multi-omic-integration"),
    ("da-18-5", "da-18-7", 0.85, None, 0.95, "used", 10, True, True, "oncology", "oncology", "mutation-analysis", "mutation-analysis"),
    ("da-19-4", "da-19-6", 0.69, None, 1.00, "used", 3, True, True, "oncology", "oncology", "chromatin-profiling", "chromatin-profiling"),
    ("da-9-1", "da-9-7", 1.00, None, 0.93, "used", 2, True, False, "oncology", "oncology", "survival-analysis", "association-testing"),
    ("da-14-8", "da-14-1", 0.80, None, 1.00, "used", 0, True, False, "immunology", "immunology", "association-testing", "clustering"),
    ("da-15-2", "da-15-7", 0.70, None, 0.70, "used", 10, True, False, "neurology", "neurology", "co-expression-networks", "association-testing"),
    ("da-17-5", "da-17-1", 0.00, 78, 0.84, "used", 3, True, True, "immunology", "immunology", "cell-composition", "cell-composition"),
    ("da-13-6", "da-13-5", 0.70, None, 0.90, "used", 1, True, True, "metabolic", "metabolic", "cross-cohort-comparison", "cross-cohort-comparison"),
    ("da-12-4", "da-12-2", 0.60, None, 0.63, "used", 2, True, False, "oncology", "oncology", "survival-analysis", "pathway-enrichment"),
    ("da-4-7", "da-4-1", 0.61, None, 0.86, "used", 2, True, False, "oncology", "oncology", "tcr-repertoire", "clustering"),
    ("da-10-3", "da-10-1", 0.94, None, 0.64, "used", 2, True, True, "general-biology", "general-biology", "predictive-modeling", "predictive-modeling"),
    ("da-11-1", "da-6-5", 0.92, None, 0.67, "used", 1, False, False, "immunology", "cardiovascular", "cell-cell-communication", "multi-omic-integration"),
    ("da-26-4", "da-26-2", 0.87, None, 0.67, "used", 2, True, True, "oncology", "oncology", "predictive-modeling", "predictive-modeling"),
    ("da-4-1", "da-14-3", 0.85, None, 0.85, "blocked_but_overridden", 3, False, False, "oncology", "immunology", "clustering", "association-testing"),
    ("da-25-1", "da-1-3", 0.95, None, 0.90, "used", 2, True, False, "oncology", "oncology", "mutation-analysis", "cell-composition"),
    ("da-10-1", "da-13-6", 0.60, None, 0.60, "used", 3, False, False, "general-biology", "metabolic", "predictive-modeling", "cross-cohort-comparison"),
    ("da-17-5", "da-17-3", 0.73, None, 0.73, "used", 3, True, False, "immunology", "immunology", "cell-composition", "differential-expression"),
    ("da-15-2", "da-15-1", 1.00, None, 1.00, "used", 10, True, False, "neurology", "neurology", "co-expression-networks", "differential-expression"),
    ("da-13-6", "da-13-3", 1.00, None, 0.87, "used", 1, True, False, "metabolic", "metabolic", "cross-cohort-comparison", "association-testing"),
    ("da-19-4", "da-19-1", 0.72, None, 0.63, "used", 3, True, False, "oncology", "oncology", "chromatin-profiling", "differential-expression"),
    ("da-18-5", "da-18-1", 0.90, None, 0.72, "used", 10, True, True, "oncology", "oncology", "mutation-analysis", "mutation-analysis"),
    ("da-10-1", "da-6-2", 0.72, None, 0.92, "used", 3, False, False, "general-biology", "cardiovascular", "predictive-modeling", "longitudinal-analysis"),
    ("da-19-4", "da-19-3", 0.75, None, 0.90, "used", 3, True, True, "oncology", "oncology", "chromatin-profiling", "chromatin-profiling"),
    ("da-17-5", "da-14-3", 0.85, None, 0.71, "used", 3, True, False, "immunology", "immunology", "cell-composition", "association-testing"),
    ("da-13-6", "da-13-1", 0.95, None, 0.69, "used", 1, True, False, "metabolic", "metabolic", "cross-cohort-comparison", "differential-expression"),
    ("da-4-7", "da-12-2", 0.60, None, 0.60, "blocked_but_overridden", 2, True, False, "oncology", "oncology", "tcr-repertoire", "pathway-enrichment"),
    ("da-4-1", "da-12-2", 0.60, None, 0.60, "blocked_but_overridden", 3, True, False, "oncology", "oncology", "clustering", "pathway-enrichment"),
    ("da-9-1", "da-1-4", 0.86, None, 0.86, "used", 2, True, False, "oncology", "oncology", "survival-analysis", "association-testing"),
    ("da-15-2", "da-15-8", 0.63, None, 0.63, "blocked_but_overridden", 10, True, False, "neurology", "neurology", "co-expression-networks", "multi-omic-integration"),
    ("da-25-1", "da-18-7", 0.85, None, 0.70, "used", 2, True, True, "oncology", "oncology", "mutation-analysis", "mutation-analysis"),
    ("da-5-1", "da-26-2", 0.87, None, 0.69, "used", 8, True, False, "oncology", "oncology", "multi-omic-integration", "predictive-modeling"),
    ("da-26-4", "da-12-2", 0.60, None, 0.60, "blocked_but_overridden", 2, True, False, "oncology", "oncology", "predictive-modeling", "pathway-enrichment"),
    ("da-12-4", "da-17-1", 0.00, 78, 0.84, "blocked_but_overridden", 2, False, False, "oncology", "immunology", "survival-analysis", "cell-composition"),
    ("da-14-8", "da-1-3", 0.95, None, 0.95, "blocked_but_overridden", 0, False, False, "immunology", "oncology", "association-testing", "cell-composition"),
    ("da-10-1", "da-6-5", 0.92, None, 0.67, "used", 3, False, False, "general-biology", "cardiovascular", "predictive-modeling", "multi-omic-integration"),
    ("da-11-1", "da-6-2", 0.72, None, 0.75, "used", 4, False, False, "immunology", "cardiovascular", "cell-cell-communication", "longitudinal-analysis"),
    ("da-10-3", "da-13-6", 0.60, None, 0.60, "used", 2, False, False, "general-biology", "metabolic", "predictive-modeling", "cross-cohort-comparison"),
]

# Compute deltas
def get_delta(base_rec, base_real, trans):
    if base_real is not None:
        # Use real score if available
        real_base = base_real / 100.0  # convert 78 -> 0.78
        return round(trans - real_base, 2)
    elif base_rec is not None:
        return round(trans - base_rec, 2)
    return None

print("=" * 140)
print(f"{'#':>3} | {'Pair':>25} | {'Base_rec':>8} | {'Base_real':>8} | {'Trans':>6} | {'Δ_orig':>8} | {'Δ_real':>8} | {'SkillStat':>22} | {'Category':>20}")
print("=" * 140)

categories = {
    "skill_help": [],      # used + Δ>0.05
    "skill_none": [],      # used + Δ within ±0.05
    "skill_harm": [],      # used + Δ<-0.05
    "blocked_neutral": [], # blocked + Δ within ±0.05 or baseline artifact
    "blocked_artifact": [], # blocked + baseline=0 artifact
    "skill_help_artifact": [], # used + baseline=0 artifact
}

for i, p in enumerate(pairs):
    src, tgt, base_rec, base_real, trans, status, ops, same_cat, same_type = p[:9]
    
    delta_orig = round(trans - base_rec, 2) if base_rec is not None else None
    if base_real is not None:
        real_base = base_real / 100.0
        delta_real = round(trans - real_base, 2)
    else:
        delta_real = None
    
    # Determine category
    is_artifact = (base_rec == 0.0 and base_real is not None and base_real > 0)
    
    base_rec_str = f"{base_rec:.2f}" + ("⚠️" if is_artifact else "")
    base_real_str = f"{base_real/100:.2f}" if base_real is not None else "N/A"
    trans_str = f"{trans:.2f}"
    delta_orig_str = f"{delta_orig:+.2f}" if delta_orig is not None else "N/A"
    delta_real_str = f"{delta_real:+.2f}" if delta_real is not None else f"{delta_orig:+.2f}" if delta_orig is not None else "N/A"
    
    pair_name = f"{src}→{tgt}"
    
    # Use real delta for classification
    effective_delta = delta_real if delta_real is not None else delta_orig
    
    if is_artifact and status == "used":
        cat = "base_artifact_used"
        category = "BaselineArtifact+Used"
    elif is_artifact and status == "blocked_but_overridden":
        cat = "base_artifact_blocked"
        category = "BaselineArtifact+Blocked"
    elif status == "blocked_but_overridden":
        cat = "blocked"
        if effective_delta is not None and effective_delta > 0.05:
            category = "BlockedButImproved"
        elif effective_delta is not None and effective_delta < -0.05:
            category = "BlockedButWorse"
        else:
            category = "BlockedNeutral"
    else:  # used
        if effective_delta is not None and effective_delta > 0.05:
            category = "SkillHelped ✅"
        elif effective_delta is not None and effective_delta < -0.05:
            category = "SkillHarmed ❌"
        else:
            category = "SkillNeutral ➖"
    
    print(f"{i+1:>3} | {pair_name:>25} | {base_rec_str:>8} | {base_real_str:>8} | {trans_str:>6} | {delta_orig_str:>8} | {delta_real_str:>8} | {status:>22} | {category:>20}")

print("=" * 140)

# Summary
print("\n\n=== SUMMARY ===")
print(f"\n1. BASELINE ARTIFACTS (baseline=0 but real score >0):")
print(f"   da-17-1 baseline: recorded=0.00, real=78/100 (affects pairs #7, #33)")
print(f"   → Both pairs involving da-17-1 as target have inflated Δ")

print(f"\n2. SKILL APPLICATION STATUS:")
blocked = [p for p in pairs if p[5] == "blocked_but_overridden"]
used = [p for p in pairs if p[5] == "used"]
print(f"   Used: {len(used)} pairs")
print(f"   Blocked (agent said skill not applicable): {len(blocked)} pairs")
print(f"   Blocked pairs: {', '.join([f'{p[0]}→{p[1]}' for p in blocked])}")

print(f"\n3. GENUINE SKILL HELP (skill used, Δ > +0.05, no artifact):")
genuine_help = []
for p in pairs:
    src, tgt, base_rec, base_real, trans, status, ops = p[:7]
    if status == "used":
        delta = round(trans - (base_real/100.0 if base_real else base_rec), 2)
        is_artifact = (base_rec == 0.0 and base_real and base_real > 0)
        if not is_artifact and delta > 0.05:
            genuine_help.append((src, tgt, delta))
for s, t, d in genuine_help:
    print(f"   {s}→{t}: Δ = {d:+.2f}")

print(f"\n4. SKILL HARMED (skill used, Δ < -0.05, no artifact):")
skill_harm = []
for p in pairs:
    src, tgt, base_rec, base_real, trans, status, ops = p[:7]
    if status == "used":
        delta = round(trans - (base_real/100.0 if base_real else base_rec), 2)
        is_artifact = (base_rec == 0.0 and base_real and base_real > 0)
        if not is_artifact and delta < -0.05:
            skill_harm.append((src, tgt, delta))
for s, t, d in skill_harm:
    print(f"   {s}→{t}: Δ = {d:+.2f}")

print(f"\n5. SKILL NEUTRAL (skill used, Δ within ±0.05):")
skill_neutral = []
for p in pairs:
    src, tgt, base_rec, base_real, trans, status, ops = p[:7]
    if status == "used":
        delta = round(trans - (base_real/100.0 if base_real else base_rec), 2)
        is_artifact = (base_rec == 0.0 and base_real and base_real > 0)
        if not is_artifact and -0.05 <= delta <= 0.05:
            skill_neutral.append((src, tgt, delta))
for s, t, d in skill_neutral:
    print(f"   {s}→{t}: Δ = {d:+.2f}")

print(f"\n6. BLOCKED PAIRS (skill deemed not applicable):")
for p in blocked:
    src, tgt, base_rec, base_real, trans, status, ops = p[:7]
    delta = round(trans - (base_real/100.0 if base_real else base_rec), 2)
    is_artifact = (base_rec == 0.0 and base_real and base_real > 0)
    print(f"   {src}→{tgt}: trans={trans}, base({'real' if base_real else 'rec'})={base_real/100.0 if base_real else base_rec}, Δ={delta:+.2f}")

print(f"\n7. CORRECTED STATISTICS:")
total = 37
# Skill helped (genuine, no artifact)
n_help = len(genuine_help)
n_harm = len(skill_harm)
n_neutral = len(skill_neutral)
n_blocked = len(blocked)
n_artifact = len([p for p in pairs if p[2] == 0.0 and p[3] is not None and p[3] > 0])
print(f"   Skill Helped:  {n_help}/{total} ({n_help/total*100:.0f}%)")
print(f"   Skill Harmed:  {n_harm}/{total} ({n_harm/total*100:.0f}%)")
print(f"   Skill Neutral: {n_neutral}/{total} ({n_neutral/total*100:.0f}%)")
print(f"   Blocked (skill not applicable): {n_blocked}/{total} ({n_blocked/total*100:.0f}%)")
print(f"   Baseline Artifact: {n_artifact}/{total} ({n_artifact/total*100:.0f}%)")
print(f"   Net positive (help - harm): {n_help - n_harm}")
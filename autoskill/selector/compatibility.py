from typing import Mapping, Tuple

GROUPS = [
    {"differential-expression", "chromatin-profiling", "pathway-enrichment"},
    {"association-testing", "gwas-eqtl"},
    {"cell-composition", "cell-cell-communication", "clustering"},
    {"predictive-modeling", "survival-analysis", "longitudinal-analysis"},
    {"co-expression-networks", "multi-omic-integration", "cross-cohort-comparison"},
    {"mutation-analysis", "tcr-repertoire"},
]


def tier(source: str, target: str, types: Mapping[str, str]) -> str:
    st, tt = types.get(source), types.get(target)
    if st and tt and st == tt:
        return "same"
    if st and tt and any(st in group and tt in group for group in GROUPS):
        return "compatible"
    return "incompatible"


def score_params(kind: str, cfg) -> Tuple[float, float]:
    if kind == "same":
        return cfg.same_bonus, cfg.same_threshold
    if kind == "compatible":
        return cfg.compatible_bonus, cfg.compatible_threshold
    return -1.0, float("inf")

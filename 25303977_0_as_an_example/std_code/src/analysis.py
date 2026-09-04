from __future__ import annotations

from pathlib import Path

import pandas as pd

SUBSTITUTION_COLUMNS = ["A>C", "A>G", "A>T", "C>A", "C>G", "C>T", "CC>TT", "Others"]
KNOWN_SUBSTITUTIONS = set(SUBSTITUTION_COLUMNS[:-1])


def determine_substitution(reference: str, alternate: str) -> str | None:
    if reference == alternate:
        return None
    substitution = f"{reference}>{alternate}"
    return substitution if substitution in KNOWN_SUBSTITUTIONS else "Others"


def compute_substitution_ratios(mutation_csv: str | Path) -> pd.DataFrame:
    data_mutations = pd.read_csv(mutation_csv)
    data_mutations["Substitution1"] = data_mutations.apply(
        lambda row: determine_substitution(row["Reference_Allele"], row["Tumor_Seq_Allele1"]), axis=1
    )
    data_mutations["Substitution2"] = data_mutations.apply(
        lambda row: determine_substitution(row["Reference_Allele"], row["Tumor_Seq_Allele2"]), axis=1
    )
    data_mutations["Substitution"] = data_mutations["Substitution1"].combine_first(data_mutations["Substitution2"])
    data_mutations = data_mutations.dropna(subset=["Substitution"])
    substitution_ratios = data_mutations.groupby(["Tumor_Sample_Barcode", "Substitution"]).size().unstack(fill_value=0)
    substitution_ratios = substitution_ratios.reindex(columns=SUBSTITUTION_COLUMNS, fill_value=0)
    substitution_ratios = substitution_ratios.div(substitution_ratios.sum(axis=1), axis=0)
    return substitution_ratios

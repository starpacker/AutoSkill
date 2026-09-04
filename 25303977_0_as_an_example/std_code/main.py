from __future__ import annotations

from pathlib import Path

from src.analysis import compute_substitution_ratios

mutation_csv = Path("visible_data/cases/case_000/input_data/data_mutations.csv")
substitution_ratios = compute_substitution_ratios(mutation_csv)

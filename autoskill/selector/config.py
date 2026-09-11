import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SelectorConfig:
    results_index: Path = Path(os.getenv("AUTOSKILL_RESULTS_INDEX", "results_index.json"))
    similarity: Path = Path(os.getenv("AUTOSKILL_SIMILARITY", "similarity_matrix.json"))
    model: Path = Path(os.getenv("AUTOSKILL_SELECTOR_MODEL", "v7_model.json"))
    task_types: Path = Path(os.getenv("AUTOSKILL_TASK_TYPES", "task_types.json"))
    same_bonus: float = 0.15
    same_threshold: float = -0.15
    compatible_bonus: float = 0.02
    compatible_threshold: float = 0.05
    baseline_max: float = 0.80

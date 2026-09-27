# BioMNIBench dataloader — loads task metadata from organized tasks directory
from __future__ import annotations

import os
import tomllib

from skillopt.datasets.base import SplitDataLoader


class BioMNIBenchDataLoader(SplitDataLoader):
    """Load BioMNIBench tasks.

    Tasks are organized as ``<task_id>/`` directories under ``data_path``.
    For skill-opt we treat each task as a single item with its metadata.
    """

    def load_raw_items(self, data_path: str) -> list[dict]:
        """Scan <data_path> for task directories, return list of item dicts."""
        items = []
        for entry in sorted(os.listdir(data_path)):
            task_dir = os.path.join(data_path, entry)
            if not os.path.isdir(task_dir):
                continue
            task_id = entry

            # Read task.toml
            task_toml_path = os.path.join(task_dir, "task.toml")
            metadata = {}
            if os.path.exists(task_toml_path):
                with open(task_toml_path, "rb") as f:
                    metadata = tomllib.load(f)

            # Read README
            readme_path = os.path.join(task_dir, "README.md")
            readme = ""
            if os.path.exists(readme_path):
                with open(readme_path, "r", encoding="utf-8") as f:
                    readme = f.read()

            items.append({
                "id": task_id,
                "task_dir": task_dir,
                "readme": readme,
                "metadata": metadata,
                "category": (
                    metadata.get("metadata", {}).get("category", "unknown")
                ),
                "difficulty": (
                    metadata.get("metadata", {}).get("difficulty", "unknown")
                ),
                "task_type": (
                    metadata.get("metadata", {}).get("task_type", "unknown")
                ),
            })
        return items
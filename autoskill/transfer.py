"""Unified evaluation-arm specifications and result aggregation."""

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional

from my_claude import HarnessRunner, Skill, Task


ARMS = ("no-skill", "oracle", "gt-few-shot", "v10-sel")


@dataclass
class ArmResult:
    task_id: str
    arm: str
    reward: Optional[float]
    status: str
    source_skill: Optional[str] = None


def run_arms(task: Task, runner: HarnessRunner, *,
             oracle: Optional[Skill] = None, selected: Optional[Skill] = None,
             execute: bool = False) -> list[ArmResult]:
    specs = [("no-skill", None), ("oracle", oracle), ("gt-few-shot", oracle),
             ("v10-sel", selected)]
    results = []
    for arm, skill in specs:
        result = runner.run(task, arm, skill, execute=execute)
        results.append(ArmResult(task.task_id, arm, result.reward, result.status,
                                 skill.name if skill else None))
    return results


def write_comparison(rows: Iterable[ArmResult], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    output.write_text(json.dumps([asdict(r) for r in rows], indent=2), encoding="utf-8")
    csv_path = output.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["task_id", "arm", "reward", "status", "source_skill"])
        writer.writeheader()
        writer.writerows(asdict(r) for r in rows)

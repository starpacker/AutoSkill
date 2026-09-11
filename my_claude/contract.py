from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Task:
    task_id: str
    path: Path
    instruction: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Skill:
    name: str
    path: Path
    content: str


@dataclass(frozen=True)
class EvaluationResult:
    task_id: str
    arm: str
    reward: Optional[float]
    status: str
    command: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)

"""Thin adapter around the private my_claude/Bun harness.

The public package deliberately does not vendor the private runtime. It emits
the same command shape used on server1 and supports dry-runs locally.
"""

import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from .contract import EvaluationResult, Skill, Task


@dataclass
class HarnessConfig:
    harness_dir: Path = Path(os.environ.get("AUTOSKILL_HARNESS_DIR", ""))
    bun_bin: Path = Path(os.environ.get("AUTOSKILL_BUN_BIN", "bun"))
    tasks_dir: Path = Path(os.environ.get("AUTOSKILL_TASKS_DIR", "tasks"))
    runs_dir: Path = Path(os.environ.get("AUTOSKILL_RUNS_DIR", "runs"))
    max_rounds: int = 5
    timeout_seconds: int = 7200


class HarnessRunner:
    def __init__(self, config: Optional[HarnessConfig] = None):
        self.config = config or HarnessConfig()

    def command(self, task: Task, arm: str, skill: Optional[Skill] = None) -> Sequence[str]:
        c = self.config
        cmd = [
            str(c.bun_bin), "src/harness/evaluation/cli.ts",
            "--task", task.task_id, "--tasks-dir", str(c.tasks_dir),
            "--runs-dir", str(c.runs_dir / arm),
            "--max-rounds", str(c.max_rounds),
            "--timeout-seconds", str(c.timeout_seconds),
        ]
        if skill:
            cmd += ["--enable-skills", "--skills-dir", str(skill.path.parent),
                    "--skill-name", skill.name, "--max-active-skills", "1"]
        return cmd

    def run(self, task: Task, arm: str, skill: Optional[Skill] = None,
            execute: bool = False) -> EvaluationResult:
        cmd = list(self.command(task, arm, skill))
        rendered = " ".join(shlex.quote(x) for x in cmd)
        if not execute:
            return EvaluationResult(task.task_id, arm, None, "dry-run", rendered)
        if not self.config.harness_dir.exists():
            raise FileNotFoundError(
                f"Harness directory not found: {self.config.harness_dir}. "
                "Set AUTOSKILL_HARNESS_DIR or use dry-run."
            )
        proc = subprocess.run(cmd, cwd=self.config.harness_dir, text=True,
                              capture_output=True,
                              timeout=self.config.timeout_seconds + 60)
        raw = {"stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:],
               "returncode": proc.returncode}
        reward = None
        for line in proc.stdout.splitlines():
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) and "reward" in obj:
                    reward = float(obj["reward"])
            except (ValueError, TypeError, json.JSONDecodeError):
                continue
        status = "success" if proc.returncode == 0 else "failed"
        return EvaluationResult(task.task_id, arm, reward, status, rendered, raw)

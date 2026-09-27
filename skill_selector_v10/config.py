"""
Centralized configuration for the V10 skill selector pipeline.

All server paths, API keys, model names, and evaluation parameters
are defined here. Single source of truth — import this everywhere.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class V10Config:
    # ── Server Paths ──────────────────────────────────────────────────────
    remote_base: str = field(default_factory=lambda: os.environ.get(
        "AUTOSKILL_REMOTE_BASE", "/path/to/skill-transfer-eval"))
    generalized_skills_dir: str = field(init=False)
    skills_dir: str = field(init=False)
    similarity_path: str = field(init=False)
    results_index_path: str = field(init=False)
    confidence_model_path: str = field(init=False)
    bio_dir: str = field(default_factory=lambda: os.environ.get(
        "BIOMNIBENCH_DIR", "/path/to/biomnibench-organized"))
    runs_dir: str = field(init=False)
    transfer_dir: str = field(init=False)

    # ── Harness / CLI ────────────────────────────────────────────────────
    harness_dir: str = field(default_factory=lambda: os.environ.get(
        "AUTOSKILL_HARNESS_DIR", "/path/to/my_claude_harness"))
    bun_bin: str = field(default_factory=lambda: os.environ.get(
        "AUTOSKILL_BUN_BIN", "bun"))

    # ── API ───────────────────────────────────────────────────────────────
    anthropic_api_key: str = field(default_factory=lambda: os.environ.get(
        "ANTHROPIC_API_KEY", ""))
    anthropic_base_url: str = field(default_factory=lambda: os.environ.get(
        "ANTHROPIC_BASE_URL", "https://api.example.com"))
    worker_model: str = field(default_factory=lambda: os.environ.get(
        "ANTHROPIC_MODEL", "your-model"))

    qwen_api_key: str = field(default_factory=lambda: os.environ.get("QWEN_API_KEY", ""))
    qwen_base_url: str = field(default_factory=lambda: os.environ.get(
        "QWEN_BASE_URL", "https://api.example.com/v1"))
    judge_model: str = field(default_factory=lambda: os.environ.get(
        "QWEN_MODEL", "your-model"))

    # ── Evaluation ────────────────────────────────────────────────────────
    max_rounds: int = 5
    timeout_seconds: int = 7200
    concurrency: int = 1
    temperature: float = 1.0
    thinking: str = "disabled"

    # ── Selector Thresholds ───────────────────────────────────────────────
    # Same-type: very permissive (validation shows even negative scores can give +0.11)
    same_type_bonus: float = 0.15
    same_type_threshold: float = -0.15

    # Compatible: moderate
    compatible_bonus: float = 0.02
    compatible_threshold: float = 0.05

    # Incompatible: hard reject
    incompatible_penalty: float = -1.00

    # Baseline gating: skip targets with baseline > this
    bl_max: float = 0.80

    # P1 exempt from all thresholds, but must have delta > 0 after bonus
    # P2/P3 use tiered thresholds defined above

    # ── SSH ───────────────────────────────────────────────────────────────
    ssh_host: str = field(default_factory=lambda: os.environ.get("AUTOSKILL_SSH_HOST", ""))
    ssh_opts: str = field(default_factory=lambda: os.environ.get(
        "AUTOSKILL_SSH_OPTS", "-o ConnectTimeout=10"))

    def __post_init__(self):
        self.generalized_skills_dir = f"{self.remote_base}/generalized_skills"
        self.skills_dir = f"{self.remote_base}/skills"
        self.similarity_path = f"{self.remote_base}/similarity/similarity_matrix.json"
        self.results_index_path = f"{self.remote_base}/results_index.json"
        self.confidence_model_path = f"{self.remote_base}/skill_selector/v7_model.json"
        self.runs_dir = f"{self.remote_base}/generalized"
        self.transfer_dir = f"{self.remote_base}/transfer"

    def to_env(self) -> Dict[str, str]:
        """Return environment variables dict for subprocesses."""
        return {
            "ANTHROPIC_API_KEY": self.anthropic_api_key,
            "ANTHROPIC_BASE_URL": self.anthropic_base_url,
            "ANTHROPIC_MODEL": self.worker_model,
            "QWEN_API_KEY": self.qwen_api_key,
            "QWEN_BASE_URL": self.qwen_base_url,
            "QWEN_MODEL": self.judge_model,
        }

    def ssh_cmd(self, remote_command: str) -> str:
        """Build an SSH command string."""
        return f"ssh {self.ssh_opts} {self.ssh_host} {remote_command}"


# Global default config (singleton for convenience)
DEFAULT_CONFIG = V10Config()
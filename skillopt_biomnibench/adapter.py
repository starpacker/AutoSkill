"""BioMNIBench environment adapter for SkillOpt."""
from __future__ import annotations

from skillopt.datasets.base import BatchSpec
from skillopt.envs.base import EnvAdapter
from skillopt.envs.biomnibench.dataloader import BioMNIBenchDataLoader
from skillopt.envs.biomnibench.rollout import run_batch


class BioMNIBenchAdapter(EnvAdapter):
    """BioMNIBench environment adapter.

    Each item is a task directory with README, data files, and evaluation
    rubric. The harness CLI runs the full agentic loop for each task.
    """

    def __init__(
        self,
        split_dir: str = "",
        data_path: str = "/data/yjh/biomnibench-organized",
        split_mode: str = "split_dir",
        split_ratio: str = "2:1:7",
        split_seed: int = 42,
        split_output_dir: str = "",
        max_rounds: int = 3,
        exec_timeout: int = 7200,
        workers: int = 2,
        analyst_workers: int = 8,
        failure_only: bool = False,
        minibatch_size: int = 4,
        edit_budget: int = 4,
        seed: int = 42,
        limit: int = 0,
        max_completion_tokens: int = 16384,
    ) -> None:
        self.max_rounds = max_rounds
        self.exec_timeout = exec_timeout
        self.workers = workers
        self.max_completion_tokens = int(max_completion_tokens)
        self.analyst_workers = analyst_workers
        self.failure_only = failure_only
        self.minibatch_size = minibatch_size
        self.edit_budget = edit_budget
        self.dataloader = BioMNIBenchDataLoader(
            split_dir=split_dir,
            data_path=data_path,
            split_mode=split_mode,
            split_ratio=split_ratio,
            split_seed=split_seed,
            split_output_dir=split_output_dir,
            seed=seed,
            limit=limit,
        )

    def setup(self, cfg: dict) -> None:
        super().setup(cfg)
        self.dataloader.setup(cfg)

    def get_dataloader(self):
        return self.dataloader

    def build_env_from_batch(self, batch: BatchSpec, **kwargs):
        return list(batch.payload or [])

    def build_train_env(self, batch_size: int, seed: int, **kwargs):
        batch = self.dataloader.build_train_batch(
            batch_size=batch_size, seed=seed, **kwargs
        )
        return self.build_env_from_batch(batch, **kwargs)

    def build_eval_env(self, env_num: int, split: str, seed: int, **kwargs):
        batch = self.dataloader.build_eval_batch(
            env_num=env_num, split=split, seed=seed, **kwargs
        )
        return self.build_env_from_batch(batch, **kwargs)

    def rollout(
        self,
        env_manager,
        skill_content: str,
        out_dir: str,
        **kwargs,
    ) -> list[dict]:
        """Run harness on batch of tasks under current skill."""
        items: list[dict] = env_manager
        return run_batch(
            items=items,
            out_root=out_dir,
            skill_content=skill_content,
            max_rounds=self.max_rounds,
            exec_timeout=self.exec_timeout,
            workers=self.workers,
            temperature=kwargs.get("temperature", 1.0),
        )

    def get_task_types(self) -> list[str]:
        seen: list[str] = []
        all_items = (
            self.dataloader.train_items
            + self.dataloader.val_items
            + self.dataloader.test_items
        )
        for item in all_items:
            tt = str(item.get("task_type") or "unknown")
            if tt not in seen:
                seen.append(tt)
        return seen or ["biomnibench"]
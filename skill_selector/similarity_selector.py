"""
Similarity-based Skill Selector.

Selects the skill from the source task that has the highest similarity
to the target task. This serves as the baseline selector.
"""

from typing import Dict, Optional, Tuple
from .base import SkillSelector


class SimilaritySelector(SkillSelector):
    """Selects the skill from the source task most similar to the target.

    Simple strategy: pick the source task with the highest similarity score
    to the target task. This is the baseline selector.
    """

    def __init__(self, min_similarity: float = 0.0):
        """Initialize with optional minimum similarity threshold.

        Args:
            min_similarity: Minimum similarity to consider a skill.
                            Set >0 to skip low-similarity sources.
        """
        self.min_similarity = min_similarity

    def select_skill(
        self,
        target_task: str,
        available_skills: Dict[str, str],
        similarity_matrix: Dict[str, Dict[str, float]],
    ) -> Tuple[Optional[str], float]:
        """Select skill from the most similar source task.

        Strategy:
        1. For each available source skill, look up similarity(target, source).
        2. Pick the source with the highest similarity.
        3. Skip sources below min_similarity threshold.

        Args:
            target_task: The target task ID.
            available_skills: Dict of source_task -> SKILL.md path.
            similarity_matrix: Nested similarity dict.

        Returns:
            (best_source, confidence) where confidence = similarity score.
            (None, 0.0) if no source meets the threshold.
        """
        target_sims = similarity_matrix.get(target_task, {})
        if not target_sims:
            return (None, 0.0)

        best_source = None
        best_sim = 0.0

        for source_task in available_skills:
            sim = target_sims.get(source_task, 0.0)
            if sim > best_sim and sim >= self.min_similarity:
                best_sim = sim
                best_source = source_task

        return (best_source, best_sim)

    def get_name(self) -> str:
        return "SimilaritySelector"

    def describe_selection(self, target_task: str, selected_source: Optional[str],
                          confidence: float) -> str:
        if selected_source is None:
            return (
                f"[SimilaritySelector] No skill meets min_similarity={self.min_similarity} "
                f"for target '{target_task}'"
            )
        return (
            f"[SimilaritySelector] Selected skill from '{selected_source}' "
            f"for target '{target_task}' (sim={confidence:.3f})"
        )
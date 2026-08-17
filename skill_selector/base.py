"""
Base interface for Skill Selectors.

All skill selectors must inherit from SkillSelector and implement
the select_skill method. This allows easy swapping of selection strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional


class SkillSelector(ABC):
    """Abstract base class for skill selection strategies.

    A SkillSelector takes a target task and a skill library, and selects
    the best skill to transfer to that target task.
    """

    @abstractmethod
    def select_skill(
        self,
        target_task: str,
        available_skills: Dict[str, str],
        similarity_matrix: Dict[str, Dict[str, float]],
    ) -> Tuple[Optional[str], float]:
        """Select the best skill for a target task.

        Args:
            target_task: The target task ID (e.g., 'da-6-2').
            available_skills: Dict mapping source_task_id -> path to SKILL.md.
            similarity_matrix: Nested dict sim_matrix[A][B] -> float similarity.

        Returns:
            Tuple of (selected_source_task, confidence_score).
            If no suitable skill is found, selected_source_task may be None.
            confidence_score is in [0, 1], higher = more confident.
        """
        ...

    def get_name(self) -> str:
        """Return the human-readable name of this selector."""
        return self.__class__.__name__

    def describe_selection(self, target_task: str, selected_source: Optional[str],
                          confidence: float) -> str:
        """Generate a human-readable explanation of the selection."""
        if selected_source is None:
            return f"[{self.get_name()}] No suitable skill found for {target_task}"
        return (
            f"[{self.get_name()}] Selected skill from '{selected_source}' "
            f"for target '{target_task}' (confidence={confidence:.3f})"
        )
"""
SmartSelectorV10 — SOTA Skill Selector for BioDSBench Transfer Learning.

A self-contained, standalone package with no external dependencies.
"""

from .config import V10Config
from .compatibility import Compatibility, COMPATIBILITY_GROUPS
from .data import DataLoader
from .selector import SmartSelectorV10

__all__ = [
    "V10Config",
    "Compatibility",
    "COMPATIBILITY_GROUPS",
    "DataLoader",
    "SmartSelectorV10",
]
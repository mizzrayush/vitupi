"""
Candidate ranking and diversity-aware selection algorithms.
"""

from vitupi.selection.ranking import rank_candidates
from vitupi.selection.diversity import select_diverse_photos

__all__ = ["rank_candidates", "select_diverse_photos"]

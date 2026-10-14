"""
Candidate scoring and utility ranking.
"""

from typing import List
from vitupi.models import CandidateFrame


def calculate_utility(candidate: CandidateFrame) -> float:
    """Calculate overall utility balancing photographic quality and visual novelty."""
    return (0.60 * candidate.composite_quality) + (0.40 * candidate.novelty_score)


def rank_candidates(candidates: List[CandidateFrame]) -> List[CandidateFrame]:
    """Sort candidates in descending order of calculated utility."""
    return sorted(candidates, key=calculate_utility, reverse=True)

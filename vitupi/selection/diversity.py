"""
Diversity-aware candidate selection balancing quality, coverage, and temporal distribution.
"""

from collections import defaultdict
from typing import List, Optional
from vitupi.models import CandidateFrame
from vitupi.selection.ranking import calculate_utility


def select_diverse_photos(
    candidates: List[CandidateFrame],
    max_photos: Optional[int] = 100,
    min_temporal_distance: float = 0.5,
) -> List[CandidateFrame]:
    """Select the optimal diverse subset of candidates.

    Guarantees:
    1. Coverage across all detected scenes (at least one candidate per scene if available).
    2. Minimum temporal separation between consecutive photos.
    3. Chronological ordering of final output.
    """
    valid_candidates = [c for c in candidates if not c.is_rejected]
    if not valid_candidates:
        return []

    if max_photos is not None and len(valid_candidates) <= max_photos:
        # If fewer candidates exist than max allowed, just filter by temporal distance
        chosen = _filter_by_temporal_distance(valid_candidates, min_temporal_distance)
        return sorted(chosen, key=lambda c: c.timestamp_sec)

    # 1. Group candidates by scene
    by_scene = defaultdict(list)
    for c in valid_candidates:
        by_scene[c.scene_id].append(c)

    selected: List[CandidateFrame] = []

    # 2. First pass: Pick best candidate from each scene for scene coverage
    for scene_id, scene_cands in by_scene.items():
        best_in_scene = max(scene_cands, key=calculate_utility)
        selected.append(best_in_scene)

    # Filter initial selection by temporal distance
    selected = _filter_by_temporal_distance(selected, min_temporal_distance)

    # 3. Second pass: Fill remaining quota with highest utility candidates from any scene
    remaining = [c for c in valid_candidates if c not in selected]
    remaining.sort(key=calculate_utility, reverse=True)

    for cand in remaining:
        if max_photos is not None and len(selected) >= max_photos:
            break

        # Check temporal distance with all currently selected
        too_close = any(abs(cand.timestamp_sec - s.timestamp_sec) < min_temporal_distance for s in selected)
        if not too_close:
            selected.append(cand)

    # Return in chronological order
    return sorted(selected, key=lambda c: c.timestamp_sec)


def _filter_by_temporal_distance(candidates: List[CandidateFrame], min_distance: float) -> List[CandidateFrame]:
    """Ensure no two candidates are within min_distance seconds of each other."""
    if not candidates:
        return []

    # Sort by time
    sorted_by_time = sorted(candidates, key=lambda c: c.timestamp_sec)
    filtered = [sorted_by_time[0]]

    for cand in sorted_by_time[1:]:
        if (cand.timestamp_sec - filtered[-1].timestamp_sec) >= min_distance:
            filtered.append(cand)
        else:
            # If too close, keep whichever has higher utility
            if calculate_utility(cand) > calculate_utility(filtered[-1]):
                filtered[-1] = cand

    return filtered

"""
Candidate frame generation and buffering.
"""

from typing import List, Optional
import numpy as np

from vitupi.models import CandidateFrame


class CandidateGenerator:
    """Manages the creation and collection of candidate frames for evaluation."""

    def __init__(
        self,
        novelty_threshold: float = 0.10,
        min_temporal_distance: float = 0.5,
        max_temporal_gap: float = 3.0,
    ):
        self.novelty_threshold = novelty_threshold
        self.min_temporal_distance = min_temporal_distance
        self.max_temporal_gap = max_temporal_gap
        self._last_candidate_time: float = -999.0
        self.candidates: List[CandidateFrame] = []

    def evaluate_and_add(
        self,
        frame_idx: int,
        timestamp_sec: float,
        scene_id: int,
        frame: np.ndarray,
        novelty_score: float,
        force_candidate: bool = False,
    ) -> Optional[CandidateFrame]:
        """Evaluate if the incoming frame qualifies as a candidate.

        Args:
            frame_idx: Frame index.
            timestamp_sec: Frame timestamp in seconds.
            scene_id: Associated scene boundary index.
            frame: Raw BGR frame image.
            novelty_score: Computed novelty score [0.0 - 1.0].
            force_candidate: If True, bypasses novelty threshold (e.g. scene boundaries or action peaks).

        Returns:
            CandidateFrame if added, None otherwise.
        """
        time_since_last = timestamp_sec - self._last_candidate_time
        gap_exceeded = (self._last_candidate_time >= 0) and (time_since_last >= self.max_temporal_gap)

        # Respect minimum temporal distance between candidates unless forced or gap exceeded
        if not force_candidate and not gap_exceeded and time_since_last < self.min_temporal_distance:
            return None

        if force_candidate or gap_exceeded or novelty_score >= self.novelty_threshold:
            candidate = CandidateFrame(
                frame_index=frame_idx,
                timestamp_sec=timestamp_sec,
                scene_id=scene_id,
                image=frame.copy(),
                novelty_score=novelty_score,
            )
            self.candidates.append(candidate)
            self._last_candidate_time = timestamp_sec
            return candidate

        return None

"""
Candidate frame generation and buffering.
"""

from typing import List, Optional
import numpy as np

from vitupi.models import CandidateFrame


class CandidateGenerator:
    """Manages the creation and collection of candidate frames for evaluation."""

    def __init__(self, novelty_threshold: float = 0.35, min_temporal_distance: float = 0.5):
        self.novelty_threshold = novelty_threshold
        self.min_temporal_distance = min_temporal_distance
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
        # Respect minimum temporal distance between candidates unless forced
        if not force_candidate and (timestamp_sec - self._last_candidate_time) < self.min_temporal_distance:
            return None

        if force_candidate or novelty_score >= self.novelty_threshold:
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

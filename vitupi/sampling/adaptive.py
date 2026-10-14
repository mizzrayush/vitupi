"""
Adaptive temporal sampling controller.
"""

from typing import Optional


class AdaptiveSampler:
    """Dynamically adjusts sampling frequency based on scene stability and visual events."""

    def __init__(self, base_fps: float = 1.0, dense_fps: float = 4.0, burst_duration_sec: float = 1.0):
        self.base_fps = base_fps
        self.dense_fps = dense_fps
        self.burst_duration_sec = burst_duration_sec
        self._burst_until_sec: float = -1.0
        self._last_sample_sec: float = -999.0

    def trigger_burst(self, current_time_sec: float) -> None:
        """Trigger dense temporal sampling starting now for burst_duration_sec."""
        self._burst_until_sec = max(self._burst_until_sec, current_time_sec + self.burst_duration_sec)

    def get_target_fps(self, current_time_sec: float) -> float:
        """Return the sampling rate (fps) to use for the current timestamp."""
        if current_time_sec <= self._burst_until_sec:
            return self.dense_fps
        return self.base_fps

    def should_sample_frame(self, frame_idx: int, source_fps: float, current_time_sec: float) -> bool:
        """Evaluate if the current timestamp should be processed given the adaptive rate."""
        target_fps = self.get_target_fps(current_time_sec)
        if target_fps <= 0:
            return False

        min_interval = 1.0 / target_fps
        if (current_time_sec - self._last_sample_sec) >= (min_interval - 1e-4):
            self._last_sample_sec = current_time_sec
            return True
        return False

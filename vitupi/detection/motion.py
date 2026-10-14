"""
Motion estimation and action-peak inflection detection.
"""

from typing import Optional, Tuple
import cv2
import numpy as np


class MotionAnalyzer:
    """Analyzes frame-to-frame motion magnitude and kinematic inflection points."""

    def __init__(self, target_dim: Tuple[int, int] = (160, 90)):
        self.target_dim = target_dim
        self._prev_gray: Optional[np.ndarray] = None
        self._prev_velocity: float = 0.0
        self._prev_accel: float = 0.0

    def reset(self) -> None:
        """Reset motion history."""
        self._prev_gray = None
        self._prev_velocity = 0.0
        self._prev_accel = 0.0

    def analyze_frame(self, frame: np.ndarray) -> Tuple[float, bool]:
        """Calculate average motion magnitude and detect whether this frame is an action peak.

        Returns:
            (motion_magnitude, is_peak_inflection)
        """
        small = cv2.resize(frame, self.target_dim)
        curr_gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        if self._prev_gray is None:
            self._prev_gray = curr_gray
            return 0.0, False

        # Compute dense optical flow on downscaled image for high speed
        flow = cv2.calcOpticalFlowFarneback(
            self._prev_gray, curr_gray, None, 0.5, 2, 9, 2, 5, 1.1, 0
        )
        magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        velocity = float(np.mean(magnitude))

        # Kinematic inflection: acceleration sign change (velocity peak or valley)
        acceleration = velocity - self._prev_velocity
        is_inflection = False

        # Peak of action: velocity was high and deceleration just began
        if self._prev_velocity > 1.5 and self._prev_accel > 0 and acceleration < 0:
            is_inflection = True

        self._prev_gray = curr_gray
        self._prev_accel = acceleration
        self._prev_velocity = velocity

        return velocity, is_inflection

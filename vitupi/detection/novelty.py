"""
Within-scene visual novelty detection module.
"""

from typing import Optional, Tuple
import cv2
import numpy as np


class VisualNoveltyDetector:
    """Evaluates within-scene visual novelty and composition changes."""

    def __init__(self, target_dim: Tuple[int, int] = (320, 180)):
        """Initialize novelty detector.

        Args:
            target_dim: Thumbnail dimension (w, h) for rapid signal computation.
        """
        self.target_dim = target_dim
        self._anchor_hsv_hist: Optional[np.ndarray] = None
        self._anchor_edges: Optional[np.ndarray] = None
        self._last_frame_gray: Optional[np.ndarray] = None

    def reset_anchor(self) -> None:
        """Reset scene reference anchor frame."""
        self._anchor_hsv_hist = None
        self._anchor_edges = None
        self._last_frame_gray = None

    def set_anchor(self, frame: np.ndarray) -> None:
        """Set a new reference anchor frame for cumulative scene novelty."""
        small = cv2.resize(frame, self.target_dim)
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        self._anchor_hsv_hist = self._calc_hsv_hist(hsv)

        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        self._anchor_edges = cv2.Canny(gray, 50, 150)
        self._last_frame_gray = gray

    def _calc_hsv_hist(self, hsv: np.ndarray) -> np.ndarray:
        """Calculate 2D Hue-Saturation normalized histogram."""
        hist = cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
        cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        return hist

    def compute_novelty(self, frame: np.ndarray) -> float:
        """Compute visual novelty score [0.0 to 1.0] for the incoming frame.

        Combines:
        1. Cumulative color distribution shift from scene anchor (handles pans & reveals).
        2. Edge structure novelty from scene anchor.
        3. Immediate frame-to-frame motion/luminance delta.
        """
        if self._anchor_hsv_hist is None or self._anchor_edges is None:
            self.set_anchor(frame)
            return 1.0  # First frame in scene has 100% novelty

        small = cv2.resize(frame, self.target_dim)
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        curr_hist = self._calc_hsv_hist(hsv)

        # 1. Color histogram correlation: 1.0 is identical, -1.0 is completely different
        hist_corr = cv2.compareHist(self._anchor_hsv_hist, curr_hist, cv2.HISTCMP_CORREL)
        # Map correlation [-1, 1] to distance [0, 1]
        color_distance = np.clip((1.0 - hist_corr) / 2.0, 0.0, 1.0)

        # 2. Edge structure difference
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        curr_edges = cv2.Canny(gray, 50, 150)
        edge_diff = np.mean(cv2.absdiff(self._anchor_edges, curr_edges)) / 255.0

        # 3. Short-term frame difference
        if self._last_frame_gray is not None:
            frame_delta = np.mean(cv2.absdiff(self._last_frame_gray, gray)) / 255.0
        else:
            frame_delta = 0.0
        self._last_frame_gray = gray

        # Weighted combination of cumulative novelty + short-term delta
        composite_novelty = (0.50 * color_distance) + (0.30 * edge_diff) + (0.20 * frame_delta)
        return float(np.clip(composite_novelty, 0.0, 1.0))

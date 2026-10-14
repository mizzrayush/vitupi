"""
Scene boundary and visual novelty detection algorithms.
"""

from vitupi.detection.scenes import detect_scenes
from vitupi.detection.novelty import VisualNoveltyDetector
from vitupi.detection.motion import MotionAnalyzer

__all__ = ["detect_scenes", "VisualNoveltyDetector", "MotionAnalyzer"]

"""
Configuration dataclasses and options for Vitupi extraction pipelines.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ExtractionMode(str, Enum):
    """Extraction density modes."""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    EXHAUSTIVE = "exhaustive"


class DomainPreset(str, Enum):
    """Domain-specific extraction presets."""
    DEFAULT = "default"
    SPORTS = "sports"
    SECURITY = "security"
    CANDID = "candid"


@dataclass
class VitupiConfig:
    """Master configuration for the Vitupi extraction pipeline."""

    # High-level controls
    mode: ExtractionMode = ExtractionMode.BALANCED
    preset: DomainPreset = DomainPreset.DEFAULT
    max_photos: Optional[int] = 100

    # Pipeline stages toggle
    scene_detection: bool = True
    adaptive_sampling: bool = True
    quality_scoring: bool = True
    duplicate_removal: bool = True
    generate_contact_sheet: bool = True
    generate_json_report: bool = True

    # Sampling parameters
    base_fps: float = 1.0          # Base coarse sampling rate (frames/sec)
    dense_fps: float = 4.0         # Burst/event sampling rate (frames/sec)
    min_temporal_distance: float = 0.5  # Min seconds between exported photos
    max_temporal_gap: float = 3.0       # Max seconds before forcing candidate in long shots

    # Thresholds
    novelty_threshold: float = 0.10      # Content change threshold (0.0 to 1.0)
    dedup_threshold: int = 10            # Max Hamming distance for pHash deduplication
    min_sharpness_score: float = 15.0    # Min Laplacian variance to consider

    # Scene boundary parameters
    scene_threshold: float = 27.0        # PySceneDetect content detector threshold

    # Presets / tuning options
    flattery_filter: bool = False        # Eye-blink / awkward expression rejection
    action_peak_detection: bool = False  # Kinematic inflection point detection
    motion_blur_penalty: float = 1.0     # Penalty multiplier for motion blur

    def __post_init__(self):
        # Convert strings to Enums if passed as strings
        if isinstance(self.mode, str):
            self.mode = ExtractionMode(self.mode.lower())
        if isinstance(self.preset, str):
            self.preset = DomainPreset(self.preset.lower())

        # Apply mode defaults
        if self.mode == ExtractionMode.CONSERVATIVE:
            self.novelty_threshold = max(self.novelty_threshold, 0.20)
            self.dedup_threshold = min(self.dedup_threshold, 14)  # Stricter dedup
            self.min_sharpness_score = max(self.min_sharpness_score, 25.0)
            self.base_fps = 0.5
            self.dense_fps = 2.0
            self.max_temporal_gap = 5.0
            if self.max_photos is None or self.max_photos > 30:
                self.max_photos = 30
        elif self.mode == ExtractionMode.EXHAUSTIVE:
            self.novelty_threshold = min(self.novelty_threshold, 0.05)
            self.dedup_threshold = max(self.dedup_threshold, 6)   # Looser dedup
            self.min_sharpness_score = min(self.min_sharpness_score, 8.0)
            self.base_fps = 2.0
            self.dense_fps = 8.0
            self.min_temporal_distance = 0.2
            self.max_temporal_gap = 1.5

        # Apply domain preset adjustments
        if self.preset == DomainPreset.SPORTS:
            self.action_peak_detection = True
            self.motion_blur_penalty = 1.5
            self.dense_fps = max(self.dense_fps, 6.0)
            self.min_temporal_distance = 0.15
            self.max_temporal_gap = 1.0
        elif self.preset == DomainPreset.SECURITY:
            self.base_fps = 0.2  # 1 frame every 5s for static CCTV
            self.dense_fps = 3.0
            self.novelty_threshold = 0.18
            self.min_temporal_distance = 1.0
            self.max_temporal_gap = 10.0
        elif self.preset == DomainPreset.CANDID:
            self.flattery_filter = True
            self.novelty_threshold = 0.06
            self.min_sharpness_score = max(self.min_sharpness_score, 18.0)
            self.min_temporal_distance = 0.75
            self.max_temporal_gap = 2.0
            self.dedup_threshold = 10

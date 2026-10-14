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
    PORTRAIT = "portrait"
    CUSTOM = "custom"


@dataclass
class VitupiConfig:
    """Master configuration for the Vitupi extraction pipeline."""

    # High-level controls
    mode: ExtractionMode = ExtractionMode.BALANCED
    preset: DomainPreset = DomainPreset.DEFAULT
    custom_name: Optional[str] = None
    max_photos: Optional[int] = 100

    # Pipeline stages toggle
    scene_detection: bool = True
    adaptive_sampling: bool = True
    quality_scoring: bool = True
    duplicate_removal: bool = True
    generate_contact_sheet: bool = True
    generate_json_report: bool = True

    # Sampling parameters (None = resolved from mode & preset)
    base_fps: Optional[float] = None
    dense_fps: Optional[float] = None
    min_temporal_distance: Optional[float] = None
    max_temporal_gap: Optional[float] = None

    # Thresholds (None = resolved from mode & preset)
    novelty_threshold: Optional[float] = None
    dedup_threshold: Optional[int] = None
    min_sharpness_score: Optional[float] = None
    scene_threshold: Optional[float] = None

    # Presets / tuning options (None = resolved from mode & preset)
    flattery_filter: Optional[bool] = None
    action_peak_detection: Optional[bool] = None
    motion_blur_penalty: Optional[float] = None

    def __post_init__(self):
        # Convert strings to Enums if passed as strings
        if isinstance(self.mode, str):
            self.mode = ExtractionMode(self.mode.lower())
        if isinstance(self.preset, str):
            try:
                self.preset = DomainPreset(self.preset.lower())
            except ValueError:
                self.custom_name = self.preset
                self.preset = DomainPreset.CUSTOM

        # 1. Base defaults for balanced mode
        def_base_fps = 1.0
        def_dense_fps = 4.0
        def_min_temp_dist = 0.5
        def_max_temp_gap = 3.0
        def_novelty_thresh = 0.10
        def_dedup_thresh = 6
        def_min_sharpness = 15.0
        def_scene_thresh = 27.0
        def_flattery = False
        def_action_peaks = False
        def_blur_penalty = 1.0

        # 2. Adjust defaults by Mode
        if self.mode == ExtractionMode.CONSERVATIVE:
            def_base_fps = 0.5
            def_dense_fps = 2.0
            def_novelty_thresh = 0.20
            def_dedup_thresh = 8
            def_min_sharpness = 25.0
            def_max_temp_gap = 5.0
            if self.max_photos is None or self.max_photos > 30:
                self.max_photos = 30
        elif self.mode == ExtractionMode.EXHAUSTIVE:
            def_base_fps = 2.0
            def_dense_fps = 8.0
            def_novelty_thresh = 0.04
            def_dedup_thresh = 4
            def_min_sharpness = 8.0
            def_min_temp_dist = 0.2
            def_max_temp_gap = 1.5

        # 3. Adjust defaults by Domain Preset
        if self.preset == DomainPreset.SPORTS:
            def_action_peaks = True
            def_blur_penalty = 1.5
            def_dense_fps = max(def_dense_fps, 6.0)
            def_min_temp_dist = 0.15
            def_max_temp_gap = 1.0
        elif self.preset == DomainPreset.SECURITY:
            def_base_fps = 0.2
            def_dense_fps = 3.0
            def_novelty_thresh = 0.18
            def_min_temp_dist = 1.0
            def_max_temp_gap = 10.0
        elif self.preset == DomainPreset.CANDID:
            def_flattery = True
            def_novelty_thresh = 0.05
            def_min_sharpness = max(def_min_sharpness, 18.0)
            def_min_temp_dist = 0.75
            def_max_temp_gap = 2.0
            def_dedup_thresh = 6
        elif self.preset == DomainPreset.PORTRAIT:
            def_flattery = True
            def_base_fps = 2.0
            def_dense_fps = 6.0
            def_novelty_thresh = 0.025
            def_min_sharpness = max(def_min_sharpness, 18.0)
            def_min_temp_dist = 0.4
            def_max_temp_gap = 1.0
            def_dedup_thresh = 6
        elif self.preset == DomainPreset.CUSTOM:
            def_flattery = True
            def_base_fps = 1.5
            def_dense_fps = 5.0
            def_novelty_thresh = 0.04
            def_min_sharpness = 16.0
            def_min_temp_dist = 0.4
            def_max_temp_gap = 1.5
            def_dedup_thresh = 6

        # 4. Fill in defaults ONLY if not explicitly provided by the caller
        if self.base_fps is None:
            self.base_fps = def_base_fps
        if self.dense_fps is None:
            self.dense_fps = def_dense_fps
        if self.min_temporal_distance is None:
            self.min_temporal_distance = def_min_temp_dist
        if self.max_temporal_gap is None:
            self.max_temporal_gap = def_max_temp_gap
        if self.novelty_threshold is None:
            self.novelty_threshold = def_novelty_thresh
        if self.dedup_threshold is None:
            self.dedup_threshold = def_dedup_thresh
        if self.min_sharpness_score is None:
            self.min_sharpness_score = def_min_sharpness
        if self.scene_threshold is None:
            self.scene_threshold = def_scene_thresh
        if self.flattery_filter is None:
            self.flattery_filter = def_flattery
        if self.action_peak_detection is None:
            self.action_peak_detection = def_action_peaks
        if self.motion_blur_penalty is None:
            self.motion_blur_penalty = def_blur_penalty

    def to_dict(self) -> dict:
        """Convert configuration to a clean, serializable dictionary."""
        return {
            "mode": self.mode.value if isinstance(self.mode, ExtractionMode) else str(self.mode),
            "preset": self.preset.value if isinstance(self.preset, DomainPreset) else str(self.preset),
            "custom_name": self.custom_name,
            "max_photos": self.max_photos,
            "scene_detection": self.scene_detection,
            "adaptive_sampling": self.adaptive_sampling,
            "quality_scoring": self.quality_scoring,
            "duplicate_removal": self.duplicate_removal,
            "generate_contact_sheet": self.generate_contact_sheet,
            "generate_json_report": self.generate_json_report,
            "base_fps": self.base_fps,
            "dense_fps": self.dense_fps,
            "min_temporal_distance": self.min_temporal_distance,
            "max_temporal_gap": self.max_temporal_gap,
            "novelty_threshold": self.novelty_threshold,
            "dedup_threshold": self.dedup_threshold,
            "min_sharpness_score": self.min_sharpness_score,
            "scene_threshold": self.scene_threshold,
            "flattery_filter": self.flattery_filter,
            "action_peak_detection": self.action_peak_detection,
            "motion_blur_penalty": self.motion_blur_penalty,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VitupiConfig":
        """Instantiate a VitupiConfig object from a dictionary."""
        clean = dict(data)
        mode = clean.pop("mode", "balanced")
        preset = clean.pop("preset", "custom")
        return cls(mode=mode, preset=preset, **clean)


def get_preset_defaults(
    preset: str | DomainPreset = DomainPreset.PORTRAIT,
    mode: str | ExtractionMode = ExtractionMode.BALANCED,
) -> VitupiConfig:
    """Return a fully resolved VitupiConfig for a given preset and mode."""
    return VitupiConfig(mode=mode, preset=preset)

"""
User-facing Python API for Vitupi.
"""

from typing import Optional, Union
from vitupi.config import DomainPreset, ExtractionMode, VitupiConfig
from vitupi.models import ExtractionResult
from vitupi.pipeline import ExtractionPipeline


def extract_photos(
    video_path: str,
    output_dir: str = "photos/",
    config: Optional[VitupiConfig] = None,
    mode: Union[str, ExtractionMode] = "balanced",
    preset: Union[str, DomainPreset] = "default",
    max_photos: Optional[int] = 100,
    base_fps: Optional[float] = None,
    dense_fps: Optional[float] = None,
    novelty_threshold: Optional[float] = None,
    min_sharpness_score: Optional[float] = None,
    min_temporal_distance: Optional[float] = None,
    max_temporal_gap: Optional[float] = None,
    dedup_threshold: Optional[int] = None,
    scene_threshold: Optional[float] = None,
    flattery_filter: Optional[bool] = None,
    action_peak_detection: Optional[bool] = None,
    preserve_scene_changes: bool = True,
    remove_duplicates: bool = True,
    prefer_sharp_frames: bool = True,
) -> ExtractionResult:
    """Extract visually distinct, high-quality photographs from a video.

    Args:
        video_path: Path to target video file (MP4, MOV, MKV, AVI, WebM).
        output_dir: Directory where chosen photographs and reports will be saved.
        config: Optional VitupiConfig instance. If omitted, constructed from other parameters.
        mode: Density mode: 'conservative', 'balanced', or 'exhaustive'.
        preset: Domain preset: 'default', 'sports', 'security', 'candid', 'portrait'.
        max_photos: Maximum number of photographs to export (None for unlimited).
        base_fps: Coarse sampling rate (frames/sec). Overrides preset/mode defaults.
        dense_fps: Burst/event sampling rate (frames/sec).
        novelty_threshold: Visual change sensitivity threshold [0.0 - 1.0]. Lower = more sensitive.
        min_sharpness_score: Minimum Laplacian variance to consider.
        min_temporal_distance: Minimum seconds between exported photos.
        max_temporal_gap: Maximum seconds in continuous shot before forcing candidate check.
        dedup_threshold: Max Hamming distance for pHash duplicate suppression within bursts.
        scene_threshold: PySceneDetect cut detection threshold.
        flattery_filter: Enable or disable facial/portrait flattery filter.
        action_peak_detection: Enable or disable kinematic action inflection detection.
        preserve_scene_changes: Whether to partition by scene cuts.
        remove_duplicates: Whether to suppress near-duplicate frames.
        prefer_sharp_frames: Whether to filter and rank by sharpness.

    Returns:
        ExtractionResult containing list of SelectedPhoto records and statistics.
    """
    if config is None:
        cfg = VitupiConfig(
            mode=ExtractionMode(mode) if isinstance(mode, str) else mode,
            preset=DomainPreset(preset) if isinstance(preset, str) else preset,
            max_photos=max_photos,
            base_fps=base_fps,
            dense_fps=dense_fps,
            novelty_threshold=novelty_threshold,
            min_sharpness_score=min_sharpness_score,
            min_temporal_distance=min_temporal_distance,
            max_temporal_gap=max_temporal_gap,
            dedup_threshold=dedup_threshold,
            scene_threshold=scene_threshold,
            flattery_filter=flattery_filter,
            action_peak_detection=action_peak_detection,
            scene_detection=preserve_scene_changes,
            duplicate_removal=remove_duplicates,
            quality_scoring=prefer_sharp_frames,
        )
    else:
        cfg = config

    pipeline = ExtractionPipeline(config=cfg)
    return pipeline.process(video_path=video_path, output_dir=output_dir)

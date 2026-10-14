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
        preset: Domain preset: 'default', 'sports', 'security', or 'candid'.
        max_photos: Maximum number of photographs to export (None for unlimited).
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
            scene_detection=preserve_scene_changes,
            duplicate_removal=remove_duplicates,
            quality_scoring=prefer_sharp_frames,
        )
    else:
        cfg = config

    pipeline = ExtractionPipeline(config=cfg)
    return pipeline.process(video_path=video_path, output_dir=output_dir)

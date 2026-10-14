"""
Vitupi (V2P) - Video to Photos
Intelligent, content-aware photograph extraction from videos.
"""

from vitupi.api import batch_extract_photos, extract_photos
from vitupi.config import DomainPreset, ExtractionMode, VitupiConfig
from vitupi.presets import PresetManager, get_preset_manager
from vitupi.exceptions import (
    ConfigurationError,
    ExtractionError,
    SceneDetectionError,
    VideoDecodingError,
    VideoMetadataError,
    VitupiError,
)
from vitupi.models import (
    CandidateFrame,
    ExtractionResult,
    ExtractionStatistics,
    SceneBoundary,
    SelectedPhoto,
    VideoMetadata,
)
from vitupi.benchmark import BenchmarkReport, run_benchmark

__version__ = "0.1.0"

__all__ = [
    "extract_photos",
    "batch_extract_photos",
    "run_benchmark",
    "BenchmarkReport",
    "VitupiConfig",
    "ExtractionMode",
    "DomainPreset",
    "PresetManager",
    "get_preset_manager",
    "ExtractionResult",
    "SelectedPhoto",
    "VideoMetadata",
    "CandidateFrame",
    "SceneBoundary",
    "ExtractionStatistics",
    "VitupiError",
    "VideoDecodingError",
    "VideoMetadataError",
    "SceneDetectionError",
    "ConfigurationError",
    "ExtractionError",
]

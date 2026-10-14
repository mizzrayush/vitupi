"""
Vitupi (V2P) - Video to Photos
Intelligent, content-aware photograph extraction from videos.
"""

from vitupi.api import extract_photos
from vitupi.config import DomainPreset, ExtractionMode, VitupiConfig
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

__version__ = "0.1.0"

__all__ = [
    "extract_photos",
    "VitupiConfig",
    "ExtractionMode",
    "DomainPreset",
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

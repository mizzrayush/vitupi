"""
Core data structures and representation models for Vitupi.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


@dataclass
class VideoMetadata:
    """Metadata extracted from a video source."""
    path: str
    width: int
    height: int
    fps: float
    total_frames: int
    duration_sec: float
    codec: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "width": self.width,
            "height": self.height,
            "fps": round(self.fps, 2),
            "total_frames": self.total_frames,
            "duration_sec": round(self.duration_sec, 2),
            "codec": self.codec,
        }


@dataclass
class SceneBoundary:
    """Represents a shot or scene segment."""
    scene_id: int
    start_frame: int
    end_frame: int
    start_time_sec: float
    end_time_sec: float


@dataclass
class CandidateFrame:
    """Candidate frame under evaluation with its quality and novelty metrics."""
    frame_index: int
    timestamp_sec: float
    scene_id: int
    image: np.ndarray  # BGR format from OpenCV
    sharpness_score: float = 0.0
    exposure_score: float = 0.0
    novelty_score: float = 0.0
    composite_quality: float = 0.0
    phash: Optional[int] = None
    is_rejected: bool = False
    rejection_reason: Optional[str] = None


@dataclass
class SelectedPhoto:
    """A final photograph chosen for export."""
    path: str
    timestamp_sec: float
    frame_index: int
    dimensions: Tuple[int, int]  # (width, height)
    quality_score: float
    novelty_score: float
    scene_id: int
    selection_reason: str = "visual_novelty"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "timestamp_sec": round(self.timestamp_sec, 3),
            "frame_index": self.frame_index,
            "dimensions": list(self.dimensions),
            "quality_score": round(self.quality_score, 2),
            "novelty_score": round(self.novelty_score, 2),
            "scene_id": self.scene_id,
            "selection_reason": self.selection_reason,
        }


@dataclass
class ExtractionStatistics:
    """Execution statistics for a completed extraction run."""
    total_frames_in_video: int = 0
    frames_decoded: int = 0
    scenes_detected: int = 0
    candidates_generated: int = 0
    duplicates_suppressed: int = 0
    low_quality_filtered: int = 0
    photos_exported: int = 0
    processing_time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_frames_in_video": self.total_frames_in_video,
            "frames_decoded": self.frames_decoded,
            "scenes_detected": self.scenes_detected,
            "candidates_generated": self.candidates_generated,
            "duplicates_suppressed": self.duplicates_suppressed,
            "low_quality_filtered": self.low_quality_filtered,
            "photos_exported": self.photos_exported,
            "processing_time_sec": round(self.processing_time_sec, 2),
        }


@dataclass
class ExtractionResult:
    """Master result object returned by extract_photos()."""
    source_video: str
    photos: List[SelectedPhoto]
    metadata: VideoMetadata
    statistics: ExtractionStatistics
    report_path: Optional[str] = None
    contact_sheet_path: Optional[str] = None

    @property
    def timestamps(self) -> List[float]:
        """Convenience accessor for all selected photo timestamps."""
        return [photo.timestamp_sec for photo in self.photos]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_video": self.source_video,
            "photo_count": len(self.photos),
            "metadata": self.metadata.to_dict(),
            "statistics": self.statistics.to_dict(),
            "report_path": self.report_path,
            "contact_sheet_path": self.contact_sheet_path,
            "photos": [p.to_dict() for p in self.photos],
        }

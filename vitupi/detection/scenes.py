"""
Scene transition and shot boundary detection using PySceneDetect.
"""

from typing import List
from scenedetect import detect, ContentDetector
from vitupi.exceptions import SceneDetectionError
from vitupi.models import SceneBoundary, VideoMetadata


def detect_scenes(video_path: str, metadata: VideoMetadata, threshold: float = 27.0) -> List[SceneBoundary]:
    """Detect shot cuts and scene transitions in the target video.

    Args:
        video_path: Path to the video file.
        metadata: Extracted VideoMetadata for the file.
        threshold: ContentDetector sensitivity threshold (default: 27.0).

    Returns:
        List of SceneBoundary instances. If no cuts are detected or the video
        is continuous, returns a single scene boundary covering the duration.
    """
    try:
        scene_list = detect(video_path, ContentDetector(threshold=threshold))
    except Exception as e:
        # Fallback to single scene if detection fails
        scene_list = []

    if not scene_list:
        # Single continuous scene
        return [
            SceneBoundary(
                scene_id=0,
                start_frame=0,
                end_frame=metadata.total_frames,
                start_time_sec=0.0,
                end_time_sec=metadata.duration_sec,
            )
        ]

    boundaries: List[SceneBoundary] = []
    for idx, (start_time, end_time) in enumerate(scene_list):
        boundaries.append(
            SceneBoundary(
                scene_id=idx,
                start_frame=start_time.frame_num,
                end_frame=end_time.frame_num,
                start_time_sec=start_time.seconds,
                end_time_sec=end_time.seconds,
            )
        )

    return boundaries

"""
Video metadata extraction module.
"""

import os
import cv2
from vitupi.exceptions import VideoDecodingError, VideoMetadataError
from vitupi.models import VideoMetadata


def extract_metadata(video_path: str) -> VideoMetadata:
    """Extract metadata from a video file.

    Args:
        video_path: Path to the target video file.

    Returns:
        VideoMetadata containing width, height, fps, total_frames, duration.

    Raises:
        VideoDecodingError: If the file does not exist or cannot be opened.
        VideoMetadataError: If metadata attributes are corrupt or missing.
    """
    if not os.path.exists(video_path):
        raise VideoDecodingError(f"Video file does not exist: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise VideoDecodingError(f"Failed to open video file with OpenCV: {video_path}")

    try:
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if fps <= 0.0:
            # Fallback for variable/missing frame rates
            fps = 24.0

        if total_frames <= 0:
            # If total_frames is unavailable, duration is estimated as 0
            duration_sec = 0.0
        else:
            duration_sec = total_frames / fps

        fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec = "".join([chr((fourcc_int >> 8 * i) & 0xFF) for i in range(4)]).strip()
        if not codec:
            codec = "unknown"

        return VideoMetadata(
            path=video_path,
            width=width,
            height=height,
            fps=fps,
            total_frames=total_frames,
            duration_sec=duration_sec,
            codec=codec,
        )
    except Exception as e:
        raise VideoMetadataError(f"Error parsing metadata for {video_path}: {e}") from e
    finally:
        cap.release()

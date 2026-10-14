"""
Memory-efficient video decoder using OpenCV.
"""

import os
from typing import Iterator, Optional, Tuple
import cv2
import numpy as np

from vitupi.exceptions import VideoDecodingError
from vitupi.models import VideoMetadata
from vitupi.video.metadata import extract_metadata


class VideoDecoder:
    """Streamlined, memory-bounded video decoder for frame extraction."""

    def __init__(self, video_path: str):
        self.video_path = video_path
        if not os.path.exists(video_path):
            raise VideoDecodingError(f"Video file not found: {video_path}")

        self._metadata: Optional[VideoMetadata] = None
        self._cap: Optional[cv2.VideoCapture] = None

    def __enter__(self) -> "VideoDecoder":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self) -> None:
        """Open the video stream."""
        if self._cap is None or not self._cap.isOpened():
            self._cap = cv2.VideoCapture(self.video_path)
            if not self._cap.isOpened():
                raise VideoDecodingError(f"Could not open video file: {self.video_path}")
            self._metadata = extract_metadata(self.video_path)

    def close(self) -> None:
        """Release video resources."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    @property
    def metadata(self) -> VideoMetadata:
        """Return cached video metadata."""
        if self._metadata is None:
            self._metadata = extract_metadata(self.video_path)
        return self._metadata

    def read_frame_at_index(self, frame_index: int) -> Optional[np.ndarray]:
        """Read a single frame at the specified index."""
        self.open()
        assert self._cap is not None

        # Check bounds
        if frame_index < 0:
            return None
        if self.metadata.total_frames > 0 and frame_index >= self.metadata.total_frames:
            return None

        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = self._cap.read()
        if not ret or frame is None:
            return None
        return frame

    def read_frame_at_timestamp(self, timestamp_sec: float) -> Optional[Tuple[int, np.ndarray]]:
        """Read a frame nearest to the given timestamp in seconds."""
        fps = self.metadata.fps
        target_frame = int(round(timestamp_sec * fps))
        frame = self.read_frame_at_index(target_frame)
        if frame is None:
            return None
        return target_frame, frame

    def stream_sampled_frames(self, target_fps: float) -> Iterator[Tuple[int, float, np.ndarray]]:
        """Generator yielding (frame_index, timestamp_sec, frame) sampled at target_fps.

        Iterates sequentially to maximize decoder throughput and avoid slow arbitrary seeks.
        """
        self.open()
        assert self._cap is not None

        source_fps = self.metadata.fps
        if target_fps <= 0 or target_fps >= source_fps:
            # Yield every frame
            frame_step = 1
        else:
            frame_step = max(1, int(round(source_fps / target_fps)))

        self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        current_frame_idx = 0

        while True:
            ret, frame = self._cap.read()
            if not ret or frame is None:
                break

            if current_frame_idx % frame_step == 0:
                timestamp_sec = current_frame_idx / source_fps
                yield current_frame_idx, timestamp_sec, frame

            current_frame_idx += 1

import os
import shutil
import tempfile
import cv2
import numpy as np
import pytest

from vitupi.api import extract_photos
from vitupi.config import VitupiConfig, ExtractionMode, DomainPreset
from vitupi.video.metadata import extract_metadata


def create_synthetic_video(file_path: str, fps: float = 24.0, num_frames: int = 72) -> None:
    """Create a synthetic video with 3 distinct scenes:
    - Frames 0..23 (1 sec): Blue background with static circle
    - Frames 24..47 (1 sec): Blue background with moving circle (novelty / action)
    - Frames 48..71 (1 sec): Hard cut to Yellow background with a rectangle
    """
    width, height = 320, 240
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(file_path, fourcc, fps, (width, height))

    for idx in range(num_frames):
        if idx < 24:
            # Scene 1: Static blue screen
            frame = np.full((height, width, 3), (180, 50, 20), dtype=np.uint8)
            cv2.circle(frame, (100, 100), 30, (255, 255, 255), -1)
        elif idx < 48:
            # Scene 1 continuing with motion / novelty
            frame = np.full((height, width, 3), (180, 50, 20), dtype=np.uint8)
            # Circle moves across the screen
            x = int(100 + (idx - 24) * 6)
            cv2.circle(frame, (x, 100), 30, (255, 255, 255), -1)
        else:
            # Scene 2: Hard cut to Yellow screen with dark rectangle
            frame = np.full((height, width, 3), (20, 200, 220), dtype=np.uint8)
            cv2.rectangle(frame, (50, 50), (270, 190), (40, 40, 40), -1)
            cv2.putText(frame, "Scene 2", (80, 130), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        out.write(frame)

    out.release()


def test_metadata_extraction(tmp_path):
    video_path = str(tmp_path / "test_meta.mp4")
    create_synthetic_video(video_path, fps=24.0, num_frames=48)

    meta = extract_metadata(video_path)
    assert meta.width == 320
    assert meta.height == 240
    assert meta.fps == 24.0
    assert meta.total_frames == 48
    assert abs(meta.duration_sec - 2.0) < 0.1


def test_end_to_end_extraction(tmp_path):
    video_path = str(tmp_path / "test_extract.mp4")
    out_dir = str(tmp_path / "photos_out")
    create_synthetic_video(video_path, fps=24.0, num_frames=72)

    config = VitupiConfig(
        mode=ExtractionMode.BALANCED,
        preset=DomainPreset.DEFAULT,
        min_sharpness_score=5.0,  # Synthetic shapes have crisp edges
        max_photos=10,
    )

    result = extract_photos(video_path, output_dir=out_dir, config=config)

    assert len(result.photos) > 0
    assert os.path.exists(out_dir)
    assert result.report_path is not None
    assert os.path.exists(result.report_path)

    # Verify photos are saved and readable
    for photo in result.photos:
        assert os.path.exists(photo.path)
        img = cv2.imread(photo.path)
        assert img is not None
        assert img.shape == (240, 320, 3)

    # Verify contact sheet exists
    if result.contact_sheet_path:
        assert os.path.exists(result.contact_sheet_path)


def test_sports_preset(tmp_path):
    video_path = str(tmp_path / "test_sports.mp4")
    out_dir = str(tmp_path / "photos_sports")
    create_synthetic_video(video_path, fps=24.0, num_frames=72)

    config = VitupiConfig(
        mode=ExtractionMode.BALANCED,
        preset=DomainPreset.SPORTS,
        min_sharpness_score=5.0,
    )

    result = extract_photos(video_path, output_dir=out_dir, config=config)
    assert len(result.photos) > 0
    assert result.statistics.photos_exported == len(result.photos)

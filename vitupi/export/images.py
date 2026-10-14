"""
Photograph image export utilities.
"""

import os
from typing import List, Tuple
import cv2

from vitupi.models import CandidateFrame, SelectedPhoto


def format_timestamp(timestamp_sec: float) -> str:
    """Format seconds into HH-MM-SS-mmm string."""
    hours = int(timestamp_sec // 3600)
    minutes = int((timestamp_sec % 3600) // 60)
    seconds = int(timestamp_sec % 60)
    milliseconds = int((timestamp_sec - int(timestamp_sec)) * 1000)
    return f"{hours:02d}-{minutes:02d}-{seconds:02d}-{milliseconds:03d}"


def export_photos(
    candidates: List[CandidateFrame],
    output_dir: str,
    format_ext: str = "jpg",
    quality: int = 95,
) -> List[SelectedPhoto]:
    """Export selected candidate frames to the specified directory.

    Args:
        candidates: List of chosen CandidateFrame objects.
        output_dir: Destination folder.
        format_ext: Image extension ("jpg" or "png").
        quality: JPEG export quality (default: 95).

    Returns:
        List of SelectedPhoto metadata records.
    """
    os.makedirs(output_dir, exist_ok=True)
    selected_photos: List[SelectedPhoto] = []

    encode_params = []
    if format_ext.lower() in ("jpg", "jpeg"):
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    elif format_ext.lower() == "png":
        encode_params = [int(cv2.IMWRITE_PNG_COMPRESSION), 4]

    for idx, cand in enumerate(candidates, start=1):
        time_str = format_timestamp(cand.timestamp_sec)
        filename = f"frame_{idx:06d}_{time_str}.{format_ext}"
        out_path = os.path.join(output_dir, filename)

        cv2.imwrite(out_path, cand.image, encode_params)

        h, w = cand.image.shape[:2]
        selected_photos.append(
            SelectedPhoto(
                path=out_path,
                timestamp_sec=cand.timestamp_sec,
                frame_index=cand.frame_index,
                dimensions=(w, h),
                quality_score=cand.composite_quality,
                novelty_score=cand.novelty_score,
                scene_id=cand.scene_id,
            )
        )

    return selected_photos

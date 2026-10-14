"""
Contact sheet visual overview generator.
"""

import math
import os
from typing import List, Optional
import cv2
import numpy as np

from vitupi.export.images import format_timestamp
from vitupi.models import SelectedPhoto


def generate_contact_sheet(
    photos: List[SelectedPhoto],
    output_dir: str,
    filename: str = "contact_sheet.jpg",
    cols: int = 4,
    thumb_width: int = 320,
) -> Optional[str]:
    """Create a contact sheet grid summarizing all exported photographs."""
    if not photos:
        return None

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, filename)

    num_photos = len(photos)
    cols = min(cols, num_photos)
    rows = math.ceil(num_photos / cols)

    # Read first image to determine aspect ratio
    first_img = cv2.imread(photos[0].path)
    if first_img is None:
        return None

    orig_h, orig_w = first_img.shape[:2]
    aspect = orig_h / orig_w
    thumb_height = int(thumb_width * aspect)
    label_height = 24
    tile_height = thumb_height + label_height

    # Canvas
    grid = np.zeros((rows * tile_height, cols * thumb_width, 3), dtype=np.uint8)

    for idx, photo in enumerate(photos):
        r = idx // cols
        c = idx % cols

        img = cv2.imread(photo.path)
        if img is None:
            continue

        thumb = cv2.resize(img, (thumb_width, thumb_height))

        # Position tile
        y_start = r * tile_height
        x_start = c * thumb_width

        # Place image
        grid[y_start : y_start + thumb_height, x_start : x_start + thumb_width] = thumb

        # Draw label background and text
        time_text = format_timestamp(photo.timestamp_sec)
        label_text = f"#{idx+1} {time_text}"
        cv2.rectangle(
            grid,
            (x_start, y_start + thumb_height),
            (x_start + thumb_width, y_start + tile_height),
            (30, 30, 30),
            -1,
        )
        cv2.putText(
            grid,
            label_text,
            (x_start + 8, y_start + thumb_height + 17),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (220, 220, 220),
            1,
            cv2.LINE_AA,
        )

    cv2.imwrite(out_path, grid, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    return out_path

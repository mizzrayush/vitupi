"""
Sharpness and focus estimation using Laplacian variance and gradient energy.
"""

import cv2
import numpy as np


def compute_sharpness_score(image: np.ndarray) -> float:
    """Compute photographic sharpness score based on Laplacian variance.

    Higher values correspond to sharper, crisper edges.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance = float(laplacian.var())

    return max(0.0, variance)

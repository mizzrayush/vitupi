"""
Exposure and clipping evaluation.
"""

import cv2
import numpy as np


def compute_exposure_score(image: np.ndarray) -> float:
    """Compute exposure usability score in range [0.0 to 1.0].

    Penalizes extreme underexposure (shadow crush) and overexposure (blown highlights).
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    total_pixels = gray.size
    if total_pixels == 0:
        return 0.0

    # Fractions of clipped pixels
    underexposed_frac = np.sum(gray <= 5) / total_pixels
    overexposed_frac = np.sum(gray >= 250) / total_pixels

    # Mean luminance penalty (ideal mean luminance is ~100-155)
    mean_lum = np.mean(gray)
    lum_deviation = abs(mean_lum - 128.0) / 128.0  # [0.0 to 1.0]

    # Combine metrics: 1.0 = balanced exposure, 0.0 = severe crush/blowout
    exposure_quality = 1.0 - (0.4 * underexposed_frac + 0.4 * overexposed_frac + 0.2 * lum_deviation)
    return float(np.clip(exposure_quality, 0.0, 1.0))

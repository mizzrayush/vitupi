"""
Composite photographic quality scoring combining sharpness, exposure, and filters.
"""

import cv2
import numpy as np
from vitupi.config import VitupiConfig
from vitupi.models import CandidateFrame
from vitupi.scoring.exposure import compute_exposure_score
from vitupi.scoring.sharpness import compute_sharpness_score


def score_candidate(candidate: CandidateFrame, config: VitupiConfig) -> None:
    """Evaluate and assign photographic quality scores to candidate frame in-place."""
    raw_sharpness = compute_sharpness_score(candidate.image)
    candidate.sharpness_score = raw_sharpness

    exposure_score = compute_exposure_score(candidate.image)
    candidate.exposure_score = exposure_score

    # Check minimum sharpness threshold
    if raw_sharpness < config.min_sharpness_score:
        candidate.is_rejected = True
        candidate.rejection_reason = f"Low sharpness ({raw_sharpness:.1f} < {config.min_sharpness_score:.1f})"
        candidate.composite_quality = 0.0
        return

    # Normalization: logarithmic scaling maps wide-range Laplacian variance [0 to 2000+] to [0.0, 1.0]
    normalized_sharpness = float(np.clip(np.log1p(raw_sharpness) / 7.0, 0.0, 1.0))

    # Base composite formula: 65% normalized sharpness, 35% exposure balance
    composite = (0.65 * normalized_sharpness) + (0.35 * exposure_score)

    # Flattery filter: prioritize facial & portrait sharpness for candid presets
    if config.flattery_filter:
        h, w = candidate.image.shape[:2]
        # Focus on upper/center 65% where subjects and faces typically appear
        portrait_zone = candidate.image[int(h * 0.1):int(h * 0.75), int(w * 0.15):int(w * 0.85)]
        if portrait_zone.size > 0:
            ycrcb = cv2.cvtColor(portrait_zone, cv2.COLOR_BGR2YCrCb)
            # Standard skin tone range across human skin tones
            skin_mask = cv2.inRange(ycrcb, (0, 133, 77), (255, 173, 127))
            skin_ratio = np.count_nonzero(skin_mask) / skin_mask.size

            if skin_ratio > 0.02:
                # Subject/skin detected: compute focused portrait sharpness
                portrait_sharpness = compute_sharpness_score(portrait_zone)
                norm_portrait_sharpness = float(np.clip(np.log1p(portrait_sharpness) / 7.0, 0.0, 1.0))
                # Boost composite quality based on facial/subject clarity
                composite = (0.50 * composite) + (0.50 * norm_portrait_sharpness)

    candidate.composite_quality = float(np.clip(composite, 0.0, 1.0))

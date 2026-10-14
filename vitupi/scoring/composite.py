"""
Composite photographic quality scoring combining sharpness, exposure, and filters.
"""

import cv2
import numpy as np
from vitupi.config import VitupiConfig
from vitupi.models import CandidateFrame
from vitupi.scoring.exposure import compute_exposure_score
from vitupi.scoring.faces import analyze_facial_flattery
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

    # Motion blur penalty
    if config.motion_blur_penalty is not None and config.motion_blur_penalty > 1.0:
        # If frame sharpness is marginal relative to base threshold, apply motion blur penalty
        if raw_sharpness < (config.min_sharpness_score * 1.5):
            penalty_factor = 1.0 / float(config.motion_blur_penalty)
            composite *= penalty_factor

    # Flattery filter: analyze faces, eye-blink suppression, and expression
    if config.flattery_filter:
        face_analysis = analyze_facial_flattery(candidate.image)
        if face_analysis.faces_detected > 0:
            if face_analysis.is_blinking:
                # Penalize closed eyes / mid-blink
                composite *= 0.35
            else:
                # Boost open-eyed flattering portrait frames
                composite = (0.60 * composite) + (0.40 * face_analysis.composite_face_score)

    candidate.composite_quality = float(np.clip(composite, 0.0, 1.0))

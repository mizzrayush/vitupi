"""
Composite photographic quality scoring combining sharpness, exposure, and filters.
"""

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

    # Composite formula: 65% normalized sharpness, 35% exposure balance
    composite = (0.65 * normalized_sharpness) + (0.35 * exposure_score)
    candidate.composite_quality = float(np.clip(composite, 0.0, 1.0))

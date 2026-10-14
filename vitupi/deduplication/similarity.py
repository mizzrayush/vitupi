"""
Candidate deduplication and redundancy suppression.
"""

from typing import List, Tuple
from vitupi.deduplication.hashing import compute_phash, hamming_distance
from vitupi.models import CandidateFrame


def suppress_near_duplicates(
    candidates: List[CandidateFrame],
    threshold: int = 6,
    burst_window_sec: float = 5.0,
) -> Tuple[List[CandidateFrame], int]:
    """Identify and mark redundant candidate frames using perceptual hash comparisons.

    When two frames have Hamming distance <= threshold within a temporal burst window,
    the one with higher composite quality is preserved, while the other is rejected.
    Outside the temporal window, only near-exact matches (dist <= 3) are suppressed to prevent
    distant moments with similar background horizons from being falsely discarded.

    Args:
        candidates: List of CandidateFrame objects.
        threshold: Max Hamming distance within a temporal burst (default: 6).
        burst_window_sec: Maximum time delta in seconds to consider two frames part of the same moment.

    Returns:
        (filtered_candidates, duplicates_suppressed_count)
    """
    # Precompute hashes for active candidates
    for candidate in candidates:
        if not candidate.is_rejected and candidate.phash is None:
            candidate.phash = compute_phash(candidate.image)

    suppressed_count = 0
    accepted: List[CandidateFrame] = []

    for candidate in candidates:
        if candidate.is_rejected:
            continue

        assert candidate.phash is not None
        is_duplicate = False

        for existing in accepted:
            assert existing.phash is not None
            dist = hamming_distance(candidate.phash, existing.phash)
            time_delta = abs(candidate.timestamp_sec - existing.timestamp_sec)

            # Within a localized burst, use standard threshold. Outside burst, only suppress exact duplicates.
            effective_threshold = threshold if time_delta <= burst_window_sec else min(threshold, 3)

            if dist <= effective_threshold:
                is_duplicate = True
                # If current candidate has noticeably higher quality, swap them
                if candidate.composite_quality > (existing.composite_quality + 0.1):
                    existing.is_rejected = True
                    existing.rejection_reason = f"Replaced by higher-quality duplicate (dist={dist})"
                    accepted.remove(existing)
                    accepted.append(candidate)
                else:
                    candidate.is_rejected = True
                    candidate.rejection_reason = f"Duplicate of frame {existing.frame_index} (dist={dist})"
                suppressed_count += 1
                break

        if not is_duplicate:
            accepted.append(candidate)

    return accepted, suppressed_count

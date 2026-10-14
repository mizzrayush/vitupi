"""
Discrete Cosine Transform (DCT) based perceptual hashing (pHash).
"""

import cv2
import numpy as np


def compute_phash(image: np.ndarray) -> int:
    """Compute 64-bit DCT perceptual hash for an image.

    Args:
        image: BGR or grayscale image array.

    Returns:
        64-bit integer perceptual hash.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # 1. Resize to 32x32 for frequency decomposition
    resized = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA)

    # 2. Compute 2D DCT
    dct = cv2.dct(np.float32(resized))

    # 3. Extract top-left 8x8 lowest frequencies (excluding DC term at [0, 0])
    dct_low = dct[0:8, 0:8].flatten()
    median_val = float(np.median(dct_low[1:]))

    # 4. Construct 64-bit integer mask
    bit_array = dct_low > median_val
    phash = 0
    for bit in bit_array:
        phash = (phash << 1) | int(bit)

    return phash


def hamming_distance(hash1: int, hash2: int) -> int:
    """Calculate the bit-level Hamming distance between two 64-bit hashes."""
    xor = hash1 ^ hash2
    # int.bit_count() is native in Python 3.10+
    return xor.bit_count()

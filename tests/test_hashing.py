import numpy as np
import pytest
from vitupi.deduplication.hashing import compute_phash, hamming_distance


def test_phash_identical_images():
    # Identical images must produce identical hashes (Hamming distance == 0)
    img = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    h1 = compute_phash(img)
    h2 = compute_phash(img.copy())
    assert h1 == h2
    assert hamming_distance(h1, h2) == 0


def test_phash_near_identical_images():
    # Slight brightness shift should have small Hamming distance (<= 5)
    img = np.full((120, 120, 3), 128, dtype=np.uint8)
    # Add circle
    import cv2
    cv2.circle(img, (60, 60), 30, (255, 0, 0), -1)

    img_slightly_brighter = np.clip(img.astype(np.int16) + 5, 0, 255).astype(np.uint8)

    h1 = compute_phash(img)
    h2 = compute_phash(img_slightly_brighter)
    assert hamming_distance(h1, h2) <= 5


def test_phash_completely_different_images():
    # Completely different patterns should have high Hamming distance
    img1 = np.zeros((100, 100, 3), dtype=np.uint8)
    img2 = np.zeros((100, 100, 3), dtype=np.uint8)

    import cv2
    cv2.rectangle(img1, (0, 0), (50, 100), (255, 255, 255), -1)
    cv2.circle(img2, (50, 50), 40, (255, 255, 255), -1)

    h1 = compute_phash(img1)
    h2 = compute_phash(img2)
    assert hamming_distance(h1, h2) > 10

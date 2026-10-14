"""
Unit tests for facial analysis, eye-blink detection, and flattery scoring.
"""

import cv2
import numpy as np
import pytest
from vitupi.scoring.faces import (
    FaceAnalysisResult,
    analyze_facial_flattery,
    evaluate_eye_openness,
    evaluate_mouth_flattery,
    extract_face_regions_skin,
)


def _create_synthetic_face_image() -> np.ndarray:
    """Generate a synthetic 200x200 portrait image with a skin-tone face, eyes, and mouth."""
    img = np.full((200, 200, 3), (40, 40, 40), dtype=np.uint8)  # Dark background
    # Skin color in BGR (roughly corresponds to YCrCb skin region)
    skin_bgr = (150, 180, 230)
    cv2.ellipse(img, (100, 100), (45, 60), 0, 0, 360, skin_bgr, -1)

    # Eyes (open eyes with white sclera and dark pupils)
    cv2.ellipse(img, (80, 85), (10, 6), 0, 0, 360, (255, 255, 255), -1)
    cv2.circle(img, (80, 85), 3, (20, 20, 20), -1)

    cv2.ellipse(img, (120, 85), (10, 6), 0, 0, 360, (255, 255, 255), -1)
    cv2.circle(img, (120, 85), 3, (20, 20, 20), -1)

    # Gentle smile mouth
    cv2.ellipse(img, (100, 130), (18, 8), 0, 0, 180, (50, 50, 180), -1)

    return img


def test_face_detection_synthetic():
    face_img = _create_synthetic_face_image()
    boxes = extract_face_regions_skin(face_img)
    assert len(boxes) >= 1

    x, y, w, h = boxes[0]
    assert 20 <= x <= 120
    assert 20 <= y <= 120
    assert w > 20 and h > 20


def test_analyze_facial_flattery_positive():
    face_img = _create_synthetic_face_image()
    analysis = analyze_facial_flattery(face_img)

    assert isinstance(analysis, FaceAnalysisResult)
    assert analysis.faces_detected >= 1
    assert analysis.avg_eye_openness > 0.0
    assert not analysis.is_blinking
    assert analysis.composite_face_score > 0.2


def test_eye_openness_vs_closed():
    # Face crop with open eyes (sclera + dark iris)
    open_face = np.full((120, 100, 3), (150, 180, 230), dtype=np.uint8)
    cv2.ellipse(open_face, (35, 45), (10, 6), 0, 0, 360, (255, 255, 255), -1)
    cv2.circle(open_face, (35, 45), 3, (20, 20, 20), -1)
    cv2.ellipse(open_face, (65, 45), (10, 6), 0, 0, 360, (255, 255, 255), -1)
    cv2.circle(open_face, (65, 45), 3, (20, 20, 20), -1)

    # Face crop with closed eyelids (flat skin tone)
    closed_face = np.full((120, 100, 3), (150, 180, 230), dtype=np.uint8)

    open_score = evaluate_eye_openness(open_face)
    closed_score = evaluate_eye_openness(closed_face)
    assert open_score > closed_score
    assert closed_score <= 0.25


def test_empty_or_no_face_frame():
    blank = np.zeros((100, 100, 3), dtype=np.uint8)
    res = analyze_facial_flattery(blank)
    assert res.faces_detected == 0
    assert res.composite_face_score == 1.0  # Neutral fallback

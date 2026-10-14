import cv2
import numpy as np
import pytest
from vitupi.scoring.sharpness import compute_sharpness_score
from vitupi.scoring.exposure import compute_exposure_score


def test_sharpness_distinction():
    # Sharp image with crisp high contrast edges vs blurred image
    sharp = np.zeros((100, 100, 3), dtype=np.uint8)
    for i in range(0, 100, 10):
        cv2.line(sharp, (i, 0), (i, 100), (255, 255, 255), 2)

    blurred = cv2.GaussianBlur(sharp, (15, 15), 0)

    score_sharp = compute_sharpness_score(sharp)
    score_blurred = compute_sharpness_score(blurred)

    assert score_sharp > score_blurred * 2.0


def test_exposure_scoring():
    # Balanced midtones vs completely black (blown shadow) or white (blown highlight)
    balanced = np.full((100, 100, 3), 128, dtype=np.uint8)
    blown_black = np.zeros((100, 100, 3), dtype=np.uint8)
    blown_white = np.full((100, 100, 3), 255, dtype=np.uint8)

    score_balanced = compute_exposure_score(balanced)
    score_black = compute_exposure_score(blown_black)
    score_white = compute_exposure_score(blown_white)

    assert score_balanced > score_black
    assert score_balanced > score_white

"""
Facial flattery, expression analysis, and eye-blink detection.
Detects faces, evaluates eye openness (blink suppression), mouth flattery,
and computes localized facial sharpness without external heavy dependencies.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import cv2
import numpy as np


@dataclass
class FaceAnalysisResult:
    """Detailed facial flattery and expression metrics for a candidate frame."""
    faces_detected: int = 0
    face_boxes: List[Tuple[int, int, int, int]] = field(default_factory=list)
    avg_eye_openness: float = 1.0
    is_blinking: bool = False
    facial_sharpness: float = 0.0
    expression_flattery: float = 1.0
    composite_face_score: float = 1.0


def extract_face_regions_skin(frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """
    Detect probable human face bounding boxes using YCrCb & HSV skin-tone modeling
    combined with facial anthropometry (aspect ratio, size, symmetry).
    """
    h, w = frame.shape[:2]
    if h < 64 or w < 64:
        return []

    # Convert to YCrCb (robust against luminance variations)
    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    # Standard human skin color range in Cr-Cb space
    lower_skin = np.array([0, 133, 77], dtype=np.uint8)
    upper_skin = np.array([255, 173, 127], dtype=np.uint8)
    mask = cv2.inRange(ycrcb, lower_skin, upper_skin)

    # Morphological opening and closing to remove noise and fill holes
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    face_boxes = []

    min_area = (h * w) * 0.005  # At least 0.5% of the total frame
    max_area = (h * w) * 0.70   # At most 70% of the total frame

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            continue

        x, y, bw, bh = cv2.boundingRect(cnt)
        aspect = bh / float(bw) if bw > 0 else 0

        # Human faces typically have an aspect ratio between 1.0 and 1.8
        if 0.9 <= aspect <= 2.2:
            face_boxes.append((x, y, bw, bh))

    # Keep top 5 largest detected faces sorted by area descending
    face_boxes.sort(key=lambda b: b[2] * b[3], reverse=True)
    return face_boxes[:5]


def evaluate_eye_openness(face_crop: np.ndarray) -> float:
    """
    Evaluate eye-openness in the upper eye-band of a detected face.
    Open eyes exhibit high local gradient contrast (dark iris/pupil against white sclera).
    Closed eyes (blinking) show flat skin texture with low vertical edge variance.
    Returns openness score in [0.0, 1.0]. Values < 0.25 indicate a blink.
    """
    fh, fw = face_crop.shape[:2]
    if fh < 20 or fw < 20:
        return 1.0

    # Upper eye band is typically located between 20% and 48% of face height
    y1, y2 = int(fh * 0.20), int(fh * 0.48)
    x1, x2 = int(fw * 0.12), int(fw * 0.88)
    eye_band = face_crop[y1:y2, x1:x2]

    if eye_band.size == 0:
        return 1.0

    gray = cv2.cvtColor(eye_band, cv2.COLOR_BGR2GRAY) if eye_band.ndim == 3 else eye_band
    # Compute vertical gradient (Sobel Y detects horizontal eyelid edges and pupil boundaries)
    sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_std = float(np.std(sobel_y))

    # Calibrated mapping: std below 12 indicates flat/closed eyelids; > 25 indicates crisp open eye
    openness = np.clip((grad_std - 10.0) / 25.0, 0.05, 1.0)
    return float(openness)


def evaluate_mouth_flattery(face_crop: np.ndarray) -> float:
    """
    Evaluate mouth expression flattery in the lower third of the face.
    Penalizes awkward mid-speech open-mouth contortions.
    Returns flattery score in [0.0, 1.0].
    """
    fh, fw = face_crop.shape[:2]
    if fh < 20 or fw < 20:
        return 1.0

    # Lower third mouth region
    y1, y2 = int(fh * 0.65), int(fh * 0.95)
    x1, x2 = int(fw * 0.20), int(fw * 0.80)
    mouth_region = face_crop[y1:y2, x1:x2]

    if mouth_region.size == 0:
        return 1.0

    gray = cv2.cvtColor(mouth_region, cv2.COLOR_BGR2GRAY) if mouth_region.ndim == 3 else mouth_region
    # Binarize cavity
    _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
    cavity_pixels = np.sum(thresh > 0)
    total_pixels = thresh.size

    cavity_ratio = cavity_pixels / float(total_pixels) if total_pixels > 0 else 0
    # Moderate smile/neutral cavity is small; wide yawning/speech cavity is large (> 0.35)
    if cavity_ratio > 0.40:
        return 0.45
    elif cavity_ratio > 0.25:
        return 0.75
    return 1.0


def analyze_facial_flattery(frame: np.ndarray) -> FaceAnalysisResult:
    """
    Perform complete face analysis: detect face bounding boxes, evaluate eye openness,
    detect blinking, compute localized facial sharpness, and determine composite flattery.
    """
    if frame is None or frame.size == 0:
        return FaceAnalysisResult()

    face_boxes = extract_face_regions_skin(frame)
    if not face_boxes:
        # No clear face found; return neutral score
        return FaceAnalysisResult(faces_detected=0, composite_face_score=1.0)

    openness_scores = []
    flattery_scores = []
    sharpness_scores = []

    gray_full = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    for (x, y, bw, bh) in face_boxes:
        face_crop = frame[y:y+bh, x:x+bw]
        face_gray = gray_full[y:y+bh, x:x+bw]

        # 1. Localized facial sharpness (Laplacian variance on face crop)
        lap_var = float(cv2.Laplacian(face_gray, cv2.CV_64F).var())
        sharpness_scores.append(lap_var)

        # 2. Eye openness
        eye_open = evaluate_eye_openness(face_crop)
        openness_scores.append(eye_open)

        # 3. Mouth flattery
        mouth_flat = evaluate_mouth_flattery(face_crop)
        flattery_scores.append(mouth_flat)

    avg_openness = float(np.mean(openness_scores))
    avg_flattery = float(np.mean(flattery_scores))
    avg_sharpness = float(np.mean(sharpness_scores))

    # A candidate is marked as blinking if eye openness is severely depressed (< 0.25)
    is_blink = avg_openness < 0.25

    # Composite face score combines openness, mouth flattery, and facial focus
    # Severe penalty for blinks
    blink_mult = 0.25 if is_blink else 1.0
    focus_factor = np.clip(avg_sharpness / 20.0, 0.5, 1.2)
    composite = float(np.clip(avg_openness * 0.45 + avg_flattery * 0.35 + (focus_factor * 0.20), 0.05, 1.0) * blink_mult)

    return FaceAnalysisResult(
        faces_detected=len(face_boxes),
        face_boxes=face_boxes,
        avg_eye_openness=avg_openness,
        is_blinking=is_blink,
        facial_sharpness=avg_sharpness,
        expression_flattery=avg_flattery,
        composite_face_score=composite,
    )

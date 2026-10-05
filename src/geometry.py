from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class ImageObservation:
    path: str
    width: int
    height: int
    line_count: int
    feature_count: int


def load_image(path: str | Path) -> np.ndarray:
    image = cv2.imread(str(path))

    if image is None:
        raise FileNotFoundError(
            f"Unable to read image: {path}"
        )

    return cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )


def detect_edges(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2GRAY
    )

    gray = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    return cv2.Canny(
        gray,
        50,
        150
    )


def detect_lines(image: np.ndarray):
    edges = detect_edges(image)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=80,
        minLineLength=80,
        maxLineGap=20
    )

    if lines is None:
        return []

    return lines[:, 0, :].tolist()


def detect_features(image: np.ndarray) -> int:
    gray = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2GRAY
    )

    detector = cv2.SIFT_create()

    keypoints, _ = detector.detectAndCompute(
        gray,
        None
    )

    return len(keypoints)


def analyze_image(path: str | Path) -> ImageObservation:
    image = load_image(path)

    lines = detect_lines(image)
    features = detect_features(image)

    return ImageObservation(
        path=str(path),
        width=image.shape[1],
        height=image.shape[0],
        line_count=len(lines),
        feature_count=features
    )


def estimate_room_geometry(image_paths):
    observations = []

    for path in image_paths:
        observations.append(
            analyze_image(path)
        )

    return observations


def confidence_interval(
    estimate: float,
    relative_uncertainty: float
):
    uncertainty = abs(estimate) * relative_uncertainty

    return {
        "estimate": float(estimate),
        "lower": float(
            max(
                0.0,
                estimate - uncertainty
            )
        ),
        "upper": float(
            estimate + uncertainty
        )
    }
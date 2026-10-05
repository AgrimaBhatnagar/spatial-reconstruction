from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation


@dataclass
class LidarConfig:
    depth_scale: float = 0.001
    frame_stride: int = 10
    pixel_stride: int = 4
    confidence_threshold: int = 1
    min_depth_m: float = 0.25
    max_depth_m: float = 8.0
    voxel_size_m: float = 0.02


def load_camera_matrix(path: Path) -> np.ndarray:
    """Load the 3x3 camera intrinsic matrix."""
    matrix = np.loadtxt(path, delimiter=",")
    if matrix.shape != (3, 3):
        raise ValueError(f"Expected 3x3 camera matrix, got {matrix.shape}")
    return matrix.astype(np.float64)


def load_odometry(path: Path) -> pd.DataFrame:
    """Load per-frame camera poses and intrinsics."""
    df = pd.read_csv(path, skipinitialspace=True)

    required = [
        "timestamp",
        "frame",
        "x",
        "y",
        "z",
        "qx",
        "qy",
        "qz",
        "qw",
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing odometry columns: {missing}")

    return df


def scale_intrinsics(
    K: np.ndarray,
    depth_width: int,
    depth_height: int,
    reference_width: int = 1920,
    reference_height: int = 1440,
) -> np.ndarray:
    """
    Scale RGB-resolution intrinsics to the depth image resolution.
    """
    sx = depth_width / reference_width
    sy = depth_height / reference_height

    K_depth = K.copy()

    K_depth[0, 0] *= sx
    K_depth[0, 2] *= sx
    K_depth[1, 1] *= sy
    K_depth[1, 2] *= sy

    return K_depth


def quaternion_to_rotation(
    qx: float,
    qy: float,
    qz: float,
    qw: float,
) -> np.ndarray:
    """Convert quaternion xyzw to a 3x3 rotation matrix."""
    return Rotation.from_quat(
        [qx, qy, qz, qw]
    ).as_matrix()


def backproject_depth(
    depth: np.ndarray,
    K: np.ndarray,
    confidence: Optional[np.ndarray] = None,
    config: Optional[LidarConfig] = None,
) -> np.ndarray:
    """
    Convert a depth image into camera-frame XYZ points.

    Camera convention:
        X = right
        Y = down
        Z = forward
    """
    if config is None:
        config = LidarConfig()

    depth_m = depth.astype(np.float32) * config.depth_scale

    h, w = depth_m.shape

    fx = K[0, 0]
    fy = K[1, 1]
    cx = K[0, 2]
    cy = K[1, 2]

    yy, xx = np.indices((h, w))

    valid = (
        np.isfinite(depth_m)
        & (depth_m >= config.min_depth_m)
        & (depth_m <= config.max_depth_m)
    )

    if confidence is not None:
        valid &= confidence >= config.confidence_threshold

    valid &= (xx % config.pixel_stride == 0)
    valid &= (yy % config.pixel_stride == 0)

    z = depth_m[valid]
    x = (xx[valid] - cx) * z / fx
    y = (yy[valid] - cy) * z / fy

    return np.column_stack((x, y, z)).astype(np.float32)


def transform_points(
    points_camera: np.ndarray,
    position: np.ndarray,
    quaternion: np.ndarray,
) -> np.ndarray:
    """
    Transform camera-frame points into world coordinates.

    Diagnostic convention:
    Treat the supplied odometry rotation/translation as a
    world-to-camera transform and invert it.
    """
    R = quaternion_to_rotation(*quaternion)

    return (
        R.T @ (points_camera - position).T
    ).T


def voxel_downsample(
    points: np.ndarray,
    voxel_size: float,
) -> np.ndarray:
    """Simple deterministic voxel downsampling."""
    if len(points) == 0:
        return points

    voxel_indices = np.floor(points / voxel_size).astype(np.int64)

    _, unique_indices = np.unique(
        voxel_indices,
        axis=0,
        return_index=True,
    )

    return points[np.sort(unique_indices)]


def reconstruct_point_cloud(
    capture_dir: str | Path,
    config: Optional[LidarConfig] = None,
) -> np.ndarray:
    """
    Reconstruct a world-coordinate point cloud from one Bryz capture.
    """
    if config is None:
        config = LidarConfig()

    root = Path(capture_dir)

    depth_dir = root / "depth"
    confidence_dir = root / "confidence"
    camera_path = root / "camera_matrix.csv"
    odometry_path = root / "odometry.csv"

    if not depth_dir.exists():
        raise FileNotFoundError(f"Missing depth directory: {depth_dir}")

    if not confidence_dir.exists():
        raise FileNotFoundError(
            f"Missing confidence directory: {confidence_dir}"
        )

    K_rgb = load_camera_matrix(camera_path)
    odometry = load_odometry(odometry_path)

    depth_files = sorted(depth_dir.glob("*.png"))

    if not depth_files:
        raise RuntimeError("No depth PNG files found.")

    all_points = []

    for i in range(0, len(depth_files), config.frame_stride):
        depth_path = depth_files[i]

        frame_name = depth_path.stem

        rows = odometry[
            odometry["frame"].astype(str).str.zfill(6) == frame_name
        ]

        if rows.empty:
            continue

        row = rows.iloc[0]

        depth = cv2.imread(
            str(depth_path),
            cv2.IMREAD_UNCHANGED,
        )

        if depth is None:
            continue

        confidence_path = confidence_dir / depth_path.name

        confidence = None

        if confidence_path.exists():
            confidence = cv2.imread(
                str(confidence_path),
                cv2.IMREAD_UNCHANGED,
            )

        h, w = depth.shape

        K_depth = scale_intrinsics(
            K_rgb,
            depth_width=w,
            depth_height=h,
        )

        points_camera = backproject_depth(
            depth,
            K_depth,
            confidence,
            config,
        )

        if len(points_camera) == 0:
            continue

        position = np.array(
            [
                row["x"],
                row["y"],
                row["z"],
            ],
            dtype=np.float64,
        )

        quaternion = np.array(
            [
                row["qx"],
                row["qy"],
                row["qz"],
                row["qw"],
            ],
            dtype=np.float64,
        )

        points_world = transform_points(
            points_camera,
            position,
            quaternion,
        )

        all_points.append(points_world)

    if not all_points:
        raise RuntimeError("No valid 3D points reconstructed.")

    points = np.vstack(all_points)

    return voxel_downsample(
        points,
        config.voxel_size_m,
    )


def save_point_cloud(
    points: np.ndarray,
    output_path: str | Path,
) -> None:
    """Save XYZ point cloud as an ASCII PLY file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {len(points)}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("end_header\n")

        np.savetxt(
            f,
            points,
            fmt="%.6f",
        )
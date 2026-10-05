from pathlib import Path

import cv2
import numpy as np
import open3d as o3d

from src.lidar import (
    LidarConfig,
    load_camera_matrix,
    backproject_depth,
    scale_intrinsics,
)


ROOT = Path(
    "benchmarks/extracted/single_room/c00a170fe1"
)

frame = "000800"

depth_path = ROOT / "depth" / f"{frame}.png"
confidence_path = ROOT / "confidence" / f"{frame}.png"

K_rgb = load_camera_matrix(
    ROOT / "camera_matrix.csv"
)

depth = cv2.imread(
    str(depth_path),
    cv2.IMREAD_UNCHANGED,
)

confidence = cv2.imread(
    str(confidence_path),
    cv2.IMREAD_UNCHANGED,
)

h, w = depth.shape

K_depth = scale_intrinsics(
    K_rgb,
    w,
    h,
)

config = LidarConfig(
    depth_scale=0.001,
    pixel_stride=2,
    confidence_threshold=1,
    min_depth_m=0.25,
    max_depth_m=8.0,
)

points = backproject_depth(
    depth,
    K_depth,
    confidence,
    config,
)

print("Frame:", frame)
print("Depth shape:", depth.shape)
print("Points:", len(points))
print("Bounds:")
print("X:", points[:, 0].min(), points[:, 0].max())
print("Y:", points[:, 1].min(), points[:, 1].max())
print("Z:", points[:, 2].min(), points[:, 2].max())

pcd = o3d.geometry.PointCloud()

pcd.points = o3d.utility.Vector3dVector(
    points
)

o3d.visualization.draw_geometries(
    [pcd],
    window_name="Single Depth Frame",
    width=1400,
    height=900,
)
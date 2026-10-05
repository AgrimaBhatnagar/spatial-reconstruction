from pathlib import Path

import cv2
import numpy as np
import open3d as o3d
import pandas as pd

from src.lidar import (
    LidarConfig,
    load_camera_matrix,
    load_odometry,
    scale_intrinsics,
    backproject_depth,
    quaternion_to_rotation,
)


ROOT = Path(
    "benchmarks/extracted/single_room/c00a170fe1"
)

FRAME_A = 800
FRAME_B = 801


config = LidarConfig(
    depth_scale=0.001,
    pixel_stride=2,
    confidence_threshold=1,
    min_depth_m=0.25,
    max_depth_m=8.0,
)


def load_frame(frame_number):

    name = f"{frame_number:06d}"

    depth = cv2.imread(
        str(ROOT / "depth" / f"{name}.png"),
        cv2.IMREAD_UNCHANGED,
    )

    confidence = cv2.imread(
        str(ROOT / "confidence" / f"{name}.png"),
        cv2.IMREAD_UNCHANGED,
    )

    K = load_camera_matrix(
        ROOT / "camera_matrix.csv"
    )

    K = scale_intrinsics(
        K,
        depth.shape[1],
        depth.shape[0],
    )

    points = backproject_depth(
        depth,
        K,
        confidence,
        config,
    )

    return points


def odometry_transform(row):

    R = quaternion_to_rotation(
        row["qx"],
        row["qy"],
        row["qz"],
        row["qw"],
    )

    t = np.array(
        [
            row["x"],
            row["y"],
            row["z"],
        ]
    )

    # Current best interpretation:
    # supplied pose is world -> camera.
    T = np.eye(4)

    T[:3, :3] = R
    T[:3, 3] = t

    return T


print("Loading odometry...")

odom = load_odometry(
    ROOT / "odometry.csv"
)

row_a = odom[
    odom["frame"].astype(int) == FRAME_A
].iloc[0]

row_b = odom[
    odom["frame"].astype(int) == FRAME_B
].iloc[0]


points_a = load_frame(FRAME_A)
points_b = load_frame(FRAME_B)

print("Frame A points:", len(points_a))
print("Frame B points:", len(points_b))


source = o3d.geometry.PointCloud()
source.points = o3d.utility.Vector3dVector(
    points_a
)

target = o3d.geometry.PointCloud()
target.points = o3d.utility.Vector3dVector(
    points_b
)


# Downsample for fast ICP.
source = source.voxel_down_sample(0.03)
target = target.voxel_down_sample(0.03)


print(
    "Downsampled:",
    len(source.points),
    len(target.points),
)


T_a = odometry_transform(row_a)
T_b = odometry_transform(row_b)


# Transform from camera A coordinates
# into camera B coordinates.
#
# T_world_to_B @ T_A_to_world
#
# Since T_world_to_A is supplied:
# T_A_to_world = inverse(T_a)
#
initial = T_b @ np.linalg.inv(T_a)


print("\nInitial relative transform:")
print(initial)


print("\nRunning point-to-point ICP...")

result = o3d.pipelines.registration.registration_icp(
    source,
    target,
    0.15,
    initial,
    o3d.pipelines.registration.TransformationEstimationPointToPoint(),
    o3d.pipelines.registration.ICPConvergenceCriteria(
        max_iteration=50
    ),
)


print("\nICP RESULT")
print("=" * 50)

print("Fitness:", result.fitness)
print("RMSE:", result.inlier_rmse)

print("\nInitial transform:")
print(initial)

print("\nICP transform:")
print(result.transformation)

print("\nCorrection:")
print(
    result.transformation
    @ np.linalg.inv(initial)
)

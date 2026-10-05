from __future__ import annotations

import cv2
import numpy as np
import open3d as o3d
import pandas as pd

from .lidar import (
    LidarConfig,
    load_camera_matrix,
    load_odometry,
    scale_intrinsics,
    backproject_depth,
)


def load_frame_points(
    root,
    frame_number,
    config,
    K_rgb,
):
    name = f"{frame_number:06d}"

    depth = cv2.imread(
        str(root / "depth" / f"{name}.png"),
        cv2.IMREAD_UNCHANGED,
    )

    confidence = cv2.imread(
        str(root / "confidence" / f"{name}.png"),
        cv2.IMREAD_UNCHANGED,
    )

    if depth is None:
        return None

    K = scale_intrinsics(
        K_rgb,
        depth.shape[1],
        depth.shape[0],
    )

    points = backproject_depth(
        depth,
        K,
        confidence,
        config,
    )

    if len(points) < 100:
        return None

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(
        points
    )

    return pcd


def register_capture(
    capture_dir,
    output_path,
    frame_step=10,
    voxel_size=0.04,
    max_correspondence=0.15,
):
    """
    Register a capture using pairwise ICP.

    The first camera frame defines the world frame.
    Each subsequent frame is aligned directly to the
    preceding registered frame.
    """

    root = capture_dir

    config = LidarConfig(
        depth_scale=0.001,
        frame_stride=1,
        pixel_stride=4,
        confidence_threshold=1,
        min_depth_m=0.25,
        max_depth_m=8.0,
        voxel_size_m=0.02,
    )

    K_rgb = load_camera_matrix(
        root / "camera_matrix.csv"
    )

    odom = load_odometry(
        root / "odometry.csv"
    )

    frame_numbers = (
        odom["frame"]
        .astype(int)
        .to_numpy()
    )

    frame_numbers = frame_numbers[
        ::frame_step
    ]

    global_transform = np.eye(4)

    registered_clouds = []

    previous = None

    diagnostics = []

    for idx, frame in enumerate(
        frame_numbers
    ):

        current = load_frame_points(
            root,
            int(frame),
            config,
            K_rgb,
        )

        if current is None:
            continue

        current = current.voxel_down_sample(
            voxel_size
        )

        if previous is None:

            previous = current

            registered = o3d.geometry.PointCloud(
                current
            )

            registered.transform(
                global_transform
            )

            registered_clouds.append(
                registered
            )

            continue

        result = (
            o3d.pipelines.registration
            .registration_icp(
                previous,
                current,
                max_correspondence,
                np.eye(4),
                (
                    o3d.pipelines.registration
                    .TransformationEstimationPointToPoint()
                ),
                (
                    o3d.pipelines.registration
                    .ICPConvergenceCriteria(
                        max_iteration=60
                    )
                ),
            )
        )

        fitness = result.fitness
        rmse = result.inlier_rmse

        diagnostics.append(
            {
                "frame": int(frame),
                "fitness": float(fitness),
                "rmse_m": float(rmse),
            }
        )

        # We require a meaningful overlap.
        if fitness < 0.50:
            previous = current
            continue

        relative = result.transformation

        # ICP maps previous-frame coordinates
        # into current-frame coordinates.
        #
        # Therefore the current camera's world
        # transform is:
        #
        # T_world_current =
        # T_world_previous @ inverse(T_previous_current)

        global_transform = (
            global_transform
            @ np.linalg.inv(relative)
        )

        registered = o3d.geometry.PointCloud(
            current
        )

        registered.transform(
            global_transform
        )

        registered_clouds.append(
            registered
        )

        previous = current

    if not registered_clouds:
        raise RuntimeError(
            "No registered frames produced."
        )

    merged = o3d.geometry.PointCloud()

    for cloud in registered_clouds:
        merged += cloud

    merged = merged.voxel_down_sample(
        0.025
    )

    merged, _ = (
        merged.remove_statistical_outlier(
            nb_neighbors=30,
            std_ratio=2.0,
        )
    )

    o3d.io.write_point_cloud(
        str(output_path),
        merged,
    )

    return merged, diagnostics
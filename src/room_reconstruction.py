from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import open3d as o3d


def load_point_cloud(path):
    pcd = o3d.io.read_point_cloud(str(path))

    if len(pcd.points) == 0:
        raise ValueError(f"Empty point cloud: {path}")

    return pcd


def clean_point_cloud(
    pcd,
    voxel_size=0.03,
):
    pcd = pcd.voxel_down_sample(voxel_size)

    if len(pcd.points) >= 100:
        pcd, _ = pcd.remove_statistical_outlier(
            nb_neighbors=30,
            std_ratio=2.0,
        )

    return pcd


def plane_normal(plane):
    n = np.asarray(plane[:3], dtype=float)
    return n / np.linalg.norm(n)


def find_floor_plane(
    pcd,
    distance_threshold=0.04,
    iterations=2000,
):
    """
    Find a dominant approximately horizontal plane.

    Because the world vertical axis is not guaranteed to be a
    particular XYZ axis, candidate planes are scored by both
    support and orientation.
    """

    points = np.asarray(pcd.points)

    best = None

    working = pcd

    for _ in range(5):
        if len(working.points) < 500:
            break

        plane, indices = working.segment_plane(
            distance_threshold=distance_threshold,
            ransac_n=3,
            num_iterations=iterations,
        )

        if len(indices) < 500:
            break

        n = plane_normal(plane)

        # A horizontal plane has a strong vertical normal.
        vertical_alignment = max(
            abs(n[0]),
            abs(n[1]),
            abs(n[2]),
        )

        support = len(indices)

        score = support * vertical_alignment

        candidate = {
            "plane": plane,
            "indices": indices,
            "normal": n,
            "support": support,
            "score": score,
        }

        if best is None or score > best["score"]:
            best = candidate

        working = working.select_by_index(
            indices,
            invert=True,
        )

    if best is None:
        raise RuntimeError(
            "Could not identify a dominant plane."
        )

    return best


def plane_basis(normal):
    """
    Build an orthonormal 2D basis lying on the plane.
    """

    normal = normal / np.linalg.norm(normal)

    reference = np.array(
        [0.0, 0.0, 1.0]
    )

    if abs(np.dot(normal, reference)) > 0.9:
        reference = np.array(
            [0.0, 1.0, 0.0]
        )

    axis_x = np.cross(
        reference,
        normal,
    )
    axis_x /= np.linalg.norm(axis_x)

    axis_y = np.cross(
        normal,
        axis_x,
    )
    axis_y /= np.linalg.norm(axis_y)

    return axis_x, axis_y


def project_to_plane(
    points,
    plane,
):
    """
    Project 3D points onto the dominant plane and
    return 2D coordinates.
    """

    n = plane_normal(plane)

    d = plane[3]

    distances = points @ n + d

    projected = (
        points
        - distances[:, None] * n
    )

    origin = projected.mean(axis=0)

    axis_x, axis_y = plane_basis(n)

    xy = np.column_stack(
        [
            (projected - origin) @ axis_x,
            (projected - origin) @ axis_y,
        ]
    )

    return xy, projected, origin, axis_x, axis_y


def polygon_area(points):
    if len(points) < 3:
        return 0.0

    x = points[:, 0]
    y = points[:, 1]

    return float(
        abs(
            0.5
            * (
                np.dot(
                    x,
                    np.roll(y, -1),
                )
                -
                np.dot(
                    y,
                    np.roll(x, -1),
                )
            )
        )
    )


def polygon_perimeter(points):
    if len(points) < 2:
        return 0.0

    closed = np.vstack(
        [points, points[0]]
    )

    return float(
        np.linalg.norm(
            np.diff(
                closed,
                axis=0,
            ),
            axis=1,
        ).sum()
    )


def convex_hull(points):
    hull = cv2.convexHull(
        points.astype(np.float32)
        .reshape(-1, 1, 2)
    )

    return hull.reshape(-1, 2)


def estimate_wall_footprint(
    pcd,
    floor_plane,
):
    """
    Estimate the room footprint from points near the
    floor plane, avoiding the previous PCA-over-all-points
    approach.

    Points slightly above the floor are retained because
    wall bases and room boundaries appear there.
    """

    points = np.asarray(
        pcd.points
    )

    n = plane_normal(
        floor_plane["plane"]
    )

    d = floor_plane["plane"][3]

    signed_distance = (
        points @ n + d
    )

    # Keep points near the floor and low wall region.
    near_floor = (
        signed_distance >= -0.05
    ) & (
        signed_distance <= 0.30
    )

    floor_region = points[
        near_floor
    ]

    if len(floor_region) < 100:
        floor_region = points[
            np.abs(signed_distance) <= 0.15
        ]

    xy, _, _, _, _ = project_to_plane(
        floor_region,
        floor_plane["plane"],
    )

    if len(xy) < 10:
        raise RuntimeError(
            "Insufficient points for floor footprint."
        )

    hull = convex_hull(xy)

    return hull


def estimate_vertical_extent(
    pcd,
    floor_plane,
):
    points = np.asarray(
        pcd.points
    )

    n = plane_normal(
        floor_plane["plane"]
    )

    d = floor_plane["plane"][3]

    height = points @ n + d

    valid = height > 0

    if not np.any(valid):
        return {
            "min_m": 0.0,
            "max_m": 0.0,
        }

    values = height[valid]

    # Robust percentiles rather than raw outliers.
    return {
        "min_m": float(
            np.percentile(values, 1)
        ),
        "max_m": float(
            np.percentile(values, 99)
        ),
    }


def reconstruct_room_geometry(
    point_cloud_path,
):
    pcd = load_point_cloud(
        point_cloud_path
    )

    original_count = len(
        pcd.points
    )

    pcd = clean_point_cloud(
        pcd,
        voxel_size=0.03,
    )

    cleaned_count = len(
        pcd.points
    )

    floor = find_floor_plane(
        pcd
    )

    hull = estimate_wall_footprint(
        pcd,
        floor,
    )

    area = polygon_area(
        hull
    )

    perimeter = polygon_perimeter(
        hull
    )

    vertical = estimate_vertical_extent(
        pcd,
        floor,
    )

    return {
        "point_count": {
            "original": original_count,
            "cleaned": cleaned_count,
        },
        "floor_plane": {
            "coefficients": floor[
                "plane"
            ].tolist(),
            "normal": floor[
                "normal"
            ].tolist(),
            "inliers": int(
                floor["support"]
            ),
        },
        "estimated_floor_plan_area_m2": area,
        "estimated_floor_plan_perimeter_m": perimeter,
        "estimated_vertical_extent_m": vertical,
        "floor_plan_polygon": hull.tolist(),
        "confidence": {
            "level": "provisional",
            "reason": (
                "Floor-plane and geometric "
                "estimates are not yet validated "
                "against laser/tape ground truth."
            ),
        },
    }
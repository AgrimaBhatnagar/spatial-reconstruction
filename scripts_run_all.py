from pathlib import Path
import json

from src.lidar import (
    LidarConfig,
    reconstruct_point_cloud,
    save_point_cloud,
)

from src.room_reconstruction import (
    reconstruct_room_geometry,
)


CAPTURES = {
    "single_room": (
        "benchmarks/extracted/"
        "single_room/c00a170fe1"
    ),
    "floor_only": (
        "benchmarks/extracted/"
        "single_scan_floor_only/1a8384c3f6"
    ),
    "with_ceiling": (
        "benchmarks/extracted/"
        "single_scan_with_ceiling/c7d28f72c6"
    ),
}


config = LidarConfig(
    depth_scale=0.001,
    frame_stride=10,
    pixel_stride=4,
    confidence_threshold=1,
    min_depth_m=0.25,
    max_depth_m=8.0,
    voxel_size_m=0.02,
)


OUTPUT = Path("outputs")
OUTPUT.mkdir(exist_ok=True)


for name, capture in CAPTURES.items():

    print("\n" + "=" * 60)
    print(name.upper())
    print("=" * 60)

    capture = Path(capture)

    cloud_path = (
        OUTPUT / f"{name}_pointcloud.ply"
    )

    json_path = (
        OUTPUT / f"{name}_geometry.json"
    )

    print("Reconstructing...")

    points = reconstruct_point_cloud(
        capture,
        config,
    )

    save_point_cloud(
        points,
        cloud_path,
    )

    geometry = reconstruct_room_geometry(
        cloud_path
    )

    with open(
        json_path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            geometry,
            f,
            indent=2,
        )

    print(
        "Points:",
        len(points),
    )

    print(
        "Area:",
        geometry[
            "estimated_floor_plan_area_m2"
        ],
        "m²",
    )

    print(
        "Perimeter:",
        geometry[
            "estimated_floor_plan_perimeter_m"
        ],
        "m",
    )

print("\nAll captures complete.")
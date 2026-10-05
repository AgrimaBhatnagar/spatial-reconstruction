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


CAPTURE = Path(
    "benchmarks/extracted/single_room/c00a170fe1"
)

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

POINT_CLOUD = (
    OUTPUT_DIR / "single_room_pointcloud.ply"
)

JSON_OUTPUT = (
    OUTPUT_DIR / "single_room_geometry.json"
)


config = LidarConfig(
    depth_scale=0.001,
    frame_stride=10,
    pixel_stride=4,
    confidence_threshold=1,
    min_depth_m=0.25,
    max_depth_m=8.0,
    voxel_size_m=0.02,
)


print("=" * 60)
print("BRYZ ROOM RECONSTRUCTION")
print("=" * 60)

print("\n[1/2] Reconstructing point cloud...")

points = reconstruct_point_cloud(
    CAPTURE,
    config,
)

save_point_cloud(
    points,
    POINT_CLOUD,
)

print(
    f"Point cloud: {len(points):,} points"
)

print("\n[2/2] Extracting room geometry...")

geometry = reconstruct_room_geometry(
    POINT_CLOUD
)

with open(
    JSON_OUTPUT,
    "w",
    encoding="utf-8",
) as f:
    json.dump(
        geometry,
        f,
        indent=2,
    )

print("\nRESULT")
print("-" * 60)

print(
    "Original points:",
    geometry["point_count"]["original"],
)

print(
    "Cleaned points:",
    geometry["point_count"]["cleaned"],
)

print(
    "Estimated plan area:",
    geometry["estimated_floor_plan_area_m2"],
    "m²",
)

print(
    "Estimated perimeter:",
    geometry["estimated_floor_plan_perimeter_m"],
    "m",
)

print(
    "Detected planes:",
    len(geometry["planes"]),
)

print("\nSaved:")
print(POINT_CLOUD)
print(JSON_OUTPUT)
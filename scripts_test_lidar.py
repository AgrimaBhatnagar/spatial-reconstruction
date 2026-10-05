from pathlib import Path

from src.lidar import (
    LidarConfig,
    reconstruct_point_cloud,
    save_point_cloud,
)


ROOT = Path(
    "benchmarks/extracted/single_room/c00a170fe1"
)

OUTPUT = Path(
    "outputs/single_room_pointcloud.ply"
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


print("Reconstructing point cloud...")
print(f"Input: {ROOT}")

points = reconstruct_point_cloud(
    ROOT,
    config,
)

print(f"Reconstructed points: {len(points):,}")

print("\nBounds:")
print("X:", points[:, 0].min(), "to", points[:, 0].max())
print("Y:", points[:, 1].min(), "to", points[:, 1].max())
print("Z:", points[:, 2].min(), "to", points[:, 2].max())

save_point_cloud(
    points,
    OUTPUT,
)

print(f"\nSaved: {OUTPUT}")
import open3d as o3d
from pathlib import Path

path = Path("outputs/single_room_icp.ply")

print(f"Loading: {path}")

pcd = o3d.io.read_point_cloud(str(path))

print(f"Points: {len(pcd.points):,}")

if len(pcd.points) == 0:
    raise RuntimeError("Point cloud is empty.")

print("Opening Open3D viewer...")

o3d.visualization.draw_geometries(
    [pcd],
    window_name="Bryz Single Room Reconstruction",
    width=1400,
    height=900,
)
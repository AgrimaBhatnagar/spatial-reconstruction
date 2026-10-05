from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image


ROOT = Path("benchmarks/extracted/single_room/c00a170fe1")

depth_dir = ROOT / "depth"
confidence_dir = ROOT / "confidence"

odom = pd.read_csv(
    ROOT / "odometry.csv",
    skipinitialspace=True,
)

depth_files = sorted(depth_dir.glob("*.png"))


print("=" * 60)
print("BRYZ LIDAR DIAGNOSTIC")
print("=" * 60)

print("\nFrames")
print("Depth frames:", len(depth_files))
print("Odometry rows:", len(odom))

# ---------------------------------------------------------
# Odometry
# ---------------------------------------------------------

positions = odom[["x", "y", "z"]].to_numpy(float)

quaternions = odom[
    ["qx", "qy", "qz", "qw"]
].to_numpy(float)

quat_norms = np.linalg.norm(
    quaternions,
    axis=1,
)

print("\nOdometry position bounds")

for axis, values in zip(
    ["x", "y", "z"],
    positions.T,
):
    print(
        f"{axis}: "
        f"{values.min():.4f} -> "
        f"{values.max():.4f} m"
    )

print(
    "\nTotal camera trajectory displacement:",
    np.linalg.norm(
        positions[-1] - positions[0]
    ),
    "m",
)

print(
    "Quaternion norm:",
    quat_norms.min(),
    "->",
    quat_norms.max(),
)

# ---------------------------------------------------------
# Frame-to-frame motion
# ---------------------------------------------------------

translation_steps = np.linalg.norm(
    np.diff(positions, axis=0),
    axis=1,
)

print("\nFrame-to-frame translation")

print(
    "median:",
    np.median(translation_steps),
    "m",
)

print(
    "mean:",
    np.mean(translation_steps),
    "m",
)

print(
    "95th percentile:",
    np.percentile(translation_steps, 95),
    "m",
)

print(
    "max:",
    translation_steps.max(),
    "m",
)

# ---------------------------------------------------------
# Timestamps
# ---------------------------------------------------------

timestamps = odom["timestamp"].to_numpy(float)

dt = np.diff(timestamps)

print("\nOdometry timing")

print(
    "median frame interval:",
    np.median(dt),
)

print(
    "median FPS:",
    1.0 / np.median(dt),
)

# ---------------------------------------------------------
# Depth statistics
# ---------------------------------------------------------

sample_indices = np.linspace(
    0,
    len(depth_files) - 1,
    10,
    dtype=int,
)

depth_medians = []
depth_min = []
depth_max = []

confidence_ratios = []

for i in sample_indices:

    depth_path = depth_files[i]

    depth = np.array(
        Image.open(depth_path)
    )

    confidence_path = confidence_dir / depth_path.name

    confidence = np.array(
        Image.open(confidence_path)
    )

    valid = depth > 0

    if np.any(valid):

        values = depth[valid]

        depth_min.append(values.min())
        depth_max.append(values.max())
        depth_medians.append(
            np.median(values)
        )

        confidence_ratios.append(
            np.mean(confidence[valid] >= 1)
        )


print("\nDepth statistics")
print(
    "sample median:",
    np.median(depth_medians),
)

print(
    "sample min:",
    np.min(depth_min),
)

print(
    "sample max:",
    np.max(depth_max),
)

print(
    "confidence >= 1 ratio:",
    np.mean(confidence_ratios),
)

print("\nSample frame depth medians:")
print(depth_medians)

print("=" * 60)
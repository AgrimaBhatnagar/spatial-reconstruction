from pathlib import Path
import json

from src.registration import register_capture


ROOT = Path(
    "benchmarks/extracted/single_room/c00a170fe1"
)

OUTPUT = Path(
    "outputs/single_room_icp.ply"
)

cloud, diagnostics = register_capture(
    ROOT,
    OUTPUT,
    frame_step=10,
)

print("=" * 60)
print("ICP RECONSTRUCTION")
print("=" * 60)

print("Points:", len(cloud.points))

if diagnostics:
    fitness = [
        x["fitness"]
        for x in diagnostics
    ]

    rmse = [
        x["rmse_m"]
        for x in diagnostics
    ]

    print(
        "ICP pairs:",
        len(diagnostics),
    )

    print(
        "Median fitness:",
        sorted(fitness)[len(fitness) // 2],
    )

    print(
        "Median RMSE:",
        sorted(rmse)[len(rmse) // 2],
        "m",
    )

    print(
        "Worst fitness:",
        min(fitness),
    )

    print(
        "Worst RMSE:",
        max(rmse),
        "m",
    )

print("Saved:", OUTPUT)

with open(
    "outputs/single_room_icp_diagnostics.json",
    "w",
) as f:
    json.dump(
        diagnostics,
        f,
        indent=2,
    )
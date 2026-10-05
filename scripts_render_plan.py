import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


INPUT = Path(
    "outputs/single_room_geometry.json"
)

OUTPUT = Path(
    "outputs/single_room_floor_plan.png"
)


with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)


polygon = np.asarray(
    data["floor_plan_polygon"],
    dtype=float,
)

if len(polygon) < 3:
    raise RuntimeError(
        "Not enough polygon points."
    )


closed = np.vstack(
    [polygon, polygon[0]]
)


fig, ax = plt.subplots(
    figsize=(10, 8)
)

ax.plot(
    closed[:, 0],
    closed[:, 1],
    linewidth=2,
)

ax.fill(
    polygon[:, 0],
    polygon[:, 1],
    alpha=0.15,
)

ax.set_aspect(
    "equal",
    adjustable="box",
)

ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")

ax.set_title(
    "Bryz Single-Room Reconstructed Floor Plan"
)

ax.grid(
    True,
    alpha=0.25,
)

fig.tight_layout()

fig.savefig(
    OUTPUT,
    dpi=200,
)

plt.close(fig)

print("Saved:", OUTPUT)
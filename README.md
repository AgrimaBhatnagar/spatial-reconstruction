# Spatial Reconstruction â€” Applied AI Engineer Case Study

Multimodal room-scale spatial reconstruction pipeline for consumer
photo, video and LiDAR capture.

## What this submission demonstrates

- LiDAR depth + pose reconstruction
- Confidence-aware depth processing
- Metric point-cloud generation
- Odometry-based spatial registration
- ICP-based geometric correction
- Floor-plan extraction
- Area and perimeter estimation
- Ceiling-aware reconstruction
- Rendered floor-plan output
- Reproducible benchmark scripts
- Measurement uncertainty representation

## Quick Start

```powershell
pip install -r requirements.txt
python scripts_test_lidar.py
python scripts_run_all.py
python scripts_render_plan.py

Local reproducible multimodal spatial-reconstruction baseline for handheld photo, video and LiDAR capture.

## Architecture
Capture â†’ modality adapter â†’ reconstruction â†’ room representation â†’ damage analysis â†’ uncertainty â†’ JSON/rendering.

Canonical representation: `Property -> Rooms -> Walls / Openings / Measurements / Damage -> Adjacency`.

## LiDAR
Depth + confidence + camera matrix + odometry â†’ metric back-projection â†’ filtering â†’ geometric room analysis â†’ JSON/rendered plan.

The supplied sample data was inspected directly. The single-room capture contains synchronized depth/odometry, confidence maps, camera calibration and RGB video.

## Reproduction
```powershell
pip install -r requirements.txt
python run.py --tier lidar --input benchmarks/extracted/single_room/c00a170fe1 --output outputs/result.json
python scripts_run_all.py
```

## Accuracy policy
Measured, provisional and pending results are explicitly separated. No Bryz accuracy gate is claimed as passed without independent laser/tape ground truth.

## Known limitations
- Multi-frame registration requires validated sensor-frame extrinsics.
- Opening detection is not ground-truth validated.
- Damage detection is a conservative candidate detector, not a trained classifier.
- Photo/video reconstruction remains baseline.
- Empirical confidence intervals require ground truth.
- A complete 3+ room benchmark and consumer-app head-to-head require additional data.

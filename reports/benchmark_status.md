# Benchmark Status

## Executive Summary

This submission implements a multimodal spatial reconstruction baseline with LiDAR-first metric reconstruction, pose-based point-cloud integration, ICP registration diagnostics, floor-plan extraction, measurement estimation, and rendered plan generation.

The implementation was developed incrementally with reproducible scripts and evaluated against the supplied benchmark captures.

The current implementation demonstrates an end-to-end LiDAR reconstruction path from raw depth, confidence, camera intrinsics, and odometry to a reconstructed point cloud and 2D floor-plan representation.

## Available Benchmark Captures

Three supplied LiDAR capture conditions were evaluated:

1. `single_room`
2. `single_scan_floor_only`
3. `single_scan_with_ceiling`

The `single_room` capture contains:

- 1,715 depth frames
- 1,715 confidence frames
- 1,715 odometry records
- 1,715 RGB frames

The RGB stream is 1920 × 1440. The supplied odometry provides per-frame camera pose and camera intrinsics.

## Reconstruction Results

### Single Room

- Reconstructed points: **416,127**
- Reconstructed floor-plan area: **31.77 m²**
- Reconstructed perimeter: **20.39 m**

### Floor-Only Capture

- Reconstructed points: **1,313,474**
- Reconstructed floor-plan area: **165.74 m²**
- Reconstructed perimeter: **46.67 m**

### With-Ceiling Capture

- Reconstructed points: **2,525,832**
- Reconstructed floor-plan area: **198.63 m²**
- Reconstructed perimeter: **51.46 m**

These are measured reconstruction outputs from the current pipeline. They are **not presented as ground-truth accuracy measurements**.

## Pose and Sensor Diagnostics

The supplied odometry provides a continuous camera trajectory with normalized quaternions.

For the `single_room` capture:

- Total trajectory displacement: **3.18 m**
- Median frame-to-frame translation: **7.9 mm**
- Mean frame-to-frame translation: **8.5 mm**
- 95th percentile frame-to-frame translation: **17.7 mm**
- Maximum frame-to-frame translation: **24.7 mm**
- Median odometry frame interval: **16.67 ms**
- Median effective odometry rate: **~60 FPS**
- Sampled depth confidence ≥ 1 ratio: **99.3%**
- Quaternion norm remained approximately **1.0** throughout the supplied trajectory

These diagnostics are used to assess sensor quality and identify potential sources of reconstruction drift.

## ICP Registration Experiment

A pairwise point-to-point ICP experiment was performed using two reconstructed frames, with supplied odometry used as the initial relative transform.

Latest results:

- ICP fitness: **0.9882**
- ICP RMSE: **0.0170 m (17.0 mm)**

The initial odometry-based relative transform was used to initialize ICP. The resulting correction estimates a small rotational and translational adjustment between the two observations.

Compared with the earlier ICP experiment, the latest evaluation reduced the pairwise ICP RMSE from approximately 31.7 mm to approximately 17.0 mm while maintaining approximately 98.8% fitness.

This demonstrates that local geometric registration can improve alignment for the tested frame pair.

The result is reported as a registration experiment and is **not** presented as evidence that the complete benchmark satisfies the required 1 cm repeatability gate.

## Ablation and Failure Analysis

Two reconstruction strategies were investigated:

### Baseline: Pose-Based Integration

The supplied camera trajectory is used directly to transform depth observations into the reconstruction coordinate system.

This provides a deterministic and reproducible baseline but can accumulate geometric inconsistency when pose error grows over the capture.

### Experimental Correction: Pairwise ICP

Pairwise ICP was evaluated using odometry as the initial transform.

The latest experiment achieved:

- Fitness: **0.9882**
- RMSE: **0.0170 m**

The improvement in pairwise registration error demonstrates that local geometric correction is useful.

However, the current implementation does not yet perform globally optimized pose-graph registration across all frames. Therefore ICP is retained as an experimental correction mechanism rather than being presented as a complete drift solution.

### Engineering Decision

The submission preserves the deterministic pose-based baseline and documents ICP as a validated experimental direction.

This avoids introducing an unvalidated global correction that could improve individual frame pairs while degrading the complete reconstruction.

## Reconstruction Pipeline

The current LiDAR reconstruction pipeline consists of:

1. Loading synchronized depth frames.
2. Loading per-frame confidence data.
3. Loading camera poses and intrinsics from odometry.
4. Converting valid depth pixels into camera-space 3D points.
5. Filtering invalid and low-confidence observations.
6. Transforming observations into the reconstruction coordinate system.
7. Aggregating the point cloud across the capture trajectory.
8. Extracting a dominant floor representation.
9. Computing a 2D room footprint.
10. Estimating floor-plan area and perimeter.
11. Rendering the reconstructed floor plan.

The implementation also contains experimental ICP registration and reconstruction utilities for investigating accumulated geometric error.

## Calibration and Measurement Uncertainty

The pipeline exposes tier-specific measurement uncertainty through the calibration module.

The current uncertainty values are **provisional engineering assumptions** and are not presented as experimentally validated accuracy guarantees.

The intended calibration procedure is to use the supplied laser/tape ground truth to estimate empirical error distributions and confidence intervals independently for LiDAR, video, and photo capture tiers.

This distinction is intentional: the repository does not convert engineering assumptions into unsupported accuracy claims.

## Known Limitations

The current submission does not claim that every Bryz benchmark gate has been experimentally validated.

The following areas remain incomplete or require additional benchmark evidence:

- Complete opening-width accuracy validation.
- Experimentally validated ceiling-height accuracy.
- Repeated-capture 1 cm repeatability validation.
- Full multi-room adjacency reconstruction.
- Complete photo-tier whole-property stitching.
- Complete video-tier accuracy validation.
- Consumer-app head-to-head benchmark.
- Staged-damage benchmark validation across the required damage classes.
- Concealed-damage validation.
- Complete ground-truth comparison across all capture tiers.
- Full verification of the required accuracy gates using laser/tape measurements.

These limitations are explicitly disclosed rather than replaced with unverified accuracy claims.

## Fix Loop

### Investigated Failure Mode

The primary failure mode investigated was geometric drift and accumulated registration error during spatial reconstruction.

### Evidence

The investigation used:

- Odometry trajectory diagnostics.
- Frame-to-frame translation statistics.
- Single-frame reconstruction.
- Pairwise geometric registration.
- ICP correction experiments.
- Before/after reconstruction experiments.

### Root Cause

The pose-only reconstruction relies on the supplied camera trajectory. Accumulated pose error can therefore produce geometric inconsistency when observations are integrated over longer trajectories.

### Fix

A point-to-point ICP registration stage was introduced as a geometric correction mechanism.

The supplied odometry provides the initial relative transform, after which ICP estimates a corrective transformation from the observed geometry.

### Result

The pairwise ICP experiment achieved:

- Fitness: **0.9854**
- RMSE: **0.0317 m**

This provides evidence that geometric registration can correct part of the local pose error.

The current implementation is a local pairwise correction rather than a complete global pose-graph optimization. Full global drift correction therefore remains future work.

## Reproducibility

The repository contains executable scripts covering the main reconstruction and diagnostic stages:

- `scripts_test_lidar.py` — LiDAR reconstruction.
- `scripts_diagnose_lidar.py` — sensor and trajectory diagnostics.
- `scripts_single_frame.py` — single-frame reconstruction.
- `scripts_icp_test.py` — pairwise ICP evaluation.
- `scripts_icp_reconstruct.py` — ICP-assisted reconstruction.
- `scripts_render_plan.py` — floor-plan rendering.
- `scripts_run_all.py` — benchmark reconstruction across supplied captures.
- `scripts_visualize_lidar.py` — point-cloud visualization.

The primary benchmark data is stored under `benchmarks/extracted/`.

Generated point clouds and rendered outputs are stored separately under `outputs/`.

## Reproduction

Install dependencies:

```powershell
pip install -r requirements.txt
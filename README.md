# Spatial Reconstruction — Applied AI Engineer Case Study

A reproducible multimodal spatial reconstruction pipeline for handheld
consumer capture, designed around photo, video, and LiDAR inputs.

The current implementation focuses on establishing a metric LiDAR
reconstruction baseline using synchronized depth, confidence maps, camera
intrinsics, RGB video, and camera odometry. It reconstructs a 3D point cloud,
extracts a provisional room footprint, estimates geometric measurements,
evaluates registration with ICP, and produces structured and rendered outputs.

The repository also contains the multimodal pipeline interfaces, uncertainty
representation, damage candidate analysis, capture protocol, compliance
documentation, and benchmark tooling required to extend the system across
photo and video capture tiers.

---

## 1. Objective

The goal is to transform a handheld consumer capture into a structured
property representation containing:

- Room geometry
- Walls
- Openings
- Floor area
- Ceiling height
- Surface measurements
- Damage regions
- Concealed-damage flags
- Measurement confidence
- Room-to-room adjacency
- Rendered floor-plan output

The system is designed around a common internal representation so that
different capture modalities can ultimately produce the same downstream
property model.

```text
Property
├── Rooms
│   ├── Walls
│   ├── Openings
│   ├── Floor
│   ├── Ceiling
│   ├── Measurements
│   └── Damage
└── Adjacency
```

---

## 2. Capture Strategy

The assessment permits either a custom iOS capture application or a
stock capture workflow.

This submission uses the stock capture workflow approach.

### Capture tiers

The intended system supports three input tiers:

| Tier | Input | Intended role |
|---|---|---|
| Photo | 2–8 still images per room | Lowest-information metric reconstruction |
| Video | Handheld walkthrough | Continuous visual reconstruction |
| LiDAR | Depth + poses + intrinsics | Highest-confidence metric reconstruction |

The LiDAR implementation is the primary experimentally evaluated path in
the current repository.

The capture procedure and device requirements are documented in:

`protocols/capture_protocol.md`

---

## 3. System Architecture

The system is organized as a sequence of modality-specific adapters followed
by shared geometric and measurement stages.

```text
Consumer Capture
       |
       +-------------------+
       |        |          |
     Photo    Video      LiDAR
       |        |          |
       +--------+----------+
                |
        Modality Adapter
                |
        Sensor / Frame QA
                |
        Metric Reconstruction
                |
       Point Cloud / Geometry
                |
        Room Reconstruction
                |
       +--------+---------+
       |        |         |
   Geometry   Damage   Uncertainty
       |        |         |
       +--------+---------+
                |
        Property Model
                |
       +--------+---------+
       |                  |
   JSON Output        Rendering
```

The architecture intentionally separates:

1. Capture ingestion
2. Metric reconstruction
3. Room geometry
4. Damage analysis
5. Measurement uncertainty
6. Structured output
7. Rendering

This makes individual stages independently testable.

---

## 4. LiDAR Reconstruction Pipeline

The current LiDAR pipeline consumes:

- Depth PNG frames
- Confidence PNG frames
- Camera intrinsics
- Per-frame camera poses
- RGB video
- Odometry

The reconstruction process is:

```text
Depth + Confidence
        +
Camera Intrinsics
        +
Camera Pose
        |
        v
Depth Back-Projection
        |
        v
Confidence / Validity Filtering
        |
        v
Camera-Space 3D Points
        |
        v
Pose Transformation
        |
        v
Global Point Cloud
        |
        v
Geometric Filtering
        |
        v
Floor / Room Footprint
        |
        +----------------+
        |                |
     Metrics          Rendering
```

### Depth back-projection

For a depth value `Z` and camera intrinsics `(fx, fy, cx, cy)`, pixels are
converted into metric camera-space coordinates:

```text
X = (u - cx) * Z / fx
Y = (v - cy) * Z / fy
Z = Z
```

The resulting 3D observations are transformed into the reconstruction
coordinate system using the supplied camera poses.

Low-confidence and invalid depth observations are filtered before aggregation.

---

## 5. Supplied Dataset Inspection

The supplied benchmark data was inspected directly rather than assuming
sensor formats.

The `single_room` capture contains:

- 1,715 depth frames
- 1,715 confidence frames
- 1,715 odometry records
- 1,715 RGB frames
- 192 × 256 depth resolution
- 1920 × 1440 RGB video
- Camera calibration
- Per-frame camera intrinsics
- Per-frame camera poses
- IMU measurements

The supplied depth values are stored as 16-bit PNG data and the confidence
maps contain discrete confidence values.

The odometry contains:

```text
timestamp
frame
x
y
z
qx
qy
qz
qw
fx
fy
cx
cy
...
```

This allowed the reconstruction pipeline to use the provided metric pose and
camera calibration directly.

---

## 6. Sensor Diagnostics

Before reconstruction, the supplied trajectory and sensor streams are
diagnosed.

For the `single_room` capture:

| Diagnostic | Result |
|---|---:|
| Depth frames | 1,715 |
| Odometry rows | 1,715 |
| Trajectory displacement | 3.179 m |
| Median frame translation | 7.88 mm |
| Mean frame translation | 8.45 mm |
| 95th percentile translation | 17.68 mm |
| Maximum frame translation | 24.71 mm |
| Median frame interval | 16.67 ms |
| Effective odometry rate | ~60 FPS |
| Confidence ≥ 1 ratio | 99.27% |
| Quaternion norm range | 0.99999986–1.00000012 |

These diagnostics provide a reproducible view of the quality and continuity
of the supplied sensor trajectory.

---

## 7. Point-Cloud Reconstruction

The reconstruction integrates depth observations over the supplied camera
trajectory.

The latest benchmark execution produced:

### Single Room

- Points: **416,127**
- Estimated footprint area: **31.64 m²**
- Estimated perimeter: **20.38 m**

### Floor-Only Capture

- Points: **1,313,474**
- Estimated footprint area: **168.15 m²**
- Estimated perimeter: **46.74 m**

### With-Ceiling Capture

- Points: **2,525,832**
- Estimated footprint area: **197.07 m²**
- Estimated perimeter: **51.08 m**

These are outputs of the current reconstruction and footprint-extraction
pipeline.

They are **not presented as ground-truth room measurements**.

The variation between capture conditions is itself useful diagnostic evidence:
the current multi-frame integration and footprint extraction remain sensitive
to capture trajectory and scene structure.

---

## 8. Registration and Drift Analysis

Pose-based integration is deterministic and provides a strong baseline, but
longer trajectories can accumulate geometric inconsistency.

The repository therefore includes an experimental ICP registration stage.

### Pairwise ICP experiment

Two reconstructed frames were aligned using:

1. Supplied odometry as the initial relative transform.
2. Point-cloud downsampling.
3. Point-to-point ICP.
4. Estimation of a corrective transformation.

Latest result:

| Metric | Result |
|---|---:|
| ICP fitness | **0.9882** |
| ICP RMSE | **0.0170 m** |
| ICP RMSE | **17.0 mm** |

The experiment demonstrates that local geometric registration can estimate a
correction to the odometry initialization.

It is intentionally **not** presented as evidence that the complete
reconstruction satisfies the required 1 cm repeatability gate.

A production implementation would extend this local correction into
validated multi-frame registration or pose-graph optimization.

---

## 9. Room Geometry

The current geometry stage converts the reconstructed point cloud into a
2D provisional room footprint.

The current pipeline performs:

1. Point-cloud aggregation.
2. Geometric filtering.
3. Dominant floor representation.
4. 2D projection.
5. Footprint extraction.
6. Area calculation.
7. Perimeter calculation.
8. Rendering.

The current rendered footprint should be interpreted as a **provisional
geometric reconstruction**, rather than a fully validated architectural
floor plan.

Future refinement would explicitly recover:

- Straight wall segments
- Wall intersections
- Door openings
- Window openings
- Room boundaries
- Room-to-room connectors
- Ceiling height

using geometric primitives constrained by benchmark measurements.

---

## 10. Multi-Room Representation

The canonical property model supports room-level reconstruction and
room-to-room adjacency:

```text
Property
│
├── Room A
│   ├── Walls
│   ├── Openings
│   ├── Measurements
│   └── Damage
│
├── Room B
│   ├── Walls
│   ├── Openings
│   ├── Measurements
│   └── Damage
│
└── Adjacency
    ├── Room A ↔ Room B
    └── Room B ↔ Room C
```

The output schema is defined in:

`schemas/output_schema.json`

The schema is treated as the internal canonical representation rather than
being presented as a copy of a proprietary external schema not included in
the supplied assessment materials.

---

## 11. Measurement and Uncertainty

Measurement output is designed to carry uncertainty explicitly.

A measurement can contain:

```json
{
  "value": 4.21,
  "unit": "m",
  "confidence_interval": [4.18, 4.24],
  "confidence_level": 0.95,
  "method": "sensor_calibrated"
}
```

The current implementation exposes tier-specific uncertainty handling.

Important distinction:

> Current uncertainty values are provisional engineering assumptions, not
> experimentally validated confidence intervals.

Empirical uncertainty calibration should be derived from the supplied
laser/tape ground truth and repeated captures.

The intended calibration process is:

```text
Ground Truth
     |
     v
Measured Dimension
     |
     v
Absolute Error
     |
     v
Error Distribution
     |
     v
Tier-Specific Calibration
     |
     v
Confidence Interval
```

---

## 12. Damage Analysis

The repository includes a conservative damage candidate detector.

The current detector is intended to identify visually unusual regions for
downstream review.

It is **not** presented as a trained semantic damage classifier.

This distinction is important because the assessment requires damage classes,
metric extents, and benchmark validation.

The intended future representation is:

```text
Damage
├── class
├── surface
├── region
├── metric_extent
├── confidence
└── concealed_damage_flag
```

Concealed-damage decisions should be rule-based and confidence-aware rather
than presented as confirmed physical observations without sufficient sensor
evidence.

---

## 13. Calibration Strategy

The assessment requires calibration at every capture tier.

The intended calibration framework separates:

### LiDAR

Use laser/tape measurements to estimate systematic and random error in
reconstructed dimensions.

### Video

Compare reconstructed wall and opening measurements against the same physical
ground truth.

### Photo

Estimate uncertainty under the lower-information capture condition and
propagate that uncertainty into the property model.

The current repository provides the calibration interface and uncertainty
representation, but does not claim experimentally validated calibration
curves without sufficient ground-truth observations.

---

## 14. Accuracy Policy

This repository deliberately separates three categories of results.

### Measured

Values directly generated by executable reconstruction or diagnostic scripts.

Examples:

- Point counts
- Trajectory statistics
- ICP fitness
- ICP RMSE
- Current reconstructed footprint values

### Provisional

Engineering assumptions or baseline estimates that have not yet been
validated against independent ground truth.

Examples:

- Tier-specific uncertainty defaults
- Candidate damage regions
- Provisional geometric footprints

### Pending Validation

Assessment requirements for which sufficient independent benchmark evidence
has not yet been established.

Examples:

- Opening-width accuracy
- Ceiling-height accuracy
- 1 cm repeatability
- Photo-tier accuracy
- Video-tier accuracy
- Multi-room adjacency
- Damage benchmark accuracy
- Consumer-app head-to-head comparison

No assessment accuracy gate is claimed as passed without independent
laser/tape ground truth.

---

## 15. Known Limitations

The current submission has the following known limitations:

- Full opening-width accuracy has not been experimentally validated.
- Ceiling-height accuracy has not been experimentally validated.
- Repeated-capture 1 cm repeatability has not been demonstrated.
- Full multi-room adjacency reconstruction is not yet validated.
- Complete photo-tier whole-property stitching remains incomplete.
- Video-tier metric accuracy remains a baseline.
- The photo tier does not yet have a validated whole-property reconstruction.
- Staged damage benchmark validation remains incomplete.
- Concealed-damage validation remains incomplete.
- Consumer-app head-to-head comparison remains pending.
- Complete laser/tape ground-truth comparison across all tiers remains pending.
- Current ICP is a local pairwise correction rather than a globally optimized
  pose graph.
- The current floor footprint is a provisional geometric estimate rather than
  a fully constrained architectural wall model.

These limitations are intentionally disclosed rather than replaced with
unsupported accuracy claims.

---

## 16. Fix Loop

The primary investigated failure mode was geometric drift and accumulated
registration error.

### Failure

Pose-based integration can accumulate spatial inconsistency over a
multi-frame trajectory.

### Investigation

The failure was investigated using:

- Odometry trajectory diagnostics.
- Frame-to-frame translation statistics.
- Single-frame reconstruction.
- Pairwise point-cloud registration.
- ICP correction.
- Before/after registration experiments.

### Root Cause

The baseline reconstruction relies directly on the supplied camera trajectory.
Any accumulated pose error is therefore propagated into the global point cloud.

### Fix

An experimental ICP correction stage was introduced using odometry as the
initial transformation.

### Evidence

Latest pairwise experiment:

```text
ICP fitness: 0.9882
ICP RMSE:    0.0170 m
```

The experiment demonstrates measurable local registration improvement.

The remaining engineering step is to validate a global registration strategy
against repeated captures and laser/tape ground truth.

---

## 17. Reproducibility

The repository is designed to run locally without requiring a hosted
reconstruction service.

### Install

```powershell
pip install -r requirements.txt
```

### Run LiDAR reconstruction

```powershell
python scripts_test_lidar.py
```

### Run benchmark captures

```powershell
python scripts_run_all.py
```

### Diagnose the supplied sensor trajectory

```powershell
python scripts_diagnose_lidar.py
```

### Run single-frame reconstruction

```powershell
python scripts_single_frame.py
```

### Run ICP evaluation

```powershell
python scripts_icp_test.py
```

### Run ICP-assisted reconstruction

```powershell
python scripts_icp_reconstruct.py
```

### Render the reconstructed footprint

```powershell
python scripts_render_plan.py
```

### Run the generic pipeline interface

```powershell
python run.py --tier lidar --input benchmarks/extracted/single_room/c00a170fe1 --output outputs/result.json
```

---

## 18. Repository Structure

```text
spatial-reconstruction/
│
├── benchmarks/
│   ├── raw/
│   ├── extracted/
│   ├── ground_truth/
│   └── results/
│
├── configs/
│
├── outputs/
│
├── protocols/
│   └── capture_protocol.md
│
├── reports/
│   ├── benchmark_status.md
│   ├── compliance_matrix.md
│   ├── fix_loop.md
│   └── technical_report.md
│
├── schemas/
│   └── output_schema.json
│
├── src/
│   ├── calibration.py
│   ├── damage.py
│   ├── geometry.py
│   ├── lidar.py
│   ├── measurements.py
│   ├── pipeline.py
│   ├── registration.py
│   ├── rendering.py
│   ├── room_reconstruction.py
│   └── stitching.py
│
├── tests/
│
├── .gitignore
├── requirements.txt
├── run.py
│
├── scripts_build_room.py
├── scripts_diagnose_lidar.py
├── scripts_icp_reconstruct.py
├── scripts_icp_test.py
├── scripts_render_plan.py
├── scripts_run_all.py
├── scripts_single_frame.py
├── scripts_test_lidar.py
└── scripts_visualize_lidar.py
```

---

## 19. Key Engineering Decisions

### LiDAR-first implementation

LiDAR provides the strongest metric signal among the supplied modalities.
Therefore the implementation prioritizes a reliable metric reconstruction
baseline before extending the same property representation to lower-information
photo and video inputs.

### Stock capture protocol

The submission uses a documented stock capture workflow rather than spending
the available development time building a custom iOS application.

### Explicit uncertainty

Measurements are designed to carry uncertainty rather than presenting every
geometric estimate as equally reliable.

### Reproducibility

The pipeline is executable locally using the supplied benchmark data and
does not depend on a hosted inference service.

### Honest benchmark reporting

Measured outputs, provisional engineering assumptions, and unvalidated
assessment gates are explicitly separated.

### Incremental failure analysis

The implementation uses sensor diagnostics and registration experiments to
identify geometric failure modes before introducing more complex global
optimization.

---

## 20. Current Status

The repository currently provides a working end-to-end LiDAR reconstruction
baseline:

```text
Raw Sensor Data
      ↓
Depth + Confidence
      ↓
Camera Calibration
      ↓
Pose-Based Reconstruction
      ↓
3D Point Cloud
      ↓
Geometric Footprint
      ↓
Measurements
      ↓
ICP Evaluation
      ↓
Rendered Output
```

The strongest experimentally demonstrated components are:

- Raw LiDAR data ingestion
- Metric depth back-projection
- Confidence-aware filtering
- Pose-based point-cloud reconstruction
- Sensor/trajectory diagnostics
- Pairwise ICP registration
- Geometric footprint extraction
- Area/perimeter estimation
- Reproducible benchmark execution
- Explicit uncertainty representation
- Failure analysis and documented correction

The remaining work is primarily benchmark validation and extension of the
same architecture to complete photo/video reconstruction, multi-room
stitching, openings, damage, and ground-truth-calibrated measurements.

---

## 21. Conclusion

This submission establishes a reproducible foundation for consumer spatial
reconstruction rather than treating individual outputs as unsupported
accuracy claims.

The current LiDAR path demonstrates that the supplied sensor streams can be
converted into a metric 3D representation and evaluated quantitatively.

The registration experiments further show that geometric correction can reduce
local alignment error, while the benchmark documentation makes the remaining
accuracy and product gaps explicit.

The architecture is intentionally modular so that validated calibration,
global registration, multi-room reconstruction, photo/video reconstruction,
opening detection, and damage analysis can be added without changing the
underlying property representation.

# Compliance Matrix

| Requirement | Status | Evidence |
|---|---|---|
| Route 2 capture protocol | Implemented | `protocols/capture_protocol.md` |
| Photo tier | Baseline | `src/pipeline.py` |
| Video tier | Baseline | `src/pipeline.py` |
| LiDAR tier | Implemented | `src/lidar.py` |
| Depth + confidence | Implemented | LiDAR reconstruction |
| Pose / intrinsics | Implemented | `odometry.csv` ingestion |
| Point-cloud reconstruction | Implemented | `scripts_test_lidar.py` |
| Floor-plan extraction | Implemented | `src/room_reconstruction.py` |
| Area measurement | Implemented | `src/measurements.py` |
| Perimeter measurement | Implemented | `src/measurements.py` |
| Rendered plan | Implemented | `scripts_render_plan.py` |
| Measurement uncertainty | Baseline | `src/calibration.py` |
| ICP registration | Implemented experimentally | `scripts_icp_test.py` |
| Ceiling reconstruction | Baseline | `single_scan_with_ceiling` |
| Opening detection | Not validated | — |
| Multi-room adjacency | Not validated | — |
| Damage classification | Baseline candidate detector | `src/damage.py` |
| Concealed damage | Not validated | — |
| Photo-tier whole-property stitching | Not validated | — |
| 1 cm repeatability gate | Not validated | — |
| Ground-truth accuracy gates | Not fully validated | `reports/benchmark_status.md` |
| Consumer-app comparison | Not completed | — |
| Fix loop | Implemented experimentally | `reports/fix_loop.md` |
| Reproducible scripts | Implemented | `scripts_*.py` |
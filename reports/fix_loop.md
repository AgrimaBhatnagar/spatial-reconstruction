# Fix Loop

## Failure
The odometry-fused LiDAR cloud shows visible registration streaking and unstable room envelopes.

## Evidence
The supplied capture has synchronized depth and odometry. Single-frame depth back-projection produces coherent indoor geometry. A sampled ICP comparison produced strong local overlap, but the resulting global fusion did not produce a stable room reconstruction.

## Root cause hypothesis
The depth-sensing frame and supplied odometry frame may require a validated fixed extrinsic transform. ICP without that calibration can improve local overlap while worsening global consistency.

## Shipped decision
Do not claim ICP as a production correction until extrinsic calibration is validated. Keep the odometry reconstruction as the reproducible baseline and surface registration as the main limitation.

## Predicted fix
Estimate/validate the fixed sensor extrinsic using benchmark data, then evaluate wall repeatability and dimensional error against laser/tape measurements.

## Reproduction
Baseline: `outputs/single_room_pointcloud.ply`
ICP experiment: `outputs/single_room_icp.ply`
Diagnostic: `scripts_icp_test.py`

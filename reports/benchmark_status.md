# Benchmark Status

## Supplied captures
- `single_room`
- `single_scan_floor_only`
- `single_scan_with_ceiling`

## Single-room raw observations
- 1,715 depth frames
- 1,715 confidence frames
- 1,715 odometry rows
- RGB video
- camera matrix
- IMU

Depth images are 192Ã—256 uint16. Confidence maps contain levels 0â€“2.

## Current status
Point clouds can be reconstructed for all three supplied captures. Geometry remains provisional because residual registration artifacts affect the fused envelope.

## Not claimed
Opening-width error, ceiling-height error, repeated-capture spread, photo/video wall error and consumer-app head-to-head score require independent benchmark measurements.

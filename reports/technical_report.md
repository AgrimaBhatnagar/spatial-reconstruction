# Technical Report

## Objective
Build a local multimodal reconstruction pipeline from handheld consumer capture producing room geometry, property adjacency, damage candidates and uncertainty-aware structured output.

## Capture
Route 2 uses a stock consumer capture workflow plus a written protocol.

## Reconstruction
LiDAR uses depth, confidence, camera intrinsics and supplied odometry. A single depth frame produces coherent indoor geometry. Multi-frame fusion currently shows residual registration artifacts; this is the principal limitation.

## Damage
The shipped detector identifies image-space anomalies as candidates and requires review. It does not claim semantic damage classification without labeled benchmark data.

## Uncertainty
Measurements support value, unit, confidence interval, confidence level, status and method. Current intervals are provisional model-uncertainty estimates, not empirical benchmark confidence.

## Validation
The supplied benchmark was inspected at raw-file level. Required opening, ceiling, wall, repeatability and head-to-head gates remain pending until independent ground truth/additional benchmark captures are available.

## Fix loop
The main failure is multi-frame registration. ICP was investigated but not promoted to production because local overlap did not guarantee stable global reconstruction.

## Engineering trade-off
The implementation prioritizes deterministic local execution, reproducibility, explicit uncertainty and graceful failure over an unvalidated learned reconstruction model.

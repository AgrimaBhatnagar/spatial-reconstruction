# Compliance Matrix

| Requirement | Status | Evidence |
|---|---|---|
| Stock capture route | PARTIAL | `protocols/capture_protocol.md` |
| Photo tier | PARTIAL | `src/pipeline.py` |
| Video tier | PARTIAL | `src/pipeline.py` |
| LiDAR tier | PARTIAL | `src/lidar.py` |
| Per-room plan | PARTIAL | `src/room_reconstruction.py` |
| Multi-room stitched plan | PENDING | adjacency contract exists; full benchmark not supplied |
| Walls with dimensions | PARTIAL | geometric baseline; not ground-truth validated |
| Ceiling height | PARTIAL | vertical extent baseline |
| Openings | PENDING | not benchmark validated |
| Damage regions/classes | PARTIAL | conservative candidate detector |
| Concealed damage rule | PARTIAL | `src/damage.py` |
| Scope line items | PARTIAL | output contract |
| Confidence intervals | PASS (schema) / PENDING (empirical calibration) | `src/measurements.py` |
| One-command processing | PARTIAL | `run.py` |
| JSON output | PASS | `schemas/output_schema.json` |
| Rendered plan | PASS (baseline) | `src/rendering.py` |
| Accuracy gates | PENDING | requires laser/tape ground truth |
| Repeatability | PENDING | requires repeated capture |
| Head-to-head | PENDING | requires consumer-app benchmark |
| Fix loop | PARTIAL | baseline failure and diagnosis documented |

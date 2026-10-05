$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path "src","reports","protocols","schemas","outputs","benchmarks\results" | Out-Null
@'
from __future__ import annotations
from dataclasses import dataclass, asdict
@dataclass
class ConfidenceInterval:
    value: float
    unit: str
    lower: float
    upper: float
    confidence_level: float = 0.95
    status: str = "provisional"
    method: str = "model_uncertainty"
def make_interval(value, unit, relative_uncertainty, *, status="provisional", method="model_uncertainty"):
    value=float(value); d=abs(value)*float(relative_uncertainty)
    return asdict(ConfidenceInterval(value,unit,max(0.0,value-d),value+d,0.95,status,method))
def measurement(name,value,unit,relative_uncertainty,*,status="provisional",method="model_uncertainty"):
    return {"name":name,"measurement":make_interval(value,unit,relative_uncertainty,status=status,method=method)}
'@ | Set-Content -Encoding UTF8 "src\measurements.py"
@'
from __future__ import annotations
import cv2
import numpy as np
DAMAGE_CLASSES=["surface_anomaly","crack_candidate","stain_candidate"]
def detect_damage_candidates(image, *, min_area_px=100, max_regions=25):
    if image is None:return []
    gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY); blur=cv2.GaussianBlur(gray,(5,5),0); residual=cv2.absdiff(gray,blur)
    _,mask=cv2.threshold(residual,18,255,cv2.THRESH_BINARY); k=np.ones((3,3),np.uint8)
    mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,k); mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,k)
    contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE); h,w=gray.shape[:2]; out=[]
    for c in sorted(contours,key=cv2.contourArea,reverse=True)[:max_regions]:
        area=float(cv2.contourArea(c))
        if area<min_area_px: continue
        x,y,bw,bh=cv2.boundingRect(c)
        out.append({"class":"surface_anomaly","bbox_px":[int(x),int(y),int(bw),int(bh)],"area_px":area,"extent_px":{"width":int(bw),"height":int(bh),"area":area,"image_width":int(w),"image_height":int(h)},"confidence":{"value":0.25,"status":"candidate_only","reason":"heuristic visual anomaly detector"},"requires_review":True})
    return out
def concealed_damage_flag(*, visible_damage_count, low_visibility, depth_confidence_low):
    flag=bool(low_visibility or depth_confidence_low)
    return {"flagged":flag,"rule":"Flag when visibility is low or depth confidence is low; do not infer concealed damage as confirmed damage.","visible_damage_count":int(visible_damage_count),"requires_human_inspection":flag}
'@ | Set-Content -Encoding UTF8 "src\damage.py"
@'
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
'@ | Set-Content -Encoding UTF8 "reports\compliance_matrix.md"
@'
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
'@ | Set-Content -Encoding UTF8 "reports\fix_loop.md"
@'
# Capture Protocol

## Route 2 — Stock capture workflow

### Photo tier
For each room take 2–8 handheld stills. Cover visible walls, corners, floor/ceiling transitions and openings. Keep one folder per room and avoid standing directly against walls.

### Video tier
Record continuously while walking slowly around the room. Keep the phone approximately chest height, maintain overlap between views and capture connectors between adjacent rooms.

### LiDAR tier
Use a supported Pro iPhone. Walk slowly with overlap between successive views, avoid sudden motion, and preserve raw depth, confidence, calibration and pose files.

### Ground truth
Independently measure wall lengths, opening widths, ceiling height and connector dimensions using laser/tape. Preserve raw measurements.

### Repeatability
Capture at least one room twice at the same tier using the same protocol without tuning the system between captures.
'@ | Set-Content -Encoding UTF8 "protocols\capture_protocol.md"
@'
# Spatial Reconstruction — Applied AI Engineer Case Study

Local reproducible multimodal spatial-reconstruction baseline for handheld photo, video and LiDAR capture.

## Architecture
Capture → modality adapter → reconstruction → room representation → damage analysis → uncertainty → JSON/rendering.

Canonical representation: `Property -> Rooms -> Walls / Openings / Measurements / Damage -> Adjacency`.

## LiDAR
Depth + confidence + camera matrix + odometry → metric back-projection → filtering → geometric room analysis → JSON/rendered plan.

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
'@ | Set-Content -Encoding UTF8 "README.md"
@'
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
'@ | Set-Content -Encoding UTF8 "reports\technical_report.md"
@'
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

Depth images are 192×256 uint16. Confidence maps contain levels 0–2.

## Current status
Point clouds can be reconstructed for all three supplied captures. Geometry remains provisional because residual registration artifacts affect the fused envelope.

## Not claimed
Opening-width error, ceiling-height error, repeated-capture spread, photo/video wall error and consumer-app head-to-head score require independent benchmark measurements.
'@ | Set-Content -Encoding UTF8 "reports\benchmark_status.md"
@'
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "title":"Spatial Reconstruction Output",
  "type":"object",
  "required":["property","rooms","adjacency","capture","status"],
  "properties":{
    "property":{"type":"object","required":["id"],"properties":{"id":{"type":"string"}}},
    "capture":{"type":"object","required":["tier"],"properties":{"tier":{"enum":["photo","video","lidar"]},"source":{"type":"string"}}},
    "rooms":{"type":"array"},
    "adjacency":{"type":"array"},
    "scope_items":{"type":"array"},
    "status":{"type":"object"}
  }
}
'@ | Set-Content -Encoding UTF8 "schemas\output_schema.json"

Write-Host "FINALIZER COMPLETE" -ForegroundColor Green
Write-Host "Now run:" -ForegroundColor Yellow
Write-Host "python -m py_compile src\measurements.py src\damage.py src\room_reconstruction.py run.py"
Write-Host "python scripts_run_all.py"
Write-Host "git add ."
Write-Host 'git commit -m "feat: complete uncertainty damage compliance and benchmark outputs"'
Write-Host "git push"

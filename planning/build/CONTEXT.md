---
stage: shared
owner: build-concept
status: in_progress
revision: 3
created: 2026-11-02T15:28
updated: 2026-11-02T16:31
input: VLT/10-intake.md@2
---

# CONTEXT — Ubiquitous Language

_The project's shared domain dictionary. Developers and agents use these terms — and only these — for the same things, in prose, identifiers, file names and tests. Seeded from the brief's shared vocabulary; every concept stage appends its delta. Entries are never deleted, only marked obsolete._

| Term | Meaning | In code | Introduced by | Status |
| --- | --- | --- | --- | --- |
| cube | the tracking volume; origin and axes defined by the camera calibration; all distances in mm | `Cube`, cube coordinates | VLT | active |
| ball | the tracked object (≈ 5 cm) swinging on a string (≈ 1 m) | `ball` | VLT | active |
| spot | the laser spot as seen by the cameras | `spot` | VLT | active |
| camera node | Pi 3 with one camera; detects ball and spot, sends observations | `camera` | VLT | active |
| control node | Pi 3 that fuses observations, predicts, computes targets, aiming error and hit rate; hosts the arming button | `control` | VLT | active |
| galvo node | Pi 3 that turns targets into mirror angles, drives the converter board, switches the laser | `galvo` | VLT | active |
| converter board | hardware between galvo node and galvo driver producing the analog X/Y signals | `converter` | VLT | active |
| observation | one camera's result for one frame: ball and spot image positions plus exposure time | `Observation` | VLT | active |
| ball state | fused 3D ball position (and velocity) at a time | `BallState` | VLT | active |
| target | cube point the galvo node shall aim at, with placement time and laser flag | `Target` | VLT | active |
| aiming error | distance between measured spot and measured ball centre | `aiming_error_mm` | VLT | active |
| hit | fusion step with the spot seen and within the hit radius (25 mm) of the ball centre | `hit` | VLT | active |
| run | from release (amplitude > 100 mm) until amplitude < 50 mm | `Run` | VLT | active |
| hit rate | hits ÷ fusion steps within a run | `hit_rate` | VLT | active |
| amplitude | maximum horizontal deflection from rest over the last swing | `amplitude_mm` | VLT | active |
| armed | state in which the system may switch the laser on | `armed` | VLT | active |
| safe state | laser off; targets ignored until re-armed | `SAFE` | VLT | active |
| degraded | tracking with exactly two camera nodes delivering the ball | `DEGRADED` | VLT | active |
| camera calibration / galvo calibration | stored results of the manual calibration procedures | `camera_calibration`, `galvo_calibration` | VLT | active |
| reference data set | recorded, annotated frames of all cameras that the automated tests run against | `reference_data` | VLT | active |
| monitoring laptop | observe-only sink for monitoring data | `monitor` | VLT | active |
| kill switch | physical switch cutting the laser supply independent of software | — | VLT | active |

## Naming rules

- Units: distances in mm, times in ns of the shared PTP clock (`int64`), image positions in px — suffixes `_mm`, `_ns`, `_px` in identifiers.
- Node types are lower-case nouns (`camera`, `control`, `galvo`) and name the `src/` subfolders.
- Messages and data structures are nouns in PascalCase (`Observation`, `Target`); functions are verbs.

## Notes (human)

<!-- Off limits for all skills. Copied verbatim on every rewrite. -->

---
stage: shared
owner: build-concept
status: in_progress
revision: 6
created: 2026-11-02T15:28
updated: 2026-11-10T00:00
input: VLT/10-intake.md@2, VLT/20-concept.md@6
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
| aiming error | distance in mm from the fused ball centre to the laser beam line (galvo origin → spot in 3D); unmeasurable when the spot cannot be placed in 3D (ADR-VLT-005) | `aiming_error_mm` | VLT | active |
| hit | fusion slot in which, in at least one camera that sees both, the spot lies inside the ball's image disc (ADR-VLT-005) | `hit` | VLT | active |
| run | from release (ball displaced > 100 mm starts moving) until amplitude < 50 mm; aborted when the safe state ends it (ADR-VLT-006) | `Run` | VLT | active |
| hit rate | time with a hit ÷ run duration; gaps count as misses (ADR-VLT-006) | `hit_rate` | VLT | active |
| amplitude | maximum horizontal deflection from rest over the last swing | `amplitude_mm` | VLT | active |
| armed | state in which the system may switch the laser on | `armed` | VLT | active |
| safe state | laser off; targets ignored until re-armed | `SAFE` | VLT | active |
| degraded | tracking with exactly two camera nodes delivering the ball | `DEGRADED` | VLT | active |
| camera calibration / galvo calibration | stored results of the manual calibration procedures | `camera_calibration`, `galvo_calibration` | VLT | active |
| reference data set | recorded, annotated frames of all cameras that the automated tests run against | `reference_data` | VLT | active |
| monitoring laptop | observe-only sink for monitoring data | `monitor` | VLT | active |
| kill switch | physical switch cutting the laser supply independent of software | — | VLT | active |
| restart session | one sender-process incarnation; sequence numbers are interpreted within it, preventing pre-restart messages from becoming current again (F-VLT-23) | `session_id` | VLT | proposed — PM review pending |
| setup revision | identity of the installation configuration and calibration set that communicating nodes must agree on (F-VLT-24) | `setup_revision` | VLT | proposed — PM review pending |
| galvo status | the galvo node's report to the control node: actual laser state with reason, applied target, galvo restart session (F-VLT-25) | `GalvoStatus` | VLT | proposed — PM review pending |
| grandmaster | the node whose clock all others follow by PTP; proposed: the control node (NF-VLT-24) | `grandmaster` | VLT | proposed — PM review pending |
| ground state | the defined state a node starts in: laser off, converter at centre, unarmed, no history (F-VLT-28) | `GROUND` | VLT | proposed — PM review pending |
| state message | a message whose newest valid copy replaces the previous one; never queued or retransmitted (NF-VLT-27) | — | VLT | proposed — PM review pending |
| transaction | an end-to-end real-time chain with its deadline class: T1 tracking (firm), T2 target-loss shutdown (hard), T3 unsafe-condition shutdown (hard), T4 monitoring (soft), T5 camera reintegration (no deadline) (NF-VLT-26, ADR-VLT-008) | `T1` … `T5` | VLT | active |
| camera status | per camera: absent, unsynced, ball not seen, ball seen (F-VLT-11) | `CameraStatus` | VLT | active |
| fusion slot | one period of the fixed-rate fusion, aligned to the shared clock (ADR-VLT-009) | `FusionSlot` | VLT | active |
| arming epoch | counter incremented at every arming; after a safety fault the galvo node needs a newer one (ADR-VLT-007) | `arm_epoch` | VLT | active |
| hit radius | obsolete 2026-11-10 — replaced by the ball's image disc (ADR-VLT-005) | `hit_radius_mm` | VLT | obsolete |

## Naming rules

- Units: distances in mm, times in ns of the shared PTP clock (`int64`), image positions in px — suffixes `_mm`, `_ns`, `_px` in identifiers.
- Node types are lower-case nouns (`camera`, `control`, `galvo`) and name the `src/` subfolders.
- Messages and data structures are nouns in PascalCase (`Observation`, `Target`); functions are verbs.

## Notes (human)

<!-- Off limits for all skills. Copied verbatim on every rewrite. -->

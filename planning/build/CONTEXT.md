---
stage: shared
owner: build-concept
status: in_progress
revision: 15
created: 2026-11-02T15:28
updated: 2026-11-12T14:00
input: VLT/10-intake.md@2, VLT/20-concept.md@17
---

# CONTEXT — Ubiquitous Language

_The project's shared domain dictionary. Developers and agents use these terms — and only these — for the same things, in prose, identifiers, file names and tests. Seeded from the brief's shared vocabulary; every concept stage appends its delta. Entries are never deleted, only marked obsolete._

| Term | Meaning | In code | Introduced by | Status |
| --- | --- | --- | --- | --- |
| cube | the tracking volume and its coordinate system: right-handed, in mm; origin at the floor corner marked "0" on the frame, x and y along the floor edges marked "X" and "Y", z up | `Cube`, cube coordinates | VLT | active |
| ball | the tracked object (≈ 5 cm) swinging on a string (≈ 1 m) | `ball` | VLT | active |
| spot | the laser spot as seen by the cameras | `spot` | VLT | active |
| camera node | Pi 3 with one camera; detects ball and spot, sends observations | `camera` | VLT | active |
| control node | Pi 3 that fuses observations, predicts, computes targets, aiming error and hit rate; decides arming, disarming, galvo scan and arming check in software (ADR-VLT-013; the arming button was removed 2026-11-10) | `control` | VLT | active |
| galvo node | Pi 3 that turns targets into mirror angles, drives the converter board, switches the laser | `galvo` | VLT | active |
| converter board | hardware between galvo node and galvo driver producing the analog X/Y signals: a PCM5102A I2S stereo DAC (ADR-VLT-015) | `converter` | VLT | active |
| observation | one camera's result for one frame: ball and spot image positions plus exposure time | `Observation` | VLT | active |
| ball state | fused 3D ball position (and velocity) at a time | `BallState` | VLT | active |
| target | cube point the galvo node shall aim at, with placement time and laser flag | `Target` | VLT | active |
| aiming error | distance in mm from the fused ball centre to the laser beam line (galvo origin → spot in 3D); unmeasurable when the spot cannot be placed in 3D (ADR-VLT-005) | `aiming_error_mm` | VLT | active |
| hit | fusion slot in which, in at least one camera that sees both, the spot lies inside the ball's image disc (ADR-VLT-005) | `hit` | VLT | active |
| run | from release (ball displaced > 100 mm starts moving) until amplitude < 50 mm; aborted when the safe state ends it (ADR-VLT-006) | `Run` | VLT | active |
| hit rate | time with a hit ÷ run duration; gaps count as misses (ADR-VLT-006) | `hit_rate` | VLT | active |
| rest position | the ball centre while the ball hangs still; measured once by hand, updated by the system when the ball hangs still near it (F-VLT-7) | `rest_position_mm` | VLT | active |
| amplitude | maximum horizontal deflection from rest over the last swing | `amplitude_mm` | VLT | active |
| armed | state in which the system may switch the laser on | `armed` | VLT | active |
| safe state | laser off; targets ignored until re-armed | `SAFE` | VLT | active |
| degraded | tracking with exactly two camera nodes delivering the ball | `DEGRADED` | VLT | active |
| camera calibration / galvo calibration | stored results of the automatic calibrations: cameras from the frame markers at every start, galvo by an on-demand scan (ADR-VLT-012) | `camera_calibration`, `galvo_calibration` | VLT | active |
| reference data set | recorded, annotated frames of all cameras that the automated tests run against | `reference_data` | VLT | active |
| monitoring laptop | observe-only sink for monitoring data; required to operate the demo and the only status display (F-VLT-40) | `monitor` | VLT | active |
| kill switch | physical switch cutting the laser supply independent of software; the operator's only physical control: press = disarm, release = re-arming allowed (ADR-VLT-013) | — | VLT | active |
| restart session | one sender-process incarnation; sequence numbers are interpreted within it, preventing pre-restart messages from becoming current again (F-VLT-23) | `session_id` | VLT | proposed — PM review pending |
| setup revision | identity of the installation configuration and calibration set that communicating nodes must agree on (F-VLT-24) | `setup_revision` | VLT | proposed — PM review pending |
| galvo status | the galvo node's report to the control node: actual laser state with reason, applied target, galvo restart session (F-VLT-25) | `GalvoStatus` | VLT | proposed — PM review pending |
| grandmaster | the node whose clock all others follow by PTP; proposed: the control node (NF-VLT-24) | `grandmaster` | VLT | proposed — PM review pending |
| ground state | the defined state a node starts in: laser off, converter at centre, unarmed, no history (F-VLT-28) | `GROUND` | VLT | proposed — PM review pending |
| state message | a message whose newest valid copy replaces the previous one; never queued or retransmitted (NF-VLT-27) | — | VLT | proposed — PM review pending |
| transaction | an end-to-end real-time chain with its deadline class: T1 tracking (firm), T2 target-loss shutdown (hard), T3 unsafe-condition shutdown (hard), T4 monitoring (soft), T5 camera reintegration (no deadline), T6 effect supervision (hard, 500 ms + 100 ms), T7 galvo software hang (hard, 1 s) (NF-VLT-26, ADR-VLT-008/018) | `T1` … `T7` | VLT | active |
| camera status | per camera: absent, unsynced, ball not seen, ball seen (F-VLT-11) | `CameraStatus` | VLT | active |
| marker map | ArUco marker IDs on the cube frame with their measured cube coordinates; the reference for camera calibration (ADR-VLT-012) | `marker_map` | VLT | active |
| galvo scan | the automatic galvo calibration: grid projected onto floor and walls, measured by the cameras; started by the control node when no valid calibration exists or the arming check fails (F-VLT-13, ADR-VLT-013) | `galvo_scan` | VLT | active |
| arming check | 3 projected check points measured before every arming (F-VLT-31) | `arming_check` | VLT | active |
| health overview | the monitoring screen with per-node values, limits and highlighting (F-VLT-37) | `health` | VLT | proposed — PM review pending |
| chain delay statistics | per-stage and end-to-end delay of the tracking chain with min, max, mean, jitter, percentiles over last second, run and session (F-VLT-39) | `ChainStats` | VLT | proposed — PM review pending |
| session recording | bounded, image-free recording of the loop's inputs and decisions, replayable offline (F-VLT-32) | `session_recording` | VLT | proposed — PM review pending |
| dry run | configured mode with laser disabled or galvo disabled (F-VLT-33) | `dry_run` | VLT | proposed — PM review pending |
| fusion slot | one period of the fixed-rate fusion, aligned to the shared clock (ADR-VLT-009) | `FusionSlot` | VLT | active |
| arming epoch | counter incremented at every arming; after a safety fault the galvo node needs a newer one (ADR-VLT-007) | `arm_epoch` | VLT | active |
| safety latch | safe state that persists after an alarm or repeated safety faults until the kill switch is pressed and released (F-VLT-21) | `safety_latch` | VLT | proposed — PM review pending |
| arming button | obsolete 2026-11-10 — removed; arming is done by the control node software (ADR-VLT-013) | — | VLT | obsolete |
| release | start of a run: the ball, held still > 100 mm from rest, starts moving towards rest (F-VLT-7) | `release` | VLT | proposed — Gate 1 pending |
| operating mode | start, calibrating galvo, ready, arming check, tracking (normal / degraded), safe (latched or not) (F-VLT-41) | `Mode` | VLT | proposed — Gate 1 pending |
| optical-effect watchdog | while the laser is on, a measurable spot must be seen within 500 ms and then every 500 ms; on expiry the laser is off within 100 ms (F-VLT-42, ADR-VLT-019) | — | VLT | proposed — Gate 1 pending |
| reference installation | proposed physical baseline: 800 mm cube, nominal rest centre (400, 400, 300) mm, white ball, grey floor and far walls, two elevated side views and an offset overhead view (ADR-VLT-016) | — | VLT | proposed — Gate 2 |
| camera profile | VLT-CAM-1: 640 × 480, 80–120 fps, startup exposure then locked, timestamp mapping and rectification (ADR-VLT-020); camera model not selected | `profile_id` | VLT | proposed — Gate 2 |
| calibration identity | per-camera hash of a validated calibration result, separate from the installation identity `setup_revision` (ADR-VLT-020) | `calibration_id` | VLT | proposed — Gate 2 |
| startup preparation | laser-off Start phase, separate from galvo scan attempts (ADR-VLT-017) | — | VLT | proposed — change request after Gate 1 |
| reaction matrix | per error: detection, reaction, time limit, log (NF-VLT-34) | — | VLT | proposed — Gate 1 pending |
| hit radius | obsolete 2026-11-10 — replaced by the ball's image disc (ADR-VLT-005) | `hit_radius_mm` | VLT | obsolete |

## Naming rules

- Units: distances in mm, times in ns of the shared PTP clock (`int64`), image positions in px — suffixes `_mm`, `_ns`, `_px` in identifiers.
- Node types are lower-case nouns (`camera`, `control`, `galvo`) and name the `src/` subfolders.
- Messages and data structures are nouns in PascalCase (`Observation`, `Target`); functions are verbs.

## Notes (human)

<!-- Off limits for all skills. Copied verbatim on every rewrite. -->

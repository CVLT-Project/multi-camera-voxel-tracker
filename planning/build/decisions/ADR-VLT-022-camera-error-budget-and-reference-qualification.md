# ADR-VLT-022 — Combined error budget and camera-team verification package

- **Status:** proposed · 2026-11-12 · M3 groundwork from the camera-team review; decided as a team in the M3 consistency review (Gate 2). Verification plan only; no recordings, annotations or measurements exist yet.
- **Feature:** VLT
- **Would resolve (if accepted):** OQ-14 budget/test-method choices and reference-data responsibilities.
- **Detailed fixtures:** ../VLT/camera-reference-plan.json

## Decision

| Contribution | Allocation |
| --- | --- |
| Perception: detection, calibration and triangulation | ≤ 10 mm, p99, for valid reconstructed samples with all three and every camera pair |
| Prediction and timing together | ≤ 8 mm, p99 |
| Galvo placement | ≤ 5 mm, p99 |
| Reference uncertainty and integration reserve | 2 mm |
| Nominal ball radius | 25 mm |

The first three contributions total 23 mm; the 2 mm reserve closes the nominal radius. This tightens the previous 15 mm static two-camera allowance to 10 mm, and the previous 10 mm median / 20 mm p95 prediction allowances to 8 mm p99, because the earlier individual bounds did not establish a combined ball-radius budget. These are selected qualification requirements, not demonstrated performance.

Measure component errors on the same declared scenario population. Separately verify joint aiming-error p95 ≤ 23 mm and the existing time-weighted hit rate ≥ 80 % in three consecutive physical runs with all cameras and with each pair. Missing/rejected/unmeasurable slots remain misses or explicitly unmeasurable; never remove them to improve the hit rate. Do not add independently measured percentiles and claim a proven system bound. The 80 % run criterion remains decisive; the allocation is not a substitute for that test. If the delivered ball radius differs, recheck the budget against the measured radius.

## Reference method and data

Use the ten explicit static positions and the minimum frame/run/case counts in camera-reference-plan.json. Static coordinates are independently measured with ≤ 2 mm uncertainty. Dynamic image centres/radii/spots are manually annotated and triangulated offline with the independently static-validated calibration. This is independent of production detection/fusion, not an independent-sensor truth claim; establish and record reference uncertainty ≤ 2 mm or the take cannot qualify absolute accuracy. Synthetic straight/circular/accelerating sequences provide exact time/position truth for prediction and timing perturbations without a pendulum assumption.

Record three full reference swings at 150/225/300 mm initial deflection, laser-on/off/no-ball, on/off-ball spot, occlusion and outward-carry/pause cases. Store lossless frames, timestamps, setup/calibration/profile IDs, run boundaries, measured coordinates and hashes. A second reviewer checks ≥ 10 % and at least 100 frames per camera; centre/radius/spot disagreements > 1 px are adjudicated. Uncertain labels are marked explicitly and cannot silently become good samples or hits.

Normal operation stores no images. Explicit reference recording has at most 64 MiB buffer per camera and a 16 GiB full-archive cap; overflow counts drops and invalidates/stops the take without blocking tracking. The repository contains the reviewed reference pack, labels, replay observations and hashes; bulk raw takes remain in a bounded local project archive. This refines the earlier unrestricted “all data in the repository” wording. A complete qualifying recording is still required; a size-truncated run is not accepted.

## Ownership and sign-off evidence

- Sensor and actuator modules: camera selection/settings, capture/detection/calibration qualification and reference recording.
- System design: common-time conversion, validity/latency checks and joint error integration.
- Integration support: measured marker map, manifest/schema checks and reproducible replay.
- Requirements and product owner: reviewed annotations/reference uncertainty and acceptance results.

The handoff consists of reproducible settings, calibrated geometry/IDs, schema-valid observations and restart tests, reviewed reference package, and the loaded 10-minute rate/CPU/RAM/timing/optical report. Hardware tests remain pending the camera and real setup; planning decisions are complete, not experimental results.

## Traces to

F-VLT-1/2/3/4/5/6/7/12/17/22/24/32/39/42, NF-VLT-1/17/18/19/21/22/29/32, OQ-1/14, ADR-VLT-005/006/020/021

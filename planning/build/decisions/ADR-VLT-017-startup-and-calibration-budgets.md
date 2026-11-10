# ADR-VLT-017 — Separate startup preparation and galvo calibration budgets

- **Status:** decided · 2026-11-10 · user requested resolution of the startup ambiguity; numeric targets remain to be validated. Full Gate 1 remains pending.
- **Feature:** VLT
- **Amends:** F-VLT-8/13/28/31/41, ADR-VLT-012/013

## Context

F-VLT-28 required Ready within 60 s and laser-off throughout startup. A missing galvo calibration also starts F-VLT-13's laser-on scan, which can take 60 s per attempt. Those statements did not distinguish startup preparation from calibration.

## Decision

1. **Start** is laser-off preparation: configuration, clock synchronization and camera calibration. In the healthy reference startup test it finishes within 60 s of t0, the start of the last of the five node software processes. Its exit enters Ready if the saved galvo calibration is valid, otherwise the explicit Calibrating galvo mode.
2. **Each galvo scan attempt has a separate 60 s total budget**, including completion/failure, necessary laser-off and transition to Ready, the next attempt or Safe. Reserve up to 100 ms for shutdown at an unsuccessful attempt's end; do not add it beyond the attempt budget. Quicker F-VLT-26/42 and kill-switch shutdowns take precedence.
3. With the default two attempts the first-start bounds are: Ready within 60 s with a valid saved calibration; within 120 s after a successful first scan; within 180 s after success on the second attempt. Two failures end in Safe with laser off by 180 s, no third attempt until restart. In general the bound is 60 s + N × 60 s for configured maximum N; this does not promise successful calibration.
4. Scan requires valid configuration/limits, released kill switch and at least two calibrated/synchronized cameras able to measure the scan. It does not require a valid ball state or previous galvo calibration. Boot/Start itself never emits.
5. Ready means valid setup/calibrations and readiness except for the ball. The later hold-off and ≤ 1 s Arming check are outside the startup-to-Ready bound. Failed or interrupted prerequisites keep the system unarmed with diagnostics; the healthy-start acceptance bound does not promise readiness while the kill switch is held or a fault prevents calibration.
6. Missing optical effect during a scan/check follows ADR-VLT-019: laser-off and failed attempt/check, with bounded retries. This failure alone does not set a tracking-alarm latch.

## Rationale

Separate named phases preserve the existing 60 s preparation and 60 s scan targets without forbidding the calibration's necessary emission or silently adding scan time to a 60 s total. Including failure shutdown/transition in each attempt avoids an unbudgeted gap between retries.

## Acceptance

Test saved calibration, success on attempt one, forced failure then success on attempt two, and two failures in three node startup orders. Log t0, every phase/attempt entry and exit, and Ready/Safe; independently check laser state. No boot/Start pulse, ≤ 60 s per attempt including off/transition, and the 60/120/180 s totals above. A held kill switch prevents scan/arming and produces the existing diagnostic.

Camera model, exposure, timestamp conversion, frame/fusion periods and measured feasibility remain OQ-1/OQ-12; this decision supplies targets and phase semantics, not camera measurements.

## Traces to

F-VLT-8, F-VLT-12/13/24/28/31/35/41/42, NF-VLT-26/34, ADR-VLT-012/013/019

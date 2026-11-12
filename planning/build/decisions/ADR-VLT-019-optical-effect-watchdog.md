# ADR-VLT-019 — Bounded emission without a measurable optical effect

- **Status:** proposed · 2026-11-12 · from the camera-team review (no defined response to an unmeasurable spot); decided with Gate 1; 500 ms is a selected policy limit, physical feasibility remains unverified.
- **Feature:** VLT
- **Adds:** F-VLT-42
- **Amends:** F-VLT-8/13/21/29/31 and ADR-VLT-007/012/013/015

## Context

F-VLT-6 correctly reports an unmeasurable aiming error when the spot cannot be placed in 3D. F-VLT-26 only reacted to a measurable large error or outside-cube spot, so a continuously missing/unusable spot had no explicit emission timeout. Calibration also intentionally operates without a valid ball state.

## Decision

- In every laser-on scan/check/Tracking episode start an optical-effect watchdog at the first laser-on placement. A current measurable effect must be accepted within **500 ms** and then at least every 500 ms while the laser remains on.
- In Tracking, current ball state and a measurable aiming error under F-VLT-6 are required. A spot on the ball can use the existing single-camera ray/sphere geometry; a spot off the ball needs at least two camera views. In scan/check, at least two cameras triangulate the spot; no ball state is required.
- Missing spot, one-camera off-ball spot, invalid geometry, stale/expired/duplicate/rejected data and mismatched setup cannot refresh the watchdog. “Unmeasurable” never counts as zero error or good evidence. Camera-dependent freshness and exposure conversion remain OQ-12, rather than being guessed here.
- Measure elapsed time monotonically. Clock corrections, new targets or mode changes with the laser still on cannot restart/extend the timer. An accepted current measurable effect update refreshes it; confirmed actual laser-off ends the episode. Account for the original placement time when an on-status report arrives later.
- On expiry request off immediately; physical off must occur within **100 ms**, hence **≤ 600 ms** from the first laser-on placement or last accepted current measurable effect update (T6). Only updates accepted before the local deadline refresh it; timeout takes precedence over a simultaneous/late update. Once expired, a late measurement cannot cancel that off/failure decision.
- **Tracking:** alarm and latched Safe; apply F-VLT-21's kill-switch reset and normal re-arming prerequisites.
- **Calibrating galvo:** fail/abort the current attempt, switch off before retry and apply F-VLT-13's existing maximum two consecutive attempts. Observation loss alone is not a tracking-alarm latch; exhaustion ends in Safe and needs restart before further scans.
- **Arming check:** fail, switch off, refuse arming and enter the existing bounded scan path (F-VLT-31). The overall ≤ 1 s check budget still applies.
- Faster ball-loss, clock/sync, kill-switch, local output-stop or other shutdown rules take precedence. Actual laser-off periods do not raise a missing-spot alarm. A detector/exposure requirement is not derived from the 500 ms policy: the real camera still has to demonstrate that these rules and the existing tracking targets can coexist.

## Configuration and evidence

The 500 ms watchdog is configurable for test profiles only (1…500 ms); the demo uses 500 ms. It is separate from the 500 ms large-error qualification of F-VLT-26. Each reset requires accepted current evidence, not simply receipt of any observation. Camera readout, frame rates and source-age limits remain open until OQ-1/OQ-12; names of configuration keys are architecture.

Log mode, watchdog origin, deadline, trigger reason, off request and reported off time. Independent physical off measurements remain required; node reports alone do not establish the bound.

## Acceptance

Replay and target tests cover absence from the first emission, later loss, one-camera off-ball spot, invalid geometry, stale/duplicate/rejected observations, clock step, target/mode changes, recovery before expiry and late evidence after expiry. Verify mode-specific outcomes, expiry at 500 ms, physical off by the ≤ 600 ms T6 bound, no alarm while off, no scan retry without off, and no bypass of faster shutdowns. Repeat scan/check cases with no ball to establish their intended exception. Actual optical/timing feasibility remains a camera-dependent verification item.

## Rationale

A time-based policy provides a finite bound without inventing a camera model or a number of missed frames. Distinguishing normal calibration-attempt failure from a Tracking alarm preserves the existing automatic scan/retry behavior.

## Traces to

F-VLT-6/8/11/13/21/22/23/24/26/29/31/35/41/42, NF-VLT-23/26/29/34, OQ-1/12/14, ADR-VLT-007/012/013/015/018

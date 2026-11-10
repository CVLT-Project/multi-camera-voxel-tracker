# ADR-VLT-009 — Time-triggered fusion; galvo aims at the placement time

- **Status:** accepted · 2026-11-10 · decided by the sponsor (OQ-15)
- **Feature:** VLT

## Context

The cadence of the loop was undefined, so the number of fusion steps, the load per channel and the phase relation between cameras were undefined too.

## Decision

- The control node runs fusion at a fixed period `fusion_period_ms`, aligned to the shared clock; every period is one fusion slot (ADR-VLT-006).
- Camera frames are phase-aligned to the shared clock if the camera stack allows it; otherwise cameras run free and fusion interpolates by exposure time.
- The galvo node applies each target at its `t_place_ns` and, between targets, interpolates at its own output rate using the target's velocity (and acceleration, ADR-VLT-011); it never extrapolates beyond `t_valid_until_ns`.

## Rationale

A fixed period makes scoring, load and phase analysable; aiming at the placement time removes jitter in transmission from the aim.

## Consequences

- F-VLT-3, F-VLT-5, F-VLT-7 rewritten; `Target` gets `velocity` and `acceleration`; config `fusion_period_ms` (value open, OQ-1).
- The galvo output rate and the interpolation are part of the T1 budget (NF-VLT-18).

## Traces to

F-VLT-3, F-VLT-4, F-VLT-5, F-VLT-7, F-VLT-22, NF-VLT-18, NF-VLT-27

**Profile follow-up (ADR-VLT-021):** fusion_period_ms is now 10, placement is requested 5 ms after the slot, source-use horizon is 30 ms, and expiry is min(t_place + 1 ms, source + 30 ms), exclusive. Camera capture is the selected 80–120 fps profile with timestamp alignment. Earlier wording that the period value was open is superseded.

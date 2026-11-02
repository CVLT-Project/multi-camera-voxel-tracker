# ADR-VLT-004 — Manual calibration in v1

- **Status:** accepted · 2026-11-02 · decided by the sponsor during intake (grilling #19)
- **Feature:** VLT

## Context

Triangulation needs every camera's intrinsic and extrinsic parameters in cube coordinates; aiming needs the mapping from cube coordinates to mirror angles. The cameras see the spot, so the galvo mapping could be measured automatically.

## Decision

v1 calibrates cameras and galvo with manual procedures (target object for the cameras; operator-guided procedure for the galvo). Results are stored as files and reused until recalibrated. Automatic galvo calibration via the spot is deferred to a later version — only if the cameras see the spot reliably.

## Rationale

Manual calibration does not depend on spot visibility, which is itself an open risk (OQ-1, OQ-2, OQ-7).

## Consequences

- F-VLT-12, F-VLT-13 are operator procedures with stored results.
- A drifting setup shows up as aiming error on the display (U-VLT-1); the recalibration hint (U-VLT-3) was dropped at the PM review.

## Traces to

F-VLT-12, F-VLT-13

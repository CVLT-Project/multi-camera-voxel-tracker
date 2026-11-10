# ADR-VLT-005 — Hit = beam hits the ball; aiming error = distance of the beam from the ball centre

- **Status:** accepted · 2026-11-10 · decided by the sponsor (OQ-9)
- **Feature:** VLT

## Context

The hit radius (25 mm) equals the ball radius. Measured as a 3D distance from the spot to the ball centre, a perfectly placed spot on the ball surface sits on the threshold, so the hit rate would be noise. Only cameras on the laser's side see the spot; a rule needing two cameras on the spot would rarely be measurable.

## Decision

- **Hit:** in at least one camera whose observation contains both ball and spot, the spot's image position lies inside the ball's image disc (distance to the ball centre ≤ `radius_px`). A spot inside the disc is on the ball: a spot on the background behind the ball would be hidden by it.
- **Aiming error (mm):** distance from the fused ball centre to the laser beam line (galvo origin from the galvo calibration → spot in 3D). The spot in 3D is the near intersection of a camera's spot ray with the ball sphere when the spot is on the ball, or the triangulated spot when at least two cameras see it off the ball. Otherwise the aiming error is *unmeasurable* and reported as such (`null`), never as 0.

## Rationale

Matches the demo's meaning ("the laser is on the ball"), is measurable with one camera, and gives a meaningful mm value on and off the ball.

## Consequences

- F-VLT-6, F-VLT-7 and the glossary are rewritten; `hit_radius_mm` is replaced by `ball_radius_mm` (sphere for the intersection).
- The galvo calibration must provide the galvo origin (beam pivot) in cube coordinates (F-VLT-13).
- References for the tests are computed from the annotated 2D positions and the fused 3D ball position with the same geometry (NF-VLT-21).

## Traces to

F-VLT-6, F-VLT-7, F-VLT-13, NF-VLT-1, NF-VLT-21

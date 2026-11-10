# ADR-VLT-011 — Generic constant-velocity / constant-acceleration prediction

- **Status:** accepted · 2026-11-10 · decided by the sponsor (OQ-17)
- **Feature:** VLT

## Context

The pendulum exists only to make the setup reproducible; the tracker must not depend on pendulum motion.

## Decision

F-VLT-4 predicts the ball position at `t_place_ns` with a constant-velocity or constant-acceleration model estimated from recent ball states; no pendulum model, no plausibility check based on pendulum motion (F-VLT-27). Run detection stays amplitude-based as the evaluation rule of the demo (ADR-VLT-006).

## Rationale

General motion keeps the tracker valid for a hand-moved ball; for the short prediction horizon a constant-acceleration model is close to a pendulum model.

## Consequences

F-VLT-4 rewritten; the maximum speed and acceleration of the tested envelope are part of OQ-14.

## Traces to

F-VLT-4, F-VLT-27, OQ-14

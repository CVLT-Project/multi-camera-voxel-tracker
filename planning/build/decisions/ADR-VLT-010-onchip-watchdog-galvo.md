# ADR-VLT-010 — The galvo node uses the Pi's on-chip watchdog

- **Status:** accepted · 2026-11-10 · decided by the sponsor (OQ-16)
- **Feature:** VLT

## Context

The external hardware watchdog (NF-VLT-4) was dropped at the PM review; a galvo node hang with the laser on was a residual risk covered only by the kill switch.

## Decision

The galvo node enables the SoC's hardware watchdog and its output loop feeds it. If the loop stops feeding it, the Pi resets within the watchdog interval; by NF-VLT-25 a reset switches the laser off. NF-VLT-4 stays dropped (no external circuit).

## Rationale

No additional hardware; turns a hang into a reset, which is already fail-safe.

## Consequences

NF-VLT-30 added; residual risk shrinks to "laser frozen at its last clamped aim for up to the watchdog interval"; NF-VLT-23 classifies the hang as detected.

## Traces to

NF-VLT-30, NF-VLT-25, NF-VLT-23, NF-VLT-3

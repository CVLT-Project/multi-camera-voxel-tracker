# ADR-VLT-008 — Tracking deadline is firm (p99 30 ms), laser-off deadlines are hard

- **Status:** accepted · 2026-11-10 · decided by the sponsor (OQ-12, deadline part)
- **Feature:** VLT

## Context

NF-VLT-18 called 30 ms a deadline but tested the 99th percentile. Raspberry Pi OS is not a real-time OS, so no hard bound can be proven for the tracking chain.

## Decision

The transactions and classes of NF-VLT-26 apply: T1 tracking firm (p99 ≤ 30 ms; a target whose validity has expired is discarded and counts as a miss, never applied late); T2 target-loss shutdown and T3 unsafe-condition shutdown hard (verified by measured maxima, backed by the kill switch); T4 monitoring soft; T5 camera reintegration without deadline. The numeric age, skew, horizon and sync-age limits follow from the camera choice (OQ-1) and remain open in OQ-12.

## Rationale

A late aim is useless but not dangerous; a late shutdown is the safety-relevant case.

## Consequences

NF-VLT-18 and NF-VLT-26 are aligned; OQ-12 is reduced to numeric limits and timestamp conversion.

## Traces to

NF-VLT-18, NF-VLT-26, F-VLT-10, F-VLT-22, NF-VLT-29

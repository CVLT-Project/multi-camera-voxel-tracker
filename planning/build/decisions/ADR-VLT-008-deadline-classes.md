# ADR-VLT-008 — Tracking deadline is firm (p99 30 ms), laser-off deadlines are hard

- **Status:** accepted · 2026-11-10 · decided by the sponsor (OQ-12, deadline part) · amended by ADR-VLT-018/019 on user instruction
- **Feature:** VLT

## Context

NF-VLT-18 called 30 ms a deadline but tested the 99th percentile. Raspberry Pi OS is not a real-time OS, so no hard bound can be proven for the tracking chain.

## Decision

NF-VLT-26 applies with explicit origins: T1 firm Tracking (p99 ≤ 30 ms, expired targets discarded); T2 target-loss ≤ 100 ms + 10 ms; T3 immediately qualifying unsafe conditions ≤ 100 ms (the explicit status-loss allowance of F-VLT-25 remains ≤ 110 ms); T4 soft monitoring; T5 reintegration without deadline. ADR-VLT-018 separates T6 effect supervision (500 ms qualification/watchdog + ≤ 100 ms off from its stated evidence/update origin) and T7 software hang (≤ 1 s total including reset/disable). The old blanket reading that every physical fault must be detected and switched off within 100 ms is superseded. Converter faults without a qualifying observable effect have no promised electrical detection time. Numeric camera age/skew/horizon/sync-age values and timestamp conversion remain OQ-1/OQ-12.

## Rationale

A late aim is useless but not dangerous; a late shutdown is the safety-relevant case.

## Consequences

NF-VLT-18 and NF-VLT-26 are aligned; OQ-12 is reduced to numeric limits and timestamp conversion.

## Traces to

NF-VLT-18, NF-VLT-26, F-VLT-10, F-VLT-22, NF-VLT-29

## Amendment 2026-11-17 — transaction review (approved by the sponsor)

T1 is measured from the physical change of the ball's motion, firm, p99 ≤ 45 ms (was 30 ms from the exposure). Transactions are only T1, T3 (physical conditions), T6 (F-VLT-26) and T8 kill switch (firm, 100 ms to the safe state). Target loss (was T2), local galvo faults, galvo hang (was T7), no measurable spot (F-VLT-42) and camera data loss are fault reactions with the same hard deadlines; camera reintegration (was T5) is a mode activity; monitoring (was T4) is no transaction. See NF-VLT-18, NF-VLT-26, concept §11.2.

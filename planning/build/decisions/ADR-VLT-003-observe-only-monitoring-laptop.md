# ADR-VLT-003 — Monitoring on a separate, observe-only laptop

- **Status:** accepted · 2026-11-02 · decided by the sponsor during intake (grilling #15–#17) · amended by ADR-VLT-013, ADR-VLT-014
- **Feature:** VLT

## Context

The demo needs a screen with live values and camera images (U-VLT-1). Rendering and image transfer compete with the real-time loop on Pi 3 nodes.

## Decision

A separate laptop runs a monitoring server. Every node pushes monitoring data (values, reduced camera images) to it, best effort. The laptop observes only: there is no command path from it into any node. Control stays on the Pis (arming decided by the control node software, ADR-VLT-013).

## Rationale

Keeps display load off the control node; keeps the laptop out of the safety design; lets the team analyse data without touching the loop.

## Consequences

- Monitoring must never block the loop and is dropped under back-pressure (NF-VLT-6), the system runs identically without the laptop (NF-VLT-7), bandwidth is capped (NF-VLT-8), the loop is verified with monitoring on and off (NF-VLT-9).
- Nodes must not open any listening port that accepts commands from the laptop (NF-VLT-10). Since ADR-VLT-014: SSH for administration is allowed, but the loop itself has no command interface.

## Traces to

U-VLT-1, NF-VLT-6, NF-VLT-7, NF-VLT-8, NF-VLT-9, NF-VLT-10

**Amended 2026-11-10 by ADR-VLT-013:** there is no arming button; arming, disarming, galvo scan and arming check are decided by the control node software, and the kill switch is the only physical control.

**Amended 2026-11-10 by ADR-VLT-014:** "no command path" applies to the monitoring software and to the running loop. Key-only SSH for administration (install, start/stop, configuration, logs) is allowed; configuration changes take effect only at restart.

# ADR-VLT-002 — One shared clock by software PTP (kernel)

- **Status:** accepted · 2026-11-02 · decided by the sponsor during intake (grilling #14)
- **Feature:** VLT

## Context

Three cameras observe a ball moving at up to ≈ 1 m/s. Observations must be combined at the time they were taken: 10 ms of mismatch ≈ 10 mm position error. Alternatives: hardware trigger lines to all cameras, or a shared clock with exposure timestamps.

## Decision

All five nodes share one clock synchronized over Ethernet with the kernel's PTP implementation in software mode. Every observation carries its exposure time in that clock. Target precision ≤ 1 ms (NF-VLT-5). No hardware camera trigger in v1.

## Rationale

No extra wiring; works with any camera module; the Pi 3 Ethernet (USB-attached LAN chip) has no hardware timestamping, but software PTP on a quiet dedicated switch is typically well below 1 ms [estimated].

## Consequences

- Precision must be measured, not assumed: offset per node is measured and shown (F-VLT-18, F-VLT-34).
- Monitoring traffic shares the switch and must not degrade sync (NF-VLT-20).
- Before a node is synchronized, its observations are unusable (F-VLT-20).
- Fusion must cope with cameras that expose at different moments (interpolation/selection by timestamp — architecture).

## Traces to

NF-VLT-5, NF-VLT-20, F-VLT-18, F-VLT-20

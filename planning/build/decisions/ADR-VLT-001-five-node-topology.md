# ADR-VLT-001 — Five Raspberry Pi 3 nodes on one wired Ethernet switch

- **Status:** accepted · 2026-11-02 · decided by the sponsor during intake (grilling #6, #7) · amended by ADR-VLT-013
- **Feature:** VLT

## Context

The system closes a loop camera → position → mirror → spot → camera. Hardware on hand: Raspberry Pi 3 boards with MIPI cameras, a hobby galvo kit with its own driver board. The ball must be seen from three orthogonal sides.

## Decision

Five Raspberry Pi 3 nodes on one wired Ethernet switch:

- three **camera nodes** (one MIPI camera each, on three orthogonal sides of the cube),
- one **control node** (fuses observations into the 3D ball position, computes target and aiming error, decides arming in software — see amendment),
- one **galvo node** (turns targets into mirror angles, drives the galvo through a converter board, switches the laser).

Product code: `src/<node>/` — `src/camera/`, `src/control/`, `src/galvo/` (plus shared code as the architecture decides).

## Rationale

Separating galvo output from control keeps the safety-relevant actuator logic (clamp, timeout, laser switching) on a node with a single small job. Wired Ethernet gives bounded, predictable latency compared with Wi-Fi.

## Consequences

- An extra network hop control → galvo inside the 30 ms deadline (NF-VLT-18).
- The galvo node is the last line of software safety (F-VLT-8 … F-VLT-10, F-VLT-21); its own software failure is covered only by the kill switch (NF-VLT-3); a hardware watchdog (NF-VLT-4) was dropped at the PM review.
- 100 Mbit Ethernet per Pi 3 bounds what can be sent (NF-VLT-8).

## Traces to

NF-VLT-14, NF-VLT-15, F-VLT-3, F-VLT-5, F-VLT-15

**Amended 2026-11-10 by ADR-VLT-013:** there is no arming button; arming, disarming, galvo scan and arming check are decided by the control node software, and the kill switch is the only physical control.

**Camera-profile clarification (ADR-VLT-020, user confirmation):** the five Raspberry Pi 3 boards remain fixed. The two side views are elevated, plus an offset overhead view; the camera model alone remains open under a selected capture/timing profile. The earlier statement that a galvo hang is covered only by the kill switch is superseded by the on-chip watchdog in ADR-VLT-010/018; the external watchdog remains deferred.

# ADR-VLT-012 — Automatic calibration of cameras and galvo

- **Status:** accepted · 2026-11-10 · decided by the sponsor · supersedes ADR-VLT-004 · amended by ADR-VLT-013
- **Feature:** VLT

## Context

ADR-VLT-004 chose manual calibration and deferred automatic galvo calibration, because spot visibility was uncertain. Manual calibration is too tedious to repeat for every short setup test, and a camera moved between tests would go unnoticed.

## Decision

- **Cameras — fully automatic:** ArUco markers are fixed to the cube frame at known cube coordinates (marker map, part of the setup). At every start each camera node estimates its intrinsics, distortion and pose in cube coordinates from the markers it sees. While running, it checks its pose against the visible markers at least once per second; a camera that no longer matches is excluded (treated as absent) with a diagnostic.
- **Galvo — automatic scan on demand:** the galvo scans a grid onto the cube's floor and walls; the cameras triangulate every spot seen by at least two of them, and a physical galvo model (pivot point, mirror spacing, scale and offset per axis) is fitted to the measured rays. ~~The scan runs only while the operator holds the arming button; releasing it switches the laser off and aborts the scan.~~ Superseded by ADR-VLT-013: the control node starts the scan when no valid calibration exists or the arming check fails; the kill switch or a safety fault aborts it; the number of consecutive failed scans is limited. The beam stays within configured galvo limits.
- **Check at arming:** before every arming the galvo projects 3 check points onto floor or walls; if any lies more than 5 mm from its commanded position, arming is refused and a galvo scan is started (ADR-VLT-013).

## Rationale

Repeated setup tests need calibration in seconds, not a manual session. The spot on a flat surface is far easier to see than on the ball, which removes ADR-VLT-004's reason for deferring automatic galvo calibration, provided the background allows it (OQ-7).

## Consequences

- F-VLT-12, F-VLT-13 rewritten; F-VLT-31 (arming check) added; F-VLT-8 lists the scan and the arming check as its only exceptions.
- ~~A button must be wired for galvo calibration, also on an installation running in `auto` mode.~~ Obsolete (ADR-VLT-013): there is no button.
- The arming check switches the laser on without an operator for under 1 s, inside the cube (since ADR-VLT-013 always, not only in `auto` mode).
- The automatic galvo scan depends on the spot being visible on floor and walls; the background choice (OQ-7) must allow it.
- The marker map (marker IDs and cube coordinates) becomes a setup file under F-VLT-24; the conventions themselves remain OQ-13.

**Observation-loss clarification (ADR-VLT-019, 2026-11-12):** during a galvo scan or arming check, loss of the measurable spot follows F-VLT-42 (500 ms + ≤ 100 ms to laser off): the scan or check fails and the existing bounded retry applies. A valid ball state is not required to triangulate calibration spots.

## Traces to

F-VLT-3, F-VLT-5, F-VLT-8, F-VLT-12, F-VLT-13, F-VLT-24, F-VLT-31, F-VLT-35, OQ-7, OQ-13

**Amended 2026-11-10 by ADR-VLT-013:** there is no arming button; arming, disarming, galvo scan and arming check are decided by the control node software, and the kill switch is the only physical control.

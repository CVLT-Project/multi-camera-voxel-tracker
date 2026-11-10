# ADR-VLT-013 — Software control by the control node; the kill switch is the only physical control

- **Status:** accepted · 2026-11-10 · decided by the sponsor (requirements review, gap G1) · amends ADR-VLT-001, ADR-VLT-003, ADR-VLT-007, ADR-VLT-012
- **Feature:** VLT

## Context

The requirements had two arming modes (`button`, `auto`), a physical arming button on the control node, and an on-demand galvo scan that ran only while the button was held. They didn't say how to disarm or what the button did besides arming, and they contradicted each other: U-VLT-2 described `auto` as being for a control node without a button, while ADR-VLT-012 required a button for the galvo scan. As written, an `auto` installation could never calibrate its galvo.

## Decision

- **One physical control:** the kill switch (NF-VLT-3, sense contact F-VLT-30). There is no arming button and no other physical operator input.
- **Arming, disarming, galvo scan and arming check are decided by the control node software.** No network command or other path controls them (ADR-VLT-003 unchanged).
- **Arming** happens automatically when the kill switch is released, no safety fault is active or latched, the setup is valid, at least two cameras have seen the ball continuously for the hold-off, and the arming check passes. The same rule applies at start and after a safety fault (the former `auto` mode is the only mode).
- **Disarming:** the operator presses the kill switch; the software disarms on every safety fault (ADR-VLT-007).
- **Galvo scan:** started by the control node when no valid galvo calibration exists or the arming check fails. The safeguard that was "button held" is replaced by the following: the scan is aborted with the laser off by the kill switch or any safety fault, and after a configured number of consecutive failed scans no further scan starts until the system is restarted.

## Rationale

The sponsor wants a single physical control. The kill switch already cuts the laser in hardware and is sensed by software, so it can serve as the operator's stop and as the deliberate reset.

## Consequences

- U-VLT-2, F-VLT-8, F-VLT-11, F-VLT-13, F-VLT-21, F-VLT-30 and F-VLT-31 are rewritten; the arming-button integration point and the config keys `arm_mode`, `arm_button_gpio` and `arm_button_debounce_ms` are obsolete.
- The laser comes on without an operator action: during the arming check (< 1 s), during the galvo scan (≤ 60 s) and when tracking starts. All of this stays inside the cube, with a Class ≤ 2 laser. The team's laser-safety procedure (NF-VLT-2) must cover unattended laser-on.
- ADR-VLT-007 relied on a deliberate decision to resume after a safety fault. Releasing the kill switch remains a deliberate act. For alarms (F-VLT-16, F-VLT-26) and repeated faults, a latched safe state cleared by pressing and releasing the kill switch is **proposed** in F-VLT-21. This needs PM review.

## Traces to

U-VLT-2, F-VLT-8, F-VLT-11, F-VLT-13, F-VLT-21, F-VLT-30, F-VLT-31, NF-VLT-2, NF-VLT-3

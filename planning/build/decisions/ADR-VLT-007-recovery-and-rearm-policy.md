# ADR-VLT-007 — One recovery policy: safety faults need re-arming, transient ball loss does not

- **Status:** accepted · 2026-11-10 · decided by the sponsor (OQ-11) · amended by ADR-VLT-013 and ADR-VLT-019
- **Feature:** VLT

## Context

F-VLT-8, F-VLT-11, F-VLT-17 and F-VLT-21 gave different answers on when the laser may come back on. The kill switch was invisible to software, so the system could stay armed across a kill-switch press.

## Decision

- **Transient — laser off while the condition lasts, resumes without re-arming:** ball seen by fewer than two cameras for ≤ 1 s; one camera absent, restarting or unsynced while two others deliver (degraded, F-VLT-11/17).
- **Safety fault — safe state, re-arming required (F-VLT-35):** kill switch pressed; target timeout at the galvo node; galvo or control node restart; sync loss leaving fewer than two usable cameras or on the galvo node; alarm (F-VLT-16, F-VLT-26); converter link error; fewer than two cameras present; ball not seen by two cameras for > 1 s.
- **Kill switch feedback:** the kill switch gets a sense contact read by the galvo node on a GPIO pin and reported in `GalvoStatus`.
- **Arming epoch:** every arming increments `arm_epoch`, carried in each `Target`. After a safety fault the galvo node switches the laser on only for targets with a higher `arm_epoch` than at the fault, so a lost status message cannot bypass re-arming.
- **`auto` mode** (since ADR-VLT-013 the only mode)**:** re-arms after a safety fault only when the fault has cleared and the arming condition (≥ 2 cameras see the ball) has held continuously for a configured hold-off (default 2 s).

**Amendment (ADR-VLT-019, user-requested correction):** F-VLT-42 observation timeout during Tracking is an alarm and latches Safe until kill-switch press/release. In Calibrating galvo or Arming check, observation timeout instead switches off and fails that attempt/check under F-VLT-13/31, without alone setting the tracking-alarm latch. A converter link fault is detected only through a qualifying observable effect; see ADR-VLT-018.

## Rationale

Safety-relevant shutdowns need a deliberate decision to resume; short occlusions by the string or the hand must not stop the demo.

## Consequences

- F-VLT-8, F-VLT-11, F-VLT-21 are rewritten; F-VLT-30 (kill-switch sense) added; `Target.arm_epoch` and config `auto_rearm_holdoff_ms` added.
- The 1 s and 2 s values are [estimated].

## Traces to

F-VLT-8, F-VLT-10, F-VLT-11, F-VLT-17, F-VLT-20, F-VLT-21, F-VLT-25, F-VLT-30, F-VLT-35, NF-VLT-3

**Amended 2026-11-10 by ADR-VLT-013:** there is no arming button; arming, disarming, galvo scan and arming check are decided by the control node software, and the kill switch is the only physical control.

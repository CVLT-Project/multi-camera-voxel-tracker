---
stage: control
owner: build
status: in_progress
revision: 27
created: 2026-11-02T15:27
updated: 2026-11-12T20:15
input: problem statement (chat)
title: Voxel Camera with Laser Tracking
code_root: ../../src
git: yes
language: en
budget_min: {intake: 60, concept: 120, synthesis_per_slice: 45, rescue: 60}
profile: profile/
contract_in: none
register: —
---

# Build: Voxel Camera with Laser Tracking

## Starting point

- **Input:** problem statement in prose (chat, 2026-11-02): "Voxel Camera with Laser Tracking. Three Raspberry Pi cameras stand at right angles around a cube. A ball swings on a string through the cube. A master node computes the 3D position of the ball. It steers a laser through a galvo mirror pair so that the spot stays on the ball. The cameras also see the spot, so the system measures its own aiming error."
- **Sponsor / product owner:** Ralf Hintersteininger (signs all build gates — profile)
- **Decision date:** open
- **Purpose of this build:** a working system in which three camera nodes and a master node track a swinging ball in 3D and keep a galvo-steered laser spot on it, measuring their own aiming error.

## Features

| Code | Title | Path | Field of application | Concept version | Status |
| --- | --- | --- | --- | --- | --- |
| VLT | Voxel Camera with Laser Tracking | A | distributed real-time system (+ embedded, hardware) | — | in_progress |

## Feature VLT — Voxel Camera with Laser Tracking

| Stage | Skill | File | Status | Current revision | Started | Finished | Minutes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | intake | VLT/10-intake.md | done | 2 | 2026-11-02T15:28 | 2026-11-02T16:03 | 31 |
| 2 | concept | VLT/20-concept.md | in_progress | 22 | 2026-11-02T16:03 | | |
| 3 | synthesis | VLT/30-synthesis.md | open | — | | | |
| 4 | rescue | VLT/40-rescue.md | open | — | | | on demand |

### Gates VLT

| Gate | MANIFEST | When | Decision | By | Date | Rationale / accepted items |
| --- | --- | --- | --- | --- | --- | --- |
| PM review | Phase 4 | after concept §3–§10, before architecture | approved | Ralf Hintersteininger (sponsor), with the team | 2026-11-12 | requirements of concept rev 22 approved as written (Gate 1), incl. all requirements marked "proposed — PM review pending" / "Gate 1 pending". Accepted as open into the architecture (decided at Gate 2): OQ-3, OQ-4, OQ-7, OQ-12, OQ-14 (each with a proposal) and risk R-1 (camera mode vs. NF-VLT-18). Not part of this approval: the requirement change requests in §11 (ADR-VLT-017/020/021/022) — each needs its own team decision |
| Consistency review | Phase 6 | after architecture, before synthesis | pending | | | |
| Gap analysis | Phase 9 | after the last slice | pending | | | |

## Cross-feature interactions

| Feature | Depends on | Touches | Interference risk | Where documented |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

## Decision log

| Time | Feature | Stage | Decision | Note |
| --- | --- | --- | --- | --- |
| 15:27 | VLT | — | start | path A (cold start), git yes, code root `src/` (project root) with one subfolder per node — user constraint |
| 15:28 | VLT | intake | next | intake started |
| 16:03 | VLT | intake | next | intake done (rev 2): 40 draft requirements, 8 open questions (OQ-1 … OQ-8); concept started |
| 16:13 | VLT | concept | — | §0–§10 written (rev 1): 21 F, 3 U, 20 NF; ADR-VLT-001 … 004; PM review pending |
| 16:16 | VLT | concept | — | sponsor decisions applied (concept rev 2): NF-VLT-4, U-VLT-3 dropped; F-VLT-14 optional. Logged as approval in error — corrected 16:20 |
| 16:20 | VLT | concept | stop | PM review still pending; requirements not approved; no architecture started; nothing of the concept committed |
| 16:24 | VLT | concept | wip_commit | user request: commit the requirements draft (concept rev 2, status in_progress) as work in progress for team discussion — a deliberate exception to RULES §6 (commits mark frozen states); on resume: ask the PM review question first |
| 16:31 | VLT | concept | — | team feedback applied (concept rev 3): NF-VLT-21 reference data set added; acceptance of F-VLT-1, 2, 3, 4, 6, 7, NF-VLT-11, NF-VLT-17 rewritten against it; still PM review pending; wip commit on user request |
| 2026-11-06 15:24 | VLT | concept | requirements review | user requested only useful additions/clarifications: proposed F-VLT-22 … F-VLT-24, NF-VLT-22; metric/release acceptance gaps exposed, OQ-9 … OQ-14 added; ≈ 90 fps reclassified as an unverified estimate; concept rev 4 and shared vocabulary updated; PM review pending, no architecture or commit |
| 2026-11-10 | VLT | concept | requirements review | user requested a DRS completeness and consistency check: proposed F-VLT-25 … F-VLT-29, NF-VLT-23 … NF-VLT-29; corrected F-VLT-8 (camera restart), F-VLT-16 (action delay), F-VLT-18/20 + `clock_sync_limit_ms` (pairwise π); sharpened F-VLT-1/4/11/15, U-VLT-1; exposed hit-rule degeneracy (OQ-9), F-VLT-14 vs. re-arm (OQ-8), calibration vs. F-VLT-8 (OQ-13); added OQ-15/16 and a DRS coverage table (§9); concept rev 5, CONTEXT rev 5; PM review pending, no commit |
| 2026-11-10 | VLT | concept | sponsor decisions | OQ-6/8/9/10/11/15/16/17 decided, OQ-12 (deadline classes) and OQ-14 (every camera pair ≥ 80 %) partly; ADR-VLT-005 … 011; F-VLT-14 deferred; F-VLT-30, NF-VLT-30 added; F-VLT-27 without pendulum model; OQ-13 kept for team discussion; concept rev 6, CONTEXT rev 6; PM review pending, no commit |
| 2026-11-10 | VLT | concept | sponsor decision | automatic calibration (ADR-VLT-012 supersedes ADR-VLT-004): cameras incl. lens from frame markers at every start + continuous pose check; galvo scan on demand with button held; 3-point check at arming (F-VLT-31); background stays with OQ-7; OQ-13 reduced to conventions and marker map; concept rev 7, CONTEXT rev 7 |
| 2026-11-10 | VLT | concept | sponsor decision | OQ-13 resolved: cube frame and rest position in §2, annotation pixel coordinates in NF-VLT-21, design details to the architecture; proposed U-VLT-4 (health overview incl. clock counters), U-VLT-5, F-VLT-32, F-VLT-33, NF-VLT-31 for integration and debugging; concept rev 8, CONTEXT rev 8; wip commit on user request |
| 2026-11-10 | VLT | concept | requirement added | proposed U-VLT-6 chain delay statistics (per stage and end to end, min/max/mean/jitter/percentiles, stage shares, histogram, saved per run); concept rev 9, CONTEXT rev 9 |
| 2026-11-10 | VLT | concept | sponsor decision | review gap G1 resolved: no arming button, the kill switch is the only physical control, arming/disarming/galvo scan/arming check decided by the control node software (ADR-VLT-013, amends ADR-VLT-001/003/007/012); U-VLT-2, F-VLT-8/11/13/21/30/31 rewritten; proposed safety latch cleared by kill-switch press and release; concept rev 10, CONTEXT rev 10; wip commit on user request |
| 2026-11-10 | VLT | concept | sponsor decision | review gap G2 resolved: monitoring laptop required to operate, no local indicators; U-VLT-7 added (state on connect, stale nodes, diagnostics logged locally), F-VLT-29 log contents extended; concept rev 11, CONTEXT rev 11 |
| 2026-11-10 | VLT | concept | sponsor decision | review gap G3 resolved: key-only SSH for administration, separate from control of the loop, which has no command interface; config changes take effect at restart (ADR-VLT-014, amends ADR-VLT-003); NF-VLT-10 rewritten, NF-VLT-28 adjusted; concept rev 12; wip commit on user request |
| 2026-11-10 | VLT | concept | Gate 1 preparation | checked against the report requirements and the lecture checklist [L] p. 287–288: design moved from §3–§5 to §10 (p. 287 rule); reason and lecture page per requirement; U-VLT-1 … 7 → F-VLT-34 … 40; G4 → NF-VLT-32, G5 → F-VLT-7/1; new F-VLT-41 (modes), NF-VLT-33 (timing of actions), NF-VLT-34 (reaction matrix, coverage); values for F-VLT-26/27/28; OQ owners as sub-team roles; lecture checklist table in §9; concept rev 13, CONTEXT rev 12 |
| 2026-11-10 | VLT | concept | hardware decision | galvo set (AliExpress), PCM5102A I2S DAC, Laserfuchs 650 nm 1 mW Class 2 laser (ADR-VLT-015); OQ-2, OQ-5 resolved; link faults detected by effect monitoring (team choice, ≈ 600 ms); F-VLT-15, NF-VLT-16 rewritten; galvo specs still open (OQ-4); concept rev 14, CONTEXT rev 13 |
| 2026-11-10 | VLT | concept | hardware data | galvo specs from the listing (±5 V, 0.33 V/°, ±15°/±30° optical, ≤ 0.5 ms step, ±12 V) added to ADR-VLT-015 and §6; NF-VLT-32 requires the cube within the usable scan angle; F-VLT-19 conditional; OQ-4 narrowed (wiring, supply, pattern board, level matching); concept rev 15 |
| 2026-11-12 | VLT | concept | effect supervision | requirement part of the camera-team review (PR review 2026-11-11): F-VLT-42 optical-effect watchdog (ADR-VLT-019); T3/T6/T7 origins and bounds (ADR-VLT-018); converter link faults detected only through an observable effect, blanket 600 ms withdrawn (ADR-VLT-015); F-VLT-8/13/15/21/26/29/31, NF-VLT-23/26/29/30/34, reaction matrix and OQ-4 adjusted. Camera handoff, timing budget and reference plan deferred to the architecture (M3). |
| 2026-11-12 | VLT | concept | M3 groundwork | camera-team handoff recast as proposed §11 content: interfaces and messages, T1 budget in five phases, g = 2 ms with derivation, reference plan; ADR-VLT-016/017/020/021/022 proposed for the M3 consistency review (Gate 2); requirement changes listed as change requests, not applied. Remaining transactions, integration tests and fault injection are M3 to-dos. |
| 2026-11-12 | VLT | concept | M3 groundwork | from the camera-team PR #6 (not merged): T2, T3 (frame-evidenced and local) and T5 budgets in §11.2, camera fault-injection tests in §11.4; T3 corrected (kill switch separate, budget consistent with T1). Requirements unchanged. |
| 2026-11-12 | VLT | concept | hardware fact | camera given: Raspberry Pi Camera Module v2.1 (IMX219, rolling shutter) on Pi 3 Model B+; OQ-1 resolved, §6 updated; the cropped 640 × 480 mode (≈ 26.5° × 20°) conflicts with the proposed layout (≥ 45°) — open check in §11.6. |
| 2026-11-12 | VLT | concept | report review | consistency fixes for the M2 report (rev 20): galvo, DAC and laser recorded as given hardware (ADR-VLT-015); open-question limits marked as architecture values with the requirements that need them; F-VLT-42 → ADR-VLT-018/019; F-VLT-14 row, reaction-matrix camera row, checklist row 18 and duplicate T1/π wording corrected; no requirement changes meaning. |
| 2026-11-12 | VLT | concept | start-up and envelope | rev 21, on user instruction: F-VLT-28 allows the start-up galvo scan (conflict with F-VLT-13 resolved); operating envelope from the OQ-14 proposal fixed in NF-VLT-1 (release 100 … 300 mm, ≤ 1000 mm/s, ≤ 4000 mm/s²); risk R-1 (camera mode vs. 30 ms) recorded in §8. |
| 2026-11-12 | VLT | concept | review follow-up | NF-VLT-1 lowest release ≈ 120 mm (F-VLT-7 threshold), room lighting defined and recorded; F-VLT-28 failure path and second-scan case; ADR-VLT-016 no longer claims the operating envelope (now NF-VLT-1). |
| 2026-11-12 20:15 | VLT | concept | Gate 1 approved | PM review (MANIFEST Phase 4) passed on concept rev 22: requirements approved by the sponsor with the team; open questions OQ-3/4/7/12/14 and risk R-1 carried into the architecture; §11 change requests not approved with it. Architecture (second half of the concept) may start. |

## Open items for the Director

- Gate 1 approved 2026-11-12 (concept rev 22). Next: the concept author flips the "proposed — PM review pending / Gate 1 pending" markers in the concept and `CONTEXT.md` to approved, then continues with the architecture (§11, M3) and the consistency review (§12, Gate 2).
- Before or with Gate 2: team decisions on the §11 requirement change requests (ADR-VLT-017/020/021/022); answers to OQ-3/4/7/12/14; bench check of R-1 (camera mode vs. NF-VLT-18 30 ms).
- Design question still to settle in the architecture: programming language of the nodes (Python / C++ / mixed).

## Notes (human)

<!-- Off limits for all skills. The human corrects, adds and comments here. Copied verbatim on every rewrite. -->

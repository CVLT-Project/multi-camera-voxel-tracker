---
stage: control
owner: build
status: in_progress
revision: 28
created: 2026-11-02T15:27
updated: 2026-11-10T16:29
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
| 2 | concept | VLT/20-concept.md | in_progress | 21 | 2026-11-02T16:03 | | |
| 3 | synthesis | VLT/30-synthesis.md | open | — | | | |
| 4 | rescue | VLT/40-rescue.md | open | — | | | on demand |

### Gates VLT

| Gate | MANIFEST | When | Decision | By | Date | Rationale / accepted items |
| --- | --- | --- | --- | --- | --- | --- |
| PM review | Phase 4 | after concept §3–§10, before architecture | pending | | | current requirements concept rev 21; Pi 3 retained by user; all camera-team profile/timing/reference choices delegated and recorded (ADR-VLT-020/021/022); camera model/driver binding, physical qualification and galvo OQ-4 remain; full Gate 1 not yet approved |
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
| 2026-11-10 15:02 | VLT | concept | delegated setup definition | user delegated physical installation definition, camera stays open, normal room lighting without deliberate extremes. ADR-VLT-016: 800 mm cube, white 50 mm ball, 1 m suspension, ≤ 300 mm deflection, grey panels, 18 markers, nominal camera/galvo mounts; geometry review sets overhead offset to 300 mm and cross-member width ≤ 40 mm. OQ-3 and OQ-7 choices resolved; OQ-14 envelope defined, combined error budget pending; camera/exposure/timing remain OQ-1/OQ-12, electrical range OQ-4. NF-VLT-17 clarified; concept rev 17, CONTEXT rev 15; no measurements, Gate 1 approval or commit |
| 2026-11-10 15:23 | VLT | concept | consistency corrections | user requested resolution of three ambiguities, camera-dependent choices kept open. ADR-VLT-017: 60 s laser-off preparation, optional ≤ 60 s scans incl. off/transition, ≤ 2 attempts, Ready/Safe ≤ 180 s for first start. ADR-VLT-018: explicit T2/T3/T6/T7 origins and bounds; no blanket converter-fault detection guarantee. ADR-VLT-019, new F-VLT-42: 500 ms optical-effect watchdog + ≤ 100 ms off, tracking alarm latched, scan/check attempt fails. Requirements, reaction matrix, prior ADRs and CONTEXT aligned; concept rev 19, CONTEXT rev 17; no code, physical measurements, full Gate 1 approval or commit |
| 2026-11-10 15:58 | VLT | concept | camera-team specification | user delegated remaining camera-team choices and confirmed Raspberry Pi 3 stays fixed; camera model remains open. ADR-VLT-020/021/022, camera-profile.json, observation schema and reference plan fix acquisition/exposure/calibration handoff, numeric time limits/budgets, combined error allocation and qualification ownership. Side camera heights/marker sizes refined for the 640 × 480 profile. Added F-VLT-43/44 and NF-VLT-35; tightened pair position/prediction allowances to close the error budget. OQ-12/14 design resolved, physical results pending; concept rev 21, CONTEXT rev 19. M2 PDF refreshed, original preserved; no code, hardware claims, full Gate 1 approval or commit |
| 2026-11-10 16:29 | VLT | concept | pull request requested | user explicitly requested a PR for the local planning changes: WIP commit and push to a new fork branch are authorized for review, a deliberate exception to RULES §6 frozen-state commits. Requirements remain in_progress, full Gate 1 and hardware qualification remain pending. Include profile/contracts/reference plan, ADRs and regenerated report/source backup; exclude temporary PDF QA renders. |

## Open items for the Director

- Full Gate 1 remains pending for concept rev 21. Software architecture/synthesis have not started; the user delegated camera-team design choices, not full-gate approval.
- Fixed: five Raspberry Pi 3 nodes. OQ-1 only: select the camera model and bind/qualify its concrete driver/capture/row-timing capabilities against VLT-CAM-1. Image/rate/exposure, numeric time limits, combined budget and test ownership are selected targets, not measured results.
- Physical work still required: build/measure the setup, record/review reference data, and perform the loaded Pi 3 timing/resource/optical and independent timing qualification. Failures must be reported; do not invent achieved values.
- OQ-4 remains outside camera-team closure: delivered galvo electrical facts, full-range level matching, measured range and settling.
- The updated M2 report is generated from current requirement/profile/plan sources; its earlier 6 November version is retained under reports/reference/.
- Next general software-design decision after Gate 1: node programming language and full module/slice architecture.

## Notes (human)

<!-- Off limits for all skills. The human corrects, adds and comments here. Copied verbatim on every rewrite. -->

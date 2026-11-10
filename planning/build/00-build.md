---
stage: control
owner: build
status: in_progress
revision: 15
created: 2026-11-02T15:27
updated: 2026-11-10T00:00
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
| 2 | concept | VLT/20-concept.md | in_progress | 9 | 2026-11-02T16:03 | | |
| 3 | synthesis | VLT/30-synthesis.md | open | — | | | |
| 4 | rescue | VLT/40-rescue.md | open | — | | | on demand |

### Gates VLT

| Gate | MANIFEST | When | Decision | By | Date | Rationale / accepted items |
| --- | --- | --- | --- | --- | --- | --- |
| PM review | Phase 4 | after concept §3–§10, before architecture | pending | | | sponsor decisions applied (NF-VLT-4, U-VLT-3 dropped; F-VLT-14 optional); reference data set in rev 3; focused requirements review in rev 4 proposes F-VLT-22 … F-VLT-24, NF-VLT-22 and OQ-9 … OQ-14; DRS completeness review in rev 5 proposes F-VLT-25 … F-VLT-29, NF-VLT-23 … NF-VLT-29, OQ-15/16 and corrects F-VLT-8/16/18/20 — requirements not yet approved |
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
| 2026-11-10 | VLT | concept | sponsor decision | review gap G1 resolved: no arming button, the kill switch is the only physical control, arming/disarming/galvo scan/arming check decided by the control node software (ADR-VLT-013, amends ADR-VLT-001/003/007/012); U-VLT-2, F-VLT-8/11/13/21/30/31 rewritten; proposed safety latch cleared by kill-switch press and release; concept rev 10, CONTEXT rev 10; no commit |

## Open items for the Director

- PM review pending for VLT (concept rev 8) — sponsor answers in ADR-VLT-005 … 012; open: OQ-1 … OQ-5, OQ-7, OQ-12 (numeric limits), OQ-14 (envelope, error budget). rev 8 adds proposed debugging requirements (U-VLT-4/5, F-VLT-32/33, NF-VLT-31). rev 5 added the DRS completeness review: 12 proposed requirements, 4 in-place corrections, OQ-15/16; 16 open questions in total. Earlier note for rev 4: — sponsor has not approved the requirements yet. Four proposed requirements and six new clarification topics are ready for team discussion; 14 open questions in total. Next design question once approved: programming language of the nodes (Python / C++ / mixed).
- OQ-1 (camera model) is critical for NF-VLT-18 (30 ms deadline).
- Discuss OQ-9/OQ-10 first (measurable aiming error and unbiased run scoring), then OQ-11/OQ-12 (recovery and temporal validity); OQ-13/OQ-14 cover calibration conventions and the acceptance envelope. These are unresolved decisions, not new approved scope.

## Notes (human)

<!-- Off limits for all skills. The human corrects, adds and comments here. Copied verbatim on every rewrite. -->

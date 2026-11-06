---
stage: control
owner: build
status: in_progress
revision: 9
created: 2026-11-02T15:27
updated: 2026-11-06T15:24
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
| 2 | concept | VLT/20-concept.md | in_progress | 4 | 2026-11-02T16:03 | | |
| 3 | synthesis | VLT/30-synthesis.md | open | — | | | |
| 4 | rescue | VLT/40-rescue.md | open | — | | | on demand |

### Gates VLT

| Gate | MANIFEST | When | Decision | By | Date | Rationale / accepted items |
| --- | --- | --- | --- | --- | --- | --- |
| PM review | Phase 4 | after concept §3–§10, before architecture | pending | | | sponsor decisions applied (NF-VLT-4, U-VLT-3 dropped; F-VLT-14 optional); reference data set in rev 3; focused requirements review in rev 4 proposes F-VLT-22 … F-VLT-24, NF-VLT-22 and OQ-9 … OQ-14 — requirements not yet approved |
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

## Open items for the Director

- PM review pending for VLT (concept rev 4) — sponsor has not approved the requirements yet. Four proposed requirements and six new clarification topics are ready for team discussion; 14 open questions in total. Next design question once approved: programming language of the nodes (Python / C++ / mixed).
- OQ-1 (camera model) is critical for NF-VLT-18 (30 ms deadline).
- Discuss OQ-9/OQ-10 first (measurable aiming error and unbiased run scoring), then OQ-11/OQ-12 (recovery and temporal validity); OQ-13/OQ-14 cover calibration conventions and the acceptance envelope. These are unresolved decisions, not new approved scope.

## Notes (human)

<!-- Off limits for all skills. The human corrects, adds and comments here. Copied verbatim on every rewrite. -->

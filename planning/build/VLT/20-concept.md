---
stage: concept
owner: build-concept
status: in_progress
revision: 12
version: 0.1
created: 2026-11-02T16:10
updated: 2026-11-10T00:00
input: VLT/10-intake.md@2, requirements review request (chat, 2026-11-06), DRS completeness review request and sponsor answers to OQ-6 … OQ-17 (chat, 2026-11-10), sponsor decisions on operator control, operator feedback and admin access (chat, 2026-11-10)
feature: VLT
---

# VLT Concept — Consolidated Requirements

_Sections 0–12 of the MANIFEST document structure. Together with `30-synthesis.md` (Sections 13–16) this is the source of truth for the feature's code: a fresh agent, given only these files and `CONTEXT.md`, must be able to regenerate the implementation. IDs carry the feature code (`F-VLT-1`) and never change after `done`; reruns append, never renumber._

## 0. Synthesis Context

- **Development path:** A — frontloaded (cold start from a problem statement).
- **Synthesis dependencies:** none.
- **Synthesis scope:** the complete software of all node types (camera, control, galvo), the calibration procedures, the node setup scripts and the monitoring server on the laptop. Hardware (converter board, kill switch, laser) is specified by its interface only; the hardware watchdog remains out of scope (§7).
- **Field of application:** distributed real-time system (+ embedded, hardware) — checklists: Cross-cutting, DRS, Embedded, Hardware, By Technology, General Robustness (Software).

### Register trace

not relevant — no register

### Requirements review — 2026-11-06

F-VLT-22 … F-VLT-24 and NF-VLT-22 are proposed additions from a review of the existing requirements, not sponsor-approved decisions. OQ-9 … OQ-14 identify implementation blockers and conflicting interpretations; their owners and affected requirements are listed in §8. Existing sponsor decisions remain in place. In particular, the measurement and recovery rules are not implementation-ready until OQ-9 … OQ-12 are settled. No architecture is introduced by this review.

### DRS completeness review — 2026-11-10

Review of the whole requirement set against the DRS checklist (coverage table in §9) and against itself. All items below are **proposals pending the PM review**, not sponsor-approved decisions.

- **Added (proposed):** F-VLT-25 (galvo status feedback), F-VLT-26 (actuator-effect monitoring), F-VLT-27 (fusion plausibility), F-VLT-28 (start-up, ground state, shutdown), F-VLT-29 (safety event log); NF-VLT-23 (fault hypothesis), NF-VLT-24 (global time base), NF-VLT-25 (fail-safe laser enable), NF-VLT-26 (real-time transaction classes), NF-VLT-27 (state-message semantics and load hypothesis), NF-VLT-28 (node platform and isolated network), NF-VLT-29 (independent timing measurement).
- **Inconsistencies corrected in place (confirm at PM review):** F-VLT-20 / `synced` / `clock_sync_limit_ms` used a per-node 1 ms limit, which allows 2 ms between two nodes and so breaks the pairwise bound of NF-VLT-5 — now π/2 = 0.5 ms per node. F-VLT-16 would alarm on every laser-off transition, because frames exposed before the switch-off took effect still show the spot — action-delay window added. F-VLT-8 narrowed to control/galvo restarts, in line with the sponsor's degraded-mode decision (F-VLT-11/17); the full recovery policy stays in OQ-11. F-VLT-18 now checks the pairwise bound.
- **Acceptance sharpened:** F-VLT-1 (spot on the ball as a separate case — the laser is a hidden channel into ball detection), F-VLT-4 (tail bound, not only median), F-VLT-11 (camera absent vs. ball not seen), F-VLT-15 (defined output at power-up).
- **Wrong or contradictory requirements exposed, decision needed:** the hit rule of F-VLT-7 is degenerate if read as a 3D distance (OQ-9, extended); F-VLT-14 cannot meet "resumes ≤ 1 s" in `button` mode, because the target timeout puts the system into the safe state, and re-arming then needs a button press (OQ-8, extended); the galvo calibration (F-VLT-13) and the F-VLT-5 acceptance need the laser on without a ball, which F-VLT-8 forbids (OQ-13, extended).
- **New open questions:** OQ-15 (activation and cadence of the loop), OQ-16 (on-chip watchdog as a no-hardware mitigation of the dropped NF-VLT-4), OQ-17 (prediction model without pendulum assumption).
- **Sponsor decision 2026-11-10:** the pendulum exists only for a reproducible setup; no plausibility check or rejection may rely on pendulum motion (F-VLT-27 revised accordingly).

### Sponsor decisions — 2026-11-10

- Also proposed: U-VLT-6 (chain delay statistics per stage and end to end).
- Later the same day: automatic calibration (ADR-VLT-012, superseding ADR-VLT-004, F-VLT-12/13/31). OQ-13 resolved by defining the cube frame and the rest position (§2); marker map and setup-revision contents move to the architecture. Proposed for integration and debugging: U-VLT-4 (system health overview incl. clock counters), U-VLT-5 (fused position drawn into camera images), F-VLT-32 (session recording and replay), F-VLT-33 (dry-run modes), NF-VLT-31 (nodes testable against simulated peers).
- Later the same day (requirements review, gap G1): no arming button. The kill switch is the only physical control; arming, disarming, galvo scan and arming check are decided by the control node software (ADR-VLT-013). Rewritten: U-VLT-2, F-VLT-8/11/13/21/30/31; arming-button integration point and `arm_mode` / `arm_button_*` keys obsolete; added `galvo_scan_max_attempts`. Proposed (PM review pending): latched safe state after alarms or repeated safety faults, cleared by pressing and releasing the kill switch (F-VLT-21).
- Later the same day (review gap G2): the monitoring laptop is required to operate the demo and is the only status display; no local indicators. Added U-VLT-7 (state shown on connect, stale nodes flagged, diagnostics also logged locally); F-VLT-29 log contents extended.
- Later the same day (review gap G3): admin access over key-only SSH is allowed, separate from control of the loop, which has no command interface (ADR-VLT-014, amends ADR-VLT-003). NF-VLT-10 rewritten; NF-VLT-28 allows a team machine for administration outside acceptance runs.


OQ-6, OQ-8, OQ-9, OQ-10, OQ-11, OQ-15, OQ-16, OQ-17 decided; OQ-12 decided for the deadline classes (numeric limits still open); OQ-14 decided for degraded mode (envelope and error budget still open); OQ-13 open for team discussion. New ADRs: ADR-VLT-005 … ADR-VLT-011. Rewritten: F-VLT-3/4/5/6/7/8/11/13/21, NF-VLT-1/2/18, NF-VLT-23 (hang), NF-VLT-26 (decided). F-VLT-14 deferred. Added: F-VLT-30 (kill-switch sense), NF-VLT-30 (on-chip watchdog). The other requirements proposed on 2026-11-10 remain proposals until the PM review.

## 1. Purpose

A lab demo that shows multi-camera 3D tracking. Three Raspberry Pi cameras stand at right angles around a cube; a ball swings on a string through the cube. The system computes the 3D position of the ball and steers a laser through a galvo mirror pair so that the spot stays on the ball. The cameras also see the spot, so the system measures its own aiming error. Built and operated by a team of 11 students, presented once to other students.

## 2. Ubiquitous Language & Context

Full dictionary in `CONTEXT.md`. Delta introduced by this feature:

| Term | Meaning | Used in code as |
| --- | --- | --- |
| cube | the tracking volume and its coordinate system: right-handed, in mm; origin at the floor corner marked "0" on the frame, x and y along the floor edges marked "X" and "Y", z up. All positions in requirements and tests are given in it. | `Cube`, cube coordinates in mm |
| ball | the tracked object, ≈ 5 cm diameter, on a ≈ 1 m string | `ball` |
| spot | the laser spot as seen by the cameras | `spot` |
| camera node / control node / galvo node | the three node types (ADR-VLT-001) | `camera`, `control`, `galvo` |
| observation | one camera's detection result for one frame: ball and spot image positions plus exposure time | `Observation` |
| ball state | fused 3D ball position (and velocity) at a time | `BallState` |
| target | the cube point the galvo node shall aim at, with its validity time and laser flag | `Target` |
| aiming error | distance in mm from the fused ball centre to the laser beam line (galvo origin → spot in 3D); unmeasurable when the spot cannot be placed in 3D (ADR-VLT-005) | `aiming_error_mm` |
| hit | a fusion slot in which, in at least one camera that sees both, the spot lies inside the ball's image disc (ADR-VLT-005) | `hit` |
| run | from release (ball displaced > 100 mm starts moving) until the amplitude falls below 50 mm; aborted when the safe state ends it (ADR-VLT-006) | `Run` |
| hit rate | time with a hit ÷ run duration; gaps count as misses (ADR-VLT-006) | `hit_rate` |
| fusion slot | one period of the fixed-rate fusion, aligned to the shared clock (ADR-VLT-009) | `FusionSlot` |
| arming epoch | counter incremented at every arming; the galvo node needs a newer one after a safety fault (ADR-VLT-007) | `arm_epoch` |
| rest position | the ball centre while the ball hangs still | `rest_position_mm` |
| amplitude | the ball's maximum horizontal distance from its rest position over the last swing | `amplitude_mm` |
| armed | the state in which the system may switch the laser on | `armed` |
| safe state | laser off; galvo node ignores targets until re-armed | `SAFE` |
| degraded | tracking with exactly two camera nodes delivering the ball | `DEGRADED` |
| camera calibration / galvo calibration | stored results of the automatic calibrations (ADR-VLT-012) | `camera_calibration`, `galvo_calibration` |
| reference data set | recorded, annotated frames of all cameras used by the automated tests (NF-VLT-21) | `reference_data` |
| monitoring laptop | observe-only sink for monitoring data (ADR-VLT-003) | `monitor` |
| kill switch | physical switch cutting the laser supply independent of software | — |

## 3. Functional Requirements

| ID | Requirement | Acceptance (falsifiable) | Origin | Evidence |
| --- | --- | --- | --- | --- |
| F-VLT-1 | Each camera node detects the ball in every captured frame and sends an observation with the ball's image position (or "not seen") and the exposure time in the shared clock to the control node. | On the reference data set (NF-VLT-21): the detected ball position lies within 3 px of the annotation in ≥ 95 % of the frames with an annotated ball; frames without the ball report "not seen". The 3 px / 95 % bound also holds when evaluated only over frames with the spot on the ball (the laser is a hidden channel into ball detection; review 2026-11-10). Automated test, runs without hardware; the same test run on a camera node gives identical results. | intake d-1 · team review (reference data set) · DRS review 2026-11-10 | [evidenced] |
| F-VLT-2 | Each camera node detects the laser spot in every captured frame and includes its image position (or "not seen") in the same observation. | On the reference data set (NF-VLT-21): the detected spot position lies within 3 px of the annotation in ≥ 95 % of the frames with an annotated spot; frames recorded with the laser off report "not seen" in ≥ 99 %. Automated test, runs without hardware; the same test run on a camera node gives identical results. | intake d-2 · team review (reference data set) | [evidenced] / thresholds [estimated] |
| F-VLT-3 | The control node computes the ball's 3D position in cube coordinates from the observations of at least two camera nodes, using the camera calibration and combining observations by exposure time. Fusion runs at a fixed period `fusion_period_ms` aligned to the shared clock (ADR-VLT-009); cameras whose frames are not phase-aligned are interpolated to the fusion time by exposure time. | On the reference data set (NF-VLT-21): for the resting positions, the computed 3D position lies within 10 mm of the hand-measured position with 3 cameras and within 15 mm with any 2 cameras. Automated test, runs without hardware. Fusion slot start times on the node deviate ≤ 1 ms from the configured grid over a 10-min run. | intake d-3 · team review (reference data set) · ADR-VLT-009 | [evidenced] / thresholds [estimated] |
| F-VLT-4 | The control node sends the galvo node targets for where the ball will be at the moment the spot is placed (compensating the loop delay), not where it was last measured. The prediction uses a constant-velocity or constant-acceleration model estimated from recent ball states; no pendulum model (ADR-VLT-011). Each target carries the predicted velocity and acceleration for interpolation at the galvo node (ADR-VLT-009). | Replay of the recorded swings of the reference data set (NF-VLT-21): the predicted position for the placement time deviates ≤ 10 mm (median) and ≤ 20 mm (95th percentile) from the recorded position at that time. Replay of a synthetic straight-line and a synthetic circular motion within the tested envelope (OQ-14) meets the same bounds. | intake d-4 · DRS review 2026-11-10 · ADR-VLT-011 | [estimated] |
| F-VLT-5 | The galvo node converts each target into mirror angles using the galvo calibration and drives the galvo accordingly. It applies each target at its `t_place_ns` and, between targets, interpolates the position with the target's velocity and acceleration at its own output rate; it never uses a target beyond `t_valid_until_ns` (ADR-VLT-009). | Laser aimed at 9 known cube points (grid): spot lands within 5 mm of each point. Replay of a target stream with known motion: the commanded output at each output tick equals the interpolated position within 0.5 mm, and the first output of each target is applied within 1 ms of `t_place_ns`. | intake d-5 · ADR-VLT-009 | [evidenced] / threshold [estimated] |
| F-VLT-6 | The control node computes the aiming error for every fusion slot: the distance in mm from the fused ball centre to the laser beam line (galvo origin → spot in 3D). The spot in 3D is the near intersection of a camera's spot ray with the ball sphere (`ball_radius_mm`) when the spot lies inside the ball's image disc, or the triangulated spot when at least two cameras see it off the ball. Otherwise the aiming error is reported as unmeasurable (`null`), never as 0 (ADR-VLT-005). | On the reference data set (NF-VLT-21): the computed aiming error lies within 5 mm of the error derived with the same geometry from the annotated spot and ball positions and the hand-measured or fused 3D ball position; frames with a spot seen by one camera off the ball report unmeasurable. | intake d-6 · team review (reference data set) · ADR-VLT-005 | [evidenced] / threshold [estimated] |
| F-VLT-7 | The control node detects a run and reports its hit rate. Start (release): after the ball was displaced more than 100 mm from rest, the moment its speed first exceeds `release_speed_mm_s` (default 100 mm/s), so holding the ball out does not start a run; end: the amplitude falls below 50 mm. A fusion slot is a hit when, in at least one camera that sees both, the spot lies inside the ball's image disc (ADR-VLT-005). Hit rate = time with a hit ÷ run duration; every fusion slot weighs the same, and a slot without valid ball state, without target or with the laser off is a miss. A run ended by the safe state is reported as aborted (ADR-VLT-006). The run result reports duration, hit time, gap time and the outcome. | Replay of a recorded run of the reference data set (NF-VLT-21), including holding the ball before release and gaps without valid fusion output: start and end detected within one swing period of the annotated moments; holding the ball at 150 mm for 5 s does not start a run; reported hit rate equals the hand count ± 1 %; gap time equals the injected gaps. | intake d-7 · ADR-VLT-005/006 | [evidenced] / release threshold [estimated] |
| F-VLT-8 | The laser is off at start-up, during the restart of the control node or the galvo node, whenever the system is not armed and whenever no valid ball state is available. The restart of a single camera node is governed by F-VLT-11/F-VLT-17 (ADR-VLT-007). Exceptions: the galvo calibration scan (F-VLT-13) and the arming check (F-VLT-31) (ADR-VLT-012/013). | Power-up, control/galvo node restarts and covering the ball: a photodiode at the galvo output shows the laser off within 100 ms in every case, and no on-pulse occurs during start-up. A camera node restart with the other two tracking: behaviour per F-VLT-11. | intake d-10 · ADR-VLT-007 | [evidenced] |
| F-VLT-9 | The galvo node clamps every aim to the cube volume, regardless of the target it receives. | Targets outside the cube (incl. NaN, ±∞, far out of range) sent to the galvo node: the commanded mirror angles never leave the cube's angle envelope; NaN/∞ targets switch the laser off. | intake d-11 | [evidenced] |
| F-VLT-10 | The galvo node switches the laser off when it has not received a fresh target for 100 ms. | Stop the control node or unplug its cable while tracking: laser off ≤ 100 ms + 10 ms after the last target. | intake d-12 | [evidenced] / value [estimated] |
| F-VLT-11 | With exactly two camera nodes delivering the ball, tracking continues in degraded mode without re-arming. A camera "delivers" when its latest observation is valid (F-VLT-22/23) and sees the ball; the control node distinguishes per camera *absent* (no valid observation within the observation-age limit), *unsynced*, *present, ball not seen* and *present, ball seen*, and reports this per camera (U-VLT-1). If fewer than two cameras see the ball while at least two are present, the laser is off and tracking resumes without re-arming if two see it again within 1 s; otherwise, and whenever fewer than two cameras are present, the safe state is entered (ADR-VLT-007). | Cover one camera, then stop one camera: tracking continues in both cases, mode = degraded naming that camera, and the reported camera status differs (ball not seen vs. absent); cover the ball for two cameras for 0.5 s: laser off ≤ 100 ms, resumes without re-arming; for 2 s: safe state, re-arming needed; stop two cameras: safe state. | intake d-15 · DRS review 2026-11-10 · ADR-VLT-007 | [evidenced] / 1 s [estimated] |
| F-VLT-12 | Camera calibration is automatic (ADR-VLT-012). ArUco markers fixed to the cube frame at known cube coordinates (marker map) are the reference. At every start each camera node estimates its intrinsics, distortion and pose in cube coordinates from the visible markers and stores the result with its residual. While running it checks its pose against the visible markers at least once per second; if the reprojection error of the markers exceeds `camera_pose_check_px` (default 2 px), the camera is treated as absent (F-VLT-11) and a diagnostic names it. If too few markers are visible at start, the node uses its last stored calibration only if the visible markers confirm it, otherwise it stays absent. | After an automatic calibration the F-VLT-3 acceptance passes, with marker reprojection error ≤ 0.5 px. Calibration at start completes in ≤ 10 s per camera. Turning one camera by a few degrees during tracking: that camera is excluded within 1 s, tracking continues degraded; after a restart in the new position it calibrates itself again and F-VLT-3 passes. | intake d-25 · ADR-VLT-012 | [estimated] |
| F-VLT-13 | Galvo calibration is an automatic scan (ADR-VLT-012): the galvo steps a grid onto the cube's floor and walls, the cameras triangulate every spot seen by at least two of them, and a physical galvo model (pivot point = galvo origin, mirror spacing, scale and offset per axis) is fitted to the measured rays. The control node starts the scan by itself when no valid galvo calibration exists or the arming check fails (F-VLT-31); there is no operator trigger (ADR-VLT-013). The laser is on only during the scan; pressing the kill switch or any safety fault (F-VLT-21) aborts it with the laser off. After `galvo_scan_max_attempts` (default 2) consecutive failed scans, no further scan starts until the system is restarted, and a diagnostic names the reason. Commanded angles stay within configured galvo limits inside the cube (F-VLT-9). The result is stored and loaded at start until the next scan. | Start without a galvo calibration: the scan starts by itself, completes in ≤ 60 s and reports the model residual; afterwards the F-VLT-5 acceptance passes. Pressing the kill switch mid-scan: scan aborted, the previous calibration stays in use. Covering the spot so that every scan fails: after 2 attempts no further scan, laser off, diagnostic shown. After restart the same calibration is loaded. | intake d-26 · ADR-VLT-005 · ADR-VLT-012 · ADR-VLT-013 | [estimated] / spot visibility depends on OQ-7 |
| F-VLT-14 | deferred by the sponsor (2026-11-10, OQ-8) — was: optional redundant control node with takeover ≤ 1 s. Reason: it conflicts with re-arming after the target timeout and adds a membership protocol and a second PTP grandmaster. See §7. | — | intake d-29 | — |
| F-VLT-15 | The galvo node outputs X/Y signals matching the galvo driver's input specification through a converter board, with a defined reaction to errors on the link to that board (laser off). The converter output is at a defined value (mirror centre) from power-up and after a galvo node reset until the first valid target is applied, and the link is checked by read-back so that a link error is detected. | Full-range X/Y sweep measured at the driver input with a multimeter/scope within the driver's specified range; disconnecting the converter board turns the laser off; power-cycling the galvo node shows the driver input at the centre value throughout boot (scope trace). (open: OQ-4, OQ-5) | intake d-36 · DRS review 2026-11-10 | [evidenced] |
| F-VLT-16 | If a camera sees the spot in a frame whose exposure started later than the reported laser-off time (F-VLT-25) plus the laser switch-off delay plus one frame period, the system raises an alarm on the display and enters the safe state. Spots in frames exposed within that action-delay window after a commanded switch-off do not raise the alarm (rev 5: action delay added, as the earlier wording alarmed on every laser-off transition). | Inject a spot-like light (second pointer) while the system is disarmed: alarm shown, system stays/enters safe state. Switch the laser off 20 × during tracking (disarm, cover the ball): no alarm. | intake d-38 · DRS review 2026-11-10 (permanence / action delay) | [estimated] |
| F-VLT-17 | A restarted camera node rejoins the running system without restarting other nodes. | Restart one camera node during tracking: it delivers observations again after its clock is synchronized, mode returns from degraded to normal. | intake d-39 | [estimated] |
| F-VLT-18 | Every node measures its clock offset to the shared clock and reports it; the monitoring display derives the worst pairwise offset (max − min over all synchronized nodes) and flags it when it exceeds π = 1 ms (NF-VLT-24). | Values appear on the display for all 5 nodes, updated at least once per second, together with the worst pairwise offset. Since these offsets are each node's own estimate, the independent cross-check of NF-VLT-5 (LED flash) is still required. | intake d-17 · DRS review 2026-11-10 | [evidenced] |
| F-VLT-19 | The galvo kit's own pattern player ("Programm Board") is disabled or bypassed so that only the galvo node drives the mirrors. | With the galvo node stopped, the mirrors do not move and no pattern is projected. (open: OQ-4) | concept §9 (galvo kit) | [estimated] |
| F-VLT-20 | A node's observations or targets are used only while its clock is synchronized within π/2 = 0.5 ms of the grandmaster (NF-VLT-24); until then the laser stays off. (rev 5: was "within 1 ms" per node, which allows 2 ms between two nodes and contradicts the pairwise bound of NF-VLT-5.) | Start the system with PTP disabled on one camera: its observations are ignored; with PTP disabled on all cameras or on the galvo node, the laser stays off. Offset forced to 0.6 ms on one camera (test profile): its observations are ignored. | concept §9 (PTP start-up) · DRS review 2026-11-10 | [estimated] |
| F-VLT-21 | After the safe state was entered for a safety fault — kill switch pressed (F-VLT-30), target timeout, galvo or control restart, sync loss leaving fewer than two usable cameras or on the galvo node, alarm (F-VLT-16/26), converter link error, fewer than two cameras present, ball not seen by two cameras for > 1 s — the laser stays off until the control node arms again per U-VLT-2, i.e. only after the fault has cleared and ≥ 2 cameras have seen the ball continuously for `auto_rearm_holdoff_ms` (default 2 s) (ADR-VLT-007/013). Every arming increments `arm_epoch`; after a safety fault the galvo node switches the laser on only for targets with a higher `arm_epoch` than at the fault. Proposed (2026-11-10, ADR-VLT-013, PM review pending): an alarm (F-VLT-16/26), or `safety_fault_latch_count` (default 3) safety faults within `safety_fault_latch_window_s` (default 60 s), latches the safe state; the latch clears only when the kill switch is pressed and released, which replaces the deliberate resume decision formerly made with the button. | For each listed fault: the laser stays off after the fault clears until the hold-off has passed. Suppress all `GalvoStatus` messages and inject a galvo timeout: the galvo node still keeps the laser off for targets of the old `arm_epoch`. Inject an alarm, or 3 target timeouts within 60 s: the system stays in the safe state after the hold-off and re-arms only after the kill switch has been pressed and released. | concept §9 (kill switch / re-arm) · ADR-VLT-007 · ADR-VLT-013 | [estimated] / hold-off and latch values [estimated] |
| F-VLT-22 | Data used for fusion and actuation must meet explicit limits for observation age, inter-camera exposure-time difference, prediction horizon and target validity. A newly received target based on expired observations is not fresh. Clock synchronization is checked throughout operation, including the age of the sync status; invalid data is excluded and the existing laser-off rules apply when no valid input remains. A shared-clock correction must not extend the local target-loss timeout. Limits and recovery are open in OQ-11/OQ-12. | Replay delayed observations, a stream of targets based on old frames, expired targets, lost sync and a clock step: invalid inputs never drive the laser, a healthy pair of cameras can still track, and the local target-loss timeout is not extended by a clock change. Boundary tests use the limits agreed in OQ-12. | requirements review 2026-11-06 · F-VLT-3/4/10/20 | [estimated] / limits [unknown] |
| F-VLT-23 | Camera → control and control → galvo messages have one shared, versioned contract. Receivers validate structure, sender identity, finite numeric values, restart session and sequence order, including counter wrap. Duplicate, obsolete-session, incompatible and malformed messages cannot update the accepted state or refresh its timeout. Buffers have finite limits and an explicit overflow policy that prevents processing an ever-growing backlog. | Contract tests inject wrong versions/IDs, truncated messages, NaN/∞, duplicates, reordering, counter wrap and a restart with sequence reset; only current valid inputs update the state. A burst beyond buffer capacity has bounded memory use and expired messages are discarded per F-VLT-22. | requirements review 2026-11-06 · §10 messages, F-VLT-17 | [estimated] |
| F-VLT-24 | Before arming, required configuration and calibration files are validated together: units and coordinate convention, camera IDs and image modes, setup revision, finite parameters and cross-field limits must agree. Missing, corrupt or incompatible required files keep the laser off and produce a specific local diagnostic, also available to monitoring when connected. Peers must not combine data or targets from different setup revisions. | Remove/corrupt a file, swap camera calibrations, change image mode or setup revision on one node, and set invalid timing/geometry limits: arming is refused for an invalid local setup; incompatible peer data is rejected. A matching validated setup passes F-VLT-3/5 after restart. Coordinate and calibration-procedure details remain OQ-13. | requirements review 2026-11-06 · F-VLT-12/13, §10 configuration | [estimated] |
| F-VLT-25 | Proposed (DRS review 2026-11-10): the galvo node sends a `GalvoStatus` message (§10) to the control node with every applied target and at least every 50 ms. It contains the actual laser state, the reason for laser-off (startup, not armed, timeout, non-finite target, link error, safe state), the last applied target `seq` and the time the output was applied. The control node uses the actual laser state, not its own command, for F-VLT-16 and hit counting. When the galvo `session_id` changes (galvo restart), the control node enters the safe state, so that a restarted galvo node never switches the laser on without re-arming. | Restart the galvo node while armed and tracking: laser stays off until re-armed per U-VLT-2; display shows galvo restart. Force each laser-off reason: the status reports it within 50 ms. Stop status messages: control node enters safe state within the target timeout. | DRS review (effect monitoring, reintegration) · F-VLT-8/16/21 | [estimated] |
| F-VLT-26 | Proposed (DRS review 2026-11-10): while armed, the control node monitors the effect of the actuator, not only the command. If the spot is seen outside the cube volume, or the aiming error stays above a configured limit while the ball is tracked and the laser is on for longer than a configured time, the system switches the laser off, raises an alarm and enters the safe state. The limit and time are set so that normal tracking (NF-VLT-1) never trips it. | Block one mirror mechanically (or command a fixed calibration offset in a test profile) while armed: laser off and alarm within the configured time; spot projected outside the cube by a second pointer: alarm. Three normal runs: no false trip. | DRS checklist (safety-relevant actuator: effect monitored; test with a blocked actuator) | [estimated] |
| F-VLT-27 | Proposed (DRS review 2026-11-10): before an observation enters the ball state, the control node checks its plausibility. With three cameras, a camera whose reprojection residual exceeds a configured limit is excluded for that step and counted as not delivering. A ball state outside the cube volume is not used for aiming. No motion model of the pendulum is used for plausibility. The pendulum only makes the setup reproducible; the ball's motion is not restricted to it (sponsor, 2026-11-10). Rejected steps count as gaps (OQ-10), never silently as hits. | Replay with one camera reporting a false ball (reflection, synthetic offset of 30 px): that camera is excluded and the 3D error stays within F-VLT-3 limits; a ball state outside the cube is not aimed at; rejection counts are reported per run. | DRS checklist (fault hypothesis — value failures of one camera) · F-VLT-3 | [estimated] |
| F-VLT-28 | Proposed (DRS review 2026-11-10): the nodes can be powered and started in any order. Each node starts in a defined ground state (laser off, converter at centre, unarmed, no ball state, no history from a previous session) and the system reaches "ready to arm" without manual sequencing within a configured time after the last node is up (PTP convergence included). A controlled shutdown switches the laser off and centres the mirrors before the galvo node stops. | Power up the five nodes in three different orders: ready to arm in every case within the configured time; laser off throughout (photodiode). Shut down via the documented procedure: laser off before mirrors stop being driven. | DRS checklist (reintegration — ground state) · F-VLT-8/17/20 | [estimated] |
| F-VLT-29 | Proposed (DRS review 2026-11-10): the control node and the galvo node log every mode and safety transition (arm, disarm, safe state with reason, safety latch set/cleared, kill switch, degraded with camera, alarm, sync lost/regained, arming refused with reason, galvo scan started/failed/given up, setup invalid, run start/end with its result) with shared-clock time and local monotonic time; camera nodes log their own diagnostics (calibration failed, pose check failed) the same way (U-VLT-7). The log contains no images, is written without blocking the loop, and its size is bounded per session. | After a fault-injection session, every injected fault appears in the log with its reason, in the right order; log writing throttled to the SD card's worst case does not change loop timing (NF-VLT-18). | DRS review (verification of F-VLT-8 … 11, fault injection evidence) · NF-VLT-11 | [estimated] |
| F-VLT-30 | The kill switch has a sense contact read by the galvo node on a GPIO pin; its state is reported in `GalvoStatus` (`laser_off_reason = kill_switch`), and pressing it puts the system into the safe state (ADR-VLT-007). The kill switch is the operator's only physical control: pressing it disarms, and releasing it allows the control node to re-arm per U-VLT-2 (ADR-VLT-013). The supply interruption itself stays independent of software (NF-VLT-3). | Press the kill switch during tracking: laser off immediately (hardware), display shows kill switch within 100 ms, safe state entered; release: laser stays off until the control node re-arms after the hold-off (F-VLT-21). Unplug the sense wire: reported as kill switch pressed (fail-safe reading). | sponsor 2026-11-10 (OQ-11) · ADR-VLT-007 · ADR-VLT-013 | [estimated] |
| F-VLT-31 | Before every arming, the galvo node projects 3 check points onto floor or walls (points occluded by the ball are replaced), and the cameras measure them. If any lies more than 5 mm from its commanded position, arming is refused, a diagnostic names the reason, and the control node starts a galvo calibration scan by itself (F-VLT-13) (ADR-VLT-012/013). The check takes ≤ 1 s with the laser on inside the cube and runs without an operator. | Shift the galvo mounting slightly (or load a calibration with an offset): arming refused with the diagnostic, a scan starts by itself, and afterwards the check passes and the system arms; correct calibration: arming succeeds and the check takes ≤ 1 s (photodiode / log). | sponsor 2026-11-10 · ADR-VLT-012 · ADR-VLT-013 | [estimated] |
| F-VLT-32 | Proposed (2026-11-10): on request in the configuration, the control node records a session — every observation, target, galvo status, mode event and timestamp the loop uses, no images. Recording never blocks the loop and its size per session is bounded. A recorded session can be fed into the hardware-free replay (NF-VLT-22) and yields the same decisions. | Record a 10-min session and replay it offline: mode changes, validity decisions and run results identical; NF-VLT-18 unchanged with recording on; recording stops at its size limit without affecting the loop. | sponsor 2026-11-10 (integration and debugging) · NF-VLT-11/22 | [estimated] |
| F-VLT-33 | Proposed (2026-11-10): dry-run modes set in the configuration — *laser disabled*: the whole loop runs and the mirrors move, the laser enable stays off; *galvo disabled*: tracking and monitoring only, no galvo output. The mode is shown on the display. | In each mode a full run produces tracking and monitoring data; a photodiode shows the laser never on; in *galvo disabled* the converter output stays at centre. | sponsor 2026-11-10 (integration and debugging) | [estimated] |

## 4. User Interaction Requirements

| ID | Requirement | Acceptance | Origin | Evidence |
| --- | --- | --- | --- | --- |
| U-VLT-1 | The monitoring laptop shows live: mode (safe / armed / tracking / degraded + missing camera), current aiming error, hit rate of the current and last run, camera status per node (absent / unsynced / ball not seen / ball seen, F-VLT-11), galvo status and laser-off reason (F-VLT-25), clock offset per node and worst pairwise offset (F-VLT-18), and the camera images with the detected ball and spot marked. | During a run every listed value is visible and updates at least once per second; images at ≥ 1 per second per camera. | intake d-18 | [evidenced] |
| U-VLT-2 | Arming and disarming are decided by the control node software (ADR-VLT-013). The only physical operator control is the kill switch (NF-VLT-3, F-VLT-30); there is no arming button. The control node arms, at start and after a safety fault alike, when all of these hold: the kill switch is released, no safety fault is active or latched (F-VLT-21), the setup is valid (F-VLT-24), ≥ 2 cameras have seen the ball continuously for `auto_rearm_holdoff_ms`, and the arming check passes (F-VLT-31). It disarms on every safety fault (F-VLT-21) and when the kill switch is pressed. No network command or other control path arms, disarms or starts a calibration. F-VLT-8 … F-VLT-10, F-VLT-21 and NF-VLT-3 apply unchanged. | After start and after every safety fault: the laser switches on only after ≥ 2 cameras have seen the ball for the hold-off and the arming check has passed; with the kill switch pressed or the setup invalid, it never arms. Pressing the kill switch disarms. No network command arms or disarms the system, and the setup has no physical operator input other than the kill switch (inspection). | intake d-24 · ADR-VLT-013 | [evidenced] |
| U-VLT-3 | dropped by the sponsor at the PM review (2026-11-02) — was: "recalibration recommended" hint on a systematic aiming error. | — | intake d-27 | — |
| U-VLT-4 | Proposed (2026-11-10): a system health overview on the monitoring laptop shows per node: status, software version, setup revision, the node's shared-clock counter (its current shared-clock time, the local monotonic counter, the clock's frequency correction and the number of clock steps since start) next to the measured offset (F-VLT-18), CPU and RAM, message rates in and out, dropped and rejected messages, and the latency per stage of the tracking chain (median and 99th percentile over the last second; full statistics in U-VLT-6). Every value that has a limit in these requirements is shown with that limit and highlighted when outside; a version or setup-revision mismatch between nodes, a clock counter that stops, jumps or runs at a different rate than the others are highlighted too. Clock counters are sampled together with a shared-clock timestamp, so values from different nodes can be compared despite transmission delay. | Inject one fault each — unsynced camera, clock step on one node, frozen clock (process stopped), overloaded camera node, wrong software version, delayed messages: within 2 s the highlighted value names the faulty node and stage. All values update at least once per second; NF-VLT-6/8 still hold. | sponsor 2026-11-10 (integration and debugging) | [estimated] |
| U-VLT-5 | Proposed (2026-11-10): the fused 3D ball position, the predicted target and the measured spot are drawn into every camera image on the monitoring laptop, next to that camera's own detection. | Shift one camera's calibration by 5 px: its image shows the drawn position visibly off the detected ball while the other two match; with a correct setup the drawn and detected positions agree within the F-VLT-3 tolerance. | sponsor 2026-11-10 (integration and debugging) | [estimated] |
| U-VLT-6 | Proposed (2026-11-10): chain delay statistics. For every fusion step the delay of each stage of the tracking chain is traced — capture/readout, detection, camera → control transmission, waiting for fusion, fusion and prediction, control → galvo transmission, waiting until placement, galvo output — per camera where a stage is per camera; mirror settling, which the nodes cannot see, is shown from the independent measurement (NF-VLT-29). For each stage and for the end-to-end delay the monitoring laptop shows count, minimum, maximum, mean, standard deviation (jitter), median, 95th and 99th percentile, over three windows: last second, current run, whole session (resettable on the laptop). An overview shows how the end-to-end delay splits into stages (share of each stage) and a histogram of the end-to-end delay with the 30 ms limit (NF-VLT-18) and each stage's budget marked; deadline misses and discarded targets are counted. At the end of each run and session the statistics are saved on the laptop as a file (numbers only) for the test report. | 10-min run: statistics for all stages and windows shown and saved; the sum of stage means equals the end-to-end mean within 1 ms; adding a 5 ms delay in one stage (test profile) shows up in that stage's statistics and share within 2 s, not in the others; values agree with the logged per-stage timestamps of NF-VLT-18. | sponsor 2026-11-10 (integration and debugging) · NF-VLT-18/26/29 | [estimated] |
| U-VLT-7 | Operating the demo requires the monitoring laptop: it is the operator's only status display, and no node has a local indicator (sponsor 2026-11-10, review gap G2). Without the laptop the system still tracks and stays safe (NF-VLT-7), but the operator sees only the laser. For this reason: (a) when the laptop connects or reconnects, it shows within 2 s the current state of every node: mode, armed or safe, active safety latch with its cause, kill switch, and the reason the system is not armed (e.g. kill switch pressed, setup invalid, arming check failed, galvo scan running or given up, fewer than two cameras). It also shows the most recent diagnostics and alarms since the node started, not only events after the connection. (b) A node from which no monitoring data has arrived for 2 s is shown as stale, and its last values are marked as not current. (c) Every diagnostic and alarm shown on the laptop is also written to the local log (F-VLT-29), so faults that occur without the laptop can be read afterwards. | Start the system without the laptop, inject an alarm (safety latch) and an invalid setup on one camera, then connect the laptop: within 2 s it shows the latch with its cause, the setup error naming the camera, and the reason the system is not armed. Stop one node's monitoring (SIGSTOP of its sender): that node is shown as stale within 2 s. After a session without the laptop, every injected fault appears in the log. | sponsor 2026-11-10 (review gap G2) · NF-VLT-7 · F-VLT-21/24/29/31 | [estimated] |

## 5. Non-Functional Requirements

| ID | Requirement | Acceptance / measure | Origin | Evidence |
| --- | --- | --- | --- | --- |
| NF-VLT-1 | Acceptance of the demo: in a run (F-VLT-7) from release until the amplitude is below 50 mm, the hit rate is at least 80 %, with all three cameras and with each of the three two-camera pairs (degraded mode; sponsor, OQ-14). | System-reported hit rate ≥ 80 % in 3 of 3 consecutive runs with three cameras and in 3 of 3 consecutive runs for each camera pair (the third camera stopped); an aborted run counts as failed. | intake d-8 · sponsor 2026-11-10 (OQ-14) · ADR-VLT-006 | [evidenced] |
| NF-VLT-2 | Laser safety (IEC 60825-1): the laser is visible and at most Class 2 (≤ 1 mW). The student team is responsible for laser safety in the lab (OQ-6) and records its laser-safety procedure before the first laser-on test. | Laser label / datasheet shows Class 1, 1M, 2 or lower; recorded in the setup documentation together with the team's laser-safety procedure and the team role responsible. (open: OQ-2) | intake d-9 · sponsor 2026-11-10 (OQ-6) | [evidenced] |
| NF-VLT-3 | A physical kill switch cuts the laser supply independent of all software. | Kill switch pressed during tracking: laser off immediately, with all nodes still running. | intake d-13 | [evidenced] |
| NF-VLT-4 | dropped by the sponsor at the PM review (2026-11-02) — was: hardware watchdog switching the laser off when the galvo node software stops. Residual risk: see §7. | — | intake d-14 | — |
| NF-VLT-5 | All nodes share one clock synchronized over Ethernet (software PTP, ADR-VLT-002) with an offset ≤ 1 ms between any two nodes; every observation carries its exposure time in that clock. | The worst pairwise offset derived per F-VLT-18 stays ≤ 1 ms during a 10-min run (each node ≤ 0.5 ms to the grandmaster, NF-VLT-24); cross-check: one LED flash seen by all cameras yields exposure times within 1 ms + one frame period. | intake d-16 | [evidenced] |
| NF-VLT-6 | Sending monitoring data never blocks the tracking loop; under back-pressure monitoring data is dropped, not queued. | Monitoring server paused (SIGSTOP) during a run: loop timing (NF-VLT-18) unchanged, node memory does not grow. | intake d-19 | [evidenced] |
| NF-VLT-7 | Tracking and safety behave identically with and without the monitoring laptop connected. | NF-VLT-1 and F-VLT-8 … F-VLT-11 pass with the laptop absent. | intake d-20 | [evidenced] |
| NF-VLT-8 | Monitoring traffic of all nodes together stays ≤ 20 Mbit/s; camera images are sent at ≤ 5 per second, ≤ 320 × 240 px. | Switch/port counters or capture over a 10-min run: total monitoring traffic ≤ 20 Mbit/s. | intake d-21 | [estimated], confirmed by sponsor |
| NF-VLT-9 | Loop timing (NF-VLT-18) and the demo acceptance (NF-VLT-1) are verified both with monitoring on (at its maximum rate) and off. | Both measurements recorded in the test report. | intake d-22 | [evidenced] |
| NF-VLT-10 | No network message controls the running loop: the loop processes on every node have no command interface, and nothing over the network arms, disarms, starts a calibration or changes running behaviour. The monitoring software is observe-only (ADR-VLT-003). Separate from this, admin access is allowed (ADR-VLT-014). It is authenticated SSH, key only with no password login, from devices on the demo network (NF-VLT-28). It covers installing and updating software, starting, stopping and restarting node software, reboot and shutdown, editing configuration and calibration files, and fetching logs, recordings and statistics. Configuration and calibration changes take effect only when the node software restarts, and that restart follows the existing rules (F-VLT-8/17/21). | Port scan of every node: listening ports only for SSH, PTP and the loop's own messages; the loop's message ports accept only the message types of §10 from their expected senders (F-VLT-23). SSH with a password is refused. Edit the configuration of a running node: behaviour unchanged until restart. Restart the galvo software over SSH while armed: safe state, re-arming per U-VLT-2. | intake d-23 · ADR-VLT-003 · ADR-VLT-014 | [evidenced] |
| NF-VLT-11 | Camera images are shown live only and are not stored by default (GDPR). | After a run, no image files on any node or on the laptop unless storage was explicitly enabled in the configuration. Exception: the reference data set (NF-VLT-21). | intake d-28 | [evidenced] |
| NF-VLT-12 | The system runs continuously for 10 minutes (several runs) without a restart. | 10-min soak: no node restart, no memory growth > 10 %, NF-VLT-1 still met in the last run. | intake d-30, sponsor | [evidenced] |
| NF-VLT-13 | Every node can be set up reproducibly from the repository by a script; code is version-controlled, reviewed before merge, and every node's code has automated tests. | A fresh SD card set up only with the documented script runs the node; the test suite runs with one command. | intake d-31 | [evidenced] |
| NF-VLT-14 | Product code lives under `src/` with one subfolder per node type (`src/camera/`, `src/control/`, `src/galvo/`); the monitoring server has its own subfolder. | Repository layout inspection. | intake d-32, ADR-VLT-001 | [evidenced] |
| NF-VLT-15 | All nodes are Raspberry Pi 3 on one wired Ethernet switch. | Setup documentation lists the hardware; all tests run on it. | intake d-33, ADR-VLT-001 | [evidenced] |
| NF-VLT-16 | The laser can be switched on and off by the galvo node in software (e.g. TTL input or switched supply). | Galvo node toggles the laser 10 × per second for 10 s; photodiode confirms every transition. (open: OQ-2) | intake d-34 | [evidenced] |
| NF-VLT-17 | Laser colour, ball colour and background are chosen so that the spot is distinguishable on the ball and the ball against the background for every camera. | Proven by F-VLT-1 and F-VLT-2 passing on the reference data set (NF-VLT-21), evaluated separately for each camera. (open: OQ-2, OQ-7) | intake d-35 · team review (reference data set) | [evidenced] / threshold [estimated] |
| NF-VLT-18 | End-to-end tracking transaction T1 (firm, ADR-VLT-008): from the exposure of a frame to the spot being placed at the corresponding target, p99 ≤ 30 ms, with a budget per stage (capture/readout, detection, transmission, fusion and prediction, transmission, galvo output incl. interpolation, mirror settling) defined in the architecture. A target whose validity has expired on arrival is discarded and counts as a miss. | Per-stage timestamps logged over a 10-min run plus the independent measurement of NF-VLT-29: 99th percentile of the end-to-end time ≤ 30 ms; maximum and count of discarded targets reported; each stage within its budget. | intake d-37, sponsor · ADR-VLT-008 | [evidenced] |
| NF-VLT-19 | Each node stays within ≤ 75 % average CPU and ≤ 50 % RAM on the Pi 3 during a run. | Resource log during a 10-min run. | intake d-40 | [estimated], confirmed by sponsor |
| NF-VLT-20 | Clock precision (NF-VLT-5) holds with monitoring traffic at its maximum (NF-VLT-8). | Clock offsets ≤ 1 ms during a run with monitoring at maximum rate. | concept §9 (PTP vs. monitoring on one switch) | [estimated] |
| NF-VLT-21 | A reference data set is recorded once with the final setup: time-synchronized frames of all three cameras covering a resting ball at ≥ 10 positions spread over the cube, swinging runs (release until amplitude < 50 mm), the spot on and off the ball, laser off, and frames without the ball. Every frame is annotated with the image positions of ball and spot, in the same pixel coordinates as the detection (origin top-left, v downward); for the resting positions the 3D ball position is measured by hand. The set and its annotations are stored in the repository and are the input of the automated detection, triangulation, aiming-error, prediction and run tests. It is an explicit exception to NF-VLT-11 on the condition that no people appear in the frames. After a significant setup change (camera, background, ball, laser or lighting) the set is recorded again. | The data set exists in the repository with an annotation file that passes a schema check, covers every listed case for all three cameras, and contains no people (reviewed). | team review (feedback on F-VLT-1 … F-VLT-3) | [evidenced] |
| NF-VLT-22 | The shared processing and decision logic can be tested without cameras, Pis or galvo hardware by replaying the reference data set and synthetic message/time events through the same logic used on the nodes, with a simulated clock and captured actuator output. Replay includes two-camera combinations, loss/delay/reordering, node restart and sync loss. It adds no live command path to the monitoring laptop. | One documented command runs the replay suite without hardware. Repeating the same input/event schedule gives the same validity decisions, state transitions and run result; numeric outputs satisfy the existing tolerances. Fault cases check F-VLT-22 … F-VLT-24. Physical timing and aiming acceptance still require the actual setup. | requirements review 2026-11-06 · NF-VLT-13/21 | [estimated] |
| NF-VLT-23 | Proposed (DRS review 2026-11-10) — **fault hypothesis.** Fault-containment regions: each of the five nodes, the Ethernet switch, converter board + galvo driver, the laser module. **Tolerated (k = 1, degree 2-of-3):** crash, omission or timing failure of one camera node, including its restart (F-VLT-11/17), and a detectable value failure of one camera while three deliver (F-VLT-27). **Detected and turned into the safe state (fail-safe, not tolerated):** crash/omission of the control node or of the switch (via F-VLT-10), loss of the PTP grandmaster or sync loss (F-VLT-20/22), galvo node restart (F-VLT-25), converter link error (F-VLT-15), a second camera fault, actuator misbehaviour (F-VLT-16/26). galvo node software hang (via the on-chip watchdog, NF-VLT-30, within its interval). **Not covered — residual risk, kill switch only (NF-VLT-3):** a hang shorter than the watchdog interval (laser frozen at its last clamped aim), undetected consistent value failures of two cameras, a laser stuck on in hardware. **Fault frequency assumption:** at most one fault at a time; a second fault is assumed no earlier than 10 s after the system has recovered from the first. | Fault-injection campaign on the real setup with one test per listed fault, plus at least two faults beyond the hypothesis (two cameras at once; camera fault during control restart): each tolerated fault keeps tracking, each detected fault ends in laser off within its deadline (NF-VLT-26), each beyond-hypothesis case ends in laser off or is recorded as residual. Results logged per F-VLT-29. | DRS checklist (fault hypothesis, k, degree of redundancy, fault injection beyond the hypothesis) | [estimated] / inter-fault time [estimated] |
| NF-VLT-24 | Proposed (DRS review 2026-11-10) — **global time base.** The control node is the PTP grandmaster: its failure already forces the safe state, so the clock master shares the fate of the node that needs it. Precision π ≤ 1 ms pairwise (NF-VLT-5), therefore every node stays within π/2 = 0.5 ms of the grandmaster. Global granularity g for cross-node comparisons is fixed with g > π (reasonableness condition); timestamps stay ns-resolved in messages, but the order or duration of events on different nodes is only claimed beyond ±2g, and the fusion error budget (OQ-14) includes the timestamp uncertainty × maximum ball speed. Local timeouts (F-VLT-10, F-VLT-22) use each node's monotonic clock, never the PTP clock. No other time service (NTP, systemd-timesyncd, RTC set) adjusts the clocks. | Configuration check on every node: only PTP adjusts the clock. Stop PTP on the grandmaster during tracking: nodes flag unsynced within the sync-status age (OQ-12) and the laser goes off. Step the PTP clock by 50 ms on the galvo node: the target-loss timeout still fires at 100 ms ± 10 ms. The value of g is recorded in §10 once OQ-1/OQ-12 fix the camera timestamp source. | DRS checklist (global time base π, g > π; reasonableness; ±2g) · ADR-VLT-002 | [estimated] |
| NF-VLT-25 | Proposed (DRS review 2026-11-10) — **fail-safe laser enable.** The laser emits only while the galvo node actively drives its enable signal. Unpowered, booting, rebooting or crashed (GPIO released) galvo node, broken enable wire or floating input → laser off, by hardware design (external pull-down, GPIO pin whose boot default is low). | With the laser supply on and the kill switch closed: power the galvo node off, reboot it, kill the galvo process, unplug the enable wire — a photodiode shows the laser off in every case, including during the whole boot. | DRS review (safety-relevant actuator; ground state) · NF-VLT-16, F-VLT-8 | [estimated] |
| NF-VLT-26 | Decided by the sponsor 2026-11-10 (OQ-12, ADR-VLT-008) — **real-time transactions and deadline classes.** **T1 tracking** (exposure → spot placed) is *firm*. Target p99 ≤ 30 ms; a target whose validity (F-VLT-22) has expired on arrival is discarded, never applied late, and counts as a miss. **T2 target-loss shutdown** (last valid target → laser off) is *hard* at 100 ms + 10 ms (F-VLT-10). **T3 unsafe-condition shutdown** (detection of < 2 cameras, sync loss, alarm, actuator fault → laser off) is *hard* at 100 ms from the first frame exposure that shows the condition. **T4 monitoring** is *soft*, best effort (NF-VLT-6). **T5 camera reintegration** has no deadline. Hard deadlines are met by the software design and backed by the kill switch; the OS is not real-time, so they are verified by measurement of the maximum, not proven. | 10-min run with monitoring at maximum (NF-VLT-9) plus the fault campaign (NF-VLT-23): T1 p99 and maximum reported, late targets counted; T2 and T3 maximum ≤ their deadline in every injected case, measured independently (NF-VLT-29). | DRS checklist (end-to-end deadline, per-stage budget) · NF-VLT-18, OQ-12 | [estimated] |
| NF-VLT-27 | Proposed (DRS review 2026-11-10) — **state messages and load hypothesis.** `Observation`, `Target` and `GalvoStatus` are state messages: the newest valid message replaces the previous one (update in place), there is no queue of old values, no retransmission and no acknowledgement. This makes the overflow policy of F-VLT-23 concrete. Under overload every node processes the newest frame or message and skips older ones; latency never grows with load. Load hypothesis per channel at peak (values fixed when OQ-1/OQ-15 fix the rates): camera → control: frame rate × observation size per camera; control → galvo: fusion rate × target size; galvo → control: status rate; PTP: sync rate; monitoring ≤ 20 Mbit/s (NF-VLT-8); total ≤ 50 % of the 100 Mbit/s link of each node. | Load test at 1.5 × the nominal camera frame rate (synthetic observations) and monitoring at maximum: end-to-end latency of the newest frame stays bounded (no growing backlog, no thrashing), skipped frames are counted, node memory constant. Port counters confirm each channel within its hypothesis. | DRS checklist (load hypothesis per channel and node; freedom from thrashing; permanence) · F-VLT-23, NF-VLT-8/19 | [estimated] |
| NF-VLT-28 | Proposed (DRS review 2026-11-10) — **node platform and isolated network.** The five nodes and the monitoring laptop are the only devices on a dedicated switch with static addresses and no uplink to the lab network or the internet; for administration (NF-VLT-10) a team machine may be connected in addition, but not during acceptance runs. Since that network is trusted, sender identity (F-VLT-23) is checked by ID and address, without cryptographic authentication. Each node runs a minimal OS image set up by the script of NF-VLT-13: no desktop, Wi-Fi and Bluetooth off, automatic updates and NTP off, and the loop processes at real-time priority with the remaining load on other cores. | During acceptance runs the switch port list shows only the six devices; no default route on any node. Setup-script check on a fresh SD card: listed services disabled, loop processes have the configured priority. NF-VLT-18 measured with this image. | DRS review (composability, hidden channels via shared resources) · NF-VLT-10/13/15 | [estimated] |
| NF-VLT-29 | Proposed (DRS review 2026-11-10) — **independent timing measurement.** End-to-end timing (T1) and shutdown deadlines (T2, T3) are verified with an instrument independent of the node clocks, not only from the nodes' own timestamps. For example, an LED flash in the cameras' view, timed by a separate microcontroller or scope, and a photodiode at the galvo output or on the ball measure exposure → spot placed and event → laser off. The nodes' per-stage timestamps (NF-VLT-18) give the budget breakdown; the independent measurement gives the truth. | The test report contains, for T1, T2 and T3, the independent measurement (≥ 100 samples each) next to the self-reported values; their difference is stated. | DRS checklist (measurement per stage on the target; target measurement) · NF-VLT-18, OQ-12 | [estimated] |
| NF-VLT-30 | The galvo node enables the Pi's on-chip hardware watchdog, fed by its output loop; if the loop stops, the Pi resets within `galvo_watchdog_s` (default 1 s), and the reset switches the laser off by NF-VLT-25 (ADR-VLT-010). | Freeze the galvo output loop (SIGSTOP) while the laser is on: photodiode shows the laser off within the watchdog interval + boot-time pull-down; the node reboots into the ground state (F-VLT-28). | sponsor 2026-11-10 (OQ-16) · ADR-VLT-010 | [estimated] |
| NF-VLT-31 | Proposed (2026-11-10): each node type can run on the real setup while any of its peers is replaced by a simulator sending the same messages — a camera simulator playing recorded data, a galvo simulator recording the targets it receives, a control simulator sending scripted targets. Simulators never drive the laser. | Each node passes its node tests with all peers simulated and with any mix of real and simulated peers; the health overview (U-VLT-4) marks simulated nodes. | sponsor 2026-11-10 (integration and debugging) · NF-VLT-13/22 | [estimated] |

### Load and growth model

| Quantity | At launch | 1 year | 3 years | Peak factor | Evidence |
| --- | --- | --- | --- | --- | --- |
| Users / concurrent at peak | 1 operating team (11 students), 1 monitoring laptop | — (project ended) | — | 1 | [evidenced] |
| Requests per second at peak | per camera node: one observation per frame (frame rate open, OQ-1/OQ-12); control → galvo: one target per fusion step (cadence open, OQ-10/OQ-12) | — | — | 1 | [unknown] |
| Data volume / largest table or collection | none stored; monitoring stream ≤ 20 Mbit/s live | — | — | — | [evidenced] |
| Calls to external services per minute vs. their limit | none; internal limit 100 Mbit/s Ethernet per Pi 3 | — | — | — | [evidenced] |

- **Scale decision:** single installation is enough — scale-out deferred, reason: one installation, one presentation, project ends afterwards. The relevant capacity limits are per-node CPU (NF-VLT-19), link bandwidth (NF-VLT-8) and the deadline (NF-VLT-18).

### Operating cost model

Fixed running cost only — no usage-dependent drivers (hardware bought once; no cloud or metered services).

- **Cost per typical action:** none.
- **Covered by:** not relevant — expected load n.a., heaviest user n.a.

## 6. Integration Points

| System / module | Direction | Contract (schema, protocol, version) | Owner |
| --- | --- | --- | --- |
| MIPI camera module on each camera node | in | Linux camera stack on Raspberry Pi OS; image mode, exposure timestamp semantics and measured timing must support NF-VLT-18 (open: OQ-1/OQ-12; the earlier ≈ 90 fps figure was an estimate, not a derived minimum) | student team |
| Kernel PTP (software timestamping) | both | IEEE 1588 over UDP on the demo switch (ADR-VLT-002) | student team |
| Galvo driver (IMLCDRS "10K 3D DIY Laser Galvo … 15V") | out | X/Y analog input — signal type, range, connector open (OQ-4) | student team |
| Converter board galvo node → galvo driver | out | open (OQ-5); digital link from the galvo node (e.g. SPI/I2C) → analog X/Y | student team |
| Laser module | out | software switch input (TTL or switched supply), Class ≤ 2 (open: OQ-2) | student team |
| Kill switch | out (hardware) + in | interrupts the laser supply; sense contact on a GPIO of the galvo node (F-VLT-30) | student team |
| Arming button | — | removed 2026-11-10 (ADR-VLT-013): arming is done by software; the kill switch is the only physical control | — |
| Monitoring laptop | out (from nodes) | push-only monitoring messages (§10), observe-only (ADR-VLT-003) | student team |

## 7. Out of Scope

- Manual calibration procedures — replaced by automatic calibration (ADR-VLT-012, superseding ADR-VLT-004); only the marker map is measured by hand once, when the cube frame is built.
- Storing camera images by default — GDPR, not needed for the demo (NF-VLT-11).
- Long-term operation, OTA updates, flash-wear management — the project ends after one presentation.
- Certification (CE, EMC, electrical safety, functional safety / SIL) — one-off lab demo, not placed on the market; off-the-shelf boards and supplied power supplies used as delivered.
- Any control path from the monitoring laptop, any network control of the running loop, including over SSH — ADR-VLT-003, ADR-VLT-014, U-VLT-2. SSH for administration is in scope (NF-VLT-10).
- Redundancy of the galvo node and of camera nodes beyond "two of three" — failures lead to the safe state.
- Redundant control node (F-VLT-14) — deferred by the sponsor 2026-11-10 (OQ-8): conflicts with re-arming after the target timeout and needs a membership protocol and a second PTP grandmaster.
- External hardware watchdog for the laser (NF-VLT-4 dropped at the PM review) — replaced by the Pi's on-chip watchdog on the galvo node (NF-VLT-30, ADR-VLT-010). Residual risk: a hang shorter than the watchdog interval leaves the beam frozen at its last clamped aim inside the cube (Class ≤ 2) until the reset or the kill switch (NF-VLT-3).
- Recalibration hint (U-VLT-3 dropped at the PM review) — the aiming error on the display (U-VLT-1) is the operator's cue to recalibrate.
- Hardware camera trigger — clock-based fusion instead (ADR-VLT-002).
- Local status indicators on the nodes (LED, buzzer, display) — the monitoring laptop is required to operate the demo and is the only status display (U-VLT-7); safety does not depend on it (NF-VLT-7).
- Arming button and any physical operator control other than the kill switch — arming, disarming, galvo scan and arming check are decided by the control node software (ADR-VLT-013).
- Tracking more than one ball, or objects other than a ball on a string.

## 8. Resolved Questions & ADRs

| OQ | Question | Decision | ADR |
| --- | --- | --- | --- |
| — | Node topology and network | Five Pi 3 nodes (3 camera, control, galvo) on wired Ethernet | decisions/ADR-VLT-001-five-node-topology.md |
| — | Time base across nodes | Software PTP (kernel), ≤ 1 ms | decisions/ADR-VLT-002-software-ptp-clock.md |
| — | Where the display runs, laptop authority | Separate laptop, nodes push, observe only | decisions/ADR-VLT-003-observe-only-monitoring-laptop.md |
| — | Calibration method | Manual in v1, automatic galvo calibration later — superseded 2026-11-10 | decisions/ADR-VLT-004-manual-calibration-v1.md |
| OQ-13 (procedure part) | Calibration procedure | Automatic: cameras from frame markers at every start + continuous pose check; galvo scan on demand (since ADR-VLT-013 started by the control node, not by a button); 3-point check at arming | decisions/ADR-VLT-012-automatic-calibration.md |
| — (review gap G1) | Operator control: button semantics, disarm, calibration trigger in `auto` mode | No arming button; the kill switch is the only physical control; arming, disarming, galvo scan and arming check are decided by the control node software | decisions/ADR-VLT-013-software-control-kill-switch-only.md |
| — (review gap G3) | How is the system administered if no node accepts network commands? | Key-only SSH for administration; the loop has no command interface; configuration changes take effect at restart | decisions/ADR-VLT-014-admin-access-separate-from-loop-control.md |
| — (review gap G2) | Operator feedback without the laptop | The laptop is required to operate; no local indicators; on connect it shows current state and recent diagnostics, flags stale nodes; everything is also logged locally | → U-VLT-7, F-VLT-29 |
| OQ-13 (conventions) | Coordinate conventions | Cube frame (marked floor corner, right-handed, mm, z up) and rest position defined in §2; image coordinates of annotations = detection; the rest goes to the architecture | → §2, NF-VLT-21 |
| — | Success criterion and test window | 80 % hit rate from release to amplitude < 50 mm | → NF-VLT-1, F-VLT-7 |
| — | Laser class | ≤ Class 2 | → NF-VLT-2 |
| — | Camera failure behaviour | Degraded mode with two cameras | → F-VLT-11 |
| — | End-to-end deadline | 30 ms (sponsor) | → NF-VLT-18 |
| — | Continuous operation | 10 min (sponsor) | → NF-VLT-12 |
| — | Numeric defaults (laser timeout 100 ms, monitoring ≤ 20 Mbit/s, CPU ≤ 75 % / RAM ≤ 50 %, run start > 100 mm) | Accepted by the sponsor | → F-VLT-7, F-VLT-10, NF-VLT-8, NF-VLT-19 |
| — | How to verify detection and triangulation without hand-placed checks every time | Recorded, annotated reference data set; automated tests against it (team review) | → NF-VLT-21, F-VLT-1 … F-VLT-4, F-VLT-6, F-VLT-7, NF-VLT-17 |
| — | PM review: hardware watchdog, recalibration hint, redundant control node | NF-VLT-4 and U-VLT-3 dropped; F-VLT-14 optional (nice to have) | → §7, F-VLT-14 |
| OQ-6 | Who is responsible for laser safety in the lab? | The student team | → NF-VLT-2 |
| OQ-8 | Build the redundant control node? | No — deferred | → F-VLT-14, §7 |
| OQ-9 | Hit and aiming-error metric | Hit = spot inside the ball's image disc in ≥ 1 camera; error = ball centre to beam line | decisions/ADR-VLT-005-hit-and-aiming-error.md |
| OQ-10 | Scoring and release | By time, gaps are misses, aborted runs fail; release = start of motion after > 100 mm | decisions/ADR-VLT-006-time-based-run-scoring.md |
| OQ-11 | Recovery and re-arming | Safety faults need re-arming, transient ball loss ≤ 1 s does not; kill-switch sense contact; arming epoch | decisions/ADR-VLT-007-recovery-and-rearm-policy.md |
| OQ-12 (deadline part) | Hard deadline or p99? | T1 firm p99 ≤ 30 ms, shutdowns hard | decisions/ADR-VLT-008-deadline-classes.md |
| OQ-14 (degraded part) | 80 % also with two cameras? | Yes, for every camera pair | → NF-VLT-1 |
| OQ-15 | Loop activation | Time-triggered fusion; galvo applies at `t_place_ns` and interpolates | decisions/ADR-VLT-009-time-triggered-loop.md |
| OQ-16 | Galvo hang | On-chip watchdog on the galvo node | decisions/ADR-VLT-010-onchip-watchdog-galvo.md |
| OQ-17 | Prediction model | Constant velocity / acceleration, no pendulum model | decisions/ADR-VLT-011-generic-motion-prediction.md |

### Open questions

- **OQ-1** — Camera model: resolution, frame rate modes, global vs. rolling shutter. Select and measure a mode against the 30 ms budget, including exposure/readout and detection; the earlier ≈ 90 fps figure is an unverified estimate, not a consequence of that deadline alone. — student team — blocks: NF-VLT-18, F-VLT-1, F-VLT-2, the camera node design.
- **OQ-2** — Laser type, colour and power (Class ≤ 2, software-switchable, colour per NF-VLT-17). — student team — blocks: NF-VLT-2, NF-VLT-16, NF-VLT-17.
- **OQ-3** — Cube size (maximum amplitude, starting deflection, clamp envelope). — student team — blocks: F-VLT-9 envelope values, the cube configuration.
- **OQ-4** — Galvo driver input (signal type, voltage range, connector), mirror size, scan angle, step response; can the "Programm Board" be bypassed. — student team, from the delivered board — blocks: F-VLT-15, F-VLT-19, NF-VLT-18 settling budget.
- **OQ-5** — Converter board between galvo node and galvo driver. — student team — blocks: F-VLT-15.
- **OQ-6** — resolved 2026-11-10 → NF-VLT-2.
- **OQ-7** — Background dark or light (with ball and laser colour). Since 2026-11-10 the automatic galvo scan (F-VLT-13) and the arming check (F-VLT-31) need the spot visible on floor and walls, and the frame markers (F-VLT-12) need contrast for the cameras. — student team — blocks: NF-VLT-17, F-VLT-12/13/31.
- **OQ-8** — resolved 2026-11-10: F-VLT-14 deferred (§7).
- **OQ-9** — resolved 2026-11-10 → ADR-VLT-005.
- **OQ-10** — resolved 2026-11-10 → ADR-VLT-006.
- **OQ-11** — resolved 2026-11-10 → ADR-VLT-007.
- **OQ-12** — deadline classes resolved 2026-11-10 (ADR-VLT-008). Still open: maximum observation age, exposure-time skew, prediction horizon, target age, sync-status age, `fusion_period_ms` and the global granularity g (NF-VLT-24); conversion of the camera's exposure timestamp to the shared clock and rolling-shutter timing. — student team, after OQ-1 — blocks: F-VLT-3/4/20/22/23, NF-VLT-24/27.
- **OQ-13** — resolved 2026-11-10: calibration procedure → ADR-VLT-012; cube frame and rest position defined in §2. Marker count and positions and the contents of the setup revision are design and move to the architecture (§11).
- **OQ-15** — resolved 2026-11-10 → ADR-VLT-009.
- **OQ-16** — resolved 2026-11-10 → ADR-VLT-010.
- **OQ-17** — resolved 2026-11-10 → ADR-VLT-011.
- **OQ-14** — degraded-mode part resolved 2026-11-10 (every camera pair must reach 80 %, NF-VLT-1). Still open: the tested operating envelope (ball size, maximum speed and acceleration — the prediction is generic, ADR-VLT-011 — lighting/exposure, expected occlusions, with OQ-3/OQ-7) and one combined error budget for detection, calibration, triangulation, timing/prediction and galvo placement against the ball radius; individually passing tests do not establish a combined bound. — student team + sponsor, before acceptance recording — blocks: F-VLT-1 … F-VLT-5, NF-VLT-1/17/18/21.

## 9. Artifact Interactions & Interferences

Embedded checklist (MANIFEST Phase 3) applied; no other features exist. Rows are the existing components the feature touches.

| Existing component / feature | Interaction (how we use it) | Interference (how we might break it) | Extension needed | Backward-compatible |
| --- | --- | --- | --- | --- |
| Galvo kit driver + "Programm Board" | drives the mirrors from our X/Y signals | the kit's own pattern player could drive the mirrors concurrently or at power-up → uncontrolled beam | disable/bypass the player → **F-VLT-19** (new) | n.a. |
| Kernel PTP / system clock on each node | exposure times and target validity in one clock | startup/ongoing sync loss or clock changes invalidate fusion and timeout assumptions | F-VLT-20/22; OQ-12 defines validity limits and clock handling | n.a. |
| Ethernet switch (shared by PTP, loop messages, monitoring) | carries all traffic | monitoring bursts (images) delay PTP packets and loop messages → precision and deadline degrade | **NF-VLT-20** (new); NF-VLT-6, NF-VLT-8 | n.a. |
| Kill switch / laser supply | hardware supply interruption | software may not observe the switch and may retain the armed state after release | F-VLT-21, F-VLT-30 (sense contact), ADR-VLT-007 | n.a. |
| Camera stack on Pi 3 (CPU, USB-attached Ethernet share the same SoC) | capture at high frame rate, on-node detection | high frame rate capture + detection + network on a Pi 3 may exceed CPU; Ethernet on the Pi 3 shares USB bandwidth | NF-VLT-19 budget; frame mode selection in architecture | n.a. |
| Raspberry Pi OS scheduling | all node processes | non-real-time scheduling → jitter in detection and galvo output | priorities / CPU pinning decided in architecture; measured via NF-VLT-18 | n.a. |
| Monitoring laptop | receives pushed data | none on the loop as long as NF-VLT-6/7/10 hold | — | n.a. |
| Calibration files / installation configuration | loaded by nodes using one coordinate convention | wrong camera assignment/image mode or mismatched setup revisions corrupt fusion and aiming | F-VLT-24 validates known metadata; a moved camera is detected by the continuous pose check (F-VLT-12), a moved galvo by the arming check (F-VLT-31) | n.a. |
| Camera/control/galvo message streams | connect independently developed nodes | delayed, duplicated or pre-restart messages can overwrite fresh state or keep an expired target alive | F-VLT-22/23; shared envelope and source time below | n.a. |
| Reference data set / evaluation | verifies detection, prediction and hit rate | 2D labels do not yet define all metric references; missing fusion output can bias a step-based score | ADR-VLT-005/006 define metric and scoring; repeatable replay per NF-VLT-22 | n.a. |
| Laser spot on the ball (physical hidden channel) | the spot is what we want on the ball | the spot changes the ball's colour/brightness in the image and can shift or break ball detection, which in turn moves the aim | F-VLT-1 acceptance evaluated on frames with the spot on the ball | n.a. |
| Galvo node GPIO / power / boot | switches the laser enable | GPIO pins float or default high during boot and after a crash; a power loss of the Pi with the laser supply on could leave the laser enabled | **NF-VLT-25** (new) | n.a. |
| OS time services (NTP, systemd-timesyncd) | none — must not be used | a second time service steps or slews the clock against PTP → invalid exposure times, extended timeouts | **NF-VLT-24**, **NF-VLT-28** (new) | n.a. |
| Galvo → control feedback (new channel) | actual laser state, galvo restart | without it the control node judges F-VLT-16 and hits by its own command and misses a galvo restart | **F-VLT-25** (new) | n.a. |

### DRS checklist coverage (review 2026-11-10)

| DRS checklist row | Covered by | Still open |
| --- | --- | --- |
| Global time base: π, g > π | NF-VLT-5, NF-VLT-24, F-VLT-18, F-VLT-20 | value of g (OQ-1/OQ-12) |
| Timestamps across nodes: reasonableness, ±2g | NF-VLT-24, F-VLT-3, F-VLT-22 | exposure-timestamp source (OQ-12) |
| Temporal accuracy d_acc, phase sensitivity | F-VLT-4, F-VLT-22, NF-VLT-26 | limits (OQ-12), phase alignment (OQ-15) |
| Permanence / action delay, hidden channels | F-VLT-16 (action delay), F-VLT-22, F-VLT-23, NF-VLT-27, §9 spot row | — |
| End-to-end deadline, per-stage budget | NF-VLT-18, NF-VLT-26, NF-VLT-29 | stage budgets in §11 |
| Fault hypothesis, k, redundancy degree, injection beyond | NF-VLT-23, F-VLT-11, F-VLT-27 | inter-fault time confirmation; hang (OQ-16) |
| Replica determinism / voting | deferred with F-VLT-14 (no replicated controller); inexact 2-of-3 camera fusion via F-VLT-27 | OQ-8 |
| Membership, clique detection, degraded mode | F-VLT-11 (camera states), F-VLT-17, F-VLT-25 (galvo session); clique detection not relevant — star topology, one switch, the control node is the only membership authority | recovery policy (OQ-11) |
| Load hypothesis, freedom from thrashing | NF-VLT-27, NF-VLT-8, NF-VLT-19 | rates (OQ-1/OQ-15) |
| Composability | NF-VLT-6, NF-VLT-7, NF-VLT-9, NF-VLT-28 | — |
| Gateway between clusters | not relevant — one cluster on one switch, the laptop is a sink only | — |
| Safety-relevant actuator: effect monitored | F-VLT-16, F-VLT-25, F-VLT-26, NF-VLT-25 | — |
| Node reintegration: ground state, h-state, reintegration point | F-VLT-17, F-VLT-25, F-VLT-28, F-VLT-23 (session) | reintegration point (OQ-11) |

## 10. Schema Extensions

All distances in mm (cube coordinates), times in ns of the shared PTP clock (`int64`), image positions in px. Transport and encoding are decided in the architecture; the fields below are binding.

**Proposed contract additions from the review** (F-VLT-22 … F-VLT-24; pending PM review)

`Observation` and `Target` both carry:

| Field | Type | Range / meaning |
| --- | --- | --- |
| `schema_version` | `uint16` | supported contract version; incompatible versions rejected |
| `session_id` | `string` | identifies one sender-process incarnation; changes on restart; sequence order is scoped to sender + session |
| `setup_revision` | `string` | identifies the validated installation configuration and calibration set; must match the receiver's expected setup |

Session adoption and counter-wrap comparison are specified once for all receivers before implementation; a changed session is not permission to re-arm (OQ-11). Message validation and bounded-buffer rules are shared by node tests and replay (F-VLT-23, NF-VLT-22).

**`Observation`** (camera node → control node, one per frame)

| Field | Type | Range / default |
| --- | --- | --- |
| `camera_id` | `uint8` | 0, 1, 2 |
| `frame_seq` | `uint32` | monotonic per camera, wraps |
| `t_exposure_ns` | `int64` | mid-exposure time, shared clock |
| `ball` | `{u: float32, v: float32, radius_px: float32}` or `null` | `null` = not seen |
| `spot` | `{u: float32, v: float32}` or `null` | `null` = not seen |
| `clock_offset_ns` | `int64` | last measured offset to the shared clock (F-VLT-18) |
| `synced` | `bool` | false until offset ≤ π/2 = 0.5 ms to the grandmaster (F-VLT-20, NF-VLT-24) |

**`Target`** (control node → galvo node, one per fusion step)

| Field | Type | Range / default |
| --- | --- | --- |
| `seq` | `uint32` | monotonic, wraps |
| `control_id` | `uint8` | identifies the sending control node (F-VLT-14) |
| `t_source_ns` | `int64` | proposed: oldest contributing observation's exposure time; permits a source-age check even when targets keep arriving (F-VLT-22) |
| `t_place_ns` | `int64` | time at which the spot shall be at `position` |
| `t_valid_until_ns` | `int64` | proposed: expiry of this target in the shared clock; must not exceed the configured source-age/prediction limits (OQ-12) |
| `position` | `{x, y, z: float32}` | cube coordinates; galvo node clamps (F-VLT-9) |
| `velocity` | `{vx, vy, vz: float32}` | mm/s at `t_place_ns`, for interpolation (ADR-VLT-009/011) |
| `acceleration` | `{ax, ay, az: float32}` | mm/s², zero for the constant-velocity model |
| `arm_epoch` | `uint32` | incremented at every arming (ADR-VLT-007) |
| `laser_on` | `bool` | false in safe state, not armed or no valid ball state |

**`GalvoStatus`** (galvo node → control node, with every applied target and at least every 50 ms; proposed, F-VLT-25; carries the shared envelope fields above)

| Field | Type | Range / default |
| --- | --- | --- |
| `seq` | `uint32` | monotonic, wraps |
| `applied_target_seq` | `uint32` or `null` | `seq` of the target currently on the output; `null` before the first |
| `t_applied_ns` | `int64` | shared-clock time the output was applied |
| `laser_on` | `bool` | actual state of the enable output |
| `laser_off_reason` | `enum` or `null` | `startup`, `not_armed`, `timeout`, `non_finite`, `clamped_invalid`, `link_error`, `kill_switch`, `safe`; `null` while on |
| `kill_switch_pressed` | `bool` | sense contact (F-VLT-30); wire open reads as pressed |
| `t_laser_change_ns` | `int64` | shared-clock time of the last laser on/off transition (F-VLT-16 action-delay window) |

**`MonitorMessage`** (any node → monitoring laptop, push only, best effort)

| Field | Type | Range / default |
| --- | --- | --- |
| `node` | `string` | `camera0..2`, `control`, `galvo` |
| `t_ns` | `int64` | shared clock |
| `kind` | `enum` | `status`, `image`, `run_result`, `alarm` |
| `payload` | per kind | `status`: mode, aiming error, hit rate, clock offset, CPU, RAM; `image`: JPEG ≤ 320 × 240 with overlay data; `run_result`: start, end, steps, hits, hit rate; `alarm`: text |

**Configuration keys** (one file per installation, read at start)

| Key | Type | Default | Valid range |
| --- | --- | --- | --- |
| `arm_mode` | — | obsolete (ADR-VLT-013: software arming only) | — |
| `arm_button_gpio` | — | obsolete (ADR-VLT-013: no arming button) | — |
| `arm_button_debounce_ms` | — | obsolete (ADR-VLT-013) | — |
| `galvo_scan_max_attempts` | `int` | 2 | 1–5 (F-VLT-13) |
| `safety_fault_latch_count` | `int` | 3 | 2–10 (proposed, F-VLT-21) |
| `safety_fault_latch_window_s` | `float` | 60 | 10–600 (proposed, F-VLT-21) |
| `cube_size_mm` | `{x, y, z}` | open (OQ-3) | > 0 |
| `hit_radius_mm` | — | obsolete (ADR-VLT-005) | — |
| `ball_radius_mm` | `float` | 25 | 10–50 (measured ball) |
| `release_speed_mm_s` | `float` | 100 | 20–500 |
| `fusion_period_ms` | `float` | open (OQ-1/OQ-12) | > 0 |
| `auto_rearm_holdoff_ms` | `int` | 2000 | 500–10000 |
| `kill_switch_gpio` | `int` | open (wiring) | valid BCM pin, galvo node |
| `galvo_watchdog_s` | `float` | 1 | 1–15 (SoC limit) |
| `run_start_amplitude_mm` | `float` | 100 | > `run_end_amplitude_mm` |
| `run_end_amplitude_mm` | `float` | 50 | > 0 |
| `laser_timeout_ms` | `int` | 100 | 20–500 |
| `clock_sync_limit_ms` | `float` | 0.5 (per node, to the grandmaster) | 0.05–0.5 (rev 5: the old range up to 5 ms could relax NF-VLT-5) |
| `monitor_host` | `string` | — (absent = no monitoring) | host:port |
| `monitor_image_rate_hz` | `float` | 5 | 0–5 |
| `monitor_image_size` | `{w, h}` | 320 × 240 | ≤ 320 × 240 |
| `store_images` | `bool` | false | — |

F-VLT-22 requires explicit observation-age, fusion-skew, prediction-horizon, target-age and sync-status-age limits; their values and configuration keys remain open in OQ-12. F-VLT-24 checks these against one another and the configured timeout. Configurability does not relax acceptance: the demo profile must use the measured ball radius, 100/50 mm run thresholds, 100 ms target-loss timeout and ≤ 1 ms clock bound; other values are test profiles, not evidence of NF-VLT-1 compliance.

**Reference data set** (NF-VLT-21) — one folder in the repository

- frames per camera as lossless images, named by `camera_id` and `frame_seq`, with `t_exposure_ns`;
- `annotations` file: per frame `camera_id`, `frame_seq`, `t_exposure_ns`, `ball` `{u, v, radius_px}` or `null`, `spot` `{u, v}` or `null`, `laser_on` `bool`, `case` (`resting`, `swing`, `no_ball`, `laser_off`); per resting position `position_mm` `{x, y, z}` measured by hand; per swing the run boundaries;
- the camera calibration used during recording;
- recording date and setup description (camera model, ball, background, laser, lighting).

Additions from ADR-VLT-005/006: aiming-error and hit references derived with the ADR-VLT-005 geometry, moving-position reference times, explicit release/end markers and the scoring rule for gaps. Replay fault schedules record delivery order/times, restart sessions and clock/sync changes without changing the original annotations (NF-VLT-22).

**Calibration files**

- `marker_map`: marker dictionary, marker size, and per marker ID the cube coordinates of its corners (measured once when the frame is built; ADR-VLT-012).
- `camera_calibration` per camera (written automatically at start): intrinsic matrix (3 × 3), distortion coefficients, rotation (3 × 3) and translation (3) into cube coordinates, image size, number of markers used, date, residual error.
- `galvo_calibration` (written by the scan): parameters of the physical galvo model (galvo origin, mirror spacing, scale and offset per axis), configured galvo limits / angle envelope of the cube (for F-VLT-9), number of scan points, date, residual error.

Proposed shared metadata (F-VLT-24): file schema version, `setup_revision`, coordinate convention and units; camera files additionally bind `camera_id` and calibrated image mode (resolution/crop). Configuration defines the expected metadata; the setup revision changes when calibration or a relevant setup parameter changes. Physical changes are detected by the pose check (F-VLT-12) and the arming check (F-VLT-31), not by the setup revision.

## 11. Architecture & Vertical Slices

open — after PM review

## 12. Architecture Consistency Review

open — after PM review

## Notes (human)

<!-- Off limits for all skills. Copied verbatim on every rewrite. -->

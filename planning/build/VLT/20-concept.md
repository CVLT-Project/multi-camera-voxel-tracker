---
stage: concept
owner: build-concept
status: in_progress
revision: 4
version: 0.1
created: 2026-11-02T16:10
updated: 2026-11-06T15:24
input: VLT/10-intake.md@2, requirements review request (chat, 2026-11-06)
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

## 1. Purpose

A lab demo that shows multi-camera 3D tracking. Three Raspberry Pi cameras stand at right angles around a cube; a ball swings on a string through the cube. The system computes the 3D position of the ball and steers a laser through a galvo mirror pair so that the spot stays on the ball. The cameras also see the spot, so the system measures its own aiming error. Built and operated by a team of 11 students, presented once to other students.

## 2. Ubiquitous Language & Context

Full dictionary in `CONTEXT.md`. Delta introduced by this feature:

| Term | Meaning | Used in code as |
| --- | --- | --- |
| cube | the tracking volume; origin and axes defined by the camera calibration | `Cube`, cube coordinates in mm |
| ball | the tracked object, ≈ 5 cm diameter, on a ≈ 1 m string | `ball` |
| spot | the laser spot as seen by the cameras | `spot` |
| camera node / control node / galvo node | the three node types (ADR-VLT-001) | `camera`, `control`, `galvo` |
| observation | one camera's detection result for one frame: ball and spot image positions plus exposure time | `Observation` |
| ball state | fused 3D ball position (and velocity) at a time | `BallState` |
| target | the cube point the galvo node shall aim at, with its validity time and laser flag | `Target` |
| aiming error | distance between measured spot and measured ball centre | `aiming_error_mm` |
| hit | a fusion step in which the spot is seen and lies within the hit radius (25 mm) of the ball centre | `hit` |
| run | from release (amplitude rises above 10 cm) until the amplitude falls below 5 cm | `Run` |
| hit rate | hits ÷ fusion steps within a run | `hit_rate` |
| amplitude | the ball's maximum horizontal deflection from its rest position over the last swing | `amplitude_mm` |
| armed | the state in which the system may switch the laser on | `armed` |
| safe state | laser off; galvo node ignores targets until re-armed | `SAFE` |
| degraded | tracking with exactly two camera nodes delivering the ball | `DEGRADED` |
| camera calibration / galvo calibration | stored results of the manual calibration procedures | `camera_calibration`, `galvo_calibration` |
| reference data set | recorded, annotated frames of all cameras used by the automated tests (NF-VLT-21) | `reference_data` |
| monitoring laptop | observe-only sink for monitoring data (ADR-VLT-003) | `monitor` |
| kill switch | physical switch cutting the laser supply independent of software | — |

## 3. Functional Requirements

| ID | Requirement | Acceptance (falsifiable) | Origin | Evidence |
| --- | --- | --- | --- | --- |
| F-VLT-1 | Each camera node detects the ball in every captured frame and sends an observation with the ball's image position (or "not seen") and the exposure time in the shared clock to the control node. | On the reference data set (NF-VLT-21): the detected ball position lies within 3 px of the annotation in ≥ 95 % of the frames with an annotated ball; frames without the ball report "not seen". Automated test, runs without hardware; the same test run on a camera node gives identical results. | intake d-1 · team review (reference data set) | [evidenced] |
| F-VLT-2 | Each camera node detects the laser spot in every captured frame and includes its image position (or "not seen") in the same observation. | On the reference data set (NF-VLT-21): the detected spot position lies within 3 px of the annotation in ≥ 95 % of the frames with an annotated spot; frames recorded with the laser off report "not seen" in ≥ 99 %. Automated test, runs without hardware; the same test run on a camera node gives identical results. | intake d-2 · team review (reference data set) | [evidenced] / thresholds [estimated] |
| F-VLT-3 | The control node computes the ball's 3D position in cube coordinates from the observations of at least two camera nodes, using the camera calibration and combining observations by exposure time. | On the reference data set (NF-VLT-21): for the resting positions, the computed 3D position lies within 10 mm of the hand-measured position with 3 cameras and within 15 mm with any 2 cameras. Automated test, runs without hardware. | intake d-3 · team review (reference data set) | [evidenced] / thresholds [estimated] |
| F-VLT-4 | The control node sends the galvo node targets for where the ball will be at the moment the spot is placed (compensating the loop delay), not where it was last measured. | Replay of the recorded swings of the reference data set (NF-VLT-21): the predicted position for the placement time deviates ≤ 10 mm (median) from the recorded position at that time. | intake d-4 | [estimated] |
| F-VLT-5 | The galvo node converts each target into mirror angles using the galvo calibration and drives the galvo accordingly. | Laser aimed at 9 known cube points (grid): spot lands within 5 mm of each point. | intake d-5 | [evidenced] / threshold [estimated] |
| F-VLT-6 | The control node computes the aiming error for every fusion step in which the spot is seen by at least one camera. The metric, required geometry and behaviour when the error cannot be measured are still open (OQ-9). | On the reference data set (NF-VLT-21): the computed aiming error lies within 5 mm of the aiming error derived from the annotations (spot and ball positions). OQ-9 must first define how those annotations yield a reference error in mm, including single-camera spot visibility. | intake d-6 · team review (reference data set) · requirements review 2026-11-06 | [evidenced] / threshold [estimated] / metric [unknown] |
| F-VLT-7 | The control node detects a run — start when the amplitude first rises above 100 mm, end when it falls below 50 mm — counts hits (spot seen and within 25 mm of the ball centre) and fusion steps, and reports the hit rate at the end of the run. A step in which no camera sees the spot counts as a miss. Release detection, the scoring time base and treatment of tracking gaps are still open (OQ-10). | Replay of a recorded run of the reference data set (NF-VLT-21) with annotated spot and ball positions: start and end detected within one swing period of the true moment; reported hit rate equals the hand count ± 1 %. The replay must include holding the ball before release and gaps without valid fusion output; the reference count follows the rule agreed in OQ-10. | intake d-7 · requirements review 2026-11-06 | [evidenced] / gap and release rules [unknown] |
| F-VLT-8 | The laser is off at start-up, during the restart of any node, whenever the system is not armed and whenever no valid ball state is available. | Power-up, node restarts and covering the ball: a photodiode (or camera) at the galvo output shows the laser off within 100 ms in every case. | intake d-10 | [evidenced] |
| F-VLT-9 | The galvo node clamps every aim to the cube volume, regardless of the target it receives. | Targets outside the cube (incl. NaN, ±∞, far out of range) sent to the galvo node: the commanded mirror angles never leave the cube's angle envelope; NaN/∞ targets switch the laser off. | intake d-11 | [evidenced] |
| F-VLT-10 | The galvo node switches the laser off when it has not received a fresh target for 100 ms. | Stop the control node or unplug its cable while tracking: laser off ≤ 100 ms + 10 ms after the last target. | intake d-12 | [evidenced] / value [estimated] |
| F-VLT-11 | With exactly two camera nodes delivering the ball, tracking continues in degraded mode; with fewer than two, the laser is off until at least two deliver again. | Cover or stop one camera: tracking continues, mode = degraded naming that camera; cover two: laser off ≤ 100 ms; uncover: tracking resumes without restart. | intake d-15 | [evidenced] |
| F-VLT-12 | A manual calibration procedure determines each camera's intrinsic and extrinsic parameters in cube coordinates; the result is stored and loaded at start until recalibrated. | After calibration, F-VLT-3 acceptance passes; after a node restart the same calibration is loaded (file checksum logged). | intake d-25, ADR-VLT-004 | [evidenced] |
| F-VLT-13 | A manual calibration procedure determines the mapping from cube coordinates to mirror angles; the result is stored and loaded at start until recalibrated. | After calibration, F-VLT-5 acceptance passes; after restart the same calibration is loaded. | intake d-26, ADR-VLT-004 | [evidenced] |
| F-VLT-14 | Optional — nice to have (sponsor, PM review); built only if OQ-8 confirms enough Pis: a second control node takes over when the active one fails; the galvo node follows exactly one control node at a time; both use the same calibration. | Kill the active control node during tracking: the standby takes over and tracking resumes ≤ 1 s; at no time does the galvo node accept targets from two control nodes. | intake d-29 | [evidenced] / value [estimated] |
| F-VLT-15 | The galvo node outputs X/Y signals matching the galvo driver's input specification through a converter board, with a defined reaction to errors on the link to that board (laser off). | Full-range X/Y sweep measured at the driver input with a multimeter/scope within the driver's specified range; disconnecting the converter board turns the laser off. (open: OQ-4, OQ-5) | intake d-36 | [evidenced] |
| F-VLT-16 | If a camera sees the spot while the laser should be off, the system raises an alarm on the display and enters the safe state. | Inject a spot-like light (second pointer) while the system is disarmed: alarm shown, system stays/enters safe state. | intake d-38 | [estimated] |
| F-VLT-17 | A restarted camera node rejoins the running system without restarting other nodes. | Restart one camera node during tracking: it delivers observations again after its clock is synchronized, mode returns from degraded to normal. | intake d-39 | [estimated] |
| F-VLT-18 | Every node measures its clock offset to the shared clock and reports it. | Values appear on the display for all 5 nodes, updated at least once per second. | intake d-17 | [evidenced] |
| F-VLT-19 | The galvo kit's own pattern player ("Programm Board") is disabled or bypassed so that only the galvo node drives the mirrors. | With the galvo node stopped, the mirrors do not move and no pattern is projected. (open: OQ-4) | concept §9 (galvo kit) | [estimated] |
| F-VLT-20 | A node's observations or targets are used only after its clock is synchronized within 1 ms; until then the laser stays off. | Start the system with PTP disabled on one camera: its observations are ignored; with PTP disabled on all cameras or on the galvo node, the laser stays off. | concept §9 (PTP start-up) | [estimated] |
| F-VLT-21 | After the safe state was entered (kill switch, timeout, fewer than two cameras for > 1 s, alarm), the laser stays off until the system is armed again per U-VLT-2. | Release the kill switch after pressing it: the laser stays off until the button is pressed (mode `button`) or the arming condition is met (mode `auto`). | concept §9 (kill switch / re-arm) | [estimated] |
| F-VLT-22 | Data used for fusion and actuation must meet explicit limits for observation age, inter-camera exposure-time difference, prediction horizon and target validity. A newly received target based on expired observations is not fresh. Clock synchronization is checked throughout operation, including the age of the sync status; invalid data is excluded and the existing laser-off rules apply when no valid input remains. A shared-clock correction must not extend the local target-loss timeout. Limits and recovery are open in OQ-11/OQ-12. | Replay delayed observations, a stream of targets based on old frames, expired targets, lost sync and a clock step: invalid inputs never drive the laser, a healthy pair of cameras can still track, and the local target-loss timeout is not extended by a clock change. Boundary tests use the limits agreed in OQ-12. | requirements review 2026-11-06 · F-VLT-3/4/10/20 | [estimated] / limits [unknown] |
| F-VLT-23 | Camera → control and control → galvo messages have one shared, versioned contract. Receivers validate structure, sender identity, finite numeric values, restart session and sequence order, including counter wrap. Duplicate, obsolete-session, incompatible and malformed messages cannot update the accepted state or refresh its timeout. Buffers have finite limits and an explicit overflow policy that prevents processing an ever-growing backlog. | Contract tests inject wrong versions/IDs, truncated messages, NaN/∞, duplicates, reordering, counter wrap and a restart with sequence reset; only current valid inputs update the state. A burst beyond buffer capacity has bounded memory use and expired messages are discarded per F-VLT-22. | requirements review 2026-11-06 · §10 messages, F-VLT-17 | [estimated] |
| F-VLT-24 | Before arming, required configuration and calibration files are validated together: units and coordinate convention, camera IDs and image modes, setup revision, finite parameters and cross-field limits must agree. Missing, corrupt or incompatible required files keep the laser off and produce a specific local diagnostic, also available to monitoring when connected. Peers must not combine data or targets from different setup revisions. | Remove/corrupt a file, swap camera calibrations, change image mode or setup revision on one node, and set invalid timing/geometry limits: arming is refused for an invalid local setup; incompatible peer data is rejected. A matching validated setup passes F-VLT-3/5 after restart. Coordinate and calibration-procedure details remain OQ-13. | requirements review 2026-11-06 · F-VLT-12/13, §10 configuration | [estimated] |

## 4. User Interaction Requirements

| ID | Requirement | Acceptance | Origin | Evidence |
| --- | --- | --- | --- | --- |
| U-VLT-1 | The monitoring laptop shows live: mode (safe / armed / tracking / degraded + missing camera), current aiming error, hit rate of the current and last run, camera status per node, clock offset per node, and the camera images with the detected ball and spot marked. | During a run every listed value is visible and updates at least once per second; images at ≥ 1 per second per camera. | intake d-18 | [evidenced] |
| U-VLT-2 | The arming method is set in the configuration: `button` — the operator arms with a physical button on the control node (GPIO pin and debounce time configurable) — or `auto` — the system arms as soon as at least two cameras see the ball (for a control node without a button). No other control path exists. F-VLT-8 … F-VLT-10, F-VLT-21, NF-VLT-3 apply unchanged in both modes. | In `button` mode the laser never switches on without a button press after start or safe state; in `auto` mode it switches on only when ≥ 2 cameras see the ball; no network command arms the system. | intake d-24 | [evidenced] |
| U-VLT-3 | dropped by the sponsor at the PM review (2026-11-02) — was: "recalibration recommended" hint on a systematic aiming error. | — | intake d-27 | — |

## 5. Non-Functional Requirements

| ID | Requirement | Acceptance / measure | Origin | Evidence |
| --- | --- | --- | --- | --- |
| NF-VLT-1 | Acceptance of the demo: in a run (F-VLT-7) from release until the amplitude is below 50 mm, the hit rate is at least 80 %. | System-reported hit rate ≥ 80 % in 3 of 3 consecutive runs. | intake d-8 | [evidenced] |
| NF-VLT-2 | Laser safety (IEC 60825-1): the laser is visible and at most Class 2 (≤ 1 mW). | Laser label / datasheet shows Class 1, 1M, 2 or lower; recorded in the setup documentation. (open: OQ-2, OQ-6) | intake d-9 | [evidenced] |
| NF-VLT-3 | A physical kill switch cuts the laser supply independent of all software. | Kill switch pressed during tracking: laser off immediately, with all nodes still running. | intake d-13 | [evidenced] |
| NF-VLT-4 | dropped by the sponsor at the PM review (2026-11-02) — was: hardware watchdog switching the laser off when the galvo node software stops. Residual risk: see §7. | — | intake d-14 | — |
| NF-VLT-5 | All nodes share one clock synchronized over Ethernet (software PTP, ADR-VLT-002) with an offset ≤ 1 ms between any two nodes; every observation carries its exposure time in that clock. | Offsets reported per F-VLT-18 stay ≤ 1 ms during a 10-min run; cross-check: one LED flash seen by all cameras yields exposure times within 1 ms + one frame period. | intake d-16 | [evidenced] |
| NF-VLT-6 | Sending monitoring data never blocks the tracking loop; under back-pressure monitoring data is dropped, not queued. | Monitoring server paused (SIGSTOP) during a run: loop timing (NF-VLT-18) unchanged, node memory does not grow. | intake d-19 | [evidenced] |
| NF-VLT-7 | Tracking and safety behave identically with and without the monitoring laptop connected. | NF-VLT-1 and F-VLT-8 … F-VLT-11 pass with the laptop absent. | intake d-20 | [evidenced] |
| NF-VLT-8 | Monitoring traffic of all nodes together stays ≤ 20 Mbit/s; camera images are sent at ≤ 5 per second, ≤ 320 × 240 px. | Switch/port counters or capture over a 10-min run: total monitoring traffic ≤ 20 Mbit/s. | intake d-21 | [estimated], confirmed by sponsor |
| NF-VLT-9 | Loop timing (NF-VLT-18) and the demo acceptance (NF-VLT-1) are verified both with monitoring on (at its maximum rate) and off. | Both measurements recorded in the test report. | intake d-22 | [evidenced] |
| NF-VLT-10 | The monitoring laptop has observe-only access: no node accepts commands over the network. | Port scan of every node: no listening port accepts commands; only outgoing monitoring connections and the loop's own messages. | intake d-23, ADR-VLT-003 | [evidenced] |
| NF-VLT-11 | Camera images are shown live only and are not stored by default (GDPR). | After a run, no image files on any node or on the laptop unless storage was explicitly enabled in the configuration. Exception: the reference data set (NF-VLT-21). | intake d-28 | [evidenced] |
| NF-VLT-12 | The system runs continuously for 10 minutes (several runs) without a restart. | 10-min soak: no node restart, no memory growth > 10 %, NF-VLT-1 still met in the last run. | intake d-30, sponsor | [evidenced] |
| NF-VLT-13 | Every node can be set up reproducibly from the repository by a script; code is version-controlled, reviewed before merge, and every node's code has automated tests. | A fresh SD card set up only with the documented script runs the node; the test suite runs with one command. | intake d-31 | [evidenced] |
| NF-VLT-14 | Product code lives under `src/` with one subfolder per node type (`src/camera/`, `src/control/`, `src/galvo/`); the monitoring server has its own subfolder. | Repository layout inspection. | intake d-32, ADR-VLT-001 | [evidenced] |
| NF-VLT-15 | All nodes are Raspberry Pi 3 on one wired Ethernet switch. | Setup documentation lists the hardware; all tests run on it. | intake d-33, ADR-VLT-001 | [evidenced] |
| NF-VLT-16 | The laser can be switched on and off by the galvo node in software (e.g. TTL input or switched supply). | Galvo node toggles the laser 10 × per second for 10 s; photodiode confirms every transition. (open: OQ-2) | intake d-34 | [evidenced] |
| NF-VLT-17 | Laser colour, ball colour and background are chosen so that the spot is distinguishable on the ball and the ball against the background for every camera. | Proven by F-VLT-1 and F-VLT-2 passing on the reference data set (NF-VLT-21), evaluated separately for each camera. (open: OQ-2, OQ-7) | intake d-35 · team review (reference data set) | [evidenced] / threshold [estimated] |
| NF-VLT-18 | End-to-end deadline: from the exposure of a frame to the spot being placed at the corresponding target ≤ 30 ms, with a budget per stage (capture/readout, detection, transmission, fusion and prediction, transmission, galvo output, mirror settling) defined in the architecture. | Per-stage timestamps logged over a 10-min run: 99th percentile of the end-to-end time ≤ 30 ms; each stage within its budget. | intake d-37, sponsor | [evidenced] |
| NF-VLT-19 | Each node stays within ≤ 75 % average CPU and ≤ 50 % RAM on the Pi 3 during a run. | Resource log during a 10-min run. | intake d-40 | [estimated], confirmed by sponsor |
| NF-VLT-20 | Clock precision (NF-VLT-5) holds with monitoring traffic at its maximum (NF-VLT-8). | Clock offsets ≤ 1 ms during a run with monitoring at maximum rate. | concept §9 (PTP vs. monitoring on one switch) | [estimated] |
| NF-VLT-21 | A reference data set is recorded once with the final setup: time-synchronized frames of all three cameras covering a resting ball at ≥ 10 positions spread over the cube, swinging runs (release until amplitude < 50 mm), the spot on and off the ball, laser off, and frames without the ball. Every frame is annotated with the image positions of ball and spot; for the resting positions the 3D ball position is measured by hand. The set and its annotations are stored in the repository and are the input of the automated detection, triangulation, aiming-error, prediction and run tests. It is an explicit exception to NF-VLT-11 on the condition that no people appear in the frames. After a significant setup change (camera, background, ball, laser or lighting) the set is recorded again. | The data set exists in the repository with an annotation file that passes a schema check, covers every listed case for all three cameras, and contains no people (reviewed). | team review (feedback on F-VLT-1 … F-VLT-3) | [evidenced] |
| NF-VLT-22 | The shared processing and decision logic can be tested without cameras, Pis or galvo hardware by replaying the reference data set and synthetic message/time events through the same logic used on the nodes, with a simulated clock and captured actuator output. Replay includes two-camera combinations, loss/delay/reordering, node restart and sync loss. It adds no live command path to the monitoring laptop. | One documented command runs the replay suite without hardware. Repeating the same input/event schedule gives the same validity decisions, state transitions and run result; numeric outputs satisfy the existing tolerances. Fault cases check F-VLT-22 … F-VLT-24. Physical timing and aiming acceptance still require the actual setup. | requirements review 2026-11-06 · NF-VLT-13/21 | [estimated] |

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
| Kill switch | out (hardware) | interrupts the laser supply, no software interface | student team |
| Arming button | in | GPIO input on the control node, pin and debounce configurable (U-VLT-2) | student team |
| Monitoring laptop | out (from nodes) | push-only monitoring messages (§10), observe-only (ADR-VLT-003) | student team |

## 7. Out of Scope

- Automatic galvo calibration via the spot — later version, only if spot visibility allows (ADR-VLT-004).
- Storing camera images by default — GDPR, not needed for the demo (NF-VLT-11).
- Long-term operation, OTA updates, flash-wear management — the project ends after one presentation.
- Certification (CE, EMC, electrical safety, functional safety / SIL) — one-off lab demo, not placed on the market; off-the-shelf boards and supplied power supplies used as delivered.
- Any control path from the monitoring laptop, SSH control of the loop — ADR-VLT-003, U-VLT-2.
- Redundancy of the galvo node and of camera nodes beyond "two of three" — failures lead to the safe state.
- Hardware watchdog for the laser (NF-VLT-4 dropped at the PM review) — residual risk accepted by the sponsor: if the galvo node software hangs with the laser on, the beam stays frozen at its last aim inside the cube (clamped, Class ≤ 2) until the kill switch (NF-VLT-3) is used.
- Recalibration hint (U-VLT-3 dropped at the PM review) — the aiming error on the display (U-VLT-1) is the operator's cue to recalibrate.
- Hardware camera trigger — clock-based fusion instead (ADR-VLT-002).
- Tracking more than one ball, or objects other than a ball on a string.

## 8. Resolved Questions & ADRs

| OQ | Question | Decision | ADR |
| --- | --- | --- | --- |
| — | Node topology and network | Five Pi 3 nodes (3 camera, control, galvo) on wired Ethernet | decisions/ADR-VLT-001-five-node-topology.md |
| — | Time base across nodes | Software PTP (kernel), ≤ 1 ms | decisions/ADR-VLT-002-software-ptp-clock.md |
| — | Where the display runs, laptop authority | Separate laptop, nodes push, observe only | decisions/ADR-VLT-003-observe-only-monitoring-laptop.md |
| — | Calibration method | Manual in v1, automatic galvo calibration later | decisions/ADR-VLT-004-manual-calibration-v1.md |
| — | Success criterion and test window | 80 % hit rate from release to amplitude < 50 mm | → NF-VLT-1, F-VLT-7 |
| — | Laser class | ≤ Class 2 | → NF-VLT-2 |
| — | Camera failure behaviour | Degraded mode with two cameras | → F-VLT-11 |
| — | End-to-end deadline | 30 ms (sponsor) | → NF-VLT-18 |
| — | Continuous operation | 10 min (sponsor) | → NF-VLT-12 |
| — | Numeric defaults (laser timeout 100 ms, monitoring ≤ 20 Mbit/s, CPU ≤ 75 % / RAM ≤ 50 %, run start > 100 mm) | Accepted by the sponsor | → F-VLT-7, F-VLT-10, NF-VLT-8, NF-VLT-19 |
| — | How to verify detection and triangulation without hand-placed checks every time | Recorded, annotated reference data set; automated tests against it (team review) | → NF-VLT-21, F-VLT-1 … F-VLT-4, F-VLT-6, F-VLT-7, NF-VLT-17 |
| — | PM review: hardware watchdog, recalibration hint, redundant control node | NF-VLT-4 and U-VLT-3 dropped; F-VLT-14 optional (nice to have) | → §7, F-VLT-14 |

### Open questions

- **OQ-1** — Camera model: resolution, frame rate modes, global vs. rolling shutter. Select and measure a mode against the 30 ms budget, including exposure/readout and detection; the earlier ≈ 90 fps figure is an unverified estimate, not a consequence of that deadline alone. — student team — blocks: NF-VLT-18, F-VLT-1, F-VLT-2, the camera node design.
- **OQ-2** — Laser type, colour and power (Class ≤ 2, software-switchable, colour per NF-VLT-17). — student team — blocks: NF-VLT-2, NF-VLT-16, NF-VLT-17.
- **OQ-3** — Cube size (maximum amplitude, starting deflection, clamp envelope). — student team — blocks: F-VLT-9 envelope values, the cube configuration.
- **OQ-4** — Galvo driver input (signal type, voltage range, connector), mirror size, scan angle, step response; can the "Programm Board" be bypassed. — student team, from the delivered board — blocks: F-VLT-15, F-VLT-19, NF-VLT-18 settling budget.
- **OQ-5** — Converter board between galvo node and galvo driver. — student team — blocks: F-VLT-15.
- **OQ-6** — Lab laser-safety rules and responsible person. — student team, ask the lab supervisor before the first demo with the laser on — blocks: first laser-on test.
- **OQ-7** — Background dark or light (with ball and laser colour). — student team — blocks: NF-VLT-17.
- **OQ-8** — Enough Raspberry Pis for a redundant control node? — student team — blocks: whether optional F-VLT-14 is built.
- **OQ-9** — What exactly is the aiming error in mm: distance to the ball centre, distance to its surface, or a projected image-plane error? Define when it is measurable if only one camera sees the spot, how a spot on the background is distinguished from one on the ball, and how unmeasurable error is reported. Specify independent reference values for this metric and moving-ball prediction: the current 2D annotations and resting 3D points do not yet define those references. — student team, confirm acceptance meaning with sponsor before implementing scoring — blocks: F-VLT-4/6/7, NF-VLT-1/21/22.
- **OQ-10** — How is actual release distinguished from holding/pulling the ball beyond 100 mm? Define the amplitude window and end rule, the scoring cadence or elapsed-time weighting (the purpose says "80 % of the time", while F-VLT-7 counts fusion steps), and treatment of missing ball states, rejected frames, long gaps and aborted runs. Gaps must not silently disappear from the reported evaluation. — student team + sponsor, before implementing run evaluation — blocks: F-VLT-7, NF-VLT-1/22.
- **OQ-11** — Agree one recovery policy for startup, temporary ball loss, camera restart, target timeout, sync loss, alarm and kill switch, in both arming modes. F-VLT-8 currently says any node restart turns the laser off, while F-VLT-11/17 allow operation with two cameras; F-VLT-11 resumes on visibility while F-VLT-21 requires re-arming after some faults. How is kill-switch activation made known to software, given that §6 currently specifies supply interruption only? In `auto` mode, is a continuously true visibility condition sufficient to re-arm after a fault? — student team + sponsor, before implementing arming/recovery — blocks: F-VLT-8/10/11/17/20/21/22, U-VLT-2, NF-VLT-3.
- **OQ-12** — Agree maximum observation age, exposure-time skew, prediction horizon, target age and sync-status age, plus bounded queue/overflow rules. Define the conversion of the camera's exposure timestamp to the shared clock and handling of rolling-shutter timing and clock changes. Clarify whether 30 ms is a hard deadline or a p99 objective (NF-VLT-18 currently uses both), what happens on a miss, and how physical spot placement/settling is measured separately from issuing a command. Specify a check of the pairwise ≤ 1 ms clock bound; per-node offsets to a master alone need an explicit pairwise check. — student team, deadline interpretation with sponsor, before freezing timing contracts — blocks: F-VLT-3/4/10/20/22/23, NF-VLT-5/18/20.
- **OQ-13** — Fix cube origin, axis directions/handedness, image-coordinate convention and transform direction; agree how a setup revision binds camera IDs, resolution/crop, camera and galvo calibration. Describe the manual calibration steps, physical reference points and how calibration is operated under the observe-only laptop and arming rules; F-VLT-5 also needs a way to measure its test points. A setup revision detects known changes, not a physically moved camera by itself. — student team, before calibration/interface implementation — blocks: F-VLT-3/5/12/13/24, NF-VLT-21.
- **OQ-14** — Define the demo's tested operating envelope: actual ball size, swing amplitude/speed, lighting/exposure and expected occlusions, together with OQ-3/OQ-7. Check one combined error budget for detection, calibration, triangulation, timing/prediction and galvo placement against the 25 mm hit radius; individually passing the existing tests does not establish a combined bound. Decide whether the 80 % acceptance is required in degraded mode for every camera pair as well as with all three cameras. — student team + sponsor, before acceptance recording — blocks: F-VLT-1 … F-VLT-5/11, NF-VLT-1/17/18/21.

## 9. Artifact Interactions & Interferences

Embedded checklist (MANIFEST Phase 3) applied; no other features exist. Rows are the existing components the feature touches.

| Existing component / feature | Interaction (how we use it) | Interference (how we might break it) | Extension needed | Backward-compatible |
| --- | --- | --- | --- | --- |
| Galvo kit driver + "Programm Board" | drives the mirrors from our X/Y signals | the kit's own pattern player could drive the mirrors concurrently or at power-up → uncontrolled beam | disable/bypass the player → **F-VLT-19** (new) | n.a. |
| Kernel PTP / system clock on each node | exposure times and target validity in one clock | startup/ongoing sync loss or clock changes invalidate fusion and timeout assumptions | F-VLT-20/22; OQ-12 defines validity limits and clock handling | n.a. |
| Ethernet switch (shared by PTP, loop messages, monitoring) | carries all traffic | monitoring bursts (images) delay PTP packets and loop messages → precision and deadline degrade | **NF-VLT-20** (new); NF-VLT-6, NF-VLT-8 | n.a. |
| Kill switch / laser supply | hardware supply interruption | software may not observe the switch and may retain the armed state after release | F-VLT-21; switch feedback and recovery policy remain OQ-11 (watchdog stays out of scope) | n.a. |
| Camera stack on Pi 3 (CPU, USB-attached Ethernet share the same SoC) | capture at high frame rate, on-node detection | high frame rate capture + detection + network on a Pi 3 may exceed CPU; Ethernet on the Pi 3 shares USB bandwidth | NF-VLT-19 budget; frame mode selection in architecture | n.a. |
| Raspberry Pi OS scheduling | all node processes | non-real-time scheduling → jitter in detection and galvo output | priorities / CPU pinning decided in architecture; measured via NF-VLT-18 | n.a. |
| Monitoring laptop | receives pushed data | none on the loop as long as NF-VLT-6/7/10 hold | — | n.a. |
| Calibration files / installation configuration | loaded by nodes using one coordinate convention | wrong camera assignment/image mode or mismatched setup revisions corrupt fusion and aiming | F-VLT-24 validates known metadata; physical movement still requires manual recalibration (OQ-13) | n.a. |
| Camera/control/galvo message streams | connect independently developed nodes | delayed, duplicated or pre-restart messages can overwrite fresh state or keep an expired target alive | F-VLT-22/23; shared envelope and source time below | n.a. |
| Reference data set / evaluation | verifies detection, prediction and hit rate | 2D labels do not yet define all metric references; missing fusion output can bias a step-based score | OQ-9/10; repeatable replay per NF-VLT-22 | n.a. |

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
| `synced` | `bool` | false until offset ≤ 1 ms (F-VLT-20) |

**`Target`** (control node → galvo node, one per fusion step)

| Field | Type | Range / default |
| --- | --- | --- |
| `seq` | `uint32` | monotonic, wraps |
| `control_id` | `uint8` | identifies the sending control node (F-VLT-14) |
| `t_source_ns` | `int64` | proposed: oldest contributing observation's exposure time; permits a source-age check even when targets keep arriving (F-VLT-22) |
| `t_place_ns` | `int64` | time at which the spot shall be at `position` |
| `t_valid_until_ns` | `int64` | proposed: expiry of this target in the shared clock; must not exceed the configured source-age/prediction limits (OQ-12) |
| `position` | `{x, y, z: float32}` | cube coordinates; galvo node clamps (F-VLT-9) |
| `laser_on` | `bool` | false in safe state, not armed or no valid ball state |

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
| `arm_mode` | `enum` | `button` | `button`, `auto` |
| `arm_button_gpio` | `int` | open (wiring) | valid BCM pin |
| `arm_button_debounce_ms` | `int` | 50 | 5–500 |
| `cube_size_mm` | `{x, y, z}` | open (OQ-3) | > 0 |
| `hit_radius_mm` | `float` | 25 | 5–100 |
| `run_start_amplitude_mm` | `float` | 100 | > `run_end_amplitude_mm` |
| `run_end_amplitude_mm` | `float` | 50 | > 0 |
| `laser_timeout_ms` | `int` | 100 | 20–500 |
| `clock_sync_limit_ms` | `float` | 1.0 | 0.1–5 |
| `monitor_host` | `string` | — (absent = no monitoring) | host:port |
| `monitor_image_rate_hz` | `float` | 5 | 0–5 |
| `monitor_image_size` | `{w, h}` | 320 × 240 | ≤ 320 × 240 |
| `store_images` | `bool` | false | — |

F-VLT-22 requires explicit observation-age, fusion-skew, prediction-horizon, target-age and sync-status-age limits; their values and configuration keys remain open in OQ-12. F-VLT-24 checks these against one another and the configured timeout. Configurability does not relax acceptance: the demo profile must use the agreed 25 mm hit radius, 100/50 mm run thresholds, 100 ms target-loss timeout and ≤ 1 ms clock bound; other values are test profiles, not evidence of NF-VLT-1 compliance.

**Reference data set** (NF-VLT-21) — one folder in the repository

- frames per camera as lossless images, named by `camera_id` and `frame_seq`, with `t_exposure_ns`;
- `annotations` file: per frame `camera_id`, `frame_seq`, `t_exposure_ns`, `ball` `{u, v, radius_px}` or `null`, `spot` `{u, v}` or `null`, `laser_on` `bool`, `case` (`resting`, `swing`, `no_ball`, `laser_off`); per resting position `position_mm` `{x, y, z}` measured by hand; per swing the run boundaries;
- the camera calibration used during recording;
- recording date and setup description (camera model, ball, background, laser, lighting).

Review additions pending OQ-9/OQ-10: metric reference values and their derivation, moving-position reference times, explicit release/end markers and the scoring rule for gaps. Replay fault schedules record delivery order/times, restart sessions and clock/sync changes without changing the original annotations (NF-VLT-22).

**Calibration files**

- `camera_calibration` per camera: intrinsic matrix (3 × 3), distortion coefficients, rotation (3 × 3) and translation (3) into cube coordinates, image size, date, residual error.
- `galvo_calibration`: mapping cube point → (angle X, angle Y), form set in architecture; angle envelope of the cube (for F-VLT-9); date, residual error.

Proposed shared metadata (F-VLT-24): file schema version, `setup_revision`, coordinate convention and units; camera files additionally bind `camera_id` and calibrated image mode (resolution/crop). Configuration defines the expected metadata; the setup revision changes when calibration or a relevant setup parameter changes. Physical changes not reflected in the files still require the manual procedure (OQ-13).

## 11. Architecture & Vertical Slices

open — after PM review

## 12. Architecture Consistency Review

open — after PM review

## Notes (human)

<!-- Off limits for all skills. Copied verbatim on every rewrite. -->

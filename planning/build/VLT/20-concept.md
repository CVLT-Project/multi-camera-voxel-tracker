---
stage: concept
owner: build-concept
status: in_progress
revision: 2
version: 0.1
created: 2026-11-02T16:10
updated: 2026-11-02T16:16
input: VLT/10-intake.md@2
feature: VLT
---

# VLT Concept — Consolidated Requirements

_Sections 0–12 of the MANIFEST document structure. Together with `30-synthesis.md` (Sections 13–16) this is the source of truth for the feature's code: a fresh agent, given only these files and `CONTEXT.md`, must be able to regenerate the implementation. IDs carry the feature code (`F-VLT-1`) and never change after `done`; reruns append, never renumber._

## 0. Synthesis Context

- **Development path:** A — frontloaded (cold start from a problem statement).
- **Synthesis dependencies:** none.
- **Synthesis scope:** the complete software of all node types (camera, control, galvo), the calibration procedures, the node setup scripts and the monitoring server on the laptop. Hardware (converter board, kill switch, watchdog circuit, laser) is specified by its interface only.
- **Field of application:** distributed real-time system (+ embedded, hardware) — checklists: Cross-cutting, DRS, Embedded, Hardware, By Technology, General Robustness (Software).

### Register trace

not relevant — no register

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
| monitoring laptop | observe-only sink for monitoring data (ADR-VLT-003) | `monitor` |
| kill switch | physical switch cutting the laser supply independent of software | — |

## 3. Functional Requirements

| ID | Requirement | Acceptance (falsifiable) | Origin | Evidence |
| --- | --- | --- | --- | --- |
| F-VLT-1 | Each camera node detects the ball in every captured frame and sends an observation with the ball's image position (or "not seen") and the exposure time in the shared clock to the control node. | With the ball placed at 10 known positions in the cube, every camera that has the ball in view reports it within 3 px of the manually marked image position in ≥ 95 % of frames; frames without the ball report "not seen". | intake d-1 | [evidenced] |
| F-VLT-2 | Each camera node detects the laser spot in every captured frame and includes its image position (or "not seen") in the same observation. | With the laser aimed at the resting ball, every camera that has the spot in view reports it within 3 px of the manually marked position in ≥ 95 % of frames; with the laser off it reports "not seen" in ≥ 99 % of frames. | intake d-2 | [evidenced] / thresholds [estimated] |
| F-VLT-3 | The control node computes the ball's 3D position in cube coordinates from the observations of at least two camera nodes, using the camera calibration and combining observations by exposure time. | Ball at 10 positions measured by hand: computed position within 10 mm of the measured position with 3 cameras and within 15 mm with any 2 cameras. | intake d-3 | [evidenced] / thresholds [estimated] |
| F-VLT-4 | The control node sends the galvo node targets for where the ball will be at the moment the spot is placed (compensating the loop delay), not where it was last measured. | Replay of a recorded swing: the predicted position for the placement time deviates ≤ 10 mm (median) from the recorded position at that time. | intake d-4 | [estimated] |
| F-VLT-5 | The galvo node converts each target into mirror angles using the galvo calibration and drives the galvo accordingly. | Laser aimed at 9 known cube points (grid): spot lands within 5 mm of each point. | intake d-5 | [evidenced] / threshold [estimated] |
| F-VLT-6 | The control node computes the aiming error for every fusion step in which the spot is seen by at least one camera. | With the spot placed at a known offset (0, 20, 40 mm) from the resting ball, the computed aiming error is within 5 mm of the offset. | intake d-6 | [evidenced] / threshold [estimated] |
| F-VLT-7 | The control node detects a run — start when the amplitude first rises above 100 mm, end when it falls below 50 mm — counts hits (spot seen and within 25 mm of the ball centre) and fusion steps, and reports the hit rate at the end of the run. A step in which no camera sees the spot counts as a miss. | Replay of a recorded run with known spot/ball positions: start and end detected within one swing period of the true moment; reported hit rate equals the hand count ± 1 %. | intake d-7 | [evidenced] |
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
| NF-VLT-11 | Camera images are shown live only and are not stored by default (GDPR). | After a run, no image files on any node or on the laptop unless storage was explicitly enabled in the configuration. | intake d-28 | [evidenced] |
| NF-VLT-12 | The system runs continuously for 10 minutes (several runs) without a restart. | 10-min soak: no node restart, no memory growth > 10 %, NF-VLT-1 still met in the last run. | intake d-30, sponsor | [evidenced] |
| NF-VLT-13 | Every node can be set up reproducibly from the repository by a script; code is version-controlled, reviewed before merge, and every node's code has automated tests. | A fresh SD card set up only with the documented script runs the node; the test suite runs with one command. | intake d-31 | [evidenced] |
| NF-VLT-14 | Product code lives under `src/` with one subfolder per node type (`src/camera/`, `src/control/`, `src/galvo/`); the monitoring server has its own subfolder. | Repository layout inspection. | intake d-32, ADR-VLT-001 | [evidenced] |
| NF-VLT-15 | All nodes are Raspberry Pi 3 on one wired Ethernet switch. | Setup documentation lists the hardware; all tests run on it. | intake d-33, ADR-VLT-001 | [evidenced] |
| NF-VLT-16 | The laser can be switched on and off by the galvo node in software (e.g. TTL input or switched supply). | Galvo node toggles the laser 10 × per second for 10 s; photodiode confirms every transition. (open: OQ-2) | intake d-34 | [evidenced] |
| NF-VLT-17 | Laser colour, ball colour and background are chosen so that the spot is distinguishable on the ball and the ball against the background for every camera. | Static test: ball detected per F-VLT-1 and spot on ball detected per F-VLT-2 in ≥ 95 % of frames for each camera. (open: OQ-2, OQ-7) | intake d-35 | [evidenced] / threshold [estimated] |
| NF-VLT-18 | End-to-end deadline: from the exposure of a frame to the spot being placed at the corresponding target ≤ 30 ms, with a budget per stage (capture/readout, detection, transmission, fusion and prediction, transmission, galvo output, mirror settling) defined in the architecture. | Per-stage timestamps logged over a 10-min run: 99th percentile of the end-to-end time ≤ 30 ms; each stage within its budget. | intake d-37, sponsor | [evidenced] |
| NF-VLT-19 | Each node stays within ≤ 75 % average CPU and ≤ 50 % RAM on the Pi 3 during a run. | Resource log during a 10-min run. | intake d-40 | [estimated], confirmed by sponsor |
| NF-VLT-20 | Clock precision (NF-VLT-5) holds with monitoring traffic at its maximum (NF-VLT-8). | Clock offsets ≤ 1 ms during a run with monitoring at maximum rate. | concept §9 (PTP vs. monitoring on one switch) | [estimated] |

### Load and growth model

| Quantity | At launch | 1 year | 3 years | Peak factor | Evidence |
| --- | --- | --- | --- | --- | --- |
| Users / concurrent at peak | 1 operating team (11 students), 1 monitoring laptop | — (project ended) | — | 1 | [evidenced] |
| Requests per second at peak | per camera node: one observation per frame (frame rate open, OQ-1; ≥ 90 / s expected for NF-VLT-18); control → galvo: one target per fusion step | — | — | 1 | [estimated] |
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
| MIPI camera module on each camera node | in | Linux camera stack on Raspberry Pi OS; mode with ≥ 90 fps at reduced resolution required for NF-VLT-18 (open: OQ-1) | student team |
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
| — | PM review: hardware watchdog, recalibration hint, redundant control node | NF-VLT-4 and U-VLT-3 dropped; F-VLT-14 optional (nice to have) | → §7, F-VLT-14 |

### Open questions

- **OQ-1** — Camera model: resolution, frame rate modes, global vs. rolling shutter. Critical: NF-VLT-18 (30 ms) needs ≈ 90 fps or more. — student team — blocks: NF-VLT-18, F-VLT-1, F-VLT-2, the camera node design.
- **OQ-2** — Laser type, colour and power (Class ≤ 2, software-switchable, colour per NF-VLT-17). — student team — blocks: NF-VLT-2, NF-VLT-16, NF-VLT-17.
- **OQ-3** — Cube size (maximum amplitude, starting deflection, clamp envelope). — student team — blocks: F-VLT-9 envelope values, the cube configuration.
- **OQ-4** — Galvo driver input (signal type, voltage range, connector), mirror size, scan angle, step response; can the "Programm Board" be bypassed. — student team, from the delivered board — blocks: F-VLT-15, F-VLT-19, NF-VLT-18 settling budget.
- **OQ-5** — Converter board between galvo node and galvo driver. — student team — blocks: F-VLT-15.
- **OQ-6** — Lab laser-safety rules and responsible person. — student team, ask the lab supervisor before the first demo with the laser on — blocks: first laser-on test.
- **OQ-7** — Background dark or light (with ball and laser colour). — student team — blocks: NF-VLT-17.
- **OQ-8** — Enough Raspberry Pis for a redundant control node? — student team — blocks: whether optional F-VLT-14 is built.

## 9. Artifact Interactions & Interferences

Embedded checklist (MANIFEST Phase 3) applied; no other features exist. Rows are the existing components the feature touches.

| Existing component / feature | Interaction (how we use it) | Interference (how we might break it) | Extension needed | Backward-compatible |
| --- | --- | --- | --- | --- |
| Galvo kit driver + "Programm Board" | drives the mirrors from our X/Y signals | the kit's own pattern player could drive the mirrors concurrently or at power-up → uncontrolled beam | disable/bypass the player → **F-VLT-19** (new) | n.a. |
| Kernel PTP / system clock on each node | exposure times and target validity in one clock | clock steps at start-up or a node not yet synchronized corrupt fusion and timeouts | use data only after sync → **F-VLT-20** (new) | n.a. |
| Ethernet switch (shared by PTP, loop messages, monitoring) | carries all traffic | monitoring bursts (images) delay PTP packets and loop messages → precision and deadline degrade | **NF-VLT-20** (new); NF-VLT-6, NF-VLT-8 | n.a. |
| Kill switch / watchdog / laser supply | hardware safety layer | after the kill switch is released, software that still "thinks" it is armed would switch the laser on unexpectedly | re-arm required after any safe state → **F-VLT-21** (new) | n.a. |
| Camera stack on Pi 3 (CPU, USB-attached Ethernet share the same SoC) | capture at high frame rate, on-node detection | high frame rate capture + detection + network on a Pi 3 may exceed CPU; Ethernet on the Pi 3 shares USB bandwidth | NF-VLT-19 budget; frame mode selection in architecture | n.a. |
| Raspberry Pi OS scheduling | all node processes | non-real-time scheduling → jitter in detection and galvo output | priorities / CPU pinning decided in architecture; measured via NF-VLT-18 | n.a. |
| Monitoring laptop | receives pushed data | none on the loop as long as NF-VLT-6/7/10 hold | — | n.a. |
| Calibration files | loaded at start by control and galvo nodes | stale calibration after the setup was bumped → systematic aiming error | none — visible as aiming error on the display (U-VLT-1); recalibrate per F-VLT-12/13 | n.a. |

## 10. Schema Extensions

All distances in mm (cube coordinates), times in ns of the shared PTP clock (`int64`), image positions in px. Transport and encoding are decided in the architecture; the fields below are binding.

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
| `t_place_ns` | `int64` | time at which the spot shall be at `position` |
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

**Calibration files**

- `camera_calibration` per camera: intrinsic matrix (3 × 3), distortion coefficients, rotation (3 × 3) and translation (3) into cube coordinates, image size, date, residual error.
- `galvo_calibration`: mapping cube point → (angle X, angle Y), form set in architecture; angle envelope of the cube (for F-VLT-9); date, residual error.

## 11. Architecture & Vertical Slices

open — after PM review

## 12. Architecture Consistency Review

open — after PM review

## Notes (human)

<!-- Off limits for all skills. Copied verbatim on every rewrite. -->

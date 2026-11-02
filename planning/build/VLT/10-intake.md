---
stage: intake
owner: build-intake
status: done
revision: 2
created: 2026-11-02T15:59
updated: 2026-11-02T16:03
input: problem statement (chat, 2026-11-02), 00-build.md@2
feature: VLT
path: A
---

# Intake VLT: Voxel Camera with Laser Tracking

_Result of the intake stage. Part 1 is what the prototype, the brief, the register or the shortlist entry already answer (Path B, R, S — extracted, not asked). Part 2 is what had to be grilled (Path A). Part 3 is the draft the concept stage starts from. Nothing here is ratified; the concept stage numbers and freezes._

## Part 1 — Extracted from the brief, the prototype, the register or the shortlist entry (Path B · R · S)

### Field of application

Distributed real-time system (DRS) — five networked nodes closing a loop through the physical world (camera → compute → galvo/laser → camera). Checklist sections also used: Embedded system, Hardware system, Cross-cutting standards, By Technology, General Robustness (Software). Confirmed by the user.

### Purpose and the specific person

A lab demo that shows multi-camera 3D tracking: three Raspberry Pi cameras at right angles around a cube watch a ball swinging on a string through the cube; a node computes the ball's 3D position and steers a laser through a galvo mirror pair so that the spot stays on the ball; the cameras also see the spot, so the system measures its own aiming error. Built and operated by a team of 11 students; watched by other students at one presentation. [evidenced]

### What the prototype really does

not relevant for this feature — cold start

### Candidate requirements taken over

not relevant for this feature — cold start

### Guardrails taken over

not relevant for this feature — cold start (guardrails set during grilling appear in Part 2 as d-9 … d-14)

### Deliberately-cannot rows (brief Part 2)

not relevant for this feature — cold start

### As-built architecture sketch

not relevant for this feature — cold start

### Decided and open questions carried over

not relevant for this feature — cold start

### Register trace (Path R)

not relevant for this feature

### Taken from the shortlist entry (Path S)

not relevant for this feature

## Part 2 — Grilling (Path A)

### Agenda worked through

| # | Topic | Source | Answer (short) | Evidence |
| --- | --- | --- | --- | --- |
| 1 | Purpose | user | Lab demo to show multi-camera 3D tracking | [evidenced] |
| 2 | Operator and audience | user | Students who build the system operate it; other students watch | [evidenced] |
| 3 | Camera nodes | user | Raspberry Pi 3 with a MIPI camera each; camera model unknown → OQ-1 | [evidenced] / [unknown] |
| 4 | Galvo | user + product page | IMLCDRS "10K 3D DIY Laser Galvo … 15º+ Programm Board + 15V Netzteil"; "10K" likely 10 kpps, "15º+" unlabelled; input signal, mirror size, step response unknown → OQ-4 | [evidenced] (title) / [estimated] / [unknown] |
| 5 | Laser, cube size | user | Not decided → OQ-2, OQ-3 | [unknown] |
| 6 | Master node | user | Raspberry Pi 3 | [evidenced] |
| 7 | Network and node topology | user | Wired Ethernet through a switch; 3 camera Pis → control Pi (3D position) → galvo Pi → converter board (open, OQ-5) → galvo driver. Five Pi 3 nodes in total | [evidenced] |
| 8 | Pendulum | user | Ball ≈ 5 cm diameter, string ≈ 1 m. Derived: period ≈ 2 s; at ±30 cm amplitude peak speed ≈ 1 m/s; "on the ball" radius 25 mm is crossed in ≈ 25 ms at peak speed | [estimated] |
| 9 | Success criterion | user | Spot on the ball 80 % of the time | [evidenced] |
| 10 | Test window | user | From release until the swing amplitude is below 5 cm (instead of a fixed 60 s) | [evidenced] |
| 11 | Laser class | user | Class 2 maximum; lab rules not yet checked → OQ-6 | [evidenced] |
| 12 | Laser safety behaviours | proposed, user confirmed | Off by default; aim clamped to cube; off when no fresh target; physical kill switch | [evidenced] |
| 13 | Camera failure | user | Keep running with two cameras (degraded, shown); fewer than two → laser off | [evidenced] |
| 14 | Time base | user | Identical clock on all nodes by software clock synchronization, kernel PTP preferred; precision ≤ 1 ms | [evidenced] |
| 15 | Display | user | A screen with live values and camera images; location open (design note: separate debug laptop with a socket server, every Pi pushes data) | [evidenced] |
| 16 | Monitoring vs. real time | proposed, user confirmed | Best effort, never blocks the loop, system runs without the laptop, bandwidth bounded, loop timing proven with monitoring on and off | [evidenced] |
| 17 | Laptop authority | user | Observe only; control stays on the Pis | [evidenced] |
| 18 | Operator control | user | Physical button on the control Pi; control method configurable: `button` or self-arming `auto` (for a Pi without a button); no SSH control | [evidenced] |
| 19 | Calibration | user | Manual for cameras and galvo in v1; automatic galvo calibration via the spot later, only if the cameras see the spot well | [evidenced] |
| 20 | Environment | user | Controlled setup, uniform background (dark or light — open, OQ-7), coloured ball | [evidenced] |
| 21 | Operation (I7) | user | Team of 11 students during testing and one presentation; project ends afterwards | [evidenced] |
| 22 | Running cost (I8), load (I9), standard deferrals | proposed, user confirmed | Fixed cost only; one installation, small and stable; deferrals as in the table below | [evidenced] |
| 23 | Control-node redundancy | user | Optional: a redundant control Pi takes over if the active one fails, only if enough Pis are available → OQ-8 | [evidenced] |

**ADR seeds (decided by the user, to be recorded by the concept stage):**

- Five Raspberry Pi 3 nodes on one wired Ethernet switch: 3 × camera, 1 × control, 1 × galvo (galvo output on its own Pi).
- Clock synchronization by software PTP (kernel), target ≤ 1 ms. Note: the Pi 3 Ethernet (USB-attached) has no hardware timestamping — precision must be measured. [estimated: well below 1 ms on a quiet switch]
- Debug/monitoring on a separate laptop, observe only, nodes push data to it (design note — location of the display still a design choice).
- Manual calibration in v1.
- Product code under `src/` with one subfolder per node (from 00-build.md).

**Design notes parked (requirements first):**

- Latency compensation: a pendulum is predictable; aiming at the predicted position at illumination time (not the last measured one) is likely needed to meet d-8 — design choice for concept.
- Whether camera nodes detect the ball on-board or ship images to the control node: architecture question (Pi 3 CPU, 100 Mbit Ethernet).
- The galvo kit's "Programm Board" may include its own pattern player; it must be bypassed so X/Y are driven by our code.
- Hardware camera trigger as an alternative to timestamp-based fusion.

### Field-standard concerns

| Concern | Standard / check | Applies | Candidate requirement or deferral rationale |
| --- | --- | --- | --- |
| Laser product classification | IEC 60825-1 (laser classes) | yes | d-9 (Class ≤ 2), d-10 … d-14 safety behaviours, OQ-6 lab rules |
| Personal data (people may appear in camera images) | GDPR | yes (light) | d-28: images shown live only, not stored by default |
| Product sold in the EU | CE marking | deferred | One-off lab demo, not placed on the market |
| Accessibility, PCI-DSS, HIPAA, ISO 27001, ISO 9001 | — | no | Not triggered |
| DRS: global time base | precision π, granularity g > π | yes | d-16, d-17 |
| DRS: timestamps compared across nodes | reasonableness condition, ±2g | yes | d-16; fusion rule for observations of different age → concept |
| DRS: temporal accuracy of RT images | d_acc per image; phase sensitivity | yes | d-4 (aim at the ball's position at illumination time), d-37 |
| DRS: message triggers action | permanence / action delay | yes | d-12 (stale target → laser off); d-37 |
| DRS: end-to-end transaction | end-to-end deadline, budget per stage | yes | d-37 (budget per stage camera → control → galvo → spot, measured on target) |
| DRS: node failure tolerated | fault hypothesis, k, redundancy degree | yes | d-15 (k = 1 camera node); control/galvo failure → safe state (d-12, d-14); d-29 optional control redundancy |
| DRS: replicated nodes vote | replica determinism | only with d-29 | Concept decides together with d-29 (OQ-8) |
| DRS: nodes join / leave | membership, degraded mode | yes | d-15, d-39; with d-29 also leader/follower membership |
| DRS: peak load | load hypothesis per channel, no thrashing | yes | d-21 (monitoring bandwidth), d-40 (CPU budget) |
| DRS: composability | property survives integration | yes | d-22 (loop timing unchanged with monitoring on/off) |
| DRS: gateway between clusters | flow control | no | Single cluster on one switch |
| DRS: safety-relevant actuator | effect monitored, not command | yes | d-6 (spot measured by cameras); d-38 (spot seen while laser should be off → alarm, safe state) |
| DRS: node reintegration | ground state, reintegration point | yes | d-39 (camera node restarts into the running system) |
| Embedded: real-time deadlines, jitter | WCET / timing analysis | yes | d-37 (measured, not proven — demo) |
| Embedded: safety-relevant (IEC 61508 etc.) | functional safety standard | deferred | Class ≤ 2 laser with hardware kill switch in a lab demo; no SIL claim |
| Embedded: constrained resources | CPU/RAM budgets | yes | d-40 |
| Embedded: battery / power | power budget | no | Mains powered |
| Embedded: OTA update with rollback | — | deferred | No operation after the presentation; d-31 covers reproducible setup |
| Embedded: flash wear | write-cycle budget | deferred | SD cards, no continuous storage (d-28); one-off operation |
| Embedded: watchdog | kick strategy, fault recovery | yes | d-14 |
| Embedded: buses (I2C/SPI) | error handling | yes | d-36 (converter board link; bus decided with OQ-5) |
| Hardware: EMC, environment, electrical safety, manufacturing, reliability | EN 55032, IEC 62368-1 … | deferred | Off-the-shelf boards and supplied PSUs used as delivered; lab environment; one unit |
| Hardware: signal integrity / level matching | voltage levels | yes | d-36 (converter output matches driver input, OQ-4) |
| Technology: code review, version control, tests | — | yes | d-31 |
| Technology: CI pipeline, SBOM, static analysis | — | to decide in concept | Team of 11 on one repo; scope set at concept |
| Technology: concurrency present | race/deadlock analysis, stress test | yes | Every node is concurrent (capture, network, output); stress test in synthesis |
| Technology: Docker, DB, secrets, public endpoint | — | no | Not triggered |
| Robustness: failure handling, config externalized, observability, reproducibility | — | yes | d-12, d-15, d-18, d-24, d-31 |
| Operating cost section | — | no | Fixed running cost only (I8) |
| Capacity & scaling section | — | deferred | One installation, small and stable (I9) |

### Operation

| Role | Name | Time share | Evidence |
| --- | --- | --- | --- |
| content / data upkeep (calibration, setup) | student team (11) | during testing and the presentation only | [evidenced] |
| technology / hosting (Pis, network, software) | student team (11) | during testing and the presentation only | [evidenced] |
| user support (running the demo) | student team (11) | one presentation; project ends afterwards | [evidenced] |

### Running cost

| Question | Answer | Evidence |
| --- | --- | --- |
| Cost drivers that grow with use (AI calls, documents, compute, metered services) | fixed running cost only — hardware, no cloud or metered services | [estimated], confirmed by user |
| Who pays — price per user, fixed budget, nobody yet | not relevant — one-off hardware | [estimated], confirmed by user |
| Heaviest realistic user — what, how much | not relevant | — |
| Monthly ceiling | not relevant | — |

### Load and growth

| Quantity | At launch | In 1 year | In 3 years | Evidence |
| --- | --- | --- | --- | --- |
| Users (named / active per day; internal or external) | 11 operators, one audience of students | — (project ended) | — | [evidenced] |
| Concurrent users at peak | 1 operating team, 1 observer laptop | — | — | [estimated], confirmed |
| Peak pattern and factor (time of day, month end, campaign) | one presentation | — | — | [evidenced] |
| Data volume (records, documents, GB) | live monitoring stream only; no stored images by default | — | — | [estimated], confirmed |
| External limits (rate limits or quotas of services we call) | none; 100 Mbit Ethernet per Pi 3 is the internal limit | — | — | [evidenced] |

### New candidate requirements

| Draft ID | Requirement | Type | Origin | Evidence |
| --- | --- | --- | --- | --- |
| d-1 | Each camera node detects the ball in every captured frame and sends its image position, tagged with the exposure timestamp, to the control node. | F | grilling #7, #14 | [evidenced] |
| d-2 | Each camera node detects the laser spot in every captured frame and sends its image position, tagged with the exposure timestamp, to the control node. | F | problem statement, #12 | [evidenced] |
| d-3 | The control node computes the ball's 3D position in cube coordinates from the observations of at least two camera nodes using the stored camera calibration. | F | problem statement, #13 | [evidenced] |
| d-4 | The control node sends the galvo node a target such that the spot lands where the ball is at the moment of illumination (compensating the loop delay), not where it was last measured. | F | #8 derived | [estimated] |
| d-5 | The galvo node converts each target into mirror angles using the stored galvo calibration and drives the galvo accordingly. | F | #7 | [evidenced] |
| d-6 | The control node computes the aiming error (distance between measured spot and measured ball centre) for every frame in which the spot is seen. | F | problem statement | [evidenced] |
| d-7 | The system detects the start of a run (release of the ball) and its end (swing amplitude below 5 cm), computes the hit rate of the run and shows it. A frame counts as a hit when the spot is within 25 mm of the measured ball centre; a frame in which no camera sees the spot counts as a miss. | F | #9, #10 | [evidenced] |
| d-8 | Acceptance: in a run from release until the amplitude is below 5 cm, the hit rate per d-7 is at least 80 %. | NF | #9, #10 | [evidenced] |
| d-9 | The laser is visible and at most Class 2 (IEC 60825-1). | NF | #11 | [evidenced] |
| d-10 | The laser is off at start-up, during restart of any node, and whenever no valid ball position is available. | F | #12 | [evidenced] |
| d-11 | The galvo node clamps every aim to the cube volume, regardless of the target it receives. | F | #12 | [evidenced] |
| d-12 | The galvo node switches the laser off when it has not received a fresh target within a timeout (value set in concept). | F | #12 | [evidenced] |
| d-13 | A physical kill switch cuts the laser independently of all software. | NF | #12 | [evidenced] |
| d-14 | If the galvo node's software hangs, the laser is switched off by hardware (watchdog). Candidate — to be confirmed at the PM review. | NF | #13 (extrapolated) | [estimated] |
| d-15 | With exactly two camera nodes delivering the ball, tracking continues and the operator display shows "degraded" and which camera is missing; with fewer than two, the laser is off until at least two deliver again. | F | #13 | [evidenced] |
| d-16 | All nodes share one clock synchronized over Ethernet with precision ≤ 1 ms; every observation carries its exposure time in that clock. | NF | #14 | [evidenced] |
| d-17 | The clock offset of every node is measured and shown on the display. | F | #14 (extrapolated, user confirmed) | [evidenced] |
| d-18 | A screen shows live values (hit rate, aiming error, mode, camera status, clock offset) and the camera images with the detected ball and spot marked. | F/U | #15 | [evidenced] |
| d-19 | Sending monitoring data never blocks the tracking loop; under back-pressure monitoring data is dropped, not queued. | NF | #16 | [evidenced] |
| d-20 | Tracking and safety behave identically with and without the monitoring laptop connected. | NF | #16 | [evidenced] |
| d-21 | Monitoring traffic of all nodes together stays within a defined share of the 100 Mbit link (images reduced in rate and size; value set in concept). | NF | #16 | [evidenced] |
| d-22 | The loop timing (d-37) and the acceptance (d-8) are verified both with monitoring on and off. | NF | #16 | [evidenced] |
| d-23 | The monitoring laptop has observe-only access: there is no command path from it into any node. | NF | #17 | [evidenced] |
| d-24 | The arming method is set in the configuration: `button` (operator arms tracking and laser with a physical button on the control node; GPIO pin and debounce configurable) or `auto` (arms as soon as at least two cameras see the ball, for a node without a button). No other control path (e.g. SSH commands). The safety behaviours d-10 … d-14 apply unchanged in both modes. | F | #18 | [evidenced] |
| d-25 | A manual calibration procedure determines each camera's intrinsic and extrinsic parameters in cube coordinates; the result is stored and reused until recalibrated. | F | #19 | [evidenced] |
| d-26 | A manual calibration procedure determines the mapping from cube coordinates to mirror angles; the result is stored and reused until recalibrated. | F | #19 | [evidenced] |
| d-27 | When the aiming error stays systematically high, the display recommends recalibration. | F | #19 (extrapolated, user did not object) | [estimated] |
| d-28 | Camera images are shown live only and are not stored by default. | NF | #22 (GDPR) | [evidenced] |
| d-29 | Optional: a second control node takes over when the active one fails; the galvo node follows exactly one control node at a time; both use the same calibration. (open: OQ-8) | F | #23 | [evidenced] |
| d-30 | The system runs stably for repeated full runs (several minutes each) within one presentation session. | NF | #10 (extrapolated) | [estimated] |
| d-31 | The setup of every node is reproducible from the repository (scripted), code is version-controlled and reviewed, and every node's code has automated tests. | NF | #22 | [evidenced] |
| d-32 | Product code lives under `src/` with one subfolder per node type. | NF | Director start | [evidenced] |
| d-33 | All nodes are Raspberry Pi 3 on one wired Ethernet switch. | NF | #3, #6, #7 | [evidenced] |
| d-34 | The laser can be switched on and off by the galvo node in software (e.g. TTL input or switched supply). | NF | #12 (consequence) | [evidenced] |
| d-35 | Laser colour, ball colour and background are chosen so that the spot is distinguishable on the ball and the ball against the background for all cameras. (open: OQ-2, OQ-7) | NF | #20 | [evidenced] |
| d-36 | The galvo node outputs X/Y signals matching the galvo driver's input specification through a converter board, with defined error handling on the link to that board. (open: OQ-4, OQ-5) | F | #4, #7 | [evidenced] |
| d-37 | An end-to-end latency budget from exposure to spot placement is defined per stage (capture, detection, transmission, fusion, transmission, galvo output, mirror settling) and measured on the target hardware. | NF | DRS checklist, #8 | [estimated] |
| d-38 | If a camera sees the spot while the laser should be off, the system raises an alarm and goes to the safe state. | F | DRS checklist (effect monitored) | [estimated] |
| d-39 | A restarted camera node rejoins the running system without restarting the others. | F | DRS checklist, #13 | [estimated] |
| d-40 | Each node stays within a defined CPU and memory budget on the Pi 3, measured during a run. | NF | Embedded checklist | [estimated] |

### Still open after grilling

- **OQ-1** — Camera model (resolution, frame rate, global vs. rolling shutter). Rolling shutter distorts a ball at ~1 m/s. — student team, before the PM review.
- **OQ-2** — Laser type, colour and power (Class ≤ 2, software-switchable, colour per d-35). — student team, before the PM review.
- **OQ-3** — Cube size (sets the maximum swing amplitude and the starting deflection of a run). — student team, before the PM review.
- **OQ-4** — Galvo driver input: signal type, voltage range, connector; mirror size, scan angle, step response; whether the "Programm Board" can be bypassed. Product page gave the title only. — student team, from the delivered board or its datasheet, before concept §11.
- **OQ-5** — Converter board between the galvo node and the galvo driver (depends on OQ-4). — student team, before concept §11.
- **OQ-6** — Lab laser-safety rules and responsible person. — student team, ask the lab supervisor before the first demo with the laser on.
- **OQ-7** — Background dark or light (chosen together with ball and laser colour, d-35). — student team, before concept §11.
- **OQ-8** — Are enough Raspberry Pis available for a redundant control node (d-29)? — student team, before the PM review (sets d-29's priority).

## Part 3 — Draft for the concept stage

- **Path:** A — cold start from a problem statement; everything grilled.
- **Ubiquitous language seeds:** cube (the tracking volume, cube coordinates), ball, string / pendulum, swing, amplitude, run (release until amplitude < 5 cm), hit (spot within 25 mm of ball centre), hit rate, spot (laser spot), aiming error, camera node, control node, galvo node, converter board, galvo driver, observation (image position + exposure time), target, camera calibration, galvo calibration, arming (button / auto), safe state (laser off), degraded mode (two cameras), monitoring laptop, kill switch.
- **Out of scope (for now):** automatic galvo calibration via the spot (later, if spot visibility allows); storing camera images; long-term operation, OTA updates; certification (CE, EMC, functional safety); any control path from the laptop; SSH control; redundancy of the galvo node.
- **Integration points known:** 5 × Raspberry Pi 3 on wired Ethernet (switch); software PTP clock sync; MIPI cameras (OQ-1); galvo driver IMLCDRS kit with 15 V supply (OQ-4) via converter board (OQ-5); software-switchable Class ≤ 2 laser (OQ-2); GPIO button on the control node; hardware kill switch; hardware watchdog (d-14); observe-only monitoring laptop with a socket server.
- **Riskiest assumption after intake:** Pi 3 camera nodes, a 100 Mbit network and a hobby galvo are fast enough — with prediction of the pendulum — to keep the spot on a 5 cm ball for 80 % of a run. Second: the cameras can see the spot on the ball reliably (OQ-1, OQ-2, OQ-7).
- **Recommended first vertical slice:** two camera nodes detect a hanging, non-swinging ball, the control node triangulates it, the galvo node aims the laser at it — with all safety behaviours (d-10 … d-13) in place from the start.

## Notes (human)

<!-- Off limits for all skills. Copied verbatim on every rewrite. -->

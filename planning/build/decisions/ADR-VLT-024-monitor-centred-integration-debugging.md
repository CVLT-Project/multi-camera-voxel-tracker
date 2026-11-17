# ADR-VLT-024 — Monitor-centred integration debugging with a mirror stream

- **Status:** accepted · 2026-11-17 · decided by the team (integration test debugging concept, M3)
- **Feature:** VLT

## Context

M3 asks for a concept to find the cause quickly when an end-to-end test fails on the assembled system with live data. The architecture already has a push-only monitoring laptop (F-VLT-34/37/39/40), but it received only condensed status, images and events, and ChainStats, SessionRecorder and the dashboard were planned for slice S7, after all hardware slices. The team has three sub-teams (camera, control, laser team) and no separate integration team.

## Decision

1. **The monitor is the main debugging tool.** Every node sends every loop message it sends a second time, as the same bytes, to the laptop (**mirror stream**); the control and galvo nodes add one record per slot or received Target with receive stamps, rejections and decisions. The monitor runs cross-node **plausibility checks** and keeps an **incident list** with a drill-down to the stage times of the affected update.
2. **The laptop stays optional and nothing waits for it.** Loop → bounded queue with `put_nowait` (drop and count) → sender process with a non-blocking socket, errors counted, no retry; no presence check; dynamic ARP so an absent laptop causes no flooding. The mirror stream is always on (same timing in test and demo). The monitor never acts on the system.
3. **Separate tools only where the monitor can't reach:** a Saleae Logic 8 with trace pins, laser-enable and kill-switch lines for independent timing of the electrical chain (NF-VLT-29; no LED or photodiode, amended rev 30); SessionRecorder and Replay to reproduce (F-VLT-32, NF-VLT-22); a FaultInjector with a local schedule in the test profile only (NF-VLT-10); node and hardware simulators to isolate a node.
4. **Slice order:** S7 (monitoring) is built right after S1, so the monitor serves every hardware integration step.
5. **Owners:** monitor, SessionRecorder, Replay: control team; bench measurement and trace pins: laser team; reference data set: camera team; fault injection: the node team that finishes its node slice first.

## Alternatives considered

- Separate tools per debugging step (tcpdump on the nodes, ChainStats only in S7): more tools, monitor blind during the first integration.
- A 16-channel analyzer or a microcontroller as instrument: the team's Saleae Logic 8 with two wiring profiles suffices.
- Fault injection over SSH from the laptop: a network path into the running loop, excluded by NF-VLT-10 and ADR-VLT-014.

## Consequences

- MonitorLink, MonitorServer, the network budget (+ ≈ 4 Mbit/s) and the slice plan change (concept rev 29, §11.7); new modules PlausibilityChecker, TracePin, FaultInjector, BenchCapture, TraceMerge.
- tcpdump is not needed; SessionRecorder stays, because Replay needs a lossless record of what the loop used.
- The monitor's checks are diagnostic only; safety stays on the nodes.

## Traces to

F-VLT-32, F-VLT-39, F-VLT-40, NF-VLT-5, NF-VLT-6, NF-VLT-10, NF-VLT-18, NF-VLT-20, NF-VLT-22, NF-VLT-23, NF-VLT-29, NF-VLT-31, NF-VLT-34

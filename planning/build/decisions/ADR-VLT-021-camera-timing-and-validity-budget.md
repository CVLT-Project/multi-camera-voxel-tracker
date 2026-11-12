# ADR-VLT-021 — Numeric camera-chain timing and validity profile

- **Status:** proposed · 2026-11-10 · camera-chain timing and validity budget proposal for team review at M3 consistency review (Gate 2); measured feasibility on Pi 3 and selected camera remains pending.
- **Feature:** VLT
- **Resolves:** OQ-12 design values; hardware timestamp adapter qualification follows OQ-1.
- **Source of numeric values:** ../VLT/camera-profile.json

## Decision

Fusion runs every 10 ms, aligned to the shared clock, with placement requested 5 ms after the slot begins. Cameras may free-run at 80–120 fps; timestamp-based alignment/rectification is mandatory. Choose these values; do not present them as inferred specifications of an unknown camera.

| Validity item | Limit |
| --- | --- |
| Current observation age at fusion | ≤ 25 ms |
| Exposure skew before alignment | ≤ 20 ms |
| Prediction horizon | ≤ 30 ms |
| Target transport age, creation to receipt | ≤ 5 ms |
| Oldest current source sample to actual target use | ≤ 30 ms |
| Target expiry | min(t_place + 1 ms, oldest source + 30 ms) |
| Sync-status age | ≤ 100 ms; report at least every 50 ms |
| Pairwise clock offset / per-node offset | ≤ 1 ms / ≤ 0.5 ms |
| Global granularity g | 2 ms, greater than 1 ms precision; cross-node order claims only beyond ±4 ms |
| Future timestamp tolerance | 2 ms; beyond this reject |
| Camera timestamp-mapping error | ≤ 0.5 ms |
| Galvo interpolation period | ≤ 0.5 ms |

Target creation time is explicit. Old-source targets are rejected even if newly received. At the configured validity boundary a value is still usable, except t_valid_until is exclusive: at/after expiry it is rejected. Local watchdog/timeout durations remain monotonic and cannot be extended by shared-clock correction. The 100 ms target-loss timeout remains the communication fallback; it does not permit using a stale target for 100 ms.

## T1 budget

| Stage | Maximum allocation, ms |
| --- | --- |
| Exposure midpoint through capture/readout | 6 |
| Detection | 4 |
| Camera to control | 1 |
| Waiting for fusion (including grid jitter) | 11 |
| Fusion/prediction | 1 |
| Control to galvo | 1 |
| Output/DAC | 2 |
| Mirror settling | 1 |
| Reserve | 3 |
| Total | 30 |

Each stage's measured high-water mark in the loaded 10-minute target run must fit its allocation; end-to-end p99 must be ≤ 30 ms, with maxima and discarded targets reported. Reused observations are additionally bounded by the source-age rule: a nominal 25 ms old source at the slot plus the 5 ms placement lead reaches the 30 ms limit; expiry never adds time beyond it. A target that cannot be placed while valid is a miss. The budgets are simultaneous constraints, not evidence of achieved latency.

The frame period is 8.333…–13 ms, detection ≤ 4 ms per frame; fusion period 10 ms with the existing ≤ 1 ms grid jitter and execution ≤ 1 ms; galvo interpolation period ≤ 0.5 ms, execution ≤ 0.25 ms; status on each applied target and at least every 50 ms; monitoring remains asynchronous at ≤ 5 images/s. Nominal/output sampling details and RT scheduling implementations are to satisfy these bounds in the later architecture, rather than add open camera-team choices.

## Acceptance

Boundary tests for every limit, clock steps, old-source/fresh-packet targets, row timing and future timestamps; loaded 10-minute measurements with monitoring off/on/paused; independently measured T1 and shutdowns under NF-VLT-29. Camera/driver binding has to demonstrate these targets. Failure to qualify is reported; no timing result is filled with an estimate.

## Traces to

F-VLT-1/3/4/5/18/20/22/23/24/39/42/43/44, NF-VLT-5/18/19/24/26/27/29/33, OQ-1/12, ADR-VLT-002/008/009/018/020/022

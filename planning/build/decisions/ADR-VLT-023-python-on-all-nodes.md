# ADR-VLT-023 — Python on all nodes

- **Status:** accepted · 2026-11-17 · decided by the sponsor (architecture design question "programming language of the nodes", open since Gate 1)
- **Feature:** VLT

## Context

The architecture (§11) needs typed module signatures, so the implementation language had to be fixed. The nodes are Raspberry Pi 3 Model B+ (NF-VLT-15): three camera nodes (≈ 80–120 fps capture and detection, ADR-VLT-020), the control node (10 ms fusion period, ADR-VLT-021), the galvo node (I2S DAC output stream with an interpolation period ≤ 0.5 ms, ADR-VLT-021), and the monitoring laptop. Options were: C++ on camera and galvo with Python elsewhere, C++ on all Pi nodes, Python everywhere, or deciding after the R-1 bench check.

## Decision

All node software and the monitoring server are written in **Python 3** (the version shipped with the node OS image of NF-VLT-13). Numerical work uses NumPy; image processing uses OpenCV (Python bindings); the camera is driven through picamera2/libcamera; the DAC is written as a stereo audio stream through ALSA. Message schemas, the shared decision logic, the replay (NF-VLT-22) and the simulators (NF-VLT-31) are one Python package used by every node.

## Rationale

One language for every node gives one package for the shared logic, the replay and the simulators, so the hardware-free tests (NF-VLT-22) test exactly the code the nodes run. It is also the fastest to develop and review for the student team.

## Consequences

- **Timing risk, camera nodes (adds to R-1).** Per-frame detection at 80–120 fps in Python on a Pi 3 must fit the 4 ms detection stage of T1 (ADR-VLT-021) and NF-VLT-19 (CPU ≤ 75 %). Detection works on the camera's low-resolution stream with vectorised NumPy/OpenCV calls only, never per-pixel Python loops. The R-1 bench check now also measures detection time in Python; if it fails, the fallback is a change request (lower frame rate or a compiled detection kernel), decided by the team.
- **Timing risk, galvo node (new risk R-2).** The output stream is produced in blocks: the DAC is fed through ALSA in periods of ≤ 0.5 ms of samples, each block interpolated with NumPy from the current target. Garbage collection and interpreter pauses can delay a block; the ALSA buffer depth bounds how long the mirrors keep moving without new samples, and an empty buffer is an output-stream stop (T3, F-VLT-15). Bench check before Gate 2: block jitter and buffer underruns over a 10-min run.
- **Real-time configuration on every node.** Loop processes run with a real-time scheduling priority, pinned to one core, with automatic garbage collection disabled inside the loop and collected explicitly between periods; monitoring and logging run in separate processes (NF-VLT-6).
- Measured worst-case execution times (NF-VLT-33) are the deciding evidence; the architecture budgets stay as proposed until then.

## Traces to

NF-VLT-13, NF-VLT-14, NF-VLT-15, NF-VLT-18, NF-VLT-19, NF-VLT-22, NF-VLT-31, NF-VLT-33, F-VLT-15

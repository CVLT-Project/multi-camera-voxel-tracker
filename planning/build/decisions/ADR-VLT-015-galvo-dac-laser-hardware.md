# ADR-VLT-015 — Galvo, DAC and laser hardware; converter link faults detected by effect monitoring

- **Status:** accepted · 2026-11-10 · decided by the team (hardware selection) · resolves OQ-2 and OQ-5
- **Feature:** VLT

## Context

OQ-2 (laser) and OQ-5 (converter board) were open. OQ-4 (galvo input) is still open. The team has now selected the hardware.

## Decision

- **Galvo:** "15Kpps Laser Galvo DIY SLA 3D" scanner set with driver from AliExpress (item 1005013402042428). From the listing:
  - analog input ±5 V, 200 kΩ, 0.33 V/°;
  - optical scan angle ±15° at the standard setting, up to ±30°;
  - small-step response ≤ 0.5 ms, linearity 99.9 %, repeatability 8 µrad;
  - mirrors 11 × 7 mm, dielectric, > 99 % reflectance at 400–700 nm;
  - supply ±12 V DC, 0.5 A average, 1.2 A peak;
  - no pattern board listed.
  Still open (OQ-4): single-ended or differential input, connector, whether a supply is included.
- **Converter:** a PCM5102A I2S stereo audio DAC module (Amazon B0F7LL4S8Z); left channel = X, right channel = Y. Facts from the TI datasheet (SLAS859C):
  - output DC-coupled and ground-centred, full scale 2.1 V RMS (≈ ±2.97 V peak), single-ended;
  - filter delay 20 samples, or 3.5 samples with low-latency filter (FLT high);
  - 8–384 kHz sample rate;
  - when the I2S clock stops, the chip mutes to 0 V.
- **Laser:** Laserfuchs LFD650-1-12 (9 × 20 mm) dot laser (Amazon B0081S0Y40), from the manufacturer's data:
  - red, 650 nm, 1 mW, **Class 2**;
  - 3–12 V DC (typ. 3 V), 15–30 mA;
  - two power wires only, no modulation input;
  - collimated, 1 mrad divergence;
  - **housing at supply potential (+V)**.
- **Converter link faults are detected by effect monitoring only.** I2S is one-way, so the DAC output can't be read back. A lost I2S clock puts the mirrors at the centre (chip mute). A broken data line freezes or corrupts the aim. Both are detected by the cameras through F-VLT-26 (aiming error > 50 mm for 500 ms → laser off, alarm, latched safe state), i.e. within ≈ 600 ms instead of 100 ms. The team accepts this. While undetected, the beam stays inside the cube and the laser is Class 2. No read-back ADC is added.

## Rationale

The parts are cheap and available, and a Pi 3 drives I2S natively. A read-back ADC would add hardware and code for a fault that the cameras already detect, and the exposure in the meantime is limited to a Class 2 beam inside the cube.

## Consequences

- F-VLT-15 is rewritten: there is no separate link check. An interrupted output stream must switch the laser off within 100 ms.
- F-VLT-21, NF-VLT-23 and the reaction matrix (NF-VLT-34) treat a converter link fault as detected by its effect within 600 ms.
- NF-VLT-16: the laser is switched through its supply (no TTL input) and mounted electrically insulated (housing at +V).
- OQ-4 now includes level matching. The DAC's ≈ ±2.97 V covers ≈ 59 % of the galvo's ±5 V input, i.e. ≈ ±8.9° optical at the standard setting. Options: driver gain trim (up to ≈ ±17.8°), an amplifier with gain ≈ 1.7, or a larger galvo distance. NF-VLT-32 requires the cube to fit the usable angle.
- Audio output on the Pi is streamed through a buffer. Its depth counts against the 30 ms budget (NF-VLT-18), and an empty buffer drops the output to 0 V. These are architecture topics.

## Traces to

F-VLT-5, F-VLT-15, F-VLT-21, F-VLT-26, NF-VLT-2, NF-VLT-16, NF-VLT-18, NF-VLT-23, NF-VLT-25, NF-VLT-34, OQ-2, OQ-4, OQ-5, OQ-7

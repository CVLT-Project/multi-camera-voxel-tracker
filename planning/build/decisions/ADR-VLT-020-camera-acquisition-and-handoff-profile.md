# ADR-VLT-020 — Camera acquisition, exposure, calibration and data handoff

- **Status:** proposed · 2026-11-12 · M3 groundwork from the camera-team review; decided as a team in the M3 consistency review (Gate 2). Raspberry Pi 3 stays fixed; the camera model is not selected; Pi 3 feasibility at 80–120 fps with detection and JSON output is unverified.
- **Feature:** VLT
- **Would resolve (if accepted):** design choices in OQ-1/OQ-7/OQ-13, except camera model; amends ADR-VLT-001/012/016.
- **Machine-readable baseline:** ../VLT/camera-profile.json

## Decision

The fixed output image plane is 640 × 480 px, with 80–120 captured observations/s (frame period at most 13 ms). This is a chosen qualification target for the existing Pi 3, not a claim about an unknown camera. Each captured frame produces one Observation, including not-seen results; only one current complete frame is retained for processing, with no growing FIFO.

Use ordinary room lighting. Startup auto exposure/gain/white-balance has at most 5 s, within the existing 10 s camera-calibration budget. Initial exposure is 1000 us, allowed 250–2000 us; analogue gain 1–8, digital gain 1. Target white-ball luma 160–220 in 8-bit images. Freeze these settings until restart. Focus is fixed and recorded. If contrast or timing cannot be achieved in normal room light within these bounds, qualification fails; do not silently add lamps or lengthen exposure.

Global shutter is acceptable. Rolling shutter is acceptable only with measured row-exposure timing and motion rectification into the common frame-mid-exposure image coordinates. Record raw ball/spot sample times separately; timestamp-mapping error must be ≤ 0.5 ms. An arrival/callback timestamp is not a substitute for exposure time. Camera driver/API binding is supplied with the selected camera and validated, not guessed here.

Require ball diameter ≥ 14 px and coded marker short side ≥ 12 px throughout the test envelope. To improve oblique-marker visibility at this resolution, the two side camera centres become (-1200,400,1000) and (400,-1200,1000) mm; the overhead centre remains (700,400,2000). All aim at (400,400,400). Ideal full-cube FOV bounds are about 37.1° × 38.5°, 37.1° × 38.5°, and 39.3° × 38.0°; require at least 45° in both image directions. These are two elevated side views plus the offset overhead view, superseding the prior horizontal-side mounts.

Keep the 18 marker IDs/centres/planes of ADR-VLT-016, enlarge coded squares to 140 mm plus 20 mm white margin (180 mm total), and use corner offsets ±70 mm. Nominal scan-grid local u/v become {20,250,400,550,780} mm on each panel so points avoid the enlarged pads. Arming-check points (240,240,0), (800,560,240), (240,800,560) stay on grey areas. Actual visibility, corner positions and fits must be checked; nominal geometry is not calibration. Scan-point dwell is at most 500 ms; each arming-check point must have a valid measurement within 250 ms or the check fails with laser-off, still inside the overall 1 s budget.

## Camera/control contract

Use UDP unicast, UTF-8 JSON, at most 1400 bytes per datagram. Schema version 1; finite numbers only; int64 clock values are signed decimal strings on wire, with int64 semantics internally. Observation data is never retransmitted or queued behind old frames. The observation schema is ../VLT/camera-observation.schema.json.

Each Observation binds camera ID (0/1/2), sender session, frame sequence, setup revision, image profile and calibration ID; includes common-frame t_exposure_ns, raw t_ball_sample_ns/t_spot_sample_ns (null for not-seen), exposure/gain, rectified ball centre/radius and spot or null, clock offset/sync state. Ball/spot positions refer to the same rectified image time, while source-age checks use the oldest actual feature sample contributing to the current position. Driver timing/rectification must pass the synthetic and recorded tests; no exposure timestamp is invented if metadata is missing.

A CameraCalibration state message repeats every 500 ms, including camera/session/profile/setup/calibration IDs, K (9 values), distortion (k1,k2,p1,p2,k3), rotation (9), translation in mm (3), measured fit residual and marker count. It uses the same byte cap and latest-state semantics. Control only uses frames after matching calibration is validated. Unknown-calibration frames are discarded, not held in a backlog.

setup_revision hashes the fixed installation/profile/marker-map manifest. Per-camera calibration results have separate calibration_id hashes, so an otherwise valid camera restart does not change every peer's setup identity. A newly validated session/calibration is adopted before using its observations; retired-session frames are rejected. This clarifies the earlier proposed global calibration-set identity. Two healthy cameras keep tracking while the third rejoins. CameraCalibration is state data, not an operator command. Generic transport implementations/modules remain in the later architecture.

## Acceptance and ownership

Sensor and actuator modules delivers the settings/driver binding, calibration, schema-valid observations and real Pi 3 qualification report. System design checks time/validity integration; Integration support supplies measured marker corners and repeatable replay. Test missing metadata, dropped frames, stale/duplicate data, unknown calibration, mismatched image mode/setup and camera restart. No hardware pass is claimed before measurement. Only the camera model and its concrete driver binding remain open; the chosen values are targets.

## Traces to

F-VLT-1/2/3/7/12/17/22/23/24, NF-VLT-15/17/18/19/21/24/27/32/33, OQ-1/7/13, ADR-VLT-016/021/022

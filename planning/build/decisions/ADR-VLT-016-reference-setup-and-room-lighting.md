# ADR-VLT-016 — Reference installation and normal room lighting

- **Status:** selected design baseline · 2026-11-10 · physical layout definition delegated by the user; construction and measurements pending. This does not approve Gate 1.
- **Feature:** VLT
- **Resolves:** OQ-3, OQ-7 (colour/background choice), OQ-14 (operating-envelope definition). Camera model/driver binding and optical/timing verification remain pending; numerical settings and error budget are selected by ADR-VLT-020/021/022.

## Context

There is no physical installation yet. The user asked for its definition, keeping the camera model open, and specified ordinary room lighting without deliberately dark or over-bright conditions. The dimensions and materials below are design choices, not measurements of existing hardware. Camera-dependent settings must not be guessed.

## Decision

### Volume, frame and motion

| Item | Reference value |
| --- | --- |
| Cube | Clear inner volume 800 × 800 × 800 mm; origin (0, 0, 0), x/y along the floor, z up |
| Installation space | Reserve approximately 3 × 3 m of floor area and at least 2.3 m clear height; cube floor on a low base, at most 100 mm above the room floor |
| Frame | Rigid and braced, matte surfaces; supports outside the clear volume and camera sight lines |
| Ball | Rigid, matte white sphere, nominal diameter 50 mm; measure the delivered diameter for `ball_radius_mm` |
| Rest centre | Nominal (400, 400, 300) mm; measure the installed centre by hand for `rest_position_mm` (F-VLT-7) |
| Suspension | Thin matte dark thread; pivot (400, 400, 1300) mm; pivot-to-ball-centre distance 1000 mm, so the actual thread is shorter by the attachment offset |
| Suspension support | Separate rigid bridge above the cube; cross-member along y at x = 400 mm, at most 40 mm wide in x near z = 1300 mm, outside the overhead sight bundle over the swing envelope |
| Starting deflection | More than 100 mm and at most 300 mm horizontally from rest, any horizontal direction; release without pushing |
| Motion envelope | Speed ≤ 1000 mm/s and acceleration magnitude ≤ 4000 mm/s²; no intentional impacts or sudden hand-driven motions in acceptance runs |

The reference pendulum's centre stays within approximately x/y = 100…700 mm and z = 300…346.1 mm; a 25 mm radius leaves clearance to all faces. An ideal 1 m pendulum released from a 300 mm horizontal deflection reaches about 0.951 m/s. This is a geometric/design sanity check, not measured compliance. Measure the actual motion. Prediction and plausibility checks remain generic, without a pendulum assumption (ADR-VLT-011).

### Camera mounting

All three cameras aim at (400, 400, 400) mm. Coordinates are nominal optical centres in cube mm; the camera model remains OQ-1.

| Camera ID | Position (x, y, z), mm | View |
| --- | --- | --- |
| 0 | (-1200, 400, 1000) | Elevated view from the open x side |
| 1 | (400, -1200, 1000) | Elevated view from the open y side |
| 2 | (700, 400, 2000) | Downward, offset 300 mm in x from the suspension axis |

The offset overhead view deliberately refines the original ideal of three exactly perpendicular optical axes: a camera directly over the ball would look through its suspension. Ideal full-cube field-of-view bounds are about 37.1° × 38.5° for cameras 0/1 and 39.3° × 38.0° for camera 2. Reserve at least 45° in both image directions after crop, with the whole cube and markers in frame. This constrains the later lens/mode choice; it does not assert that an unknown module meets it. Mounts allow distance/aim adjustment, followed by recalibration and visibility checks. Secure cables outside the viewing volume.

At the suspension cross-member height the nominal overhead sight bundle to the ball stays at x ≥ approximately 435 mm over the reference swing, whereas the specified member ends at x = 420 mm. This ideal-geometry check includes the 25 mm ball radius. Check the actual bracket, support thickness and visibility over the whole swing after mounting; looking clear at rest alone is insufficient.

Hands leave the volume after release. Incidental occluders in normal runs are the thin thread and small frame/support silhouettes. Deliberate camera/ball covering remains a fault test, not a normal operating condition.

### Background and lighting

- Matte medium-grey panels cover the floor z = 0 and far walls x = 800 and y = 800, each 800 × 800 mm. Use neutral grey, approximately RAL 7037 as a colour reference, with a non-glossy finish. Keep x = 0, y = 0 and the top open for views and beam entry. These are backgrounds/scan surfaces; grey paint alone is not a certified laser enclosure.
- Use the room's normal installed lighting at its ordinary setting. No extra tracking lamps, deliberate dimming, over-lighting or lighting stress campaign is required for acceptance. Position the installation without a direct sun patch or strong specular glare on the volume.
- White ball, red laser and grey panels are the selected contrast arrangement. Spot/ball/marker visibility still has to pass F-VLT-1/2/12/13/31 and NF-VLT-32 with the actual cameras in that ordinary room light.
- No lux threshold, exposure time, gain or white-balance value is asserted without a camera. Determine and record camera settings after OQ-1, and actual exposure timing under OQ-12. Room brightness and sensor exposure are separate parameters; ADR-VLT-020 now selects bounded startup auto settings and locking, while actual model-specific settings must be recorded.
- Record room, light setting, daylight condition and camera settings with the reference data. Significant lighting/setup changes follow NF-VLT-21's re-recording rule.

### Calibration markers

Use 18 ArUco markers from the 4 × 4, 50-ID dictionary, rigidly attached to the frame-fixed panels. Each coded black square is 140 mm wide with a 20 mm white margin on every side (180 mm overall). Confirm readability in the final camera mode. Measure actual corner coordinates once for `marker_map`.

Use this ordered local centre list `(u, v)` in mm: (120, 120), (400, 120), (680, 120), (120, 680), (400, 680), (680, 680). IDs follow that order on each plane:

| IDs | Plane | Centre P, cube mm | Marker right U | Marker down V |
| --- | --- | --- | --- | --- |
| 0…5 | Floor | (u, v, 0) | (1, 0, 0) | (0, -1, 0) |
| 6…11 | Far x wall | (800, u, v) | (0, -1, 0) | (0, 0, -1) |
| 12…17 | Far y wall | (u, 800, v) | (1, 0, 0) | (0, 0, -1) |

Print in the U/V orientation. Coded-square corners in printed top-left, top-right, bottom-right, bottom-left order are `P - 70U - 70V`, `P + 70U - 70V`, `P + 70U + 70V`, `P - 70U + 70V`. White margins are outside those corners. The calibration uses measured corners, not nominal design coordinates.

Plan for each camera to see at least four complete markers on each of at least two planes. This layout target does not prove a well-conditioned intrinsic/distortion fit from a fixed scene. F-VLT-12/3 must demonstrate ≤ 0.5 px reprojection error, calibration within 10 s and the required 3D accuracy with the final camera. A failed fit keeps the camera absent; never substitute nominal calibration. Check marker visibility without the laser first.

### Galvo geometry and calibration points

Nominal galvo optical origin is (-1400, -1400, 2200) mm, neutral aim (400, 400, 400). The beam enters from the open upper-front corner, on the side of the views. A geometric check over the reference swing puts an ideal sphere's centrally illuminated point on the visible hemisphere of all three cameras. Actual support occlusions, spot contrast and NF-VLT-32's ≥ 95 % visibility for every camera pair remain physical tests.

The largest centre-axis-to-corner ray angle is about 12.75°. Leaving 10 % of the usable half-angle unused requires ≥ 14.17° usable optical half-angle. The listing's ±15° would meet that geometry only if the full range is driven and measured. The unamplified DAC estimate of ±8.9° (ADR-VLT-015) is insufficient at this position. Baseline level matching makes the full driver input range available, nominally ±5 V, with about 1.7 gain over the DAC peak. Use verified driver gain adjustment if sufficient, otherwise a suitable amplifier stage. Input type, actual gain, DC response, limits and settling remain OQ-4; this is not a wiring design or verification of delivered hardware.

The initial galvo scan uses every u/v combination of {20, 250, 400, 550, 780} mm on each panel, using the plane mappings above: 75 points total. Nominal points avoid the marker pads; skip/replace any actually covered by hardware or the ball, and use only points seen by at least two cameras. Arming-check reference points are (240, 240, 0), (800, 560, 240) and (240, 800, 560); replace an occluded point per F-VLT-31. These define points for the existing procedures, not new controls.

### Electronics and completion checks

Keep the five Pi 3 nodes and dedicated wired switch (at least six ports for nodes plus monitoring laptop). Mount power supplies/galvo driver outside the view and secure leads. The accessible kill switch stays outside beam paths; the existing laser isolation and laser-safety requirements continue to apply. No new safety certification is claimed.

Before reference recording: measure the frame, ball, rest point, marker corners and optical poses; verify field of view, marker readability, scan coverage, spot visibility and motion bounds. Then measure capture/detection and full T1 timing under ordinary room lighting, and record NF-VLT-21's data. Close the combined detection/calibration/triangulation/timing/prediction/placement error budget against the actual ball radius. Independent percentiles cannot simply be added as proof. OQ-14 remains open for that budget and evidence; OQ-12 remains camera-dependent.

## Rationale

An 800 mm cube contains the 50 mm ball and 300 mm deflection with clearance. A matte white ball and neutral grey background give a simple starting contrast arrangement. The two far walls and floor supply non-coplanar references and existing galvo-scan surfaces. The offset overhead view avoids the suspension axis; upper-front illumination exposes the lit side toward the views. Ordinary room lighting follows the user's stated conditions.

**Camera-profile amendment (ADR-VLT-020/021/022):** Pi 3 remains fixed. This current table uses elevated side views and enlarged 140 mm coded markers for the 640 × 480 profile; the former 400 mm side height and 80 mm coded squares are superseded. Exposure/gain/row policy, rates, numeric timing and the combined error/test plan are now selected in camera-profile.json; only the camera-model binding and measured results remain pending. Its earlier paragraphs describing all camera settings/budgets as unchosen are historical context, superseded by that profile.

## Consequences

- OQ-3 is resolved as a design choice; as-built measurements are still required.
- OQ-7's colour/background choice is resolved, with camera-dependent visibility validation pending. No lighting-extreme acceptance requirement is added.
- OQ-14 has numerical physical/motion bounds, with selected exposure/error policies and real performance still unverified.
- OQ-1 camera model/binding and delivered-hardware checks in OQ-4 remain open; OQ-12 numeric policy is resolved by ADR-VLT-021.
- `cube_size_mm` defaults to {x: 800, y: 800, z: 800}. Nominal rest centre (400, 400, 300) is replaced by the hand measurement. Marker/mount layout is defined; software architecture and Gate 1 remain pending.

## Traces to

F-VLT-1…7, F-VLT-9, F-VLT-12/13/24/31, NF-VLT-1/2/3/17/18/21/32, OQ-1/3/4/7/12/13/14, ADR-VLT-011/012/015

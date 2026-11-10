"""Rebuild the M2 review PDF from the selected requirement/profile sources."""
from pathlib import Path
import json
import re
import shutil
from xml.sax.saxutils import escape

import reportlab
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, Line, Circle, String, Polygon

HERE = Path(__file__).resolve().parent
BUILD = HERE.parent
CONCEPT = BUILD / 'VLT/20-concept.md'
PROFILE = json.loads((BUILD / 'VLT/camera-profile.json').read_text(encoding='utf-8'))
QA = json.loads((BUILD / 'VLT/camera-reference-plan.json').read_text(encoding='utf-8'))
SOURCE = CONCEPT.read_text(encoding='utf-8')
REV = re.search(r'^revision: (\d+)$', SOURCE, re.M).group(1)
DATE = '10 November 2026'
OUT = HERE / 'output/pdf/DRS_M2_Vocel_camera.pdf'
ORIGINAL = HERE / 'reference/DRS_M2_Vocel_camera_2026-11-06.pdf'
NAVY = colors.HexColor('#142b3b')
TEAL = colors.HexColor('#087e86')
LIGHT = colors.HexColor('#edf4f5')
GREY = colors.HexColor('#56646f')
AMBER = colors.HexColor('#fff2d9')
WIDTH = A4[0] - 84

assert PROFILE['hardware']['node_platform'] == 'Raspberry Pi 3'
assert PROFILE['hardware']['camera_model'] is None
assert sum(v for k, v in PROFILE['tracking_budget_ms'].items() if k != 'total') == 30
assert sum(PROFILE['accuracy_budget_mm'][k] for k in ('perception_including_detection_calibration_triangulation', 'prediction_and_timing', 'galvo_placement', 'reference_and_integration_reserve')) == 25

font_candidates = [
    (Path('C:/Windows/Fonts/arial.ttf'), Path('C:/Windows/Fonts/arialbd.ttf')),
    (Path(reportlab.__file__).parent / 'fonts/Vera.ttf', Path(reportlab.__file__).parent / 'fonts/VeraBd.ttf'),
]
font_pair = next((pair for pair in font_candidates if all(path.is_file() for path in pair)), None)
if font_pair is None:
    raise RuntimeError('Neither Arial nor the bundled ReportLab Vera fonts are available')
pdfmetrics.registerFont(TTFont('Body', str(font_pair[0])))
pdfmetrics.registerFont(TTFont('Bold', str(font_pair[1])))
pdfmetrics.registerFontFamily('Body', normal='Body', bold='Bold', italic='Body', boldItalic='Bold')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='B', fontName='Body', fontSize=9.2, leading=12.3, textColor=NAVY, spaceAfter=7))
styles.add(ParagraphStyle(name='SmallB', fontName='Body', fontSize=8.1, leading=10.6, textColor=GREY, spaceAfter=5))
styles.add(ParagraphStyle(name='H', fontName='Bold', fontSize=22, leading=26, textColor=NAVY, spaceAfter=13))
styles.add(ParagraphStyle(name='H2B', fontName='Bold', fontSize=11.5, leading=15, textColor=TEAL, spaceBefore=9, spaceAfter=6))
styles.add(ParagraphStyle(name='Cell', fontName='Body', fontSize=8.4, leading=11.2, textColor=NAVY))
styles.add(ParagraphStyle(name='CellHead', fontName='Bold', fontSize=8.4, leading=11.2, textColor=colors.white))
styles.add(ParagraphStyle(name='Card', fontName='Body', fontSize=8.8, leading=11.6, textColor=NAVY, spaceAfter=6))

def clean(value):
    return str(value).replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', '-').replace('\u2212', '-')

def para(text, style='B'):
    return Paragraph(clean(text), styles[style])

story = []
def p(text, style='B'):
    story.append(para(text, style))

def title(label, subtitle=None):
    p(label, 'H')
    if subtitle:
        p(subtitle)

def table(headers, rows, fractions=(0.36, 0.64), compact=False):
    data = [[para(escape(clean(v)), 'CellHead') for v in headers]]
    data += [[para(escape(clean(v)), 'Cell') for v in row] for row in rows]
    t = Table(data, colWidths=[WIDTH * v for v in fractions], hAlign='LEFT', repeatRows=1)
    padding = 4 if compact else 6
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), padding), ('BOTTOMPADDING', (0, 0), (-1, -1), padding),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, NAVY),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

def card(code, label, text):
    story.append(KeepTogether([para(f'{code}  |  {label}', 'H2B'), para(text, 'Card')]))

def page():
    story.append(PageBreak())

def setup_drawing():
    d = Drawing(WIDTH, 144)
    x, y, w = 190, 22, 105
    d.add(Rect(x, y, w, w, fillColor=LIGHT, strokeColor=TEAL, strokeWidth=1.4))
    d.add(Line(x, y+w, x+w, y+w, strokeColor=NAVY, strokeWidth=4))
    d.add(Line(x+w, y, x+w, y+w, strokeColor=NAVY, strokeWidth=4))
    d.add(Circle(x+w/2, y+w/2, 10, fillColor=colors.white, strokeColor=NAVY))
    d.add(String(x+w/2, y+w/2-3, 'ball', fontName='Body', fontSize=7, textAnchor='middle'))
    d.add(Rect(80, y+40, 57, 22, fillColor=TEAL, strokeColor=None))
    d.add(String(108, y+48, 'camera 0', fontName='Bold', fontSize=8, fillColor=colors.white, textAnchor='middle'))
    d.add(Line(138, y+51, x-4, y+51, strokeColor=TEAL))
    d.add(Rect(x+25, 0, 57, 17, fillColor=TEAL, strokeColor=None))
    d.add(String(x+53, 5, 'camera 1', fontName='Bold', fontSize=8, fillColor=colors.white, textAnchor='middle'))
    d.add(Line(x+53, 18, x+53, y-2, strokeColor=TEAL))
    d.add(Circle(x+80, y+65, 7, fillColor=AMBER, strokeColor=NAVY))
    d.add(String(320, y+70, 'camera 2 above, offset', fontName='Body', fontSize=8))
    d.add(Line(x+88, y+65, 314, y+70, strokeColor=GREY))
    d.add(Line(143, 130, x+45, y+60, strokeColor=colors.HexColor('#b94c3c'), strokeWidth=1.2))
    d.add(String(80, 132, 'galvo: upper-front', fontName='Body', fontSize=8, fillColor=NAVY))
    d.add(String(320, y+114, 'two grey far walls', fontName='Body', fontSize=8))
    d.add(String(320, y+100, 'grey floor underneath', fontName='Body', fontSize=8))
    d.add(String(320, y+18, 'top view, schematic', fontName='Body', fontSize=8, fillColor=GREY))
    return d

# 1 - current review status.
title('Voxel Camera with Laser Tracking', 'Milestone M2 - requirements and camera-team handoff')
p(DATE, 'H2B')
table(['Review state', 'Current position'], [
    ('GATE 1: PENDING', 'Team approval has not been recorded. This updated report is not an approval record.'),
    ('Source of truth', f'20-concept.md revision {REV}, VLT-CAM-1, camera-reference-plan.json and ADR-VLT-001 through ADR-VLT-022.'),
    ('Fixed hardware', 'Five Raspberry Pi 3 nodes: three camera, one control and one galvo node; dedicated wired Ethernet switch.'),
    ('Camera-team choices', 'Acquisition, exposure policy, calibration/data handoff, numeric timing limits, error budget and verification ownership are specified.'),
    ('Still pending', 'Camera model/driver binding and all real measurements. Galvo electrical verification (OQ-4) and global Gate 1 remain separate.'),
])
p('The demonstrator reconstructs a swinging ball in 3D and aims a galvo-steered laser at it. The cameras observe the ball and the physical spot, allowing measured aiming error and time-weighted hit scoring. Exactly two healthy cameras may continue in degraded mode.')
p('All new rates, tolerances and budgets are <b>selected qualification targets</b>. No camera, reference recording, hardware benchmark or completed acceptance result is invented. If the selected hardware cannot satisfy the profile under normal room light, qualification fails visibly.')
p('Changes since the 6 November report', 'H2B')
p('Automatic calibration replaces manual-first calibration. The physical setup and normal lighting are fixed. Startup and optional scans have separate budgets; shutdowns have explicit origins. F-VLT-42 bounds emission without a measurable effect. F-VLT-43/44 and NF-VLT-35 complete the camera-team profile and handoff. Raspberry Pi 3 remains fixed.')
p('Source convention: [L] refers to the 308-page lecture deck indexed in lecture-sources.md. Lecture references justify bounding and testing; the numeric values are project choices. Detailed product modules and synthesis remain after Gate 1.', 'SmallB')
page()

# 2 - physical setup, including the camera-profile refinement.
title('Reference installation', 'Chosen dimensions; as-built coordinates and optical performance still require measurement.')
story.append(setup_drawing())
table(['Element', 'Selected baseline'], [
    ('Clear tracking cube', '800 x 800 x 800 mm; right-handed frame, origin at marked floor corner; x/y along floor, z up.'),
    ('Ball / suspension', 'Matte white 50 mm sphere; rest centre (400,400,300) mm; 1000 mm pivot-to-centre length, pivot (400,400,1300).'),
    ('Motion envelope', 'Initial horizontal deflection >100 to 300 mm; speed <=1000 mm/s, acceleration <=4000 mm/s^2. Release without a push.'),
    ('Camera optical centres', '0: (-1200,400,1000); 1: (400,-1200,1000); 2: (700,400,2000) mm. All aim at (400,400,400).'),
    ('Field of view', 'At least 45 degrees in both image directions; whole cube and markers in frame. Elevated side views support oblique marker visibility.'),
    ('Floor / far walls', 'Matte neutral grey at z=0, x=800 and y=800; front sides and top remain open. Normal installed room lights; no extra tracking lamps or lighting extremes.'),
    ('Markers', '18 ArUco DICT_4X4_50 markers; coded square 140 mm plus 20 mm white margin, 180 mm total. At least four readable markers on each of two planes.'),
    ('Galvo / space', 'Nominal galvo (-1400,-1400,2200) mm. Reserve about 3 x 3 m floor space and 2.3 m height, cube base <=100 mm above floor.'),
], compact=True)
p('The 140 mm coded squares and elevated side centres supersede the earlier 80 mm markers / 400 mm side height. Marker IDs and centre coordinates remain in ADR-VLT-016; use measured corners with +/-70 mm nominal offsets. Scan grid u/v: {20,250,400,550,780} mm on each panel. Actual marker/spot visibility must pass qualification.', 'SmallB')
p('The galvo geometry still requires >=14.17 degrees usable optical half-angle including reserve; the bare DAC estimate is insufficient. Level matching, input type, supply and measured settling remain OQ-4. Grey panels alone are not a certification claim.', 'SmallB')
page()

# 3 - camera profile.
title('Camera-team acquisition profile', 'F-VLT-43 / ADR-VLT-020 - fixed targets; hardware-model selection is the remaining camera purchase decision.')
cp = PROFILE['capture']; im = PROFILE['image']
table(['Parameter', 'VLT-CAM-1'], [
    ('Image / platform', f"{im['width_px']} x {im['height_px']} px, rectified RGB8 plane; Raspberry Pi 3 remains fixed; compatible MIPI camera model not selected."),
    ('Rate / buffering', f"{cp['minimum_frame_rate_hz']}-{cp['maximum_frame_rate_hz']} captured observations/s; frame interval <= {cp['maximum_frame_period_ms']} ms. Keep one current complete frame; no growing FIFO."),
    ('Exposure', f"Initial {cp['exposure_default_us']} us; allowed {cp['exposure_min_us']}-{cp['exposure_max_us']} us. Analogue gain 1-8; digital gain 1."),
    ('Startup / locking', 'Auto exposure/gain/AWB for <=5 s, within <=10 s total camera calibration. White-ball luma target 160-220 / 255. Lock settings and fixed focus until restart.'),
    ('Lighting policy', 'Ordinary installed room lights, ordinary setting. If the bounds and contrast do not work, fail qualification; do not silently add lamps or lengthen exposure.'),
    ('Shutter / time', 'Global shutter allowed. Rolling shutter requires measured row timing and motion rectification to a common frame-midpoint image time; mapping error <=0.5 ms.'),
    ('Optical coverage', 'Ball diameter >=14 px; shortest coded-marker side >=12 px. At least four complete markers on each of two planes; calibration residual <=0.5 px.'),
    ('Missing metadata', 'No callback/arrival-time substitute for exposure. Missing or incompatible timing/calibration metadata leaves that camera unqualified/absent with a diagnostic.'),
], compact=True)
p('Sensor and actuator modules delivers the reproducible camera/driver/mode settings and capture/detection/calibration evidence. The concrete driver binding depends on the selected camera; no further numeric exposure policy is waiting to be chosen.')
p('Image coordinates use pixel centres: u right, v down, top-left origin; u=0..639, v=0..479. Ball centre/radius and spot coordinates are rectified to the same image time. Keep raw feature sample times for source-age checks.', 'SmallB')
p('Timing basis: [L] pp. 111-120, 266, 287-288. Profile values are selected targets, not lecture-prescribed values or measured camera specifications.', 'SmallB')
page()

# 4 - data handoff.
title('Observation and calibration handoff', 'F-VLT-1/2/17/23/24/44 - current data is bound to the geometry that produced it.')
table(['Contract', 'Defined behavior'], [
    ('Wire format', 'UDP unicast, UTF-8 JSON, schema version 1, <=1400 bytes per datagram. Finite numbers only; int64 ns timestamps are decimal strings on wire and range-checked.'),
    ('Observation identity', 'camera_id 0/1/2, sender session, frame_seq uint32, profile_id VLT-CAM-1, fixed setup_revision and per-camera calibration_id.'),
    ('Observation values', 't_exposure_ns for common rectified frame time; original t_ball_sample_ns / t_spot_sample_ns; ball {u,v,radius_px} or null; spot {u,v} or null; exposure/gain, clock offset and synchronized flag.'),
    ('CameraCalibration', 'Announce every 500 ms: camera/session/profile/setup/calibration IDs, K (9), five distortion coefficients, R (9), t_mm (3), fit residual and marker count/IDs. Same byte cap.'),
    ('Transform convention', 'Row-major K/R; camera axes right/down/forward. R maps camera into cube axes; t_mm is the optical origin in cube coordinates.'),
    ('Setup versus calibration', 'setup_revision hashes the fixed installation/profile/marker-map manifest. calibration_id hashes a camera/session/mode result. A camera restart alone does not invalidate all healthy peers.'),
    ('Adoption / restart', 'Validate calibration before accepting matching frames; discard unknown/retired-session or mismatched data. Keep tracking with the healthy pair while the third calibrates and rejoins.'),
    ('Ordering / buffering', 'No retransmission or late FIFO. Within session: newer iff 0 < uint32(n-last) < 2^31; equality is duplicate, half-range ambiguous/rejected. No restart can bypass re-arming rules.'),
], compact=True)
p('The machine-readable Observation and CameraCalibration JSON schemas accompany the requirements. Schema checks do not replace finite/range, identity, fit, row-time and temporal-validity checks. Calibration announcements are state data, not a remote operator command.')
p('Timestamp and restart tests include old-source packets, duplicates, reordering, image-mode swaps, unknown calibration, missing timing metadata and a camera reboot while the remaining pair tracks. Basis: [L] pp. 97-98, 137, 240.', 'SmallB')
page()

# 5 - numeric timing profile.
title('Timing and validity budget', 'F-VLT-22 / NF-VLT-18/24/33 / ADR-VLT-021')
budget_names = ['Capture/readout', 'Detection', 'Camera to control', 'Fusion wait incl. grid jitter', 'Fusion and prediction', 'Control to galvo', 'Output/DAC', 'Mirror settling', 'Reserve']
budget_values = [v for k,v in PROFILE['tracking_budget_ms'].items() if k != 'total']
table(['Tracking stage', 'Maximum allocation'], list(zip(budget_names, [f'{v} ms' for v in budget_values])) + [('TOTAL', '30 ms')], compact=True)
t = PROFILE['timing']
table(['Validity / scheduling', 'Limit'], [
    ('Fusion / placement', '10 ms shared-clock grid; existing +/-1 ms grid jitter; requested placement 5 ms after slot starts.'),
    ('Observation / pre-alignment skew', f"Age <={t['observation_max_age_ms']} ms; exposure skew <={t['exposure_skew_max_ms']} ms."),
    ('Prediction / oldest source at use', 'Each <=30 ms. Old current feature time, not new packet arrival, controls freshness.'),
    ('Target transport / expiry', 'Creation-to-receipt <=5 ms; exclusive expiry min(t_place+1 ms, oldest source+30 ms). At/after expiry discard.'),
    ('Clock / metadata', 'Pairwise <=1 ms; per node <=0.5 ms; g=2 ms, cross-node order claims only beyond +/-4 ms. Sync status <=100 ms old; publish at least every 50 ms.'),
    ('Future times / row mapping', 'Reject >2 ms into receiver future. Camera mapping error <=0.5 ms. Local timeouts progress monotonically.'),
    ('Output interpolation', '<=0.5 ms period; <=0.25 ms CPU execution. Other periodic bounds are in camera-profile.json.'),
], compact=True)
p('T1 is firm: end-to-end p99 <=30 ms, plus maxima and discarded-target counts. Per-stage measured high-water marks must fit this simultaneous budget. A source already 25 ms old cannot be used at a +5 ms placement that reaches its exclusive 30 ms expiry. All these are requirements to qualify, not timing results.', 'SmallB')
p('Basis: [L] pp. 36-40, 52-53, 65, 72, 92-120, 266, 287-288. Independent target measurements are required.', 'SmallB')
page()

# 6 - core behavior and joint accuracy.
title('Core behavior and combined accuracy', 'Selected requirements; complete numbered requirements remain in the concept document.')
card('F-VLT-1/2', 'Detect ball and physical spot', 'Ball centre within 3 px and radius within 2 px in >=95% of labelled ball frames, including spot-on-ball cases. Spot within 3 px in >=95%; >=99% of laser-off frames have no spot detection. Report not seen explicitly.')
card('F-VLT-3/4', 'Fuse and predict', 'At least two calibrated cameras, aligned by exposure time. Static position <=10 mm with all cameras and every pair. Perception p99 <=10 mm and prediction plus timing p99 <=8 mm. Prediction is generic, without a pendulum assumption; requested placement is slot+5 ms.')
card('F-VLT-5/6', 'Aim and measure the result', 'Nine known points within 5 mm; interpolation within 0.5 mm and first output within 1 ms of requested placement. Never apply expired targets. Error is ball-centre to beam-line distance: ray/sphere geometry for an on-ball spot, two-view triangulation off-ball, otherwise unmeasurable, never zero.')
card('F-VLT-7 / NF-VLT-1', 'Run and score', 'Release follows a >=0.5 s hold below 20 mm/s at >100 mm deflection, then motion toward rest above 100 mm/s. End below 50 mm amplitude over the last swing window. A hit is spot inside the ball image disc in at least one eligible view. Score by time on fixed fusion slots; missing/invalid/off slots are misses, a Safe-ended run is aborted. Require >=80% in three consecutive runs with all cameras and with each pair.')
table(['Contribution - NF-VLT-35', 'Allocation'], [
    ('Detection + calibration + triangulation', '<=10 mm p99 for valid reconstructed samples'),
    ('Prediction + timing', '<=8 mm p99'),
    ('Galvo placement', '<=5 mm p99'),
    ('Reference / integration reserve', '2 mm; nominal radius 25 mm'),
    ('Joint verification', 'Aiming error p95 <=23 mm; full-run >=80% hit test still required'),
], compact=True)
p('This intentionally tightens the earlier two-camera 15 mm and prediction median-10 / p95-20 mm allowances. Evaluate components on the same declared population; do not add independently measured percentiles as proof. Reference uncertainty must be <=2 mm and missing/unmeasurable cases remain explicit.', 'SmallB')
page()

# 7 - startup and calibration.
title('Startup, calibration and recovery', 'F-VLT-8/11/12/13/21/28/31/35/41 - explicit modes and budgets.')
table(['Phase / condition', 'Required outcome'], [
    ('Start', 'Laser-off preparation: configuration, shared time, camera warmup/calibration. <=60 s after the last of five node processes starts in the healthy reference test.'),
    ('Saved galvo calibration valid', 'Ready within 60 s. Ready is unarmed and does not wait for the ball; arming/check time is separate.'),
    ('Missing galvo calibration', 'Enter a separate Calibrating galvo mode. Each attempt <=60 s including laser-off and next-mode transition. Default at most two attempts.'),
    ('First / second attempt succeeds', 'Ready by <=120 / <=180 s from the same startup origin. Two failures: Safe and off by <=180 s; no third scan until restart.'),
    ('Camera calibration', '<=10 s including <=5 s exposure/AWB warmup; >=4 readable markers on each of >=2 planes; residual <=0.5 px; pose check every 1 s, >2 px change excludes camera.'),
    ('Galvo scan / check', 'Scan points dwell <=500 ms. Before every arming, three valid 3D check points, each within 5 mm and observed within 250 ms; whole check including failure-off <=1 s.'),
    ('Automatic arming', 'Kill switch released, no active/latched fault, valid setup, >=2 cameras seeing the ball for 2 s, passed check. The kill switch is the only physical operator control.'),
    ('Camera / ball loss', 'One camera can rejoin while two track. Ball loss turns laser off within 100 ms; return within 1 s can resume without re-arming if the required cameras are still present.'),
], compact=True)
p('Only Calibrating galvo, Arming check and armed Tracking may emit. Their deliberate emission does not violate laser-off in boot/Start. A kill switch or fault prevents readiness with diagnostics; healthy-start timing is not a promise to become ready while prerequisites fail.')
p('Alarms and repeated safety faults latch Safe; reset requires kill-switch press and release, then the normal arming checks. An optical timeout in scan/check fails that attempt instead of by itself setting the Tracking-alarm latch. Basis: [L] pp. 79, 162, 186, 240, 254.', 'SmallB')
page()

# 8 - shutdown transaction origins and missing effect.
title('Fault response and emission supervision', 'F-VLT-42 / NF-VLT-23/26/30/34 / ADR-VLT-018/019')
table(['Case / transaction', 'Origin, limit and outcome'], [
    ('T2 - missing target', 'From last fresh accepted target: physical off <=100 ms +10 ms. Invalid packets cannot refresh the timeout.'),
    ('T3 - immediately qualifying fault', 'From first valid exposure showing the condition, or local fault/expiry: <=100 ms off. Outside-cube spot >20 mm has no 500 ms persistence wait. The stated status-loss allowance remains <=110 ms.'),
    ('T6 - persistent aiming error', 'Error >50 mm for 500 ms, then off within <=100 ms: <=600 ms from first qualifying exposure. Fresh good measurement clears the episode; invalid data cannot count as good.'),
    ('T6 - no measurable effect', '500 ms watchdog from first laser-on placement or last accepted current effect update, then <=100 ms to off. Missing/one-view off-ball/invalid/stale evidence cannot refresh it.'),
    ('Tracking timeout outcome', 'Alarm and latched Safe. Clock steps, new targets and mode changes while on cannot extend the watchdog. At expiry the timeout wins over simultaneous/late data.'),
    ('Scan/check timeout outcome', 'Laser off, fail attempt/check and follow its bounded retry/scan policy. The faster point/check/scan deadline still applies; no ball is needed to triangulate calibration spots.'),
    ('T7 - output-loop hang', 'Watchdog reset and physical laser-disable within 1 s total from hang, including reset/disable delay; no added boot-time allowance.'),
    ('Converter coverage limitation', 'No electrical read-back. Qualifying optical effects use T3/T6. A fault without a qualifying observable effect has no promised electrical detection time; record it separately.'),
], compact=True)
p('Faster applicable shutdowns always take precedence. A confirmed laser-off ends its optical-watchdog episode. The independent physical kill switch removes laser supply. The selected laser remains Class 2; existing electrical isolation and lab procedure requirements continue. This report is not a certification.')
p('Coverage target: 10/10 timely detections/responses for each guaranteed injected case; residual/no-guaranteed-detector cases are reported separately, never counted as successful guaranteed detections. Independent instruments measure physical off and record electrical injection, evidence/watchdog origin and alarm times separately. Basis: [L] pp. 52-53, 167, 206-207, 254, 284.', 'SmallB')
page()

# 9 - concrete data and camera-team deliverables.
title('Reference package and qualification', 'NF-VLT-21/22/29/35 - camera-reference-plan.json fixes fixtures, reviews and ownership.')
table(['Work package', 'Defined evidence'], [
    ('Static reference', 'Ten listed positions: eight (100/700,100/700,100/700) corners, centre (400,400,400) and rest (400,400,300). >=80 frames per position/camera; independent coordinates uncertainty <=2 mm.'),
    ('Moving / negative cases', 'Three full reference swings at 150/225/300 mm deflection; >=80 frames/camera for no ball, laser off, spot off/on ball, occlusion and controlled outward carry/pause. Operators outside stored images.'),
    ('Labels / review', 'Lossless PNG, JSONL labels with centre/radius/spot or null, original times, laser state and run boundaries. Second review >=10% and >=100 frames/camera; adjudicate >1 px disagreements.'),
    ('Truth and uncertainty', 'Dynamic labels triangulated offline with independently static-validated calibration, separate from production detection/fusion; not an independent-sensor truth claim. Establish <=2 mm uncertainty. Synthetic trajectories provide exact reference truth.'),
    ('Storage / integrity', 'Explicit recording only, 64 MiB buffer/camera, full raw archive <=16 GiB. Overflow counts drops and invalidates the take without blocking Tracking. Repository: reviewed pack, labels, replay observations and SHA-256 manifest; bulk raw takes in bounded local archive.'),
    ('Loaded Pi 3 test', '10 minutes with monitoring off/on/paused; frame rate/periods, stage high-water times, T1 p99/max, CPU <=75% average and RAM <=50%, no backlog. Test all camera pairs and restart cases.'),
    ('Independent timing', 'At least 100 samples each for T1/T2/T3 and at least 10 injections per T6/T7 case, using separate timing stimulus/instrument and photodiode. Report self-measurement differences.'),
], compact=True)
table(['Owner role', 'Handoff'], [
    ('Sensor / actuator modules', 'Camera selection/settings, capture/detection/calibration, reference recording and real Pi 3 qualification.'),
    ('System design', 'Clock conversion, time-validity/latency integration and combined error budget.'),
    ('Integration support', 'Measured marker map, schema/manifest checks and repeatable replay.'),
    ('Requirements / product owner', 'Annotation/reference review, uncertainty evidence and acceptance.'),
], compact=True)
p('All recording and qualification evidence is pending actual hardware/setup. No synthetic image or invented measurement may be presented as a real pass. A failed profile or uncertain reference is reported as such. Basis: [L] pp. 264-266, 267-272, 279-284.', 'SmallB')
page()

# 10 - complete checklist and precise remaining scope.
title('DRS coverage and remaining work', 'The lecture checklist [L], PDF pages 287-288; requirements versus chosen design remain distinguishable.')
coverage = [
    ('1. End-to-end functions', 'F-1..7, F-43/44; NF-1/35'), ('2. Modes/configurations', 'F-28/33/35/41; ADR-017/019'),
    ('3. Node/network structure', 'NF-15/28; five Pi 3 nodes; ADR-001'), ('4. Interfaces', 'F-15/24/44; observation/calibration schemas; galvo OQ-4'),
    ('5. Messages/data', 'F-1/2/23/44; units, identities and null semantics'), ('6. Action timing/WCET', 'NF-33; selected periodic bounds in camera-profile.json'),
    ('7. Transaction deadlines/budgets', 'NF-18/26; ADR-018/021; 30 ms allocation'), ('8. Temporal accuracy', 'F-22; numeric ages/skew/horizon/expiry'),
    ('9. Shared time', 'NF-5/24; pairwise 1 ms, g=2 ms, mapping 0.5 ms'), ('10. Startup/restart/modes', 'F-13/17/28/41/44; 60/120/180 s phase bounds'),
    ('11. Resource limits', 'NF-8/19/27; CPU/RAM/link and bounded buffers'), ('12. Fault hypothesis', 'NF-23; guaranteed effects versus residual cases'),
    ('13. Load hypothesis', 'NF-27; 80-120 obs/s and 100 fusion slots/s'), ('14. Node failure modes', 'F-8/10/11/21/25; NF-30'),
    ('15. Detection coverage', 'NF-34; reaction matrix and timed fault injection'), ('16. Safety', 'NF-2/3/25; F-26/30/42; independent kill switch'),
    ('17. Security', 'NF-10/28; isolated switch, admin SSH, no loop command API'), ('18. Traceability', 'Numbered requirements, linked ADRs and verification package'),
]
table(['Checklist item', 'Coverage'], coverage, fractions=(0.42,0.58), compact=True)
p('Remaining decisions and measurements', 'H2B')
p('<b>Camera team:</b> select the compatible camera model and concrete driver binding, then build and measure the specified profile. Raspberry Pi 3 stays fixed; other camera-team policies are selected. <b>Other project work:</b> OQ-4 galvo electrical/range/settling facts, the full Gate 1 decision, and later product architecture/synthesis remain pending.', 'SmallB')
p('Sources: 20-concept.md rev '+REV+'; camera-profile.json; camera-reference-plan.json; two JSON schemas; ADR-VLT-001..022. [L] Distributed Real-Time Systems, WS26, 308 pages; lecture-sources.md provides the page/topic index. The earlier 12-page exercise source used in the 6 November report is not silently reused with new page numbers.', 'SmallB')

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.saved = []

    def showPage(self):
        self.saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        count = len(self.saved)
        for state in self.saved:
            self.__dict__.update(state)
            self.setStrokeColor(colors.HexColor('#d5dfe3'))
            self.line(42, 37, A4[0]-42, 37)
            self.setFillColor(GREY)
            self.setFont('Body', 7.5)
            self.drawString(42, 24, f'Voxel Camera | M2 | Gate 1 pending | concept rev {REV}')
            self.drawRightString(A4[0]-42, 24, f'{DATE} | {self._pageNumber} / {count}')
            super().showPage()
        super().save()

def header(canv, doc):
    canv.saveState()
    canv.setFont('Bold', 8)
    canv.setFillColor(TEAL)
    canv.drawString(42, A4[1]-31, 'VOXEL CAMERA')
    canv.setFont('Body', 7.5)
    canv.setFillColor(GREY)
    canv.drawRightString(A4[0]-42, A4[1]-31, 'M2 / REQUIREMENTS / CAMERA-TEAM PROFILE')
    canv.restoreState()

if OUT.exists() and not ORIGINAL.exists():
    ORIGINAL.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OUT, ORIGINAL)
OUT.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=42, leftMargin=42, topMargin=55, bottomMargin=48,
                        title='M2 Requirements - Voxel Camera - updated camera profile', author='Voxel Camera project',
                        subject=f'Requirements review draft, concept rev {REV}; Gate 1 pending; no measured results')
doc.build(story, onFirstPage=header, onLaterPages=header, canvasmaker=NumberedCanvas)
print(OUT)

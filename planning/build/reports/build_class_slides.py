#!/usr/bin/env python3
"""Two short slide decks (16:9 PDF) for the class presentation:

    output/pdf/Slides_Requirements_<team>.pdf    the most important requirements
    output/pdf/Slides_System_Design_<team>.pdf   the most important parts of the system design

Hand-picked summaries of ../VLT/20-concept.md (approved at Gate 1 and Gate 2); the
numbers are copied from the requirements and the architecture. Typst with the system
font Noto Sans (embedded into the PDF).

Usage (from the repository root):
    python3 planning/build/reports/build_class_slides.py
"""

import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_m2_report as m2  # noqa: E402
import build_m3_report as m3  # noqa: E402

TEAM = m2.TEAM
DATE = "19 November 2026"
OUT_DIR = m3.OUT_DIR
STAMP = "1795046400"  # 19 Nov 2026, fixed so the PDFs are reproducible

STYLE = r"""
#let navy = rgb("#16324f")
#let laser = rgb("#d1495b")
#let teal = rgb("#2a9d8f")
#let amber = rgb("#e9a23b")
#let soft = rgb("#eef2f7")
#let grey = rgb("#5b6b7d")
#set document(title: "__TITLE__", author: "__TEAM__")
#set text(font: ("Noto Sans", "Libertinus Serif"), size: 15pt, fill: rgb("#1d2733"))
#set par(leading: 0.55em)
#set page(width: 25.4cm, height: 14.29cm, margin: (x: 1.5cm, top: 1.3cm, bottom: 1.1cm),
  background: place(top + left, rect(width: 100%, height: 0.32cm, fill: navy)),
  footer: context {
    set text(8.5pt, fill: grey)
    [__TEAM__ · __DECK__]
    h(1fr)
    if counter(page).get().first() > 1 [#counter(page).display() / #counter(page).final().first()]
  })
#show strong: set text(fill: navy)

#let slide(kicker, title, body) = {
  pagebreak(weak: true)
  text(9.5pt, weight: "bold", fill: laser, tracking: 0.08em, upper(kicker))
  v(-0.35em)
  text(23pt, weight: "bold", fill: navy, title)
  v(0.45em)
  body
}
#let card(title, body, accent: teal) = rect(width: 100%, height: 100%, fill: soft, radius: 6pt,
  stroke: (left: 3.5pt + accent), inset: (x: 10pt, y: 9pt))[
  #text(15pt, weight: "bold", fill: navy, title) \
  #v(-0.1em)
  #text(12.5pt, body)]
#let stat(value, label, note, accent: navy) = rect(width: 100%, height: 100%, fill: soft, radius: 6pt, inset: 10pt)[
  #align(center)[
    #v(0.3em)
    #text(32pt, weight: "bold", fill: accent, value) \
    #text(13pt, weight: "bold", label) \
    #text(10pt, fill: grey, note)]]
#let tag(t) = box(fill: navy, radius: 3pt, inset: (x: 4pt, y: 2pt), text(8.5pt, fill: white, weight: "bold", t))
"""


def title_slide(title: str, sub: str) -> str:
    return f"""
#page(fill: navy, background: none, footer: none)[
  #set text(fill: white)
  #v(1fr)
  #text(11pt, weight: "bold", fill: laser, tracking: 0.1em)[DISTRIBUTED REAL-TIME SYSTEMS · WINTER TERM 2026]
  #v(0.2em)
  #text(34pt, weight: "bold")[{TEAM}]
  #v(-0.3em)
  #text(20pt)[{title}]
  #v(0.8em)
  #rect(width: 4cm, height: 3pt, fill: laser)
  #v(0.4em)
  #text(12pt, fill: rgb("#c9d6e3"))[{sub} \\ {DATE}]
  #v(1fr)
]
"""


# --------------------------------------------------------------------------- diagrams

def modes_svg() -> str:
    """Operating modes (F-VLT-41); the laser may be on only in the red ones."""
    W, H = 980, 330
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="Noto Sans, sans-serif" font-size="17">',
         '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0,0 L10,5 L0,10 z" fill="#16324f"/></marker></defs>']
    y, h = 110, 60
    boxes = [("START", 10, 140, False), ("CALIBRATING|GALVO", 200, 160, True), ("READY", 410, 140, False),
             ("ARMING|CHECK", 600, 150, True), ("TRACKING", 800, 160, True)]
    for name, x, w, on in boxes:
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{"#d1495b" if on else "#16324f"}"/>')
        lines = name.split("|")
        for i, ln in enumerate(lines):
            yy = y + h / 2 + 6 + (i - (len(lines) - 1) / 2) * 20
            s.append(f'<text x="{x + w / 2}" y="{yy}" text-anchor="middle" fill="white" font-weight="bold">{ln}</text>')
    s.append('<rect x="410" y="255" width="140" height="60" rx="12" fill="#16324f"/>'
             '<text x="480" y="291" text-anchor="middle" fill="white" font-weight="bold">SAFE</text>')

    def line(x1, y1, x2, y2):
        s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#16324f" stroke-width="2.2" marker-end="url(#a)"/>')
    line(150, 140, 198, 140)
    line(360, 140, 408, 140)
    line(550, 140, 598, 140)
    line(750, 140, 798, 140)
    # START -> READY when a galvo calibration is stored (over the top)
    s.append('<path d="M80,110 L80,55 L480,55 L480,106" fill="none" stroke="#16324f" stroke-width="2.2" marker-end="url(#a)"/>')
    s.append('<text x="280" y="45" text-anchor="middle" fill="#5b6b7d" font-size="15">galvo calibration already stored</text>')
    # faults -> SAFE
    s.append('<path d="M880,170 L880,285 L554,285" fill="none" stroke="#d1495b" stroke-width="2.2" marker-end="url(#a)"/>')
    s.append('<path d="M675,170 L675,285" fill="none" stroke="#d1495b" stroke-width="2.2"/>')
    s.append('<path d="M280,170 L280,285 L406,285" fill="none" stroke="#d1495b" stroke-width="2.2" marker-end="url(#a)"/>')
    s.append('<text x="770" y="275" text-anchor="middle" fill="#d1495b" font-size="15">any safety fault</text>')
    s.append('<text x="300" y="275" fill="#d1495b" font-size="15">scan fails</text>')
    # SAFE -> READY
    line(480, 253, 480, 174)
    s.append('<text x="490" y="225" fill="#5b6b7d" font-size="15">kill switch released, latch cleared</text>')
    s.append('<rect x="10" y="215" width="18" height="18" rx="3" fill="#d1495b"/>'
             '<text x="36" y="230" fill="#1d2733" font-size="15">laser may be on</text>')
    s.append('<rect x="10" y="245" width="18" height="18" rx="3" fill="#16324f"/>'
             '<text x="36" y="260" fill="#1d2733" font-size="15">laser off</text>')
    s.append("</svg>")
    return "\n".join(s)


def arch_svg() -> str:
    """Simplified node diagram with large labels for the slides."""
    W, H = 900, 430
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="Noto Sans, sans-serif" font-size="18">',
         '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0,0 L10,5 L0,10 z" fill="#16324f"/></marker></defs>']

    def box(x, y, w, h, title, sub, fill, fg="white", dash=False):
        d = ' stroke="#16324f" stroke-dasharray="6 4" stroke-width="2"' if dash else ""
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}"{d}/>')
        s.append(f'<text x="{x + w / 2}" y="{y + h / 2 - 2}" text-anchor="middle" fill="{fg}" font-weight="bold">{title}</text>')
        s.append(f'<text x="{x + w / 2}" y="{y + h / 2 + 20}" text-anchor="middle" fill="{fg}" font-size="14">{sub}</text>')

    def line(x1, y1, x2, y2, c="#16324f", w=2.5, dash=False, arrow=True):
        d = ' stroke-dasharray="6 4"' if dash else ""
        m = ' marker-end="url(#a)"' if arrow else ""
        s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{w}"{d}{m}/>')

    for i, y in enumerate((20, 140, 260)):
        box(10, y, 200, 80, f"Camera node {i}", "capture · detect", "#2a9d8f")
    box(340, 140, 170, 80, "Switch", "Ethernet · PTP", "#c9d1db", fg="#16324f")
    box(640, 20, 240, 80, "Control node", "fuse · predict · modes", "#16324f")
    box(640, 240, 240, 80, "Galvo node", "mirrors · laser guard", "#d1495b")
    box(340, 330, 170, 80, "Laptop", "monitoring only", "white", fg="#16324f", dash=True)
    for y in (60, 180, 300):
        line(210, y, 340, 180, arrow=False)
    line(510, 160, 640, 60, arrow=False)
    line(510, 200, 640, 280, arrow=False)
    line(425, 220, 425, 330, dash=True, arrow=False)
    s.append('<text x="218" y="48" fill="#2a9d8f" font-size="15" font-weight="bold">Observation</text>')
    s.append('<text x="585" y="128" fill="#16324f" font-size="15" font-weight="bold">Target</text>')
    s.append('<text x="505" y="262" fill="#d1495b" font-size="15" font-weight="bold">GalvoStatus</text>')
    s.append('<text x="435" y="290" fill="#5b6b7d" font-size="15">push only</text>')
    # actuators
    box(640, 350, 110, 64, "DAC", "I²S", "#eef2f7", fg="#16324f")
    box(770, 350, 110, 64, "Mirrors", "+ laser", "#eef2f7", fg="#16324f")
    line(695, 320, 695, 348)
    line(750, 382, 768, 382)
    s.append("</svg>")
    return "\n".join(s)


# --------------------------------------------------------------------------- deck 1: requirements

def requirements_deck() -> str:
    p = [STYLE.replace("__TITLE__", "Requirements").replace("__TEAM__", TEAM).replace("__DECK__", "Requirements")]
    p.append(title_slide("The most important requirements", "76 requirements · approved at Gate 1, updated at Gate 2"))
    p.append(r"""
#slide("Functions", "What the system must do")[
  #grid(columns: (1fr, 1fr, 1fr), rows: (3.75cm, 3.75cm), gutter: 0.45cm,
    card([See #h(1fr) #tag("F-VLT-1/2/43")], [Every camera detects ball and laser spot in *every frame*, at ≥ 80 fps, time-stamped in a shared clock.]),
    card([Locate #h(1fr) #tag("F-VLT-3")], [The control node fuses ≥ 2 cameras into the ball's *3D position*, every 10 ms.]),
    card([Predict #h(1fr) #tag("F-VLT-4")], [Aim where the ball *will be* when the spot lands, not where it was.]),
    card([Aim #h(1fr) #tag("F-VLT-5/9")], [The galvo node places the spot at the requested time and never aims outside the cube.], accent: laser),
    card([Measure itself #h(1fr) #tag("F-VLT-6/7")], [Aiming error from the spot the cameras see; *hit rate* per swing of the ball.], accent: laser),
    card([Calibrate itself #h(1fr) #tag("F-VLT-12/13/31")], [Cameras from frame markers at every start; galvo by an automatic scan; a 3-point check before each arming.], accent: laser),
  )
]

#slide("Performance", "How well it must work")[
  #grid(columns: (1fr, 1fr, 1fr), rows: (3.55cm, 3.55cm), gutter: 0.45cm,
    stat("≥ 80 %", "hit rate per run", "with 3 cameras and with every pair of 2 · NF-VLT-1", accent: laser),
    stat("≤ 45 ms", "ball moves → spot placed", "99th percentile · NF-VLT-18"),
    stat("≤ 10 mm", "3D position error", "resting ball, 2 or 3 cameras · F-VLT-3"),
    stat("≥ 80 fps", "per camera", "exposure time accurate to 0.5 ms · F-VLT-43"),
    stat("≤ 1 ms", "clock offset", "between any two nodes · NF-VLT-5"),
    stat("25 mm", "total error budget", "10 perception + 8 prediction + 5 galvo + 2 reserve · NF-VLT-35", accent: teal),
  )
  #v(0.2em)
  #align(center, text(11.5pt, fill: grey)[Operating envelope: release from 100–300 mm, ball speed ≤ 1 m/s, acceleration ≤ 4 m/s², normal room light.])
]

#slide("Safety", "The laser is never out of control")[
  #set text(11.5pt)
  #table(columns: (1.35fr, 1.6fr, 0.7fr, 0.75fr), stroke: none, inset: (x: 8pt, y: 5pt),
    fill: (_, y) => if y == 0 { navy } else if calc.odd(y) { soft } else { white },
    table.header(text(fill: white, weight: "bold")[Situation], text(fill: white, weight: "bold")[Reaction], text(fill: white, weight: "bold")[Deadline], text(fill: white, weight: "bold")[Req.]),
    [Kill switch pressed], [laser supply cut *in hardware*, independent of all software], [at once], [NF-VLT-3],
    [Not armed or no valid ball], [laser stays off (arming only by software rules)], [—], [F-VLT-8/35],
    [Control node silent], [galvo node switches the laser off by itself], [110 ms], [F-VLT-10],
    [Spot outside the cube], [laser off, alarm, safe state], [100 ms], [F-VLT-26],
    [Spot not on the ball (> 50 mm)], [laser off, alarm, safe state], [600 ms], [F-VLT-26],
    [Spot cannot be measured], [laser off — no light without feedback], [600 ms], [F-VLT-42],
    [Galvo software hangs], [laser guard, then hardware watchdog reset], [1 s], [NF-VLT-30],
  )
  #v(0.1em)
  #text(11.5pt, fill: grey)[Laser: visible red, 1 mW, Class 2 (NF-VLT-2). After a safety fault the laser stays off until the system arms again.]
]

#slide("Fault tolerance", "What may fail — and what happens then")[
  #grid(columns: (1fr, 1fr, 1fr), rows: (7.3cm,), gutter: 0.45cm,
    card([Tolerated #h(1fr) #tag("F-VLT-11")], [
      *One camera* may crash, go silent, restart or deliver wrong data.
      #v(0.3em)
      Tracking continues with *two cameras* (degraded mode), without re-arming; the camera rejoins after a restart.]),
    card([Fail-safe #h(1fr) #tag("NF-VLT-23")], [
      Control node, network switch, clock or galvo fail → the system detects it and goes to the *safe state: laser off*.
      #v(0.3em)
      Every fault in the hypothesis is injected ≥ 10 times on the real setup (NF-VLT-34).], accent: laser),
    card([Monitoring #h(1fr) #tag("NF-VLT-6/10")], [
      A laptop shows mode, images, health and delay statistics.
      #v(0.3em)
      It *only observes*: it can't command the system, and a slow or missing laptop never delays the loop.], accent: amber),
  )
]

#slide("Summary", "Requirements at a glance")[
  #grid(columns: (1fr, 1fr, 1fr, 1fr), rows: (3.9cm,), gutter: 0.45cm,
    stat("42", "functional", "what the system does"),
    stat("34", "non-functional", "timing, safety, quality"),
    stat("4", "real-time transactions", "tracking, shutdown, supervision, kill switch", accent: laser),
    stat("2", "approvals", "requirements 12 Nov · architecture 19 Nov", accent: teal),
  )
  #v(0.6em)
  #rect(fill: soft, radius: 6pt, inset: 14pt, width: 100%)[
    #set text(15pt)
    Every requirement has a *reason* (with lecture page), a *measurable acceptance test* and an *evidence mark*. Requirements say *what* must hold; the design follows in the architecture.]
]
""")
    return "".join(p)


# --------------------------------------------------------------------------- deck 2: system design

def design_deck() -> str:
    p = [STYLE.replace("__TITLE__", "System design").replace("__TEAM__", TEAM).replace("__DECK__", "System design")]
    p.append(title_slide("System design", "Architecture approved at Gate 2"))
    p.append(r"""
#slide("Architecture", "Five nodes, one switch, one clock")[
  #grid(columns: (1.9fr, 1fr), gutter: 0.6cm,
    align(center + horizon, image("architecture.svg", width: 100%)),
    [
      #set text(11.5pt)
      *3 camera nodes* — capture, detect ball and spot, send one observation per frame.
      #v(0.25em)
      *Control node* — fuses, predicts, decides the mode; clock master.
      #v(0.25em)
      *Galvo node* — drives the mirrors through an I²S DAC and switches the laser.
      #v(0.25em)
      *Laptop* — monitoring only, receives.
      #v(0.5em)
      #rect(fill: soft, radius: 6pt, inset: 8pt, width: 100%)[#text(11.5pt)[All Raspberry Pi 3 B+, Python 3, isolated 100 Mbit/s Ethernet, software PTP clock.]]
    ])
]

#slide("Real-time chain", "From ball movement to laser spot in ≤ 45 ms")[
  #let stage(w, c, top, bottom) = box(width: w * 1fr)[
    #rect(width: 100%, height: 1.5cm, fill: c, stroke: white + 1.5pt)[#align(center + horizon, text(15pt, fill: white, weight: "bold", top))]
    #align(center, text(10.5pt, fill: grey, bottom))]
  #v(0.2em)
  #grid(columns: (19fr, 4fr, 1.6fr, 11fr, 1.6fr, 1.6fr, 3fr, 1.6fr, 4fr), gutter: 0pt,
    stage(1, teal, [19], [wait for frame + readout]),
    stage(1, teal, [4], [detect]),
    stage(1, grey, [1], []),
    stage(1, navy, [11], [wait for fusion step]),
    stage(1, navy, [1], []),
    stage(1, grey, [1], []),
    stage(1, laser, [3], [galvo]),
    stage(1, laser, [1], []),
    stage(1, rgb("#c9d1db"), [4], [slack]),
  )
  #v(0.1em)
  #align(center, text(11.5pt, fill: grey)[worst case in ms · #text(fill: teal, weight: "bold")[camera] · #text(fill: grey, weight: "bold")[network] · #text(fill: navy, weight: "bold")[control] · #text(fill: laser, weight: "bold")[galvo] → *41 of 45 ms*])
  #v(0.6em)
  #grid(columns: (1fr, 1fr, 1fr), rows: (3.7cm,), gutter: 0.45cm,
    card([Free-running cameras], [≥ 80 fps each, no synchronised trigger; every frame carries its *exposure time* in the shared clock.]),
    card([Time-triggered fusion], [Every *10 ms* on the shared clock; only fresh observations count (age ≤ 25 ms).]),
    card([Prediction], [Constant-acceleration filter predicts the ball *45 ms ahead*; a target expires instead of arriving late.], accent: laser),
  )
]

#slide("Interfaces", "Small JSON messages over UDP")[
  #set text(12pt)
  #table(columns: (1.1fr, 1.3fr, 1fr, 2.2fr), stroke: none, inset: (x: 8pt, y: 7pt),
    fill: (_, y) => if y == 0 { navy } else if calc.odd(y) { soft } else { white },
    table.header(..([Message], [From → to], [Rate], [Content]).map(x => text(fill: white, weight: "bold", x))),
    [*Observation*], [camera → control], [per frame (≥ 80/s)], [ball and spot in the image, exposure time, sync state],
    [*CameraCalibration*], [camera → control], [every 500 ms], [lens and pose of the camera; frames count only after it is validated],
    [*Target*], [control → galvo], [every 10 ms], [aim point, placement time, expiry, laser request, arm epoch],
    [*GalvoStatus*], [galvo → control], [≥ every 50 ms], [applied target, laser on/off and why, kill switch],
    [*MonitorMessage*], [every node → laptop], [best effort], [status, health, events, images, delay records],
  )
  #v(0.2em)
  #text(11.5pt, fill: grey)[One JSON object per datagram (≤ 1400 B), schema version 1. *Newest wins:* no queues, no retransmission — an old message is dropped, never used late.]
]

#slide("Modes", "One owner decides when the laser may be on")[
  #align(center, image("modes.svg", height: 6.3cm))
  #v(0.1em)
  #text(13pt)[The *control node* owns the mode; the galvo node can only refuse (laser off) and never switches the laser on by itself. There is no arming button — the *kill switch* is the only physical control.]
]

#slide("Safety design", "Several independent ways to turn the laser off")[
  #let layer(n, c, title, body, time) = rect(width: 100%, fill: soft, radius: 5pt, inset: (x: 12pt, y: 7pt), stroke: (left: 4pt + c))[
    #grid(columns: (0.7cm, 1fr, 3.3cm), align: (left, left, right),
      text(17pt, weight: "bold", fill: c, n), [*#title* — #text(12pt, body)], text(13pt, weight: "bold", fill: c, time))]
  #set text(14pt)
  #stack(spacing: 0.2cm,
    layer("1", laser, "Kill switch", "cuts the laser supply in hardware", "at once"),
    layer("2", laser, "Laser guard", "own process on the galvo node; output loop must beat every 20 ms", "29 ms"),
    layer("3", amber, "Target timeout", "no fresh valid target for 100 ms → off", "110 ms"),
    layer("4", amber, "Effect supervision", "control node checks the spot the cameras see", "100 / 600 ms"),
    layer("5", navy, "Hardware watchdog", "on-chip; resets the galvo node if both processes hang", "1 s"),
  )
  #v(0.15em)
  #text(11.5pt, fill: grey)[Every reaction is a *fault reaction with a hard deadline*, measured on the bench with a logic analyzer (laser-enable line, trace pins).]
]

#slide("Building it", "Three teams, eight increments")[
  #grid(columns: (1fr, 1fr, 1fr), rows: (3.2cm,), gutter: 0.45cm,
    card([Camera team], [camera nodes: capture, detection, calibration, camera model, reference data]),
    card([Control team], [control node, monitoring laptop, shared package and message codec], accent: navy),
    card([Laser team], [galvo node, laser guard, galvo model, logic-analyzer bench], accent: laser),
  )
  #v(0.45em)
  #let inc(id, name, c) = rect(width: 100%, height: 1.6cm, fill: c, radius: 4pt, inset: 4pt)[#align(center + horizon, text(10pt, fill: white)[#text(14pt, weight: "bold")[#id] \ #name])]
  #grid(columns: (1fr,) * 8, gutter: 0.15cm,
    inc("S1", "skeleton, no hardware", navy), inc("S7", "monitoring", navy), inc("S2", "camera node", teal), inc("S3", "galvo node", laser),
    inc("S4", "calibration", teal), inc("S5", "modes, safety", laser), inc("S6", "aiming, scoring", navy), inc("S8", "acceptance", grey))
  #v(0.35em)
  #text(11.5pt)[*Open risks, checked on the bench first:* camera field of view at ≥ 80 fps (S2) · Python timing of detection and galvo output (S2/S3). Teams integrate against each other's *simulators* before the real nodes meet.]
]
""")
    return "".join(p)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = {"modes.svg": modes_svg(), "architecture.svg": arch_svg()}
    for name, svg in tmp.items():
        (OUT_DIR / name).write_text(svg, encoding="utf-8")
    rc = 0
    for stem, src in ((f"Slides_Requirements_{TEAM.replace(' ', '_')}", requirements_deck()),
                      (f"Slides_System_Design_{TEAM.replace(' ', '_')}", design_deck())):
        typ, pdf = OUT_DIR / f"{stem}.typ", OUT_DIR / f"{stem}.pdf"
        typ.write_text(src, encoding="utf-8")
        res = subprocess.run(["typst", "compile", "--creation-timestamp", STAMP, str(typ), str(pdf)])
        if res.returncode == 0:
            typ.unlink()
            print(pdf)
        rc |= res.returncode
    for name in tmp:
        (OUT_DIR / name).unlink()
    return rc


if __name__ == "__main__":
    sys.exit(main())

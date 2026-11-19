#!/usr/bin/env python3
"""Generate the M3 architecture and integration-test report (DRS_M3_<team>.pdf).

Sources: the architecture (§10–§12) and requirements (§3, §5) in ../VLT/20-concept.md
and the decision records in ../decisions/. Tables are taken from the concept so the
report cannot drift from it; text that only makes sense inside the repository
(section numbers, file names, revision markers) is removed. The architecture
diagram is written as SVG next to the Typst file. Typst runs with its embedded
fonts only, so the PDF looks the same on every machine.

Usage (from the repository root):
    python3 planning/build/reports/build_m3_report.py
"""

import pathlib
import re
import subprocess
import sys

sys.dont_write_bytecode = True  # no __pycache__ next to the generators
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_m2_report as m2  # noqa: E402  (shared Typst helpers)

TEAM = m2.TEAM
MILESTONE = "M3"
REPORT_DATE = "19 November 2026"
GATE2_STATE = "19 November 2026"  # "pending" or the date of the team's approval, e.g. "20 November 2026"

HERE = pathlib.Path(__file__).resolve().parent
BUILD = HERE.parent
CONCEPT = BUILD / "VLT" / "20-concept.md"
DECISIONS = BUILD / "decisions"
OUT_DIR = HERE / "output" / "pdf"
STEM = f"DRS_{MILESTONE}_{TEAM.replace(' ', '_')}"

esc, md, typ_str, section = m2.esc, m2.md, m2.typ_str, m2.section


def table_rows(block: str):
    """Markdown table rows without the header; keeps empty cells in place."""
    rows = []
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|") or re.match(r"^\|\s*-{3}", line):
            continue
        rows.append([x.strip() for x in line[1:-1].split("|")])
    return rows[1:]


# --------------------------------------------------------------------------- cleaning

def clean(s: str) -> str:
    """Remove repository-internal references so the report is self-contained."""
    s = re.sub(r"`?VLT/[\w.-]+\.json`?(?: \(to update\))?", "machine-readable schema", s)
    s = re.sub(r"\s*\((?:§\s?\d+(?:\.\d+)?(?:[–-]§?\d+(?:\.\d+)?)?(?:,\s*)?)+\)", "", s)
    s = re.sub(r"\s*\(rev \d+\)", "", s)
    s = re.sub(r",? rev \d+(?=\))", "", s)
    s = re.sub(r"\s*in rev \d+", "", s)
    s = re.sub(r"§10 and `[\w-]+\.schema\.json`", "the earlier message specification", s)
    s = re.sub(r"`[\w-]+\.schema\.json`", "the machine-readable schema", s)
    s = s.replace("§10", "the message specification")
    s = s.replace("the schema files are updated", "the machine-readable schemas are updated")
    s = re.sub(r"\s*\((?:11\.\d)\)", "", s)
    for ref, name in (("§11.1", "the message specification"), ("§11.2", "the transaction tables"),
                      ("§11.3", "the global time"), ("§11.4", "the integration tests"),
                      ("§11.5", "the reference installation"), ("§11.6", "the open bench checks"),
                      ("§11.7", "the debugging concept"), ("§11.8", "the team contracts")):
        s = s.replace(ref, name)
    s = s.replace("§11", "the architecture")
    s = re.sub(r"§\s?\d+(?:\.\d+)?", "", s)
    s = re.sub(r"\(\s*\)", "", s)
    s = re.sub(r"\(was U-VLT-\d+\)\s*", "", s)
    s = re.sub(r"recording tool \(test_tooling\.md\)", "recording tool", s)
    s = s.replace("[evidenced]", "(tested)").replace("[estimated]", "(estimate)")
    return s.strip()


def c(s: str) -> str:
    return "[" + md(clean(s)) + "]"


def tbl(cols: str, header: list, rows: list) -> str:
    out = [f"#table(columns: {cols}, table.header(" + ", ".join(f"[{h}]" for h in header) + "),"]
    out.append(",\n".join("  " + ", ".join(c(x) for x in r) for r in rows))
    return "\n".join(out) + ")\n"


# --------------------------------------------------------------------------- concept parsing

def sub_tables(block: str):
    """Split a block into (#### heading, body) pairs."""
    parts = re.split(r"^#### (.+)$", block, flags=re.M)
    return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts), 2)]


def first_para(block: str) -> str:
    return next((p.strip() for p in block.split("\n\n") if p.strip() and not p.strip().startswith("|")), "")


def modules(text: str):
    tree = section(text, "### Module overview & tree")
    code = tree.split("```")[1]
    node, out = None, []
    names = {"common/": "all nodes (shared)", "camera/": "camera node", "control/": "control node",
             "galvo/": "galvo node", "monitor/": "monitoring laptop", "sim/": "test tools",
             "bench/": "test bench (laptop)"}
    for line in code.splitlines():
        m = re.match(r"^  (\w+/)\s", line)
        if m:
            node = names.get(m.group(1))
            continue
        m = re.match(r"^    ([\w/]+\.py|dashboard/)\s+(\S.*?)\s{2,}(\S.*)$", line)
        if m and node:
            out.append((node, m.group(2).strip(), m.group(3).strip()))
    return out


def message_fields(text: str, name: str):
    block = text.split(f"**`{name}`**", 1)[1]
    rows = table_rows(block.split("\n\n**")[0])
    return [r for r in rows if "obsolete" not in r[2]]


def message_examples(text: str, name: str):
    """JSON examples of one message from the concept's message examples, as (note, json) pairs."""
    sec = text.split("#### Message examples (schema version 1)", 1)[1].split("\nOwner (role):", 1)[0]
    out = []
    for m in re.finditer(r"\*\*`(\w+)` example\*\*([^\n]*)\n\n```json\n(.*?)\n```", sec, re.S):
        if m.group(1) == name:
            out.append((m.group(2).strip(), m.group(3)))
    return out


def example_block(text: str, name: str) -> str:
    s = ""
    for note, js in message_examples(text, name):
        label = f"Example {note}:" if note else "Example:"
        s += "\n" + md(clean(label)) + "\n"
        s += "#block(width: 100%, fill: luma(245), inset: 6pt, radius: 2pt)[#set text(size: 7.4pt)\n```json\n" + js + "\n```\n]\n"
    return s


def monitor_kinds(text: str):
    """(kinds table rows, [(kind, sender, rows)]) from the MonitorMessage kinds and payloads."""
    sec = section(text, "#### MonitorMessage kinds and payloads")
    kinds = table_rows(sec.split("**Payload", 1)[0])
    payloads = []
    for m in re.finditer(r"^\*\*Payload `(\w+)` — ([^*]+)\*\*\n\n((?:\|.*\n?)+)", sec, re.M):
        payloads.append((m.group(1), m.group(2).strip(), table_rows(m.group(3))))
    return kinds, payloads


def monitor_block(text: str, senders=None) -> str:
    """Kinds table and the payload tables (only those of `senders` if given)."""
    kinds, payloads = monitor_kinds(text)
    status = first_para(section(text, "#### MonitorMessage kinds and payloads")).strip("_")
    s = "\n" + md(clean(status)) + "\n\n"
    s += tbl("(24mm, 24mm, 30mm, 1fr)", ["Kind", "Sent by", "When / rate", "Used for"], kinds)
    for kind, who, rows in payloads:
        if senders and not any(x in who for x in senders):
            continue
        s += "\n" + md(f"**Payload:** `{kind}` — {who}") + "\n\n"
        s += tbl("(38mm, 30mm, 1fr)", ["Field", "Type", "Meaning"], rows)
    return s


NODE_OF = {"camera": "camera nodes", "control": "control node", "galvo": "galvo node",
           "monitor": "monitoring laptop", "common": "all nodes", "sim": "test tools", "deploy": "all nodes"}


def trace_matrix(text: str):
    rows = table_rows(section(text, "### Requirement traceability matrix"))
    out = {}
    for r in rows:
        nodes = []
        for mod in re.findall(r"\b(camera|control|galvo|monitor|common|sim|deploy)/", r[1]):
            n = NODE_OF[mod]
            if n not in nodes:
                nodes.append(n)
        if not nodes and re.search(r"all (?:loop |detecting )?modules", r[1]):
            nodes = ["all nodes"]
        if not nodes:
            nodes = ["hardware / procedure"] if r[2] != "—" else ["—"]
        out[r[0]] = (r[1], ", ".join(nodes), r[2])
    return out


# requirement → transaction, fault reaction or mode activity (from the transaction tables)
TX = {
    "T1": "F-VLT-1 F-VLT-2 F-VLT-3 F-VLT-4 F-VLT-5 F-VLT-6 F-VLT-7 F-VLT-9 F-VLT-22 F-VLT-23 F-VLT-27 "
          "F-VLT-39 F-VLT-43 NF-VLT-1 NF-VLT-5 NF-VLT-17 NF-VLT-18 NF-VLT-24 NF-VLT-27 NF-VLT-32 NF-VLT-33 NF-VLT-35",
    "T3": "F-VLT-8 F-VLT-11 F-VLT-16 F-VLT-26",
    "T6": "F-VLT-26",
    "T8": "F-VLT-30 F-VLT-35 NF-VLT-3",
    "fault reaction: target loss": "F-VLT-10 F-VLT-21",
    "fault reaction: local galvo faults": "F-VLT-15 F-VLT-25 NF-VLT-16 NF-VLT-25",
    "fault reaction: galvo hang": "NF-VLT-30",
    "fault reaction: no measurable spot": "F-VLT-42",
    "fault reaction: camera data loss": "F-VLT-11 F-VLT-20 F-VLT-22",
    "mode activity: camera reintegration": "F-VLT-12 F-VLT-17 F-VLT-28 F-VLT-44",
    "mode activity: arming check": "F-VLT-31 F-VLT-24 F-VLT-35 F-VLT-41",
    "mode activity: galvo scan": "F-VLT-13 F-VLT-19",
    "all transactions": "NF-VLT-9 NF-VLT-19 NF-VLT-20 NF-VLT-26 NF-VLT-29",
    "all fault reactions": "NF-VLT-23 NF-VLT-34",
}

# requirement → integration test ID (IT-n, numbered in the order of the test table)
IT = {
    "F-VLT-1": [1], "F-VLT-2": [1], "F-VLT-3": [1], "F-VLT-4": [1], "F-VLT-5": [1], "F-VLT-22": [1, 3],
    "F-VLT-23": [1], "NF-VLT-18": [1], "NF-VLT-27": [1], "NF-VLT-33": [1], "F-VLT-39": [1], "NF-VLT-5": [3],
    "NF-VLT-24": [3], "F-VLT-11": [2, 4], "F-VLT-20": [3], "F-VLT-26": [4, 7], "F-VLT-16": [4], "F-VLT-8": [4, 6],
    "F-VLT-12": [5], "F-VLT-10": [6], "F-VLT-21": [6, 7], "F-VLT-15": [7, 9], "F-VLT-42": [8], "F-VLT-25": [9],
    "NF-VLT-25": [9, 10], "NF-VLT-30": [10], "NF-VLT-16": [11], "F-VLT-30": [11], "NF-VLT-3": [11],
    "F-VLT-35": [11, 12], "F-VLT-31": [12], "F-VLT-24": [12], "F-VLT-13": [13], "F-VLT-41": [11, 12, 13],
    "NF-VLT-26": list(range(1, 14)), "NF-VLT-29": [1, 4, 6, 7, 8, 9, 10, 11], "NF-VLT-23": list(range(2, 12)),
    "NF-VLT-34": list(range(2, 14)), "NF-VLT-9": [1], "NF-VLT-20": [3],
    "F-VLT-43": [1], "F-VLT-44": [2, 5], "NF-VLT-35": [1],
}


# message fields the design adds to the message specification (finding A-4)
EXTRA_FIELDS = {
    "Observation": [["`profile_id`, `calibration_id`", "string", "camera profile and validated calibration the frame was measured with"],
                    ["`t_ball_sample_ns`, `t_spot_sample_ns`", "int64 or null", "sample time of ball and spot from their image row (rolling shutter)"],
                    ["`exposure_us`, `analogue_gain`", "uint32, float32", "locked exposure settings"],
                    ["`t_readout_ns`, `t_detected_ns`, `t_sent_ns`", "int64", "stage timestamps for the chain statistics (F-VLT-39)"]],
    "Target": [["`t_created_ns`", "int64", "creation time at the control node; transport age ≤ 5 ms"],
               ["`purpose`", "enum", "TRACK, SCAN (galvo scan), CHECK (arming check) or IDLE (laser off)"]],
    "GalvoStatus": [["`synced`, `clock_offset_ns`", "bool, int64", "the galvo node's sync state (F-VLT-20)"]],
}


def tx_of(rid: str) -> str:
    hits = [k for k, v in TX.items() if rid in v.split()]
    return "; ".join(hits) if hits else "— (no real-time chain)"


# --------------------------------------------------------------------------- architecture diagram

def diagram_svg() -> str:
    W, H = 760, 470
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="Helvetica, Arial, sans-serif" font-size="11">',
         '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
         'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#222"/></marker></defs>',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="white"/>']

    def box(x, y, w, h, title, sub="", fill="#ffffff", dash=False, bold=True):
        d = ' stroke-dasharray="4 3"' if dash else ""
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="#222"{d}/>')
        ty = y + (h / 2 if not sub else h / 2 - 5) + 4
        s.append(f'<text x="{x + w / 2}" y="{ty}" text-anchor="middle" font-weight="{"bold" if bold else "normal"}">{title}</text>')
        if sub:
            for i, line in enumerate(sub.split("|")):
                s.append(f'<text x="{x + w / 2}" y="{ty + 13 + 12 * i}" text-anchor="middle" font-size="9.5" fill="#333">{line}</text>')

    def line(x1, y1, x2, y2, arrow=True, dash=False, label="", lx=None, ly=None, w=1.4):
        d = ' stroke-dasharray="5 3"' if dash else ""
        m = ' marker-end="url(#a)"' if arrow else ""
        s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#222" stroke-width="{w}"{d}{m}/>')
        if label:
            s.append(f'<text x="{lx if lx is not None else (x1 + x2) / 2 + 4}" y="{ly if ly is not None else (y1 + y2) / 2 - 3}" font-size="9.5" fill="#333">{label}</text>')

    # section labels
    s.append('<text x="10" y="18" font-weight="bold" font-size="12">Computer system</text>')
    s.append('<text x="10" y="392" font-weight="bold" font-size="12">Controlled object</text>')
    s.append(f'<line x1="0" y1="376" x2="{W}" y2="376" stroke="#999" stroke-dasharray="3 3"/>')

    # camera nodes
    for i, y in enumerate((40, 120, 200)):
        box(20, y, 150, 60, f"Camera node {i}", "Raspberry Pi 3 B+|camera process, pose check")
    # switch
    box(290, 110, 120, 80, "Ethernet switch", "100 Mbit/s, isolated|UDP state messages|PTP (software)", fill="#f2f2f2")
    for y in (70, 150, 230):
        line(170, y, 290, 150 + (y - 150) * 0.25, arrow=False, w=1.8)
    s.append('<text x="196" y="58" font-size="9.5" fill="#333">Observation, CameraCalibration</text>')
    # control node
    box(500, 40, 170, 60, "Control node", "Pi 3 B+ · PTP grandmaster|10 ms fusion step, modes")
    line(410, 135, 500, 75, arrow=False, w=1.8)
    s.append('<text x="414" y="124" font-size="9.5" fill="#333">Target ↓ · GalvoStatus ↑</text>')
    # galvo node
    box(500, 172, 170, 86, "Galvo node", "Pi 3 B+|output loop · laser guard|on-chip watchdog")
    line(410, 165, 500, 210, arrow=False, w=1.8)
    # laptop
    box(290, 260, 120, 50, "Monitoring laptop", "dashboard, push only", dash=True)
    line(350, 190, 350, 260, arrow=False, dash=True, w=1.4)
    s.append('<text x="356" y="232" font-size="9.5" fill="#333">MonitorMessage</text>')
    # DAC, driver
    box(500, 290, 80, 40, "PCM5102A DAC", "", fill="#f7f7f7", bold=False)
    box(600, 290, 80, 40, "Galvo driver", "±5 V X/Y", fill="#f7f7f7", bold=False)
    line(560, 258, 540, 290, label="I2S", lx=553, ly=278)
    line(580, 310, 600, 310)
    # laser path
    box(690, 180, 62, 70, "Laser", "supply|switch", fill="#f7f7f7", bold=False)
    line(670, 215, 690, 215, label="", )
    s.append('<text x="664" y="206" font-size="9" fill="#333">GPIO</text>')
    box(690, 100, 62, 50, "Kill", "switch", fill="#f7f7f7", bold=False)
    line(721, 150, 721, 180, label="cuts", lx=726, ly=170)
    line(690, 125, 670, 200, arrow=True, dash=True)
    s.append('<text x="676" y="160" font-size="9" fill="#333">sense</text>')

    # controlled object
    box(20, 405, 150, 50, "Cameras (sensors)", "IMX219, rolling shutter, ≥ 80 fps", fill="#eef3ff")
    box(300, 405, 150, 50, "Ball and laser spot", "800 mm cube, 1 m pendulum", fill="#eef3ff")
    box(560, 405, 160, 50, "Mirrors + laser (actuators)", "X/Y galvo, 650 nm 1 mW Class 2", fill="#eef3ff")
    line(640, 330, 640, 405)
    line(721, 250, 700, 405)
    line(560, 430, 450, 430, label="beam places the spot", lx=468, ly=424)
    line(300, 430, 170, 430, label="light", lx=220, ly=424)
    line(95, 405, 95, 262, arrow=True, w=1.2)
    s.append('<text x="100" y="330" font-size="9.5" fill="#333">CSI-2 (each camera to its node)</text>')
    s.append("</svg>")
    return "\n".join(s)


# --------------------------------------------------------------------------- report

PREAMBLE = m2.PREAMBLE.replace("__MS__ · Requirements", "__MS__ · Architecture and integration tests")


def build() -> str:
    text = CONCEPT.read_text(encoding="utf-8")
    arch = section(text, "## 11. Architecture & Vertical Slices")
    review = section(text, "## 12. Architecture Consistency Review")
    tx_block = section(text, "### 11.2 Transactions, fault reactions and mode activities")
    mods = modules(text)
    trace = trace_matrix(text)
    f_ids = [r[0] for r in table_rows(section(text, "## 3. Functional Requirements")) if re.fullmatch(r"F-VLT-\d+", r[0])]
    nf_ids = [r[0] for r in table_rows(section(text, "## 5. Non-Functional Requirements")) if re.fullmatch(r"NF-VLT-\d+", r[0])]
    req_text = {r[0]: r[1] for r in table_rows(section(text, "## 3. Functional Requirements")) + table_rows(section(text, "## 5. Non-Functional Requirements"))}

    p = []
    a = p.append
    a(PREAMBLE.replace("__TEAM__", TEAM).replace("__MS__", MILESTONE).replace("__DATE__", REPORT_DATE))
    gate_box = ("*Gate 2 — pending.* The consistency review is done (Section 7). The team's approval of the "
                "design is still outstanding; the proposed status of every finding is given in Section 7.1."
                if GATE2_STATE == "pending" else
                f"*Gate 2.* The consistency review is done and the team approved the design on {GATE2_STATE}.")
    a(f"""
#v(55mm)
#text(size: 26pt, weight: "bold")[{esc(TEAM)}]
#v(4mm)
#text(size: 15pt)[Milestone {MILESTONE} — Architecture, transactions and integration tests]
#v(10mm)
#text(size: 12pt)[Team: {esc(TEAM)} \\ Milestone: {MILESTONE} \\ Date: {REPORT_DATE}]
#v(25mm)
#block(width: 100%, inset: 8pt, stroke: 0.8pt)[{gate_box}]
#v(1fr)
#text(size: 8.5pt, fill: luma(70))[{esc(m2.LECTURE)} Requirement IDs (F-VLT-n, NF-VLT-n) refer to the requirements approved at Gate 1 (milestone M2) and amended by the transaction review of 17 November 2026 and by the change requests approved at Gate 2 on 19 November 2026; decision IDs are ADR-VLT-n. Owners are sub-team roles: camera team, control team, laser team.]
#pagebreak()
#outline(depth: 2, indent: auto)
#pagebreak()
""")

    # 1 overview & architecture
    a("= Architecture\n")
    a(md("Three camera nodes observe a ball swinging through an 800 mm cube and the laser spot on it. The control "
         "node fuses their observations into the ball's 3D position, predicts where the ball will be when the spot "
         "is placed, and commands the galvo node, which drives two galvo mirrors and switches the laser. The cameras "
         "see the spot as well, so the system measures its own aiming error (F-VLT-6). All five nodes are "
         "Raspberry Pi 3 Model B+ on one isolated 100 Mbit/s Ethernet switch (NF-VLT-15, NF-VLT-28) and share one "
         "software PTP clock (NF-VLT-5). The monitoring laptop only receives (NF-VLT-6, NF-VLT-10). All node "
         "software is Python 3 (ADR-VLT-023).") + "\n\n")
    a('#figure(image("architecture.svg", width: 100%), caption: [Nodes, network, sensors and actuators. '
      'Solid lines carry the real-time messages; dashed lines are monitoring and the kill-switch sense. '
      'The kill switch interrupts the laser supply in hardware (NF-VLT-3).])\n')
    a("\n== Nodes, sensors and actuators\n")
    a(tbl("(28mm, 1.2fr, 1.6fr, 1.2fr)", ["Node", "Hardware", "Software (processes)", "Sensors / actuators"], [
        ["Camera node ×3", "Raspberry Pi 3 Model B+, Camera Module v2.1 (Sony IMX219, rolling shutter) on CSI-2",
         "capture and detection loop (real-time priority, one core); pose check every 1 s (low priority); monitoring sender",
         "sensor: camera; observes ball, spot and frame markers (F-VLT-1, F-VLT-2, F-VLT-12)"],
        ["Control node", "Raspberry Pi 3 Model B+",
         "fusion loop every 10 ms (real-time priority): validity gate, triangulation, prediction, effect supervision, modes, targets; event log and recorder; PTP grandmaster",
         "none (decides; F-VLT-3, F-VLT-4, F-VLT-41)"],
        ["Galvo node", "Raspberry Pi 3 Model B+, PCM5102A I2S DAC, galvo driver and X/Y mirrors, laser supply switch, kill-switch sense",
         "output loop (0.5 ms blocks, ALSA) and laser guard (1 ms), both real-time; on-chip watchdog",
         "actuators: mirrors (F-VLT-5, F-VLT-15), laser on/off (NF-VLT-16); sensor: kill-switch sense (F-VLT-30)"],
        ["Monitoring laptop", "any laptop on the switch", "monitoring server and dashboard; receives only",
         "display for the operator (F-VLT-34, F-VLT-40)"],
        ["Ethernet switch", "dedicated, no uplink", "—", "network: UDP state messages, PTP (NF-VLT-28)"],
    ]))
    a("\n== Software modules\n")
    a(md("One module = one file = one class = one responsibility (NF-VLT-14). The shared package is used by every node, "
         "so the replay tests run exactly the code the nodes run (NF-VLT-22).") + "\n\n")
    a(tbl("(26mm, 30mm, 1fr)", ["Runs on", "Module", "Responsibility"], [[n, m_, d] for n, m_, d in mods]))
    a("\n== Operating modes\n")
    a(md("The control node owns the mode (F-VLT-41): Start → Calibrating galvo (F-VLT-13) → Ready → Arming check "
         "(F-VLT-31) → Tracking (normal with three cameras, degraded with two, F-VLT-11) → Safe (latched or not, "
         "F-VLT-21). Safe is left only through Ready. The laser may be on only in Arming check, Calibrating galvo and "
         "Tracking with a valid ball state (F-VLT-8). The galvo node keeps only an arming-epoch block: after any local "
         "safety fault, and for the first epoch of a new control-node session, it refuses to switch the laser on "
         "until a new arming (F-VLT-21, F-VLT-25).") + "\n")
    adr_rows = []
    for f in sorted(DECISIONS.glob("ADR-VLT-0*.md")):
        n = int(re.search(r"ADR-VLT-(\d+)", f.name).group(1))
        if n not in (8, 9, 11, 15, 16, 17, 18, 19, 20, 21, 22, 23):
            continue
        t = f.read_text(encoding="utf-8")
        ident, _, name = t.splitlines()[0].lstrip("# ").partition(" — ")
        status = re.search(r"^- \*\*Status:\*\* (.+)$", t, re.M).group(1).split(" · ")[0]
        amended = "amended 17 Nov 2026" if "## Amendment" in t else ""
        adr_rows.append([ident, name, status + (", " + amended if amended else "")])
    a("\n== Architecture decisions\n")
    a(md("Decisions the architecture rests on. \"Proposed\" decisions are decided by the team at Gate 2 (Section 8)."
         if GATE2_STATE == "pending" else
         f"Decisions the architecture rests on; the team accepted the camera-team decisions at Gate 2 on {GATE2_STATE}.") + "\n\n")
    a(tbl("(23mm, 1fr, 40mm)", ["ID", "Decision", "State"], adr_rows))

    # 2 transactions
    a("\n= Transactions\n")
    for para in [x.strip() for x in tx_block.split("####")[0].split("\n\n") if x.strip()]:
        if not para.startswith("_Rebuilt"):
            a(md(clean(para)) + "\n\n")
    for head, body in sub_tables(tx_block):
        rows = table_rows(body)
        a(f"\n== {md(clean(head))}\n")
        intro = [x.strip() for x in body.split("\n\n") if x.strip() and not x.strip().startswith("|")]
        if head.startswith("T"):
            owner = "Owner (role): system design."
            a(md(owner) + "\n\n")
            if intro and not intro[0].startswith("Derivation"):
                a(md(clean(intro[0])) + "\n\n")
            a("#block[#set text(size: 7.6pt)\n")
            a(tbl("(4mm, 19mm, 24mm, 1.7fr, 14mm, 13mm, 17mm, 1.1fr, 0.9fr)",
                  ["\\#", "Stage", "Node / element", "What happens", "Period", "WCET", "Worst case", "Error handling", "Check"],
                  rows))
            a("]\n")
            for x in intro[1:] if not (intro and intro[0].startswith("Derivation")) else intro:
                a("\n" + md(clean(x)) + "\n")
        elif head.startswith("Fault"):
            a(tbl("(20mm, 1fr, 1fr, 0.9fr, 0.9fr, 0.9fr, 21mm)",
                  ["Fault reaction", "Origin", "Detection", "Reaction", "Worst case", "Deadline (class)", "Requirement"], rows))
        elif head.startswith("Mode"):
            a(tbl("(24mm, 1fr, 1.6fr, 16mm, 22mm)", ["Mode activity", "Start → end", "Composition", "Worst case", "Limit"], rows))
        else:
            a(md(clean(body.strip())) + "\n")
    slices = table_rows(section(text, "### Vertical slices"))
    a("\n== Build increments\n")
    a(md("The checks above name the build increment (S1 … S8) in which a stage is first measured. Each increment "
         "delivers named requirements end to end; the first proves the tracking chain without hardware.") + "\n\n")
    a(tbl("(9mm, 30mm, 1fr)", ["ID", "Increment", "Acceptance"], [[r[0], r[1], r[4]] for r in slices]))

    # 3 global time
    a("\n= Global time\n")
    gt = section(text, "### 11.3 Global time")
    a("\n".join("- " + md(clean(x)) for x in re.findall(r"^- (.+)$", gt, re.M)) + "\n")
    a("- " + md("**Synchronization.** Software PTP (IEEE 1588 over UDP, kernel software timestamping, ADR-VLT-002); "
                "the control node is the grandmaster. Each node polls its offset every 20 ms; a node counts as synchronized "
                "only while |offset| ≤ 0.5 ms and its sync status is younger than 100 ms (F-VLT-20, F-VLT-22). No other "
                "time service runs (NF-VLT-28).") + "\n")
    a("- " + md("**Local timeouts** (target timeout, optical-effect watchdog, kill-switch debounce) use each node's raw "
                "monotonic clock, which clock corrections never adjust (F-VLT-10, F-VLT-22, F-VLT-42).") + "\n")
    a("- " + md("**Requirements:** NF-VLT-5 (π ≤ 1 ms), NF-VLT-24 (π/2 per node, g > π, ±2g), NF-VLT-20 (holds under "
                "maximum monitoring load), F-VLT-18 (offsets reported and shown).") + "\n")

    # 4 interfaces and messages
    a("\n= Interfaces and messages\n")
    i11 = table_rows(section(text, "### 11.1 Interfaces and messages — camera handoff (ADR-VLT-020)"))
    a("== Transport and message rules\n")
    a(md("All messages between the nodes (camera, control, galvo, monitoring) are JSON: one UTF-8 JSON object per UDP "
         "datagram. The only non-JSON traffic between the nodes is the PTP time synchronisation (F-VLT-23).") + "\n\n")
    a(tbl("(32mm, 1fr)", ["Item", "Rule"], [[r[0], r[1]] for r in i11]))
    env = table_rows(text.split("`Observation` and `Target` both carry:", 1)[1].split("\n\n**")[0])
    a("\n== Common fields\n")
    a(md("Every Observation, Target and GalvoStatus carries these fields; receivers reject a message whose version, "
         "sender session order or setup does not match (F-VLT-23, F-VLT-24). Of these, a MonitorMessage carries only `type` and "
         "`schema_version`.") + "\n\n")
    a(tbl("(32mm, 18mm, 1fr)", ["Field", "Type", "Meaning"], env))
    for name, direction in (("Observation", "camera node → control node, UDP, one per frame"),
                            ("Target", "control node → galvo node, UDP, one per fusion step (10 ms), in every mode"),
                            ("GalvoStatus", "galvo node → control node, UDP, with each newly applied target and at least every 50 ms"),
                            ("MonitorMessage", "every node → monitoring laptop, UDP, best effort; events at once, status ≤ 20 Hz, images ≤ 5/s, diagnostics summary every 1 s")):
        a(f"\n== {name}\n")
        a(md(direction) + "\n\n")
        a(tbl("(38mm, 26mm, 1fr)", ["Field", "Type", "Range / meaning"], message_fields(text, name) + EXTRA_FIELDS.get(name, [])))
        if name == "MonitorMessage":
            a(monitor_block(text))
        a(example_block(text, name))
    a("\n== CameraCalibration\n")
    a(md("camera node → control node, UDP state message every 500 ms: camera, session, profile, setup and calibration "
         "IDs; intrinsic matrix K (9 values), distortion (k1, k2, p1, p2, k3), rotation (9), translation (3, mm), "
         "reprojection residual (px), marker count and IDs. The control node uses a camera's frames only after the "
         "matching calibration is validated (F-VLT-12, F-VLT-24).") + "\n")
    a(example_block(text, "CameraCalibration"))
    hw = table_rows(section(text, "## 6. Integration Points"))
    a("\n== Hardware interfaces\n")
    a(tbl("(34mm, 18mm, 1fr, 26mm)", ["Component", "Direction", "Contract", "Owner (role)"], [r[:4] for r in hw]))
    a("\n== Interfaces inside a node\n")
    inner = [r for r in table_rows(section(text, "### Inter-module interfaces")) if "UDP" not in r[2]]
    a(tbl("(28mm, 32mm, 1fr, 1fr)", ["From", "To", "Call / message", "Errors"], [[r[0], r[1], r[2], r[4]] for r in inner]))

    # 5 integration tests
    a("\n= Integration test specification\n")
    it = section(text, "### 11.4 Integration tests")
    a(md(clean(first_para(it))) + "\n\n")
    it_rows = table_rows(it)
    a(tbl("(9mm, 24mm, 1fr, 1.4fr)", ["ID", "Transaction / reaction", "End-to-end measurement on the hardware", "Faults injected (fault hypothesis NF-VLT-23)"],
          [[f"IT-{i}"] + r for i, r in enumerate(it_rows, 1)]))
    tail = [x.strip() for x in it.split("\n\n") if x.strip().startswith("Accuracy")]
    if tail:
        a("\n" + md(clean(tail[0])) + "\n")
    a("\n" + md("**Instruments.** The end-to-end durations are measured independently of the node clocks (NF-VLT-29): a "
                "logic analyzer records a GPIO trace pin of every node, the laser-enable line and the kill-switch contact. "
                "It covers the electrical part of each chain; there is no optical stimulus or sensor, so the input stage "
                "and the physical output (mirror settling, laser switch-off) are taken from the node timestamps and the "
                "stage budgets. "
                "Each node also logs its per-stage timestamps, so every stage is checked against its budget (NF-VLT-18, "
                "NF-VLT-33). Fault injection uses cable pulls, SIGSTOP, clock steps, a second laser pointer, blocked "
                "mirrors and calibration offsets as listed.") + "\n")

    # 6 traceability
    a("\n= Traceability\n")
    a(md("Every requirement (approved at Gate 1, amended at Gate 2) with the transaction (or fault reaction, mode activity) that carries it, the "
         "nodes that implement it, and the test that checks it. IT-n are the integration tests of Section 5; "
         "\"acceptance Sn\" is the requirement's own acceptance criterion, checked when build increment Sn is "
         "finished.") + "\n\n")
    rows = []
    for rid in f_ids + nf_ids:
        txt = req_text[rid]
        if re.match(r"(deferred|dropped)", txt):
            rows.append([rid, "— (" + txt.split(" ")[0] + ")", "—", "—"])
            continue
        mod, nodes, sl = trace.get(rid, ("", "—", "—"))
        tests = ", ".join(f"IT-{i}" for i in IT.get(rid, []))
        acc = f"acceptance {sl}" if sl not in ("—", "") else ""
        rows.append([rid, tx_of(rid), nodes, ", ".join(x for x in (tests, acc) if x) or "inspection"])
    a(tbl("(22mm, 1.3fr, 1fr, 1fr)", ["Requirement", "Transaction", "Node(s)", "Test"], rows))

    # 7 consistency review
    a("\n= Consistency review\n")
    a(md("Every requirement whose fulfilment spans several modules or nodes was traced end to end with the "
         "architecture consistency checklist (data elements, interfaces, state machine, timing budgets, global time, "
         "message semantics, fault hypothesis, ground state). OK = both ends agree; MISMATCH = they disagree; "
         "DANGLING = a value, endpoint or budget contributor is missing or not yet measured.") + "\n\n")
    mat = table_rows(section(review, "### Cross-module consistency matrix"))
    a(tbl("(22mm, 40mm, 19mm, 1fr)", ["Requirement", "Element", "Verdict", "Note"], [[r[0], r[1], r[4], r[5]] for r in mat]))
    a("\n== Findings\n")
    a(md("Each finding with its proposed status. **The team's Gate 2 decision on these statuses is pending.**" if GATE2_STATE == "pending"
         else "Each finding with the status decided at Gate 2.") + "\n\n")
    findings = [
        ["A-1", "Target expiry of one ms after placement left the galvo without a valid target for 9 of every 10 ms (F-VLT-5, F-VLT-22, NF-VLT-18).",
         "accepted", "Expiry = min(t_place + fusion period + g, oldest source + 45 ms); prediction horizon ≤ 45 ms; prediction error at 45 ms shown in S1."],
        ["A-2", "The on-chip watchdog backstop for a galvo hang has no reserve: its minimum timeout of 1 s equals the deadline (NF-VLT-30).",
         "accepted", "The laser guard switches the laser off ≈ 29 ms after an output-loop stall; the watchdog only covers a stall of the laser guard or the kernel."],
        ["A-3", "The laser switch-off delay (supply switch and laser decay) is not measured; it sets the 8 ms output stage and F-VLT-16's action-delay window. Target loss has only 0.5 ms slack.",
         "accepted", "Estimated from the datasheets of the supply switch and the laser module (default 8 ms); there is no optical measurement."],
        ["A-4", "Message fields needed by the design were missing (stage timestamps, purpose, session, setup, sync state) (F-VLT-23, F-VLT-24, F-VLT-39).",
         "accepted", "Added to the message specification (Section 4); the machine-readable schema is updated before S1."],
        ["A-5", "No camera mode is confirmed that gives both the field of view of the layout and ≥ 80 fps (risk R-1, NF-VLT-18, NF-VLT-32).",
         "open", "Bench measurement in S2; the T1 input stage is unverified until then, and S2 is accepted only with the measurement."],
        ["A-6", "Python timing of camera detection (4 ms) and the galvo output blocks is unverified (risk R-2, NF-VLT-18, NF-VLT-19).",
         "open", "Bench measurement in S2 and S3; levers: region of interest, frame rate, larger output buffer."],
        ["A-7", "A laptop that connects late could not show the diagnostics since node start (F-VLT-40).",
         "fixed", "Every node resends a bounded diagnostics summary every 1 s."],
        ["A-8", "The overlay in the camera images lagged by up to ≈ 35 mm of ball motion (F-VLT-38).",
         "fixed", "The monitoring server draws the control state closest to each image's exposure time."],
        ["CR", "Requirement change requests from the camera-team groundwork (ADR-VLT-017 start-up budgets; ADR-VLT-020 camera profile; ADR-VLT-021 validity limits; ADR-VLT-022 error budget).",
         "approved", "Applied to the requirements: F-VLT-3, F-VLT-4, F-VLT-8, F-VLT-12, F-VLT-13, F-VLT-22, F-VLT-28, F-VLT-31, F-VLT-41 changed; F-VLT-43 (camera acquisition), F-VLT-44 (calibration handoff), NF-VLT-35 (combined error budget) new (Section 8)."],
        ["OQ", "Open questions OQ-3 (cube 800 mm), OQ-4 (galvo facts), OQ-7 (white ball, grey background), OQ-12 (validity limits), OQ-14 (error budget).",
         "accepted", "Proposals accepted and the questions closed; OQ-4 values are confirmed on the bench in S3."],
    ]
    a(tbl("(10mm, 1.4fr, 16mm, 1.2fr)", ["ID", "Finding", "Proposed status" if GATE2_STATE == "pending" else "Status", "Action / reason"], findings))

    # 8 gate 2
    a("\n= Gate 2\n")
    if GATE2_STATE == "pending":
        a(md("The consistency review is done: the matrix in Section 7 covers every requirement that spans modules or "
             "nodes, and every finding has a proposed status. **The team's approval of the design is pending.** Gate 2 "
             "is passed when the team approves the design with the statuses of Section 7.1 (or changed ones). "
             "Milestone M3 is reached when this report and the report \"Mx – Integration Test Debugging Concept\" are "
             "both accepted.") + "\n")
    else:
        a(md(f"The consistency review is done and the team approved the design on {GATE2_STATE}, with the statuses of "
             "Section 7.1: A-1 to A-4 accepted as proposed; A-5 (camera mode, risk R-1) and A-6 (Python timing, risk R-2) "
             "stay open until the bench measurements of build increments S2 and S3; open questions OQ-3, OQ-4, OQ-7, OQ-12 "
             "and OQ-14 closed with their proposals; the camera-team decisions ADR-VLT-016 to ADR-VLT-022 accepted.") + "\n\n")
        a(md("The team also approved the requirement change requests of the camera-team groundwork. They change "
             "requirements approved at Gate 1:") + "\n\n")
        changed = ["F-VLT-3", "F-VLT-4", "F-VLT-8", "F-VLT-12", "F-VLT-13", "F-VLT-22", "F-VLT-28", "F-VLT-31", "F-VLT-41"]
        new = ["F-VLT-43", "F-VLT-44", "NF-VLT-35"]
        cr_note = {
            "F-VLT-3": "two cameras: 15 mm → 10 mm", "F-VLT-4": "10 mm median / 20 mm p95 → 8 mm p99",
            "F-VLT-8": "no emission at boot and in Start", "F-VLT-12": "≥ 4 markers on ≥ 2 planes, ≤ 5 s exposure settling, pose check ≥ every 1 s",
            "F-VLT-13": "≤ 60 s per scan attempt incl. laser off and transition", "F-VLT-22": "numeric validity limits",
            "F-VLT-28": "separate budgets: Start ≤ 60 s, each scan attempt ≤ 60 s", "F-VLT-31": "each check point within 250 ms",
            "F-VLT-41": "Start defined as laser-off preparation", "F-VLT-43": "new", "F-VLT-44": "new", "NF-VLT-35": "new",
        }
        a(tbl("(24mm, 34mm, 1fr)", ["Requirement", "Change", "Requirement text (as approved at Gate 2)"],
              [[rid, cr_note[rid], req_text[rid]] for rid in changed + new]))
        a("\n" + md("Milestone M3 is reached when this report and the report \"Mx – Integration Test Debugging Concept\" "
                    "are both accepted.") + "\n")
    return "".join(p)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    typ = OUT_DIR / f"{STEM}.typ"
    svg = OUT_DIR / "architecture.svg"
    svg.write_text(diagram_svg(), encoding="utf-8")
    typ.write_text(build(), encoding="utf-8")
    pdf = OUT_DIR / f"{STEM}.pdf"
    res = subprocess.run(["typst", "compile", "--ignore-system-fonts",
                          "--creation-timestamp", "1795046400", str(typ), str(pdf)])
    if res.returncode == 0:
        typ.unlink()
        svg.unlink()
        print(pdf)
    return res.returncode


if __name__ == "__main__":
    sys.exit(main())

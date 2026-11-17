#!/usr/bin/env python3
"""Generate the M3 integration-test debugging concept (DRS_M3_<team>_Debugging.pdf).

Source: the debugging concept (architecture section "Integration test debugging (M3)"),
the vertical slices and the transaction deadlines in ../VLT/20-concept.md. Tables are
taken from the concept so the report cannot drift from it; repository-internal
references are removed with the cleaning rules of the M3 architecture report. The
test-bench diagram is written as SVG next to the Typst file. Typst runs with its
embedded fonts only.

Usage (from the repository root):
    python3 planning/build/reports/build_m3_debug_report.py
"""

import pathlib
import re
import subprocess
import sys

sys.dont_write_bytecode = True  # no __pycache__ next to the generators
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_m2_report as m2  # noqa: E402
import build_m3_report as m3  # noqa: E402

TEAM = m2.TEAM
MILESTONE = "M3"
REPORT_DATE = "17 November 2026"

HERE = pathlib.Path(__file__).resolve().parent
CONCEPT = HERE.parent / "VLT" / "20-concept.md"
OUT_DIR = HERE / "output" / "pdf"
STEM = f"DRS_{MILESTONE}_{TEAM.replace(' ', '_')}_Debugging"

esc, md, section = m2.esc, m2.md, m2.section
table_rows, clean, tbl = m3.table_rows, m3.clean, m3.tbl

PREAMBLE = m2.PREAMBLE.replace("__MS__ · Requirements", "__MS__ · Integration test debugging concept")

SEC = "### 11.7 Integration test debugging (M3)"


def tables(block: str):
    """All markdown tables of a block, in order, as row lists (header removed)."""
    out, cur = [], []
    for line in block.splitlines() + [""]:
        if line.strip().startswith("|"):
            cur.append(line)
        elif cur:
            out.append(table_rows("\n".join(cur)))
            cur = []
    return out


def para(block: str, lead: str) -> str:
    """The paragraph that starts with the bold lead-in `lead`, lead-in removed."""
    for p in block.split("\n\n"):
        p = p.strip()
        if p.startswith(f"**{lead}**"):
            return p[len(lead) + 4:].strip()
    raise KeyError(lead)


def after(block: str, lead: str) -> str:
    """Text from the paragraph `lead` up to the next bold lead-in paragraph (lists included)."""
    start = block.index(f"**{lead}**")
    m = re.search(r"\n\n\*\*[A-Z][^*]+\.\*\*", block[start + 2:])
    return block[start:start + 2 + m.start()] if m else block[start:]


def bullets(text: str) -> list:
    return [l[2:].strip() for l in text.splitlines() if l.startswith("- ")]


def numbered(text: str) -> list:
    return [re.sub(r"^\d+\.\s*", "", l).strip() for l in text.splitlines() if re.match(r"^\d+\.\s", l)]


def p_(s: str) -> str:
    return m3.md(clean(s)) + "\n\n"


def bench_svg() -> str:
    W, H = 640, 330
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="Helvetica, Arial, sans-serif" font-size="11">',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="white"/>']

    def box(x, y, w, h, title, sub="", fill="#ffffff", dash=False):
        d = ' stroke-dasharray="4 3"' if dash else ""
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="#222"{d}/>')
        ty = y + (h / 2 if not sub else h / 2 - 5) + 4
        s.append(f'<text x="{x + w / 2}" y="{ty}" text-anchor="middle" font-weight="bold">{title}</text>')
        for i, ln in enumerate(sub.split("|") if sub else []):
            s.append(f'<text x="{x + w / 2}" y="{ty + 13 + 12 * i}" text-anchor="middle" font-size="9.5" fill="#333">{ln}</text>')

    def ln(x1, y1, x2, y2, dash=False, w=1.6, color="#222"):
        d = ' stroke-dasharray="5 3"' if dash else ""
        s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}"{d}/>')

    def txt(x, y, t, size=9.5, anchor="start", color="#333"):
        s.append(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{color}">{t}</text>')

    # nodes
    for i, y in enumerate((20, 80, 140)):
        box(20, y, 130, 46, f"Camera node {i}", "trace pin")
    box(20, 210, 130, 46, "Control node", "trace pin · PTP master")
    box(20, 270, 130, 46, "Galvo node", "trace pin · laser enable")
    # switch
    box(250, 112, 110, 86, "Ethernet switch", "isolated|loop msgs, PTP|mirror stream", fill="#f2f2f2")
    for y in (43, 103, 163, 233, 293):
        ln(150, y, 250, 155, w=1.4)
    # laptop
    box(470, 120, 150, 70, "Monitoring laptop", "monitor · incident list|BenchCapture · TraceMerge", dash=True)
    ln(360, 155, 470, 155, dash=True)
    txt(372, 148, "mirror stream (UDP)")
    # analyzer
    box(470, 240, 150, 56, "Saleae Logic 8", "8 channels · USB", fill="#f7f7f7")
    ln(545, 240, 545, 190, w=1.4)
    txt(551, 222, "USB")
    # probe wires to the analyzer (grey, dashed)
    g = "#777"
    ln(160, 318, 545, 318, dash=True, w=1.2, color=g); ln(545, 318, 545, 296, dash=True, w=1.2, color=g)
    for y in (43, 103, 163, 233, 293):
        ln(150, y + 12, 160, y + 12, w=1.2, color=g)
    ln(160, 55, 160, 318, dash=True, w=1.2, color=g)
    txt(170, 312, "GPIO trace pins, laser enable, kill switch (3.3 V logic)", color=g)
    s.append("</svg>")
    return "\n".join(s)


def build() -> str:
    text = CONCEPT.read_text(encoding="utf-8")
    sec = section(text, SEC)
    t_limits, t_bench, t_wiring, t_trace, t_order, t_tools = tables(sec)
    slices = table_rows(section(text, "### Vertical slices"))

    p = []
    a = p.append
    a(PREAMBLE.replace("__TEAM__", TEAM).replace("__MS__", MILESTONE).replace("__DATE__", REPORT_DATE))
    a(f"""
#v(55mm)
#text(size: 26pt, weight: "bold")[{esc(TEAM)}]
#v(4mm)
#text(size: 15pt)[Milestone {MILESTONE} — Integration test debugging concept]
#v(10mm)
#text(size: 12pt)[Team: {esc(TEAM)} \\ Milestone: {MILESTONE} \\ Date: {REPORT_DATE}]
#v(1fr)
#text(size: 8.5pt, fill: luma(70))[{esc(m2.LECTURE)} Requirement IDs (F-VLT-n, NF-VLT-n) refer to the requirements approved at Gate 1 (milestone M2) as amended on 17 November 2026; decision IDs are ADR-VLT-n. The team has three sub-teams, named by their role: camera team, control team and laser team. There is no separate integration-support sub-team; its tasks are assigned per tool in Section 7.]
#pagebreak()
#outline(depth: 2, indent: auto)
#pagebreak()
""")

    # 1 purpose
    a("\n= Purpose and principle\n")
    a(p_("When an end-to-end test fails on the assembled system with live data, the team must find the cause "
         "quickly. This concept fixes the test bench, the trace points, the debugging order, the rule that "
         "separates timing violations from functional errors, how failures are reproduced, and the integration "
         "tools with owner and ready date. It is written before the nodes are built, so that the tools are "
         "planned into the slices (ADR-VLT-024)."))
    a("== System under test\n")
    a(p_("Five Raspberry Pi 3 B+ nodes on one isolated Ethernet switch (NF-VLT-15): three camera nodes observe "
         "a swinging ball, the control node (PTP grandmaster) fuses the observations every 10 ms and sends "
         "targets, the galvo node steers the laser spot through a DAC and the galvo driver and switches the "
         "laser supply. A monitoring laptop receives pushed data and never sends anything to the nodes "
         "(NF-VLT-10). All node messages are JSON over UDP. The end-to-end tests check these chains:"))
    a(tbl("(32mm, 14mm, 1fr, 36mm)", ["Chain", "Class", "From → to", "Deadline"], [
        ["T1 tracking", "firm", "physical change of the ball's motion → spot placed (NF-VLT-18)", "p99 ≤ 45 ms"],
        ["T3 unsafe condition", "hard", "spot outside the cube, ball seen by < 2 cameras, spot while off → laser off (F-VLT-26, F-VLT-11, F-VLT-16)", "100 ms"],
        ["T6 effect supervision", "hard", "aiming error > 50 mm persisting 500 ms → laser off (F-VLT-26)", "600 ms"],
        ["T8 kill switch", "firm", "press → safe state at the control node (F-VLT-30)", "100 ms"],
        ["fault reactions", "hard", "target loss (F-VLT-10), local galvo faults (F-VLT-15, F-VLT-25), galvo hang (NF-VLT-30), no measurable spot (F-VLT-42), camera data loss (F-VLT-11, F-VLT-20)", "110 ms · 100 ms · 1 s · 600 ms · 100 ms"],
    ]))
    a("\n== The monitor first\n")
    a(p_(para(sec, "Principle.")))
    a(tbl("(42mm, 1fr, 48mm)", ["Limit of the monitor", "Consequence", "Tool"], t_limits))
    a("\n" + p_("**Mirror stream.** Every node sends every loop message (Observation, CameraCalibration, Target, "
                "GalvoStatus) a second time, as the same bytes, to the laptop. The control node adds one record "
                "per 10 ms fusion slot (receive stamps of the drained messages, discarded messages with the "
                "reason, messages used, ball state, prediction, mode, laser request); the galvo node adds one "
                "record per received target (receive stamp, accepted or rejected with reason, time applied). "
                "Events (fault reaction, injection, latch, mode change) are sent at once. This adds about "
                "4 Mbit/s; all monitoring stays within 20 Mbit/s (NF-VLT-20)."))
    a(p_("**Nothing waits for the laptop.** The laptop is optional; the nodes don't check whether it is there "
         "and behave identically without it. The loop puts a copy into a bounded queue without waiting and "
         "drops it when the queue is full (NF-VLT-6); a separate sender process uses a non-blocking socket, "
         "counts send errors and never retries. The laptop's address is resolved by normal ARP, so with the "
         "laptop absent each node drops the copies itself instead of the switch flooding them to every port. "
         "The mirror stream is always on, also in the demo, so tests and demo have the same timing "
         "([L] p. 282, probe effect). The monitor only notifies: it has no safety role and no path back to "
         "the nodes (NF-VLT-10)."))

    # 2 test bench
    a("\n= Test bench\n")
    a(tbl("(26mm, 1fr)", ["Element", "Setup"], t_bench))
    a('\n#figure(image("bench.svg", width: 88%), caption: [Test bench. Solid: Ethernet; dashed black: '
      'mirror stream to the optional laptop; dashed grey: analyzer probes.])\n')
    a("\n== Wiring profiles\n")
    a(p_("The analyzer has eight channels. Two fixed wiring profiles cover all end-to-end tests; the profile is "
         "part of each test's setup."))
    a(tbl("(8mm, 1fr, 1fr)", ["Ch", "Profile A “chain”", "Profile B “galvo”"], t_wiring))
    a("\n" + p_(next(x.strip() for x in sec.split("\n\n") if x.strip().startswith("No optical stimulus"))))
    a("\n== How events are timestamped\n")
    a(p_(para(sec, "How events are timestamped.")))

    # 3 trace points
    a("\n= Trace points\n")
    a(p_("Every stage of the tracking transaction T1 is observed as follows. The analyzer covers the electrical "
         "part of the chain; the first and the last row are not observed independently."))
    a(tbl("(50mm, 1fr, 48mm)", ["Stage", "Observed by", "Collected in"], t_trace))
    trace_tail = sec.split("| spot placed |", 1)[1].split("\n", 1)[1]
    a("\n" + p_(trace_tail.strip().split("\n\n")[0]))
    a("== Plausibility checks of the monitor\n")
    a(p_("The monitor turns the mirror stream into incidents. Each incident has a time, a transaction, a "
         "stage, a node, the sequence numbers involved, the measured value and the limit."))
    a(tbl("(1fr, 1fr)", ["Check", "Finds"], [
        ["Sent vs received, per sender and sequence number", "network loss vs a message discarded by the receiver (F-VLT-23)"],
        ["Target sent vs received and applied at the galvo node", "lost or late target, galvo hang (F-VLT-10, F-VLT-25)"],
        ["Stage delays of every position update vs the stage budgets; end to end vs 45 ms", "the slow stage, for each single update (F-VLT-39, NF-VLT-18, NF-VLT-33)"],
        ["Clock offsets of all nodes vs 0.5 ms; timestamps in the future or going backwards", "clock and timestamp errors (NF-VLT-5, F-VLT-18, F-VLT-20)"],
        ["Frame, target and status rates per node", "a node that slows down before it fails (NF-VLT-33)"],
        ["Ball track physically plausible: speed, acceleration, reprojection per camera", "bad detection or calibration of one camera (F-VLT-3, F-VLT-12, F-VLT-27)"],
        ["Commanded vs reported laser state; mode at control vs galvo", "inconsistency between nodes (F-VLT-25, F-VLT-41)"],
        ["Own recomputation of node decisions: aiming error > 50 mm for 500 ms, target expiry, camera status", "bugs in the node checks themselves (F-VLT-26, F-VLT-22, F-VLT-11)"],
        ["Gaps in the monitor's own input", "marked “monitor data incomplete”; no false incidents (NF-VLT-6)"],
    ]))

    # 4 debugging order
    a("\n= Debugging order\n")
    a(p_("From the whole transaction down to one stage, one node and one message. Each step names its tool; "
         "the first five steps run on live data, the last two offline or with a replaced peer."))
    a(tbl("(22mm, 1fr, 1fr, 38mm)", ["Step", "Question", "Tool", "Leads to"], t_order))

    # 5 timing vs functional
    a("\n= Timing violation or functional error\n")
    lead = after(sec, "Timing violation or functional error.")
    a(p_(lead.split("\n\n")[0].replace("**Timing violation or functional error.**", "").strip()))
    a("#enum(\n" + ",\n".join("  [" + m3.md(clean(x)) + "]" for x in numbered(lead)) + ")\n")

    # 6 reproduction
    a("\n= Reproducing a failure\n")
    rep = after(sec, "Reproducing a failure.")
    a("#list(\n" + ",\n".join("  [" + m3.md(clean(x)) + "]" for x in bullets(rep)) + ")\n")

    # 7 tools
    a("\n= Integration tools\n")
    a(p_(para(sec, "Integration tools.").replace("relative to the slices", "relative to the slices below")))
    a(tbl("(34mm, 1fr, 34mm, 24mm, 18mm)", ["Tool", "Purpose", "Requirement / test", "Owner", "Ready"], t_tools))
    a("\n== Slice plan\n")
    a(p_("The system is built in vertical slices. The monitoring slice S7 is built right after S1, so the "
         "monitor serves every hardware integration step."))
    order = ["S1", "S7", "S2", "S3", "S4", "S5", "S6", "S8"]
    by = {r[0]: r for r in slices}
    a(tbl("(10mm, 10mm, 40mm, 1fr)", ["Order", "Slice", "Name", "Depends on"],
          [[str(i), s, by[s][1], by[s][3]] for i, s in enumerate(order, 1)]))
    return "\n".join(p)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    typ = OUT_DIR / f"{STEM}.typ"
    svg = OUT_DIR / "bench.svg"
    svg.write_text(bench_svg(), encoding="utf-8")
    typ.write_text(build(), encoding="utf-8")
    pdf = OUT_DIR / f"{STEM}.pdf"
    res = subprocess.run(["typst", "compile", "--ignore-system-fonts",
                          "--creation-timestamp", "1794873600", str(typ), str(pdf)])
    if res.returncode == 0:
        typ.unlink()
        svg.unlink()
        print(pdf)
    return res.returncode


if __name__ == "__main__":
    sys.exit(main())

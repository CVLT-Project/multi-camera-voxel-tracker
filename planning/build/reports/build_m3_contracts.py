#!/usr/bin/env python3
"""Generate one team contract per node team (DRS_M3_<team>_Contract_<Team>.pdf).

Source: the team contracts in the architecture of ../VLT/20-concept.md (subsection
"11.8 Team contracts"). Each contract copies in the detail it assigns: the module
specifications of the team's modules, the messages it provides and consumes, its
stages in the transactions and fault reactions, the requirements traced to its
modules and the build increments it delivers. Nothing is written by hand here, so a
contract cannot drift from the concept.

Usage (from the repository root):
    python3 planning/build/reports/build_m3_contracts.py
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
REPORT_DATE = "19 November 2026"
CONCEPT = m3.CONCEPT
OUT_DIR = m3.OUT_DIR

esc, md, section = m2.esc, m2.md, m2.section
table_rows, tbl, clean = m3.table_rows, m3.tbl, m3.clean

TEAMS = {
    # heading in the concept → (short name, file suffix, keywords that mark the team's stages and interfaces)
    "Camera team": ("camera team", "Camera_Team",
                    ["camera node", "camera sensor", "CameraNode", "Detector", "FrameSource", "Calibrator", "PoseChecker"]),
    "Control team": ("control team", "Control_Team",
                     ["control node", "ControlNode", "ValidityGate", "Triangulator", "Predictor", "TargetBuilder",
                      "EffectSupervisor", "ModeMachine", "GalvoCalibration", "MonitorServer", "every node", "any loop"]),
    "Laser team": ("laser team", "Laser_Team",
                   ["galvo node", "GalvoNode", "TargetGuard", "LaserPolicy", "OutputStream", "LaserGuard", "HwWatchdog",
                    "DAC", "kill switch", "ALSA", "underrun"]),
}
SENDERS = {"Camera team": ["camera", "every node"], "Control team": ["control", "every node"],
           "Laser team": ["galvo", "every node"]}
MESSAGES = ["Observation", "CameraCalibration", "Target", "GalvoStatus", "MonitorMessage"]
MSG_DIR = {
    "Observation": "camera node → control node, UDP, one per frame",
    "CameraCalibration": "camera node → control node, UDP state message every 500 ms",
    "Target": "control node → galvo node, UDP, one per fusion step (10 ms), in every mode",
    "GalvoStatus": "galvo node → control node, UDP, with each newly applied target and at least every 50 ms",
    "MonitorMessage": "every node → monitoring laptop, UDP, best effort; events at once, status ≤ 20 Hz, images ≤ 5/s, diagnostics summary every 1 s",
}


# --------------------------------------------------------------------------- concept parsing

def contracts(text: str):
    """{heading: (title line, {item: value})} from the team contract tables."""
    sec = section(text, "### 11.8 Team contracts")
    out = {}
    for head, body in m3.sub_tables(sec):
        key = head.split(" — ")[0]
        out[key] = (head, {r[0]: r[1] for r in table_rows(body)})
    rules = sec.split("**Rules for all teams**", 1)[1].split("\n#### ", 1)[0]
    return out, [x for x in re.findall(r"^- (.+)$", rules, re.M)]


def module_paths(cell: str):
    return re.findall(r"`([\w/]+(?:\.py|/))`", cell)


def module_specs(text: str):
    """{module path: spec body} for every '#### <path>[, <path>] — <Class>' heading."""
    specs = section(text, "### Module specifications")
    out = {}
    for head, body in m3.sub_tables(specs):
        paths, _, cls = head.partition(" — ")
        for p_ in [x.strip() for x in paths.split(",")]:
            out[p_] = (cls.strip(), body.strip())
    return out


def tree_lines(text: str):
    """{module path: (class, one-line responsibility)} from the module tree."""
    code = section(text, "### Module overview & tree").split("```")[1]
    out, folder = {}, None
    for line in code.splitlines():
        m = re.match(r"^  (\w+/)\s", line)
        if m:
            folder = m.group(1)
            continue
        m = re.match(r"^    ([\w/]+\.py|dashboard/)\s+(\S.*?)\s{2,}(\S.*)$", line)
        if m and folder:
            out[folder + m.group(1)] = (m.group(2).strip(), m.group(3).strip())
    return out


def render_spec(body: str) -> str:
    """Bullets and paragraphs as Typst text, code fences as raw blocks."""
    out = []
    for i, part in enumerate(body.split("```")):
        if i % 2:
            lang, _, code = part.partition("\n")
            code = code.replace("see §11.1", "see the message specification").replace("fields of §10", "message fields").replace("# §10", "# message fields")
            out.append("#block(width: 100%, fill: luma(245), inset: 6pt, radius: 2pt)[#set text(size: 7.2pt)\n```"
                       + (lang.strip() or "python") + "\n" + code.rstrip() + "\n```\n]\n")
            continue
        for para in [x.strip() for x in part.split("\n\n") if x.strip()]:
            if para.startswith("|"):
                rows = table_rows(para)
                hdr = [x.strip() for x in para.splitlines()[0].strip()[1:-1].split("|")]
                out.append(tbl("(" + ", ".join(["1fr"] * len(hdr)) + ")", hdr, rows))
                continue
            for line in para.splitlines():
                line = line.strip()
                out.append(("- " + md(clean(line[2:])) if line.startswith("- ") else md(clean(line))) + "\n")
            out.append("\n")
    return "".join(out)


def hits(row, words) -> bool:
    s = " ".join(row)
    return any(w in s for w in words)


# --------------------------------------------------------------------------- one contract

def build(text: str, key: str, head: str, items: dict, rules: list, owner_of: dict) -> str:
    short, _, words = TEAMS[key]
    mods = module_paths(items["Modules"])
    specs = module_specs(text)
    tree = tree_lines(text)
    p = []
    a = p.append
    a(m3.PREAMBLE.replace("__TEAM__", TEAM).replace("__MS__", MILESTONE).replace("__DATE__", REPORT_DATE)
      .replace("Architecture and integration tests", f"Team contract — {key}"))
    a(f"""
#v(55mm)
#text(size: 26pt, weight: "bold")[{esc(TEAM)}]
#v(4mm)
#text(size: 15pt)[Milestone {MILESTONE} — Team contract: {esc(head)}]
#v(10mm)
#text(size: 12pt)[Team: {esc(TEAM)} \\\\ Sub-team: {esc(key)} \\\\ Milestone: {MILESTONE} \\\\ Date: {REPORT_DATE}]
#v(25mm)
#block(width: 100%, inset: 8pt, stroke: 0.8pt)[*What this is.* Everything the {esc(short)} builds, what it provides to and expects from the other two teams, its share of the timing budgets, its requirements and how it is accepted. Taken from the architecture approved at Gate 2 on {m3.GATE2_STATE}; the architecture stays binding where this extract is shorter.]
#v(1fr)
#text(size: 8.5pt, fill: luma(70))[{esc(m2.LECTURE)} Requirement IDs (F-VLT-n, NF-VLT-n) refer to the requirements approved at Gate 1 and amended at Gate 2; decision IDs are ADR-VLT-n. Module paths are relative to the code folder `src/`.]
#pagebreak()
#outline(depth: 2, indent: auto)
#pagebreak()
""")

    # 1 contract
    a("= Contract\n")
    a(tbl("(32mm, 1fr)", ["Item", "Contract"], [[k, v] for k, v in items.items() if k != "Modules"]))
    a("\n== Rules for all teams\n")
    a("\n".join("- " + md(clean(r)) for r in rules) + "\n")

    # 2 modules
    a("\n= Modules and logic\n")
    a(md(f"The {short} owns these modules; only it changes them. One module = one file = one class = one "
         "responsibility (NF-VLT-14). Pseudocode is Python with type hints: `Ns` = shared-clock nanoseconds (int64), "
         "`MonoNs` = local monotonic nanoseconds, never corrected by the clock synchronization; `Mm`, `Px` = millimetres, "
         "pixels. Inside a loop a rejected input is a return value, never an exception.") + "\n\n")
    a(tbl("(44mm, 30mm, 1fr)", ["Module", "Class", "Responsibility"],
          [[f"`{m}`", tree.get(m, ("—", ""))[0], tree.get(m, ("", "—"))[1]] for m in mods]))
    for m in mods:
        if m in specs:
            cls, body = specs[m]
            a(f"\n== {esc(cls)}\n")
            a(md(f"`{m}`") + "\n\n")
            a(render_spec(body))

    # 3 interfaces
    a("\n= Interfaces\n")
    prov = [n for n in MESSAGES if re.search(rf"`{n}`", items.get("Provides", ""))]
    cons = [n for n in MESSAGES if re.search(rf"`{n}`", items.get("Consumes", ""))]
    a(md("**Provides:** " + clean(items.get("Provides", "—"))) + "\n\n")
    a(md("**Consumes:** " + clean(items.get("Consumes", "—"))) + "\n\n")
    a(md("All messages between the nodes are JSON: one UTF-8 JSON object per UDP datagram, ≤ 1400 bytes "
         "(MonitorMessage ≤ 60 000 bytes), `type` and `schema_version` in every message, int64 values as decimal "
         "strings, never retransmitted or queued behind old data (F-VLT-23, NF-VLT-27). A change to a message needs "
         "the review of all three teams.") + "\n\n")
    a("== Common fields\n")
    env = table_rows(text.split("`Observation` and `Target` both carry:", 1)[1].split("\n\n**")[0])
    a(tbl("(32mm, 18mm, 1fr)", ["Field", "Type", "Meaning"], env))
    for name in prov + [x for x in cons if x not in prov]:
        role = "provided and consumed" if name in prov and name in cons else ("provided" if name in prov else "consumed")
        a(f"\n== {name} ({role})\n")
        a(md(MSG_DIR[name]) + "\n\n")
        if name == "CameraCalibration":
            a(md("Camera, session, profile, setup and calibration IDs; intrinsic matrix K (9 values), distortion "
                 "(k1, k2, p1, p2, k3), rotation (9), translation (3, mm), reprojection residual (px), marker count "
                 "and IDs. The control node uses a camera's frames only after the matching calibration is validated "
                 "(F-VLT-12, F-VLT-24, F-VLT-44).") + "\n")
        else:
            a(tbl("(38mm, 26mm, 1fr)", ["Field", "Type", "Range / meaning"],
                  m3.message_fields(text, name) + m3.EXTRA_FIELDS.get(name, [])))
            if name == "MonitorMessage":
                a("\n" + md("**What your node sends:** " + clean(items.get("Monitoring", "—"))) + "\n")
                a(m3.monitor_block(text, None if name in cons else SENDERS[key]))
        a(m3.example_block(text, name))
    inner = [r for r in table_rows(section(text, "### Inter-module interfaces")) if hits(r[:2], words)]
    if inner:
        a("\n== Calls and channels at the team's boundary\n")
        a(tbl("(28mm, 32mm, 1fr, 1fr)", ["From", "To", "Call / message", "Errors"], [[r[0], r[1], r[2], r[4]] for r in inner]))
    used = sorted({m for m in re.findall(r"`(\w+)`", items.get("Consumes", "")) if m in
                   {"CameraModel", "GalvoModel", "ClockStatus", "Config", "SetupIdentity", "RtLoop", "MonitorLink", "EventLog",
                    "MessageCodec", "StateLink", "SequenceTracker", "NodeHealth"}})
    if used:
        a("\n== Classes used from other teams\n")
        by_cls = {cls: (path, body) for path, (cls, body) in specs.items()}
        rows = []
        for cls in used:
            path = by_cls.get(cls, ("—", ""))[0]
            rows.append([cls, f"`{path}`", owner_of.get(path, "—"), tree.get(path, ("", "—"))[1]])
        a(tbl("(28mm, 40mm, 24mm, 1fr)", ["Class", "Module", "Owner", "What it gives you"], rows))

    # 4 timing
    a("\n= Timing\n")
    a(md("Your stages in the transactions and fault reactions. Each stage's measured high-water mark over a "
         "10-min run must fit its worst case (NF-VLT-33); the end-to-end chains are accepted jointly in S8.") + "\n\n")
    a(md("**Stage budgets:** " + items.get("Stage budgets", "—")) + "\n")
    tx = section(text, "### 11.2 Transactions, fault reactions and mode activities")
    for h, body in m3.sub_tables(tx):
        rows = table_rows(body)
        if h.startswith("T"):
            mine = [r for r in rows if r[0] and hits(r[1:3], words)]
            if not mine:
                continue
            total = [r for r in rows if "end to end" in r[1]]
            a(f"\n== {md(clean(h))}\n")
            a("#block[#set text(size: 7.6pt)\n")
            a(tbl("(4mm, 19mm, 26mm, 1.7fr, 14mm, 13mm, 17mm, 1.1fr, 0.9fr)",
                  ["\\#", "Stage", "Node / element", "What happens", "Period", "WCET", "Worst case", "Error handling", "Check"], mine))
            a("]\n")
            if total:
                a(md("End to end: " + total[0][6]) + "\n")
        elif h.startswith("Fault"):
            mine = [r for r in rows if hits(r[1:4], words)]
            if mine:
                a("\n== Fault reactions\n")
                a(tbl("(20mm, 1fr, 1fr, 0.9fr, 0.9fr, 0.9fr, 21mm)",
                      ["Fault reaction", "Origin", "Detection", "Reaction", "Worst case", "Deadline (class)", "Requirement"], mine))
        elif h.startswith("Numeric"):
            a("\n== Validity limits (all teams)\n")
            a(md(clean(body.strip())) + "\n")

    # 5 requirements
    a("\n= Requirements\n")
    trace = table_rows(section(text, "### Requirement traceability matrix"))
    mine_base = {x.removesuffix(".py") for x in mods}
    reqs = {r[0]: r for r in table_rows(section(text, "## 3. Functional Requirements"))
            + table_rows(section(text, "## 5. Non-Functional Requirements"))}
    rows = []
    for r in trace:
        named = re.findall(r"\b((?:camera|control|galvo|monitor|common|sim|bench)/\w+)", r[1])
        if not any(n in mine_base for n in named):
            continue
        others = sorted({owner_of.get(n + ".py", owner_of.get(n + "/", "")) for n in named if n not in mine_base} - {"", short})
        req = reqs.get(r[0])
        if not req:
            continue
        rows.append([r[0], req[1], req[3], r[2], ", ".join(others) if others else "—"])
    also = re.findall(r"(?:NF|F)-VLT-\d+", items.get("Also responsible for", ""))
    slice_of = {r[0]: r[2] for r in trace}
    for rid in also:
        if rid in reqs and rid not in [x[0] for x in rows]:
            rows.append([rid, reqs[rid][1], reqs[rid][3], slice_of.get(rid, "—"), "see contract"])
    a(md(f"Every requirement whose traceability names one of your modules, plus those listed under "
         f"*Also responsible for*: {len(rows)} requirements. "
         "\"Shared with\" names the other teams whose modules also carry it; each team delivers its part.") + "\n\n")
    a("#block[#set text(size: 7.6pt)\n")
    a(tbl("(17mm, 1.4fr, 1.2fr, 12mm, 18mm)", ["ID", "Requirement", "Acceptance", "Increment", "Shared with"], rows))
    a("]\n")

    # 6 increments and deliveries
    a("\n= Build increments and acceptance\n")
    a(md("**Delivers to the other teams:** " + items.get("Delivers to others", "—")) + "\n\n")
    want = set(re.findall(r"S\d", items.get("Acceptance", "")))
    slices = [r for r in table_rows(section(text, "### Vertical slices")) if r[0] in want]
    a(tbl("(9mm, 28mm, 1fr, 1.2fr)", ["ID", "Increment", "Delivers (requirements)", "Acceptance"],
          [[r[0], r[1], r[2], r[4]] for r in slices]))
    a("\n== Open checks\n")
    a(md(items.get("Open checks", "none")) + "\n")
    return "".join(p)


def main() -> int:
    text = CONCEPT.read_text(encoding="utf-8")
    cons, rules = contracts(text)
    owner_of = {}
    for key, (_, items) in cons.items():
        for m in module_paths(items["Modules"]):
            assert m not in owner_of, f"{m} owned twice"
            owner_of[m] = TEAMS[key][0]
    unowned = [m for m in tree_lines(text) if m not in owner_of and not m.endswith("fault_injector.py")]
    if unowned:
        print("modules without a team:", ", ".join(unowned), file=sys.stderr)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rc = 0
    for key, (head, items) in cons.items():
        stem = f"DRS_{MILESTONE}_{TEAM.replace(' ', '_')}_Contract_{TEAMS[key][1]}"
        typ, pdf = OUT_DIR / f"{stem}.typ", OUT_DIR / f"{stem}.pdf"
        typ.write_text(build(text, key, head, items, rules, owner_of), encoding="utf-8")
        res = subprocess.run(["typst", "compile", "--ignore-system-fonts",
                              "--creation-timestamp", "1795046400", str(typ), str(pdf)])
        if res.returncode == 0:
            typ.unlink()
            print(pdf)
        rc |= res.returncode
    return rc


if __name__ == "__main__":
    sys.exit(main())

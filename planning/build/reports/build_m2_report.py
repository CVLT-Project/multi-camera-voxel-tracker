#!/usr/bin/env python3
"""Generate the M2 requirements report (DRS_M2_<team>.pdf).

Sources: the requirements in ../VLT/20-concept.md and the decision records
in ../decisions/ that it links. The script writes a Typst file next to the
PDF and compiles it with the `typst` CLI using only Typst's embedded fonts,
so the result does not depend on the fonts installed on the machine.

Usage (from the repository root):
    python3 planning/build/reports/build_m2_report.py
"""

import pathlib
import re
import subprocess
import sys

TEAM = "Voxel Camera with Laser Tracking"
MILESTONE = "M2"
REPORT_DATE = "12 November 2026"
GATE1_DATE = "12 November 2026"  # date of the team's Gate 1 approval

HERE = pathlib.Path(__file__).resolve().parent
BUILD = HERE.parent
CONCEPT = BUILD / "VLT" / "20-concept.md"
DECISIONS = BUILD / "decisions"
OUT_DIR = HERE / "output" / "pdf"
STEM = f"DRS_{MILESTONE}_{TEAM.replace(' ', '_')}"

LECTURE = ('[L] = lecture slides "Distributed Real-Time Systems", winter term 2026, '
           "308 pages; \"p.\" is the PDF page number.")


# --------------------------------------------------------------------------- markdown → typst

def esc(s: str) -> str:
    """Escape plain text for Typst markup."""
    s = s.replace("\\", "\\\\")
    for ch in "#$*_`<>@[]~=":
        s = s.replace(ch, "\\" + ch)
    s = s.replace("/", "\\/")  # avoid // comments and /* */
    s = s.replace("--", "-​-")
    return s


ID = re.compile(r"\b(?:N?F|ADR)-VLT-\d+(?:/\d+)*|\bOQ-\d+|\bT\d\b")


def plain(s: str) -> str:
    """Escape text and keep requirement/decision IDs on one line."""
    out, pos = [], 0
    for m in ID.finditer(s):
        out.append(esc(s[pos:m.start()]))
        out.append("#box[" + esc(m.group(0)) + "]")
        pos = m.end()
    out.append(esc(s[pos:]))
    return "".join(out)


INLINE = re.compile(r"\*\*(.+?)\*\*|`([^`]+)`|(?<![\w*])\*([^*\s][^*]*?)\*(?![\w*])")


def md(s: str) -> str:
    """Convert the inline markdown used in the concept (bold, italic, code) to Typst."""
    out, pos = [], 0
    for m in INLINE.finditer(s):
        out.append(plain(s[pos:m.start()]))
        if m.group(1) is not None:
            out.append("#strong[" + esc(m.group(1)) + "]")
        elif m.group(2) is not None:
            out.append("#raw(" + typ_str(m.group(2)) + ")")
        else:
            out.append("#emph[" + esc(m.group(3)) + "]")
        pos = m.end()
    out.append(plain(s[pos:]))
    return "".join(out)


def typ_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


SECTION_REFS = [
    (r"\s*\(§10\)", ""),
    (r"\(§6, ", "(given components, "),
    (r"\(§6\)", "(given components)"),
    (r"§6", "given components"),
    (r"§2", "terms"),
    (r"§7", "out of scope"),
    (r"§9", "interference review"),
]


def clean(s: str) -> str:
    """Make concept text self-contained: no section references, no old U- IDs, no 'Proposed' markers."""
    for pat, rep in SECTION_REFS:
        s = re.sub(pat, rep, s)
    s = re.sub(r"\(was U-VLT-\d+\)\s*", "", s)
    s = re.sub(r", was U-VLT-\d+", "", s)
    s = re.sub(r"U-VLT-\d+ \(now (F-VLT-\d+)\)", r"\1", s)
    s = re.sub(r"^Proposed(:| —)\s*", "", s)
    s = re.sub(r"Proposed \((ADR-VLT-\d+)\): an ", r"(\1) An ", s)
    return s


def c(s: str) -> str:
    """A Typst content block from markdown text."""
    return "[" + md(clean(s.strip())) + "]"


# --------------------------------------------------------------------------- concept parsing

def section(text: str, heading: str) -> str:
    """Body of a '## '/'### ' section, up to the next heading of the same or higher level."""
    level = heading.split(" ")[0]
    start = text.index("\n" + heading) + 1
    nxt = re.compile(r"^#{1,%d} " % len(level), re.M)
    m = nxt.search(text, start + len(heading))
    return text[start + len(heading):m.start() if m else len(text)]


def table_rows(block: str):
    rows = []
    for line in block.splitlines():
        if not line.startswith("|") or re.match(r"^\|\s*-{3}", line):
            continue
        cells = [x.strip() for x in line.strip().strip("|").split(" | ")]
        rows.append(cells)
    return rows[1:]  # without the header row


def strip_proposed(s: str) -> str:
    return re.sub(r"^Proposed(:| —)\s*", "", s)


def requirements(block: str, prefix: str):
    reqs = []
    for r in table_rows(block):
        if re.fullmatch(prefix + r"-VLT-\d+", r[0]):
            reqs.append({"id": r[0], "text": strip_proposed(r[1]), "reason": r[2], "acc": r[3]})
    return reqs


def adrs():
    out = []
    for f in sorted(DECISIONS.glob("ADR-VLT-*.md")):
        t = f.read_text(encoding="utf-8")
        title = t.splitlines()[0].lstrip("# ").strip()
        ident, _, name = title.partition(" — ")
        status = re.search(r"^- \*\*Status:\*\* (.+)$", t, re.M).group(1)
        if "Gate 2" in status:  # M3 architecture proposals are not part of the M2 report
            continue
        rationale = section(t, "## Rationale").strip().split("\n\n")[0].replace("\n", " ")
        if status.startswith("superseded"):
            state = "superseded by " + re.search(r"ADR-VLT-\d+", status).group(0)
        elif status.startswith("proposed"):
            state = "decided at Gate 1"
        else:
            state = "decided " + re.search(r"\d{4}-\d{2}-\d{2}", status).group(0)
        out.append((ident, name, state, rationale))
    return out


def open_questions(block: str):
    qs = []
    for m in re.finditer(r"^- \*\*(OQ-\d+)\*\* — (.+)$", block, re.M):
        oq, body = m.groups()
        if body.startswith("resolved"):
            continue
        owner = re.search(r" — owner: ([^—]+?)(?: — |$)", body)
        blocks = re.search(r" — blocks: (.+)$", body)
        text = re.split(r" — owner: ", body)[0]
        qs.append((oq, text, owner.group(1).strip() if owner else "—",
                   blocks.group(1).strip().rstrip(".") if blocks else "—"))
    return qs


# --------------------------------------------------------------------------- report

PREAMBLE = r"""
#set document(title: "DRS __MS__ — __TEAM__", author: "__TEAM__")
#set text(font: "Libertinus Serif", size: 9.5pt, lang: "en", hyphenate: false)
#set par(justify: true, leading: 0.55em)
#set heading(numbering: "1.")
#show heading.where(level: 1): it => block(above: 1.4em, below: 0.8em, text(size: 13pt, it))
#show heading.where(level: 2): it => block(above: 1.1em, below: 0.6em, text(size: 11pt, it))
#set table(stroke: 0.4pt + luma(180), inset: 4pt)
#show table.cell.where(y: 0): set text(weight: "bold")
#show table: set par(justify: false)
#set page(paper: "a4", margin: (x: 18mm, top: 22mm, bottom: 20mm),
  header: context { if here().page() > 1 [
    #set text(size: 8pt, fill: luma(90))
    __TEAM__ #h(1fr) __MS__ · Requirements
    #v(-4pt) #line(length: 100%, stroke: 0.4pt + luma(180)) ] },
  footer: context { if here().page() > 1 [
    #set text(size: 8pt, fill: luma(90))
    __DATE__ #h(1fr) #counter(page).display("1 / 1", both: true) ] })

#let req(id, body, reason, acc) = block(breakable: true, width: 100%, inset: (y: 4pt),
  stroke: (bottom: 0.4pt + luma(200)))[
  #grid(columns: (19mm, 1fr), column-gutter: 3mm,
    text(weight: "bold", id),
    [#body
     #block(above: 0.5em)[#text(fill: luma(70))[_Reason._ #reason]]
     #block(above: 0.4em)[_Acceptance._ #acc]])]
"""


def build() -> str:
    text = CONCEPT.read_text(encoding="utf-8")
    purpose = section(text, "## 1. Purpose").strip()
    terms = table_rows(section(text, "## 2. Ubiquitous Language & Context"))
    f_reqs = requirements(section(text, "## 3. Functional Requirements"), "F")
    nf_block = section(text, "## 5. Non-Functional Requirements")
    nf_reqs = requirements(nf_block, "NF")
    matrix = table_rows(nf_block.split("**Reaction matrix (NF-VLT-34)**")[1].split("###")[0])
    interfaces = table_rows(section(text, "## 6. Integration Points"))
    out_of_scope = re.findall(r"^- (.+)$", section(text, "## 7. Out of Scope"), re.M)
    sec8 = section(text, "## 8. Resolved Questions & ADRs")
    direct = [r for r in table_rows(sec8.split("### Open questions")[0]) if r[3].startswith("→")]
    oqs = open_questions(sec8)
    checklist = table_rows(section(text, '### Lecture checklist "Requirements for DRS"'))

    p = []
    a = p.append
    a(PREAMBLE.replace("__TEAM__", TEAM).replace("__MS__", MILESTONE).replace("__DATE__", REPORT_DATE))

    # title page
    a(f"""
#v(55mm)
#text(size: 26pt, weight: "bold")[{esc(TEAM)}]
#v(4mm)
#text(size: 15pt)[Milestone {MILESTONE} — Requirements and Gate 1]
#v(10mm)
#text(size: 12pt)[Team: {esc(TEAM)} \\ Milestone: {MILESTONE} \\ Date: {REPORT_DATE}]
#v(25mm)
#block(width: 100%, inset: 8pt, stroke: 0.8pt)[
  *Gate 1.* The team has read and approved the requirements in this report on {GATE1_DATE}.
]
#v(1fr)
#text(size: 8.5pt, fill: luma(70))[{esc(LECTURE)} Lecture pages justify every requirement with a time; the numeric values are the project's own choices unless stated otherwise.]
#pagebreak()
""")

    # 1 system
    loop = ("The physical loop runs from the swinging ball and the laser spot, through the three cameras, "
            "the network and the control node (3D position and prediction), to the galvo mirrors and the laser, "
            "and back to the spot on the ball, which the cameras observe again. The cameras therefore see the "
            "effect of the actuator, so the system measures its own aiming error.")
    field = ("Field of application: a distributed real-time system with embedded sensing and actuation — "
             "five Raspberry Pi 3 nodes (three camera nodes, one control node, one galvo node) on one wired "
             "Ethernet switch with a shared software PTP clock, built as a laboratory demonstrator.")
    a("= The system in a few sentences\n")
    a(md(purpose) + "\n\n" + md(field) + "\n\n" + md(loop) + "\n")
    a("\n== Terms\n")
    a("#table(columns: (30mm, 1fr), table.header([Term], [Meaning]),\n")
    a(",\n".join(f"  {c(t[0])}, {c(t[1])}" for t in terms) + ")\n")
    a("\n== How to read the requirements\n")
    a(md("Every requirement has an ID (F- functional, NF- non-functional), a reason with its lecture basis "
         "[L] and a falsifiable acceptance criterion. Every time carries a unit. IDs are never renumbered; a "
         "dropped requirement keeps its ID. Requirements reference decisions (ADR-VLT-n, Section 5) and open "
         "questions (OQ-n, Section 6) by ID. The real-time transactions T1 … T7 and their deadline classes "
         "are defined in NF-VLT-26.") + "\n")

    # 2 functional
    a("\n= Functional requirements\n")
    for r in f_reqs:
        a(f"#req({typ_str(r['id'])}, {c(r['text'])}, {c(r['reason'])}, {c(r['acc'])})\n")

    # 3 non-functional
    a("\n= Non-functional requirements\n")
    for r in nf_reqs:
        a(f"#req({typ_str(r['id'])}, {c(r['text'])}, {c(r['reason'])}, {c(r['acc'])})\n")
    a("\n== Reaction matrix (NF-VLT-34)\n")
    a("#table(columns: (1.3fr, 1.1fr, 1.1fr, 0.9fr, 0.8fr), "
      "table.header([Error], [Detected by], [Reaction], [Time limit], [Requirement]),\n")
    a(",\n".join("  " + ", ".join(c(x) for x in r[:5]) for r in matrix) + ")\n")

    # 4 checklist, given components, scope
    a("\n= DRS requirements checklist\n")
    a(md("The lecture's checklist \"Requirements for DRS\" ([L] p. 287–288). Rule ([L] p. 287): an item "
         "that is given to us is a requirement; an item we choose belongs in the architecture and is "
         "deferred there with that reason.") + "\n\n")
    a("#table(columns: (6mm, 1.2fr, 1.3fr, 1.2fr), "
      "table.header([\\#], [Checklist item], [Covered by], [Deferred / still open (reason)]),\n")
    rows = []
    for r in checklist:
        cov = r[2].replace("(§6, ", "(given components, ").replace("§6", "given components")
        dfr = re.sub(r"\s*\(§10 is design input\)", "", r[3])
        rows.append("  " + ", ".join(c(x) for x in (r[0], r[1], cov, dfr)))
    a(",\n".join(rows) + ")\n")
    a("\n== Given components and interfaces\n")
    a("#table(columns: (1.1fr, 0.5fr, 2fr, 0.7fr), "
      "table.header([Component], [Direction], [Given contract], [Owner (role)]),\n")
    a(",\n".join("  " + ", ".join(c(x) for x in r[:4]) for r in interfaces) + ")\n")
    a("\n== Out of scope\n")
    a("\n".join("- " + md(clean(x)) for x in out_of_scope) + "\n")

    # 5 decisions
    a("\n= Decisions taken\n")
    a(md("Each decision with its reason. Decisions marked \"decided at Gate 1\" were approved together with "
         "the requirements.") + "\n\n")
    a("#table(columns: (23mm, 1.3fr, 19mm, 2fr), table.header([ID], [Decision], [State], [Reason]),\n")
    a(",\n".join(f"  {c(i)}, {c(n)}, {c(s)}, {c(r)}" for i, n, s, r in adrs()) + ")\n")
    a("\n== Decisions recorded directly as requirements\n")
    a("#table(columns: (1.2fr, 1.3fr, 1fr), table.header([Question], [Decision], [Requirement]),\n")
    a(",\n".join(f"  {c(r[1])}, {c(r[2])}, {c(r[3].lstrip('→ '))}" for r in direct) + ")\n")

    # 6 open questions
    a("\n= Open questions\n")
    a(md("Owners are sub-team roles. The open questions block numeric values and hardware facts only; every "
         "requirement already states what has to hold.") + "\n\n")
    a("#table(columns: (12mm, 2.4fr, 0.9fr, 0.9fr), table.header([ID], [Question], [Owner], [Blocks]),\n")
    a(",\n".join(f"  {c(q[0])}, {c(q[1])}, {c(q[2])}, {c(q[3])}" for q in oqs) + ")\n")
    resolved = []
    for oq, body in re.findall(r"^- \*\*(OQ-\d+)\*\* — resolved [\d-]+(?: →|:)?\s*(.+)$", sec8, re.M):
        resolved.append(oq + " → " + re.split(r"\. ", body)[0].rstrip("."))
    a("\n== Resolved questions\n")
    a("\n".join("- " + md(clean(x)) for x in resolved) + "\n")

    # 7 gate 1
    a("\n= Gate 1\n")
    a(md(f"The team has read and approved the requirements in this report (F-VLT-1 … F-VLT-{len(f_reqs)}, "
         f"NF-VLT-1 … NF-VLT-{len(nf_reqs)}) and the decisions in Section 5 on {GATE1_DATE}. The architecture "
         "(milestone M3) starts after this approval.") + "\n")
    return "".join(p)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    typ = OUT_DIR / f"{STEM}.typ"
    typ.write_text(build(), encoding="utf-8")
    pdf = OUT_DIR / f"{STEM}.pdf"
    res = subprocess.run(["typst", "compile", "--ignore-system-fonts",
                          "--creation-timestamp", "1794441600", str(typ), str(pdf)])
    if res.returncode == 0:
        typ.unlink()
        print(pdf)
    return res.returncode


if __name__ == "__main__":
    sys.exit(main())

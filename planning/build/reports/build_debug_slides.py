#!/usr/bin/env python3
"""Short slide deck (16:9 PDF) for the class presentation of the debugging concept,
in German and English:

    output/pdf/Slides_Debugging_<team>.pdf       German
    output/pdf/Slides_Debugging_<team>_EN.pdf    English (the German text with the EN table applied)

Follows the system-design deck (build_class_slides.py) and reuses its style; the big
picture of the system is not repeated. Hand-picked summary of the M3 integration test
debugging concept (DRS_M3_..._Debugging.pdf). Typst with the system font Noto Sans.

Usage (from the repository root):
    python3 planning/build/reports/build_debug_slides.py
"""

import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_class_slides as cs  # noqa: E402  (STYLE and the deck helpers)

TEAM = cs.TEAM
DATE = "17. November 2026"
OUT_DIR = cs.OUT_DIR
STAMP = "1795392000"  # 17 Nov 2026, fixed so the PDF is reproducible
DECK = "Debugging"


def title_slide() -> str:
    return f"""
#page(fill: navy, background: none, footer: none)[
  #set text(fill: white)
  #v(1fr)
  #text(11pt, weight: "bold", fill: laser, tracking: 0.1em)[DISTRIBUTED REAL-TIME SYSTEMS · WINTERSEMESTER 2026]
  #v(0.2em)
  #text(34pt, weight: "bold")[{TEAM}]
  #v(-0.3em)
  #text(20pt)[Debugging der Integrationstests]
  #v(0.8em)
  #rect(width: 4cm, height: 3pt, fill: laser)
  #v(0.4em)
  #text(12pt, fill: rgb("#c9d6e3"))[Meilenstein M3 · Debugging-Konzept \\ {DATE}]
  #v(1fr)
]
"""


def bench_svg() -> str:
    """Test bench: five nodes, switch, monitoring laptop and logic analyzer."""
    W, H = 960, 400
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="Noto Sans, sans-serif" font-size="18">']

    def box(x, y, w, h, title, sub, fill, fg="white", dash=False):
        d = ' stroke="#16324f" stroke-dasharray="6 4" stroke-width="2"' if dash else ""
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}"{d}/>')
        s.append(f'<text x="{x + w / 2}" y="{y + h / 2 - 2}" text-anchor="middle" fill="{fg}" font-weight="bold" font-size="22">{title}</text>')
        s.append(f'<text x="{x + w / 2}" y="{y + h / 2 + 22}" text-anchor="middle" fill="{fg}" font-size="16">{sub}</text>')

    nodes = [("Kamera 0", "#2a9d8f"), ("Kamera 1", "#2a9d8f"), ("Kamera 2", "#2a9d8f"),
             ("Control", "#16324f"), ("Galvo", "#d1495b")]
    xs = [10 + i * 175 for i in range(5)]
    # trace pins: node tops -> analyzer (dashed grey)
    for x in xs:
        s.append(f'<line x1="{x + 80}" y1="150" x2="450" y2="76" stroke="#5b6b7d" stroke-width="2" stroke-dasharray="5 4"/>')
    # Ethernet: node bottoms -> switch
    for x in xs:
        s.append(f'<line x1="{x + 80}" y1="220" x2="440" y2="300" stroke="#16324f" stroke-width="2.5"/>')
    # mirror stream and USB
    s.append('<line x1="520" y1="330" x2="680" y2="340" stroke="#d1495b" stroke-width="3" stroke-dasharray="8 5"/>')
    s.append('<path d="M650,43 H940 V340 H922" fill="none" stroke="#e9a23b" stroke-width="2.5"/>')
    box(250, 10, 400, 66, "Logic Analyzer", "Trace-Pins, Laser-Enable, Kill-Switch", "#e9a23b")
    for (name, c), x in zip(nodes, xs):
        box(x, 150, 160, 70, name, "Pi 3 B+", c)
    box(360, 300, 160, 60, "Switch", "isoliert", "#c9d1db", fg="#16324f")
    box(680, 300, 240, 80, "Laptop · Monitor", "empfängt nur", "white", fg="#16324f", dash=True)
    s.append('<text x="600" y="112" fill="#5b6b7d" font-size="18" font-weight="bold">Trace-Pins</text>')
    s.append('<text x="530" y="300" fill="#d1495b" font-size="18" font-weight="bold">Mirror-Stream</text>')
    s.append('<text x="948" y="200" fill="#e9a23b" font-size="18" font-weight="bold" text-anchor="end">USB</text>')
    s.append("</svg>")
    return "\n".join(s)


def deck() -> str:
    p = [cs.STYLE.replace("__TITLE__", DECK).replace("__TEAM__", TEAM).replace("__DECK__", DECK)]
    p.append(title_slide())
    p.append(r"""
#slide("Integrationstest", "Testaufbau")[
  #grid(columns: (2.4fr, 1fr), gutter: 0.5cm,
    align(center + horizon, image("bench.svg", width: 100%)),
    align(horizon, stack(spacing: 0.4cm,
      block(width: 100%, height: 3.35cm,
        stat("5 Nodes", "Demo-Aufbau", "Raspberry Pi 3 B+ · isolierter Switch", accent: laser)),
      block(width: 100%, height: 3.35cm,
        stat("≤ 1 ms", "2 Zeitachsen", "PTP-Uhr ↔ Analyzer, über Sekundenmarken abgeglichen")))))
]

#slide("Prinzip", "Erst der Monitor")[
  #text(15pt)[Jeder Node spiegelt jede Loop-Nachricht an den Laptop. Der Monitor zeigt, *welche Transaktion, Stufe und welcher Node* fehlschlägt — weitere Tools nur, wo er blind ist.]
  #v(0.3em)
  #grid(columns: (1fr, 1fr, 1fr, 1fr), rows: (4.4cm,), gutter: 0.45cm,
    card([Logic Analyzer], [Monitor-Zeiten sind *selbstberichtet*; die Laser-Enable-Leitung sieht er nicht.], accent: amber),
    card([Sequenzcheck], [Der Mirror-Stream ist *best effort* — Lücken werden markiert, kein Fehlalarm.]),
    card([Aufnahme + Replay], [Tritt ein Fehler nur *einmal* auf, kann er erneut abgespielt werden.], accent: navy),
    card([Fault Injection], [Jeder Fehler der Fehlerhypothese wird *provoziert*, ≥ 10-mal pro Fall.], accent: laser),
  )
  #v(0.5em)
  #let chip(t) = box(fill: navy, radius: 4pt, inset: (x: 9pt, y: 6pt), text(12pt, fill: white, weight: "bold", t))
  #align(center)[Mirror-Stream: #h(0.3em) #chip[immer an, auch in der Demo] #h(0.3em) #chip[wartet nie] #h(0.3em) #chip[kein Rückkanal]]
]

#slide("Debugging-Reihenfolge", "Von der Transaktion bis zur Nachricht")[
  #let step(n, name, c) = rect(width: 100%, height: 2.3cm, fill: c, radius: 5pt, inset: 5pt)[
    #align(center + horizon, text(fill: white)[#text(20pt, weight: "bold", n) \ #text(12.5pt, weight: "bold", name)])]
  #let note(t) = align(center, text(10.5pt, fill: grey, t))
  #grid(columns: (1fr,) * 7, gutter: 0.18cm,
    grid.cell(colspan: 5, align(center, text(10pt, weight: "bold", fill: navy)[LIVE AM SYSTEM])),
    grid.cell(colspan: 2, align(center, text(10pt, weight: "bold", fill: teal)[OFFLINE])),
    step("1", "Transaktion", navy), step("2", "Stufe", navy), step("3", "Trust Check", laser),
    step("4", "Node", navy), step("5", "Nachricht", navy), step("6", "Replay", teal), step("7", "Isolieren", teal),
    note[Alarme, Incident-Liste], note[Stufenzeit vs. Budget], note[Analyzer vs. Monitor], note[Health, EventLog],
    note[gesendet vs. empfangen], note[Fehler reproduzieren], note[Node-Simulator],
  )
  #v(0.8em)
  #rect(fill: soft, radius: 6pt, inset: 12pt, width: 100%)[
    #set text(14pt)
    *Trust Check vor der Detailsuche:* Weichen Analyzer und Monitor um mehr als die Uhrenpräzision π ab, stimmen Uhr oder Zeitstempel nicht — das wird repariert, bevor man weitersucht.]
]

#slide("Timing oder Funktion?", "Das Replay entscheidet")[
  #text(14pt, fill: grey)[Deterministisches Replay: gleiche Logik, gleiche aufgezeichnete Inputs, ohne Echtzeit.]
  #v(0.2em)
  #grid(columns: (1fr, 1fr, 1fr), rows: (4.6cm,), gutter: 0.45cm,
    card([Auch im Replay falsch], [→ *funktionaler Fehler* \ #v(0.2em) Modultest, offline, ohne Hardware], accent: teal),
    card([Nur live falsch], [→ *Timing-Fehler* \ #v(0.2em) live andere Inputs oder Reihenfolge: veraltete Observation, abgelaufenes Target], accent: amber),
    card([Richtig, aber zu spät], [→ *Timing-Verletzung* \ #v(0.2em) Stufe → Node → Nachricht verfolgen (Schritte 2–5)], accent: laser),
  )
]
""")
    return "".join(p)


# English version: every German text of the deck and the diagram, replaced in order.
EN = [
    ("WINTERSEMESTER 2026", "WINTER TERM 2026"),
    ("Debugging der Integrationstests", "Debugging the integration tests"),
    ("Meilenstein M3 · Debugging-Konzept", "Milestone M3 · debugging concept"),
    ("17. November 2026", "17 November 2026"),
    ("Kamera 0", "Camera 0"), ("Kamera 1", "Camera 1"), ("Kamera 2", "Camera 2"),
    (">isoliert<", ">isolated<"), ("empfängt nur", "receives only"),
    (">Trace-Pins<", ">trace pins<"), (">Mirror-Stream<", ">mirror stream<"),
    ("Trace-Pins, Laser-Enable, Kill-Switch", "trace pins, laser enable, kill switch"),
    ('#slide("Integrationstest", "Testaufbau")', '#slide("Integration test", "Test bench")'),
    ('"Demo-Aufbau", "Raspberry Pi 3 B+ · isolierter Switch"', '"demo setup", "Raspberry Pi 3 B+ · isolated switch"'),
    ('"2 Zeitachsen", "PTP-Uhr ↔ Analyzer, über Sekundenmarken abgeglichen"', '"2 timelines", "PTP clock ↔ analyzer, aligned by the full-second marks"'),
    ('#slide("Prinzip", "Erst der Monitor")', '#slide("Principle", "The monitor first")'),
    ("Jeder Node spiegelt jede Loop-Nachricht an den Laptop. Der Monitor zeigt, *welche Transaktion, Stufe und welcher Node* fehlschlägt — weitere Tools nur, wo er blind ist.",
     "Every node mirrors every loop message to the laptop. The monitor shows *which transaction, stage and node* fails — further tools only where it is blind."),
    ("[Monitor-Zeiten sind *selbstberichtet*; die Laser-Enable-Leitung sieht er nicht.]",
     "[Monitor times are *self-reported*; it can't see the laser-enable line.]"),
    ("card([Sequenzcheck], [Der Mirror-Stream ist *best effort* — Lücken werden markiert, kein Fehlalarm.])",
     "card([Sequence check], [The mirror stream is *best effort* — gaps are marked, no false alarms.])"),
    ("card([Aufnahme + Replay], [Tritt ein Fehler nur *einmal* auf, kann er erneut abgespielt werden.]",
     "card([Record + replay], [If a failure occurs only *once*, it can be played back again.]"),
    ("[Jeder Fehler der Fehlerhypothese wird *provoziert*, ≥ 10-mal pro Fall.]",
     "[Every fault of the fault hypothesis is *provoked*, ≥ 10 times per case.]"),
    ("Mirror-Stream: #h(0.3em) #chip[immer an, auch in der Demo] #h(0.3em) #chip[wartet nie] #h(0.3em) #chip[kein Rückkanal]",
     "Mirror stream: #h(0.3em) #chip[always on, also in the demo] #h(0.3em) #chip[never waits] #h(0.3em) #chip[no path back]"),
    ('#slide("Debugging-Reihenfolge", "Von der Transaktion bis zur Nachricht")', '#slide("Debugging order", "From the transaction down to one message")'),
    ("[LIVE AM SYSTEM]", "[LIVE ON THE SYSTEM]"),
    ('step("1", "Transaktion", navy), step("2", "Stufe", navy)', 'step("1", "Transaction", navy), step("2", "Stage", navy)'),
    ('step("5", "Nachricht", navy)', 'step("5", "Message", navy)'), ('step("7", "Isolieren", teal)', 'step("7", "Isolate", teal)'),
    ("note[Alarme, Incident-Liste], note[Stufenzeit vs. Budget], note[Analyzer vs. Monitor], note[Health, EventLog]",
     "note[alarms, incident list], note[stage time vs budget], note[analyzer vs monitor], note[health, event log]"),
    ("note[gesendet vs. empfangen], note[Fehler reproduzieren], note[Node-Simulator]",
     "note[sent vs received], note[reproduce the failure], note[node simulator]"),
    ("*Trust Check vor der Detailsuche:* Weichen Analyzer und Monitor um mehr als die Uhrenpräzision π ab, stimmen Uhr oder Zeitstempel nicht — das wird repariert, bevor man weitersucht.",
     "*Trust check before the detailed search:* if analyzer and monitor differ by more than the clock precision π, the clock or the timestamps are wrong — fix that before searching further."),
    ('step("3", "Trust Check", laser)', 'step("3", "Trust check", laser)'),
    ('#slide("Timing oder Funktion?", "Das Replay entscheidet")', '#slide("Timing or function?", "The Replay decides")'),
    ("[Deterministisches Replay: gleiche Logik, gleiche aufgezeichnete Inputs, ohne Echtzeit.]",
     "[Deterministic Replay: same logic, same recorded inputs, no real time.]"),
    ("card([Auch im Replay falsch], [→ *funktionaler Fehler* \\ #v(0.2em) Modultest, offline, ohne Hardware]",
     "card([Wrong in the Replay too], [→ *functional error* \\ #v(0.2em) module test, offline, no hardware]"),
    ("card([Nur live falsch], [→ *Timing-Fehler* \\ #v(0.2em) live andere Inputs oder Reihenfolge: veraltete Observation, abgelaufenes Target]",
     "card([Wrong only live], [→ *timing error* \\ #v(0.2em) live used other inputs or order: stale observation, expired target]"),
    ("card([Richtig, aber zu spät], [→ *Timing-Verletzung* \\ #v(0.2em) Stufe → Node → Nachricht verfolgen (Schritte 2–5)]",
     "card([Right, but too late], [→ *timing violation* \\ #v(0.2em) follow stage → node → message (steps 2–5)]"),
]


def to_english(text: str) -> str:
    """Apply the EN table to deck or diagram source; only entries found in the text are applied."""
    for de, en in EN:
        text = text.replace(de, en)
    return text


def check_english() -> None:
    """Stop if a German text has no English entry (every entry must match somewhere)."""
    src = title_slide() + deck() + bench_svg()
    missing = [de for de, _ in EN if de not in src]
    if missing:
        sys.exit(f"EN table out of date, not found: {missing}")


def main() -> int:
    check_english()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    svg = OUT_DIR / "bench.svg"
    rc = 0
    base = f"Slides_Debugging_{TEAM.replace(' ', '_')}"
    for stem, lang in ((base, "de"), (base + "_EN", "en")):
        conv = to_english if lang == "en" else (lambda t: t)
        svg.write_text(conv(bench_svg()), encoding="utf-8")
        typ, pdf = OUT_DIR / f"{stem}.typ", OUT_DIR / f"{stem}.pdf"
        typ.write_text(conv(deck()), encoding="utf-8")
        res = subprocess.run(["typst", "compile", "--creation-timestamp", STAMP, str(typ), str(pdf)])
        if res.returncode == 0:
            typ.unlink()
            print(pdf)
        rc |= res.returncode
    svg.unlink()
    return rc


if __name__ == "__main__":
    sys.exit(main())

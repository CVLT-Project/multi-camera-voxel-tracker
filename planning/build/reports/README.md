# DRS reports

| Milestone | Report | Generator |
| --- | --- | --- |
| M2 — requirements and Gate 1 | `output/pdf/DRS_M2_Voxel_Camera_with_Laser_Tracking.pdf` | `build_m2_report.py` |
| M3 — architecture, transactions, integration tests, Gate 2 | `output/pdf/DRS_M3_Voxel_Camera_with_Laser_Tracking.pdf` | `build_m3_report.py` (state of Gate 2 in `GATE2_STATE`) |
| M3 — integration test debugging concept | `output/pdf/DRS_M3_Voxel_Camera_with_Laser_Tracking_Debugging.pdf` | `build_m3_debug_report.py` (separate file by team decision; reads the debugging section of the concept) |
| M3 — team contracts (camera, control, laser team) | `output/pdf/DRS_M3_Voxel_Camera_with_Laser_Tracking_Contract_<Team>.pdf` | `build_m3_contracts.py` (one PDF per team from the team contracts in the architecture; copies in module specifications, messages, stage budgets, requirements and increments) |
| Class presentation — requirements and system design (2 × 7 slides, 16:9) | `output/pdf/Slides_Requirements_<team>.pdf`, `output/pdf/Slides_System_Design_<team>.pdf` | `build_class_slides.py` (hand-picked summary; uses the system font Noto Sans, embedded in the PDF) |
| Class presentation — debugging concept (5 slides, 16:9, German and English) | `output/pdf/Slides_Debugging_<team>.pdf`, `output/pdf/Slides_Debugging_<team>_EN.pdf` | `build_debug_slides.py` (follows the system-design deck; reuses the style of `build_class_slides.py`) |

The first M2 version (6 November 2026) was removed from the repository on 12 November 2026 to avoid confusion with the current report; it remains in the Git history (commit `172288b`, `planning/build/reports/reference/DRS_M2_Vocel_camera_2026-11-06.pdf`).

## Regenerate

From the repository root:

```sh
python3 planning/build/reports/build_m2_report.py
```

Dependencies: Python 3 (standard library only) and the [Typst](https://typst.app) CLI (tested with 0.15). The generator uses only Typst's embedded fonts (`--ignore-system-fonts`), so the PDF looks the same on every machine.

## Sources

- `../VLT/20-concept.md` — purpose, terms, requirements (§3, §5), reaction matrix, given components (§6), out of scope (§7), decisions and open questions (§8), the lecture checklist (§9).
- `../decisions/ADR-VLT-*.md` — title, state and rationale of each decision.

Team name, milestone, report date and Gate 1 date are constants at the top of the generator. `lecture-sources.md` lists the lecture pages ([L]) used as sources in the requirements.

## Report rules checked

- One PDF per team, named `DRS_<milestone>_<team>.pdf`; the title page shows team, milestone and date.
- No student names anywhere (text, headers, PDF metadata); owners are sub-team roles.
- Self-contained: no references to repository files or concept sections; tables and extracts are copied into the report.
- Requirement IDs (F-VLT-n, NF-VLT-n), decision IDs (ADR-VLT-n) and open-question IDs (OQ-n) are used throughout.
- Gate 1: the team's approval and its date, without approver names.

`build_m3_report.py` reuses the M2 helpers, takes its tables from the architecture, transaction, integration-test and consistency-review sections of the concept, and draws the architecture diagram as SVG. Set `GATE2_STATE` to the approval date once the team has approved the design.

`build_m3_contracts.py` checks that every module of the module tree has exactly one owning team (except the FaultInjector, which goes to the first team that finishes its node slice) and stops otherwise. The contracts name code paths under `src/`, because they are working documents for the teams, not graded reports.

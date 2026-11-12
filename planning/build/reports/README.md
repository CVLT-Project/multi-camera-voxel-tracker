# DRS reports

| Milestone | Report | Generator |
| --- | --- | --- |
| M2 — requirements and Gate 1 | `output/pdf/DRS_M2_Voxel_Camera_with_Laser_Tracking.pdf` | `build_m2_report.py` |

The first M2 version (6 November 2026) is kept unchanged as `reference/DRS_M2_Vocel_camera_2026-11-06.pdf`.

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

For M3, the same generator can be extended to produce `DRS_M3_<team>.pdf`.

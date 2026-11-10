# M2 requirements report

The current PDF is `output/pdf/DRS_M2_Vocel_camera.pdf`. Its 6 November source version is retained unchanged as `reference/DRS_M2_Vocel_camera_2026-11-06.pdf`.

Regenerate from the repository root with Python and the dependencies below (the Codex bundled Python runtime can also be used):

```sh
python planning/build/reports/build_m2_report.py
```

On Windows the generator uses Arial when available; other platforms use ReportLab's bundled Vera fonts.

Sources: `../VLT/20-concept.md`, `../VLT/camera-profile.json`, `../VLT/camera-reference-plan.json`, the observation/calibration schemas and the decisions linked there. `lecture-sources.md` identifies the lecture/checklist pages. The report reads current revisions and numeric profile values; changes still require a consistency review of the explanatory text.

The report is a requirements draft, not measured performance or Gate 1 approval. Raspberry Pi 3 is fixed; camera-model selection/driver binding and hardware qualification are pending. Galvo electrical verification and the global approval gate are separate open items.

Visual QA renders are retained under `tmp/pdfs/` as review intermediates. No network services or cloud storage are needed. Python dependencies for generation and QA are `reportlab`, `pypdf`, `Pillow` and `pypdfium2`; these are available in the Codex bundled runtime.

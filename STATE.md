# Current state

Updated 2026-10-18, America/New_York.

Active objective: implement the revised object-visibility-aware AIMv2/DINOv2 project, execute a real pilot, and prepare reviewable milestone evidence. Canvas remains read-only; do not submit work or send messages to the instructor without user authorization.

Completed: isolated project environment; official model code/checkpoints pinned; both encoders pass actual MPS inference benchmarks; complete Pet mirror verified against official filenames/labels/splits, plus 100 original JPEG byte comparisons; protocol written before dataset predictions; 14 empty-foreground annotation exclusions recorded before sampling; 25 mask/data safety tests pass.

Pilot v1: 1,480 train / 370 validation / 185 test images, 37 breeds. AIMv2 then DINOv2 run sequentially. Read `results/pilot_v1/*-run.log` and actual prediction files before claiming completion. No classifier or dataset metrics should be inferred from model benchmark success.

Next: complete both inference runs, analyze paired predictions, visually inspect figures, write bilingual evidence report, and verify repository tracking excludes data/weights/private Canvas material. Private remote repository created and verified: https://github.com/Bensssonxx/comp669-object-visibility. Existing HTTPS Git credential helper works; use it for fetch/push. The GitHub connector cannot see this private repository, and SSH auth is unavailable, so do not retry those routes or create new credentials.

## Exact continuation

Active unified-exec session at initial handoff: 66991. It runs AIMv2 then DINOv2, then `scripts/analyze.py`, with per-stage logs in results/pilot_v1. Check logs and process state before launching a duplicate. AIMv2 clean train/val extraction and validation-only probe selection have completed; occluded-image inference is in progress. Do not infer test scores from the clean validation score. Models each have 4,255 evaluation rows, including 185 clean, 3,330 standard masked and 740 diagnostic paired rows.

When both prediction CSVs exist, run:

```bash
.venv/bin/python scripts/analyze.py --run pilot_v1
.venv/bin/python scripts/audit_run.py --require-predictions
.venv/bin/python scripts/qualitative_cases.py
.venv/bin/python scripts/write_reports.py
```

Inspect actual figures and CSVs before presenting any findings. The report generator writes reports/PILOT_REPORT_ZH.md and reports/PILOT_REPORT_EN.md from saved tables and rejects missing models. Review its interpretation rather than delivering it unchecked. Update this status with actual completion and commit/push the new results to the private remote. Main code/protocol were published in ab35577; later commits add audits and report generation.

Do not edit src/occlusion_visibility while a run is active: its hash binds resumable feature caches. Analysis, documentation and script changes outside src do not affect encoder features. Cache files are ignored by Git. If an encoder stage fails, read the exact error, fix the narrow issue, preserve completed cached batches and rerun only that stage. Never silently change checkpoint, config or test set.

The official trimaps cover all downloaded images, but head bounding-box XMLs cover only the official training subset. None of the 185 pilot test images has a head box. Do not claim head-visibility matching or generate that metric without new annotations. Foreground-pixel matching is not semantic-part matching.

Milestone: Part 2 slides due Oct 21, 2026 at 11:59 PM ET; presentation Oct 22, 12 minutes plus 1–2 minutes Q&A. Must include preliminary results, analysis, additional experiments, repository link and AI-use disclosure. These dates were checked live in this chat on Oct 18.

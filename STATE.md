# Current state

Updated 2026-10-18, America/New_York.

Active objective: implement the revised object-visibility-aware AIMv2/DINOv2 project, execute a real pilot, and prepare reviewable milestone evidence. Canvas remains read-only; do not submit work or send messages to the instructor without user authorization.

Completed: isolated project environment; official model code/checkpoints pinned; both encoders pass actual MPS inference benchmarks; complete Pet mirror verified against official filenames/labels/splits, plus 100 original JPEG byte comparisons; protocol written before dataset predictions; 14 empty-foreground annotation exclusions recorded before sampling; 26 mask/data/statistical tests pass.

Pilot v1: 1,480 train / 370 validation / 185 test images, 37 breeds. AIMv2 then DINOv2 run sequentially. Read `results/pilot_v1/*-run.log` and actual prediction files before claiming completion. No classifier or dataset metrics should be inferred from model benchmark success.

Next: complete both inference runs, analyze paired predictions, visually inspect figures, write bilingual evidence report, and verify repository tracking excludes data/weights/private Canvas material. Private remote repository created and verified: https://github.com/Bensssonxx/comp669-object-visibility. Existing HTTPS Git credential helper works; use it for fetch/push. The GitHub connector cannot see this private repository, and SSH auth is unavailable, so do not retry those routes or create new credentials.

## Exact continuation

Original session 66991 finished AIMv2 and then terminated because this host stopped processing editable-install source paths for the next Python process. AIMv2 predictions are complete and audited: 4,255 rows, clean test 173/185 (93.5%); equal-area object-contrast high/low 172/185 vs 134/185; matched-pair correctness flips 22/185 (11.9%). These are AIMv2-only preliminary results, not a cross-model conclusion.

Current live DINOv2 unified-exec session: 56446. It was started separately with explicit PYTHONPATH, and has finished clean train/val extraction plus validation-only classifier selection. It is now evaluating the same 4,255 conditions. Poll this specific handle or inspect its log before restarting. The original shell pipeline's automatic analysis will NOT run because it exited. After DINOv2 completes, run the commands below manually.

Source `scripts/env.sh` from the project root in Bash or zsh before direct Python commands. It sets project/AIM source paths and a writable Matplotlib cache. Verified in both shells. `scripts/run_pilot.sh` includes it. The new setup also explicitly lists pandas, which was previously present only in the host system environment.

When both prediction CSVs exist, run:

```bash
.venv/bin/python scripts/analyze.py --run pilot_v1
.venv/bin/python scripts/audit_run.py --require-predictions
.venv/bin/python scripts/qualitative_cases.py
.venv/bin/python scripts/write_reports.py
.venv/bin/python scripts/prepare_slide_assets.py
```

Inspect actual figures and CSVs before presenting any findings. The report generator writes reports/PILOT_REPORT_ZH.md and reports/PILOT_REPORT_EN.md from saved tables and rejects missing models. Review its interpretation rather than delivering it unchecked. Update this status with actual completion and commit/push the new results to the private remote. Main code/protocol were published in ab35577; later commits add audits and report generation.

Do not edit src/occlusion_visibility while a run is active: its hash binds resumable feature caches. Analysis, documentation and script changes outside src do not affect encoder features. Cache files are ignored by Git. If an encoder stage fails, read the exact error, fix the narrow issue, preserve completed cached batches and rerun only that stage. Never silently change checkpoint, config or test set.

The official trimaps cover all downloaded images, but head bounding-box XMLs cover only the official training subset. None of the 185 pilot test images has a head box. Do not claim head-visibility matching or generate that metric without new annotations. Foreground-pixel matching is not semantic-part matching.

Milestone: Part 2 slides due Oct 21, 2026 at 11:59 PM ET; presentation Oct 22, 12 minutes plus 1–2 minutes Q&A. Must include preliminary results, analysis, additional experiments, repository link and AI-use disclosure. These dates were checked live in this chat on Oct 18.

## Milestone deck work

`scripts/build_milestone.mjs` builds a 12-slide local PPTX with actual statistics and speaker notes. `scripts/prepare_slide_assets.py` requires both completed models plus the integration audit and qualitative-case selection. The presentation skill was read and the required artifact-operation marker was run once (create, 1 PPTX). `.build-presentation/node_modules` links to the bundled runtime. Copy the builder into that directory and run the bundled Node from the project root after slide_data.json exists. First run uses MILESTONE_VERSION=v1; repairs must use a new version and retain the old candidate/final output. Rendered previews and validation receipt stay in .build-presentation/v1. Inspect all slides individually. No PPTX or generated report has been delivered yet.

A pre-prediction coverage check found no common object-visibility bin with >=5 images in all four standard patterns at 50% visible image area. The 25% and 75% budgets have limited overlap. Report this non-estimability explicitly. The same-image square-occluder pairs are a separate design and do not establish that the original four-pattern comparison is fully controlled. The report generator and slide notes preserve this limitation.

Both classifiers selected the upper C-grid boundary (C=10) using clean validation only. Treat probe-regularization and pooling sensitivity as limitations; do not rank general encoder quality from this diagnostic setup.

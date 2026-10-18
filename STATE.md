# Current state

Updated 2026-10-18, America/New_York. This file is the handoff for continuing the project.

## Active extension v2

User authorized continuing the research. An independent follow-up protocol is fixed in `docs/EXTENSION_V2_PROTOCOL.md` before new predictions. Config: `configs/extension_v2.json`. Standalone extension scripts preserve all pilot core/cache hashes.

Samples prepared and audited: 740 new official test images (20 per breed), disjoint from all pilot IDs/bytes; 185 unused official trainval images with head-box annotations form a separate auxiliary cohort. All 740 primary images have foreground-matched pairs. 159/185 auxiliary images meet the predeclared head-contrast/foreground-match constraints; no thresholds were relaxed. There are 16,361 actual conditions per model, gray128 and black0 fills, one shared clean input. Frozen original C=10 probes are saved under `results/extension_v2/probes/` for standalone reproduction.

Run from a GPU-enabled host, not the restricted sandbox: `bash scripts/run_extension.sh`. It validates inputs, executes both encoders, audits every prediction, and computes seven prespecified paired contrasts plus secondary diagnostics. For interrupted runs resume finite-batch caches; do not modify `scripts/extension_v2.py`, core sources, config, manifests or probes while running. `scripts/analyze_extension.py` can be refined independently of the encoder cache. No extension conclusions before both models finish and audits pass. Pre-prediction commit 815a33b was pushed before inference. Live unified-exec session: 2187, running `/usr/bin/caffeinate -i bash scripts/run_extension.sh` on the GPU-enabled host. Inspect `results/extension_v2/run.log` and finite cache rows before any restart. AIMv2 is first, then DINOv2. The runner ends with audit and `analyze_extension.py`; separately run `report_extension.py` after both complete. The 36 focused tests pass. Do not claim any extension result from preparation or benchmark output.

## Delivered scope

The initial research-and-milestone preparation is complete: a real two-model pilot, audited predictions, reproducible source/data/model pins, bilingual reports, and a reviewed 12-slide presentation with speaker notes. This does not mean the final course project or instructor approval is complete. Canvas remains read-only; no assignment was submitted and no instructor was contacted.

Private repository: https://github.com/Bensssonxx/comp669-object-visibility. Arrange instructor access before formal submission. HTTPS Git credential helper works; use `GIT_TERMINAL_PROMPT=0 git push origin main`. The GitHub connector cannot see this private repository; SSH auth is unavailable. Do not retry those routes or create credentials.

## Read and present

- `reports/PILOT_REPORT_ZH.md`: actual results, interpretation and limitations.
- `reports/PILOT_REPORT_EN.md`: copy-ready technical report for instructor review.
- `milestone/COMP669_Object_Visibility_Milestone_v4.pptx`: final reviewed 12-slide deck. Native text/tables, embedded scientific figures, clickable repository link, source notes and AI-use disclosure.
- `milestone/SPEAKER_NOTES_EN.md`: approximately 1,230 spoken words; personally rehearse before presenting.
- `milestone/QA_EN.md`: likely questions and bounded answers.
- `docs/PRESENTATION_VALIDATION.json`: package/layout/import/font checks; all final previews inspected; representative LibreOffice renders checked. Microsoft PowerPoint itself was not tested.

Part 2 slides are due Oct 21, 2026 at 11:59 PM ET; presentation Oct 22, 12 minutes plus 1–2 minutes Q&A. These dates were checked live on Canvas in this chat on Oct 18. Required preliminary results, analysis, future experiments, code link and AI disclosure are in the deck. Check Canvas again before actual submission.

## Executed pilot

Oxford-IIIT Pet, 37 breeds, official trainval/test split. 1,480 clean train / 370 clean validation / 185 test images (5 per breed), seed 6692026. Fourteen empty-foreground annotations excluded before sampling. Official metadata agrees with the pinned image mirror, including 100 original-JPEG byte comparisons. Both frozen L/14 encoders use normalized mean patch features and clean-only logistic probes; clean validation selected C=10 for both. Shared 224x224 full-frame pixels and RGB128 masking; no token removal.

Both models completed all 4,255 test conditions (8,510 prediction rows total). No inference process remains active. All stored mask/coverage values were recomputed; saved classifiers reproduce every label and target probability. Twenty-six focused protocol/statistical tests pass.

Main observation: at 25% visible image area, random masking yields AIMv2 32.6% / DINOv2 70.6%, whereas center masking yields 90.8% / 62.7%. This ordering crossover is descriptive, not a pretraining-mechanism claim. Clean scores are 93.5% / 83.2%. Object-contrast paired accuracy gaps are 20.5 pp / 11.9 pp; matched-foreground correctness flips are 11.9% / 9.7%. Full intervals and joint outcomes are in the report/tables.

There is no eligible common foreground-coverage bin across all four standard patterns at 50% image area. Do not claim a reliable adjusted comparison there. Same-image square-occluder pairs are a separate design. Matching foreground area does not match parts, texture or background; all 185 test images lack head-box XMLs. The selected illustrative case is post hoc, with its selection rule stored.

A post-hoc C=10/100/1000 sensitivity supplement reports every tested value without replacing the main results. The random/center ordering persists; flip rates change. This does not establish general encoder rankings or resolve pooling sensitivity.

## Reproduce and extend

```bash
bash scripts/setup_reference.sh
bash scripts/run_pilot.sh
```

The numeric reference is macOS arm64, Python 3.12.2, Conda Pillow 10.4.0 and libjpeg 9e, pinned in `environment.reference.yml`. Pip Pillow of the same version uses another JPEG decoder and differs numerically; the failed smoke check is preserved in `docs/FRESH_ENCODER_SMOKE.json`. A separate reference environment matches all 2,035 selected decoded RGB/trimap fingerprints; first 8 conditions per encoder replay with zero feature difference. This is not a second full independent experiment. See `docs/REFERENCE_REPLAY_CHECK.json`.

Source `scripts/env.sh` before direct Python commands; it handles hosts that suppress editable-install paths. Default runner interpreter is `.reference-conda/bin/python`. Input hashes must pass before cache reuse. The documented setup and full runner were replayed successfully in the reference environment with verified feature caches; probes, analyses and audits were rerun (docs/PIPELINE_REPLAY_CHECK.json). Data, weights, vendor source, feature caches, environments and build previews are ignored by Git. Do not edit `src/occlusion_visibility` to reuse v1 caches: source hashes bind them. New experimental settings require a new run name and untouched v1 evidence.

Next scientific priorities: enlarge the held-out test set and vary fill color, then improve matching support and analyze semantic parts using valid annotations. Before any expansion, personally review the motivation, protocol and implementation, and ask the instructor whether this scope addresses the original feedback. No claim of first-ever foreground/background analysis or causal prefix-attention effect is supported.

# Object visibility and occlusion robustness

**COMP 669 research project, Boshen Yang.** A reproducible, annotation-aware evaluation of frozen AIMv2-L/14 and DINOv2-L/14. The question is whether location/pattern comparisons change when we explicitly measure how much of the target foreground remains visible.

Pilot v1 is complete for both models. Start with the [Chinese report](reports/PILOT_REPORT_ZH.md), [English report](reports/PILOT_REPORT_EN.md), and [milestone materials](milestone/README_ZH.md). The final reviewed presentation is `milestone/COMP669_Object_Visibility_Milestone_v4.pptx`.

This is a course-scale replication and extension of prior occlusion work, including [Intriguing Properties of Vision Transformers / PatchDrop](https://arxiv.org/abs/2105.10497). We do not claim that separating foreground/background occlusion is new, nor that cross-model differences identify the effect of prefix attention.

## Read first

- [Direction in Chinese](docs/DIRECTION_ZH.md): motivation and contribution boundaries.
- [Pre-inference protocol](docs/PROTOCOL.md): sampling, masks, probe fitting, matched pairs and uncertainty.
- [Source revisions and hashes](docs/SOURCES.json): official code/checkpoints and dataset provenance.
- [Related work](docs/RELATED_WORK.md): what already exists and what this project adds.
- [AI assistance disclosure](docs/AI_USE.md).
- [Current project status](STATE.md).

## Pilot design

Oxford-IIIT Pet, 37 breed classes, official trainval/test split. Sample 40 clean training, 10 clean validation and 5 test images/class. Models remain frozen. Mean final patch features are L2 normalized; a separate logistic classifier is trained per model on clean training images only, with C selected on clean validation images.

Both models receive the same 224x224 RGB pixels, the same 14-pixel patch grid, and the same visible regions. Masked pixels are filled with RGB 128 before ImageNet normalization. Tokens are not removed. Full-frame resize preserves the annotated scene but distorts aspect ratio; published model scores using other preprocessing are not reproduced here.

Evaluate clean images and 75%/50%/25% visible area under prefix, suffix, center-nearest and three deterministic random masks. Record actual foreground/background visibility, excluding unknown trimap pixels. Additionally, use annotation-selected, same-image square-occluder pairs with either contrasting or approximately matched foreground visibility. These are diagnostic oracle conditions, not a proposed deployment method.

## Reproduce

Python 3.12 is the tested version. **The numeric reference is macOS arm64 with Pillow 10.4.0 built against libjpeg 9e**, pinned in `environment.reference.yml`. A plain pip Pillow wheel uses libjpeg-turbo and produces different JPEG pixels despite the same Pillow version. We verified all 2,035 selected RGB/trimap inputs against a second reference environment and replayed 8 conditions per encoder with zero feature difference; see [reference replay evidence](docs/REFERENCE_REPLAY_CHECK.json). This is not a second full experiment.

Apple MPS is the pilot device; for CUDA or CPU create a separately versioned experiment. Assets require about 5 GB including extracted data and checkpoints, plus the environment. Install Conda before running the reference setup.

```bash
bash scripts/setup_reference.sh
bash scripts/run_pilot.sh
```

The runner defaults to `.reference-conda/bin/python`. `PROJECT_PYTHON` can select another interpreter, but the canonical decoded-input hash check must pass before any feature cache is reused. `scripts/setup.sh` remains a generic pip environment for code development and tests, not exact replication of the reference JPEG decoding.

Or run steps separately (reference interpreter):

```bash
source scripts/env.sh
.reference-conda/bin/python scripts/download_assets.py
.reference-conda/bin/python scripts/import_pet_mirror.py
.reference-conda/bin/python -m occlusion_visibility.experiment prepare
.reference-conda/bin/python scripts/verify_preprocessing.py
.reference-conda/bin/python scripts/preview_inputs.py
.reference-conda/bin/python -m occlusion_visibility.experiment run --model aimv2
.reference-conda/bin/python -m occlusion_visibility.experiment run --model dinov2
.reference-conda/bin/python scripts/analyze.py --run pilot_v1
.reference-conda/bin/python scripts/audit_run.py --require-predictions
.reference-conda/bin/python scripts/qualitative_cases.py
.reference-conda/bin/python scripts/write_reports.py
```

Feature extraction resumes at saved finite batches. Caches are bound to configuration, row order, image/annotation hashes, encoder source and checkpoint hash. The runner separately checks every decoded input against the stored RGB/trimap fingerprints; the legacy v1 cache metadata alone does not identify the JPEG decoder. A changed experiment must use a new run name. Stop on checksum mismatch, input-fingerprint mismatch, missing foreground, cross-split duplicate image bytes, stale cache or non-finite features; never silently substitute a smaller checkpoint.

## Outputs

`results/pilot_v1/` contains the configuration, sample manifest, annotation exclusions, shared mask metadata, raw predictions, probe validation choices, accuracy summaries, paired diagnostics, object-visibility counts, exploratory common-support standardization, analysis audit and figures. Large image/checkpoint/feature files are ignored by Git and downloaded by the scripts. Dataset images remain attributed to their original owners and are not redistributed in the repository.

Example input figures contain research-use excerpts from the Oxford-IIIT Pet dataset, attributed to [Parkhi et al. and original image owners](https://www.robots.ox.ac.uk/~vgg/data/pets/); full raw image files are not tracked. Model code and weights retain their upstream licenses. No license grant to third-party assets is implied by this project.

Bootstrap confidence intervals resample original test images, not individual masks, and are conditional on the fixed learned probes. The pilot has only 5 test images/class. Equal foreground area is not equal semantic information; parts, texture, shape and background can still differ. Masked-image robustness does not establish robustness to real occluders. Pretraining data overlap is unknown.

`scripts/env.sh` sets explicit project/AIM source paths for Python hosts that suppress editable-install `.pth` processing, and gives Matplotlib a writable project-local cache. No global interpreter or authentication settings are changed.

## Validation

```bash
.reference-conda/bin/python -m pytest -q
```

Tests cover exact visible budgets, annotation semantics, pixel preservation, deterministic shared masks, diagnostic-pair area/caliper constraints and unsafe archive rejection. Integration audits check official filenames/labels/splits, cross-model mask identity and image-level sampling. The documented setup and full runner were replayed successfully in the reference environment using verified feature caches; see [pipeline replay scope](docs/PIPELINE_REPLAY_CHECK.json). This replay refits probes and reruns analyses, without claiming a second full feature-extraction experiment.

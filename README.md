# Object visibility and occlusion robustness

**COMP 669 research project, Boshen Yang.** A reproducible, annotation-aware evaluation of frozen AIMv2-L/14 and DINOv2-L/14. The question is whether location/pattern comparisons change when we explicitly measure how much of the target foreground remains visible.

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

Python 3.12 is the tested version. `requirements.txt` pins the two core encoder libraries to the versions actually used; package availability on another host must be checked. Apple MPS is the pilot device; for CUDA or CPU create a versioned config changing `device` and `run_name`. Assets require about 5 GB including extracted data and checkpoints, plus the environment.

```bash
bash scripts/setup.sh
bash scripts/run_pilot.sh
```

Or run steps separately:

```bash
.venv/bin/python scripts/download_assets.py
.venv/bin/python scripts/import_pet_mirror.py
.venv/bin/python -m occlusion_visibility.experiment prepare
.venv/bin/python scripts/preview_inputs.py
.venv/bin/python -m occlusion_visibility.experiment run --model aimv2
.venv/bin/python -m occlusion_visibility.experiment run --model dinov2
.venv/bin/python scripts/analyze.py --run pilot_v1
.venv/bin/python scripts/audit_run.py --require-predictions
.venv/bin/python scripts/write_reports.py
```

Feature extraction resumes at saved finite batches. Caches are bound to configuration, row order, image/annotation hashes, encoder source and checkpoint hash. A changed experiment must use a new run name. Stop on checksum mismatch, missing foreground, cross-split duplicate image bytes, stale cache or non-finite features; never silently substitute a smaller checkpoint.

## Outputs

`results/pilot_v1/` contains the configuration, sample manifest, annotation exclusions, shared mask metadata, raw predictions, probe validation choices, accuracy summaries, paired diagnostics, object-visibility counts, exploratory common-support standardization, analysis audit and figures. Large image/checkpoint/feature files are ignored by Git and downloaded by the scripts. Dataset images remain attributed to their original owners and are not redistributed in the repository.

Example input figures contain research-use excerpts from the Oxford-IIIT Pet dataset, attributed to [Parkhi et al. and original image owners](https://www.robots.ox.ac.uk/~vgg/data/pets/); full raw image files are not tracked. Model code and weights retain their upstream licenses. No license grant to third-party assets is implied by this project.

Bootstrap confidence intervals resample original test images, not individual masks, and are conditional on the fixed learned probes. The pilot has only 5 test images/class. Equal foreground area is not equal semantic information; parts, texture, shape and background can still differ. Masked-image robustness does not establish robustness to real occluders. Pretraining data overlap is unknown.

## Validation

```bash
.venv/bin/python -m pytest -q
```

Tests cover exact visible budgets, annotation semantics, pixel preservation, deterministic shared masks, diagnostic-pair area/caliper constraints and unsafe archive rejection. Integration audits check official filenames/labels/splits, cross-model mask identity and image-level sampling.

# Object visibility and occlusion robustness

**COMP 669 research project, Boshen Yang.** A reproducible, annotation-aware evaluation of frozen AIMv2-L/14 and DINOv2-L/14. The question is whether location/pattern comparisons change when we explicitly measure how much of the target foreground remains visible.

Pilot v1 and follow-up v2 are complete. Start with the latest [follow-up report](reports/EXTENSION_V2_EN.md) and the [code guide](docs/CODE_GUIDE.md). The updated [milestone presentation](milestone/COMP669_Object_Visibility_Milestone_v6.pptx) incorporates follow-up v2, with [English speaker notes](milestone/SPEAKER_NOTES_EN_v6.md) and [questions to prepare for](milestone/QA_EN_v5.md). It has 12 main slides and two hidden backups, with a 1,006-word conversational speech estimated at 10.7-11.8 minutes. See the [milestone index](milestone/README.md). The original [pilot report](reports/PILOT_REPORT_EN.md) and v4 pilot deck remain preserved.

This is a course-scale replication and extension of prior occlusion work, including [Intriguing Properties of Vision Transformers / PatchDrop](https://arxiv.org/abs/2105.10497). We do not claim that separating foreground/background occlusion is new, nor that cross-model differences identify the effect of prefix attention.

## Where the important code lives

| Read first | Purpose |
| --- | --- |
| [Code guide](docs/CODE_GUIDE.md) | Guided reading order and one-result walkthrough |
| [Core package](src/occlusion_visibility/) | Images, masks, frozen encoders and pilot classifier fitting |
| [Follow-up runner](scripts/extension_v2.py) | New-image sampling, two fills, head-region pairs and frozen-probe predictions |
| [Follow-up analysis](scripts/analyze_extension.py) | Image-level aggregation, paired contrasts and bootstrap intervals |
| [Reports](reports/README.md) | Current findings and the preserved pilot report |
| [Milestone files](milestone/README.md) | Current presentation, speaker notes and questions |

Repository documentation, report generators and presentation text use English. Local study translations are kept outside the Git repository.

## Completed follow-up v2

Start with the [follow-up report](reports/EXTENSION_V2_EN.md). Both encoders completed 16,361 conditions each (32,722 predictions), and every saved prediction/probability passed reconstruction audit. The design and samples were fixed before new predictions in commit `815a33b`: [extension protocol](docs/EXTENSION_V2_PROTOCOL.md).

The 740 new official-test images exclude all pilot IDs and exact image bytes. The original C=10 clean-trained probes stay frozen. At 25% image visibility, gray center scores are AIMv2 87.0% / DINOv2 63.1%, and gray random scores are 33.6% / 69.6%. With black fill they are 87.3% / 61.9% and 30.4% / 62.2%. All four component model differences retain their directions under the seven-contrast family-wise intervals. Fill still changes accuracy; stable ordering does not mean equivalent fills.

A separate cohort of 185 unused official-trainval images supplies head boxes absent from the downloaded official-test annotations. 159 meet the fixed head-region contrast constraints, with foreground visibility matched within 3 pp. Their results are exploratory and describe changing content bundles, not a pure head effect or the cause of the main crossover. Do not pool this cohort into the official-test estimate.

Evidence: [integration audit](results/extension_v2/integration_audit.json), [numeric review](results/extension_v2/report_numeric_review.json), [source provenance](results/extension_v2/provenance_audit.json), [925-input replay](docs/EXTENSION_INPUT_REPLAY_CHECK.json), and [independent 24-condition encoder replay](docs/EXTENSION_ENCODER_REPLAY_CHECK.json). Both replayed encoders matched with zero feature difference. This is not another full independent experiment.

Run on a GPU-enabled macOS arm64 host from a fresh clone:

```bash
bash scripts/setup_reference.sh
source scripts/env.sh
.reference-conda/bin/python scripts/download_assets.py
.reference-conda/bin/python scripts/import_pet_mirror.py
.reference-conda/bin/python scripts/verify_extension_provenance.py
bash scripts/run_extension.sh
.reference-conda/bin/python scripts/report_extension.py
```

The tracked small extension probes allow this without first refitting pilot classifiers. Valid existing assets are reused. Source/core code and all pilot results remain unchanged. Extension feature caches and upstream model weights are ignored by Git. Exact-byte disjointness does not establish absence of visual near duplicates or pretraining overlap.

For statistical reanalysis using committed predictions, the following commands need no model weights or raw images. They use the stored completed-run audit and independently recalculate tables; they do not rerun the model integration audit:

```bash
source scripts/env.sh
.reference-conda/bin/python scripts/analyze_extension.py
.reference-conda/bin/python scripts/report_extension.py
```

## Read first

- [Code guide](docs/CODE_GUIDE.md): reading order, main functions, C selection, data flow and result trace.
- [Research direction](docs/PROJECT_DIRECTION.md): motivation and contribution boundaries.
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

# Protocol frozen before pilot predictions (2026-10-18)

## Question and scope

Does accounting for visible foreground change how we interpret location/pattern differences in frozen AIMv2 and DINOv2 classification? This is a course-scale replication and extension, not a claim that foreground/background occlusion is new. We do not identify the causal effect of prefix attention or of pretraining objectives.

The main experimental unit is the original image. Multiple masks and random repetitions are repeated measurements of that image, not independent test samples.

## Dataset

Oxford-IIIT Pet: 37 breed labels and pixel-level trimaps. Use the official trainval/test lists. Deterministically sample 40 training, 10 validation and 5 test images per class with seed 6692026: 1,480 / 370 / 185 images. Test images are never used to choose classifier hyperparameters, mask rules or thresholds. This is an exploratory pilot on a single fine-grained dataset, not an ImageNet result. Pretraining overlap is unknown.

Annotations: 1=foreground (pet), 2=background, 3=unclassified. Object visibility is the number of visible label-1 pixels divided by all label-1 pixels. Background visibility uses label-2 pixels only. Label 3 is excluded from these denominators and its full-image fraction is recorded. These masks describe the foreground in the photographed image, not the complete amodal animal or its discriminative information.

Pre-inference annotation audit: exclude invalid trimap labels or zero foreground after the shared resize, before deterministic sampling in each official split. Record all exclusions in `annotation_exclusions.json`. This rule was added after the first data preparation encountered an empty-foreground annotation, before any dataset predictions were generated.

Resize the entire RGB image to 224x224 with bicubic interpolation and the trimap with nearest neighbor. This intentionally preserves the full frame instead of cropping the animal; aspect-ratio distortion is a declared limitation and common to both encoders. No geometric transform follows masking. Fill hidden RGB pixels with (128,128,128) before ImageNet normalization. No patch tokens are deleted and no model-native mask interface is invoked. This does not reduce inference compute.

## Models and probe

- AIMv2-L/14, official 224 checkpoint pinned to `ac764a25c832c7dc5e11871daa588e98e3cdbfb7`.
- DINOv2-L/14 without register tokens, official checkpoint.
- Official upstream code revisions and checkpoint hashes are recorded in SOURCES.json.
- Both frozen; mean of final normalized patch features, L2 normalization, then a separate multinomial logistic regression. Pooling is deliberately shared; it is not either model's published best evaluation recipe.
- Select C from [0.01, 0.1, 1, 10] using only clean held-out validation accuracy. Tie breaks favor the first (smaller) C. Train on clean training features only. No test-label tuning, no occlusion training, no refit on validation.
- Float32 on Apple MPS, batch 8. Record actual library versions and benchmark. All evaluations use identical raw masked RGB inputs and shared masks.

## A. Standard visibility patterns

100% clean; 75%, 50%, 25% visible. On a 16x16 patch grid use:

- prefix: first k patches in raster order;
- suffix: last k patches;
- center: k patches nearest the geometric center, stable row-major distance ties;
- random: exactly k patches, 3 predetermined repeats. The image ID/repeat determines a stable seed shared by both models. The same ordering makes masks nested across fractions.

All budgets are exact. The center rule is a compact, center-nearest region rather than a guaranteed rectangular block. Prefix/suffix at these budgets are mainly top/bottom spatial conditions, not attention manipulations.

Report accuracy, loss relative to clean accuracy, and accuracy retention, alongside actual object-visibility distributions. Random repetitions are averaged within image before aggregation or bootstrap. Report paired cross-model differences on the identical images, not unpaired uncertainty.

## B. Same-image equal-shape/area diagnostic pairs

Generate 25 candidate 8x8-patch square occluders at a fixed 5x5 placement grid. Every candidate hides exactly 25% of the image, leaving 75% visible. Select pairs using annotations only, before looking at any model outputs:

1. **Object contrast:** maximum and minimum object visibility among candidates. Same image, same occluder shape and area. This is a diagnostic contrast, not a deployable annotation-free method; content/part/location changes are part of the intervention.
2. **Visibility matched:** object-visibility difference <=0.03 and placement distance >=4 patches. Among eligible pairs choose the most separated centers, then the closest visibility, then deterministic name tie breaks. Do not relax the caliper when a sample has no eligible pair. Report eligibility rate and characteristics of excluded images.

Report high-minus-low accuracy and paired uncertainty for object-contrast pairs. For visibility-matched pairs report correctness discordance, class-prediction disagreement, and absolute target-probability change. An average signed difference can cancel heterogeneous effects, so it is not sufficient to establish invariance. Equal object area does not imply equal object parts, shape, background, texture or semantic information; residual differences do not uniquely identify a spatial mechanism.

## C. Exploratory visibility stratification

Within each visible-image budget, bin object visibility into [0,.2), [.2,.4), [.4,.6), [.6,.8), [.8,1]. For random masks average outcomes/coverage within image first. Show counts. Standardize pattern means only over bins with at least 5 images in every compared pattern, using weights proportional to the minimum bin count across patterns. Report discarded support and do not extrapolate into empty bins. This is descriptive composition adjustment, not causal mediation. The matched and unmatched subsets have different populations; never compare their raw scores as a treatment effect.

## Uncertainty and interpretation

Use 2,000 bootstrap resamples of original images, carrying all their repeated conditions together. CIs describe test-image sampling conditional on this trained probe/checkpoint; they omit probe-training, dataset and checkpoint uncertainty. Pilot estimates can be wide. No significance threshold or required winner. No claim that differences vanish merely because a CI includes zero.

Expansion decisions follow the pilot: larger held-out test set, second fill color, original aspect ratio/letterbox or crop sensitivity, second dataset, alternative feature pooling. New analyses must be labeled exploratory or placed in a versioned protocol.

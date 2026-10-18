# Extension v2 protocol, fixed before extension predictions

Date: October 18, 2026. This follow-up was motivated by pilot_v1 observations, so it is not an independently conceived preregistered study. The design and endpoints below are committed before predictions on the new images. Pilot evidence stays unchanged.

## Purpose and fixed choices

Check whether the pilot's AIMv2-versus-DINOv2 ordering crossover at 25% visible image area repeats on previously unevaluated images, and whether it is sensitive to replacing RGB128 gray with RGB0 black. Reuse exactly the original C=10 clean-trained logistic heads (save their bytes and hashes), frozen encoder checkpoints, feature pooling, full-frame resize, JPEG decoder and pixel-mask rules. No further fitting, C selection or test-driven mask selection occurs. This evaluates these particular encoder/probe systems, not their best possible performance or causal pretraining mechanisms.

## Samples

Primary set: 20 previously unevaluated official test images per breed, 740 total. Exclude every pilot manifest image ID and exact image byte hash, invalid/empty foreground annotations, and exact duplicates, before deterministic sampling with seed 6692027. Report all exclusions. Pixel-level near duplicates and pretraining overlap remain unknown. Do not pool pilot test observations into this follow-up estimate.

Annotation audit found zero head-box XMLs for the entire official test split. A separate auxiliary set therefore samples 5 unused official trainval images per breed, 185 total, with valid head-box XML and nonempty foreground inside the box. They are disjoint in IDs and exact image bytes from pilot training/validation/test and the primary set. They are not used to train or select any parameter. Keep this auxiliary analysis separate because its source split and annotation eligibility differ from the primary set.

## Primary inputs

One clean input per image; at 25% image visibility, prefix, suffix, center-nearest, and three original deterministic random masks. Reuse the pilot seed (6692026) for mask generation so the mask algorithm is unchanged; the new seed controls image sampling only. Also reuse the annotation-only equal-square-area object-contrast and foreground-matched pair designs: occlude 25% of the image, identical shape/area, foreground visibility caliper 0.03 and center separation >=4 patches. If a pair is ineligible, record that fact, do not loosen thresholds.

Each masked condition is evaluated with both fills, gray128 and black0; masks and retained RGB pixels are identical across fills and models. Clean images are computed once. Expected primary rows are 740 x 21 = 15,540 per model if all foreground-matched pairs exist; report actual eligibility. Filling pixels is not token deletion and not a natural occluder.

## Auxiliary head-region diagnostic

The XML is a head bounding box, not a precise head segmentation. Convert PASCAL 1-based inclusive coordinates to a rectangle in the shared 224x224 resized frame using pixel-center membership, and intersect it with label-1 foreground. This is the **head-region foreground proxy**. Foreground outside the rectangle is a complementary body-region proxy; do not call either an exact semantic-part annotation.

Among the same 25 square occluders, seek a pair with foreground visibility difference <=0.03, centers >=4 patches apart, and head-region visibility difference >=0.20. Choose maximum head-region contrast, then minimum foreground gap, then maximum distance, with deterministic name ties. Selection uses annotations only. Keep all selected images in the eligibility denominator even if no eligible pair exists. Evaluate clean plus eligible high-head/low-head versions with both fills. Report eligibility, head/body/background coverage, both individual accuracies, paired accuracy difference and correctness flips. This changes a content bundle: it does not isolate the causal effect of the head alone.

## Endpoints and uncertainty

Primary: for each fill, paired AIM-minus-DINO accuracy differences under center and random masks (random repeats averaged within each original image), and their difference: (AIM-DINO)_center - (AIM-DINO)_random. Check signs of the two component differences; a nonzero interaction alone does not establish opposite rankings. Report the black-minus-gray change in this interaction. These seven prespecified contrasts are descriptive with individual 95% intervals; also provide family-wise 95% Bonferroni intervals over the seven contrasts. No binary significance rule or favorable-color selection. Use 10,000 breed-stratified image bootstrap resamples, carrying every repeat, fill, mask and model for a sampled image together. Equal breed weights match the balanced 20-per-breed design. Family-wise intervals require tail quantiles 0.0035714/0.9964286 for seven contrasts.

Secondary: all pattern accuracies, drops from clean, object-contrast paired differences, foreground-matched correctness flips/class changes/joint correctness, within-image fill differences and cross-model flip-rate differences. Auxiliary head-region paired differences and visibility distributions are exploratory. Bootstrap within each breed among eligible images, retaining only represented breeds and reporting their counts; do not imply equal representation of all 37 breeds after eligibility filtering. Bootstrap intervals condition on the fixed probes/checkpoints and do not cover training, dataset, checkpoint or protocol-selection uncertainty.

## Interpretation and stopping

Run every specified condition regardless of interim scores. Do not stop after obtaining a favorable direction. Preserve raw predictions, shared masks, resized-input fingerprints, frozen probes, source/checkpoint hashes, cache binding and audit. Cache only finite feature batches. No replacement images after viewing predictions. A failure of replication or strong fill dependence is a substantive outcome. The four-pattern 50%-visibility common-support problem from pilot_v1 is not solved by this 25%-visibility follow-up. No new causal prefix-attention or novelty claim is supported.

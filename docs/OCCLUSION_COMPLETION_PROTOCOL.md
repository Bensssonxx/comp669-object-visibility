# Occlusion completion protocol

Fixed November 4, 2026, before new-condition or new-cohort predictions. Motivated by previously inspected results; this is not a preregistered study.

## Fixed systems and runs

Reuse the extension-v2 frozen encoders and original C=10 clean-trained probes, final-patch mean pooling, 224-pixel full-frame resize, original libjpeg decoder, float32, and pixel fills 128/0. Mask seed remains 6692026. No fitting, tuning, or replacement based on predictions.

`completion_primary`: the original 740 primary images, adding 50% and 75% visible-image budgets for prefix, suffix, center, and three random repeats. Existing 25%/clean predictions are combined only in analysis after identity checks. New condition IDs include budget and mask bytes. Record exact source hashes. Replay the first original batch of eight conditions for each model before inference; require feature agreement within absolute 1e-5 and unchanged predicted classes. Use original batch size 8 for reproducibility.

`completion_head`: 185 unused official-trainval images, five per breed, with valid head-box/foreground intersection. Exclude IDs and byte hashes from all pilot and extension manifests, and duplicate byte hashes within the new pool. Choose deterministically in sorted breed/ID order with seed 6692031, before predictions. Keep every sampled image for standard-pattern analysis, regardless of head-pair eligibility. Record all exclusions and split origin. Run clean plus all four patterns at 25/50/75% visibility, both fills, three random repeats. Add the original head-contrast square rule (foreground gap <=.03, centers >=4 patches apart, head-coverage gap >=.20); ineligible images stay in the denominator, without replacement.

The head ROI is box-intersected foreground, not anatomical segmentation. Body proxy is its foreground complement. Raw image, annotation, transformed-input, checkpoint, probe and condition hashes bind each run. Preserve existing results. A preparation lock records this protocol and runner hashes before any new predictions.

## Analyses fixed now

The primary and new-head cohorts are always separate. Existing auxiliary head-selected pairs remain separate from both. Standard-pattern random repeats are averaged within original image for headline means and main foreground-bin plots. Bin individual random conditions with weight 1/3 as a supplementary check; never treat repeats as independent images.

Show accuracy and paired AIM-minus-DINO differences by pattern, fill, and image budget. Show foreground-conditioned accuracy in 20-percentage-point bins, and 10-point bins as sensitivity; rightmost bin includes 100%. Use the actual within-bin mean as x coordinate. Suppress cells with fewer than five unique images, flag 5–19 as sparse, and report counts and breed composition. No interpolation across missing bins. Descriptive bin means weight images equally; all-image means on balanced cohorts equal the equal-breed estimand. Existing head-pair overall estimates weight represented breeds equally, matching the prior report.

Bootstrap original images within breed, jointly retaining all model/fill/pattern/repeat conditions, 10,000 resamples (seed 6692032); paired model differences use shared draws. Bin estimates are ratio estimates from resampled numerator/denominator totals over the entire cohort. Report empty-resample frequency; suppress bootstrap intervals if fewer than 95% of draws have a nonzero denominator. Intervals are conditional on fixed systems; ordinary curve intervals are pointwise and exploratory, not simultaneous evidence across all bins.

For the primary model-ranking question, define 12 center/random AIM-minus-DINO contrasts (3 budgets x 2 fills x 2 patterns). Report pointwise and approximate Bonferroni simultaneous 95% intervals across these 12 contrasts; inspect both component signs to describe reversal. Pattern-by-model interaction is supplementary and is not enough by itself to establish reversal. Repeat the same descriptive family separately in the new head cohort, without pooling evidence or treating it as a global familywise guarantee. Report all directions.

Common-support summaries use only bins containing at least five images in all four patterns, with fixed weights proportional to the minimum pattern count in each retained bin. Report the bins, retained fractions, and within-bin foreground distributions. Recompute this descriptively for 20- and 10-point bins; do not choose the favorable resolution. These are composition-standardized associations, not causal adjustment; no uncertainty-based claims from these standardized point estimates.

For head analysis, report head/body/background/total foreground coverage, eligibility, paired accuracy changes and correctness flips. Existing diagnostic examples use the prior annotation-selected image; outcome-selected examples are explicitly illustrative. On the new cohort, report accuracy split into prespecified head-visibility thirds within foreground bins and fixed pattern/budget/fill; suppress sparse cells using the same rule. These cells may be uninformative if coverage is too narrow. Do not relax criteria after predictions or claim an isolated head effect. No new learned failure predictor is required in this completion pass.

## Interpretation

New primary conditions are an extension on known images, not independent replication. The new annotated cohort was not used to fit the frozen classifiers, but comes from a different official source split and has annotation-based eligibility. Neither cohort identifies the effect of pretraining, prefix attention, or precise anatomical parts. Empty overlap, weak region associations, or a disappearing reversal are substantive results.

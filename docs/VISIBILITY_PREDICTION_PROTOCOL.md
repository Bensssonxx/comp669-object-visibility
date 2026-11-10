# Exploratory prediction of occlusion failures

Date: 2026-10-22. This plan is written before fitting the diagnostic models below, after inspecting the existing study results and available fields. This is post-hoc exploratory reanalysis, not preregistration or a new independent image experiment. Existing encoder weights, breed classifiers, inputs and predictions remain unchanged.

## Question

Do annotation-based visibility measurements improve predictions of an encoder/classifier system's correctness on images excluded from fitting the diagnostic predictor? Does mask pattern still add information after these measurements? Can head-region visibility add information beyond total foreground coverage in the separate auxiliary cohort?

## Data and units

Use the two immutable `results/extension_v2/*_predictions.csv` files, checked against `conditions.csv`. Analyze encoders separately. Never supply target probability, predicted class, clean-image correctness, breed label or image identity as predictor inputs. Breed labels are used only to balance folds and aggregation.

Primary analysis: all 740 official-test images, standard masked conditions only, 25% image visibility, four patterns and two fills. Weight each random repeat by 1/3 so each image/pattern/fill contributes equally. Exclude clean images and square-pair suites from this analysis.

Auxiliary analysis: eligible head-contrast pairs only, 159 images from the separate auxiliary cohort, 75% image visibility, two placements and two fills. Exclude clean images and ineligible images. Each image contributes equally within its breed, and represented breeds receive equal weight. Head-region visibility is foreground intersected with a head bounding box, not precise semantic head segmentation. Neither cohort is pooled with the other.

## Predictors fixed before fitting

Fit separate regularized logistic correctness predictors with a fixed quadratic basis for numeric inputs (each input and its square), standardized using fitting images only. Add categorical pattern indicators where specified. Use an intercept, L2 penalty strength 1 on non-intercept standardized coefficients, and all training sample weights normalized to sum to the number of fitting images. No parameter selection on held-out outcomes. Fixed penalties 0.1 and 10 are reported as sensitivity checks, without selecting a favorable penalty. Use a NumPy Newton solver with line search, convergence checks and numerical gradient tests.

Feature sets:

- `budget`: image visible fraction and fill color.
- `foreground`: budget plus foreground visible fraction.
- `content`: foreground plus background visible fraction, original object fraction and unknown annotation fraction.
- `mask`: budget plus pattern category in the primary cohort, or square center x/y in the auxiliary cohort.
- `mask_foreground`: mask plus foreground visibility.
- `mask_content`: mask plus the content measurements.
- Auxiliary only: `foreground_head`, `content_head`, and `mask_content_head` add head-region visibility to the corresponding feature set.

At each cohort's fixed image-area budget, image visible fraction is constant. The baseline therefore measures what fill and average correctness alone can predict. Background, foreground and original composition are related by geometry; added prediction does not estimate independent causal effects. Square centers come from the recorded mask, not model outputs. Pair role high/low and selection metadata are excluded.

## Validation and metrics

Use five outer folds defined on unique original images, balanced within breed with a deterministic shuffle (seed 6692028). All masks, fills, random repeats and both encoders for an image share its fold. Every diagnostic prediction is out of fold. This is image-grouped cross-validation of a post-hoc analysis of already evaluated images, not untouched external validation.

Primary metric: weighted Brier loss for predicting binary correctness, lower is better. Also report log loss, ROC AUC (descriptive), and threshold-0.5 accuracy. Averaging conditions within image and then breeds defines the estimand. Predicting correctness is distinct from predicting the animal breed or improving breed-classification accuracy.

Compute paired per-image Brier improvement for these six comparisons in each cohort: foreground over budget, content over foreground, mask over budget, mask_foreground over mask, mask_content over mask_foreground, mask_content over content. Auxiliary adds three: foreground_head over foreground, content_head over content, mask_content_head over mask_content. Report individual 95% intervals and Bonferroni simultaneous 95% intervals across the 30 planned encoder/cohort comparisons, using 10,000 bootstrap resamples of images within breed. These intervals condition on the fitted cross-validation predictions and omit predictor-refitting and analysis-selection uncertainty. Folds are dependent, so do not treat per-fold scores as independent experimental replications. Penalty sensitivity is descriptive only.

Also report out-of-fold errors and observed-versus-predicted model accuracy gaps for each primary mask/fill. This is a descriptive check, not causal mediation or a percentage of the crossover explained.

## Reporting and limitations

Report every feature set and contrast regardless of direction. A small, unstable or absent improvement is a substantive finding. No claims of novel foreground/background analysis, isolated head effects, causal pretraining effects, deployment without annotations, generalization to unseen breeds, or real-occluder robustness. This first pass does not extend standard masks to 50% or 75% visibility and does not change feature pooling. A future untouched cohort would be needed for confirmatory testing after freezing this diagnostic pipeline.

Primary references: [PatchDrop](https://arxiv.org/html/2105.10497v3), [background dependence](https://arxiv.org/abs/2006.09994), [grouped cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data), [Brier loss](https://scikit-learn.org/stable/modules/model_evaluation.html#brier-score-loss).

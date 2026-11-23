# Follow-up v2: new-image replication, fill sensitivity and head-region diagnostics

The design was motivated by pilot_v1 and committed before predictions on the follow-up images (815a33b). It is an internally fixed follow-up, not an independently conceived external preregistration. The pilot evidence is preserved.

The point-estimate ordering crossover repeats under both fills: AIMv2 is higher under center visibility, DINOv2 under random visibility. The family-wise intervals for all four component model differences are on their corresponding sides of zero. This describes specified frozen encoder/probe systems and pixel interventions, not a pretraining mechanism.

## Design

Primary cohort: 740 previously unevaluated official-test images, 20 per breed, disjoint in IDs and image-byte hashes from all pilot training/validation/test samples. The original C=10 clean-trained classifiers remain fixed. No fitting or parameter selection uses follow-up images. At 25% visible image area, evaluate prefix, suffix, center and three random masks; repeat with gray128 and black0 fills on identical retained pixels. Also repeat the same-image square-occluder diagnostics, which instead retain 75% image area.

Auxiliary cohort: 185 unused official-trainval images with head boxes, separate from primary and pilot samples. 159/185 meet fixed head-contrast eligibility: foreground-visibility gap <=3 pp, center distance >=4 patches, head-region gap >=20 pp. Thresholds were not relaxed. All official-test images lack the downloaded head XMLs, so this auxiliary cohort cannot be presented as official-test head analysis.

There are 32,722 actual predictions (16,361 per model). Random repetitions are averaged within original images. Main estimates use equal breed weights and 10,000 within-breed image bootstrap resamples, retaining all paired conditions together. Seven fixed primary contrasts receive individual and approximate family-wise 95% Bonferroni intervals. Pair/auxiliary results use equal represented-breed weights after eligibility; raw joint counts are retained separately. Intervals condition on the frozen probes/checkpoints.

Input examples below follow manifest order and annotation eligibility, without looking at model outcomes. Cyan annotations are not encoder inputs.

![Actual shared inputs](../results/extension_v2/figures/design_inputs.png)

## Primary results, 25% visible image area

| Model | Fill RGB | Clean | Prefix 25% | Suffix 25% | Center 25% | Random 25% |
| --- | --- | --- | --- | --- | --- | --- |
| aimv2 | 128 | 93.5% | 46.6% | 28.6% | 87.0% | 33.6% |
| dinov2 | 128 | 84.6% | 26.6% | 26.5% | 63.1% | 69.6% |
| aimv2 | 0 | 93.5% | 44.5% | 28.5% | 87.3% | 30.4% |
| dinov2 | 0 | 84.6% | 28.8% | 29.3% | 61.9% | 62.2% |

| Pattern | Mean foreground visible | Median foreground visible | Original images |
| --- | --- | --- | --- |
| prefix | 9.6% | 8.1% | 740 |
| suffix | 15.3% | 12.6% | 740 |
| center | 62.5% | 60.2% | 740 |
| random | 25.0% | 25.0% | 740 |

![Primary accuracy](../results/extension_v2/figures/primary_accuracy.png)

| Contrast | Estimate pp | 95% CI pp | Family-wise 95% CI pp |
| --- | --- | --- | --- |
| aim_minus_dino_center_fill128 | 23.9 | [20.8, 27.0] | [19.9, 28.2] |
| aim_minus_dino_random_fill128 | -36.1 | [-38.9, -33.3] | [-39.9, -32.3] |
| center_minus_random_model_difference_fill128 | 60.0 | [56.0, 64.0] | [54.5, 65.6] |
| aim_minus_dino_center_fill0 | 25.4 | [22.4, 28.4] | [21.4, 29.3] |
| aim_minus_dino_random_fill0 | -31.8 | [-34.7, -28.9] | [-35.7, -28.0] |
| center_minus_random_model_difference_fill0 | 57.2 | [53.3, 61.2] | [51.7, 62.5] |
| black_minus_gray_model_by_pattern_interaction | -2.8 | [-6.4, 0.9] | [-7.9, 2.3] |

![Paired contrasts](../results/extension_v2/figures/primary_contrasts.png)


An interaction alone does not establish opposite rankings: inspect the two component model differences. Black-minus-gray measures fill sensitivity of the model-by-pattern interaction.

Despite equal 25% image visibility, mean foreground visibility is 62.5% under center and 25.0% under random masks. Coverage is shared across both models and fills; random repeats are averaged within image. These patterns retain different content distributions. This follow-up does not estimate how much foreground or parts explain their score differences, and does not identify a content-controlled pure position effect.

Stable ordering does not imply fill invariance. For random visibility, black-minus-gray accuracy is -3.2 pp for AIMv2 (95% CI [-5.0, -1.4]) and -7.4 pp for DINOv2 (95% CI [-9.2, -5.7]). The black-minus-gray change in the model-by-pattern interaction is -2.8 pp (individual 95% CI [-6.4, 0.9]). That interval crossing zero does not establish equivalence of fills. All eight fill contrasts are retained in fill_sensitivity.csv.

## Same-image paired diagnostics

A/B means more/less foreground for object_contrast, fixed selected locations for visibility_matched, and more/less head-region visibility for head_contrast. These square occluders hide 25% of the image, unlike the primary 25%-visible conditions.

| Cohort | Pair | Model | Fill | n | A breed-macro accuracy | B breed-macro accuracy | A-B pp [95% CI] | Correctness flips | Class changes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auxiliary_head | head_contrast | aimv2 | 0 | 159 | 92.4% | 75.5% | 17.0 [11.3, 22.7] | 20.8% | 22.1% |
| auxiliary_head | head_contrast | aimv2 | 128 | 159 | 92.4% | 73.2% | 19.2 [13.5, 24.9] | 23.0% | 24.4% |
| auxiliary_head | head_contrast | dinov2 | 0 | 159 | 81.3% | 72.9% | 8.4 [4.1, 12.7] | 13.2% | 14.3% |
| auxiliary_head | head_contrast | dinov2 | 128 | 159 | 82.9% | 72.4% | 10.5 [5.8, 15.1] | 14.6% | 15.1% |
| primary | object_contrast | aimv2 | 0 | 740 | 92.3% | 67.3% | 25.0 [22.0, 28.1] | 25.8% | 29.1% |
| primary | visibility_matched | aimv2 | 0 | 740 | 85.0% | 90.9% | -5.9 [-8.1, -3.8] | 10.3% | 11.4% |
| primary | object_contrast | aimv2 | 128 | 740 | 92.8% | 67.2% | 25.7 [22.7, 28.8] | 25.9% | 28.6% |
| primary | visibility_matched | aimv2 | 128 | 740 | 84.9% | 90.1% | -5.3 [-7.6, -3.0] | 10.7% | 12.0% |
| primary | object_contrast | dinov2 | 0 | 740 | 83.1% | 65.5% | 17.6 [14.7, 20.4] | 20.5% | 25.7% |
| primary | visibility_matched | dinov2 | 0 | 740 | 77.7% | 80.0% | -2.3 [-4.3, -0.3] | 9.1% | 12.0% |
| primary | object_contrast | dinov2 | 128 | 740 | 82.6% | 67.2% | 15.4 [12.6, 18.2] | 20.0% | 24.7% |
| primary | visibility_matched | dinov2 | 128 | 740 | 78.9% | 80.1% | -1.2 [-3.1, 0.8] | 8.5% | 11.2% |

Head-region visibility averaged 83.0% vs 12.7%; foreground visibility averaged 55.9% vs 55.4%. These coverage means are unweighted image means. The complementary body-region proxy averages 35.9% vs 85.7% visible.

![Head-region diagnostic](../results/extension_v2/figures/head_region_diagnostic.png)

The head-region proxy intersects the head bounding rectangle with annotated foreground; it is not exact head segmentation. Approximate foreground-area matching still changes parts, texture and background together. This is a content-bundle diagnostic, not the isolated causal effect of the head. It also does not establish that head visibility explains the primary model-ordering crossover: the cohorts and mask designs differ. Correctness-flip rates alone cannot rank robustness: two wrong predictions yield no correctness flip.

## Motivation and limits

The motivation is to determine whether evaluation conditions alter model ordering and what image-area or foreground-area summaries omit. New images and a second fill test two limitations of the pilot. Same-image comparisons hold image identity, shape/area, model and probe fixed; fill comparisons additionally hold retained pixels fixed. Different model pretraining remains uncontrolled, so no causal prefix-attention attribution follows. The pilot's lack of shared foreground coverage at 50% image visibility remains unresolved.

This remains one dataset, two synthetic constant fills, one pooling recipe and fixed probes. Exact-byte independence is not proof of no visual near duplicates or pretraining overlap. Auxiliary eligibility/source differs from the primary cohort and must not be pooled into its estimate. The contribution is reproducible replication and diagnostic extension, not first-ever foreground/background analysis. Source protocol, raw predictions, probes, input fingerprints and audits accompany the results. Codex assistance is disclosed in docs/AI_USE.md. No Canvas upload or instructor message was performed.

Evidence: [protocol](../docs/EXTENSION_V2_PROTOCOL.md), [primary contrasts](../results/extension_v2/primary_contrasts.csv), [paired statistics](../results/extension_v2/paired_summary.csv), [integration audit](../results/extension_v2/integration_audit.json).

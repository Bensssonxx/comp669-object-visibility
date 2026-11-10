"""Write the English diagnostic report from saved results, without refitting."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'results/visibility_prediction_v1'
with (BASE / 'metrics.csv').open() as f:
    metrics = list(csv.DictReader(f))
with (BASE / 'contrasts.csv').open() as f:
    contrasts = list(csv.DictReader(f))
with (BASE / 'pattern_predictions.csv').open() as f:
    pattern_rows = list(csv.DictReader(f))
assert json.loads((BASE / 'verification.json').read_text())['passed']


def loss(cohort, model, variant, penalty=1):
    return float(next(r['brier'] for r in metrics if r['cohort'] == cohort and r['model'] == model
                      and r['variant'] == variant and float(r['penalty']) == penalty))


def relative(model, base, extra):
    a, b = loss('primary', model, base), loss('primary', model, extra)
    return (a - b) / a * 100


lines = ['# Predicting classification failures from visible content',
'''Exploratory reanalysis, October 22, 2026. The original experiments and presentation results are unchanged. This analysis trains small predictors of whether each saved model response is correct. It does not change AIMv2, DINOv2, their breed classifiers or their classification accuracies.

The main finding is that foreground coverage and mask pattern provide complementary predictive information in this diagnostic model. Animal area helps even after the pattern is known. The available area measurements also leave useful information associated with pattern. Head-region measurements give a more limited result in the separate auxiliary sample.''',
'## Design',
'''The primary sample contains 740 original images under four masking patterns and two fills, all at 25% image visibility. Random repeats share the total weight of one pattern. The auxiliary sample contains the 159 eligible head-contrast images at 75% image visibility. Its pairs were selected to have similar total foreground area but contrasting head-region visibility. The samples are analyzed separately.

Five folds are allocated to original images within breed. Every version of an image stays in the same fold, for both encoders. The correctness predictor is fitted on four folds and evaluated on the fifth. Predictors use annotation coverage and mask descriptors, never image identity, breed, clean correctness, target probability, predicted class or pair role. Numeric predictors use a fixed quadratic basis and regularized logistic regression. The main penalty is fixed at 1; penalties 0.1 and 10 are descriptive sensitivity checks.

The main score is Brier loss: the mean squared error of predicted probability of correctness. Lower is better. A reduction in this score is not an increase in animal-breed accuracy. Conditions are averaged within original image and then within breed. The primary budget-only baseline has no variation in visible fraction, so it mainly predicts average correctness by fill. The comparison against a pattern-aware baseline is therefore particularly useful.''',
'## Primary results',
'Brier loss from out-of-fold predictions:',
'| Diagnostic inputs | AIMv2 | DINOv2 |\n| --- | ---: | ---: |']
for variant, name in [('budget', 'Visible image fraction and fill'), ('foreground', 'Add animal visibility'),
                      ('content', 'Add background visibility and original composition'), ('mask', 'Visible image fraction, fill and mask pattern'),
                      ('mask_foreground', 'Pattern plus animal visibility'), ('mask_content', 'Pattern plus all area/composition measurements')]:
    lines.append(f'| {name} | {loss("primary", "aimv2", variant):.4f} | {loss("primary", "dinov2", variant):.4f} |')
lines += [f'''Adding animal visibility to the budget-only baseline reduces Brier loss by {relative('aimv2', 'budget', 'foreground'):.1f}% for AIMv2 and {relative('dinov2', 'budget', 'foreground'):.1f}% for DINOv2. More importantly, adding it to a predictor that already knows the masking pattern reduces loss by {relative('aimv2', 'mask', 'mask_foreground'):.1f}% and {relative('dinov2', 'mask', 'mask_foreground'):.1f}%, respectively. These are relative reductions in correctness-prediction error.

Conversely, adding the mask pattern to the area/composition predictor improves predictions for both encoders. This is residual predictive information in the specified diagnostic model, not proof of a pure position mechanism. Its quadratic feature basis may miss other nonlinear content relationships.''',
'Paired Brier improvements for the main comparisons (positive is better):',
'| Comparison | Model | Improvement | Individual 95% interval | Simultaneous 95% interval |\n| --- | --- | ---: | --- | --- |']
for base, extra in [('budget', 'foreground'), ('mask', 'mask_foreground'), ('content', 'mask_content')]:
    for model in ['aimv2', 'dinov2']:
        r = next(r for r in contrasts if r['cohort'] == 'primary' and r['model'] == model and r['base'] == base and r['extra'] == extra)
        lines.append(f'| {base} to {extra} | {model} | {float(r["brier_improvement"]):.4f} | [{float(r["ci_low"]):.4f}, {float(r["ci_high"]):.4f}] | [{float(r["simultaneous_ci_low"]):.4f}, {float(r["simultaneous_ci_high"]):.4f}] |')
lines += ['''Intervals use 10,000 image resamples within breed. The simultaneous intervals cover the 30 planned encoder/cohort contrasts approximately using Bonferroni tail quantiles. They condition on the saved cross-validation predictions and omit refitting and analysis-selection uncertainty. All planned contrasts, including weaker and negative results, are in `contrasts.csv`.

Adding the full context group beyond foreground plus pattern gives much smaller gains: the simultaneous intervals include zero for both encoders. Thus, the strongest incremental evidence is for foreground coverage beyond pattern, rather than a separate background effect.''',
'## Relation to the ranking reversal',
'''For gray fill, the observed AIM-minus-DINO accuracy gaps are +23.9 percentage points for center and -36.1 for random. The area/composition-only diagnostic predicts gaps of +18.3 and -8.2 points on held-out images. It captures the signs but considerably underestimates the random-mask gap. This does not quantify a causal fraction of the crossover explained. Pattern-aware predictors capture the average gaps more closely, which is expected because their fitting folds contain those patterns. Their within-pattern predictive improvement from foreground coverage is the more informative comparison.''',
'## Head-region check',
'| Inputs | AIMv2 Brier | DINOv2 Brier |\n| --- | ---: | ---: |']
for variant, name in [('foreground', 'Animal visibility and fill'), ('foreground_head', 'Add head-region visibility'),
                      ('mask_content', 'Area/composition, square position and fill'), ('mask_content_head', 'Add head-region visibility to the full baseline')]:
    lines.append(f'| {name} | {loss("auxiliary_head", "aimv2", variant):.4f} | {loss("auxiliary_head", "dinov2", variant):.4f} |')
lines += ['''Head visibility improves the simple foreground predictor for both encoders. After adding all context and square-position measurements, the gain is smaller for AIMv2 and essentially absent for DINOv2. Neither full-baseline head contrast excludes zero in the simultaneous intervals. The sample is small and deliberately selected for head contrast, and the region proxy is a head box intersected with foreground. It does not show that heads alone cause success or explain the primary crossover.''',
'## Stability checks',
'''The primary comparisons retain their directions for penalties 0.1, 1 and 10. After inspecting the first run, two additional image-fold seeds were fixed and run with penalty 1. These are post-hoc checks, not additional independent image evidence.''',
'| Brier improvement over the three fold allocations | AIMv2 range | DINOv2 range |\n| --- | ---: | ---: |']
all_metrics = [metrics]
for seed in [6692029, 6692030]:
    with (BASE / f'fold_seed_{seed}/metrics.csv').open() as f:
        all_metrics.append(list(csv.DictReader(f)))
for cohort, base, extra, name in [('primary', 'mask', 'mask_foreground', 'Primary: add foreground beyond pattern'),
                                 ('primary', 'content', 'mask_content', 'Primary: add pattern beyond content'),
                                 ('auxiliary_head', 'mask_content', 'mask_content_head', 'Auxiliary: add head beyond full baseline')]:
    ranges = []
    for model in ['aimv2', 'dinov2']:
        values = []
        for rows in all_metrics:
            d = {r['variant']: float(r['brier']) for r in rows if r['cohort'] == cohort and r['model'] == model and float(r['penalty']) == 1}
            values.append(d[base] - d[extra])
        ranges.append(f'{min(values):.4f} to {max(values):.4f}')
    lines.append(f'| {name} | {ranges[0]} | {ranges[1]} |')
lines += ['## Interpretation and next question',
'''A useful next research question is whether richer retained-content measurements can improve failure prediction beyond foreground coverage and pattern. The current result supports this direction, but it does not yet support a general claim that semantic part measurements solve the ranking reversal.

A stronger follow-up would fix the diagnostic pipeline and test it on an untouched, unselected cohort with head-region annotations across all four standard masking patterns. That would address the current mismatch between the primary patterns and the auxiliary head-selected pairs. The present analysis cannot identify pretraining causes, generalize to new breeds or datasets, or operate without access to annotations. All images were used in earlier project analyses, so out-of-fold evaluation here remains exploratory rather than confirmatory.

No new encoder inference, 50%/75% standard-pattern extension or pooling experiment was performed in this pass.''',
'## Wording for a professor',
'''“Building on the ranking reversal, I am investigating whether the content that remains visible can help predict when each model succeeds or fails. I compare image visibility, animal visibility, and available region information, while keeping different versions of each original image together during validation. My preliminary analysis suggests that animal coverage adds useful information even when we already know the masking pattern. However, the pattern still contributes information beyond the area measurements. This gives us a more specific account of failure conditions, without claiming that we have identified their causal mechanism.”''',
'## Related work',
'''Foreground and background occlusion are established topics. [PatchDrop](https://arxiv.org/html/2105.10497v3), Section 3.1, compares random, salient and non-salient dropping. [Xiao et al.](https://arxiv.org/abs/2006.09994) show that backgrounds can affect object recognition. [Kortylewski et al.](https://arxiv.org/abs/1905.11826) use compositional representations related to object parts for occlusion robustness. These sources motivate measuring retained content; this project does not claim that foreground or part analysis itself is new.

The present contribution is an image-grouped, annotation-based diagnostic of two fixed encoder/classifier systems, including explicit tests of what foreground coverage adds beyond the mask pattern and the limits of the available head proxy. Method references: [grouped validation](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data) and [Brier scoring](https://scikit-learn.org/stable/modules/model_evaluation.html#brier-score-loss).''',
'## Reproduce',
'''Python 3.12 and NumPy are sufficient for this reanalysis. The saved run used NumPy 2.3.5. No image decoding or pretrained model packages are needed. `scripts/visibility_prediction.py` checks the fixed source hashes and writes out-of-fold probabilities, folds, metrics, contrasts and convergence records. It uses a small NumPy Newton solver so this analysis does not depend on the original inference environment's pandas/scikit-learn imports.

```bash
python scripts/visibility_prediction.py
python tests/test_visibility_prediction.py
python scripts/visibility_prediction_stability.py
python scripts/verify_visibility_prediction.py
python scripts/report_visibility_prediction.py
```

The stability script refuses to overwrite existing sensitivity-run directories. Preserve or move those two directories before an intentional rerun. The original plan is in `docs/VISIBILITY_PREDICTION_PROTOCOL.md`; the separately declared post-hoc check is in `docs/VISIBILITY_PREDICTION_STABILITY.md`. Raw results and verification are under `results/visibility_prediction_v1/`. Codex assisted this analysis under the project's existing AI-use disclosure.''']
report = ROOT / 'reports/VISIBILITY_PREDICTION_EN.md'
text = '\n\n'.join(lines) + '\n'
text = re.sub(r'(?m)^(\|[^\n]*)\n\n(?=\|)', r'\1\n', text)
report.write_text(text)
print(report)

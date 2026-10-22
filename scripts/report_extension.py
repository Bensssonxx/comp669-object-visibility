"""Research figures and English report; refuse incomplete extension evidence."""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from occlusion_visibility.data import load_image
from occlusion_visibility.experiment import decode_mask
from occlusion_visibility.masks import apply_mask

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/extension_v2'
COLORS = {'aimv2': '#0072B2', 'dinov2': '#D55E00'}


def markdown_table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows])


def actual_inputs():
    """Two examples selected by annotation/manifest only, without model outcomes."""
    conditions = pd.read_csv(OUT / 'conditions.csv', keep_default_na=False)
    manifest = json.loads((OUT / 'manifest.json').read_text())
    main = next(r['image_id'] for r in manifest if r['cohort'] == 'primary')
    eligible = set(conditions[conditions.pair_type == 'head_contrast'].image_id)
    aux = next(r['image_id'] for r in manifest if r['cohort'] == 'auxiliary_head' and r['image_id'] in eligible)
    selection = {'rule': 'First primary manifest image and first eligible auxiliary manifest image; no prediction lookup.',
                 'primary_image_id': main, 'auxiliary_image_id': aux}
    selection_path = OUT / 'design_example_selection.json'
    if selection_path.exists():
        assert json.loads(selection_path.read_text()) == selection
    selection_path.write_text(json.dumps(selection, indent=2) + '\n')
    fig, axes = plt.subplots(2, 5, figsize=(16.5, 8.5))
    for row, image_id in enumerate([main, aux]):
        rgb, trimap = load_image(ROOT, image_id)
        axes[row, 0].imshow(rgb)
        axes[row, 0].set_title(image_id + '\nOriginal input', fontsize=11)
        if row == 0:
            selections = [('center', 128), ('random', 128), ('center', 0), ('random', 0)]
            filtered = conditions[(conditions.image_id == image_id) & (conditions.repeat == 0)]
            for col, (pattern, fill) in enumerate(selections, start=1):
                r = filtered[(filtered.pattern == pattern) & (filtered.fill == fill)].iloc[0]
                mask = decode_mask(r.mask_hex, 224, 14)
                axes[row, col].imshow(apply_mask(rgb, mask, fill))
                axes[row, col].set_title(f'{pattern}, fill {fill}\n25% image, {r.object_visibility:.1%} foreground', fontsize=11)
        else:
            from extension_v2 import load_head
            head, _ = load_head(ROOT, image_id, trimap)
            axes[row, 0].contour(head, levels=[.5], colors=['#00FFFF'], linewidths=1)
            axes[row, 0].set_title(image_id + '\nOriginal, auxiliary cohort\nCyan = head-region FG proxy', fontsize=11)
            for col, (role, fill) in enumerate([('high', 128), ('low', 128), ('high', 0), ('low', 0)], start=1):
                r = conditions[(conditions.image_id == image_id) & (conditions.pair_type == 'head_contrast') & (conditions.pair_role == role) & (conditions.fill == fill)].iloc[0]
                axes[row, col].imshow(apply_mask(rgb, decode_mask(r.mask_hex, 224, 14), fill))
                axes[row, col].set_title(f'{role} head, fill {fill}\n75% image, FG {float(r.object_visibility):.1%}\nHead region {float(r.head_visibility):.1%}', fontsize=11)
        for ax in axes[row]:
            ax.axis('off')
    fig.suptitle('Actual extension inputs; annotation outlines are never fed to the encoders', fontsize=14)
    fig.tight_layout(h_pad=3.0, rect=(0, 0, 1, .96))
    (OUT / 'figures').mkdir(exist_ok=True)
    fig.savefig(OUT / 'figures/design_inputs.png', dpi=170, bbox_inches='tight')
    plt.close(fig)


def figure_results(summary, pairs, contrasts):
    destination = OUT / 'figures'
    destination.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size': 12, 'axes.spines.top': False, 'axes.spines.right': False})
    patterns = ['prefix', 'suffix', 'center', 'random']
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.8), sharey=True)
    for ax, fill in zip(axes, [128, 0]):
        for j, model in enumerate(['aimv2', 'dinov2']):
            g = summary[(summary.cohort == 'primary') & (summary.fill == fill) & (summary.model == model)].set_index('pattern').loc[patterns]
            x = np.arange(4) + (j - .5) * .36
            ax.bar(x, g.estimate * 100, width=.34, color=COLORS[model], label=model)
            ax.errorbar(x, g.estimate * 100, yerr=np.stack([(g.estimate - g.ci_low) * 100, (g.ci_high - g.estimate) * 100]), fmt='none', color='black', capsize=3)
        ax.set_xticks(np.arange(4), patterns)
        ax.set_ylim(0, 100)
        ax.set_title(f'{"Gray" if fill == 128 else "Black"} fill (RGB {fill})')
        ax.grid(axis='y', alpha=.15)
    axes[0].set_ylabel('Accuracy (%)')
    axes[1].legend(loc='upper left')
    fig.suptitle('25% image visibility, 740 new official-test images; image-paired breed bootstrap')
    fig.tight_layout()
    fig.savefig(destination / 'primary_accuracy.png', dpi=170, bbox_inches='tight')
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6.1))
    labels = []
    for i, r in enumerate(contrasts.itertuples()):
        ax.plot([r.familywise_ci_low * 100, r.familywise_ci_high * 100], [i, i], color='#A5BEC9', linewidth=7, solid_capstyle='round')
        ax.plot([r.ci_low * 100, r.ci_high * 100], [i, i], color='#17313D', linewidth=2.5)
        ax.scatter([r.estimate * 100], [i], color='#007F7B', s=42, zorder=3)
        labels.append(r.contrast.replace('aim_minus_dino_', 'AIM - DINO: ').replace('center_minus_random_model_difference_', 'Center - random model gap: ').replace('black_minus_gray_model_by_pattern_interaction', 'Black - gray: model-by-pattern interaction').replace('fill128', 'gray').replace('fill0', 'black').replace('_', ' '))
    ax.axvline(0, color='#777777', linewidth=1)
    ax.set_yticks(range(len(labels)), labels, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel('Paired difference (percentage points)')
    ax.set_title('Seven fixed contrasts; dark = individual 95% CI, light = family-wise 95% CI')
    ax.grid(axis='x', alpha=.12)
    fig.tight_layout()
    fig.savefig(destination / 'primary_contrasts.png', dpi=170, bbox_inches='tight')
    plt.close(fig)

    auxiliary = pairs[pairs.pair_type == 'head_contrast']
    if not len(auxiliary):
        return
    fig, axes = plt.subplots(1, 2, figsize=(11.7, 5), sharey=True)
    for ax, fill in zip(axes, [128, 0]):
        for j, role in enumerate(['a', 'b']):
            g = auxiliary[auxiliary.fill == fill].set_index('model').loc[['aimv2', 'dinov2']]
            x = np.arange(2) + (j - .5) * .36
            value = g[f'accuracy_{role}']
            ax.bar(x, value * 100, width=.34, color=['#007F7B', '#9CB9B8'][j], label=['More head-region visible', 'Less head-region visible'][j])
            ax.errorbar(x, value * 100, yerr=np.stack([(value - g[f'accuracy_{role}_ci_low']) * 100, (g[f'accuracy_{role}_ci_high'] - value) * 100]), fmt='none', color='black', capsize=3)
        ax.set_xticks(np.arange(2), ['AIMv2', 'DINOv2'])
        ax.set_ylim(0, 100)
        ax.set_title(f'{"Gray" if fill == 128 else "Black"} fill')
        ax.grid(axis='y', alpha=.15)
    n = int(auxiliary.n_images.iloc[0])
    axes[0].set_ylabel('Accuracy, equal represented-breed weight (%)')
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=11, loc='lower center', ncol=2, frameon=False, bbox_to_anchor=(.5, .005))
    fig.suptitle(f'Exploratory head-region pairs, n={n}; foreground gap <=3 pp, same square area')
    fig.tight_layout(rect=(0, .09, 1, 1))
    fig.savefig(destination / 'head_region_diagnostic.png', dpi=170, bbox_inches='tight')
    plt.close(fig)


def report():
    analysis = json.loads((OUT / 'analysis_audit.json').read_text())
    integration = json.loads((OUT / 'integration_audit.json').read_text())
    assert analysis['passed'] and set(integration['completed_and_reconstructed_models']) == {'aimv2', 'dinov2'}
    preparation = json.loads((OUT / 'preparation_audit.json').read_text())
    summary = pd.read_csv(OUT / 'summary.csv')
    contrasts = pd.read_csv(OUT / 'primary_contrasts.csv')
    pairs = pd.read_csv(OUT / 'paired_summary.csv')
    figure_results(summary, pairs, contrasts)
    main = summary[summary.cohort == 'primary']
    accuracy_rows = []
    for fill in [128, 0]:
        for model in ['aimv2', 'dinov2']:
            g = main[(main.fill == fill) & (main.model == model)].set_index('pattern')
            clean = main[(main.model == model) & (main.pattern == 'clean')].estimate.iloc[0]
            accuracy_rows.append([model, fill, f'{clean:.1%}'] + [f'{g.loc[p,"estimate"]:.1%}' for p in ['prefix', 'suffix', 'center', 'random']])
    accuracy = markdown_table(['Model', 'Fill RGB', 'Clean', 'Prefix 25%', 'Suffix 25%', 'Center 25%', 'Random 25%'], accuracy_rows)
    foreground = pd.read_csv(OUT / 'foreground_coverage.csv').set_index('pattern')
    foreground_table = markdown_table(['Pattern', 'Mean foreground visible', 'Median foreground visible', 'Original images'],
        [[p, f'{foreground.loc[p,"mean"]:.1%}', f'{foreground.loc[p,"median"]:.1%}', int(foreground.loc[p,'count'])] for p in ['prefix', 'suffix', 'center', 'random']])
    contrast_table = markdown_table(['Contrast', 'Estimate pp', '95% CI pp', 'Family-wise 95% CI pp'],
        [[r.contrast, f'{r.estimate*100:.1f}', f'[{r.ci_low*100:.1f}, {r.ci_high*100:.1f}]', f'[{r.familywise_ci_low*100:.1f}, {r.familywise_ci_high*100:.1f}]'] for r in contrasts.itertuples()])
    pair_rows = []
    for r in pairs.itertuples():
        pair_rows.append([r.cohort, r.pair_type, r.model, r.fill, r.n_images, f'{r.accuracy_a:.1%}', f'{r.accuracy_b:.1%}',
            f'{r.paired_accuracy_difference*100:.1f} [{r.paired_accuracy_difference_ci_low*100:.1f}, {r.paired_accuracy_difference_ci_high*100:.1f}]', f'{r.correctness_flip_rate:.1%}', f'{r.class_change_rate:.1%}'])
    paired = markdown_table(['Cohort', 'Pair', 'Model', 'Fill', 'n', 'A breed-macro accuracy', 'B breed-macro accuracy', 'A-B pp [95% CI]', 'Correctness flips', 'Class changes'], pair_rows)
    lookup = contrasts.set_index('contrast')
    fill_checks = pd.read_csv(OUT / 'fill_sensitivity.csv').set_index(['model', 'pattern'])
    ar, dr = fill_checks.loc[('aimv2', 'random')], fill_checks.loc[('dinov2', 'random')]
    interaction = lookup.loc['black_minus_gray_model_by_pattern_interaction']
    fill_note_en = f'Stable ordering does not imply fill invariance. For random visibility, black-minus-gray accuracy is {ar.estimate*100:.1f} pp for AIMv2 (95% CI [{ar.ci_low*100:.1f}, {ar.ci_high*100:.1f}]) and {dr.estimate*100:.1f} pp for DINOv2 (95% CI [{dr.ci_low*100:.1f}, {dr.ci_high*100:.1f}]). The black-minus-gray change in the model-by-pattern interaction is {interaction.estimate*100:.1f} pp (individual 95% CI [{interaction.ci_low*100:.1f}, {interaction.ci_high*100:.1f}]). That interval crossing zero does not establish equivalence of fills. All eight fill contrasts are retained in fill_sensitivity.csv.'
    point_crossover = all(lookup.loc[f'aim_minus_dino_center_fill{f}', 'estimate'] > 0 and lookup.loc[f'aim_minus_dino_random_fill{f}', 'estimate'] < 0 for f in [128, 0])
    family_crossover = all(lookup.loc[f'aim_minus_dino_center_fill{f}', 'familywise_ci_low'] > 0 and lookup.loc[f'aim_minus_dino_random_fill{f}', 'familywise_ci_high'] < 0 for f in [128, 0])
    conclusion_en = ('The point-estimate ordering crossover repeats under both fills: AIMv2 is higher under center visibility, DINOv2 under random visibility.' if point_crossover else 'The pilot ordering crossover does not repeat as point estimates under both fills; inspect each condition.')
    conclusion_en += (' The family-wise intervals for all four component model differences are on their corresponding sides of zero.' if family_crossover else 'Not all four component family-wise intervals exclude zero in their expected directions.')
    head = pairs[pairs.pair_type == 'head_contrast']
    head_details = ''
    if len(head):
        first = head.iloc[0]
        head_details = f'Head-region visibility averaged {first.mean_head_visibility_a:.1%} vs {first.mean_head_visibility_b:.1%}; foreground visibility averaged {first.mean_object_visibility_a:.1%} vs {first.mean_object_visibility_b:.1%}. These coverage means are unweighted image means.'
        if 'mean_body_visibility_a' in first and pd.notna(first.mean_body_visibility_a):
            head_details += f' The complementary body-region proxy averages {first.mean_body_visibility_a:.1%} vs {first.mean_body_visibility_b:.1%} visible.'
    common = f'''\n{accuracy}\n\n{foreground_table}\n\n![Primary accuracy](../results/extension_v2/figures/primary_accuracy.png)\n\n{contrast_table}\n\n![Paired contrasts](../results/extension_v2/figures/primary_contrasts.png)\n'''
    en = f'''# Follow-up v2: new-image replication, fill sensitivity and head-region diagnostics

The design was motivated by pilot_v1 and committed before predictions on the follow-up images (815a33b). It is an internally fixed follow-up, not an independently conceived external preregistration. The pilot evidence is preserved.

{conclusion_en} This describes specified frozen encoder/probe systems and pixel interventions, not a pretraining mechanism.

## Design

Primary cohort: 740 previously unevaluated official-test images, 20 per breed, disjoint in IDs and image-byte hashes from all pilot training/validation/test samples. The original C=10 clean-trained classifiers remain fixed. No fitting or parameter selection uses follow-up images. At 25% visible image area, evaluate prefix, suffix, center and three random masks; repeat with gray128 and black0 fills on identical retained pixels. Also repeat the same-image square-occluder diagnostics, which instead retain 75% image area.

Auxiliary cohort: 185 unused official-trainval images with head boxes, separate from primary and pilot samples. {preparation['eligibility']['auxiliary_head']['eligible']}/185 meet fixed head-contrast eligibility: foreground-visibility gap <=3 pp, center distance >=4 patches, head-region gap >=20 pp. Thresholds were not relaxed. All official-test images lack the downloaded head XMLs, so this auxiliary cohort cannot be presented as official-test head analysis.

There are {analysis['prediction_rows']:,} actual predictions ({preparation['rows_per_model']:,} per model). Random repetitions are averaged within original images. Main estimates use equal breed weights and 10,000 within-breed image bootstrap resamples, retaining all paired conditions together. Seven fixed primary contrasts receive individual and approximate family-wise 95% Bonferroni intervals. Pair/auxiliary results use equal represented-breed weights after eligibility; raw joint counts are retained separately. Intervals condition on the frozen probes/checkpoints.

Input examples below follow manifest order and annotation eligibility, without looking at model outcomes. Cyan annotations are not encoder inputs.

![Actual shared inputs](../results/extension_v2/figures/design_inputs.png)

## Primary results, 25% visible image area
{common}

An interaction alone does not establish opposite rankings: inspect the two component model differences. Black-minus-gray measures fill sensitivity of the model-by-pattern interaction.

Despite equal 25% image visibility, mean foreground visibility is {foreground.loc['center','mean']:.1%} under center and {foreground.loc['random','mean']:.1%} under random masks. Coverage is shared across both models and fills; random repeats are averaged within image. These patterns retain different content distributions. This follow-up does not estimate how much foreground or parts explain their score differences, and does not identify a content-controlled pure position effect.

{fill_note_en}

## Same-image paired diagnostics

A/B means more/less foreground for object_contrast, fixed selected locations for visibility_matched, and more/less head-region visibility for head_contrast. These square occluders hide 25% of the image, unlike the primary 25%-visible conditions.

{paired}

{head_details}

![Head-region diagnostic](../results/extension_v2/figures/head_region_diagnostic.png)

The head-region proxy intersects the head bounding rectangle with annotated foreground; it is not exact head segmentation. Approximate foreground-area matching still changes parts, texture and background together. This is a content-bundle diagnostic, not the isolated causal effect of the head. It also does not establish that head visibility explains the primary model-ordering crossover: the cohorts and mask designs differ. Correctness-flip rates alone cannot rank robustness: two wrong predictions yield no correctness flip.

## Motivation and limits

The motivation is to determine whether evaluation conditions alter model ordering and what image-area or foreground-area summaries omit. New images and a second fill test two limitations of the pilot. Same-image comparisons hold image identity, shape/area, model and probe fixed; fill comparisons additionally hold retained pixels fixed. Different model pretraining remains uncontrolled, so no causal prefix-attention attribution follows. The pilot's lack of shared foreground coverage at 50% image visibility remains unresolved.

This remains one dataset, two synthetic constant fills, one pooling recipe and fixed probes. Exact-byte independence is not proof of no visual near duplicates or pretraining overlap. Auxiliary eligibility/source differs from the primary cohort and must not be pooled into its estimate. The contribution is reproducible replication and diagnostic extension, not first-ever foreground/background analysis. Source protocol, raw predictions, probes, input fingerprints and audits accompany the results. Codex assistance is disclosed in docs/AI_USE.md. No Canvas upload or instructor message was performed.

Evidence: [protocol](../docs/EXTENSION_V2_PROTOCOL.md), [primary contrasts](../results/extension_v2/primary_contrasts.csv), [paired statistics](../results/extension_v2/paired_summary.csv), [integration audit](../results/extension_v2/integration_audit.json).
'''
    destination = ROOT / 'reports'
    destination.mkdir(exist_ok=True)
    (destination / 'EXTENSION_V2_EN.md').write_text(en)
    print('Wrote audited extension reports and research figures')


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--inputs-only', action='store_true')
    args = p.parse_args()
    if args.inputs_only:
        actual_inputs()
    else:
        report()

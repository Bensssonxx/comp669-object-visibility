"""Prespecified follow-up contrasts, image-paired and breed-stratified."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd


def stratified_samples(values, labels, repetitions=10000, seed=6692027):
    """Equal represented-breed estimand, preserving every repeated outcome per image."""
    value = np.asarray(values, dtype=float)
    if value.ndim == 1:
        value = value[:, None]
    labels = np.asarray(labels)
    assert len(value) == len(labels) and len(value) > 0 and np.isfinite(value).all()
    groups = [np.flatnonzero(labels == label) for label in sorted(set(labels.tolist()))]
    rng = np.random.default_rng(seed)
    means = np.zeros((repetitions, value.shape[1]))
    point = np.zeros(value.shape[1])
    for ix in groups:
        point += value[ix].mean(axis=0) / len(groups)
        draw = rng.integers(0, len(ix), size=(repetitions, len(ix)))
        means += value[ix[draw]].mean(axis=1) / len(groups)
    return point, means


def estimate(values, labels, config, names=None, family_size=None):
    point, boot = stratified_samples(values, labels, config['bootstrap_repetitions'], config['seed'])
    ci = np.quantile(boot, [.025, .975], axis=0)
    rows = []
    for i, value in enumerate(point):
        row = {'estimate': float(value), 'ci_low': float(ci[0, i]), 'ci_high': float(ci[1, i]),
               'n_images': len(labels), 'n_represented_breeds': len(set(labels)),
               'estimand': 'Equal represented-breed average; condition on eligibility where applicable'}
        if names:
            row['contrast'] = names[i]
        if family_size:
            q = .05 / (2 * family_size)
            lo, hi = np.quantile(boot[:, i], [q, 1 - q])
            row.update(family_size=family_size, familywise_ci_low=float(lo), familywise_ci_high=float(hi))
        rows.append(row)
    return rows


def primary_contrasts(per_image):
    """Build all seven contrasts on exactly the same original-image rows."""
    table = per_image[(per_image.cohort == 'primary') & (per_image.pattern != 'clean')].pivot(
        index=['image_id', 'label'], columns=['model', 'fill', 'pattern'], values='correct').sort_index()
    columns, names, interactions = [], [], {}
    for fill in [128, 0]:
        delta = {}
        for pattern in ['center', 'random']:
            value = table[('aimv2', fill, pattern)] - table[('dinov2', fill, pattern)]
            columns.append(value.to_numpy())
            names.append(f'aim_minus_dino_{pattern}_fill{fill}')
            delta[pattern] = value
        interactions[fill] = delta['center'] - delta['random']
        columns.append(interactions[fill].to_numpy())
        names.append(f'center_minus_random_model_difference_fill{fill}')
    columns.append((interactions[0] - interactions[128]).to_numpy())
    names.append('black_minus_gray_model_by_pattern_interaction')
    return np.stack(columns, axis=1), table.index.get_level_values('label').to_numpy(), names


def joint_metrics(a, b, config):
    assert a.index.equals(b.index)
    labels = a.label.to_numpy()
    values = np.stack([a.correct.to_numpy(), b.correct.to_numpy(),
        a.correct.to_numpy() - b.correct.to_numpy(),
        (a.correct.to_numpy() != b.correct.to_numpy()).astype(float),
        (a.prediction.to_numpy() != b.prediction.to_numpy()).astype(float),
        np.abs(a.target_probability.to_numpy() - b.target_probability.to_numpy())], axis=1)
    names = ['accuracy_a', 'accuracy_b', 'paired_accuracy_difference', 'correctness_flip_rate',
             'class_change_rate', 'mean_absolute_target_probability_difference']
    summaries = estimate(values, labels, config, names)
    result = {'n_images': len(a), 'n_represented_breeds': len(set(labels))}
    for name, s in zip(names, summaries):
        result[name] = s['estimate']
        result[name + '_ci_low'] = s['ci_low']
        result[name + '_ci_high'] = s['ci_high']
    result.update(n_both_correct=int(((a.correct == 1) & (b.correct == 1)).sum()),
                  n_both_wrong=int(((a.correct == 0) & (b.correct == 0)).sum()),
                  n_only_a_correct=int(((a.correct == 1) & (b.correct == 0)).sum()),
                  n_only_b_correct=int(((a.correct == 0) & (b.correct == 1)).sum()))
    for field in ['object_visibility', 'background_visibility', 'head_visibility', 'body_visibility']:
        if field in a and a[field].notna().all() and b[field].notna().all():
            result['mean_' + field + '_a'] = float(a[field].mean())
            result['mean_' + field + '_b'] = float(b[field].mean())
            result['mean_abs_' + field + '_gap'] = float(np.abs(a[field] - b[field]).mean())
            result['max_abs_' + field + '_gap'] = float(np.abs(a[field] - b[field]).max())
    result['estimand'] = 'Equal represented-breed mean among eligible images; joint counts unweighted'
    return result


def analyze(root):
    out = root / 'results/extension_v2'
    config = json.loads((out / 'config.json').read_text())
    audit = json.loads((out / 'integration_audit.json').read_text())
    assert audit['passed'] and set(audit['completed_and_reconstructed_models']) == {'aimv2', 'dinov2'}
    df = pd.concat([pd.read_csv(out / f'{m}_predictions.csv', keep_default_na=False, na_values=['']) for m in ['aimv2', 'dinov2']], ignore_index=True)
    assert not df.duplicated(['condition_id', 'model']).any()
    for field in ['label', 'fill', 'correct', 'prediction', 'target_probability', 'object_visibility', 'background_visibility', 'head_visibility', 'body_visibility']:
        df[field] = pd.to_numeric(df[field], errors='coerce')
    a, b = [g.set_index('condition_id').sort_index() for _, g in df.groupby('model')]
    assert a.index.equals(b.index) and (a.mask_sha256 == b.mask_sha256).all()
    per_image = df[df.suite == 'standard'].groupby(['cohort', 'image_id', 'label', 'model', 'fill', 'pattern'], as_index=False).agg(
        correct=('correct', 'mean'), object_visibility=('object_visibility', 'mean'),
        target_probability=('target_probability', 'mean'))
    per_image.to_csv(out / 'standard_per_image.csv', index=False)
    values, labels, names = primary_contrasts(per_image)
    primary = pd.DataFrame(estimate(values, labels, config, names, family_size=7))
    primary.to_csv(out / 'primary_contrasts.csv', index=False)
    standard = []
    for (cohort, model, fill, pattern), g in per_image.groupby(['cohort', 'model', 'fill', 'pattern']):
        g = g.sort_values('image_id')
        result = estimate(g.correct, g.label, config)[0]
        result.update(cohort=cohort, model=model, fill=int(fill), pattern=pattern,
                      mean_object_visibility=float(g.object_visibility.mean()))
        standard.append(result)
    summary = pd.DataFrame(standard)
    clean = summary[summary.pattern == 'clean'].set_index(['cohort', 'model']).estimate.to_dict()
    summary['clean_accuracy'] = [clean[(r.cohort, r.model)] for r in summary.itertuples()]
    summary['accuracy_drop_from_clean'] = summary.clean_accuracy - summary.estimate
    summary.to_csv(out / 'summary.csv', index=False)
    pairs = []
    for (cohort, model, fill, pair_type), g in df[df.suite == 'paired'].groupby(['cohort', 'model', 'fill', 'pair_type']):
        role_a, role_b = ('a', 'b') if pair_type == 'visibility_matched' else ('high', 'low')
        a = g[g.pair_role == role_a].set_index('image_id').sort_index()
        b = g[g.pair_role == role_b].set_index('image_id').sort_index()
        pairs.append(dict(cohort=cohort, model=model, fill=int(fill), pair_type=pair_type,
                          role_a=role_a, role_b=role_b, **joint_metrics(a, b, config)))
    pairs = pd.DataFrame(pairs)
    pairs.to_csv(out / 'paired_summary.csv', index=False)
    fill_differences = []
    for (model, pattern), g in per_image[(per_image.cohort == 'primary') & (per_image.pattern != 'clean')].groupby(['model', 'pattern']):
        table = g.pivot(index=['image_id', 'label'], columns='fill', values='correct').sort_index()
        s = estimate(table[0] - table[128], table.index.get_level_values('label'), config)[0]
        fill_differences.append(dict(model=model, pattern=pattern, contrast='black_minus_gray_accuracy', **s))
    pd.DataFrame(fill_differences).to_csv(out / 'fill_sensitivity.csv', index=False)
    flip_diffs = []
    match = df[(df.cohort == 'primary') & (df.pair_type == 'visibility_matched')]
    for fill, g in match.groupby('fill'):
        pivot = g.pivot(index=['image_id', 'label'], columns=['model', 'pair_role'], values='correct').sort_index()
        delta = (pivot[('aimv2', 'a')] != pivot[('aimv2', 'b')]).astype(float) - (pivot[('dinov2', 'a')] != pivot[('dinov2', 'b')]).astype(float)
        s = estimate(delta, pivot.index.get_level_values('label'), config)[0]
        flip_diffs.append(dict(fill=int(fill), contrast='aim_minus_dino_matched_flip_rate', **s))
    pd.DataFrame(flip_diffs).to_csv(out / 'paired_model_flip_differences.csv', index=False)
    coverage = per_image[(per_image.cohort == 'primary') & (per_image.model == 'aimv2') & (per_image.fill == 128)].groupby('pattern').object_visibility.agg(['count', 'mean', 'median', 'min', 'max'])
    coverage.to_csv(out / 'foreground_coverage.csv')
    # Approximate equality does not imply part or semantic-content equality.
    checks = {'passed': True, 'prediction_rows': len(df), 'primary_images': int(len(labels)),
              'primary_contrast_count': len(primary), 'bootstrap_repetitions': config['bootstrap_repetitions'],
              'bootstrap_unit': 'Original image, stratified within breed; repeated conditions carried together',
              'random_repeats_averaged_within_image': True, 'primary_family_size': 7,
              'interval_scope': 'Conditional on fixed probes/checkpoints; follow-up design selected after pilot'}
    (out / 'analysis_audit.json').write_text(json.dumps(checks, indent=2) + '\n')
    print(primary.to_string(index=False), flush=True)
    print(json.dumps(checks, indent=2), flush=True)
    return df, summary, primary, pairs


def main():
    p = argparse.ArgumentParser()
    p.parse_args()
    analyze(Path(__file__).resolve().parents[1])


if __name__ == '__main__':
    main()

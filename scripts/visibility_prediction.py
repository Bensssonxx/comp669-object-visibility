"""Predict saved classification correctness from annotation-based visibility.

Exploratory, image-grouped cross-validation. This does not rerun either encoder
or fit an animal-breed classifier. Run with Python 3.12 and NumPy only.
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/visibility_prediction_v1'
SEED = 6692028
PENALTIES = [1.0, 0.1, 10.0]
PATTERNS = ['prefix', 'suffix', 'center', 'random']


def read_csv(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -35, 35)))


def objective(beta, x, y, weight, penalty):
    z = x @ beta
    return float(np.dot(weight, np.logaddexp(0, z) - y * z)
                 + penalty / 2 * np.dot(beta[1:], beta[1:]))


def fit_logistic(x, y, weight, penalty, n_images):
    """Weighted ridge logistic regression, Newton updates with backtracking."""
    weight = weight / weight.sum() * n_images
    mean = np.average(x, axis=0, weights=weight)
    scale = np.sqrt(np.average((x - mean) ** 2, axis=0, weights=weight))
    scale[scale < 1e-10] = 1
    design = np.column_stack([np.ones(len(x)), (x - mean) / scale])
    beta = np.zeros(design.shape[1])
    prevalence = np.clip(np.average(y, weights=weight), 1e-6, 1 - 1e-6)
    beta[0] = np.log(prevalence / (1 - prevalence))
    ridge = np.full(len(beta), penalty)
    ridge[0] = 0
    for iteration in range(100):
        probability = sigmoid(design @ beta)
        gradient = design.T @ (weight * (probability - y)) + ridge * beta
        gradient_max = float(np.abs(gradient).max())
        if gradient_max < 1e-7:
            return beta, mean, scale, iteration, gradient_max
        hessian = (design.T * (weight * probability * (1 - probability))) @ design
        hessian += np.diag(ridge + 1e-10)
        step = np.linalg.solve(hessian, gradient)
        loss = objective(beta, design, y, weight, penalty)
        rate = 1.0
        while rate > 1e-10:
            candidate = beta - rate * step
            if objective(candidate, design, y, weight, penalty) <= loss + 1e-12:
                beta = candidate
                break
            rate /= 2
        else:
            raise RuntimeError('Newton line search did not converge')
    raise RuntimeError(f'Logistic fit did not converge: gradient {gradient_max}')


def predict(fit, x):
    beta, mean, scale, *_ = fit
    return sigmoid(np.column_stack([np.ones(len(x)), (x - mean) / scale]) @ beta)


def image_folds(rows):
    """Allocate unique images within breed; never split masks of one image."""
    labels = {}
    for row in rows:
        if row['image_id'] in labels:
            assert labels[row['image_id']] == int(row['label'])
        labels[row['image_id']] = int(row['label'])
    rng = np.random.default_rng(SEED)
    folds = {}
    for label in sorted(set(labels.values())):
        ids = np.array(sorted(i for i, v in labels.items() if v == label))
        ids = rng.permutation(ids)
        offset = int(rng.integers(5))
        folds.update({str(image): (j + offset) % 5 for j, image in enumerate(ids)})
    return folds


def feature_sets(auxiliary=False):
    budget = ['visible_fraction', 'fill_numeric']
    foreground = budget + ['object_visibility']
    content = foreground + ['background_visibility', 'object_fraction', 'unknown_fraction']
    geometry = ['square_x', 'square_y'] if auxiliary else ['pattern']
    result = {'budget': budget, 'foreground': foreground, 'content': content,
              'mask': budget + geometry, 'mask_foreground': foreground + geometry,
              'mask_content': content + geometry}
    if auxiliary:
        for key in ['foreground', 'content', 'mask_content']:
            result[key + '_head'] = result[key] + ['head_visibility']
    return result


def design_matrix(rows, fields):
    columns = []
    for field in fields:
        if field == 'pattern':
            columns.extend(np.array([row['pattern'] == pattern for row in rows], float)
                           for pattern in PATTERNS)
        else:
            value = np.array([float(row[field]) for row in rows])
            assert np.isfinite(value).all(), field
            assert ((value >= 0) & (value <= 1)).all(), field
            columns.extend([value, value ** 2])
    return np.column_stack(columns)


def weighted_auc(y, p, weight):
    order = np.argsort(p, kind='stable')
    y, p, weight = y[order], p[order], weight[order]
    positive, negative = weight * y, weight * (1 - y)
    _, start = np.unique(p, return_index=True)
    pos, neg = np.add.reduceat(positive, start), np.add.reduceat(negative, start)
    below = np.cumsum(neg) - neg
    return float(np.dot(pos, below + .5 * neg) / (pos.sum() * neg.sum()))


def load_inputs():
    record = json.loads((OUT / 'design_record.json').read_text())
    for name, expected in record['sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    conditions = {r['condition_id']: r for r in read_csv(ROOT / 'results/extension_v2/conditions.csv')}
    assert len(conditions) == 16361
    result = {}
    for model in ['aimv2', 'dinov2']:
        rows = read_csv(ROOT / f'results/extension_v2/{model}_predictions.csv')
        assert len(rows) == len(conditions) and len({r['condition_id'] for r in rows}) == len(rows)
        assert {r['condition_id'] for r in rows} == set(conditions)
        for row in rows:
            assert all(row[k] == value for k, value in conditions[row['condition_id']].items())
            assert int(row['correct']) == (int(row['prediction']) == int(row['label']))
        result[model] = rows
    return result


def prepare(rows, auxiliary):
    if auxiliary:
        keep = [r.copy() for r in rows if r['cohort'] == 'auxiliary_head' and r['pair_type'] == 'head_contrast']
    else:
        keep = [r.copy() for r in rows if r['cohort'] == 'primary' and r['suite'] == 'standard' and r['pattern'] != 'clean']
    keep.sort(key=lambda r: r['condition_id'])
    labels = {r['image_id']: int(r['label']) for r in keep}
    breed_counts = {label: list(labels.values()).count(label) for label in set(labels.values())}
    for row in keep:
        row['fill_numeric'] = int(row['fill']) / 128
        row['row_weight'] = (1 / 3 if row['pattern'] == 'random' else 1) / breed_counts[int(row['label'])]
        assert float(row['visible_fraction']) == (.75 if auxiliary else .25)
        if auxiliary:
            y, x = map(int, re.fullmatch(r'square_y(\d+)_x(\d+)', row['pattern']).groups())
            row['square_x'], row['square_y'] = (x + 4) / 16, (y + 4) / 16
            mask = np.unpackbits(np.frombuffer(bytes.fromhex(row['mask_hex']), np.uint8)).reshape(16, 16)
            expected = np.ones((16, 16), np.uint8)
            expected[y:y + 8, x:x + 8] = 0
            assert np.array_equal(mask, expected)
    assert len(labels) == (159 if auxiliary else 740)
    assert len(keep) == (636 if auxiliary else 8880)
    assert len(breed_counts) == 37
    return keep


def bootstrap(contrasts, labels, repetitions=10000):
    """Paired differences by original image, equal-weight represented breeds."""
    rng = np.random.default_rng(SEED)
    boot = np.zeros((repetitions, contrasts.shape[1]))
    point = np.zeros(contrasts.shape[1])
    for label in sorted(set(labels)):
        values = contrasts[labels == label]
        point += values.mean(axis=0) / len(set(labels))
        draw = rng.integers(0, len(values), size=(repetitions, len(values)))
        boot += values[draw].mean(axis=1) / len(set(labels))
    return point, np.quantile(boot, [.025, .975], axis=0), np.quantile(boot, [.05 / 60, 1 - .05 / 60], axis=0)


def run():
    inputs = load_inputs()
    metrics, contrast_rows, fold_rows, gap_rows, fit_audit = [], [], [], [], []
    for auxiliary in [False, True]:
        cohort = 'auxiliary_head' if auxiliary else 'primary'
        variants = feature_sets(auxiliary)
        cohort_folds = None
        for model in ['aimv2', 'dinov2']:
            rows = prepare(inputs[model], auxiliary)
            mapping = image_folds(rows)
            assert cohort_folds is None or mapping == cohort_folds
            cohort_folds = mapping
            if model == 'aimv2':
                labels_by_image = {r['image_id']: int(r['label']) for r in rows}
                fold_rows.extend({'cohort': cohort, 'image_id': image, 'label': labels_by_image[image], 'fold': fold}
                                 for image, fold in sorted(mapping.items()))
            folds = np.array([mapping[r['image_id']] for r in rows])
            y = np.array([int(r['correct']) for r in rows])
            weight = np.array([r['row_weight'] for r in rows])
            image_ids = np.array(sorted(mapping))
            image_ix = np.array([np.flatnonzero(np.array([r['image_id'] for r in rows]) == image) for image in image_ids])
            labels = np.array([int(rows[ix[0]]['label']) for ix in image_ix])
            matrices = {key: design_matrix(rows, fields) for key, fields in variants.items()}
            probabilities = np.full((len(PENALTIES), len(variants), len(rows)), np.nan)
            for pi, penalty in enumerate(PENALTIES):
                for vi, (variant, x) in enumerate(matrices.items()):
                    for fold in range(5):
                        train, test = folds != fold, folds == fold
                        train_ids = {r['image_id'] for j, r in enumerate(rows) if train[j]}
                        test_ids = {r['image_id'] for j, r in enumerate(rows) if test[j]}
                        assert train_ids.isdisjoint(test_ids) and len(test_ids) > 0
                        fit = fit_logistic(x[train], y[train], weight[train], penalty, len(train_ids))
                        probabilities[pi, vi, test] = predict(fit, x[test])
                        fit_audit.append({'cohort': cohort, 'model': model, 'variant': variant, 'penalty': penalty,
                                          'fold': fold, 'iterations': fit[3], 'gradient_max': fit[4],
                                          'fit_images': len(train_ids), 'heldout_images': len(test_ids)})
                    p = probabilities[pi, vi]
                    assert np.isfinite(p).all()
                    log_loss = -(y * np.log(p) + (1 - y) * np.log1p(-p))
                    metrics.append({'cohort': cohort, 'model': model, 'variant': variant, 'penalty': penalty,
                                    'n_images': len(image_ids), 'n_rows': len(rows),
                                    'brier': np.average((y - p) ** 2, weights=weight),
                                    'log_loss': np.average(log_loss, weights=weight),
                                    'auc': weighted_auc(y, p, weight),
                                    'correctness_prediction_accuracy': np.average((p >= .5) == y, weights=weight)})
                print(f'{cohort} {model}: completed penalty {penalty}', flush=True)
            np.savez_compressed(OUT / f'{cohort}_{model}_oof.npz',
                                condition_id=np.array([r['condition_id'] for r in rows]),
                                image_id=np.array([r['image_id'] for r in rows]), label=np.array([int(r['label']) for r in rows]),
                                fold=folds, correct=y, weight=weight, probability=probabilities,
                                variants=np.array(list(variants)), penalties=np.array(PENALTIES))
            comparisons = [('budget', 'foreground'), ('foreground', 'content'), ('budget', 'mask'),
                           ('mask', 'mask_foreground'), ('mask_foreground', 'mask_content'), ('content', 'mask_content')]
            if auxiliary:
                comparisons += [(key, key + '_head') for key in ['foreground', 'content', 'mask_content']]
            vnames = list(variants)
            per_image = []
            for base, extra in comparisons:
                delta = (y - probabilities[0, vnames.index(base)]) ** 2 - (y - probabilities[0, vnames.index(extra)]) ** 2
                per_image.append([np.average(delta[ix], weights=weight[ix]) for ix in image_ix])
            point, ci, simultaneous = bootstrap(np.array(per_image).T, labels)
            for j, (base, extra) in enumerate(comparisons):
                contrast_rows.append({'cohort': cohort, 'model': model, 'base': base, 'extra': extra,
                                      'brier_improvement': point[j], 'ci_low': ci[0, j], 'ci_high': ci[1, j],
                                      'simultaneous_ci_low': simultaneous[0, j], 'simultaneous_ci_high': simultaneous[1, j],
                                      'family_size': 30, 'n_images': len(image_ids)})
            if not auxiliary:
                for vi, variant in enumerate(variants):
                    for pattern in PATTERNS:
                        for fill in [0, 128]:
                            ix = np.array([r['pattern'] == pattern and int(r['fill']) == fill for r in rows])
                            gap_rows.append({'model': model, 'variant': variant, 'pattern': pattern, 'fill': fill,
                                             'observed_accuracy': np.average(y[ix], weights=weight[ix]),
                                             'predicted_accuracy_oof': np.average(probabilities[0, vi, ix], weights=weight[ix])})
    write_csv(OUT / 'metrics.csv', metrics)
    write_csv(OUT / 'contrasts.csv', contrast_rows)
    write_csv(OUT / 'folds.csv', fold_rows)
    write_csv(OUT / 'pattern_predictions.csv', gap_rows)
    write_csv(OUT / 'fit_audit.csv', fit_audit)
    # Verify every original source and plan again after all fitting.
    load_inputs()
    audit = {'passed': True, 'python': platform.python_version(), 'numpy': np.__version__,
             'seed': SEED, 'outer_folds': 5, 'penalties': PENALTIES, 'fit_count': len(fit_audit),
             'all_fits_converged': True, 'max_gradient': max(r['gradient_max'] for r in fit_audit),
             'original_images': {'primary': 740, 'auxiliary_head': 159},
             'source_sha256_unchanged': True, 'image_group_leakage': False, 'out_of_fold_for_every_row': True,
             'bootstrap_repetitions': 10000, 'simultaneous_contrast_count': len(contrast_rows),
             'scope': 'Exploratory reuse of known data. CIs conditional on OOF predictions, not refit uncertainty.'}
    assert len(contrast_rows) == 30
    (OUT / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps(audit, indent=2), flush=True)


if __name__ == '__main__':
    run()

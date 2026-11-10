"""Independently reconstruct diagnostic metrics from saved OOF arrays."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'results/visibility_prediction_v1'
checks = []
for directory in [BASE, BASE / 'fold_seed_6692029', BASE / 'fold_seed_6692030']:
    with (directory / 'folds.csv').open() as f:
        fold_rows = list(csv.DictReader(f))
    expected_folds = {(r['cohort'], r['image_id']): int(r['fold']) for r in fold_rows}
    assert len(expected_folds) == 899
    with (directory / 'metrics.csv').open() as f:
        metrics = list(csv.DictReader(f))
    with (directory / 'contrasts.csv').open() as f:
        contrasts = list(csv.DictReader(f))
    assert len(contrasts) == 30
    for cohort in ['primary', 'auxiliary_head']:
        paired = []
        for model in ['aimv2', 'dinov2']:
            d = np.load(directory / f'{cohort}_{model}_oof.npz', allow_pickle=False)
            assert len(np.unique(d['image_id'])) == (740 if cohort == 'primary' else 159)
            assert all(int(fold) == expected_folds[cohort, image] for image, fold in zip(d['image_id'], d['fold']))
            assert np.isfinite(d['probability']).all()
            assert ((d['probability'] > 0) & (d['probability'] < 1)).all()
            paired.append((d['condition_id'], d['fold']))
            for row in metrics:
                if row['cohort'] != cohort or row['model'] != model:
                    continue
                pi = np.flatnonzero(d['penalties'] == float(row['penalty'])).item()
                vi = np.flatnonzero(d['variants'] == row['variant']).item()
                p = d['probability'][pi, vi]
                loss = (d['correct'] - p) ** 2
                assert abs(np.average(loss, weights=d['weight']) - float(row['brier'])) < 1e-12
                # A second aggregation path, explicitly conditions -> image -> breed.
                breed_scores = []
                for label in np.unique(d['label']):
                    image_scores = []
                    for image in np.unique(d['image_id'][d['label'] == label]):
                        ix = d['image_id'] == image
                        image_scores.append(np.average(loss[ix], weights=d['weight'][ix]))
                    breed_scores.append(np.mean(image_scores))
                assert abs(np.mean(breed_scores) - float(row['brier'])) < 1e-12
            main = {row['variant']: float(row['brier']) for row in metrics
                    if row['cohort'] == cohort and row['model'] == model and float(row['penalty']) == 1}
            for row in contrasts:
                if row['cohort'] != cohort or row['model'] != model:
                    continue
                value = main[row['base']] - main[row['extra']]
                assert abs(value - float(row['brier_improvement'])) < 1e-12
                assert float(row['simultaneous_ci_low']) <= float(row['ci_low']) <= float(row['ci_high']) <= float(row['simultaneous_ci_high'])
        assert np.array_equal(paired[0][0], paired[1][0])
        assert np.array_equal(paired[0][1], paired[1][1])
    checks.append(directory.name + ': saved scores, image grouping, encoder pairing and all 30 contrasts verified')
record = json.loads((BASE / 'design_record.json').read_text())
for path, expected in record['sha256'].items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
checks.append('Original condition files, predictions and analysis plan hashes unchanged')
result = {'passed': True, 'checks': checks, 'unit_tests': 6,
          'source_sha256': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in [
              'scripts/visibility_prediction.py', 'scripts/visibility_prediction_stability.py',
              'scripts/verify_visibility_prediction.py', 'tests/test_visibility_prediction.py']}}
(BASE / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))

"""Synthetic, temporary-only end-to-end statistical pipeline with known contrasts."""
import importlib.util
import json
from pathlib import Path
import numpy as np
import pandas as pd


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / 'scripts' / file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_known_followup_contrasts_and_report_smoke(tmp_path):
    analysis = module('followup_analysis_e2e', 'analyze_extension.py')
    report = module('followup_report_e2e', 'report_extension.py')
    out = tmp_path / 'results/extension_v2'
    out.mkdir(parents=True)
    (out / 'config.json').write_text(json.dumps({'bootstrap_repetitions': 100, 'seed': 9}))
    (out / 'integration_audit.json').write_text(json.dumps({'passed': True, 'completed_and_reconstructed_models': ['aimv2', 'dinov2']}))
    all_rows = []
    for model in ['aimv2', 'dinov2']:
        rows = []
        def add(image_id, label, cohort, suite, pattern, fill, correct, repeat=0, pair_type='', role=''):
            rows.append(dict(image_id=image_id, label=label, cohort=cohort, suite=suite, pattern=pattern, fill=fill,
                correct=correct, repeat=repeat, pair_type=pair_type, pair_role=role, model=model,
                prediction=label if correct else (label + 1) % 37, target_probability=.8 if correct else .1,
                condition_id=f'{image_id}:{suite}:{pattern}:{fill}:{repeat}:{pair_type}:{role}', mask_sha256=f'{pattern}:{repeat}:{role}',
                object_visibility=.55, background_visibility=.8,
                head_visibility=(.9 if role == 'high' else .1) if cohort == 'auxiliary_head' else None,
                body_visibility=(.3 if role == 'high' else .9) if cohort == 'auxiliary_head' else None))
        for label in [0, 1]:
            for index in [0, 1]:
                image_id = f'primary_{label}_{index}'
                add(image_id, label, 'primary', 'standard', 'clean', -1, 1)
                for fill in [128, 0]:
                    for pattern in ['prefix', 'suffix', 'center', 'random']:
                        correct = int((model == 'aimv2' and pattern == 'center' and fill == 128) or (model == 'dinov2' and pattern == 'random'))
                        for repeat in ([0, 1, 2] if pattern == 'random' else [0]):
                            add(image_id, label, 'primary', 'standard', pattern, fill, correct, repeat)
                    for pair_type, roles in [('object_contrast', ['high', 'low']), ('visibility_matched', ['a', 'b'])]:
                        for role in roles:
                            add(image_id, label, 'primary', 'paired', 'square_' + role, fill, int(role in ['high', 'a']), pair_type=pair_type, role=role)
        add('aux', 0, 'auxiliary_head', 'standard', 'clean', -1, 1)
        for fill in [128, 0]:
            for role in ['high', 'low']:
                add('aux', 0, 'auxiliary_head', 'paired', 'square_' + role, fill, int(model == 'aimv2' and role == 'high'), pair_type='head_contrast', role=role)
        pd.DataFrame(rows).to_csv(out / f'{model}_predictions.csv', index=False)
        all_rows.extend(rows)
    _, _, contrasts, pairs = analysis.analyze(tmp_path)
    assert contrasts.estimate.tolist() == [1., -1., 2., 0., -1., 1., -1.]
    assert pairs[pairs.pair_type == 'head_contrast'].set_index(['model', 'fill']).paired_accuracy_difference.to_dict() == {('aimv2', 0): 1., ('aimv2', 128): 1., ('dinov2', 0): 0., ('dinov2', 128): 0.}
    (out / 'preparation_audit.json').write_text(json.dumps({'rows_per_model': len(all_rows) // 2, 'eligibility': {'auxiliary_head': {'eligible': 1}}}))
    report.ROOT, report.OUT = tmp_path, out
    report.report()
    assert (tmp_path / 'reports/EXTENSION_V2_ZH.md').exists()
    assert (out / 'figures/primary_contrasts.png').exists()

import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location('analyze_extension', Path(__file__).parents[1] / 'scripts/analyze_extension.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def test_stratification_keeps_equal_breed_weight_when_eligibility_unbalanced():
    point, draws = a.stratified_samples([0., 1., 1., 1.], [0, 1, 1, 1], repetitions=200)
    assert point[0] == .5
    assert (draws[:, 0] == .5).all()


def test_paired_outcomes_remain_joint_during_image_bootstrap():
    x = np.array([[0., 0.], [1., 1.], [1., 1.], [0., 0.]])
    _, draws = a.stratified_samples(x, [0, 0, 1, 1], repetitions=200)
    assert np.array_equal(draws[:, 0], draws[:, 1])


def test_interaction_sign_and_seven_contrasts():
    rows = []
    for image_id, label in [('cat', 0), ('dog', 1)]:
        for fill in [128, 0]:
            for model in ['aimv2', 'dinov2']:
                for pattern in ['center', 'random']:
                    correct = int((model == 'aimv2' and pattern == 'center' and fill == 128) or (model == 'dinov2' and pattern == 'random'))
                    rows.append(dict(cohort='primary', image_id=image_id, label=label, fill=fill, model=model, pattern=pattern, correct=correct))
    values, labels, names = a.primary_contrasts(pd.DataFrame(rows))
    assert values.shape == (2, 7)
    assert values[0].tolist() == [1., -1., 2., 0., -1., 1., -1.]
    assert len(set(names)) == 7 and labels.tolist() == [0, 1]

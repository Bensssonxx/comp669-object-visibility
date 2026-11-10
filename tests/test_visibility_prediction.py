"""Numerical and leakage checks for the exploratory correctness predictor."""
import importlib.util
import unittest
from pathlib import Path
import numpy as np

spec = importlib.util.spec_from_file_location('visibility_prediction', Path(__file__).parents[1] / 'scripts/visibility_prediction.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class DiagnosticTests(unittest.TestCase):
    def test_intercept_has_closed_form_weighted_prevalence(self):
        x = np.zeros((5, 2))
        y = np.array([0., 1., 0., 1., 1.])
        w = np.array([1., 2., 1., 3., 2.])
        fit = m.fit_logistic(x, y, w, 1, 5)
        self.assertTrue(np.allclose(m.predict(fit, x), np.average(y, weights=w), atol=1e-9))

    def test_solver_reaches_stationary_point_and_improves_loss(self):
        rng = np.random.default_rng(14)
        x = rng.normal(size=(200, 3))
        y = (rng.random(200) < m.sigmoid(x[:, 0] - .8 * x[:, 1])).astype(float)
        fit = m.fit_logistic(x, y, np.ones(200), 1, 200)
        self.assertLess(fit[4], 1e-7)
        beta, mean, scale, *_ = fit
        d = np.column_stack([np.ones(200), (x - mean) / scale])
        eps = 1e-5
        finite_gradient = []
        for j in range(len(beta)):
            step = np.zeros(len(beta)); step[j] = eps
            finite_gradient.append((m.objective(beta + step, d, y, np.ones(200), 1) - m.objective(beta - step, d, y, np.ones(200), 1)) / (2 * eps))
        self.assertLess(np.max(np.abs(finite_gradient)), 1e-6)
        baseline = np.zeros(len(beta)); baseline[0] = np.log(y.mean() / (1 - y.mean()))
        self.assertLess(m.objective(beta, d, y, np.ones(200), 1), m.objective(baseline, d, y, np.ones(200), 1))

    def test_training_standardization_does_not_depend_on_test_rows(self):
        x = np.array([[0.], [.1], [.8], [1.]])
        fit = m.fit_logistic(x, np.array([0, 0, 1, 1]), np.ones(4), 1, 4)
        original = m.predict(fit, np.array([[.4]]))[0]
        combined = m.predict(fit, np.array([[.4], [100.]]))[0]
        self.assertAlmostEqual(original, combined)

    def test_group_folds_are_stable_and_never_use_outcomes(self):
        rows = [{'image_id': str(i), 'label': i // 10, 'correct': r} for i in range(30) for r in [0, 1]]
        folds = m.image_folds(rows)
        self.assertEqual(folds, m.image_folds(list(reversed(rows))))
        self.assertEqual(len(folds), 30)
        self.assertEqual(set(folds.values()), set(range(5)))

    def test_weighted_auc_handles_ties(self):
        y = np.array([0, 1, 0, 1])
        self.assertAlmostEqual(m.weighted_auc(y, np.array([.1, .5, .5, .9]), np.ones(4)), .875)
        self.assertAlmostEqual(m.weighted_auc(y, np.ones(4), np.ones(4)), .5)

    def test_predictors_exclude_outcomes_labels_and_pair_roles(self):
        forbidden = {'correct', 'prediction', 'target_probability', 'image_id', 'label', 'pair_role', 'pair_type'}
        for auxiliary in [False, True]:
            for fields in m.feature_sets(auxiliary).values():
                self.assertFalse(set(fields) & forbidden)


if __name__ == '__main__':
    unittest.main()

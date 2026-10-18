"""Statistical safeguards: repeated masks must not inflate the sample count."""
import importlib.util
from pathlib import Path

import pandas as pd

spec = importlib.util.spec_from_file_location("project_analysis", Path(__file__).parents[1] / "scripts/analyze.py")
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def test_three_masks_are_two_image_units_not_six():
    rows = []
    for image_id, correct in [("a", 1), ("b", 0)]:
        for repeat in range(3):
            rows.append(dict(model="aimv2", image_id=image_id, label=0, pattern="random", fraction=.5,
                             correct=correct, object_visibility=.5, background_visibility=.5,
                             target_probability=.8 if correct else .2, repeat=repeat))
    collapsed = analysis.collapse_repetitions(pd.DataFrame(rows))
    assert len(collapsed) == 2
    assert collapsed.correct.mean() == .5
    # With 2 independent images (1 right, 1 wrong), the 95% bootstrap spans [0,1].
    # Treating all 6 masks as independent would produce a misleading narrower interval.
    assert analysis.cluster_ci(collapsed.correct, n=2000) == [0., 1.]

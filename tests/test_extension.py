"""Follow-up checks target independence, shared fill inputs and head-proxy semantics."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest
from PIL import Image

spec = importlib.util.spec_from_file_location('extension_v2', Path(__file__).parents[1] / 'scripts/extension_v2.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
CFG = {'primary_fraction': .25, 'random_seeds': [0, 1, 2], 'pair_caliper': .03,
       'minimum_center_distance_patches': 4, 'head_minimum_visibility_gap': .2, 'fills': [128, 0], 'patch': 14}


def test_pascal_box_inclusive_conversion_and_foreground_intersection():
    trimap = np.ones((4, 4), dtype=np.uint8)
    trimap[0, 0] = 2
    value = e.rectangle_proxy(trimap, (4, 4), [1, 1, 2, 2])
    expected = np.zeros((4, 4), dtype=bool)
    expected[:2, :2] = True
    expected[0, 0] = False
    assert np.array_equal(value, expected)
    with pytest.raises(ValueError):
        e.rectangle_proxy(trimap, (4, 4), [0, 1, 2, 2])


def test_head_contrast_keeps_foreground_area_shape_and_threshold():
    trimap = np.ones((224, 224), dtype=np.uint8)
    head = np.zeros_like(trimap, dtype=bool)
    head[:70, :70] = True
    pairs = e.head_pair(trimap, head, CFG)
    assert len(pairs) == 2 and [r[0] for r in pairs] == ['high', 'low']
    a, b = pairs[0][1], pairs[1][1]
    assert a[1].mean() == b[1].mean() == .75
    assert abs(a[3] - b[3]) <= .03
    assert a[4] - b[4] >= .2
    assert np.linalg.norm(np.array(a[2]) - np.array(b[2])) >= 4
    assert [r[1][0] for r in pairs] == [r[1][0] for r in e.head_pair(trimap, head, CFG)]


def test_head_pair_ineligible_threshold_is_not_relaxed():
    trimap = np.ones((224, 224), dtype=np.uint8)
    assert e.head_pair(trimap, np.ones_like(trimap, dtype=bool), CFG) == []


def test_fill_variants_keep_identical_visible_pixels_and_single_clean(tmp_path):
    for folder in ['images', 'annotations/trimaps']:
        (tmp_path / 'data/raw' / folder).mkdir(parents=True)
    rgb = np.arange(224 * 224 * 3, dtype=np.uint32).reshape(224, 224, 3).astype(np.uint8)
    Image.fromarray(rgb).save(tmp_path / 'data/raw/images/sample.jpg')
    Image.fromarray(np.ones((224, 224), dtype=np.uint8)).save(tmp_path / 'data/raw/annotations/trimaps/sample.png')
    rows, eligibility, inputs = e.make_conditions(tmp_path, [{'image_id': 'sample', 'label': 0, 'cohort': 'primary'}], CFG)
    assert len(rows) == 21 and len({r['condition_id'] for r in rows}) == 21
    assert len([r for r in rows if r['pattern'] == 'clean']) == 1
    assert len(inputs) == 1 and eligibility[0]['eligible']
    rgb, _ = e.load_image(tmp_path, 'sample')
    for i in range(1, len(rows), 2):
        a, b = rows[i:i + 2]
        assert a['mask_hex'] == b['mask_hex'] and {a['fill'], b['fill']} == {0, 128}
        mask = e.decode_mask(a['mask_hex'], 224, 14)
        first, second = [e.apply_mask(rgb, mask, r['fill']) for r in [a, b]]
        assert np.array_equal(first[mask], second[mask])
        assert (first[~mask] == 128).all() and (second[~mask] == 0).all()


def test_new_sampling_fails_instead_of_silently_reducing_class_counts():
    with pytest.raises(ValueError, match='Insufficient class'):
        e.choose_balanced([{'label': 0, 'image_id': 'x'}], 2, np.random.default_rng(1))


def test_frozen_configuration_cannot_be_overwritten(tmp_path):
    p = tmp_path / 'frozen.json'
    e.write_json(p, {'seed': 1})
    e.write_json(p, {'seed': 1})
    with pytest.raises(ValueError, match='Refuse to change frozen input'):
        e.write_json(p, {'seed': 2})


def test_frozen_multiclass_head_uses_classes_and_normalized_probabilities():
    head = {'coef': np.array([[1., 0.], [0., 1.]]), 'intercept': np.zeros(2), 'classes': np.array([5, 9])}
    label, prob = e.predict(np.eye(2), head)
    assert label.tolist() == [5, 9]
    assert np.allclose(prob.sum(axis=1), 1)
    assert np.all((prob > 0) & (prob < 1))

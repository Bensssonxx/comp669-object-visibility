import io
import tarfile
import numpy as np
import pytest

from occlusion_visibility.masks import apply_mask, coverage, select_pairs, visibility_mask
from occlusion_visibility.data import safe_extract


@pytest.mark.parametrize("pattern", ["prefix", "suffix", "center", "random"])
@pytest.mark.parametrize("fraction", [0, 0.25, 0.5, 0.75, 1])
def test_exact_pixel_budget(pattern, fraction):
    mask = visibility_mask(pattern, fraction, seed=2)
    assert mask.shape == (224, 224)
    assert mask.sum() == round(256 * fraction) * 14 * 14


def test_pixels_and_semantics():
    rgb = np.full((224, 224, 3), 213, dtype=np.uint8)
    visible = visibility_mask("prefix", 0.5)
    output = apply_mask(rgb, visible)
    assert (output[visible] == 213).all()
    assert (output[~visible] == 128).all()
    assert (rgb == 213).all()
    trimap = np.full((224, 224), 2, dtype=np.uint8)
    trimap[:112] = 1
    trimap[-1] = 3
    assert coverage(trimap, visible)["object_visibility"] == 1
    assert coverage(trimap, ~visible)["object_visibility"] == 0
    assert coverage(trimap, visible)["background_visibility"] == 0


def test_random_reproducibility_and_matched_pair():
    assert np.array_equal(visibility_mask("random", 0.5, seed=3), visibility_mask("random", 0.5, seed=3))
    assert not np.array_equal(visibility_mask("random", 0.5, seed=3), visibility_mask("random", 0.5, seed=4))
    trimap = np.full((224, 224), 2, dtype=np.uint8)
    trimap[56:168, 56:168] = 1
    rows = select_pairs(trimap)
    assert len(rows) == 4
    for _, _, (_, mask, _, _) in rows:
        assert mask.sum() == 224 * 224 * 0.75
    matched = [item[-1] for item in rows if item[0] == "visibility_matched"]
    assert abs(matched[0][3] - matched[1][3]) <= 0.03


def test_invalid_or_empty_annotations_fail():
    with pytest.raises(ValueError):
        coverage(np.full((224, 224), 2), visibility_mask("prefix", 0.5))
    with pytest.raises(ValueError):
        coverage(np.zeros((224, 224)), visibility_mask("prefix", 0.5))


def test_archive_traversal_rejected(tmp_path):
    archive = tmp_path / "bad.tar"
    with tarfile.open(archive, "w") as t:
        info = tarfile.TarInfo("../outside.txt")
        info.size = 1
        t.addfile(info, io.BytesIO(b"x"))
    with pytest.raises(ValueError):
        safe_extract(archive, tmp_path / "out")

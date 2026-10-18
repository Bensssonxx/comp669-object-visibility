import numpy as np
from occlusion_visibility.experiment import mask_hex, decode_mask
from occlusion_visibility.masks import visibility_mask, stable_seed


def test_serialized_masks_round_trip_and_nested_random_budgets():
    seed = stable_seed(6692026, "sample", 0)
    previous = np.zeros((224, 224), dtype=bool)
    for fraction in [.25, .5, .75, 1.]:
        mask = visibility_mask("random", fraction, seed=seed)
        restored = decode_mask(mask_hex(mask, 14), 224, 14)
        assert np.array_equal(mask, restored)
        assert (mask[previous]).all()
        previous = mask

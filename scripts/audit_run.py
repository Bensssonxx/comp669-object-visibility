"""Fail-fast integration audit of real manifests, condition metadata and completed predictions."""
import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from occlusion_visibility.data import load_image
from occlusion_visibility.experiment import decode_mask
from occlusion_visibility.masks import coverage

parser = argparse.ArgumentParser()
parser.add_argument("--run", default="pilot_v1")
parser.add_argument("--require-predictions", action="store_true")
args = parser.parse_args()
root = Path.cwd()
out = root / "results" / args.run
config = json.loads((out / "config.json").read_text())
manifest = json.loads((out / "manifest.json").read_text())
ids = [r["image_id"] for r in manifest]
assert len(ids) == len(set(ids))
assert len({r["image_sha256"] for r in manifest}) == len(ids)
for split, amount in [("train", config["train_per_class"]), ("val", config["val_per_class"]), ("test", config["test_per_class"])]:
    counts = Counter(r["label"] for r in manifest if r["split"] == split)
    assert len(counts) == 37 and set(counts.values()) == {amount}
conditions = pd.read_csv(out / "conditions.csv", keep_default_na=False)
assert set(conditions.image_id) == {r["image_id"] for r in manifest if r["split"] == "test"}
assert len(conditions[conditions.pattern == "clean"]) == 37 * config["test_per_class"]
for image_id, rows in conditions.groupby("image_id", sort=False):
    _, trimap = load_image(root, image_id)
    for row in rows.itertuples():
        mask = decode_mask(row.mask_hex, config["size"], config["patch"])
        measurements = coverage(trimap, mask)
        for key in ["visible_fraction", "object_visibility", "unknown_fraction"]:
            assert abs(measurements[key] - getattr(row, key)) < 1e-10, (image_id, key)
        assert abs(mask.mean() - row.fraction) < 1e-10
    matched = rows[rows.pair_type == "visibility_matched"]
    if len(matched):
        assert len(matched) == 2
        assert matched.object_visibility.max() - matched.object_visibility.min() <= config["pair_caliper"] + 1e-10
        assert np.allclose(matched.fraction, .75)
predictions = []
reproduced_classifiers = []
for model in ["aimv2", "dinov2"]:
    path = out / f"{model}_predictions.csv"
    if not path.exists():
        if args.require_predictions:
            raise FileNotFoundError(path)
        continue
    data = pd.read_csv(path, keep_default_na=False)
    assert len(data) == len(conditions)
    for col in ["image_id", "pattern", "mask_sha256", "label", "pair_type", "pair_role", "repeat"]:
        assert data[col].tolist() == conditions[col].tolist(), (model, col)
    assert np.array_equal(data.correct, (data.prediction == data.label).astype(int))
    assert np.isfinite(data.target_probability).all() and data.target_probability.between(0, 1).all()
    saved_head = out / "classifiers" / f"{model}_linear.npz"
    saved_features = out / "features" / f"{model}_evaluation.npy"
    if saved_head.exists() and saved_features.exists():
        head = np.load(saved_head)
        features = np.load(saved_features, mmap_mode="r")
        assert features.shape == (len(data), 1024) and np.isfinite(features).all()
        logits = features @ head["coef"].T + head["intercept"]
        reconstructed = head["classes"][logits.argmax(axis=1)]
        assert np.array_equal(reconstructed, data.prediction), model
        probabilities = np.exp(logits - logits.max(axis=1, keepdims=True))
        probabilities /= probabilities.sum(axis=1, keepdims=True)
        assert np.allclose(probabilities[np.arange(len(data)), data.label], data.target_probability, atol=1e-10), model
        reproduced_classifiers.append(model)
    predictions.append(model)
audit = {"passed": True, "split_counts": dict(Counter(r["split"] for r in manifest)),
    "all_37_classes_balanced": True, "exact_duplicate_bytes_across_samples": False,
    "condition_rows": len(conditions), "all_stored_coverage_recomputed": True,
    "matched_caliper_verified": True, "completed_prediction_models": predictions,
    "cached_classifier_prediction_reproduction_verified": reproduced_classifiers,
    "zero_foreground_annotation_exclusions": len(json.loads((out / "annotation_exclusions.json").read_text()))}
(out / "integration_audit.json").write_text(json.dumps(audit, indent=2))
print(json.dumps(audit, indent=2))

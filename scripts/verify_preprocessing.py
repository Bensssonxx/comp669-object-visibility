"""Verify canonical resized RGB/trimap hashes; optionally replay one encoder batch."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import features

from occlusion_visibility.data import load_image
from occlusion_visibility.experiment import decode_mask
from occlusion_visibility.masks import apply_mask

parser = argparse.ArgumentParser()
parser.add_argument("--run", default="pilot_v1")
parser.add_argument("--record", action="store_true", help="Record only in the original reference decoder environment.")
parser.add_argument("--encoders", action="store_true", help="Compare first 8 cached conditions for each encoder.")
args = parser.parse_args()
root = Path.cwd()
out = root / "results" / args.run
manifest = json.loads((out / "manifest.json").read_text())
rows = []
for r in manifest:
    rgb, trimap = load_image(root, r["image_id"])
    rows.append({"image_id": r["image_id"], "rgb_sha256": hashlib.sha256(rgb.tobytes()).hexdigest(),
                 "trimap_sha256": hashlib.sha256(trimap.tobytes()).hexdigest()})
actual = pd.DataFrame(rows)
path = out / "preprocessing_fingerprints.csv"
if args.record:
    assert features.version_codec("jpg") == "9.0" and features.version_feature("libjpeg_turbo") is None
    if path.exists():
        assert actual.equals(pd.read_csv(path)), "Existing reference hashes cannot be overwritten with different inputs."
    else:
        actual.to_csv(path, index=False)
expected = pd.read_csv(path)
assert actual.image_id.tolist() == expected.image_id.tolist()
rgb_matches = (actual.rgb_sha256 == expected.rgb_sha256)
trimap_matches = (actual.trimap_sha256 == expected.trimap_sha256)
check = {"images": len(actual), "rgb_matches": int(rgb_matches.sum()), "trimap_matches": int(trimap_matches.sum()),
         "jpeg_api_version": features.version_codec("jpg"), "libjpeg_turbo": features.version_feature("libjpeg_turbo"),
         "all_match": bool(rgb_matches.all() and trimap_matches.all()), "record_mode": args.record}
if not check["all_match"]:
    print(json.dumps(check, indent=2))
    raise RuntimeError("Decoded inputs differ from pilot_v1. Use the pinned reference conda environment; do not reuse its feature cache under another decoder.")
if args.encoders:
    from occlusion_visibility.encoders import FrozenEncoder
    config = json.loads((out / "config.json").read_text())
    conditions = pd.read_csv(out / "conditions.csv").head(8)
    pixels = []
    for r in conditions.itertuples():
        rgb, _ = load_image(root, r.image_id)
        pixels.append(apply_mask(rgb, decode_mask(r.mask_hex, 224, 14), config["fill"]))
    check["encoder_batches"] = []
    for name in ["aimv2", "dinov2"]:
        model = FrozenEncoder(root, name, config["device"])
        value = model.encode(np.stack(pixels))
        cached = np.load(out / "features" / f"{name}_evaluation.npy", mmap_mode="r")[:8]
        match = bool(np.allclose(value, cached, atol=1e-4))
        check["encoder_batches"].append({"model": name, "conditions": 8,
             "max_abs_feature_difference": float(np.abs(value-cached).max()), "matches_at_atol_1e_4": match})
        del model
        import torch
        torch.mps.empty_cache()
        assert match, name
    check["scope"] = "All selected preprocessed inputs; first 8 model conditions each. Not a second full experiment."
    (root / "docs/REFERENCE_REPLAY_CHECK.json").write_text(json.dumps(check, indent=2))
print(json.dumps(check, indent=2))

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import time
from functools import lru_cache
from pathlib import Path

import numpy as np

from .data import build_manifest, load_image, sha256_file
from .masks import apply_mask, coverage, select_pairs, stable_seed, visibility_mask


def mask_hex(mask: np.ndarray, patch: int) -> str:
    return np.packbits(mask[::patch, ::patch].ravel()).tobytes().hex()


def decode_mask(code: str, size: int, patch: int) -> np.ndarray:
    g = size // patch
    bits = np.unpackbits(np.frombuffer(bytes.fromhex(code), dtype=np.uint8))[:g * g]
    return np.repeat(np.repeat(bits.reshape(g, g), patch, axis=0), patch, axis=1).astype(bool)


def evaluation_rows(root: Path, manifest: list[dict], config: dict):
    output = []
    for sample in manifest:
        if sample["split"] != "test":
            continue
        _, trimap = load_image(root, sample["image_id"], config["size"])
        entries = [("standard", "clean", 1.0, 0, "", "", visibility_mask("clean", 1.0))]
        for fraction in config["fractions"]:
            for pattern in ["prefix", "suffix", "center", "random"]:
                for repeat in (config["random_seeds"] if pattern == "random" else [0]):
                    mask = visibility_mask(pattern, fraction, size=config["size"], patch=config["patch"],
                                           seed=stable_seed(config["seed"], sample["image_id"], repeat))
                    entries.append(("standard", pattern, fraction, repeat, "", "", mask))
        for pair_type, role, (name, mask, _, _) in select_pairs(trimap, caliper=config["pair_caliper"]):
            entries.append(("paired", name, float(mask.mean()), 0,
                            pair_type, role, mask))
        for suite, pattern, fraction, repeat, pair_type, role, mask in entries:
            code = mask_hex(mask, config["patch"])
            output.append(dict(sample, suite=suite, pattern=pattern, fraction=fraction, repeat=repeat,
                               pair_type=pair_type, pair_role=role, mask_hex=code,
                               mask_sha256=hashlib.sha256(bytes.fromhex(code)).hexdigest(), **coverage(trimap, mask)))
    return output


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def prepare(root: Path, config: dict):
    out = root / "results" / config["run_name"]
    out.mkdir(parents=True, exist_ok=True)
    config_path = out / "config.json"
    if config_path.exists() and json.loads(config_path.read_text()) != config:
        raise ValueError("Run name already used with a different configuration; choose a new run name.")
    config_path.write_text(json.dumps(config, indent=2))
    manifest = build_manifest(root, config)
    rows = evaluation_rows(root, manifest, config)
    write_csv(out / "conditions.csv", rows)
    for name in ["images", "annotations"]:
        if (root / "data/raw" / (name + ".tar.gz")).exists():
            print("sha256", name, sha256_file(root / "data/raw" / (name + ".tar.gz")), flush=True)
    return manifest, rows


def feature_cache(root: Path, out: Path, name: str, tag: str, rows: list[dict], config: dict, encoder):
    directory = out / "features"
    directory.mkdir(exist_ok=True)
    path = directory / f"{name}_{tag}.npy"
    metadata_path = directory / f"{name}_{tag}.json"
    # Cache binding covers order, full config, implementation and upstream revisions/weights.
    code_hash = hashlib.sha256()
    for source in sorted(Path(__file__).parent.glob("*.py")):
        code_hash.update(source.read_bytes())
    weight = root / "models" / ("aimv2-large-patch14-224.safetensors" if name == "aimv2" else "dinov2_vitl14_pretrain.pth")
    binding = {"rows": rows, "config": config, "code_hash": code_hash.hexdigest(),
               "weights_sha256": sha256_file(weight), "normalization": "imagenet", "pooling": "mean_patch_l2"}
    fingerprint = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()
    if metadata_path.exists():
        if json.loads(metadata_path.read_text())["fingerprint"] != fingerprint:
            raise ValueError("Stale feature cache. Use a new run directory or remove only this run's feature cache.")
        features = np.lib.format.open_memmap(path, mode="r+")
    else:
        features = np.lib.format.open_memmap(path, mode="w+", dtype="float32", shape=(len(rows), 1024))
        features[:] = np.nan
        features.flush()
        metadata_path.write_text(json.dumps({"fingerprint": fingerprint, "binding": binding}, indent=2))
    @lru_cache(maxsize=64)
    def image(image_id):
        return load_image(root, image_id, config["size"])[0]
    pending = np.flatnonzero(~np.isfinite(features).all(axis=1))
    started = time.monotonic()
    for start in range(0, len(pending), config["batch_size"]):
        indices = pending[start:start + config["batch_size"]]
        pixels = []
        for i in indices:
            row = rows[int(i)]
            rgb = image(row["image_id"])
            if "mask_hex" in row:
                rgb = apply_mask(rgb, decode_mask(row["mask_hex"], config["size"], config["patch"]), config["fill"])
            pixels.append(rgb)
        batch = encoder.encode(np.stack(pixels))
        if not np.isfinite(batch).all():
            raise ValueError("Non-finite encoder output; do not save predictions.")
        features[indices] = batch
        features.flush()
        if start == 0 or (start // config["batch_size"] + 1) % 10 == 0 or start + len(indices) == len(pending):
            done = start + len(indices)
            print(f"{name} {tag}: {done}/{len(pending)} ({done / max(time.monotonic()-started, 0.001):.1f} img/s)", flush=True)
    return np.asarray(features)


def run_model(root: Path, config: dict, name: str):
    import torch
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score
    from .encoders import FrozenEncoder
    out = root / "results" / config["run_name"]
    manifest = json.loads((out / "manifest.json").read_text())
    with (out / "conditions.csv").open() as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["label"] = int(row["label"])
    trainval = [r for r in manifest if r["split"] in ["train", "val"]]
    encoder = FrozenEncoder(root, name, config["device"])
    print("benchmark", name, encoder.benchmark(config["batch_size"]), flush=True)
    x = feature_cache(root, out, name, "clean_trainval", trainval, config, encoder)
    y = np.array([r["label"] for r in trainval])
    train = np.array([r["split"] == "train" for r in trainval])
    scores, candidates = [], []
    for c in config["C_grid"]:
        clf = LogisticRegression(C=c, max_iter=2000, solver="lbfgs", random_state=config["seed"])
        clf.fit(x[train], y[train])
        score = accuracy_score(y[~train], clf.predict(x[~train]))
        scores.append({"C": c, "val_accuracy": float(score), "iterations": int(clf.n_iter_.max())})
        candidates.append(clf)
    best = int(np.argmax([s["val_accuracy"] for s in scores]))
    clf = candidates[best]  # no test-label selection and no silent refit on validation.
    print("probe selection", name, scores, "chosen", scores[best], flush=True)
    (out / f"{name}_probe.json").write_text(json.dumps({"validation": scores, "chosen": scores[best],
          "training": "clean train only; held-out val selects C; no refit", "pooling": config["pooling"]}, indent=2))
    classifiers = out / "classifiers"
    classifiers.mkdir(exist_ok=True)
    np.savez(classifiers / f"{name}_linear.npz", coef=clf.coef_, intercept=clf.intercept_, classes=clf.classes_)
    test_features = feature_cache(root, out, name, "evaluation", rows, config, encoder)
    probabilities = clf.predict_proba(test_features)
    prediction = clf.classes_[probabilities.argmax(axis=1)]
    results = []
    for i, row in enumerate(rows):
        results.append(dict(row, model=name, prediction=int(prediction[i]), correct=int(prediction[i] == row["label"]),
                            target_probability=float(probabilities[i, row["label"]])))
    write_csv(out / f"{name}_predictions.csv", results)
    print("Saved", out / f"{name}_predictions.csv", flush=True)
    del encoder
    if config["device"] == "mps":
        torch.mps.empty_cache()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["prepare", "run", "benchmark"])
    parser.add_argument("--config", default="configs/pilot.json")
    parser.add_argument("--model", choices=["aimv2", "dinov2"])
    args = parser.parse_args()
    root = Path.cwd()
    config = json.loads((root / args.config).read_text())
    if args.stage == "prepare":
        prepare(root, config)
    elif args.stage == "run":
        if not args.model:
            parser.error("--model is required")
        run_model(root, config, args.model)
    else:
        from .encoders import FrozenEncoder
        if not args.model:
            parser.error("--model is required")
        print(FrozenEncoder(root, args.model, config["device"]).benchmark(config["batch_size"]), flush=True)


if __name__ == "__main__":
    main()

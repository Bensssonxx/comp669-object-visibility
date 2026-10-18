from __future__ import annotations

import hashlib
import json
import tarfile
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_extract(archive: Path, destination: Path):
    """Extract regular files only; reject traversal, symlinks and device members."""
    destination = destination.resolve()
    with tarfile.open(archive) as tar:
        members = []
        for member in tar.getmembers():
            target = (destination / member.name).resolve()
            if not target.is_relative_to(destination) or not (member.isfile() or member.isdir()):
                raise ValueError(f"Unsafe archive entry: {member.name}")
            # macOS resource forks are not research inputs.
            if any(part.startswith("._") for part in Path(member.name).parts):
                continue
            members.append(member)
        tar.extractall(destination, members=members, filter="data")


def read_split(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            name, label, species, breed = line.split()
            rows.append({"image_id": name, "label": int(label) - 1, "species": int(species)})
    return rows


def build_manifest(root: Path, config: dict):
    raw = root / "data/raw"
    for archive, directory in [("annotations.tar.gz", "annotations"), ("images.tar.gz", "images")]:
        if not (raw / directory).exists():
            safe_extract(raw / archive, raw)
    trainval = read_split(raw / "annotations/trainval.txt")
    test = read_split(raw / "annotations/test.txt")
    assert not ({r["image_id"] for r in trainval} & {r["image_id"] for r in test})
    excluded = []
    def valid_annotations(rows, split):
        accepted = []
        for row in rows:
            path = raw / "annotations/trimaps" / (row["image_id"] + ".png")
            with Image.open(path) as annotation:
                trimap = np.array(annotation.resize((config["size"], config["size"]), Image.Resampling.NEAREST))
            if not np.isin(trimap, [1, 2, 3]).all() or not (trimap == 1).any():
                excluded.append(dict(row, official_split=split, reason="invalid labels or no foreground after shared resize"))
            else:
                accepted.append(row)
        return accepted
    # Annotation-only exclusion before sampling, never based on model correctness.
    trainval = valid_annotations(trainval, "trainval")
    test = valid_annotations(test, "test")
    rng = np.random.default_rng(config["seed"])
    manifest = []
    for label in range(37):
        candidates = sorted([r for r in trainval if r["label"] == label], key=lambda r: r["image_id"])
        indices = rng.permutation(len(candidates))
        n_train, n_val = config["train_per_class"], config["val_per_class"]
        if n_train + n_val > len(candidates):
            raise ValueError("Insufficient trainval samples; never borrow from test.")
        for split, ix in [("train", indices[:n_train]), ("val", indices[n_train:n_train + n_val])]:
            manifest.extend([dict(candidates[int(i)], split=split) for i in ix])
        candidates = sorted([r for r in test if r["label"] == label], key=lambda r: r["image_id"])
        ix = rng.permutation(len(candidates))[:config["test_per_class"]]
        manifest.extend([dict(candidates[int(i)], split="test") for i in ix])
    seen = set()
    for row in manifest:
        assert row["image_id"] not in seen
        seen.add(row["image_id"])
        for kind, ext in [("images", ".jpg"), ("annotations/trimaps", ".png")]:
            if not (raw / kind / (row["image_id"] + ext)).is_file():
                raise FileNotFoundError(row["image_id"])
        row["image_sha256"] = sha256_file(raw / "images" / (row["image_id"] + ".jpg"))
        row["annotation_sha256"] = sha256_file(raw / "annotations/trimaps" / (row["image_id"] + ".png"))
    # Exact byte duplicates cannot cross evaluation boundaries.
    hash_splits = {}
    for row in manifest:
        previous = hash_splits.setdefault(row["image_sha256"], row["split"])
        if previous != row["split"]:
            raise ValueError("Exact duplicate image bytes cross split boundaries.")
    out = root / "results" / config["run_name"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (out / "annotation_exclusions.json").write_text(json.dumps(excluded, indent=2))
    print("Annotation exclusions", len(excluded), flush=True)
    print("Manifest", dict(Counter(r["split"] for r in manifest)), flush=True)
    return manifest


def load_image(root: Path, image_id: str, size: int = 224):
    raw = root / "data/raw"
    with Image.open(raw / "images" / (image_id + ".jpg")) as img:
        rgb = np.array(img.convert("RGB").resize((size, size), Image.Resampling.BICUBIC))
    with Image.open(raw / "annotations/trimaps" / (image_id + ".png")) as mask:
        trimap = np.array(mask.resize((size, size), Image.Resampling.NEAREST))
    # Resize full frame identically (deliberate aspect-ratio distortion, no object crop).
    return rgb, trimap

"""Fetch public pinned assets. No credentials; verifies recorded SHA-256 before use."""
import json
import subprocess
from pathlib import Path

from occlusion_visibility.data import sha256_file

root = Path.cwd()
sources = json.loads((root / "docs/SOURCES.json").read_text())
mirror = sources["pet_image_mirror"]
assets = [
    (sources["aim_weights"]["url"], "models/aimv2-large-patch14-224.safetensors", sources["aim_weights"]["sha256"]),
    (sources["dino_weights"]["url"], "models/dinov2_vitl14_pretrain.pth", sources["dino_weights"]["sha256"]),
    (sources["pet_annotations"]["url"], "data/raw/annotations.tar.gz", sources["pet_annotations"]["sha256"]),
]
for f in mirror["files"]:
    split = f["split"]
    assets.append((f"https://huggingface.co/datasets/timm/oxford-iiit-pet/resolve/{mirror['revision']}/data/{split}-00000-of-00001.parquet",
                   f"data/raw/pets-{split}.parquet", f["sha256"]))
for url, name, expected in assets:
    destination = root / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and sha256_file(destination) == expected:
        print("Verified cached", name, flush=True)
        continue
    partial = destination.with_suffix(destination.suffix + ".download")
    subprocess.run(["curl", "--location", "--fail", "--show-error", "--retry", "3", "--connect-timeout", "20",
                    "--max-time", "1800", url, "--output", str(partial)], check=True)
    if sha256_file(partial) != expected:
        raise ValueError(f"Checksum mismatch: {name}")
    partial.replace(destination)
    print("Verified", name, flush=True)
# Minimal public metadata needed by the mirror importer, no account information.
(root / "docs/pets-mirror-metadata.json").write_text(json.dumps({"sha": mirror["revision"]}, indent=2))

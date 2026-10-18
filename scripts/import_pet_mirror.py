"""Import original JPEG bytes from a pinned timm mirror, validate official split/labels."""
import hashlib
import json
import tarfile
from pathlib import Path

import pyarrow.parquet as pq
from occlusion_visibility.data import read_split, safe_extract, sha256_file

root = Path.cwd()
raw = root / "data/raw"
if not (raw / "annotations").exists():
    safe_extract(raw / "annotations.tar.gz", raw)
images = raw / "images"
images.mkdir(exist_ok=True)
provenance = []
all_ids = set()
for split, official in [("train", "trainval"), ("test", "test")]:
    expected = {r["image_id"]: r["label"] for r in read_split(raw / f"annotations/{official}.txt")}
    seen = set()
    path = raw / f"pets-{split}.parquet"
    parquet = pq.ParquetFile(path)
    for batch in parquet.iter_batches(batch_size=128):
        for row in batch.to_pylist():
            name = Path(row["image"]["path"]).name
            image_id = Path(name).stem
            assert image_id in expected, image_id
            assert row["label"] == expected[image_id], image_id
            assert image_id not in all_ids, image_id
            all_ids.add(image_id)
            seen.add(image_id)
            destination = images / name
            destination.write_bytes(row["image"]["bytes"])
    assert seen == set(expected), (len(seen), len(expected))
    provenance.append({"split": split, "rows": len(seen), "sha256": sha256_file(path)})
sources_path = root / "docs/SOURCES.json"
sources = json.loads(sources_path.read_text())
previous_crosscheck = sources.get("pet_image_mirror", {}).get("official_archive_crosscheck")
sources["pet_image_mirror"] = {"repository": "https://huggingface.co/datasets/timm/oxford-iiit-pet",
    "revision": json.loads((root / "docs/pets-mirror-metadata.json").read_text())["sha"],
    "files": provenance, "validation": "All original filenames, 0-based breed labels and train/test membership exactly match official annotation lists."}
if previous_crosscheck:
    sources["pet_image_mirror"]["official_archive_crosscheck"] = previous_crosscheck
sources_path.write_text(json.dumps(sources, indent=2))
print("Imported and verified", len(all_ids), "original JPEGs", flush=True)

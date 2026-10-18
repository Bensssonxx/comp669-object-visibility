"""Render actual shared model inputs and annotation-dependent diagnostic pairs."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from occlusion_visibility.data import load_image
from occlusion_visibility.experiment import decode_mask
from occlusion_visibility.masks import apply_mask

parser = argparse.ArgumentParser()
parser.add_argument("--run", default="pilot_v1")
args = parser.parse_args()
root = Path.cwd()
out = root / "results" / args.run
config = json.loads((out / "config.json").read_text())
conditions = pd.read_csv(out / "conditions.csv", keep_default_na=False)
figures = out / "figures"
figures.mkdir(exist_ok=True)
test_ids = conditions.image_id.unique()
examples = [test_ids[i] for i in [0, 50, 100]]
fig, axes = plt.subplots(3, 5, figsize=(13, 8))
for row_index, image_id in enumerate(examples):
    rgb, trimap = load_image(root, image_id)
    axes[row_index, 0].imshow(rgb)
    axes[row_index, 0].contour(trimap == 1, levels=[.5], colors=["#00FFFF"], linewidths=.6)
    axes[row_index, 0].set_title(f"{image_id}\nForeground outline", fontsize=9)
    for column, pattern in enumerate(["prefix", "suffix", "center", "random"], start=1):
        r = conditions[(conditions.image_id == image_id) & (conditions.pattern == pattern) &
                       (conditions.fraction == .5) & (conditions.repeat == 0)].iloc[0]
        pixels = apply_mask(rgb, decode_mask(r.mask_hex, 224, 14), config["fill"])
        axes[row_index, column].imshow(pixels)
        axes[row_index, column].set_title(f"{pattern}: 50% image\n{r.object_visibility:.0%} foreground visible", fontsize=9)
    for ax in axes[row_index]:
        ax.axis("off")
fig.suptitle("Actual RGB inputs shared by both models; cyan annotation is not sent to the encoders")
fig.tight_layout()
fig.savefig(figures / "actual_inputs.png", dpi=160, bbox_inches="tight")
plt.close(fig)

fig, axes = plt.subplots(3, 5, figsize=(13, 8))
for row_index, image_id in enumerate(examples):
    rgb, _ = load_image(root, image_id)
    axes[row_index, 0].imshow(rgb)
    axes[row_index, 0].set_title(image_id, fontsize=9)
    for column, (pair_type, role) in enumerate([("object_contrast", "high"), ("object_contrast", "low"),
                                               ("visibility_matched", "a"), ("visibility_matched", "b")], start=1):
        g = conditions[(conditions.image_id == image_id) & (conditions.pair_type == pair_type) & (conditions.pair_role == role)]
        if len(g):
            r = g.iloc[0]
            axes[row_index, column].imshow(apply_mask(rgb, decode_mask(r.mask_hex, 224, 14), config["fill"]))
            axes[row_index, column].set_title(f"{pair_type.replace('_', ' ')} {role}\n{r.object_visibility:.1%} foreground visible", fontsize=8)
        else:
            axes[row_index, column].text(.5, .5, "No eligible pair", ha="center")
    for ax in axes[row_index]:
        ax.axis("off")
fig.suptitle("Annotation-selected diagnostic pairs; all square occluders hide exactly 25% of image area")
fig.tight_layout()
fig.savefig(figures / "diagnostic_inputs.png", dpi=160, bbox_inches="tight")
print("Saved input figures", figures)

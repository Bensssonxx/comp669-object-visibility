"""Illustrative post-hoc cases; counts/rates must come from the full paired table."""
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

root = Path.cwd()
out = root / "results/pilot_v1"
config = json.loads((out / "config.json").read_text())
tables = [pd.read_csv(out / f"{model}_predictions.csv", keep_default_na=False) for model in ["aimv2", "dinov2"]]
df = pd.concat(tables, ignore_index=True)
paired = df[df.pair_type == "visibility_matched"]
choices = []
for image_id, g in paired.groupby("image_id"):
    change, flip = [], []
    for model, m in g.groupby("model"):
        a, b = m[m.pair_role == "a"].iloc[0], m[m.pair_role == "b"].iloc[0]
        change.append(abs(a.target_probability - b.target_probability))
        flip.append(a.correct != b.correct)
    choices.append({"image_id": image_id, "max_target_probability_change": max(change), "any_correctness_flip": any(flip)})
ranking = sorted(choices, key=lambda r: (-r["any_correctness_flip"], -r["max_target_probability_change"], r["image_id"]))
chosen = ranking[:2]
stable = sorted([r for r in choices if not r["any_correctness_flip"]], key=lambda r: (r["max_target_probability_change"], r["image_id"]))
if stable:
    chosen.append(stable[0])
manifest = json.loads((out / "manifest.json").read_text())
labels = {r["label"]: r["image_id"].rsplit("_", 1)[0] for r in manifest}
fig, axes = plt.subplots(len(chosen), 3, figsize=(11, 4.1 * len(chosen)), squeeze=False)
case_rows = []
for i, case in enumerate(chosen):
    image_id = case["image_id"]
    rgb, _ = load_image(root, image_id)
    g = paired[paired.image_id == image_id]
    axes[i, 0].imshow(rgb)
    axes[i, 0].set_title(f"{image_id}\nTrue breed: {labels[int(g.iloc[0].label)]}", fontsize=10)
    for j, role in enumerate(["a", "b"], start=1):
        records = g[g.pair_role == role]
        row = records.iloc[0]
        axes[i, j].imshow(apply_mask(rgb, decode_mask(row.mask_hex, 224, 14), config["fill"]))
        lines = [f"Location {role.upper()}: {row.object_visibility:.1%} foreground visible"]
        for r in records.itertuples():
            lines.append(f"{r.model}: {labels[r.prediction]} ({'correct' if r.correct else 'wrong'}), p(true)={r.target_probability:.2f}")
            case_rows.append({"image_id": image_id, "model": r.model, "role": role, "object_visibility": r.object_visibility,
                              "true_label": labels[r.label], "prediction": labels[r.prediction], "correct": r.correct,
                              "target_probability": r.target_probability})
        axes[i, j].set_title("\n".join(lines), fontsize=8)
    for ax in axes[i]:
        ax.axis("off")
fig.suptitle("Post-hoc illustrations: two largest matched-visibility changes, plus one stable case\nAll masks hide 25% of image area; sample-selection rule is outcome-dependent and not used to estimate rates", fontsize=11)
fig.tight_layout()
fig.savefig(out / "figures/matched_visibility_cases.png", dpi=150, bbox_inches="tight")
(out / "qualitative_case_selection.json").write_text(json.dumps({
    "selection": "Two largest max cross-model absolute target-probability changes, prioritizing correctness flips; plus smallest-change nonflip example. Illustrative, post-hoc, not prevalence evidence.",
    "selected": chosen, "rows": case_rows}, indent=2))
print("Saved qualitative case figure and exact selection rule")

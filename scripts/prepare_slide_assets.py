"""Presentation assets derived exclusively from audited pilot predictions and inputs."""
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
destination = root / "milestone/assets"
destination.mkdir(parents=True, exist_ok=True)
audit = json.loads((out / "integration_audit.json").read_text())
assert set(audit["completed_prediction_models"]) == {"aimv2", "dinov2"}
summary = pd.read_csv(out / "summary.csv")
pairs = pd.read_csv(out / "paired_summary.csv")
conditions = pd.read_csv(out / "conditions.csv", keep_default_na=False)
config = json.loads((out / "config.json").read_text())
data = {"summary": summary.to_dict("records"), "pairs": pairs.to_dict("records"),
        "audit": audit, "config": config,
        "standardization": pd.read_csv(out / "visibility_standardization.csv").fillna("").to_dict("records")}
(root / "milestone/slide_data.json").write_text(json.dumps(data, indent=2))
plt.rcParams.update({"font.size": 13, "axes.spines.top": False, "axes.spines.right": False})

image_id = conditions.image_id.iloc[0]
rgb, _ = load_image(root, image_id)
for kind in ["ratios", "pairs"]:
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.8))
    if kind == "ratios":
        selections = [("clean", 1.), ("prefix", .75), ("prefix", .5), ("prefix", .25)]
        rows = [conditions[(conditions.image_id == image_id) & (conditions.pattern == p) & (conditions.fraction == v)].iloc[0] for p, v in selections]
        names = ["Complete", "75% image visible", "50% image visible", "25% image visible"]
    else:
        selections = [("object_contrast", "high"), ("object_contrast", "low"), ("visibility_matched", "a"), ("visibility_matched", "b")]
        rows = [conditions[(conditions.image_id == image_id) & (conditions.pair_type == p) & (conditions.pair_role == r)].iloc[0] for p, r in selections]
        names = ["More foreground", "Less foreground", "Matched location A", "Matched location B"]
    for ax, row, label in zip(axes, rows, names):
        ax.imshow(apply_mask(rgb, decode_mask(row.mask_hex, 224, 14), config["fill"]))
        ax.set_title(f"{label}\n{row.object_visibility:.1%} foreground visible", fontsize=14)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(destination / f"{kind}_inputs.png", dpi=170, bbox_inches="tight")
    plt.close(fig)

patterns = ["prefix", "suffix", "center", "random"]
colors = {"aimv2": "#0072B2", "dinov2": "#D55E00"}
fig, axes = plt.subplots(2, 2, figsize=(12, 6.2), sharex=True, sharey=True)
for ax, pattern in zip(axes.flat, patterns):
    for model in ["aimv2", "dinov2"]:
        g = summary[(summary.model == model) & summary.pattern.isin([pattern, "clean"])].sort_values("fraction")
        ax.plot(g.fraction * 100, g.accuracy * 100, marker="o" if model == "aimv2" else "s", color=colors[model], label=model)
        ax.fill_between(g.fraction * 100, g.ci_low * 100, g.ci_high * 100, alpha=.12, color=colors[model])
    ax.set_title(pattern, fontsize=16)
    ax.set_xticks([25, 50, 75, 100])
    ax.set_ylim(0, 100)
    ax.grid(axis="y", alpha=.15)
axes[0, 1].legend(loc="lower right", fontsize=12)
for ax in axes[:, 0]: ax.set_ylabel("Accuracy (%)", fontsize=14)
for ax in axes[1, :]: ax.set_xlabel("Visible image area (%)", fontsize=14)
fig.tight_layout()
fig.savefig(destination / "accuracy_curves.png", dpi=170, bbox_inches="tight")
plt.close(fig)

visibility = conditions[(conditions.suite == "standard") & (conditions.fraction == .5)]
visibility = visibility.groupby(["image_id", "pattern"], as_index=False).object_visibility.mean()
fig, ax = plt.subplots(figsize=(10, 4.1))
ax.boxplot([visibility[visibility.pattern == p].object_visibility * 100 for p in patterns], tick_labels=patterns, showfliers=False)
ax.set_ylabel("Foreground visible (%)", fontsize=15)
ax.set_ylim(0, 105)
ax.grid(axis="y", alpha=.15)
fig.tight_layout()
fig.savefig(destination / "foreground_coverage.png", dpi=170, bbox_inches="tight")
plt.close(fig)

# The example is explicitly post-hoc, selected using a stored deterministic rule.
cases = json.loads((out / "qualitative_case_selection.json").read_text())
image_id = cases["selected"][0]["image_id"]
rgb, _ = load_image(root, image_id)
case_rows = cases["rows"]
fig, axes = plt.subplots(1, 3, figsize=(12, 4.4))
axes[0].imshow(rgb)
axes[0].set_title(image_id, fontsize=14)
for j, role in enumerate(["a", "b"], start=1):
    row = conditions[(conditions.image_id == image_id) & (conditions.pair_type == "visibility_matched") & (conditions.pair_role == role)].iloc[0]
    axes[j].imshow(apply_mask(rgb, decode_mask(row.mask_hex, 224, 14), config["fill"]))
    lines = [f"{row.object_visibility:.1%} foreground visible"]
    for r in case_rows:
        if r["image_id"] == image_id and r["role"] == role:
            lines.append(f"{r['model']}: {'correct' if r['correct'] else 'wrong'} (p={r['target_probability']:.2f})")
    axes[j].set_title("\n".join(lines), fontsize=13)
for ax in axes: ax.axis("off")
fig.tight_layout()
fig.savefig(destination / "matched_case.png", dpi=170, bbox_inches="tight")
plt.close(fig)
print("Prepared slide assets from real audited results")

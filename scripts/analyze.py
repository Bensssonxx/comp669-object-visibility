"""Analyze saved predictions; original image, not mask, is the sampling unit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def cluster_ci(values, seed=6692026, n=2000):
    values = np.asarray(values, dtype=float)
    if not len(values):
        return [None, None]
    rng = np.random.default_rng(seed)
    means = np.mean(values[rng.integers(0, len(values), size=(n, len(values)))], axis=1)
    return np.quantile(means, [0.025, 0.975]).tolist()


def collapse_repetitions(standard):
    """Return one observation per original image, model, pattern and budget."""
    return standard.groupby(["model", "image_id", "label", "pattern", "fraction"], as_index=False).agg(
        correct=("correct", "mean"), object_visibility=("object_visibility", "mean"),
        background_visibility=("background_visibility", "mean"), target_probability=("target_probability", "mean"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default="pilot_v1")
    args = parser.parse_args()
    out = Path("results") / args.run
    config = json.loads((out / "config.json").read_text())
    paths = sorted(out.glob("*_predictions.csv"))
    if not paths:
        raise ValueError("No real prediction files. Run inference first.")
    df = pd.concat([pd.read_csv(p, keep_default_na=False) for p in paths], ignore_index=True)
    key = ["image_id", "suite", "pattern", "fraction", "repeat", "pair_type", "pair_role"]
    assert not df.duplicated(["model"] + key).any()
    if df.model.nunique() == 2:
        a, b = [g.set_index(key).sort_index() for _, g in df.groupby("model")]
        assert a.index.equals(b.index), "Cross-model comparisons must use identical conditions."
        assert (a.mask_sha256 == b.mask_sha256).all()
    standard = df[df.suite == "standard"]
    # Three random masks collapse to one per-original-image outcome before uncertainty.
    per_image = collapse_repetitions(standard)
    summary = []
    for (model, pattern, fraction), g in per_image.groupby(["model", "pattern", "fraction"]):
        lo, hi = cluster_ci(g.correct, n=config["bootstrap_repetitions"])
        summary.append(dict(model=model, pattern=pattern, fraction=fraction, n_images=len(g),
            accuracy=float(g.correct.mean()), ci_low=lo, ci_high=hi,
            mean_object_visibility=float(g.object_visibility.mean()),
            object_visibility_min=float(g.object_visibility.min()), object_visibility_max=float(g.object_visibility.max())))
    summary = pd.DataFrame(summary)
    clean = summary[summary.pattern == "clean"].set_index("model").accuracy.to_dict()
    summary["clean_accuracy"] = summary.model.map(clean)
    summary["accuracy_retention"] = summary.accuracy / summary.clean_accuracy
    summary["accuracy_drop"] = summary.clean_accuracy - summary.accuracy
    summary.to_csv(out / "summary.csv", index=False)

    paired_summary = []
    for (model, pair_type), g in df[df.suite == "paired"].groupby(["model", "pair_type"]):
        role_a, role_b = ("high", "low") if pair_type == "object_contrast" else ("a", "b")
        a = g[g.pair_role == role_a].set_index("image_id")
        b = g[g.pair_role == role_b].set_index("image_id")
        assert a.index.equals(b.index)
        assert np.allclose(a.visible_fraction, b.visible_fraction)
        differences = a.correct.to_numpy() - b.correct.to_numpy()
        lo, hi = cluster_ci(differences, n=config["bootstrap_repetitions"])
        flips = (a.correct.to_numpy() != b.correct.to_numpy()).astype(float)
        changes = (a.prediction.to_numpy() != b.prediction.to_numpy()).astype(float)
        flip_lo, flip_hi = cluster_ci(flips, n=config["bootstrap_repetitions"])
        change_lo, change_hi = cluster_ci(changes, n=config["bootstrap_repetitions"])
        paired_summary.append(dict(model=model, pair_type=pair_type, n_images=len(a),
            role_a=role_a, role_b=role_b, accuracy_a=float(a.correct.mean()), accuracy_b=float(b.correct.mean()),
            paired_accuracy_difference=float(differences.mean()), difference_ci_low=lo, difference_ci_high=hi,
            correctness_discordance=float(flips.mean()), correctness_discordance_ci_low=flip_lo, correctness_discordance_ci_high=flip_hi,
            prediction_disagreement=float(changes.mean()), prediction_disagreement_ci_low=change_lo, prediction_disagreement_ci_high=change_hi,
            mean_abs_target_probability_difference=float(np.abs(a.target_probability.to_numpy() - b.target_probability.to_numpy()).mean()),
            mean_object_visibility_a=float(a.object_visibility.mean()), mean_object_visibility_b=float(b.object_visibility.mean()),
            max_pair_object_visibility_difference=float(np.abs(a.object_visibility.to_numpy() - b.object_visibility.to_numpy()).max())))
    pairs = pd.DataFrame(paired_summary)
    pairs.to_csv(out / "paired_summary.csv", index=False)

    # Model differences are paired by original image and condition.
    if df.model.nunique() == 2:
        model_differences = []
        for (pattern, fraction), g in per_image.groupby(["pattern", "fraction"]):
            table = g.pivot(index="image_id", columns="model", values="correct")
            diff = table.aimv2 - table.dinov2
            lo, hi = cluster_ci(diff, n=config["bootstrap_repetitions"])
            model_differences.append(dict(pattern=pattern, fraction=fraction, n_images=len(diff),
                aim_minus_dino=float(diff.mean()), ci_low=lo, ci_high=hi))
        pd.DataFrame(model_differences).to_csv(out / "paired_model_differences.csv", index=False)
        matched = df[df.pair_type == "visibility_matched"]
        flip_data = matched.pivot(index="image_id", columns=["model", "pair_role"], values="correct")
        differences = ((flip_data["aimv2"]["a"] != flip_data["aimv2"]["b"]).astype(int) -
                       (flip_data["dinov2"]["a"] != flip_data["dinov2"]["b"]).astype(int))
        lo, hi = cluster_ci(differences, n=config["bootstrap_repetitions"])
        pd.DataFrame([dict(metric="matched_correctness_flip_rate", n_images=len(differences),
                           aim_minus_dino=float(differences.mean()), ci_low=lo, ci_high=hi)]).to_csv(
            out / "paired_diagnostic_model_differences.csv", index=False)

    # Descriptive common-support reweighting, with counts and explicit non-estimability.
    patterns = ["prefix", "suffix", "center", "random"]
    adjusted, counts = [], []
    for (model, fraction), g in per_image[per_image.pattern != "clean"].groupby(["model", "fraction"]):
        g = g.copy()
        g["visibility_bin"] = np.minimum((g.object_visibility * 5).astype(int), 4)
        bins = g.groupby(["pattern", "visibility_bin"]).agg(n=("correct", "size"), accuracy=("correct", "mean")).reset_index()
        for row in bins.to_dict("records"):
            counts.append(dict(model=model, fraction=fraction, **row))
        n_table = bins.pivot(index="visibility_bin", columns="pattern", values="n").reindex(columns=patterns, fill_value=0).fillna(0)
        support = n_table.index[(n_table >= 5).all(axis=1)]
        if not len(support):
            adjusted.append(dict(model=model, fraction=fraction, pattern="all", estimable=False,
                                 common_bins="", n_common_support=0, standardized_accuracy=None))
            continue
        weights = n_table.loc[support].min(axis=1)
        weights = weights / weights.sum()
        for pattern in patterns:
            p = bins[bins.pattern == pattern].set_index("visibility_bin")
            adjusted.append(dict(model=model, fraction=fraction, pattern=pattern, estimable=True,
                common_bins=";".join(map(str, support)), n_common_support=int(p.loc[support, "n"].sum()),
                standardized_accuracy=float(np.sum(p.loc[support, "accuracy"] * weights))))
    pd.DataFrame(counts).to_csv(out / "visibility_bin_counts.csv", index=False)
    pd.DataFrame(adjusted).to_csv(out / "visibility_standardization.csv", index=False)

    figures = out / "figures"
    figures.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 10, "figure.dpi": 150, "axes.spines.top": False, "axes.spines.right": False})
    colors = {"aimv2": "#0072B2", "dinov2": "#D55E00"}
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.7), sharey=True)
    for ax, pattern in zip(axes, patterns):
        for model in sorted(df.model.unique()):
            g = summary[(summary.model == model) & summary.pattern.isin([pattern, "clean"])].sort_values("fraction")
            ax.plot(g.fraction * 100, g.accuracy * 100, marker="o" if model == "aimv2" else "s", color=colors[model], label=model)
            ax.fill_between(g.fraction * 100, g.ci_low * 100, g.ci_high * 100, alpha=.12, color=colors[model])
        ax.set_title(pattern)
        ax.set_xlabel("Visible image area (%)")
        ax.set_xticks([25, 50, 75, 100])
        ax.set_ylim(0, 100)
    axes[0].set_ylabel("Breed classification accuracy (%)")
    axes[-1].legend()
    fig.suptitle(f"Oxford-IIIT Pet pilot: {per_image.image_id.nunique()} test images, frozen L/14 encoders")
    fig.tight_layout()
    fig.savefig(figures / "accuracy_curves.png", bbox_inches="tight")
    plt.close(fig)

    # Coverage is identical for both models; plot it once, not double-counted.
    first_model = sorted(df.model.unique())[0]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    for ax, fraction in zip(axes, sorted(config["fractions"])):
        g = per_image[(per_image.model == first_model) & (per_image.fraction == fraction)]
        ax.boxplot([g[g.pattern == p].object_visibility for p in patterns], tick_labels=patterns, showfliers=False)
        ax.set_title(f"{fraction:.0%} image visible")
        ax.set_ylim(0, 1)
    axes[0].set_ylabel("Fraction of annotated foreground visible")
    fig.suptitle("Equal visible image area can retain different amounts of foreground")
    fig.tight_layout()
    fig.savefig(figures / "object_visibility_distributions.png", bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for ax, pair_type in zip(axes, ["object_contrast", "visibility_matched"]):
        g = pairs[pairs.pair_type == pair_type]
        x = np.arange(len(g))
        ax.bar(x - .17, g.accuracy_a * 100, .34, label="Higher object visibility" if pair_type == "object_contrast" else "Location A")
        ax.bar(x + .17, g.accuracy_b * 100, .34, label="Lower object visibility" if pair_type == "object_contrast" else "Location B")
        ax.set_xticks(x, g.model)
        ax.set_ylim(0, 100)
        ax.set_title(f"{pair_type.replace('_', ' ')} (n={int(g.n_images.min())})")
        ax.legend(fontsize=8)
    axes[0].set_ylabel("Classification accuracy (%)")
    fig.suptitle("Same image and equal-shape square occluder: always 75% image visible")
    fig.tight_layout()
    fig.savefig(figures / "paired_diagnostics.png", bbox_inches="tight")
    plt.close(fig)

    audit = {"models": sorted(df.model.unique().tolist()), "test_images": int(per_image.image_id.nunique()),
        "prediction_rows": int(len(df)), "matched_eligible_images": int(df[df.pair_type == "visibility_matched"].image_id.nunique()),
        "prediction_tables_aligned": True, "random_repeats_averaged_within_image": True,
        "uncertainty": "2000 original-image bootstrap resamples; conditional on fixed probe and checkpoints",
        "caveat": "Exploratory, single-dataset, 5 test images/class. Pixel visibility is not semantic information or a causal pretraining comparison."}
    (out / "analysis_audit.json").write_text(json.dumps(audit, indent=2))
    print(summary.to_string(index=False))
    print(pairs.to_string(index=False))
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()

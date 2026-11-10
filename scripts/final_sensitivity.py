"""Clean-baseline and same-image foreground comparisons for the final talk."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/occlusion_completion"
MODELS = ["aimv2", "dinov2"]
KEYS = ["image_id", "label", "fraction", "pattern", "fill", "repeat"]
PATTERNS = ["prefix", "suffix", "center", "random"]


def load_standard():
    frames = []
    for run in ["extension_v2", "completion_primary", "completion_head"]:
        base = ROOT / "results" / run
        shared = ["condition_id", "cohort", "suite", "mask_hex", "object_visibility", *KEYS]
        left, right = [pd.read_csv(base / f"{model}_predictions.csv",
                                   usecols=shared + ["prediction", "correct"])
                       for model in MODELS]
        pd.testing.assert_frame_equal(left[shared], right[shared])
        assert left.condition_id.is_unique
        frame = left[shared].copy()
        for model, source in zip(MODELS, [left, right]):
            frame[model] = source.prediction.eq(source.label).astype(int)
            assert frame[model].equals(source.correct)
        frames.append(frame[frame.cohort.isin(["primary", "new_head"]) & frame.suite.eq("standard")])
    all_rows = pd.concat(frames, ignore_index=True)
    assert all_rows.condition_id.is_unique
    return all_rows


def bootstrap_weights(labels):
    rng = np.random.default_rng(6691110)
    weights = np.zeros((10000, len(labels)), dtype=float)
    for breed in np.unique(labels):
        ix = np.flatnonzero(labels == breed)
        weights[:, ix] = rng.multinomial(len(ix), np.full(len(ix), 1 / len(ix)), size=len(weights))
    return weights / len(labels)


def intervals(draws, family=1):
    q = .025 / family
    return np.quantile(draws, [q, 1-q])


def run():
    raw = load_standard()
    original = pd.read_csv(OUT / "accuracy_summary.csv").set_index(["cohort","fraction","fill","pattern","metric"])
    losses, matched, selected = [], [], []
    for cohort, frame in raw.groupby("cohort"):
        clean = frame[frame.pattern.eq("clean")].set_index("image_id").sort_index()
        assert clean.index.is_unique and len(clean) == {"primary":740, "new_head":185}[cohort]
        weights = bootstrap_weights(clean.label.to_numpy())
        both = clean[MODELS].eq(1).all(axis=1)
        for fraction, masks in frame[frame.pattern.ne("clean")].groupby("fraction"):
            grey = masks[masks.fill.eq(128)]
            center = grey[grey.pattern.eq("center")].set_index("image_id").object_visibility
            candidates = grey[grey.pattern.eq("random")][["image_id","repeat","object_visibility"]].copy()
            candidates["center_visibility"] = candidates.image_id.map(center)
            candidates["distance"] = (candidates.object_visibility - candidates.center_visibility).abs()
            closest = candidates.sort_values(["image_id","distance","repeat"]).drop_duplicates("image_id")
            keep = closest[closest.distance <= .03].set_index("image_id").sort_index()
            selected.append(keep.reset_index().assign(cohort=cohort, fraction=fraction))
            pair_weights = bootstrap_weights(clean.loc[keep.index, "label"].to_numpy()) if len(keep) >= 20 else None
            for fill, group in masks.groupby("fill"):
                assert set(group.pattern) == set(PATTERNS)
                mean = group.groupby(["pattern","image_id"])[MODELS].mean()
                for pattern in PATTERNS:
                    rows = group[group.pattern.eq(pattern)]
                    assert rows.groupby("image_id").size().reindex(clean.index).eq(3 if pattern == "random" else 1).all()
                    mask = mean.loc[pattern].loc[clean.index]
                    loss = clean[MODELS] - mask
                    gap = loss.aimv2 - loss.dinov2
                    draws = weights @ gap.to_numpy()
                    lo, hi = intervals(draws)
                    adj = intervals(draws, 12) if pattern in ["center","random"] else [np.nan,np.nan]
                    row = dict(cohort=cohort, fraction=fraction, fill=fill, pattern=pattern, n=len(clean),
                               n_joint_clean_correct=int(both.sum()), loss_gap=gap.mean(), ci_low=lo, ci_high=hi,
                               family_low=adj[0], family_high=adj[1])
                    for model in MODELS:
                        acc = mask[model].mean()
                        assert abs(acc-original.loc[(cohort,fraction,fill,pattern,model),"estimate"]) < 1e-10
                        row.update({f"{model}_clean":clean[model].mean(), f"{model}_masked":acc,
                                    f"{model}_loss":loss[model].mean(), f"{model}_joint_retained":mask.loc[both,model].mean()})
                    losses.append(row)
                pair_row = dict(cohort=cohort, fraction=fraction, fill=fill, eligible=len(keep), total=len(clean),
                                represented_breeds=clean.loc[keep.index,"label"].nunique(),
                                mean_abs_area_difference=keep.distance.mean())
                center_rows = group[group.pattern.eq("center")].set_index("image_id").loc[keep.index]
                random_rows = group[group.pattern.eq("random")].merge(keep["repeat"].reset_index(),
                                                                      on=["image_id","repeat"], validate="one_to_one").set_index("image_id").loc[keep.index]
                np.testing.assert_allclose(center_rows.object_visibility,keep.center_visibility)
                np.testing.assert_allclose(random_rows.object_visibility,keep.object_visibility)
                for metric in ["aimv2_center","aimv2_random","dinov2_center","dinov2_random","interaction","ci_low","ci_high"]:
                    pair_row[metric] = np.nan
                if pair_weights is not None:
                    diffs = center_rows[MODELS] - random_rows[MODELS]
                    for model in MODELS:
                        pair_row.update({f"{model}_center": center_rows[model].mean(),
                                         f"{model}_random": random_rows[model].mean()})
                    contrast = diffs.aimv2 - diffs.dinov2
                    lo, hi = intervals(pair_weights @ contrast.to_numpy())
                    pair_row.update(interaction=contrast.mean(), ci_low=lo, ci_high=hi)
                matched.append(pair_row)
    assert len(losses) == 48 and len(matched) == 12
    for name, table in [("clean_loss",pd.DataFrame(losses)), ("area_matched_patterns",pd.DataFrame(matched)),
                        ("area_matched_selection", pd.concat(selected, ignore_index=True))]:
        table.to_csv(OUT / (name + ".csv"), index=False, float_format="%.10g")
    print("Verified 48 masked comparisons against the main report and wrote 12 area-matched comparisons.")


if __name__ == "__main__":
    run()

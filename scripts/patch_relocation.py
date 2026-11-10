"""Prepare, run and audit annotation-matched patch relocation."""
import argparse
import hashlib
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from extension_v2 import predict, cache_binding
from final_sensitivity import bootstrap_weights, intervals
from occlusion_visibility.data import load_image, sha256_file
from occlusion_visibility.encoders import FrozenEncoder
from occlusion_visibility.experiment import mask_hex, decode_mask
from occlusion_visibility.masks import stable_seed, visibility_mask, apply_mask

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/patch_relocation"
CENTER = visibility_mask("center", .25)[::14, ::14].flatten()
RUNS = ["completion_primary", "completion_head"]
MODELS = ["aimv2", "dinov2"]


def propose(counts, name):
    bands = np.minimum(counts * 10 // 196, 9)
    groups = [np.flatnonzero(bands == i) for i in range(10)]
    sizes = [CENTER[g].sum() for g in groups]
    results = []
    for rep in (1, 2):
        rng = np.random.default_rng(stable_seed(6691110, name, rep))
        for _ in range(32):
            sampled = np.zeros(256, dtype=bool)
            for group, size in zip(groups, sizes):
                sampled[rng.choice(group, size=size, replace=False)] = True
            if np.count_nonzero(CENTER & ~sampled) < 16:
                continue
            if abs(counts[sampled].sum()-counts[CENTER].sum()) / counts.sum() > .03:
                continue
            if results and np.array_equal(sampled, results[0]):
                continue
            results.append(sampled)
            break
        else:
            return []
    return results


def prepare():
    OUT.mkdir(exist_ok=True)
    records, eligibility = [], []
    for run in RUNS:
        directory = ROOT / "results" / run
        fingerprints = pd.read_csv(directory / "preprocessing_fingerprints.csv").set_index("image_id")
        for entry in json.loads((directory / "manifest.json").read_text()):
            name, label, cohort = (entry[k] for k in ["image_id","label","cohort"])
            rgb, trimap = load_image(ROOT, name)
            for data, key in [(rgb,"rgb_sha256"),(trimap,"trimap_sha256")]:
                assert hashlib.sha256(data.tobytes()).hexdigest() == fingerprints.loc[name,key]
            counts = (trimap == 1).reshape(16,14,16,14).sum(axis=(1,3)).flatten()
            proposals = propose(counts, name)
            eligibility.append(dict(cohort=cohort,image_id=name,label=label,eligible=bool(proposals)))
            if not proposals:
                continue
            for role, grid in enumerate([CENTER, *proposals]):
                visible = grid.reshape(16,16).repeat(14,axis=0).repeat(14,axis=1)
                assert grid.sum() == 64
                records.append(dict(cohort=cohort,image_id=name,label=label,role=role,mask_hex=mask_hex(visible,14),
                                    animal_visible=visible[trimap==1].mean(),
                                    exchanged=int((CENTER & ~grid).sum()),
                                    rgb_sha256=fingerprints.loc[name,"rgb_sha256"]))
    for name, data in [("conditions",records),("eligibility",eligibility)]:
        path = OUT / (name+".csv")
        payload = pd.DataFrame(data).to_csv(index=False).encode()
        if path.exists() and path.read_bytes() != payload:
            raise RuntimeError(f"Design changed: {path}")
        path.write_bytes(payload)
    lock = dict(protocol=sha256_file(ROOT/"docs/PATCH_RELOCATION.md"), runner=sha256_file(Path(__file__)),
                conditions=sha256_file(OUT/"conditions.csv"), eligibility=sha256_file(OUT/"eligibility.csv"))
    path = OUT/"design_lock.json"
    if path.exists():
        assert json.loads(path.read_text()) == lock
    path.write_text(json.dumps(lock,indent=2)+"\n")
    print(pd.DataFrame(eligibility).groupby("cohort").eligible.agg(["sum","count"]),flush=True)


@lru_cache(maxsize=8)
def checked_image(name, digest):
    rgb, _ = load_image(ROOT, name)
    assert hashlib.sha256(rgb.tobytes()).hexdigest() == digest
    return rgb


def infer(model):
    lock = json.loads((OUT/"design_lock.json").read_text())
    assert lock["conditions"] == sha256_file(OUT/"conditions.csv") and lock["runner"] == sha256_file(Path(__file__))
    assert lock["protocol"] == sha256_file(ROOT/"docs/PATCH_RELOCATION.md")
    rows = pd.read_csv(OUT/"conditions.csv")
    src = ROOT/"results/completion_primary"
    cfg = json.loads((src/"config.json").read_text())
    binding = cache_binding(ROOT, src, cfg, range(17760), model)
    assert json.loads((src/f"features/{model}.json").read_text()) == binding
    encoder = FrozenEncoder(ROOT,model,"mps")
    predicted = []
    with np.load(src/f"probes/{model}_linear.npz") as probe:
        for start in range(0,len(rows),8):
            batch = rows.iloc[start:start+8]
            pixels = [apply_mask(checked_image(r.image_id,r.rgb_sha256),decode_mask(r.mask_hex,224,14),128)
                      for r in batch.itertuples()]
            feature = encoder.encode(np.stack(pixels))
            assert np.isfinite(feature).all() and np.allclose(np.linalg.norm(feature,axis=1),1,atol=1e-5)
            labels, _ = predict(feature,probe)
            predicted.extend(labels.tolist())
            if start % 512 == 0: print(model,start,"/",len(rows),flush=True)
    rows["prediction"] = predicted
    rows["correct"] = rows.prediction.eq(rows.label).astype(int)
    # Only write predictions after verifying the repeated control predictions.
    prior = pd.concat([pd.read_csv(ROOT/f"results/{run}/{model}_predictions.csv")
                       for run in ["extension_v2","completion_head"]])
    prior = prior.query("suite=='standard' and pattern=='center' and fill==128 and fraction==.25")
    ctrl = rows[rows.role.eq(0)].merge(prior,on=["cohort","image_id","mask_hex","label"],validate="one_to_one")
    assert len(ctrl) == len(rows)//3 and ctrl.prediction_x.eq(ctrl.prediction_y).all()
    path = OUT/f"{model}_predictions.csv"
    tmp = path.with_suffix(".tmp")
    rows[["cohort","image_id","role","mask_hex","prediction","correct"]].to_csv(tmp,index=False)
    tmp.replace(path)
    print(model,"verified",len(ctrl),"center replays",flush=True)


def analyze():
    design = pd.read_csv(OUT/"conditions.csv")
    eligible = pd.read_csv(OUT/"eligibility.csv")
    keys = ["cohort","image_id","role","mask_hex"]
    rows = design
    for model in MODELS:
        preds = pd.read_csv(OUT/f"{model}_predictions.csv")
        assert len(preds) == len(design)
        rows = rows.merge(preds,on=keys,validate="one_to_one")
        assert len(rows) == len(design) and rows.correct.eq(rows.prediction.eq(rows.label)).all()
        rows = rows.rename(columns={"correct":model}).drop(columns="prediction")
    summaries = []
    for cohort, sample in rows.groupby("cohort"):
        center = sample[sample.role.eq(0)].set_index("image_id").sort_index()
        altered = sample[sample.role.ne(0)]
        variants = altered.groupby("image_id")
        assert variants.size().eq(2).all() and altered.exchanged.ge(16).all()
        assert (altered.animal_visible-altered.image_id.map(center.animal_visible)).abs().max() <= .03000000001
        paired = variants[MODELS].mean().loc[center.index]
        delta = center[MODELS] - paired
        estimates = delta.assign(interaction=delta.aimv2-delta.dinov2)
        draws = bootstrap_weights(center.label.to_numpy()) @ estimates.to_numpy()
        for col, metric in enumerate(estimates):
            lo,hi = intervals(draws[:,col]); low,high = intervals(draws[:,col],3)
            summaries.append(dict(cohort=cohort,metric=metric,total=eligible.cohort.eq(cohort).sum(),eligible=len(center),
                                  center_acc=center[metric].mean() if metric in MODELS else None,
                                  relocated_acc=paired[metric].mean() if metric in MODELS else None,
                                  center_minus_relocated=estimates[metric].mean(),ci_low=lo,ci_high=hi,
                                  family_low=low,family_high=high,center_animal=center.animal_visible.mean(),
                                  relocated_animal=altered.animal_visible.mean(),mean_exchanged=altered.exchanged.mean()))
    out = pd.DataFrame(summaries)
    out.to_csv(OUT/"summary.csv",index=False,float_format="%.10g")
    print(out.to_string(index=False),flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage",choices=["prepare",*MODELS,"analyze"])
    action = parser.parse_args().stage
    if action == "prepare": prepare()
    elif action == "analyze": analyze()
    else: infer(action)

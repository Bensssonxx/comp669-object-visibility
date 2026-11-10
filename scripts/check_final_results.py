"""Verify the final presentation numbers using Python's standard library."""
import csv
import hashlib
import json
from collections import defaultdict
from math import isclose
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PATCH = RESULTS / "patch_relocation"
COMBINED = RESULTS / "occlusion_completion"
MODELS = ("aimv2", "dinov2")


def read(path):
    with path.open(newline="") as f:
        yield from csv.DictReader(f)


def check(value, expected):
    if not isclose(value, float(expected), rel_tol=0, abs_tol=2e-9):
        raise ValueError(f"{value} differs from reported {expected}")


def main():
    lock = json.loads((PATCH/"design_lock.json").read_text())
    for key,path in {"conditions":PATCH/"conditions.csv", "eligibility":PATCH/"eligibility.csv",
                     "protocol":ROOT/"docs/PATCH_RELOCATION.md","runner":ROOT/"scripts/patch_relocation.py"}.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == lock[key]
    masks, eligible = {}, set()
    for r in read(PATCH/"eligibility.csv"):
        if r["eligible"] == "True":
            eligible.add((r["cohort"],r["image_id"]))
    for r in read(PATCH/"conditions.csv"):
        key = r["cohort"],r["image_id"],int(r["role"])
        assert key not in masks
        masks[key] = r
    assert set(masks) == {(*key,role) for key in eligible for role in range(3)}
    for key in eligible:
        center = masks[(*key,0)]
        variants = set()
        for role in range(3):
            r = masks[(*key,role)]
            bits = int(r["mask_hex"],16)
            exchanged = (int(center["mask_hex"],16) & ~bits).bit_count()
            assert bits.bit_count()==64 and int(r["exchanged"])==exchanged
            assert role==0 or exchanged>=16
            assert abs(float(r["animal_visible"])-float(center["animal_visible"])) <= .03000000001
            variants.add(bits)
        assert len(variants)==3
    loss_table=list(read(COMBINED/"clean_loss.csv"))
    patch_table=list(read(PATCH/"summary.csv"))
    assert len(loss_table)==48 and len(patch_table)==6
    clean_correct_by_model = {}
    for model in MODELS:
        clean, baseline, retained = {}, {}, defaultdict(list)
        for source in ("extension_v2","completion_primary","completion_head"):
            for r in read(RESULTS/source/f"{model}_predictions.csv"):
                cohort, name = r["cohort"], r["image_id"]
                if cohort not in ("primary","new_head") or r["suite"]!="standard":
                    continue
                outcome = int(r["prediction"] == r["label"])
                assert outcome == int(r["correct"])
                if r["pattern"]=="clean":
                    assert (cohort,name) not in clean
                    clean[(cohort,name)] = outcome
                    continue
                key = (cohort,int(r["fill"]),float(r["fraction"]),r["pattern"],name)
                retained[key].append(outcome)
                if key[1:4]==(128,.25,"center"):
                    baseline[(cohort,name)] = (r["prediction"],r["mask_hex"])
        clean_correct_by_model[model] = {key for key, ok in clean.items() if ok}
        for r in loss_table:
            prefix = (r["cohort"],int(r["fill"]),float(r["fraction"]),r["pattern"])
            subset = [(clean[(key[0],key[-1])],mean(outcomes)) for key,outcomes in retained.items() if key[:-1]==prefix]
            assert len(subset) == int(r["n"])
            check(mean(masked for _,masked in subset),r[model+"_masked"])
            check(mean(original-masked for original,masked in subset),r[model+"_loss"])
        by_image=defaultdict(dict)
        for r in read(PATCH/f"{model}_predictions.csv"):
            key = r["cohort"],r["image_id"]
            role = int(r["role"])
            design=masks[(*key,role)]
            assert r["mask_hex"]==design["mask_hex"] and role not in by_image[key]
            if role==0:
                assert (r["prediction"],r["mask_hex"])==baseline[key]
            correct=int(r["prediction"]==design["label"])
            assert int(r["correct"])==correct
            by_image[key][role]=correct
        assert set(by_image)==eligible and all(set(v)=={0,1,2} for v in by_image.values())
        for r in patch_table:
            if r["metric"]!=model:
                continue
            subset=[v for key,v in by_image.items() if key[0]==r["cohort"]]
            assert len(subset)==int(r["eligible"])
            check(mean(v[0] for v in subset),r["center_acc"])
            check(mean((v[1]+v[2])/2 for v in subset),r["relocated_acc"])
            check(mean(v[0]-(v[1]+v[2])/2 for v in subset),r["center_minus_relocated"])
    joint = clean_correct_by_model["aimv2"] & clean_correct_by_model["dinov2"]
    for r in loss_table:
        assert sum(key[0]==r["cohort"] for key in joint) == int(r["n_joint_clean_correct"])
        check(float(r["aimv2_loss"])-float(r["dinov2_loss"]),r["loss_gap"])
    for r in patch_table:
        if r["metric"]=="interaction":
            others={v["metric"]:float(v["center_minus_relocated"]) for v in patch_table if v["cohort"]==r["cohort"]}
            check(others["aimv2"]-others["dinov2"],r["center_minus_relocated"])
    # This checker is also invoked in isolated (-I) mode from a fresh archive.
    import runpy
    runpy.run_path(str(ROOT/"scripts/check_region_swap.py"))["check"]()
    print("Verified 48 clean-baseline comparisons and all six relocation contrasts, including masks and center replays.")


if __name__ == "__main__":
    main()

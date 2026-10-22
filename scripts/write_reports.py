"""Generate English milestone briefs from completed real prediction analyses."""
import json
from pathlib import Path
import pandas as pd

root = Path.cwd()
run = "pilot_v1"
out = root / "results" / run
summary = pd.read_csv(out / "summary.csv")
pairs = pd.read_csv(out / "paired_summary.csv")
adjusted = pd.read_csv(out / "visibility_standardization.csv")
audit = json.loads((out / "integration_audit.json").read_text())
assert set(audit["completed_prediction_models"]) == {"aimv2", "dinov2"}
clean = summary[summary.pattern == "clean"].set_index("model")
half = summary[summary.fraction == .5].set_index(["model", "pattern"])
quarter = summary[summary.fraction == .25].set_index(["model", "pattern"])
random_difference = pd.read_csv(out / "paired_model_differences.csv").query("pattern == 'random' and fraction == .25").iloc[0]
contrast = pairs[pairs.pair_type == "object_contrast"].set_index("model")
matched = pairs[pairs.pair_type == "visibility_matched"].set_index("model")
def pct(x): return f"{x*100:.1f}%"
def pp(x): return f"{x*100:.1f}"
table = "| Model | Clean | Prefix 50% | Suffix 50% | Center 50% | Random 50% |\n| --- | ---: | ---: | ---: | ---: | ---: |\n"
for model in ["aimv2", "dinov2"]:
    table += f"| {model} | {pct(clean.loc[model,'accuracy'])} | " + " | ".join(pct(half.loc[(model,p),"accuracy"]) for p in ["prefix","suffix","center","random"]) + " |\n"
details_en = []
for model in ["aimv2", "dinov2"]:
    c, m = contrast.loc[model], matched.loc[model]
    details_en.append(f"- **{model}:** same-image square occluders with higher/lower object visibility yield {pct(c.accuracy_a)} / {pct(c.accuracy_b)} accuracy; paired difference {pp(c.paired_accuracy_difference)} percentage points (95% image-bootstrap CI {pp(c.difference_ci_low)} to {pp(c.difference_ci_high)}). In {int(m.n_images)} foreground-visibility-matched image pairs, correctness differs for {pct(m.correctness_discordance)} and predicted class differs for {pct(m.prediction_disagreement)}. Maximum foreground-coverage mismatch is {pp(m.max_pair_object_visibility_difference)} percentage points.")
fg_center = half.loc[("aimv2","center"),"mean_object_visibility"]
fg_random = half.loc[("aimv2","random"),"mean_object_visibility"]
estimable = adjusted[adjusted.estimable == True]
no_support = sorted(adjusted[adjusted.estimable == False].fraction.unique())
missing_budgets = ", ".join(f"{v:.0%}" for v in no_support) or "none"
support_note = f"{len(estimable)} pattern estimates have the prespecified common-bin support. Non-estimable visible-image budgets: {missing_budgets}. At supported budgets, the retained groups can still be small; consult visibility_standardization.csv and visibility_bin_counts.csv for bins and counts. These coarse-bin descriptive estimates do not equal exact foreground matching or causal mediation."
reports = root / "reports"
reports.mkdir(exist_ok=True)
supplement = pd.read_csv(out / 'probe_regularization_sensitivity.csv') if (out / 'probe_regularization_sensitivity.csv').exists() else None
supplement_table = ''
if supplement is not None:
    supplement_table = '| Model | C | Clean validation | Clean test | Random 25% | Center 25% | Matched flips |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: |\n'
    for r in supplement.itertuples():
        supplement_table += f'| {r.model} | {r.C:g} | {pct(r.validation_accuracy)} | {pct(r.clean_accuracy)} | {pct(r.random_25_accuracy)} | {pct(r.center_25_accuracy)} | {pct(r.matched_correctness_flip_rate)} |\n'
common_en = """## Design and interpretation

The pilot uses 1,480 training, 370 validation and 185 official-test images across 37 Oxford-IIIT Pet breeds. Fourteen invalid empty-foreground annotations were excluded before sampling (7 official trainval, 7 test). Both frozen L/14 encoders use mean final patch pooling plus L2 normalization, and separate clean-only logistic classifiers. C is chosen using clean validation labels only. Test labels never select masks or hyperparameters.

Both original validation searches selected C=10, the upper boundary of the prespecified grid. The labeled post-hoc supplement explores C=10,100,1000 while retaining all original main estimates. Pooling and wider probe choices remain unresolved; these scores do not rank general encoder quality. The shared mean-patch recipe can suit the encoders differently.

Visible area is 100/75/50/25%; patterns are raster prefix, suffix, center-nearest and three deterministic random repetitions. Hidden pixels use RGB 128 and no tokens are removed. Same-image square-occluder pairs fix hidden area to 25% and shape to 8x8 patches. Matched pairs differ by at most 0.03 in foreground visibility and are selected from annotations without model outputs.

This is a diagnostic replication/extension of existing foreground/background occlusion work, not a new general principle or a causal test of prefix attention. Shared pooling is a controlled diagnostic choice, not each model's published best evaluation recipe. The original ImageNet-100 proposal has been narrowed to this annotation-rich pilot; no result here is an ImageNet score.

## What these results can support

The measured image-area budgets and foreground-coverage distributions describe this dataset and masking implementation. Paired differences describe responses to the specified pixel interventions within each fixed model. A residual difference at matched foreground coverage does not uniquely identify a spatial mechanism: head visibility, object parts, texture and background can still change. An average signed paired difference near zero does not establish invariance; inspect discordance and cases.

A lower correctness-flip rate alone is not better robustness: two wrong predictions also produce no correctness flip. The paired table therefore includes both-correct, both-wrong and one-correct counts. Probe target probabilities are descriptive responses, not calibrated reliability scores.

Uncertainty resamples original images (all repeated masks travel with their image), conditional on fixed probes. Only 5 test images/class are included. Grayscale squares are not real-world occluders; full-frame square resizing distorts aspect ratio; pretraining overlap is unknown. A second fill, larger test set, second dataset and pooling/preprocessing sensitivity remain future work.

## Milestone presentation outline (12 minutes)

1. Revised question and why area alone can mislead (1 min).
2. Relation to PatchDrop and background-signal research (1 min).
3. Real inputs, trimap definitions and shared preprocessing (2 min).
4. Clean baseline and standard-mask curves (2 min).
5. Same-image diagnostic pairs, uncertainty and cases (3 min).
6. Limits and next experiments (2 min).
7. Repository and AI-use disclosure; leave timing margin (1 min).

Repository: https://github.com/Bensssonxx/comp669-object-visibility (private; instructor access must be arranged before submission). AI disclosure is in docs/AI_USE.md. Neither slides nor messages have been submitted to Canvas or sent to the instructor.
"""
en = f"""# Object-visibility-aware occlusion evaluation: pilot v1

Executed 2026-10-18. All numbers below come from saved model predictions, not examples or literature scores.

## Initial results

{table}

A descriptive ordering change appears at 25% visible area: under random masks, AIMv2 reaches {pct(quarter.loc[('aimv2','random'),'accuracy'])} and DINOv2 {pct(quarter.loc[('dinov2','random'),'accuracy'])}; the paired AIMv2-minus-DINOv2 difference is {pp(random_difference.aim_minus_dino)} percentage points (95% image-bootstrap CI {pp(random_difference.ci_low)} to {pp(random_difference.ci_high)}). Under center-nearest visibility at the same image-area budget, AIMv2 reaches {pct(quarter.loc[('aimv2','center'),'accuracy'])} and DINOv2 {pct(quarter.loc[('dinov2','center'),'accuracy'])}. These conditions retain different foreground distributions. This is a checkpoint-and-probe-specific pattern, not a pretraining-causality finding or a general model ranking.

At the same 50% visible image area, the center-nearest mask preserves an average {pct(fg_center)} of labeled foreground versus {pct(fg_random)} for the random condition. This is an input-composition finding, not by itself a new model-robustness result.

{chr(10).join(details_en)}

Exploratory standardization: {support_note}

{common_en}

## Post-hoc probe sensitivity

Both original validation searches ended at the C-grid boundary. The following supplement reports every tested C rather than choosing test-favorable results. Expanded-grid choices use clean validation only. The random-versus-center ordering persists across these C values, but matched correctness-flip rates change. This is not a pooling or pretraining-control experiment.

{supplement_table}

## Numeric reference environment

The original images use the Conda Pillow 10.4.0 build with libjpeg 9e. A pip wheel with libjpeg-turbo decoded different pixels despite the same Pillow version. A second decoder-pinned reference environment reproduced all 2,035 selected RGB/trimap fingerprints and the first 8 conditions per encoder with zero feature difference. Saved classifier coefficients reproduce all 8,510 main prediction rows. This is not a second full independent experiment. Use environment.reference.yml and the input-fingerprint gate before reusing caches.

## Evidence

- [Raw summary and image-bootstrap intervals](../results/pilot_v1/summary.csv)
- [Paired diagnostics](../results/pilot_v1/paired_summary.csv)
- [Paired model differences](../results/pilot_v1/paired_model_differences.csv)
- [Integration audit](../results/pilot_v1/integration_audit.json)
- [Pre-inference protocol](../docs/PROTOCOL.md)
- [Related work](../docs/RELATED_WORK.md)

![Accuracy curves](../results/pilot_v1/figures/accuracy_curves.png)
![Foreground coverage distributions](../results/pilot_v1/figures/object_visibility_distributions.png)
![Same-image paired diagnostics](../results/pilot_v1/figures/paired_diagnostics.png)
"""
(reports / "PILOT_REPORT_EN.md").write_text(en)
print("Wrote English reports from actual saved results")

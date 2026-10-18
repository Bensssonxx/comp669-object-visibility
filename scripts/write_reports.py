"""Generate bilingual milestone briefs from completed real prediction analyses."""
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
contrast = pairs[pairs.pair_type == "object_contrast"].set_index("model")
matched = pairs[pairs.pair_type == "visibility_matched"].set_index("model")
def pct(x): return f"{x*100:.1f}%"
def pp(x): return f"{x*100:.1f}"
table = "| Model | Clean | Prefix 50% | Suffix 50% | Center 50% | Random 50% |\n| --- | ---: | ---: | ---: | ---: | ---: |\n"
for model in ["aimv2", "dinov2"]:
    table += f"| {model} | {pct(clean.loc[model,'accuracy'])} | " + " | ".join(pct(half.loc[(model,p),"accuracy"]) for p in ["prefix","suffix","center","random"]) + " |\n"
details_en, details_zh = [], []
for model in ["aimv2", "dinov2"]:
    c, m = contrast.loc[model], matched.loc[model]
    details_en.append(f"- **{model}:** same-image square occluders with higher/lower object visibility yield {pct(c.accuracy_a)} / {pct(c.accuracy_b)} accuracy; paired difference {pp(c.paired_accuracy_difference)} percentage points (95% image-bootstrap CI {pp(c.difference_ci_low)} to {pp(c.difference_ci_high)}). In {int(m.n_images)} foreground-visibility-matched image pairs, correctness differs for {pct(m.correctness_discordance)} and predicted class differs for {pct(m.prediction_disagreement)}. Maximum foreground-coverage mismatch is {pp(m.max_pair_object_visibility_difference)} percentage points.")
    details_zh.append(f"- **{model}：**同一图片、相同方形遮挡面积下，主体保留更多／更少时准确率为 {pct(c.accuracy_a)}／{pct(c.accuracy_b)}；成对差值 {pp(c.paired_accuracy_difference)} 个百分点，95% 图像级 bootstrap 区间为 [{pp(c.difference_ci_low)}, {pp(c.difference_ci_high)}]。主体可见程度匹配的 {int(m.n_images)} 对图片中，{pct(m.correctness_discordance)} 的正确／错误状态不同，{pct(m.prediction_disagreement)} 的预测类别不同。最大主体可见比例差为 {pp(m.max_pair_object_visibility_difference)} 个百分点。")
fg_center = half.loc[("aimv2","center"),"mean_object_visibility"]
fg_random = half.loc[("aimv2","random"),"mean_object_visibility"]
estimable = adjusted[adjusted.estimable == True]
no_support = sorted(adjusted[adjusted.estimable == False].fraction.unique())
missing_budgets = ", ".join(f"{v:.0%}" for v in no_support) or "none"
support_note = f"{len(estimable)} pattern estimates have the prespecified common-bin support. Non-estimable visible-image budgets: {missing_budgets}. At supported budgets, the retained groups can still be small; consult visibility_standardization.csv and visibility_bin_counts.csv for bins and counts. These coarse-bin descriptive estimates do not equal exact foreground matching or causal mediation."
reports = root / "reports"
reports.mkdir(exist_ok=True)
common_en = """## Design and interpretation

The pilot uses 1,480 training, 370 validation and 185 official-test images across 37 Oxford-IIIT Pet breeds. Fourteen invalid empty-foreground annotations were excluded before sampling (7 official trainval, 7 test). Both frozen L/14 encoders use mean final patch pooling plus L2 normalization, and separate clean-only logistic classifiers. C is chosen using clean validation labels only. Test labels never select masks or hyperparameters.

Visible area is 100/75/50/25%; patterns are raster prefix, suffix, center-nearest and three deterministic random repetitions. Hidden pixels use RGB 128 and no tokens are removed. Same-image square-occluder pairs fix hidden area to 25% and shape to 8x8 patches. Matched pairs differ by at most 0.03 in foreground visibility and are selected from annotations without model outputs.

This is a diagnostic replication/extension of existing foreground/background occlusion work, not a new general principle or a causal test of prefix attention. Shared pooling is a controlled diagnostic choice, not each model's published best evaluation recipe. The original ImageNet-100 proposal has been narrowed to this annotation-rich pilot; no result here is an ImageNet score.

## What these results can support

The measured image-area budgets and foreground-coverage distributions describe this dataset and masking implementation. Paired differences describe responses to the specified pixel interventions within each fixed model. A residual difference at matched foreground coverage does not uniquely identify a spatial mechanism: head visibility, object parts, texture and background can still change. An average signed paired difference near zero does not establish invariance; inspect discordance and cases.

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

At the same 50% visible image area, the center-nearest mask preserves an average {pct(fg_center)} of labeled foreground versus {pct(fg_random)} for the random condition. This is an input-composition finding, not by itself a new model-robustness result.

{chr(10).join(details_en)}

Exploratory standardization: {support_note}

{common_en}

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
zh = f"""# 项目第一轮真实实验结果：pilot v1

实验日期：2026-10-18。下列数值来自已保存的真实模型预测，不是示意数字。

## 这轮在做什么

先用 Oxford-IIIT Pet 的 37 类品种分类和像素级主体标注，把“可见图像面积”和“主体可见程度”分开记录。固定预训练编码器，分别用完整训练图像训练小分类器。1,480 张训练、370 张验证、185 张官方测试图片。14 张无有效主体标注的图片在抽样前排除，名单保留。它是对原 ImageNet-100 计划的有理由缩小，不是 ImageNet 结果。

## 初步结果

表中的 50% 指可见图像面积。Random 是同一图片三个随机遮挡的平均，不能当作三倍独立样本。

{table}

同样保留 50% 的图像面积，center 平均保留了 {pct(fg_center)} 的已标注主体，而 random 平均保留了 {pct(fg_random)}。这说明输入条件的组成不同；这个观察本身并不是首次发现的新规律。

{chr(10).join(details_zh)}

成对实验始终遮住 25% 图像，使用相同大小方形。同一图片的匹配对在主体可见比例上相差不超过 3 个百分点，由标注选出，选取时没有查看模型输出。不能把剩余差异直接叫作“位置导致的纯效应”：遮住的具体部位、纹理与背景仍然不同。

四种标准遮挡模式共同区间不足的可见图像预算为：{missing_budgets}。在这些预算下，不能可靠报告四种模式“调整主体可见性后”的比较。有共同区间的预算也仅使用少量、粗分组样本；不能把这种描述性重加权当作精确匹配或因果解释。同图方形遮挡匹配实验是另一个设计，不等于原来的四模式比较已经解决。

## 能得出什么，不能得出什么

- 可以描述本数据、模型、分类器和像素干预下的行为，以及主体可见面积不足以描述的失败案例。
- 不能归因于 prefix attention；两个模型的训练目标、数据与结构仍然不同。
- 不能把相同主体面积等同于相同语义信息；猫的眼睛与身体毛发不是可替换的信息。
- 不能从平均差值接近零推断没有影响；必须同时看正确性翻转、预测变化和案例。
- 95% 区间按原始图片 bootstrap，随机遮挡先在图内平均；它不包括分类器重新训练和换数据集的不确定性。
- 只有每类 5 张测试图片。这是 single-dataset pilot，灰色像素遮挡也不等于真实物体遮挡。预训练重叠未知，整图缩放有宽高比失真。

## 下一步

优先扩大测试集、换一种填充颜色，检查结果是否稳定；对主体面积相近但预测不同的样本做具体部位分析。头部框在当前下载的官方标注中仅覆盖训练划分，本轮 185 张测试图没有头部 XML，因此不能假装已经控制或量化头部可见程度。后续可以在独立标注子集或新的划分中检查。

已有 PatchDrop 与背景挑战研究区分过前景／背景，因此项目定位为复现与扩展。贡献是当前模型上的可复现评估、主体可见性量化、同图匹配诊断与清楚的解释边界，尚不声称论文级新颖性。

## Milestone 怎么讲

12 分钟中，用约 2 分钟交代新问题与相关工作，2 分钟讲真实输入和实验设置，5 分钟讲结果及案例，2 分钟讲局限与下一轮计划，剩余时间展示仓库和 AI 使用说明。数据、完整结果与配置均在仓库中。

仓库：https://github.com/Bensssonxx/comp669-object-visibility （目前私有，提交前需要安排教师访问）。代码实现和实验由 Codex 辅助，详见 AI_USE.md；需要由学生理解、检查后再展示。尚未向 Canvas 提交，亦未给老师发送消息。

证据文件：[准确率与区间](../results/pilot_v1/summary.csv)、[成对实验](../results/pilot_v1/paired_summary.csv)、[模型成对差值](../results/pilot_v1/paired_model_differences.csv)、[整体审计](../results/pilot_v1/integration_audit.json)、[实验方案](../docs/PROTOCOL.md)。
"""
(reports / "PILOT_REPORT_EN.md").write_text(en)
(reports / "PILOT_REPORT_ZH.md").write_text(zh)
print("Wrote bilingual reports from actual saved results")

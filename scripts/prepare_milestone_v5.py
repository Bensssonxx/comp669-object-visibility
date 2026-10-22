"""Bind the revised milestone to completed v2 evidence, without rerunning models."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/extension_v2"

def rows(name):
    with (OUT / name).open() as f:
        return list(csv.DictReader(f))

audit = json.loads((OUT / "integration_audit.json").read_text())
analysis = json.loads((OUT / "analysis_audit.json").read_text())
assert audit["passed"] and analysis["passed"]
assert set(audit["completed_and_reconstructed_models"]) == {"aimv2", "dinov2"}
assert analysis["prediction_rows"] == 32722

slides = [
    dict(title="What does occlusion robustness measure?", seconds=25,
         anchor="The evaluation condition can change which model looks more robust.",
         note="My project studies how occlusion tests compare AIMv2 and DINOv2. After the proposal feedback, I changed the question. I now ask whether the evaluation condition changes which model looks more robust, and what visible-area measurements miss. Today I will show a follow-up on new images and explain what the controls let us conclude.",
         source="docs/EXTENSION_V2_PROTOCOL.md; reports/EXTENSION_V2_EN.md"),
    dict(title="Motivation: interpreting a robustness comparison", seconds=55,
         anchor="A useful evaluation should make clear what the comparison measures.",
         note="An accuracy drop after removing information is expected. The more useful question is whether a robustness comparison depends on how we remove that information. If two masks keep the same image area but lead to different model rankings, one score gives an incomplete picture. Also, keeping the same area may retain very different amounts of the animal. My contribution is a reproducible evaluation and diagnostic extension of earlier occlusion work. I measure the retained content and check which conclusions survive new images and a second fill color. I do not claim that foreground and background analysis is new.",
         source="docs/RELATED_WORK.md; Naseer et al., https://arxiv.org/abs/2105.10497; Xiao et al., https://arxiv.org/abs/2006.09994"),
    dict(title="Image visibility and foreground visibility", seconds=55,
         anchor="Twenty-five percent of the image is not necessarily twenty-five percent of the animal.",
         note="These are actual inputs from one follow-up image. Both masks keep exactly twenty-five percent of the image, but the center mask keeps much more of the animal. Image visibility divides retained pixels by the whole image. Foreground visibility divides retained animal pixels by the original annotated animal. Those denominators differ. The displayed foreground numbers describe this example, not the dataset average. Both encoders receive exactly the same masked pixels. Hidden pixels get a constant fill before normalization, and all patch tokens remain. This is a pixel occlusion test, with no inference-compute saving.",
         source="results/extension_v2/design_example_selection.json; results/extension_v2/conditions.csv; Oxford-IIIT Pet images and annotations, https://www.robots.ox.ac.uk/~vgg/data/pets/"),
    dict(title="Follow-up design and fixed classifiers", seconds=60,
         anchor="The new images never select or refit the classifiers.",
         note="The dataset is Oxford-IIIT Pet, with thirty-seven breed classes and foreground annotations. The original classifiers used fourteen hundred eighty clean training images and three hundred seventy clean validation images. Validation selected C equal to ten for both models. The follow-up adds seven hundred forty official-test images, twenty per breed, excluding every pilot sample by image ID and exact bytes. I reuse both frozen encoders and their original classifiers. There is no refitting or parameter selection on these new images. The follow-up design was fixed after seeing the pilot, but before making the new predictions.",
         source="docs/PROTOCOL.md; docs/EXTENSION_V2_PROTOCOL.md; results/extension_v2/preparation_audit.json; pre-inference commit 815a33b"),
    dict(title="Controls and the conclusions they permit", seconds=65,
         anchor="Shared inputs control the evaluation, but they do not control model pretraining.",
         note="There are three comparisons, with different controls. Across models, I share the images, masks, preprocessing and probe procedure. Their pretrained weights, training data and objectives still differ, so their score difference describes the two systems. It cannot isolate prefix attention. Across fill colors, I hold the mask and retained pixels fixed and change only the hidden-pixel value. In same-image pairs, I also fix the encoder, classifier, occluder area and shape. Moving that occluder still changes parts and background. These controls narrow the interpretation, but they do not turn the experiment into a causal test of pretraining.",
         source="docs/EXTENSION_V2_PROTOCOL.md; reports/EXTENSION_V2_EN.md, Motivation and limits"),
    dict(title="Model ordering reverses with the masking pattern", seconds=65,
         anchor="The center and random conditions give opposite model rankings.",
         note="Here are the main follow-up results with gray fill. Every masked condition keeps twenty-five percent of the image. With center visibility, AIMv2 reaches eighty-seven percent accuracy and DINOv2 about sixty-three percent. With random visibility, AIMv2 reaches about thirty-four percent and DINOv2 about seventy percent. So the model ordering reverses. The paired model differences are positive for center and negative for random. Both displayed intervals exclude zero after adjustment across the seven planned contrasts. Random repetitions are averaged within each image, and the bootstrap resamples images within breeds. The result concerns these fixed encoders and classifiers.",
         source="results/extension_v2/summary.csv; results/extension_v2/primary_contrasts.csv; results/extension_v2/analysis_audit.json"),
    dict(title="The ordering crossover repeats with black fill", seconds=55,
         anchor="The ordering repeats, while absolute accuracy still depends on the fill.",
         note="Next I change the hidden pixels from gray to black while retaining exactly the same visible pixels. The center condition still favors AIMv2, and the random condition still favors DINOv2. All four component model differences keep their directions under the simultaneous intervals. However, this does not make fill color irrelevant. On random masks, black fill lowers AIMv2 accuracy by about three percentage points and DINOv2 by about seven. The ordering is repeated under these two fills, while the absolute scores change. I do not claim equivalence across fill colors or robustness to natural occluders.",
         source="results/extension_v2/summary.csv; results/extension_v2/primary_contrasts.csv; results/extension_v2/fill_sensitivity.csv"),
    dict(title="Equal image area retains unequal foreground", seconds=50,
         anchor="Foreground coverage identifies a confound, without explaining away the score gap.",
         note="The annotation measurements help interpret this comparison. Although every pattern keeps twenty-five percent of the image, center visibility retains sixty-two point five percent of the animal on average. Random visibility retains about twenty-five percent. Prefix and suffix retain even less foreground. So the standard-pattern comparison changes content distribution as well as position. This makes whole-image area an incomplete description of the evaluation. It does not show how much of the accuracy gap foreground explains. I have not estimated a pure position effect after controlling content. The same-image diagnostics address a narrower question.",
         source="results/extension_v2/foreground_coverage.csv; results/extension_v2/conditions.csv"),
    dict(title="Same-image diagnostics fix occluder area and shape", seconds=60,
         anchor="Matching foreground area still allows predictions to change.",
         note="These diagnostics use a different budget: a square hides twenty-five percent, leaving seventy-five percent visible. For each image, annotations select placements before looking at predictions. One design contrasts higher and lower foreground retention. The other matches foreground retention within three percentage points and separates the occluder locations. All seven hundred forty images have an eligible matched pair. Under gray fill, correctness still flips in about eleven percent of AIMv2 pairs and nine percent of DINOv2 pairs. Area matching does not match the surviving parts or background. A lower flip rate alone is not better robustness, because both versions can be wrong.",
         source="docs/EXTENSION_V2_PROTOCOL.md; results/extension_v2/paired_summary.csv; results/extension_v2/eligibility.csv"),
    dict(title="Similar foreground area can retain different parts", seconds=70,
         anchor="This measures a change in retained content, not an isolated head effect.",
         note="I also added a separate auxiliary cohort with head boxes, because the downloaded official-test annotations lack them. Of one hundred eighty-five unused trainval images, one hundred fifty-nine meet the fixed pairing rules. Foreground retention is close, but head-region retention differs substantially. With gray fill, the paired accuracy gap is about nineteen percentage points for AIMv2 and eleven for DINOv2. This shows what area matching can miss. The head region is a bounding-box intersection with foreground, not precise segmentation. Other body parts and background change too. This cannot isolate a head effect or explain the main crossover in a different cohort.",
         source="results/extension_v2/preparation_audit.json; results/extension_v2/paired_summary.csv; results/extension_v2/design_example_selection.json; Oxford-IIIT Pet, https://www.robots.ox.ac.uk/~vgg/data/pets/"),
    dict(title="Conclusions and limits", seconds=55,
         anchor="The contribution is a bounded evaluation result with explicit diagnostic limits.",
         note="The milestone supports three conclusions. First, the model ordering depends on the evaluation condition, and the crossover repeats on new images under two fills. Second, equal image visibility can retain very different foreground amounts. Third, approximately matching foreground area still leaves meaningful content differences. These are measured behaviors under a specified evaluation. They do not establish a pretraining mechanism or a general model ranking. The main crossover still mixes content and location, and the auxiliary analysis does not resolve that. The study also uses one dataset, one pooling recipe and synthetic fills. Those limits define the next experiments.",
         source="reports/EXTENSION_V2_EN.md; docs/EXTENSION_V2_PROTOCOL.md"),
    dict(title="Next experiments, code and AI use", seconds=45,
         anchor="The next priority is to test whether the readout changes the finding.",
         note="My next priority is feature-readout sensitivity, using a fixed protocol and classifiers fitted only on clean training data, with choices made on clean validation. Since I have already seen these test results, that would be a labeled sensitivity analysis. Later, I can test another dataset or natural occluders. The repository contains the protocols, predictions and analysis. It is private, so instructor access still needs arranging. Codex assisted source review, code, execution, analysis and presentation drafting. The main finding is that the evaluation condition changes which system appears more robust. Thank you.",
         source="https://github.com/Bensssonxx/comp669-object-visibility; docs/AI_USE.md; docs/RELATED_WORK.md"),
]

evidence_names = ["summary.csv", "primary_contrasts.csv", "paired_summary.csv", "foreground_coverage.csv", "fill_sensitivity.csv", "conditions.csv", "integration_audit.json", "analysis_audit.json", "preparation_audit.json", "design_example_selection.json", "figures/design_inputs.png"]
data = {"slides": slides, "audit": audit, "analysis_audit": analysis,
        "summary": rows("summary.csv"), "contrasts": rows("primary_contrasts.csv"),
        "pairs": rows("paired_summary.csv"), "foreground": rows("foreground_coverage.csv"),
        "fill_sensitivity": rows("fill_sensitivity.csv"),
        "example_selection": json.loads((OUT / "design_example_selection.json").read_text()),
        "example_conditions": [r for r in rows("conditions.csv") if r["image_id"] in {"Abyssinian_96", "Abyssinian_12"}],
        "evidence_sha256": {str(Path("results/extension_v2") / n): hashlib.sha256((OUT / n).read_bytes()).hexdigest() for n in evidence_names}}
(ROOT / "milestone/slide_data_v5.json").write_text(json.dumps(data, indent=2) + "\n")
print(json.dumps({"main_slides": len(slides), "planned_seconds": sum(s["seconds"] for s in slides), "evidence_files": len(evidence_names)}))

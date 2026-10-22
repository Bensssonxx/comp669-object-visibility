"""Simplify the milestone narrative while retaining the saved experiment evidence."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "milestone/slide_data_v5.json").read_text())
titles = [
    "Comparing AIMv2 and DINOv2 Under Occlusion",
    "Research question",
    "Same image area, different animal area",
    "First test and second test",
    "What stays the same?",
    "The better model changes with the mask",
    "The pattern repeats with black fill",
    "How much of the animal is visible?",
    "Same square, different locations",
    "Similar area, different animal parts",
    "What we learned",
    "Next steps",
]
scripts = [
    "Hi everyone, I'm Boshen. My project studies occlusion robustness: how well a model recognizes an object when parts are hidden.\n\nI compare AIMv2 and DINOv2 on cat and dog breeds, using classification accuracy under different masks. The question is how those masks affect our comparison.",
    "An accuracy drop after hiding information is expected. What matters here is whether changing the mask changes which model appears more robust.\n\nFor example, AIMv2 may perform better when we keep the center of the picture, while DINOv2 may perform better when we keep random small patches. So the way we hide information may affect which model we would choose.\n\nFirst, let's look at how much of the animal each masking pattern leaves visible.",
    "Both masked versions keep twenty-five percent of the picture. But center visibility keeps about eighty-four percent of this cat, while random visibility keeps about twenty-two percent.\n\nHere, foreground means the animal. Picture visibility uses the whole picture as its reference. Foreground visibility uses the original animal region.\n\nSo equal picture area can retain different content. This is why I measure animal visibility alongside accuracy. Now, how do I test this across more images?",
    "This slide shows the steps of the experiment. All images come from the same Oxford-IIIT Pet dataset, with thirty-seven breeds.\n\nFirst, I use fourteen hundred eighty clean images to train a classifier for each model. I use three hundred seventy validation images to choose the classifier settings. The pretrained models stay fixed.\n\nI then test one hundred eighty-five images, five per breed, to compare the models under different masking patterns.\n\nNext, I test another seven hundred forty images, twenty per breed. These are different pictures from the same dataset. This checks whether the same model ranking appears on different images.\n\nI keep the same models and classifiers for both tests, without retraining. Next, I'll explain what else stays the same in our comparisons.",
    "This table separates three comparisons.\n\nIn the first row, both models see the same pictures and masks, with the same classifier fitting method. The models and their training histories differ.\n\nIn the second row, I keep the model, picture, mask and visible pixels fixed. Only the fill changes from gray to black.\n\nIn the last row, I move the same-sized square on the same picture. The model stays fixed, but visible parts and background change.\n\nThe bottom line is that training differences remain uncontrolled. We cannot isolate a training mechanism. Now, the results.",
    "These are the second-test results: seven hundred forty images, gray fill, and twenty-five percent of each picture visible. All four patterns were tested. This chart focuses on center and random, where the ranking reverses. Blue is AIMv2. Orange is DINOv2.\n\nFor center, AIMv2 gets eighty-seven percent accuracy and DINOv2 sixty-three. For random, AIMv2 gets thirty-four percent and DINOv2 seventy.\n\nSo changing the mask changes which model does better. Does this also happen with black fill?",
    "The first two rows repeat the gray results. The next two show black fill.\n\nWith black, center gives AIMv2 about eighty-seven percent accuracy and DINOv2 sixty-two. Random gives AIMv2 about thirty percent and DINOv2 sixty-two.\n\nAs noted below, visible pixels and mask positions stay identical. Only the fill color changes. The ordering repeats, although the scores change.\n\nNext, I measure how much animal content these patterns leave visible.",
    "All four patterns keep twenty-five percent of the picture. The chart shows how much of the animal remains, averaged over seven hundred forty images.\n\nFrom left to right, top keeps about ten percent of the animal, bottom fifteen, center sixty-three, and random twenty-five.\n\nSo mask location and visible content change together. This does not tell us how much animal visibility explains the accuracy gap.\n\nNext, I move a fixed-size square on the same image to check what area measurements miss.",
    "Here, a square covers twenty-five percent, leaving seventy-five percent visible. I move it to different locations.\n\nThe table compares more versus less animal visible. AIMv2 gets about ninety-three versus sixty-seven percent accuracy. DINOv2 gets eighty-three versus sixty-seven. Both have higher average accuracy when more animal remains.\n\nBelow, I compare two versions of one image. For example, sixty and sixty-two percent animal visibility meet the three-percentage-point limit.\n\nFor each model, I count pairs with one correct and one wrong answer: about eleven percent for AIMv2, nine percent for DINOv2.\n\nThese percentages are not accuracies. Two wrong answers count as no switch, so fewer switches are not necessarily better. Next, which animal parts remain visible?",
    "This separate check uses head boxes. Of one hundred eighty-five unused images, one hundred fifty-nine meet the pairing rules.\n\nThe pictures show the same-sized square in different positions. The left version keeps more head visible.\n\nThe table shows higher accuracy with more head visible: a gap of about nineteen percentage points for AIMv2 and eleven for DINOv2.\n\nThe measurements below show similar animal visibility, about fifty-six percent in both groups, but head visibility differs: eighty-three versus thirteen percent.\n\nOther parts and background change too. This cannot isolate a head effect or explain the main crossover. Now, the conclusions.",
    "On the left are the findings. The better model changes with the mask under gray and black fill. Equal picture area can retain different amounts of animal. Similar animal area can show different parts.\n\nOn the right are the limits. Training differs between models. Mask position and content change together. We use one dataset and artificial masks.\n\nOur follow-up focused on twenty-five percent image visibility. Next, does the ranking also reverse when more remains visible?",
    "First, I'll test fifty and seventy-five percent image visibility across all four patterns, using the same seven hundred forty images, models and classifiers. This checks whether the reversal also occurs with less occlusion.\n\nSecond, I'll compare averaging patch features with taking their maximum. I'll fit each classifier on clean training images and choose settings on validation. This checks whether feature pooling affects the reversal. Both steps reuse evaluated images.\n\nThe public repository contains our code and results. Codex helped with the work and presentation, as disclosed below. Thank you."
]
assert len(scripts) == len(titles) == len(data["slides"]) == 12
for slide, title, script in zip(data["slides"], titles, scripts):
    slide.update(title=title, note=script)
    words = len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b", script))
    slide["seconds"] = round(words / 90 * 60 + 40 / 12)
# Preserve full technical notes for questions; only the speech is spoken.
data["technical_notes"] = {
    "classifiers": "1,480 clean training / 370 clean validation. C=10 selected on clean validation. Frozen AIMv2-L/14 and DINOv2-L/14, final mean patch features and L2 normalization, shared 224x224 full-frame preprocessing. Separate learned classifiers. All patch tokens remain, with no inference-compute saving.",
    "uncertainty": "10,000 breed-stratified image bootstrap resamples. Random repetitions averaged within original image. Seven prespecified primary contrasts receive approximate Bonferroni family-wise 95% intervals. Intervals condition on fixed encoder weights and classifiers.",
    "auxiliary": "Separate auxiliary cohort, not the 740-image main sample. 159 of 185 unused trainval images meet fixed criteria. Head proxy intersects foreground with a head bounding box, not precise segmentation. This changes a content bundle, cannot isolate a head effect, and cannot explain the main crossover in another cohort.",
    "next": "Planned, not yet run: first extend the 740-image primary cohort to 50% and 75% visible area for all four patterns, both fills, reusing frozen encoders and original probes. Next compare final normalized patch mean versus elementwise max pooling for both encoders, followed by L2 normalization and separate classifiers fitted on clean training data with settings selected on clean validation only. Fix the new protocol before predictions and report all conditions. Reusing evaluated images is sensitivity analysis, not independent new-image confirmation. Neither check identifies a pretraining mechanism. Another dataset or natural occluders remain future work."
}
(ROOT / "milestone/slide_data_v6.json").write_text(json.dumps(data, indent=2) + "\n")
print(json.dumps({"main_slides":12,"spoken_words":sum(len(re.findall(r"\b[\w]+(?:['’-][\w]+)*\b", s)) for s in scripts)}))

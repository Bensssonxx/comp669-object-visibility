## 1. What does occlusion robustness measure?

My original proposal asked how AIMv2 and DINOv2 degrade when less of an image is visible. After the feedback, I narrowed the question. The important issue is not simply that occlusion reduces accuracy. It is what the experiment actually removes, and what its results let us conclude. This milestone uses a small, real experiment with foreground annotations. I will show the inputs, the results, and the limits of the comparison. The model encoders stay frozen throughout.

Sources: docs/PROTOCOL.md

## 2. Equal image area can retain unequal foreground

Suppose two masks both keep half the image. One may retain almost the entire animal, while the other keeps mostly the background. In that case, a difference between the masks is hard to interpret as a location preference. This is the motivation for recording foreground visibility separately. The foreground mask describes the visible animal in the original photograph. It does not tell us which parts are most useful for identifying its breed, so area matching will still have limits. This project examines how much these distinctions matter for interpreting our model evaluation.

Sources: Oxford-IIIT Pet trimap annotations; docs/PROTOCOL.md; Naseer et al., https://arxiv.org/abs/2105.10497

## 3. The revised question is about interpretation

I ask whether mask-location differences persist after accounting for visible foreground. I first measure how much foreground each standard mask keeps. Then I construct same-image pairs with the same square occluder size. Some pairs retain very different foreground amounts. Other pairs retain almost the same amount but place the occluder elsewhere. AIMv2 is the primary model, and DINOv2 is a reference model under the same inputs. Prior PatchDrop work already distinguishes salient foreground and non-salient background. My contribution is a reproducible extension using pixel annotations and explicit matched-pair diagnostics, rather than claiming that foreground and background effects are new.

Sources: Naseer et al., https://arxiv.org/html/2105.10497v3, Sec. 3.1; Xiao et al., https://arxiv.org/abs/2006.09994; docs/RELATED_WORK.md

## 4. The pilot uses frozen encoders and clean probes

I changed the pilot dataset from ImageNet-100 to Oxford-IIIT Pet because it provides pixel-level foreground labels. This is a breed-classification experiment across 37 categories. I use the official split, with 40 training images, 10 validation images and 5 official-test images per class. Fourteen images with empty foreground annotations were excluded before sampling. The encoders remain frozen. Each model has its own logistic classifier trained only on clean training features. Clean validation chooses the regularization parameter. The test labels do not choose that parameter, the masks, or the matching threshold. Both models use mean final patch features and the same preprocessing, which is a diagnostic recipe rather than their published best evaluation setup.

Sources: Saved pilot_v1 predictions, configuration and docs/PROTOCOL.md

## 5. Both models receive these same masked pixels

These are actual inputs from one of the held-out images, rather than schematic masks. Across the row, image visibility decreases from 100 percent to 25 percent. The second line records the fraction of annotated foreground that remains. I resize the full image and the annotation together before applying the mask. Hidden pixels receive a gray value of 128 before normalization. There is no crop or resize after masking. I keep every patch token, and I do not call either model's native mask interface. This makes the intervention a shared pixel-level occlusion test. It also means the experiment does not save inference compute.

Sources: Saved pilot_v1 predictions, configuration and docs/PROTOCOL.md

## 6. The model ordering changes with the mask

The clean held-out accuracies are 93.5% for AIMv2 and 83.2% for DINOv2 under this shared probe recipe. But with only 25 percent randomly visible, AIMv2 reaches 32.6% and DINOv2 70.6%. Under the center condition at that same image-area budget, the ordering reverses again. So clean-image performance alone does not predict the ordering in these tests. The shaded intervals resample original images, averaging random repeats inside each image first. This is a descriptive finding for these checkpoints, probes and data, not evidence about which pretraining mechanism caused it. To interpret the mask comparison, I next examine foreground coverage.

Sources: results/pilot_v1/summary.csv and paired_model_differences.csv; 2000 original-image bootstrap resamples

## 7. At 50% image visibility, foreground coverage varies

These distributions come from the input masks and annotations, so they are identical for the two models. At 50 percent visible image area, center-nearest masks retain an average 85.2% of the annotated foreground, compared with 50.2% for the random condition. This explains why image visibility alone is an incomplete description of the test. It does not prove that foreground area fully explains an accuracy difference. For example, a small visible face could matter more than a larger patch of fur. The matched-pair experiment is a first diagnostic step toward separating some of these conditions.

Sources: results/pilot_v1/conditions.csv and summary.csv; foreground label 1 only; unknown trimap label 3 excluded

## 8. Same-image pairs fix occluder area and shape

Every example on this slide keeps 75 percent of the image and uses the same square occluder shape. I generate 25 possible placements on a fixed grid. The first pair chooses the placements that retain the most and least foreground. The second pair matches foreground visibility within three percentage points and requires separated occluder locations. The annotations choose the pairs before any model outputs are examined. All 185 test images have an eligible matched pair under this rule. This is an oracle diagnostic using annotations, not an annotation-free method for deployment. It controls image identity, shape and area, but it still changes which animal parts and which background pixels remain.

Sources: Saved pilot_v1 predictions, configuration and docs/PROTOCOL.md

## 9. Paired diagnostics quantify two different changes

The upper table compares the same image with higher and lower foreground visibility while fixing square-occluder area and shape. AIMv2's paired difference is 20.5 percentage points, with a 95 percent interval from 14.6 to 27.0. DINOv2's difference is 11.9 points, with an interval from 6.5 to 17.3. The lower figures describe pairs whose foreground coverage is already close. Correctness changes for 11.9% of AIMv2 pairs and 9.7% of DINOv2 pairs. A lower flip rate alone is not better robustness: both versions can be wrong without a flip. These figures describe changes, not a pure spatial mechanism or a general model ranking.

Sources: results/pilot_v1/paired_summary.csv; paired image-bootstrap confidence intervals; n=185 per diagnostic

## 10. Similar foreground area can retain different parts

This is an illustrative case selected after the experiment, using a stored rule that prioritizes correctness changes and then large target-probability changes. It is not evidence for how common a pattern is; the previous slide reports the full test-set rates. The two occluded inputs have closely matched foreground area but expose different regions of the animal. The displayed probabilities are the probes' probabilities of the correct breed. We can inspect the surviving parts as a possible explanation, but we have not measured head visibility on this test set. The downloaded head boxes cover only the official training subset. That limitation is why I describe this as a diagnostic case rather than a controlled part-level explanation.

Sources: Saved pilot_v1 predictions, configuration and docs/PROTOCOL.md

## 11. What the pilot supports, and what remains open

The pilot establishes an executable evaluation and real paired observations under a clearly specified pixel intervention. It lets us show that equal image-area masks retain different foreground coverage, and quantify how predictions change under two same-image diagnostic designs. Importantly, the four standard mask patterns have no eligible common coverage bin at 50 percent image visibility under the prespecified rule. I therefore cannot report a reliable adjusted four-pattern comparison there. The square-occluder pairs are a different diagnostic, not a solution to that missing overlap. Nothing here identifies the effect of prefix attention. The next priority is a larger test set, another fill color, and a design with better coverage overlap.

Sources: Saved pilot_v1 predictions, configuration and docs/PROTOCOL.md

## 12. Code, next experiments and AI use

The repository contains the protocol, source hashes, data manifests, model predictions, analysis code and figures. It is currently private, so I need to arrange instructor access before submitting the link. For the final project, I will prioritize a larger test set and fill-color sensitivity, then a more precise analysis of the content that remains visible. I used OpenAI Codex for literature inspection, implementation, debugging, execution and analysis drafting. The saved outputs provide the evidence for the reported numbers, and I need to review and understand the code and interpretations before presenting them. The main related works are PatchDrop, the backgrounds challenge, AIMv2, DINOv2 and the Oxford-IIIT Pet dataset.

Sources: https://github.com/Bensssonxx/comp669-object-visibility; docs/AI_USE.md; docs/RELATED_WORK.md
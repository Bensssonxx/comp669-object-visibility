# Milestone v5 questions to prepare for

These are backup answers, not part of the 12-minute script. Use your own words and check the code or report when you need more detail.

**What is the motivation beyond “occlusion hurts”?**

The evaluation condition can change which system appears more robust. At the same 25% visible-image budget, center visibility favors AIMv2 and random visibility favors DINOv2. I measure the retained content and test whether this pattern repeats on new images and a second fill. This makes the interpretation of an occlusion comparison more explicit.

**What is your contribution? Is foreground/background masking new?**

Prior work, including PatchDrop and the Backgrounds Challenge, already studies related content interventions. My contribution is a course-scale replication and diagnostic extension: a reproducible shared-input comparison, a follow-up fixed before new predictions, measured foreground coverage, and same-image area-matched diagnostics. I do not claim a new architecture or a first-ever foreground/background finding.

**Why do you compare AIMv2 and DINOv2 if their training differs?**

They are two specified encoder/classifier systems under the same evaluation inputs. The comparison describes their behavior. It cannot identify which training choice caused a difference. A causal pretraining claim would require a matched training ablation, which this project does not include.

**Does this prove anything about prefix attention?**

No. Model pretraining remains uncontrolled. Evaluation-time prefix masks and training-time prefix attention are different concepts. I do not attribute any score difference to prefix attention.

**What exactly did you control?**

Both models receive the same images, visible pixels, masks and preprocessing, using the same readout and fitting procedure but separately learned classifiers. Fill comparisons hold the mask and retained pixels fixed. Within each same-image pair I fix image identity, encoder, classifier, occluder area and shape. Moving the mask still changes object parts, background and texture.

**Why are 25% and 75% both on the slides?**

The main pattern comparison retains 25% of the image. The square diagnostics hide 25%, leaving 75% visible. They answer different questions, and their accuracy values must not be treated as one shared masking condition.

**How did you train or select the classifiers?**

For each frozen encoder, mean final patch features are L2 normalized and passed to a separate multinomial logistic classifier. The pilot uses 1,480 clean training and 370 clean validation images. Clean validation selected C=10 for both. The 740 follow-up images never refit or select a classifier. This is our diagnostic readout, not a reproduction of each paper's best published evaluation.

**Did you choose the follow-up after seeing results?**

The pilot motivated the follow-up. I fixed its new-image sampling, conditions, probes and analysis before making predictions on those images, in commit 815a33b. It is a prespecified follow-up to an observed pilot, not an independently conceived external preregistration.

**How new are the 740 images?**

They are previously unevaluated official-test images, twenty per breed. Their IDs and exact image bytes do not overlap any pilot training, validation or test sample. This does not establish absence of visual near duplicates or overlap with model pretraining data.

**Are the confidence intervals based on thousands of independent masks?**

No. The original image is the sampling unit. I average random repetitions within image, then use 10,000 image-bootstrap resamples within breed, carrying paired conditions together. The seven fixed primary contrasts receive both individual 95% intervals and approximate Bonferroni simultaneous intervals. Those intervals condition on the fixed encoder weights and classifiers, and do not include uncertainty from choosing this project protocol.

**Does a significant interaction prove the ranking reverses?**

An interaction alone does not. I inspect the component model differences: AIMv2 minus DINOv2 is positive for center and negative for random. Both directions remain under the simultaneous intervals, for both fills.

**Does foreground coverage explain the ranking crossover?**

I have not estimated how much it explains. Center retains 62.5% of foreground on average and random retains 25.0%, despite the same 25% whole-image budget. That identifies a content-distribution difference. It does not isolate a pure position effect or quantify a mediation effect. The pilot also lacked common foreground-coverage support across all four patterns at 50% image visibility, and the follow-up does not solve that problem.

**Is the head-region result part of the main official-test result?**

No. The downloaded official-test annotations lack head-box XMLs. The auxiliary cohort contains 185 unused official-trainval images, separate from the pilot and main cohort. Only 159 meet the fixed criteria. I keep its estimates separate from the 740-image main evaluation.

**What are the head-pair criteria, and is this a causal head effect?**

Pairs have the same square shape and area, a foreground-visibility gap at most 3 percentage points, occluder centers at least four patches apart, and a head-region visibility gap at least 20 percentage points. The head proxy intersects a head rectangle with foreground pixels. It is not precise head segmentation. Mean head visibility is 83.0% versus 12.7%, but complementary body visibility is 35.9% versus 85.7%. Background and texture change too. The result measures a content substitution, not the isolated causal effect of the head, and it cannot explain the main crossover in another cohort.

**What are the paired head-result intervals?**

With gray fill, the higher-minus-lower-head accuracy gap is 19.2 percentage points for AIMv2, individual 95% CI [13.5,24.9], and 10.5 points for DINOv2, [5.8,15.1]. With black fill the gaps are 17.0 points, [11.3,22.7], and 8.4 points, [4.1,12.7]. These auxiliary results are diagnostic, use equal represented-breed weights among eligible images, and do not use the main seven-contrast family adjustment.

**Does similar performance under two fills mean fill color is irrelevant?**

No. The ordering crossover repeats, but black fill lowers random accuracy by 3.2 percentage points for AIMv2 and 7.4 for DINOv2. The black-minus-gray change in the model-by-pattern interaction is -2.8 points, individual 95% CI [-6.4,0.9]. An interval crossing zero does not establish equivalence.

**Does a lower correctness-flip rate mean a more robust model?**

Not by itself. Two wrong predictions produce no correctness flip. I also report each condition's accuracy, predicted-class changes, and both-correct/both-wrong counts.

**Could the probe or pooling recipe explain the behavior?**

That remains possible. In the pilot, a labeled post-hoc C sensitivity at 10,100,1000 preserved the center/random ordering, while flip-rate comparisons changed. The follow-up reuses the original C=10 probes, so it is not a new pooling or classifier study. Feature-readout sensitivity is the next priority. Choices should use clean train/validation only, and reuse of already evaluated images must be labeled as sensitivity analysis.

**How reproducible is this?**

The repository preserves protocols, hashes, manifests, masks, small frozen classifiers, predictions and analyses. Audits reconstruct all 32,722 follow-up prediction labels and target probabilities from cached features and frozen probes. Independent decoding matched all 925 new inputs. A separate interpreter replayed 24 aligned conditions per encoder with zero feature difference. That is a limited replay, not a second full independent experiment.

**What did AI do, and what still needs your review?**

OpenAI Codex assisted source review, project design, implementation, debugging, execution, analysis, slides and speaker-note drafting. Reported results come from saved executions. I must review and understand the code, assumptions, numbers and interpretations before presenting. The material does not claim that this review has already happened.

Sources: `docs/PROTOCOL.md`, `docs/EXTENSION_V2_PROTOCOL.md`, `docs/RELATED_WORK.md`, `docs/AI_USE.md`, `reports/EXTENSION_V2_EN.md`, `results/extension_v2/`, and `docs/EXTENSION_*REPLAY_CHECK.json`.

# Completing the occlusion study

November 4, 2026. The original forward work plan is preserved below, followed by an execution update. The original pilot, extension v2, and exploratory correctness-prediction results remain unchanged. New analyses of their predictions are labeled exploratory. Private course feedback is not reproduced in this repository.

## Research question and scope

How do masking pattern, visible animal area, and retained animal regions relate to classification accuracy in frozen AIMv2 and DINOv2 systems?

The practical output is a more informative evaluation than a single masked-image accuracy score: it shows which model does better under specified conditions, how much animal information remains, and where the available measurements do not account for the observed differences.

Finish this behavioral occlusion study first. Keep the released encoders, original clean-trained classifiers, mean pooling, image preprocessing, and shared mask rules fixed. Do not add mean-versus-max pooling, layer-wise mechanisms, new pretraining, or a second dataset to the required final-project scope. None is needed to make the existing comparison meaningful. These remain possible later projects.

## Current evidence and gaps

| Available evidence | What it can answer | What remains |
| --- | --- | --- |
| Pilot: 185 test images, four patterns, 25/50/75% image visibility | Initial behavior across budgets | Small sample; keep separate from the follow-up |
| Extension v2: 740 images, four patterns at 25% image visibility, gray/black fill | Pattern-dependent ordering and fill sensitivity | Foreground-conditioned accuracy plots; larger-sample 50/75% conditions |
| Same-square diagnostics on the 740 images | Different content with fixed occluder area/shape; correctness changes with similar foreground area | Exact visibility labels, distributions, and explicit limits |
| Auxiliary head comparison: 159 eligible of 185 images | Accuracy under matched foreground area and contrasting head-region coverage | Selected sample and coarse head proxy; other content changes too |
| Exploratory grouped correctness prediction | Foreground and pattern add complementary predictive information in the fitted diagnostic | It is not an accuracy improvement or independent confirmation |

The November 4 read-only audit of saved CSVs found the following foreground-bin counts for the primary cohort. Random repeats were averaged within image before binning, matching the original exploratory analysis convention. Each row has 740 original images; these are not new test results.

| Pattern | 0–<20% | 20–<40% | 40–<60% | 60–<80% | 80–100% |
| --- | ---: | ---: | ---: | ---: | ---: |
| Prefix/top | 644 | 89 | 6 | 1 | 0 |
| Suffix/bottom | 472 | 249 | 19 | 0 | 0 |
| Center | 3 | 79 | 281 | 228 | 149 |
| Random | 27 | 713 | 0 | 0 | 0 |

Only the 20–<40% bin has at least five images in every pattern. Even within that broad bin, visibility and image composition are not necessarily matched. A larger sample alone will not remove this structural support problem.

## Step 1 — Define quantities and audit the analysis table

**Question:** Are all percentages and comparisons measuring the same thing?

1. Join extension condition metadata and both models' predictions by condition ID; verify one prediction per model per condition and shared image/mask/fill identities.
2. Record image ID, breed, cohort, image visibility, foreground visibility, background visibility, head/body proxy visibility where available, pattern, repeat, fill, and correctness.
3. Keep four distinct quantities explicit:
   - Image visibility = unmasked pixels / all image pixels.
   - Foreground visibility = unmasked label-1 pixels / all label-1 pixels in the photographed animal.
   - Head-region visibility = unmasked foreground pixels inside the annotated head box / all foreground pixels inside that box.
   - Accuracy = correctly classified examples / evaluated examples, with stated weighting.
4. Exclude trimap label 3 from foreground/background denominators as before. Do not silently treat unknown pixels as background.
5. Replace ambiguous high/low labels in new tables with measured mean percentages, plus distributions and sample counts. Means do not describe every individual pair.

Existing gray-fill pair summaries already provide usable labels: animal-contrast means 88.7% versus 30.0%; foreground-matched means 72.25% versus 72.28%, with the per-pair 3-percentage-point rule; head-pair foreground means 55.9% versus 55.4%, head means 83.0% versus 12.7%, and complementary body-proxy means 35.9% versus 85.7%. Retain the paired gap statistics and background measurements, rather than relying on close group means.

**Deliverables:** `results/occlusion_completion/measurement_audit.json`, an analysis table, and an exact-percentage summary table. These paths are planned outputs, not existing results.

**Complete when:** source hashes, joins, denominators, repeat handling, exclusions, and cohort separation are verified. Old published summary numbers reproduce within rounding.

## Step 2 — Plot accuracy against foreground visibility using saved predictions

**Question:** How does recognition vary with how much of the animal remains visible, under each masking pattern?

1. Start with the 740-image 25%-image-visibility experiment. Use foreground visibility on the horizontal axis and breed-classification accuracy on the vertical axis.
2. Use one panel per pattern, with two model curves in each panel and shared axes. Show gray and black in separate rows or figures. Put foreground-count distributions below the curves.
3. Start with the existing five 20-percentage-point bins. Plot points at the actual mean foreground visibility within each bin; label bin counts. Do not draw through unobserved regions. Bins with fewer than five distinct images have no accuracy estimate; mark 5–19-image bins as sparse rather than treating them as equally reliable.
4. Primary reproduction convention: average the three random-mask outcomes and coverages within image, then bin. State that a random point describes average behavior across its three masks. As a sensitivity display, bin individual random conditions with weight 1/3 and bootstrap by image; this exposes variation hidden by repeat averaging.
5. For these descriptive plots, average original-image outcomes within each bin and report breed composition. Both models use exactly the same observations/weights in every cell. Any all-image headline retains the original equal-breed estimand. Do not silently substitute bin estimates for the original headline scores.
6. Bootstrap original images within breed, retaining their complete model/fill/repeat bundle. Use paired intervals for AIM-minus-DINO differences. Report unique images and represented breeds. Intervals remain conditional on these fixed systems and the observed binning; do not extrapolate empty bins.

**Deliverables:** foreground-conditioned accuracy figures, a companion count table, and a paired model-gap figure where data exist.

**Complete when:** every plotted estimate maps to saved rows; both models share support; empty and sparse bins are visible. Smooth fitted curves, if added later, are supplementary and cannot replace the empirical evidence.

## Step 3 — Compare patterns only where the data overlap

**Question:** At comparable foreground visibility, do pattern-associated accuracy differences remain?

1. Audit support separately at each image-visibility budget and fill. Never combine budgets merely to fill empty bins.
2. Reproduce the earlier broad-bin descriptive comparison, displaying the full counts and retained/discarded share. Restrict any standardized comparison to observed common bins and state its restricted population.
3. Inspect the actual within-bin coverage distributions. If center and random occupy different ends of a broad bin, a shared bin is not adequate matching. Use narrower, prespecified 10-point bins as a sensitivity check, preserving the minimum-count rule and reporting non-estimability where necessary. Do not search bin boundaries for a desired result.
4. Prefer the existing within-image square pairs for the distinct question of behavior under similar foreground area with fixed occluder shape/size. These are not center-versus-random pairs and cannot directly explain that ranking reversal.
5. Treat any residual association as an evaluation result. It does not isolate location, head content, or a training mechanism. Images, visible regions, texture continuity, and background can still differ.

**Deliverables:** a support audit and a short statement of which comparisons are estimable, weakly supported, or unavailable. An unavailable comparison is an informative limitation, not a reason to fabricate a full curve.

**Complete when:** all pattern comparisons declare their population and overlap. This step determines what additional conditions are useful.

## Step 4 — Complete the larger-cohort visibility-budget experiment

**Question:** Does the pattern-dependent model ordering persist as more of each image becomes visible?

1. Use the same 740 original images and add 50% and 75% visible-image conditions for all four standard patterns. Keep the three deterministic random repeats, gray/black fills, and existing nesting of masks across budgets. Reuse 25% and clean results only after source/input hashes match.
2. Preserve the encoder weights, C=10 classifiers, mean pooling, resize/decoder, and normalization. Do not fit a classifier on these masked test images.
3. Before the full run, validate mask counts, RGB equality across models, repeat determinism, annotation transforms, and an exact replay of a small existing condition batch. Benchmark actual throughput and memory; estimate runtime from that measurement.
4. Store the extension in a new run directory. Never overwrite the v2 config, cached features, or predictions. Bind all new caches to checkpoint, classifier, input, mask, and preprocessing hashes.
5. Regenerate Steps 2–3 separately at 25%, 50%, and 75% visibility. Show paired AIM-minus-DINO gaps for all four patterns at every budget and both fills. Check the signs in center and random explicitly; an interaction by itself is not a ranking reversal.

**Deliverables:** a fixed follow-up protocol/config, raw predictions, runtime/provenance audit, visibility curves, and a pattern-by-budget model-gap chart.

**Complete when:** every planned condition is included, even if the reversal disappears or changes sign. New conditions on previously examined images are scope extensions, not independent replication. Wider budgets may improve coverage but do not guarantee overlapping foreground distributions.

## Step 5 — Make the animal-region analysis interpretable

**Question:** When total visible animal area is similar, what visible-content differences accompany success or failure?

Required analysis using existing results:

1. Rebuild the 159-image auxiliary panel with foreground, head-proxy, complementary body-proxy, and background percentages beside both accuracies. Include paired differences, uncertainty, and the 159/185 eligibility count.
2. Explain the concrete comparison: retaining more head-region foreground also tends to retain less foreground outside the head box. It is a changed content bundle, not a head-only intervention.
3. Show actual paired images, annotation outlines, exact per-image percentages, and both model outputs. Include an annotation-selected illustrative pair chosen without model outcomes, plus clearly labeled descriptive examples of success/failure. Do not use selected examples as prevalence evidence.
4. Do not label eyes, ears, legs, or tail quantitatively: the available annotations do not support those measurements. Do not merge this auxiliary sample into the 740-image official-test results.

High-priority extension after the required curves, if runtime permits:

5. Sample 185 previously unused, valid head-annotated images (five per breed) before predictions. Exclude all prior train/validation/test/auxiliary image IDs and exact hashes; audit availability rather than assuming it. Keep the official trainval origin explicit. If the planned balanced sample is unavailable, revise the sampling plan before any new predictions.
6. Evaluate all four standard patterns and all three visibility budgets on that same cohort, not only pairs selected for extreme head contrast. Apply the fixed square-pair rule as a separate secondary analysis and report all ineligible images; do not replace them based on outcomes.
7. Freeze the sampling rule, masks, measurements, display bins, contrasts, and any correctness predictor before evaluating the new cohort. Exploratory development stays on existing data. A frozen diagnostic trained on earlier data may be evaluated here, but a changed cohort/protocol is a transfer check, not an exact replication of the old selected-pair estimate.
8. Use this cohort to connect actual retained regions to the standard patterns. It can corroborate or weaken earlier descriptive findings; it still cannot isolate the causal importance of the head.

**Deliverables:** region-comparison figures and annotated examples; if the extension runs, a disjoint-cohort manifest, fixed protocol, predictions, and a separate validation report.

**Complete when:** the reader can see what changed besides the head and what conclusion survives those limitations. A second dataset is not required for this bounded course question.

## Step 6 — Consolidate findings and final deliverables

Organize the final narrative as a chain of questions:

1. Why is one occlusion score insufficient? Establish the observed pattern-dependent ranking.
2. Do equal image-visibility percentages leave equal amounts of animal visible? Show measured distributions.
3. How does accuracy vary with foreground visibility? Show curves with counts and uncertainty.
4. What can be compared at similar foreground visibility? Show support-restricted comparisons and square pairs.
5. Does retained region content matter descriptively? Show the head/body/background bundle and its limits.
6. Does the behavior persist across budgets, fills, and any new cohort? Report all outcomes.
7. What did we learn? State an evidence-bounded evaluation recommendation and the unresolved questions.

Retain the correctness-prediction analysis as supporting evidence, not the main answer to the requested accuracy plots. Do not call Brier improvements improvements to AIMv2/DINOv2 accuracy. Do not require a positive head effect, persistent reversal, or a new mechanism to call the project complete.

Expected final artifacts: a concise English results report, reproducible code/configs and source tables, a focused slide deck, slide-ordered spoken notes, and an updated AI-use disclosure. Keep the root README brief. Code is the main course deliverable alongside presentation materials. No private course comments belong in GitHub.

## Sequence and working schedule

These are target work windows, not guaranteed compute durations. Use the earlier final submission slot as the internal deadline until the personal presentation group is verified.

| Target | Work | Dependency / exit condition |
| --- | --- | --- |
| Nov 4 | Verify feedback, requirements, existing results; write this plan | Completed planning pass; no new encoder inference |
| Nov 5–6 | Steps 1–3: audit, exact labels, first curves and overlap | Verified tables and a clear support map |
| Nov 7–10 | Step 4: benchmark and complete 50/75% conditions | All fixed conditions run or a documented compute limitation |
| Nov 10–12 | Step 5: region analysis; prepare/run unused annotated cohort if feasible | Core region figure complete; optional cohort evaluated only after design lock |
| Nov 13–14 | Integrate positive/negative findings; reproducibility checks | Every conclusion traceable to a saved result |
| Nov 15–17 | Final deck, notes, rehearsal, code cleanup | Presentation understandable within the user's 12-minute target |
| Nov 18 | Final verification and ready-to-submit package | Review code link, artifacts, and AI disclosure |

Live course requirements checked November 4: final presentations are November 19 and 24. Canvas slide deadlines are November 18 and 23 at 11:59 PM America/New_York. Previous Part 2 participation does not by itself verify the final group assignment. Plan to be ready by November 18; do not assume the later deadline.

If time is short, prioritize audited foreground curves, exact content measurements, and a transparent conclusion over adding another model component. Reduce optional scope before dropping planned conditions selectively. The public course description explicitly accepts a well-executed negative result with a clear explanation.

## Course references

- [Project details](https://sites.google.com/cs.unc.edu/unc-comp669-26f/project-details)
- [Schedule](https://sites.google.com/cs.unc.edu/unc-comp669-26f/schedule)
- [Course policies](https://sites.google.com/cs.unc.edu/unc-comp669-26f/home): AI assistance is permitted and must be disclosed with tools and requested uses.

Existing project evidence: `docs/PROTOCOL.md`, `docs/EXTENSION_V2_PROTOCOL.md`, `results/extension_v2/conditions.csv`, `results/extension_v2/standard_per_image.csv`, `results/extension_v2/paired_summary.csv`, `reports/VISIBILITY_PREDICTION_EN.md`, and `src/occlusion_visibility/encoders.py`.

## Execution update — November 4

- Completed the existing-data measurement audit, exact-percentage tables, foreground-conditioned curves, 10-point-bin sensitivity, individual-random-repeat sensitivity, and common-support tables. Previous headline estimates reproduced.
- Completed independent point-estimate reconstruction and eleven focused statistical/condition tests.
- Prepared and locked the 740-image 50/75% extension and the disjoint 185-image annotated cohort. The new cohort has 164 eligible head pairs.
- Completed both models on the 740-image 50/75% extension and all planned conditions on the new annotated cohort. Original feature replays matched exactly for both models; both complete integration audits passed.
- Independently reconstructed all headline, foreground-bin, and head-third point estimates, including saved mask nesting and per-region measurement counts. All earlier headline scores reproduce.
- Primary finding: the 25% center/random reversal is not universal across budgets. At 75% visibility, AIMv2 leads under both patterns and both fills. At 50%, black random masks do not resolve a winner.
- The new cohort repeats the 25% reversal, while its 50/75% random-mask intervals remain inconclusive. Its 164 head pairs retain the earlier direction, with smaller content-bundle accuracy gaps. These do not isolate a head effect.
- The English report, actual-input figures, and final v2 presentation are complete. The presentation has 12 main slides and two hidden backups, saved separately from milestone v6. Source-value checks, embedded-note checks, and visual inspection of all 14 exported slides passed. The 979-word script takes approximately 11.5 minutes at 90 words per minute with 40 seconds of pauses; human rehearsal is still needed.
- No pooling ablation or internal-mechanism analysis was added. New work is local; no GitHub synchronization or course submission has been performed.

See `reports/OCCLUSION_COMPLETION_EN.md` for the included-run status and `results/occlusion_completion/verification.json` for the latest independent checks.

## November 10 final controls

A clean-baseline comparison and an annotation-guided relocation experiment extend the original plan. The frozen encoders evaluated 731 main and 182 annotated images with two newly generated masks per image. The designs are in [FINAL_SENSITIVITY.md](FINAL_SENSITIVITY.md) and [PATCH_RELOCATION.md](PATCH_RELOCATION.md). The final report and talk include the observed responses from both models.

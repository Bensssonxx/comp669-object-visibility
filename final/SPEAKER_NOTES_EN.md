# Final presentation speaker notes

978 spoken words. Estimated 11.5 minutes at 90 words/minute including 40 seconds of pauses; not a rehearsal.

## 1. Comparing AIMv2 and DINOv2 Under Occlusion

Hi everyone, I'm Boshen. My project studies occlusion robustness: how well image recognition works when some of the image is hidden. I compare AIMv2 and DINOv2 on cat and dog breeds. I focus on the testing conditions that make one model appear better than the other.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv

## 2. Research question

A drop in accuracy after hiding information is expected. My question is more specific: does the masking pattern change which model performs better, and what animal content remains visible in those tests? This matters when we evaluate or choose a model. An accuracy score is easier to interpret when we know what evidence the model could actually see. I first explain the fixed setup, then show the inputs and results.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv

## 3. Data and fixed evaluation setup

I use Oxford-IIIT Pet, with thirty-seven breeds. The pretrained encoders stay frozen. Separate classifiers were trained using fourteen hundred eighty clean images, with three hundred seventy validation images for settings. The main evaluation uses seven hundred forty images. I also selected one hundred eighty-five previously unused images with head annotations. Both models receive identical masked pixels. The classifiers, pooling, and preprocessing stay fixed. The models still have different training histories, so this is a comparison of released systems, not a controlled training experiment.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv

## 4. Image visibility and animal visibility

These two masked versions both keep twenty-five percent of the image. But the center version keeps about eighty-four percent of this animal, while the random version keeps about twenty-two percent. Image visibility counts all image pixels. Animal visibility counts only pixels labeled as animal foreground. Hidden pixels are filled with gray or black; patch tokens are not removed. This example explains why an equal image budget can produce very different recognition conditions.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv

## 5. The initial ranking reversal

On the main sample with gray fill and twenty-five percent image visibility, AIMv2 gets 87.0 percent accuracy for center, versus 63.1 percent for DINOv2. With random patches, the order reverses: 33.6 percent versus 69.6 percent. Black fill shows the same initial ordering. However, center and random retain different amounts of animal. Next, I look at accuracy against measured animal visibility.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv

## 6. Accuracy versus animal visibility

Here the horizontal axis is animal visibility, and the vertical axis is classification accuracy. Each panel holds the image budget and masking pattern fixed. The points summarize foreground-visibility intervals. Center covers a much wider range than random, which is concentrated near twenty-five percent. These are different image groups, so a line is not a causal experiment that reveals more of the same animal. The full report includes all four patterns, sample counts, and uncertainty intervals. That led me to compare two masks on the same photo.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv

## 7. Moving patches while matching animal area

Can we compare masks on the very same photo while keeping about the same amount of animal visible? Only eight of the original seven hundred forty photos had a random mask close enough at this budget. So I built two new masks per photo. I moved at least sixteen of the sixty-four visible patches and kept animal visibility within three percentage points of the center version. 731 photos qualified. The table shows each model’s accuracy before and after moving the patches. AIMv2 went from 87.0 percent to 72.4 percent. DINOv2 went from 63.3 percent to 75.9 percent. The models respond in opposite directions. Which parts and textures they see can still change.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv

## 8. Model ordering across visibility budgets

Now return to the original masks. At fifty percent visibility, gray random masks still favor DINOv2. Black random masks give no clear winner. At seventy-five percent, AIMv2 has higher accuracy under both patterns and both fills. But AIMv2 started higher on clean images. Under gray random masks, it loses 5.6 points from its clean score, and DINOv2 loses 2.1. Which model finishes higher and which loses less are two different questions. What parts of the animal were actually visible?

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv

## 9. Similar animal area, different content

This separate experiment moves an equal-sized square on the same picture, always leaving seventy-five percent of the image visible. Among the original eligible head pairs, average animal visibility is 55.9 percent versus 55.4 percent. Head visibility is 83.0 percent versus 12.7 percent. Each percentage uses its own original region as the denominator. The remaining animal region changes in the opposite direction. The experiment therefore compares different visible-content combinations. It cannot isolate the head alone. I then repeat the broader evaluation on previously unused annotated images.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv

## 10. A check on previously unused images

The new cohort has one hundred eighty-five images, five per breed. They were excluded from all earlier training, validation, and evaluation, and selected before predictions. At twenty-five percent visibility, center again favors AIMv2 and random favors DINOv2. At seventy-five percent, the point estimates favor AIMv2 under both patterns, but the random-mask intervals are still too wide to resolve a winner. The matched patch experiment also repeats the opposite responses on 182 eligible photos. These photos come from the training-and-validation source split, which includes head boxes. I keep them separate from the main sample.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv

## 11. Head-region pairs on the new images

On the new images, 164 pairs satisfy the same foreground-matching and head-contrast rules. Their average animal visibility is 55.4 percent versus 55.0 percent, while head visibility is 83.0 percent versus 15.7 percent. Both models are more accurate with higher head coverage, by about fifteen percentage points for AIMv2 and seven for DINOv2. Other animal regions and background are shown as well. This checks the earlier content comparison on new pictures, but it keeps the same limitation: head coverage changes together with other information.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv

## 12. What this study tells us

If I were choosing a model, I would ask how much of the image is usually hidden and which parts stay visible. I would report both accuracy on those images and the change from clean accuracy. Here, those measures can favor different models. The patch and head comparisons show why knowing the visible area alone is insufficient. These findings concern two fixed systems and artificial masks on pet photos. I used Codex to help with code, experiments, analysis and presentation. The link takes you to the code and predictions. Thank you.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv

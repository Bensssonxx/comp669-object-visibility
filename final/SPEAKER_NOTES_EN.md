# Final presentation speaker notes

997 spoken words. Estimated 11.7 minutes at 90 words/minute including 40 seconds of pauses; not a rehearsal.

## 1. Comparing AIMv2 and DINOv2 Under Occlusion

Hi everyone, I'm Boshen. My project studies occlusion robustness: how well image recognition works when some of the image is hidden. I compare AIMv2 and DINOv2 on cat and dog breeds. I focus on the testing conditions that make one model appear better than the other.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv; docs/REGION_SWAP_PROTOCOL.md; results/region_swap/summary.csv; results/region_swap/conditions.csv

## 2. Research question

Earlier PatchDrop experiments showed that vision transformers can still recognize images with many patches hidden. My question is whether a change in the masking pattern can reverse which system looks better on the same photos. If it can, I want to know whether that reversal persists when both versions show about the same amount of the animal. I will start with the data and the two classifiers.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv; docs/REGION_SWAP_PROTOCOL.md; results/region_swap/summary.csv; results/region_swap/conditions.csv; https://papers.neurips.cc/paper/2021/hash/c404a5adbf90e09631678b13b05d9d7a-Abstract.html

## 3. Data and fixed evaluation setup

I use Oxford-IIIT Pet, with thirty-seven breeds. The pretrained encoders stay frozen. Separate classifiers were trained using fourteen hundred eighty clean images, with three hundred seventy validation images for settings. The main evaluation uses seven hundred forty images. I added a head-annotated sample, then reserved fresh official test photos for the last two checks. Both models receive identical masked pixels. The classifiers, pooling, and preprocessing stay fixed. The models still have different training histories, so this is a comparison of released systems, not a controlled training experiment.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv; docs/REGION_SWAP_PROTOCOL.md; results/region_swap/summary.csv; results/region_swap/conditions.csv

## 4. Image visibility and animal visibility

These two masked versions both keep twenty-five percent of the image. But the center version keeps about eighty-four percent of this animal, while the random version keeps about twenty-two percent. Image visibility counts all image pixels. Animal visibility counts only pixels labeled as animal foreground. Hidden pixels are filled with gray or black; patch tokens are not removed. This example explains why an equal image budget can produce very different recognition conditions.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv; docs/REGION_SWAP_PROTOCOL.md; results/region_swap/summary.csv; results/region_swap/conditions.csv

## 5. The initial ranking reversal

On the main sample with gray fill and twenty-five percent image visibility, AIMv2 gets 87.0 percent accuracy for center, versus 63.1 percent for DINOv2. With random patches, the order reverses: 33.6 percent versus 69.6 percent. Black fill shows the same initial ordering. However, center and random retain different amounts of animal. Next, I look at accuracy against measured animal visibility.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv; docs/REGION_SWAP_PROTOCOL.md; results/region_swap/summary.csv; results/region_swap/conditions.csv

## 6. Accuracy versus animal visibility

Here the horizontal axis is animal visibility, and the vertical axis is classification accuracy. Each panel holds the image budget and masking pattern fixed. The points summarize foreground-visibility intervals. Center covers a much wider range than random, which is concentrated near twenty-five percent. These are different image groups, so a line is not a causal experiment that reveals more of the same animal. The full report includes all four patterns, sample counts, and uncertainty intervals. That led me to compare two masks on the same photo.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv; docs/REGION_SWAP_PROTOCOL.md; results/region_swap/summary.csv; results/region_swap/conditions.csv

## 7. Moving patches while matching animal area

Can we compare masks on the very same photo while keeping about the same amount of animal visible? Only eight of the original seven hundred forty photos had a random mask close enough at this budget. So I built two new masks per photo. I moved at least sixteen of the sixty-four visible patches and kept animal visibility within three percentage points of the center version. 731 photos qualified. The table shows each model’s accuracy before and after moving the patches. AIMv2 went from 87.0 percent to 72.4 percent. DINOv2 went from 63.3 percent to 75.9 percent. The models respond in opposite directions. Which parts and textures they see can still change.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv; docs/REGION_SWAP_PROTOCOL.md; results/region_swap/summary.csv; results/region_swap/conditions.csv

## 8. Model ordering across visibility budgets

Now return to the original masks. At fifty percent visibility, gray random masks still favor DINOv2. Black random masks give no clear winner. At seventy-five percent, AIMv2 has higher accuracy under both patterns and both fills. But AIMv2 started higher on clean images. Under gray random masks, it loses 5.6 points from its clean score, and DINOv2 loses 2.1. Which model finishes higher and which loses less are two different questions. What parts of the animal were actually visible?

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv; docs/REGION_SWAP_PROTOCOL.md; results/region_swap/summary.csv; results/region_swap/conditions.csv

## 9. Similar animal area, different content

This separate experiment moves an equal-sized square on the same picture, always leaving seventy-five percent of the image visible. Among the original eligible head pairs, average animal visibility is 55.9 percent versus 55.4 percent. Head visibility is 83.0 percent versus 12.7 percent. Each percentage uses its own original region as the denominator. Both systems did better with more head visible. Other animal parts changed in the opposite direction. It cannot isolate the head alone. That leaves two questions. Does the earlier relocation result hold up on fresh photos? And can we test the animal and background separately?

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv; docs/REGION_SWAP_PROTOCOL.md; results/region_swap/summary.csv; results/region_swap/conditions.csv

## 10. Relocation on fresh test photos

Could the earlier relocation result depend on which photos I used? I set the rules first and drew ten previously unused official test photos per breed. Of 370 photos, 364 met the same area-matching rules. The table compares the center with the two relocated masks. AIMv2 went from 87.9 percent to 72.4 percent. DINOv2 went from 63.4 percent to 75.5 percent. Could changing the animal and changing its surroundings affect accuracy differently?

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv; docs/REGION_SWAP_PROTOCOL.md; results/region_swap/summary.csv; results/region_swap/conditions.csv

## 11. Animal and background patch swaps

For that question, I used photos with enough patches entirely inside the animal and entirely in the background. In each photo I hid four patches and revealed four others. I did this inside the animal only, in the background only, and in both regions. Look at the pictures. Even the number of visible animal pixels stays exactly the same. The table gives accuracy under each condition. DINOv2 gained more from an animal swap than a background swap, by about four percentage points. For AIMv2 the difference was too small to distinguish. These swaps cover a small part of the image, so I limit this conclusion to this particular test.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv; docs/REGION_SWAP_PROTOCOL.md; results/region_swap/summary.csv; results/region_swap/conditions.csv; https://openreview.net/pdf?id=gl3D-xY7wLq

## 12. What this study tells us

If I were choosing a model, I would ask how much of the image is usually hidden and which parts stay visible. I would report both accuracy on those images and the change from clean accuracy. Here, those measures can favor different models. Even when visible area is fixed, changing which animal patches are shown can change accuracy. These findings concern two fixed systems and artificial masks on pet photos. I used Codex to help with code, experiments, analysis and presentation. The link takes you to the code and predictions. Thank you.

Sources (not spoken): docs/OCCLUSION_COMPLETION_PROTOCOL.md; results/occlusion_completion/accuracy_summary.csv; results/occlusion_completion/foreground_bins.csv; results/occlusion_completion/pair_measurements.csv; results/occlusion_completion/verification.json; results/occlusion_completion/clean_loss.csv; results/occlusion_completion/area_matched_patterns.csv; results/patch_relocation/summary.csv; results/patch_relocation/conditions.csv; docs/REGION_SWAP_PROTOCOL.md; results/region_swap/summary.csv; results/region_swap/conditions.csv

# Complete milestone speech

This is the complete spoken script for slides 1–12, including the opening, slide transitions and closing. Read the paragraphs below each timing line. Do not read headings, timing lines or the source appendix aloud. Slides 13–14 are hidden backups for questions.

The script contains 1006 spoken words. At 90-100 words/minute plus 40 seconds for pauses and slide changes, the estimate is 10.7-11.8 minutes. This is a word-rate estimate, not a timed rehearsal.

## Slide 1. Comparing AIMv2 and DINOv2 Under Occlusion

Timing guide: 0:00–0:33. About 33 seconds.

Hi everyone, I'm Boshen. My project studies occlusion robustness: how well a model recognizes an object when parts are hidden.

I compare AIMv2 and DINOv2 on cat and dog breeds, using classification accuracy under different masks. The question is how those masks affect our comparison.

## Slide 2. Research question

Timing guide: 0:33–1:26. About 53 seconds.

An accuracy drop after hiding information is expected. What matters here is whether changing the mask changes which model appears more robust.

For example, AIMv2 may perform better when we keep the center of the picture, while DINOv2 may perform better when we keep random small patches. So the way we hide information may affect which model we would choose.

First, let's look at how much of the animal each masking pattern leaves visible.

## Slide 3. Same image area, different animal area

Timing guide: 1:26–2:18. About 52 seconds.

Both masked versions keep twenty-five percent of the picture. But center visibility keeps about eighty-four percent of this cat, while random visibility keeps about twenty-two percent.

Here, foreground means the animal. Picture visibility uses the whole picture as its reference. Foreground visibility uses the original animal region.

So equal picture area can retain different content. This is why I measure animal visibility alongside accuracy. Now, how do I test this across more images?

## Slide 4. First test and second test

Timing guide: 2:18–3:43. About 85 seconds.

This slide shows the steps of the experiment. All images come from the same Oxford-IIIT Pet dataset, with thirty-seven breeds.

First, I use fourteen hundred eighty clean images to train a classifier for each model. I use three hundred seventy validation images to choose the classifier settings. The pretrained models stay fixed.

I then test one hundred eighty-five images, five per breed, to compare the models under different masking patterns.

Next, I test another seven hundred forty images, twenty per breed. These are different pictures from the same dataset. This checks whether the same model ranking appears on different images.

I keep the same models and classifiers for both tests, without retraining. Next, I'll explain what else stays the same in our comparisons.

## Slide 5. What stays the same?

Timing guide: 3:43–4:48. About 65 seconds.

This table separates three comparisons.

In the first row, both models see the same pictures and masks, with the same classifier fitting method. The models and their training histories differ.

In the second row, I keep the model, picture, mask and visible pixels fixed. Only the fill changes from gray to black.

In the last row, I move the same-sized square on the same picture. The model stays fixed, but visible parts and background change.

The bottom line is that training differences remain uncontrolled. We cannot isolate a training mechanism. Now, the results.

## Slide 6. The better model changes with the mask

Timing guide: 4:48–5:41. About 53 seconds.

These are the second-test results: seven hundred forty images, gray fill, and twenty-five percent of each picture visible. All four patterns were tested. This chart focuses on center and random, where the ranking reverses. Blue is AIMv2. Orange is DINOv2.

For center, AIMv2 gets eighty-seven percent accuracy and DINOv2 sixty-three. For random, AIMv2 gets thirty-four percent and DINOv2 seventy.

So changing the mask changes which model does better. Does this also happen with black fill?

## Slide 7. The pattern repeats with black fill

Timing guide: 5:41–6:30. About 49 seconds.

The first two rows repeat the gray results. The next two show black fill.

With black, center gives AIMv2 about eighty-seven percent accuracy and DINOv2 sixty-two. Random gives AIMv2 about thirty percent and DINOv2 sixty-two.

As noted below, visible pixels and mask positions stay identical. Only the fill color changes. The ordering repeats, although the scores change.

Next, I measure how much animal content these patterns leave visible.

## Slide 8. How much of the animal is visible?

Timing guide: 6:30–7:27. About 57 seconds.

All four patterns keep twenty-five percent of the picture. The chart shows how much of the animal remains, averaged over seven hundred forty images.

From left to right, top keeps about ten percent of the animal, bottom fifteen, center sixty-three, and random twenty-five.

So mask location and visible content change together. This does not tell us how much animal visibility explains the accuracy gap.

Next, I move a fixed-size square on the same image to check what area measurements miss.

## Slide 9. Same square, different locations

Timing guide: 7:27–8:46. About 79 seconds.

Here, a square covers twenty-five percent, leaving seventy-five percent visible. I move it to different locations.

The table compares more versus less animal visible. AIMv2 gets about ninety-three versus sixty-seven percent accuracy. DINOv2 gets eighty-three versus sixty-seven. Both have higher average accuracy when more animal remains.

Below, I compare two versions of one image. For example, sixty and sixty-two percent animal visibility meet the three-percentage-point limit.

For each model, I count pairs with one correct and one wrong answer: about eleven percent for AIMv2, nine percent for DINOv2.

These percentages are not accuracies. Two wrong answers count as no switch, so fewer switches are not necessarily better. Next, which animal parts remain visible?

## Slide 10. Similar area, different animal parts

Timing guide: 8:46–9:55. About 69 seconds.

This separate check uses head boxes. Of one hundred eighty-five unused images, one hundred fifty-nine meet the pairing rules.

The pictures show the same-sized square in different positions. The left version keeps more head visible.

The table shows higher accuracy with more head visible: a gap of about nineteen percentage points for AIMv2 and eleven for DINOv2.

The measurements below show similar animal visibility, about fifty-six percent in both groups, but head visibility differs: eighty-three versus thirteen percent.

Other parts and background change too. This cannot isolate a head effect or explain the main crossover. Now, the conclusions.

## Slide 11. What we learned

Timing guide: 9:55–10:48. About 53 seconds.

On the left are the findings. The better model changes with the mask under gray and black fill. Equal picture area can retain different amounts of animal. Similar animal area can show different parts.

On the right are the limits. Training differs between models. Mask position and content change together. We use one dataset and artificial masks.

Our follow-up focused on twenty-five percent image visibility. Next, does the ranking also reverse when more remains visible?

## Slide 12. Next steps

Timing guide: 10:48–11:51. About 63 seconds.

First, I'll test fifty and seventy-five percent image visibility across all four patterns, using the same seven hundred forty images, models and classifiers. This checks whether the reversal also occurs with less occlusion.

Second, I'll compare averaging patch features with taking their maximum. I'll fit each classifier on clean training images and choose settings on validation. This checks whether feature pooling affects the reversal. Both steps reuse evaluated images.

The public repository contains our code and results. Codex helped with the work and presentation, as disclosed below. Thank you.

## Source appendix (not spoken)

Slide 1: docs/EXTENSION_V2_PROTOCOL.md; reports/EXTENSION_V2_EN.md

Slide 2: docs/RELATED_WORK.md; Naseer et al., https://arxiv.org/abs/2105.10497; Xiao et al., https://arxiv.org/abs/2006.09994

Slide 3: results/extension_v2/design_example_selection.json; results/extension_v2/conditions.csv; Oxford-IIIT Pet images and annotations, https://www.robots.ox.ac.uk/~vgg/data/pets/

Slide 4: docs/PROTOCOL.md; docs/EXTENSION_V2_PROTOCOL.md; results/extension_v2/preparation_audit.json; pre-inference commit 815a33b

Slide 5: docs/EXTENSION_V2_PROTOCOL.md; reports/EXTENSION_V2_EN.md, Motivation and limits

Slide 6: results/extension_v2/summary.csv; results/extension_v2/primary_contrasts.csv; results/extension_v2/analysis_audit.json

Slide 7: results/extension_v2/summary.csv; results/extension_v2/primary_contrasts.csv; results/extension_v2/fill_sensitivity.csv

Slide 8: results/extension_v2/foreground_coverage.csv; results/extension_v2/conditions.csv

Slide 9: docs/EXTENSION_V2_PROTOCOL.md; results/extension_v2/paired_summary.csv; results/extension_v2/eligibility.csv

Slide 10: results/extension_v2/preparation_audit.json; results/extension_v2/paired_summary.csv; results/extension_v2/design_example_selection.json; Oxford-IIIT Pet, https://www.robots.ox.ac.uk/~vgg/data/pets/

Slide 11: reports/EXTENSION_V2_EN.md; docs/EXTENSION_V2_PROTOCOL.md

Slide 12: https://github.com/Bensssonxx/comp669-object-visibility; docs/AI_USE.md; docs/RELATED_WORK.md

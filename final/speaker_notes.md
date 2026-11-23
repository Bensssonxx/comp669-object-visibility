# Final presentation speaker notes

1030 spoken words. About 10.0 min at 110 words/min, 11.5 min at 95 words/min (both including 40 s of pauses). Estimate only; rehearse with a timer. Limit: 12 min.

## 1. Comparing AIMv2 and DINOv2 under occlusion  (40 words)

Hi everyone, I'm Boshen. I compared two vision transformers, AIMv2 and DINOv2, on images where part of the picture is hidden. What I wanted to know is whether the way you hide the image changes which model looks more robust.

## 2. Same 25% of the image, very different amount of the animal  (78 words)

This is one of the test photos. Both masked versions keep exactly a quarter of the image and fill the rest with gray. The center mask still shows 84 percent of this cat, but the random mask shows only 22 percent. So "25 percent visible" can mean very different inputs. I wanted to see whether the mask pattern can flip which model wins, and if it does, whether that's only because one mask shows more of the animal.

## 3. Both models see exactly the same masked pixels  (109 words)

The data is Oxford-IIIT Pet, 37 cat and dog breeds. Hidden patches are filled with gray rather than removed, so both models get exactly the same pixels. I keep both encoders frozen and put a linear classifier on top of each, trained once on clean images. The main test set is 740 images, 20 per breed. I used four mask patterns, top rows, bottom rows, center and random, at 25, 50 and 75 percent visible. I also reran the main experiment with black fill as a check. The two models were pretrained very differently, so I can compare how they behave, but I can't say what causes the difference.

## 4. At 25% visible, the winner flips with the mask pattern  (56 words)

Here's the main result, with a quarter of the image visible. With the center mask, AIMv2 gets 87.0 percent and DINOv2 gets 63.1. With random patches it reverses: 33.6 for AIMv2 and 69.6 for DINOv2. Black fill gives the same flip. Keep in mind, though, that the two masks show very different amounts of the animal.

## 5. The flip only happens when most of the image is hidden  (67 words)

These are the plain accuracies at each visibility level. With the center mask, on the left, AIMv2 stays ahead the whole way. With random patches the lines cross. At 25 percent DINOv2 is far ahead, 69.6 to 33.6, and at 75 percent AIMv2 is ahead, 87.9 to 82.5. The flip only happens when most of the image is gone. DINOv2 isn't better at random masks in general.

## 6. Center and random masks barely overlap in animal visibility  (99 words)

For every masked image I measured how much of the animal is still visible, and this chart counts the images in each range. With the center mask it depends on how big the animal is and where it sits, so the images spread from about 30 to 100 percent. With random patches almost every image shows about a quarter of the animal. Because the two masks barely overlap, the main experiment can't tell me whether the flip comes from how much animal is visible or from the mask itself. For that I needed controlled tests on the same photo.

## 7. Showing the head helps both models, AIMv2 more  (131 words)

The first controlled test uses head annotations. Only the trainval split has head boxes, so I used trainval photos that were never used for training. On each photo I hide one square of the same size, once over the body and once over the head. I only kept pairs where the animal area differs by three points or less, 1.4 on average, and the head area differs by at least twenty. 159 of 185 photos had a pair like that. With the head visible, AIMv2 gets 92.4 percent, and 73.2 with it hidden. DINOv2 goes from 82.9 to 72.4. A second set of 164 photos went the same way. What's visible matters, not just how much, although hiding the head also uncovers other parts, so this isn't a clean head effect.

## 8. Matching the animal area does not remove the difference  (160 words)

This is the test I care about most. On the left is the center mask. On the right is the same photo with the same 64 visible patches, but some have moved. Red squares were visible and are now hidden, and yellow ones were hidden and are now shown. I sort the patches into ten bands by how much animal they contain, and each band keeps the same number of visible patches. A new mask only counts if the animal area stays within three points of the original, 0.3 on average, and at least sixteen patches moved. In the chart, gray is before and green is after. AIMv2 drops from 87.0 to 72.4 percent, while DINOv2 goes up from 63.3 to 75.9. I ran the same thing on 364 photos I'd never used and got the same result. So even with the animal area held fixed, the two models react in opposite ways to how the visible patches are arranged.

## 9. DINOv2 reacts more to which animal patches are shown  (156 words)

The last question is whether it's the animal patches or the background patches that matter. On 366 new photos I start again from the center mask. In the second picture I change only the animal: four visible animal patches get hidden and four hidden ones get shown. The third picture does the same in the background, and the last one does both. I only use patches that are entirely animal or entirely background, so the visible pixel counts are exactly the same in all four. I fixed the swap at four patches before running and didn't try other sizes. For DINOv2, changing animal patches raises accuracy from 57.7 to 64.4 percent, while changing background patches only gets it to 60.1. AIMv2 hardly moves either way. That suggests DINOv2's gain on the last slide comes mostly from which parts of the animal it can see, though a four-patch swap is too small to explain the whole effect.

## 10. Which model does better depends on what stays visible  (134 words)

To wrap up, here's when each model does better in these tests. AIMv2 wins when the visible part is one connected block, like the center mask, when most of the image is visible, and when the head is visible. DINOv2 wins when only scattered patches are left, and when the visible patches are spread out, even at the same animal area. It also loses less from its clean accuracy. So there's no single winner: the ranking depends on how much is hidden and how the visible part is arranged. All of this is for two fixed models, one dataset and artificial square masks. Next I'd like to try real occluders, like objects in front of the animal, and a second dataset. The code and predictions are on GitHub. Thanks, I'm happy to take questions.

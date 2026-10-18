# Questions to prepare for

**What did you learn beyond "occlusion hurts"?**

The model ordering depends on the masking condition. At 25% image visibility, DINOv2 performs better under random masks, while AIMv2 performs better under center-nearest visibility. These masks retain different foreground distributions. I also measured prediction changes in same-image pairs with closely matched foreground area, so image area or foreground area alone is not a complete description of the input.

**Does this prove prefix attention helps or hurts?**

No. These checkpoints differ in their pretraining and other design choices. I characterize their behavior under specified inputs; I do not isolate a pretraining mechanism.

**Have you controlled which object parts remain?**

No. I control image identity, occluder area and shape, and approximately match annotated foreground area. The surviving parts, texture and background can still differ. The downloaded test split has no head-box XML, so I have not quantified head visibility there.

**Can you compare all four standard patterns after matching foreground visibility?**

Not reliably at 50% visible image area in this pilot: the prespecified common-bin rule has no overlap. The square-occluder pairs are a separate diagnostic. I report that limitation rather than extrapolating an adjusted comparison.

**Why C=10? Could the classifier choice explain the results?**

The original clean-validation grid selected C=10 for both models. Because it was the upper boundary, I added a labeled post-hoc sensitivity analysis at C=10,100,1000. The random-versus-center model ordering persisted across those values, but correctness-flip rates changed. I kept the original estimates and reported the supplement separately. Pooling and other probe choices remain limitations.

**Is a lower flip rate better robustness?**

Not by itself. Two wrong predictions produce no correctness flip. I also report each version's accuracy and the both-correct/both-wrong counts.

**How reproducible is the run?**

The repository pins model code and checkpoint hashes, data splits, masks and probe rules. I found that the JPEG decoder also mattered, so the reference environment pins libjpeg 9e. A second reference environment reproduced every selected preprocessed input hash and the first 8 feature conditions per encoder exactly. Saved classifiers reproduce all 8,510 saved test predictions. I have not run a second full independent experiment.

**What did AI do?**

Codex helped inspect sources, implement and debug the pipeline, execute experiments and draft analysis and slides. The reported numbers come from saved executions. I need to understand and review the code, assumptions and claims before presenting the project.

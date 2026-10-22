# Research question and contribution

This project examines how masking conditions affect the interpretation of occlusion robustness in frozen AIMv2-L/14 and DINOv2-L/14 systems.

The questions are:

1. Does the model ordering change when the visible image-area budget stays fixed but the masking pattern changes?
2. How much annotated foreground remains under those conditions?
3. What can same-image pairs with equal occluder area/shape and approximately matched foreground visibility tell us about remaining content differences?

Oxford-IIIT Pet replaces the original ImageNet-100 proposal because the experiment needs pixel-level foreground annotations. The results concern 37-class pet-breed classification on this dataset. They are not ImageNet results.

The contribution is a course-scale replication and diagnostic extension: reproducible shared-input evaluation, measured foreground coverage, a follow-up fixed before new predictions, and explicit same-image diagnostic comparisons. Prior work such as PatchDrop already studies foreground/background masking. Paper-level novelty has not been established.

Both official pretrained encoders stay frozen. Separate logistic classifiers train only on clean pilot-training features, with regularization selected on clean validation. The follow-up reuses the original learned classifiers. This is a shared diagnostic readout, not either model's best published evaluation recipe.

The 740-image follow-up repeats the center/random ordering crossover under gray and black fill. Equal image visibility retains different foreground distributions. Approximately matched foreground area still permits different parts, texture and background to remain. The auxiliary head-region analysis uses a separate cohort and does not explain the main crossover or identify an isolated causal head effect.

Cross-model pretraining remains uncontrolled. These results do not identify the effect of prefix attention, establish a general model ranking, or demonstrate robustness to natural occluders. Filling pixels retains all patch tokens and does not reduce inference compute.

Current priorities are an understandable milestone presentation and student review of the implementation and claims. A further study should use a separately fixed protocol for readout/pooling sensitivity, then consider another dataset or natural occluders.

Start with the [code guide](CODE_GUIDE.md), [pilot protocol](PROTOCOL.md), [follow-up protocol](EXTENSION_V2_PROTOCOL.md), and [follow-up report](../reports/EXTENSION_V2_EN.md). AI assistance is disclosed in [AI_USE.md](AI_USE.md).

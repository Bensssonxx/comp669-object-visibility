# Object visibility and occlusion robustness

COMP 669 project by Boshen Yang.

I compare AIMv2 and DINOv2 on Oxford-IIIT Pet to study how masking patterns affect image classification. Both models stay frozen, with classifiers trained on clean images, and receive the same masked inputs.

In the follow-up tests with 25% of each image visible, AIMv2 performs better when the center remains visible, while DINOv2 performs better when random patches remain visible. This ranking reversal appears with both gray and black fill. We also measure how much of the animal remains visible, since equal image area can leave very different amounts of the animal in view.

The results apply to these models and test conditions. They do not establish which differences in training or architecture cause the observed behavior.

## Code and results

- [Core code](src/occlusion_visibility/): data processing, masks, model features and classifiers.
- [Follow-up experiments](scripts/extension_v2.py) and [analysis](scripts/analyze_extension.py).
- [Results report](reports/EXTENSION_V2_EN.md).
- [Code guide](docs/CODE_GUIDE.md): where to start reading the implementation.
- [Pilot protocol](docs/PROTOCOL.md) and [follow-up protocol](docs/EXTENSION_V2_PROTOCOL.md).

AI assistance is described in [docs/AI_USE.md](docs/AI_USE.md). Dataset and model sources are listed in [docs/SOURCES.json](docs/SOURCES.json).

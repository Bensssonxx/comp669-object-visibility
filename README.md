# Object visibility and occlusion robustness

COMP 669 project by Boshen Yang.

I compare AIMv2 and DINOv2 on Oxford-IIIT Pet to study how masking patterns affect image classification. Both models stay frozen, with classifiers trained on clean images, and receive the same masked inputs.

With 25% of each image visible, AIMv2 performs better when the center remains visible, while DINOv2 performs better when random patches remain visible. At 75% visibility on the main sample, AIMv2 leads under both patterns. Both findings hold with gray and black fill. We also measure visible animal area and regions to describe how the test inputs differ.

The results apply to these models and test conditions. They do not establish which differences in training or architecture cause the observed behavior.

## Code and results

- [Core code](src/occlusion_visibility/): data processing, masks, model features and classifiers.
- [Follow-up experiments](scripts/complete_occlusion.py) and [analysis](scripts/analyze_completion.py).
- [Results report](reports/OCCLUSION_COMPLETION_EN.md) and [controlled animal and background swaps](docs/REGION_SWAP_PROTOCOL.md).
- [Code guide](docs/CODE_GUIDE.md): where to start reading the implementation.
- [Pilot protocol](docs/PROTOCOL.md) and [current follow-up protocol](docs/OCCLUSION_COMPLETION_PROTOCOL.md).

Run `python3 scripts/check_final_results.py` to verify the final comparisons from the saved predictions. It uses the Python standard library.

AI assistance is described in [docs/AI_USE.md](docs/AI_USE.md). Dataset and model sources are listed in [docs/SOURCES.json](docs/SOURCES.json).

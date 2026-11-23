# Does the mask pattern change which model looks more robust?

COMP 669 (Fall 2026) final project, Boshen Yang.

I compared two frozen vision transformers, AIMv2-L/14 and DINOv2-L/14, on Oxford-IIIT Pet images with parts of the image hidden. Each model gets a linear classifier trained on clean images, and both models see exactly the same masked pixels.

## Main results

- With 25% of the image visible, AIMv2 wins with a center mask (87.0% vs 63.1%) and DINOv2 wins with random patches (69.6% vs 33.6%). Black fill gives the same flip.
- The flip goes away as more of the image is visible. At 75% visible, AIMv2 is ahead with both masks.
- Center and random masks show very different amounts of the animal, so I also ran controlled tests on the same photos. When I move the visible patches but keep the animal area within 3 percentage points, AIMv2 drops 14.6 points and DINOv2 gains 12.5. The same thing happened on 364 test photos I hadn't used before.

These results are for two fixed models, one dataset and square masks. They don't tell us which part of training causes the difference.

## What's where

| Folder | Contents |
| --- | --- |
| `src/occlusion_visibility/` | Data loading, masks, frozen encoders, linear classifiers |
| `scripts/` | Experiment runners, analysis, report generation and checks |
| `results/` | Saved predictions and summary tables for every run |
| `reports/` | Written results. Start with [OCCLUSION_COMPLETION.md](reports/OCCLUSION_COMPLETION.md) |
| `docs/` | Experiment protocols, data and model sources, and reproducibility checks (`*_CHECK.json`) |
| `final/` | Final presentation slides and speaker notes |
| `milestone/` | Milestone slides and speaker notes |
| `tests/` | Unit tests |

[docs/CODE_GUIDE.md](docs/CODE_GUIDE.md) walks through the code in reading order.

## Checking the numbers

`python3 scripts/check_final_results.py` recomputes the final comparisons from the saved predictions. It only needs the Python standard library.

Running the unit tests:

```bash
source scripts/env.sh
.reference-conda/bin/python -m pytest -q
```

Rerunning the models needs the checkpoints and the Pet images; the setup steps are in the code guide. Dataset and model sources are listed in [docs/SOURCES.json](docs/SOURCES.json).

## AI use

I used AI tools for much of this project. Details are in [docs/AI_USE.md](docs/AI_USE.md).

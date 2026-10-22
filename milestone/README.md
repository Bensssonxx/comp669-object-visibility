# Milestone presentation materials

Use **v6** for the current milestone. It uses shorter slide text and a complete conversational speech following the visible slide order, connecting each test to the next question and defining occlusion robustness. The experiment results are unchanged. It explicitly connects the first 185-image test to the second 740-image test from the same dataset. Earlier v5 and v4 materials remain preserved.

## Current files

- [Editable PowerPoint](COMP669_Object_Visibility_Milestone_v6.pptx): 12 main slides and two hidden backup slides.
- [English speaker notes](SPEAKER_NOTES_EN_v6.md): the complete conversational speech, with an opening, transitions and closing for slides 1-12. The same speech is embedded in the slide notes; timing and source information are not spoken.
- [Questions and answers](QA_EN_v5.md): motivation, controls, annotation limits, uncertainty, reproducibility and AI assistance.
- [Slide data](slide_data_v6.json): saved evidence, text and source-file hashes.
- [Timing estimate](TIMING_v6.json): 1,006 spoken words. At 90-100 words/minute plus 40 seconds of pauses, estimated time is 10:44-11:51. This is not a timed human rehearsal.
- [Follow-up report](../reports/EXTENSION_V2_EN.md): technical results and limitations.

Slides 13-14 are hidden during the main slide show and are available for questions.

## Research narrative

1. A useful robustness comparison should specify which information remains visible.
2. Test 185 images first, then another 740 images from the same official test split. Keep the original models and classifiers fixed across both rounds.
3. Separate shared-input model comparisons, within-image fill comparisons, and equal-square-area diagnostic pairs.
4. Show that center/random model ordering reverses under both fills, while absolute accuracy remains fill-sensitive.
5. Measure the different foreground coverage and explain why matched area still permits different parts/background.
6. State that pretraining, pure position effects and the isolated contribution of the head remain unresolved.
7. First extend all four patterns to 50% and 75% image visibility, then compare mean versus max pooling under a new fixed protocol. Both steps reuse evaluated images.

## Build and verify

The deck uses the bundled `@oai/artifact-tool` runtime. Use the Node executable returned by the workspace dependency tool and link `.build-presentation/node_modules` to its supplied packages directory. Run from the repository root:

```bash
python3 scripts/prepare_milestone_v6.py
cp scripts/build_milestone_v6.mjs .build-presentation/build_milestone_v6.mjs
node .build-presentation/build_milestone_v6.mjs
python3 scripts/verify_milestone_v6.py
```

The builder refuses to overwrite an existing final PPTX. Use a new `MILESTONE_BUILD` value for another deck revision. The v6 layout and numbers have been checked using slide renders and saved experiment evidence. Native PowerPoint execution has not been tested. Generated build/validation files stay in the ignored `.build-presentation/` folder.

## Earlier pilot materials

`COMP669_Object_Visibility_Milestone_v4.pptx`, `SPEAKER_NOTES_EN.md`, `QA_EN.md`, `slide_data.json` and `assets/` describe pilot v1. The v5 files contain the more detailed earlier presentation. Prefer the versioned v6 files above for the current presentation.

## Before submission

The October 21, 2026 live Canvas assignment check confirmed the October 21, 11:59 PM Eastern deadline. Submit a PPT/PDF, or a PDF linking to Google Slides, and include the code repository link and a brief AI-use disclosure. The previously checked presentation format is 12 minutes plus 1-2 minutes for questions.

The public repository contains protocols, code, predictions, analysis and the current v6 presentation package. The student should review and understand the work and rehearse at their actual speaking rate. No Canvas submission or instructor message has been made by this workflow.

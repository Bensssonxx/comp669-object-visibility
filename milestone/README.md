# Milestone presentation materials

Use **v5** for the current milestone. It includes follow-up v2 and emphasizes the motivation, experimental controls, findings and interpretation limits. The v4 deck remains as the earlier pilot presentation.

## Current files

- [Editable PowerPoint](COMP669_Object_Visibility_Milestone_v5.pptx): 12 main slides and two hidden backup slides.
- [English speaker notes](SPEAKER_NOTES_EN_v5.md): the same spoken script is embedded in the slide notes, with timing targets, anchors and sources.
- [Questions and answers](QA_EN_v5.md): motivation, controls, annotation limits, uncertainty, reproducibility and AI assistance.
- [Slide data](slide_data_v5.json): saved evidence, text and source-file hashes.
- [Timing estimate](TIMING_v5.json): 1,104 spoken words, with an 11-minute target. At 100-110 words/minute plus 40 seconds of pauses, estimated time is 10:42-11:42. This is not a timed human rehearsal.
- [Follow-up report](../reports/EXTENSION_V2_EN.md): technical results and limitations.

Slides 13-14 are hidden during the main slide show and are available for questions.

## Research narrative

1. A useful robustness comparison should specify which information remains visible.
2. On 740 new official-test images, keep the original probes fixed and compare identical inputs across both encoders.
3. Separate shared-input model comparisons, within-image fill comparisons, and equal-square-area diagnostic pairs.
4. Show that center/random model ordering reverses under both fills, while absolute accuracy remains fill-sensitive.
5. Measure the different foreground coverage and explain why matched area still permits different parts/background.
6. State that pretraining, pure position effects and the isolated contribution of the head remain unresolved.
7. Propose readout/pooling sensitivity under a new fixed protocol.

## Build and verify

The deck uses the bundled `@oai/artifact-tool` runtime. Use the Node executable returned by the workspace dependency tool and link `.build-presentation/node_modules` to its supplied packages directory. Run from the repository root:

```bash
python3 scripts/prepare_milestone_v5.py
cp scripts/build_milestone_v5.mjs .build-presentation/build_milestone_v5.mjs
node .build-presentation/build_milestone_v5.mjs
python3 scripts/verify_milestone_v5.py
```

The builder refuses to overwrite an existing final PPTX. Use a new `MILESTONE_BUILD` value for another deck revision. The delivered v5 layout and numbers have been checked, including representative LibreOffice renders. Native PowerPoint execution has not been tested. Generated build/validation files stay in the ignored `.build-presentation/` folder.

## Earlier pilot materials

`COMP669_Object_Visibility_Milestone_v4.pptx`, `SPEAKER_NOTES_EN.md`, `QA_EN.md`, `slide_data.json` and `assets/` describe pilot v1. Prefer the versioned v5 files above for the current presentation.

## Before submission

The last live Canvas check on October 19, 2026 showed an October 21, 11:59 PM Eastern slide deadline and an October 22 presentation, with 12 minutes plus 1-2 minutes for questions. Recheck Canvas before submission. Required content includes the problem/approach, preliminary results and analysis, further experiments, code link and AI-use disclosure.

The student must review and understand the work, rehearse at their actual speaking rate, and confirm instructor access to the private repository. No Canvas submission, instructor message or invitation has been made by this workflow.

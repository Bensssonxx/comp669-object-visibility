# Current state

Updated 2026-10-18, America/New_York. Read this file before continuing the project.

## Completed research

The initial pilot and the user-authorized follow-up v2 are complete, with real model predictions, audited statistics and bilingual reports. This does not mean the final course project, instructor approval or submission is complete. No inference process remains active; sessions 2187 (full extension) and 69558 (independent encoder replay) finished successfully.

Repository: https://github.com/Bensssonxx/comp669-object-visibility (private). Use the working HTTPS credential helper and `GIT_TERMINAL_PROMPT=0 git push origin main`. The GitHub connector cannot access this private repository, and SSH authentication is unavailable. Do not create credentials or retry those routes. Instructor access still needs arranging before formal submission. Canvas remains read-only; no upload, email or invitation has been performed.

## Latest findings and evidence

Read `reports/EXTENSION_V2_ZH.md` first; `reports/EXTENSION_V2_EN.md` is the technical version for instructor review.

The follow-up protocol, source, samples and original classifier heads were committed as 815a33b before new predictions. Main cohort: 740 new official-test images, 20 per breed, with no IDs or image-byte hashes shared with any pilot training/validation/test sample. Auxiliary cohort: 185 unused official-trainval images with head boxes. All 740 main images have foreground-matched pairs; 159/185 auxiliary images meet fixed head-region contrast constraints. The entire official test split has zero downloaded head XMLs. No thresholds were loosened.

Both frozen L/14 encoders evaluated the same 16,361 conditions (32,722 rows total), using the original C=10 clean-trained probes, original normalization/mean patch pooling/full-frame resize, and shared gray128/black0 inputs. All original core sources and pilot results are unchanged from 0a461ed.

At 25% visible image area:

| Fill | Pattern | AIMv2 | DINOv2 |
| --- | --- | ---: | ---: |
| Gray128 | center | 87.0% | 63.1% |
| Gray128 | random | 33.6% | 69.6% |
| Black0 | center | 87.3% | 61.9% |
| Black0 | random | 30.4% | 62.2% |

At this 25% image budget, center retains 62.5% foreground on average, random 25.0%; the standard-pattern comparison still changes content distribution and does not isolate a pure position effect. All four model-difference directions persist under family-wise intervals over seven prespecified contrasts. Black fill still reduces random accuracy by 3.2 pp for AIMv2 and 7.4 pp for DINOv2. The black-minus-gray change in the model-by-pattern interaction is -2.8 pp, individual 95% CI [-6.4, 0.9]; this is not evidence that fills are equivalent.

Auxiliary head-region pairs keep foreground visibility within 3 pp while swapping head/body content. Gray-fill breed-macro accuracy is 92.4% vs 73.2% for AIMv2 (paired gap 19.2 pp [13.5,24.9]) and 82.9% vs 72.4% for DINOv2 (10.5 pp [5.8,15.1]). Black-fill gaps are 17.0 and 8.4 pp. These are content-bundle comparisons, not pure head effects or explanations of the main crossover. Head visibility is a box-intersected-foreground proxy, not precise head segmentation.

Validation: 37 tests passed; source provenance verifies 19 frozen files and all 185 auxiliary XMLs; both saved classifiers reconstruct every prediction and target probability; independent input decoding matches all 925 new images; 24 aligned conditions per encoder replay in the original pilot interpreter with zero feature difference. All cached feature norms are near one. Raw aggregates independently reproduce all 20 summary rows, seven primary contrasts and 12 paired rows. Final research figures were visually inspected. Evidence is in `results/extension_v2/*audit.json`, `report_numeric_review.json`, and `docs/EXTENSION_*REPLAY_CHECK.json`.

## Reproduce or extend

Use the full fresh-clone and saved-prediction reanalysis commands in README.md. Numeric reference: macOS arm64, Python 3.12.2, Conda Pillow 10.4.0 with libjpeg 9e. Plain pip Pillow uses another decoder and fails pixel fingerprints despite the same Pillow version. Source `scripts/env.sh` before direct Python commands on this host.

`bash scripts/run_extension.sh` validates/prepares, runs both models sequentially, audits outputs and computes statistics. `report_extension.py` generates figures and bilingual reports. Tracked small NPZ probes allow extension execution without first refitting pilot classifiers. Raw data/checkpoints/vendor code/environments/features/build files are ignored by Git. The frozen inventory in `results/extension_v2/frozen_provenance.json` checks source/sample hashes from the pre-inference commit. Never silently edit the frozen v1/v2 source/config/probes or reuse their caches for a different experiment. Use a new versioned protocol/run for new scientific settings.

The optional independent model-replay script is `scripts/replay_extension_encoder.py`, run from the original `.venv` on the GPU-enabled host. It checks 24 aligned conditions per model and all cached feature norms; it explicitly does not repeat the full experiment. Saved-prediction reanalysis recalculates statistics without raw images or upstream model weights, but relies on the stored completed-run model audit.

## Scientific interpretation and next priorities

The supported result is evaluation-condition-dependent ordering for these specific frozen encoder/probe systems, replicated on new images and two fills. Equal image area and approximately matched foreground area do not specify identical semantic content. Cross-model training data/objectives/architecture remain uncontrolled. Do not attribute the differences to prefix attention or claim first-ever foreground/background occlusion research.

The original four-pattern common-support issue at 50% visible image area remains unresolved; the follow-up targets 25% and uses separate 75%-visible square diagnostics. Auxiliary eligibility and source split differ from the main cohort; do not pool their estimates. Bootstrap units are original images within breeds, random repeats averaged within image, and all uncertainty is conditional on the fixed probes/checkpoints. Visual near duplicates and pretraining overlap are unknown. No external dataset or natural-occluder replication is complete.

Next priorities: compare alternative feature readouts/pooling with a newly fixed protocol, then consider natural occluders or another dataset. Do not infer that a lower correctness-flip rate means better robustness; both versions can be wrong. Ask the instructor whether this bounded behavior-analysis contribution addresses the feedback before treating the research scope as approved. Student review/understanding and AI disclosure remain necessary.

## Existing milestone materials

`milestone/COMP669_Object_Visibility_Milestone_v4.pptx` is the reviewed 12-slide pilot_v1 deck, with speaker notes and QA. It has not been revised to include v2 results. Preserve it as pilot evidence. If the presentation should cover the follow-up, update it explicitly using the new reports and keep old versions.

Slides due Oct 21, 2026 at 11:59 PM ET; presentation Oct 22, 12 minutes plus 1–2 minutes Q&A. These dates were checked live on Oct 18 in the original task; recheck Canvas before actual submission. Required problem/approach, preliminary results, analysis, further experiments, code link and AI-use disclosure remain relevant. No submission has occurred.

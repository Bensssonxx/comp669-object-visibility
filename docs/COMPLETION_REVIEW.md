# Initial pilot and milestone preparation review

Completed October 18, 2026. Scope: prepare reviewable research evidence and milestone materials, not final-project completion or formal submission.

| Requirement | Evidence |
| --- | --- |
| Focused motivation and contribution boundaries | DIRECTION_ZH.md, RELATED_WORK.md, PROTOCOL.md |
| Official code/checkpoint/data provenance | SOURCES.json, ../results/pilot_v1/manifest.json, ENVIRONMENT.json |
| Shared pixel interventions and annotation semantics | protocol, mask code, actual input figures, 26 passing tests |
| Real AIMv2 and DINOv2 pilot | 4,255 saved prediction rows each; integration_audit.json |
| Within-image diagnostics and uncertainty | paired_summary.csv, paired_model_differences.csv, image-level bootstrap |
| Validation-only probe selection and honest sensitivity | per-model probe selection, probe_regularization_sensitivity.csv; post-hoc supplement labeled |
| Reproducible decoded inputs | 2,035 canonical RGB/trimap hashes; REFERENCE_REPLAY_CHECK.json |
| Executable setup and full pipeline | PIPELINE_REPLAY_CHECK.json; successful reference setup and cached-feature replay |
| Preliminary results, analysis and further experiments | PILOT_REPORT_ZH.md, PILOT_REPORT_EN.md; 12-slide v4 PPTX |
| Real figures, speaker notes, code link and AI disclosure | milestone assets, SPEAKER_NOTES_EN.md, last slide, AI_USE.md |
| Presentation review | PRESENTATION_VALIDATION.json; all previews inspected, representative LibreOffice cross-check; no PowerPoint execution claim |

The final deck is `../milestone/COMP669_Object_Visibility_Milestone_v4.pptx`. Earlier candidates are retained locally in ignored build folders. The private repository URL is https://github.com/Bensssonxx/comp669-object-visibility; instructor access still needs arranging before formal submission. No Canvas upload, email or invitation was performed.

Limitations remain scientific work for the next stage: small test set, single dataset/fill color, incomplete common coverage support, remaining semantic-part/background differences, probe/pooling sensitivity and unknown pretraining overlap. No causal prefix-attention conclusion or paper-level novelty claim is supported. The student should understand, review and rehearse the material before presenting it.

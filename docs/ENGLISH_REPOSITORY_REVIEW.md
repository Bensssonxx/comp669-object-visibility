# English-only repository update

October 21, 2026. Scope: the current GitHub file tree, reader orientation and report-generation language. Existing Git history remains intact.

## Changes

- Preserve study translations and pre-edit authoring files outside the repository under `../local-study-notes/2026-10-21-before-english-only/`.
- Remove translated report files from the current tree and replace the direction/milestone indexes with English versions.
- Make the two report generators and v5 slide-data preparation English-only.
- Add `CODE_GUIDE.md`, a README code map and a report index.
- Publish the already-created English v5 deck, notes, questions, timing and slide-data evidence.

## Verification

- All 37 tests passed in the current cleanup run. The installed validation packages were Python 3.12.2, NumPy 1.26.4, pandas 2.3.2, Matplotlib 3.10.5 and Pillow 10.4.0.
- Both English report templates remain unchanged in their parsed source structure. Both modified generators regenerated the English reports byte-identically. The real-output report check reused saved tables and skipped figure redrawing; it did not run encoders or recompute statistics.
- All saved research-output files included in the pre-edit inventory remain byte-identical. All 19 files in the frozen follow-up inventory still match their expected hashes.
- The v5 presentation's data/notes checks pass. Its PPTX bytes are unchanged by this cleanup.
- The repository language check scans current publishable text, decoded JSON strings and PPTX XML. It excludes ignored/local files, does not rewrite past commits and does not perform image OCR.
- Relative Markdown links resolve locally. Python source parses and the v5 JavaScript builder passes syntax checking.

The reference environment in the project folder contained some cloud-offloaded dependency files whose reads stalled. Validation used the already-installed base scientific packages and the existing pytest package, without installing dependencies or modifying the experimental environment. The scientific source, model weights and experiment outputs were not changed to address this local environment issue.

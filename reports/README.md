# Research reports

Start with [Follow-up v2](EXTENSION_V2_EN.md), which contains the latest completed experiments: new official-test images, gray/black fill sensitivity, and separate auxiliary head-region diagnostics.

[Pilot v1](PILOT_REPORT_EN.md) preserves the original smaller experiment and its labeled post-hoc classifier sensitivity. Its future-work section reflects that earlier stage; the follow-up answers some of those questions without replacing the pilot results.

Both reports use saved executable results. The report generators are `scripts/write_reports.py` and `scripts/report_extension.py`. They now write English reports only. Model inference, statistics and presentation authoring are separate stages; see the [code guide](../docs/CODE_GUIDE.md).

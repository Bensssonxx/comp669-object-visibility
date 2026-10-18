#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
.venv/bin/python -m pytest -q
.venv/bin/python scripts/download_assets.py
.venv/bin/python scripts/import_pet_mirror.py
.venv/bin/python -m occlusion_visibility.experiment prepare
.venv/bin/python scripts/preview_inputs.py
.venv/bin/python -m occlusion_visibility.experiment run --model aimv2
.venv/bin/python -m occlusion_visibility.experiment run --model dinov2
.venv/bin/python scripts/analyze.py --run pilot_v1
.venv/bin/python scripts/audit_run.py --require-predictions
.venv/bin/python scripts/qualitative_cases.py
.venv/bin/python scripts/write_reports.py

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/env.sh
PROJECT_PYTHON="${PROJECT_PYTHON:-.reference-conda/bin/python}"
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
"$PROJECT_PYTHON" -m pytest -q
"$PROJECT_PYTHON" scripts/download_assets.py
"$PROJECT_PYTHON" scripts/import_pet_mirror.py
"$PROJECT_PYTHON" -m occlusion_visibility.experiment prepare
"$PROJECT_PYTHON" scripts/verify_preprocessing.py
"$PROJECT_PYTHON" scripts/preview_inputs.py
"$PROJECT_PYTHON" -m occlusion_visibility.experiment run --model aimv2
"$PROJECT_PYTHON" -m occlusion_visibility.experiment run --model dinov2
"$PROJECT_PYTHON" scripts/analyze.py --run pilot_v1
"$PROJECT_PYTHON" scripts/audit_run.py --require-predictions
"$PROJECT_PYTHON" scripts/qualitative_cases.py
"$PROJECT_PYTHON" scripts/write_reports.py

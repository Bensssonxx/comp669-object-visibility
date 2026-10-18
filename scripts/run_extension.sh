#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/env.sh
PROJECT_PYTHON="${PROJECT_PYTHON:-.reference-conda/bin/python}"
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
"$PROJECT_PYTHON" -m pytest -q
"$PROJECT_PYTHON" scripts/extension_v2.py prepare
"$PROJECT_PYTHON" scripts/extension_v2.py audit
"$PROJECT_PYTHON" scripts/extension_v2.py run --model aimv2
"$PROJECT_PYTHON" scripts/extension_v2.py run --model dinov2
"$PROJECT_PYTHON" scripts/extension_v2.py audit --require-predictions
"$PROJECT_PYTHON" scripts/analyze_extension.py

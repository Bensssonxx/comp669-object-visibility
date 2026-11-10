#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/env.sh
PROJECT_PYTHON="${PROJECT_PYTHON:-.reference-conda/bin/python}"
export PYTHONUNBUFFERED=1 OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4
"$PROJECT_PYTHON" tests/test_completion_analysis.py
"$PROJECT_PYTHON" tests/test_completion_conditions.py
for cohort in primary head; do
  "$PROJECT_PYTHON" scripts/complete_occlusion.py prepare --cohort "$cohort"
  for model in aimv2 dinov2; do
    "$PROJECT_PYTHON" scripts/complete_occlusion.py run --cohort "$cohort" --model "$model"
  done
  "$PROJECT_PYTHON" scripts/complete_occlusion.py audit --cohort "$cohort"
done
"$PROJECT_PYTHON" scripts/analyze_completion.py
"$PROJECT_PYTHON" scripts/completion_examples.py
"$PROJECT_PYTHON" scripts/verify_completion.py
# The November 10 control uses the audited source runs above.
"$PROJECT_PYTHON" scripts/final_sensitivity.py
"$PROJECT_PYTHON" scripts/patch_relocation.py prepare
for model in aimv2 dinov2; do
  "$PROJECT_PYTHON" scripts/patch_relocation.py "$model"
done
"$PROJECT_PYTHON" scripts/patch_relocation.py analyze
"$PROJECT_PYTHON" scripts/check_final_results.py
"$PROJECT_PYTHON" scripts/report_completion.py

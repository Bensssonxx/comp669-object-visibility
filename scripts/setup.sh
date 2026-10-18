#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
mkdir -p vendor models data/raw
if [[ ! -d vendor/ml-aim/.git ]]; then
  git clone https://github.com/apple-aiml-research/ml-aim.git vendor/ml-aim
fi
git -C vendor/ml-aim checkout a018ae3208ef3289cae9aa024947e0bb3b71d3ff
if [[ ! -d vendor/dinov2/.git ]]; then
  git clone https://github.com/facebookresearch/dinov2.git vendor/dinov2
fi
git -C vendor/dinov2 checkout 7764ea0f912e53c92e82eb78a2a1631e92725fc8
.venv/bin/python -m pip install --no-deps -e vendor/ml-aim/aim-v1 -e vendor/ml-aim/aim-v2 -e .

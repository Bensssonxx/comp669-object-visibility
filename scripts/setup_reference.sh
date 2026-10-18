#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PROJECT_CONDA_BIN="${PROJECT_CONDA_BIN:-conda}"
if [[ ! -x .reference-conda/bin/python ]]; then
  CONDA_PKGS_DIRS="$PWD/.cache/conda-pkgs" "$PROJECT_CONDA_BIN" env create --prefix "$PWD/.reference-conda" --file environment.reference.yml --yes
fi
.reference-conda/bin/python -m pip install -r requirements.txt
mkdir -p vendor models data/raw
if [[ ! -d vendor/ml-aim/.git ]]; then git clone https://github.com/apple-aiml-research/ml-aim.git vendor/ml-aim; fi
git -C vendor/ml-aim checkout a018ae3208ef3289cae9aa024947e0bb3b71d3ff
if [[ ! -d vendor/dinov2/.git ]]; then git clone https://github.com/facebookresearch/dinov2.git vendor/dinov2; fi
git -C vendor/dinov2 checkout 7764ea0f912e53c92e82eb78a2a1631e92725fc8
.reference-conda/bin/python -m pip install --no-deps -e vendor/ml-aim/aim-v1 -e vendor/ml-aim/aim-v2 -e .

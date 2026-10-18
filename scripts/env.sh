#!/usr/bin/env bash
# Explicit paths also work on hosts that suppress editable-install .pth files.
PROJECT_ROOT="$PWD"
if [ ! -d "$PROJECT_ROOT/src/occlusion_visibility" ]; then
  printf '%s\n' 'Source scripts/env.sh from the project root.' >&2
  return 1 2>/dev/null || exit 1
fi
export PYTHONPATH="$PROJECT_ROOT/src:$PROJECT_ROOT/vendor/ml-aim/aim-v1:$PROJECT_ROOT/vendor/ml-aim/aim-v2${PYTHONPATH:+:$PYTHONPATH}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-$PROJECT_ROOT/.cache/matplotlib}"
mkdir -p "$MPLCONFIGDIR"

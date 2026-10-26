#!/usr/bin/env bash
# Run each applicable native/tool suite once on an already configured host build.
set -euo pipefail
checkpoint_build=${SMIL_BUILD_DIR:-build/smil}
checkpoint_cmake=${SMIL_CMAKE:-cmake}
checkpoint_ctest=${SMIL_CTEST:-ctest}
checkpoint_uv=${SMIL_UV:-uv}
"$checkpoint_cmake" --build "$checkpoint_build"
"$checkpoint_ctest" --test-dir "$checkpoint_build" -E '^tools_' --output-on-failure
"$checkpoint_uv" run --locked python -m unittest discover -s tools/tests
"$checkpoint_uv" run --locked python scripts/audit_evidence.py --inventory

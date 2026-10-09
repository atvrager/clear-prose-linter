#!/usr/bin/env bash
set -euo pipefail

LINT="$1"
shift
TARGETS=("$@")

"$LINT" "${TARGETS[@]}"

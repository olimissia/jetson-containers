#!/usr/bin/env bash
# launcher for jetson_containers/build.py (see docs/build.md)
ROOT="$(dirname "$(readlink -f "$0")")"
PYTHONPATH="$PYTHONPATH:$ROOT"

echo "$ROOT"
echo "$PYTHONPATH"
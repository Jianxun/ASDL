#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
out_dir="$script_dir"

# Prefer project venv CLI if available
if [[ -x "$repo_root/venv/bin/asdlc" ]]; then
  "$repo_root/venv/bin/asdlc" schema --out "$out_dir"
elif command -v asdlc >/dev/null 2>&1; then
  asdlc schema --out "$out_dir"
else
  # Fallback: run via Python module with src on PYTHONPATH
  if [[ -x "$repo_root/venv/bin/python" ]]; then
    PYTHON_BIN="$repo_root/venv/bin/python"
  else
    PYTHON_BIN="python3"
  fi
  export PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}"
  "$PYTHON_BIN" -m asdl.cli schema --out "$out_dir"
fi

echo "Wrote: $out_dir/schema.json"
echo "Wrote: $out_dir/schema.txt"

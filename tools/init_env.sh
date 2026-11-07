#!/usr/bin/env bash
# Creates directories and .env only. Dependency installation remains explicit.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$ROOT/fonts" "$ROOT/modules"
if [[ ! -e "$ROOT/.env" ]]; then cp "$ROOT/.env.example" "$ROOT/.env"; fi
printf '%s\n' 'Local directories and .env ready. See README.md for manual dependency installation.'

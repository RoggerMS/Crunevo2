#!/bin/bash
set -euo pipefail

if [[ ! -f .env ]]; then
  echo ".env file not found" >&2
  exit 1
fi

fly secrets set $(grep -v '^#' .env | xargs) "$@"

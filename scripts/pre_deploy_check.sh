#!/bin/bash
set -euo pipefail

APP_URL="${APP_URL:-https://crunevo2.fly.dev}"
HEALTH_PATH="${HEALTH_PATH:-/healthz}"

echo "Checking health endpoint..."
curl -fsS "${APP_URL}${HEALTH_PATH}" >/dev/null

CRITICAL_PATHS=("/" "/auth/login")
for path in "${CRITICAL_PATHS[@]}"; do
  echo "Checking ${path} over HTTPS..."
  curl -fsS -o /dev/null "https://${APP_URL#https://}${path}"
done

echo "Listing Fly checks..."
fly checks list

echo "Verify all checks are passing above."

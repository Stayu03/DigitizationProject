#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/Users/stang/Digitization Project/Digi_WebApp/DIgitizationProject"
cd "$PROJECT_DIR"

APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-5001}"
APP_WORKERS="${APP_WORKERS:-2}"
APP_TIMEOUT="${APP_TIMEOUT:-120}"

exec "$PROJECT_DIR/.venv/bin/gunicorn" \
  --workers "$APP_WORKERS" \
  --bind "$APP_HOST:$APP_PORT" \
  --timeout "$APP_TIMEOUT" \
  --access-logfile - \
  --error-logfile - \
  webapp:app

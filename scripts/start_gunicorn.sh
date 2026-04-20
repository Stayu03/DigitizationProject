#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${PORT:-${APP_PORT:-5001}}"
APP_WORKERS="${APP_WORKERS:-2}"
APP_TIMEOUT="${APP_TIMEOUT:-120}"

if [[ -x "$PROJECT_DIR/.venv/bin/gunicorn" ]]; then
  GUNICORN_BIN="$PROJECT_DIR/.venv/bin/gunicorn"
else
  GUNICORN_BIN="gunicorn"
fi

exec "$GUNICORN_BIN" \
  --workers "$APP_WORKERS" \
  --bind "$APP_HOST:$APP_PORT" \
  --timeout "$APP_TIMEOUT" \
  --access-logfile - \
  --error-logfile - \
  webapp:app

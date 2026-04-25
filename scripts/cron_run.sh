#!/usr/bin/env bash
# scripts/cron_run.sh — cron wrapper for the daily regime-detection pipeline.
# Contract: activate venv, run pipeline, log exit code, propagate exit code.
set -u  # undefined vars are errors; DO NOT set -e (we want to capture non-zero exit)

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"
CRON_LOG="$LOG_DIR/cron_run.log"

# Activate venv if present (support both Windows Git-Bash and Unix layouts)
if [ -f "$PROJECT_ROOT/.venv/Scripts/activate" ]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.venv/Scripts/activate"
elif [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] cron_run starting" >> "$CRON_LOG"
python scripts/run.py
RC=$?
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] cron_run exit code: $RC" >> "$CRON_LOG"
exit $RC

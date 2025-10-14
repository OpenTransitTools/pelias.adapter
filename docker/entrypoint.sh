#!/bin/bash
set -euo pipefail

# Default values
PORT=${PORT:-8000}
ENVIRONMENT=${ENVIRONMENT:-prod}

export PYTHONPATH="/pelias_adapter:${PYTHONPATH:-}"


# Configure workers and log level based on environment
case "$ENVIRONMENT" in
  dev)
    WORKERS=1
    LOG_LEVEL=debug
    echo "🧩 Environment: DEVELOPMENT"
    ;;
  stage)
    WORKERS=2
    LOG_LEVEL=info
    echo "🧪 Environment: STAGING"
    ;;
  prod|*)
    CORES=$(nproc)
    WORKERS=$((CORES * 2 + 1))
    LOG_LEVEL=warning
    echo "🚀 Environment: PRODUCTION (Detected ${CORES} cores → ${WORKERS} workers)"
    ;;
esac

# Print runtime info
echo "Starting FastAPI app with the following settings:"
echo "  PORT:       ${PORT}"
echo "  WORKERS:    ${WORKERS}"
echo "  LOG_LEVEL:  ${LOG_LEVEL}"
echo "--------------------------------------------"

# Launch Gunicorn with Uvicorn workers
exec gunicorn main:app \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:${PORT} \
  --workers "${WORKERS}" \
  --timeout 60 \
  --log-level "${LOG_LEVEL}" \
  --access-logfile - \
  --error-logfile -

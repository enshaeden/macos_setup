#!/bin/zsh
# Unified logging for macOS Setup Suite

# Default log file (will be overridden by config if needed)
LOG_DIR="${HOME}/Library/Logs/mac-setup"
LOG_FILE="${LOG_DIR}/setup.log"

mkdir -p "${LOG_DIR}"

log_info() {
  local msg="$1"
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  echo "==> ${msg}"
  echo "[${timestamp}] [INFO] ${msg}" >> "${LOG_FILE}"
}

log_error() {
  local msg="$1"
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  echo "!! ERROR: ${msg}" >&2
  echo "[${timestamp}] [ERROR] ${msg}" >> "${LOG_FILE}"
}

log_warn() {
  local msg="$1"
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  echo "?? WARNING: ${msg}"
  echo "[${timestamp}] [WARN] ${msg}" >> "${LOG_FILE}"
}

log_success() {
  local msg="$1"
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  echo "OK: ${msg}"
  echo "[${timestamp}] [SUCCESS] ${msg}" >> "${LOG_FILE}"
}

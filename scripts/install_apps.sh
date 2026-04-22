#!/bin/zsh
set -euo pipefail

# This script handles any manual app installations not covered by Homebrew.
# Currently, core apps (VS Code, GitHub Desktop) are handled via Brewfile casks.

source "${SCRIPT_DIR}/scripts/lib/logger.sh"

log_info "No manual app installations required (managed by Homebrew)."

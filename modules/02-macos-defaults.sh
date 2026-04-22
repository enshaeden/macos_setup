#!/bin/zsh
source "${SCRIPT_DIR}/scripts/lib/logger.sh"
source "${SCRIPT_DIR}/scripts/lib/state_manager.sh"

log_info "Applying macOS performance tweaks..."
# We don't mark this as 'completed' in a way that skips it, as user might want to re-apply 
# if they've changed config.yaml. But we can skip if no changes are needed.

zsh "${SCRIPT_DIR}/scripts/macos_defaults.sh"

log_success "macOS defaults module complete."

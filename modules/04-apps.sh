#!/bin/zsh
source "${SCRIPT_DIR}/scripts/lib/logger.sh"
source "${SCRIPT_DIR}/scripts/lib/state_manager.sh"

if is_completed "apps_manual"; then
  log_info "Manual apps already installed."
  return 0
fi

log_info "Installing applications..."
zsh "${SCRIPT_DIR}/scripts/install_apps.sh"

mark_completed "apps_manual"
log_success "Apps module complete."

#!/bin/zsh
source "${SCRIPT_DIR}/scripts/lib/logger.sh"
source "${SCRIPT_DIR}/scripts/lib/state_manager.sh"

if is_completed "python_env"; then
  log_info "Python environment already completed."
  return 0
fi

log_info "Installing latest Python via uv..."
uv python install

log_info "Setting up LaunchAgents..."
zsh "${SCRIPT_DIR}/scripts/setup_agents.sh"

mark_completed "python_env"
log_success "Python module complete."

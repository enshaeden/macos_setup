#!/bin/zsh
source "${SCRIPT_DIR}/scripts/lib/logger.sh"
source "${SCRIPT_DIR}/scripts/lib/state_manager.sh"

if is_completed "python_env"; then
  log_info "Python environment already completed."
  return 0
fi

log_info "Installing latest Python via uv..."
uv python install

log_info "Ensuring PyYAML available to system python3..."
if command -v python3 >/dev/null 2>&1; then
  python3 -m pip install --user PyYAML >/dev/null 2>&1 || true
else
  log_warn "python3 not found; skipping PyYAML install"
fi

log_info "Setting up LaunchAgents..."
zsh "${SCRIPT_DIR}/scripts/setup_agents.sh"

mark_completed "python_env"
log_success "Python module complete."

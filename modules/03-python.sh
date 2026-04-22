#!/bin/zsh
source "${SCRIPT_DIR}/scripts/lib/logger.sh"
source "${SCRIPT_DIR}/scripts/lib/state_manager.sh"

if is_completed "python_env"; then
  log_info "Python environment already completed."
  return 0
fi

log_info "Setting up Python environment via pyenv..."
export PYENV_ROOT="${HOME}/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

local target_version=$(pyenv install --list | sed 's/^[[:space:]]*//' | grep -E '^3\.[0-9]+\.[0-9]+$' | tail -1)
log_info "Installing Python ${target_version}..."
pyenv install -s "${target_version}"
pyenv global "${target_version}"

log_info "Installing Python dependencies..."
pip3 install PyYAML

# Setup background agents that depend on Python
log_info "Setting up LaunchAgents..."
zsh "${SCRIPT_DIR}/scripts/setup_agents.sh" # I'll extract this logic to a script

mark_completed "python_env"
log_success "Python module complete."

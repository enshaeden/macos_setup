#!/bin/zsh
set -euo pipefail

# --- Guards ---
if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script only supports macOS."
  exit 1
fi

if [[ -z "${ZSH_VERSION:-}" ]]; then
  echo "Error: This script must be run with zsh."
  exit 1
fi

# --- Environment ---
export SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/scripts/lib/logger.sh"
source "${SCRIPT_DIR}/scripts/lib/state_manager.sh"

# --- Keep-alive sudo ---
sudo -v
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &
SUDO_KEEPALIVE_PID="$!"
trap 'kill "${SUDO_KEEPALIVE_PID}" >/dev/null 2>&1 || true' EXIT

main() {
  log_info "Starting macOS Setup Orchestrator..."
  
  # Ensure base requirements for modules (like yq/jq) are met
  source "${SCRIPT_DIR}/modules/00-homebrew.sh"

  # Load and run modules
  local modules=("05-security.sh" "01-zsh.sh" "02-macos-defaults.sh" "03-python.sh" "04-apps.sh" "06-diag-tools.sh")
  local current_module_path=""
  local current_feature_name=""
  local is_enabled=""
  
  for module in "${modules[@]}"; do
    current_module_path="${SCRIPT_DIR}/modules/${module}"
    current_feature_name=$(basename "${module}" .sh | sed 's/^[0-9]*-//' | tr '-' '_')
    
    # Check if feature is enabled in config.yaml
    if command -v yq >/dev/null 2>&1; then
      is_enabled=$(yq -r ".features.${current_feature_name}" "${SCRIPT_DIR}/config.yaml")
      if [[ "${is_enabled}" == "false" ]]; then
        log_warn "Feature '${current_feature_name}' is disabled in config. Skipping."
        continue
      fi
    fi

    if [[ -f "${current_module_path}" ]]; then
      log_info "Running module: ${module}..."
      source "${current_module_path}"
    else
      log_error "Module not found: ${current_module_path}"
    fi
  done

  log_success "All setup modules completed successfully!"
  log_info "Please restart your terminal or run 'source ~/.zshrc'"
}

main "$@"

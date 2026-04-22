#!/bin/zsh
source "${SCRIPT_DIR}/scripts/lib/logger.sh"
source "${SCRIPT_DIR}/scripts/lib/state_manager.sh"

if is_completed "security"; then
  log_info "Security module already completed."
  return 0
fi

log_info "Enabling Touch ID for sudo..."
if [[ -f /etc/pam.d/sudo_local.template ]]; then
  if [[ ! -f /etc/pam.d/sudo_local ]]; then
    sudo cp /etc/pam.d/sudo_local.template /etc/pam.d/sudo_local
  fi
  sudo sed -i '' 's/^#\(auth[[:space:]]*sufficient[[:space:]]*pam_tid\.so\)/\1/' /etc/pam.d/sudo_local
fi

mark_completed "security"
log_success "Security module complete."

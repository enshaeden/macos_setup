#!/bin/zsh
source "${SCRIPT_DIR}/scripts/lib/logger.sh"
source "${SCRIPT_DIR}/scripts/lib/state_manager.sh"

if is_completed "zsh_setup"; then
  log_info "Zsh setup module already completed."
  return 0
fi

OHMYZSH_DIR="${HOME}/.oh-my-zsh"
if [[ ! -d "${OHMYZSH_DIR}" ]]; then
  log_info "Installing Oh My Zsh..."
  # KEEP_ZSHRC=yes ensures we don't overwrite if one exists, but we'll manage it anyway
  RUNZSH=no CHSH=no KEEP_ZSHRC=yes sh -c "$(curl -fsSL https://install.ohmyz.sh)" "" --unattended
fi

log_info "Configuring Zsh custom aliases..."
ZSH_CUSTOM_DIR="${OHMYZSH_DIR}/custom"
mkdir -p "${ZSH_CUSTOM_DIR}"
cp "${SCRIPT_DIR}/dotfiles/custom_aliases.zsh" "${ZSH_CUSTOM_DIR}/custom_aliases.zsh"

log_info "Applying managed .zshrc configuration..."
if [[ -f "${HOME}/.zshrc" ]]; then
  log_info "Backing up existing .zshrc to .zshrc.backup"
  cp "${HOME}/.zshrc" "${HOME}/.zshrc.backup"
fi
cp "${SCRIPT_DIR}/dotfiles/.zshrc" "${HOME}/.zshrc"

mark_completed "zsh_setup"
log_success "Zsh module complete."

log_info "Sourcing updated .zshrc..."
source "${HOME}/.zshrc" 2>/dev/null || true

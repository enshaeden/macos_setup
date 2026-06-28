#!/bin/zsh
# macOS system defaults for performance and productivity

source "${SCRIPT_DIR}/scripts/lib/logger.sh"

# 1. Dock Speed
if [[ "$(yq -r '.ui_tweaks.dock_speed' "${SCRIPT_DIR}/config.yaml")" == "true" ]]; then
  log_info "Optimizing Dock animations..."
  defaults write com.apple.dock autohide-delay -float 0
  defaults write com.apple.dock autohide-time-modifier -float 0
  defaults write com.apple.dock launchanim -bool false
fi

# 2. Finder Animations
if [[ "$(yq -r '.ui_tweaks.finder_animations' "${SCRIPT_DIR}/config.yaml")" == "false" ]]; then
  log_info "Disabling Finder animations..."
  defaults write com.apple.finder DisableAllAnimations -bool true
fi

# 3. Window animations
log_info "Disabling system-wide window animations..."
defaults write NSGlobalDomain NSAutomaticWindowAnimationsEnabled -bool false

# 4. Keyboard repeat rate
key_repeat="$(yq -r '.ui_tweaks.keyboard_repeat.key_repeat // 2' "${SCRIPT_DIR}/config.yaml")"
initial_key_repeat="$(yq -r '.ui_tweaks.keyboard_repeat.initial_key_repeat // 12' "${SCRIPT_DIR}/config.yaml")"

log_info "Setting keyboard repeat rate..."
defaults write NSGlobalDomain KeyRepeat -int "${key_repeat}"
defaults write NSGlobalDomain InitialKeyRepeat -int "${initial_key_repeat}"

# Restart affected apps
for app in "Dock" "Finder" "SystemUIServer"; do
  killall "${app}" >/dev/null 2>&1 || true
done

log_info "macOS defaults updated."

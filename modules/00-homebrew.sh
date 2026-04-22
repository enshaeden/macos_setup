#!/bin/zsh
source "${SCRIPT_DIR}/scripts/lib/logger.sh"
source "${SCRIPT_DIR}/scripts/lib/state_manager.sh"

if is_completed "homebrew"; then
  log_info "Homebrew module already completed."
  return 0
fi

log_info "Ensuring Homebrew is installed..."
BREW_BIN="/opt/homebrew/bin/brew"
if [[ ! -x "${BREW_BIN}" ]]; then
  log_info "Installing Homebrew..."
  NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
eval "$("${BREW_BIN}" shellenv)"

log_info "Bootstrapping JSON/YAML tools (jq, yq)..."
"${BREW_BIN}" install jq yq

log_info "Installing dependencies from Brewfile..."
mkdir -p "${HOME}/Applications"
# Filtering Brewfile logic
local temp_brewfile=$(mktemp)
local force_install=($(yq -r '.brew_force_install[]' "${SCRIPT_DIR}/config.yaml"))

while IFS= read -r line; do
  if [[ "$line" =~ ^brew\ \"([^\"]+)\" ]]; then
    local formula="${match[1]}"
    local force=0
    for f in "${force_install[@]}"; do
      if [[ "$f" == "$formula" ]]; then force=1; break; fi
    done

    if [[ $force -eq 1 ]]; then
      echo "$line" >> "$temp_brewfile"
    elif command -v "$formula" >/dev/null 2>&1 && [[ "$(command -v "$formula")" != "/opt/homebrew"* ]]; then
      log_info "Skipping $formula (found system version)"
    else
      echo "$line" >> "$temp_brewfile"
    fi
  else
    echo "$line" >> "$temp_brewfile"
  fi
done < "${SCRIPT_DIR}/Brewfile"

"${BREW_BIN}" bundle --file="$temp_brewfile"
rm -f "$temp_brewfile"

mark_completed "homebrew"
log_success "Homebrew module complete."

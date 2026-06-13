#!/bin/zsh
source "${SCRIPT_DIR}/scripts/lib/logger.sh"
source "${SCRIPT_DIR}/scripts/lib/state_manager.sh"

if is_completed "tools"; then
  log_info "Tools module already completed."
  return 0
fi

ARCH="$(uname -m)"
BIN_DIR="${HOME}/.local/bin"
mkdir -p "${BIN_DIR}"

# uv — Python toolchain manager
if ! command -v uv >/dev/null 2>&1; then
  log_info "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
else
  log_info "uv already installed."
fi

# volta — Node.js version manager
if ! command -v volta >/dev/null 2>&1; then
  log_info "Installing volta..."
  curl https://get.volta.sh | bash -s -- --skip-setup
  export VOLTA_HOME="${HOME}/.volta"
  export PATH="${VOLTA_HOME}/bin:${PATH}"
  volta install node
else
  log_info "volta already installed."
fi

# jq — JSON processor (standalone binary)
if ! command -v jq >/dev/null 2>&1; then
  log_info "Installing jq..."
  if [[ "${ARCH}" == "arm64" ]]; then
    JQ_URL="https://github.com/jqlang/jq/releases/latest/download/jq-macos-arm64"
  else
    JQ_URL="https://github.com/jqlang/jq/releases/latest/download/jq-macos-amd64"
  fi
  curl -fsSL "${JQ_URL}" -o "${BIN_DIR}/jq"
  chmod +x "${BIN_DIR}/jq"
else
  log_info "jq already installed."
fi

# yq — YAML processor (standalone binary)
if ! command -v yq >/dev/null 2>&1; then
  log_info "Installing yq..."
  if [[ "${ARCH}" == "arm64" ]]; then
    YQ_URL="https://github.com/mikefarah/yq/releases/latest/download/yq_darwin_arm64"
  else
    YQ_URL="https://github.com/mikefarah/yq/releases/latest/download/yq_darwin_amd64"
  fi
  curl -fsSL "${YQ_URL}" -o "${BIN_DIR}/yq"
  chmod +x "${BIN_DIR}/yq"
else
  log_info "yq already installed."
fi

export PATH="${BIN_DIR}:${PATH}"

mark_completed "tools"
log_success "Tools module complete."

#!/bin/zsh
set -euo pipefail

source "${SCRIPT_DIR}/scripts/lib/logger.sh"

APPS_DIR="${HOME}/Applications"
mkdir -p "${APPS_DIR}"

install_zip_app() {
  local name="$1"
  local url="$2"
  local tmp_zip
  tmp_zip="$(mktemp /tmp/${name}.XXXXXX.zip)"

  log_info "Downloading ${name}..."
  curl -fsSL "${url}" -o "${tmp_zip}"

  log_info "Installing ${name} to ~/Applications..."
  unzip -q -o "${tmp_zip}" -d "${APPS_DIR}"
  rm -f "${tmp_zip}"
  log_success "${name} installed."
}

vscode_url="$(yq -r '.app_urls.vscode' "${SCRIPT_DIR}/config.yaml")"
github_url="$(yq -r '.app_urls.github_desktop' "${SCRIPT_DIR}/config.yaml")"

[[ -d "${APPS_DIR}/Visual Studio Code.app" ]] \
  || install_zip_app "Visual Studio Code" "${vscode_url}"

[[ -d "${APPS_DIR}/GitHub Desktop.app" ]] \
  || install_zip_app "GitHub Desktop" "${github_url}"

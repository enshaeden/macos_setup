#!/bin/zsh
source "${SCRIPT_DIR}/scripts/lib/logger.sh"
source "${SCRIPT_DIR}/scripts/lib/state_manager.sh"

if is_completed "diag_tools"; then
  log_info "Diagnostic tools already installed."
  return 0
fi

log_info "Installing Network Diagnostic Tools..."
DIAG_TOOLS_DIR="${HOME}/Diagnostic Tools"
mkdir -p "${DIAG_TOOLS_DIR}/Network"
cp "${SCRIPT_DIR}/scripts/network_troubleshooter.py" "${DIAG_TOOLS_DIR}/Network/"

cat > "${DIAG_TOOLS_DIR}/run_troubleshooter.sh" <<EOF
#!/bin/bash
set -euo pipefail
uv_bin="\$(command -v uv 2>/dev/null || true)"
if [[ -z "\${uv_bin}" ]]; then
  echo "Error: uv is not installed or not on PATH."
  exit 1
fi
"\${uv_bin}" run "${DIAG_TOOLS_DIR}/Network/network_troubleshooter.py"
read -n 1 -s -r -p "Press any key to close..."
EOF
chmod +x "${DIAG_TOOLS_DIR}/run_troubleshooter.sh"

mark_completed "diag_tools"
log_success "Diagnostic tools module complete."

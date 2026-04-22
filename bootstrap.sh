#!/bin/bash
# Bootstrap script for macOS setup
# This script is designed to be run as a one-liner:
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/youruser/yourrepo/main/bootstrap.sh)"

set -euo pipefail

# --- Configuration ---
REPO_URL="https://github.com/youruser/yourrepo.git" # TODO: Update with your actual repository URL
TARGET_DIR="${HOME}/.mac-setup"

# --- Setup ---
log() {
  echo "==> $1"
}

cleanup() {
  local exit_code=$?
  if [ $exit_code -ne 0 ]; then
    log "An error occurred. Cleaning up..."
    # Optional: remove TARGET_DIR if it's a fresh, failed clone
  fi
}
trap cleanup EXIT

# 1. Xcode Command Line Tools
if ! xcode-select -p >/dev/null 2>&1; then
  log "Installing Xcode Command Line Tools..."
  xcode-select --install
  log "Please wait for the installation to complete, then press any key to continue..."
  read -n 1 -s -r
else
  log "Xcode Command Line Tools already installed."
fi

# 2. Git Check
if ! command -v git >/dev/null 2>&1; then
  log "Git not found. Installing via Homebrew..."
  # If brew isn't there, we'll install it next. This is a bit of a chicken-and-egg, 
  # but xcode-select usually provides a shim for git.
fi

# 3. Homebrew
if ! command -v brew >/dev/null 2>&1; then
  log "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
else
  log "Homebrew already installed."
fi

# 4. Clone Repository
if [[ "${REPO_URL}" == *"youruser"* ]]; then
  log "WARNING: REPO_URL is still set to placeholder. Attempting to use current directory if applicable..."
  if [ ! -f "macos_setup.sh" ]; then
    echo "ERROR: Please update the REPO_URL in bootstrap.sh."
    exit 1
  fi
  TARGET_DIR="$(pwd)"
else
  if [[ -d "${TARGET_DIR}" ]]; then
    log "Updating setup repository..."
    cd "${TARGET_DIR}"
    git pull
  else
    log "Cloning setup repository..."
    git clone "${REPO_URL}" "${TARGET_DIR}"
    cd "${TARGET_DIR}"
  fi
fi

# 5. Run Orchestrator
log "Starting the orchestrator..."
chmod +x macos_setup.sh
./macos_setup.sh

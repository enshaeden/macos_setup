# Managed .zshrc for macOS Setup
# This file is managed by the macos_setup tool.

# Path to your oh-my-zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Set name of the theme to load
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="robbyrussell"

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
plugins=(git python node docker brew)

# Initialize Oh My Zsh
source "$ZSH/oh-my-zsh.sh"

# --- User Customizations ---

# Preferred editor
export EDITOR='nano'

# Source custom aliases if they exist
if [[ -f "$HOME/.oh-my-zsh/custom/custom_aliases.zsh" ]]; then
    source "$HOME/.oh-my-zsh/custom/custom_aliases.zsh"
fi

# pyenv initialization
if command -v pyenv >/dev/null 2>&1; then
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
fi

# Load Homebrew shellenv if brew is in the standard Apple Silicon path
if [[ -f /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

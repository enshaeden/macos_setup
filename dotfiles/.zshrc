# Managed .zshrc for macOS Setup
# This file is managed by the macos_setup tool.

# Path to your oh-my-zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Set name of the theme to load
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="duellj"

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
plugins=(git node docker)

# Initialize Oh My Zsh
source "$ZSH/oh-my-zsh.sh"

# --- User Customizations ---

# Preferred editor
export EDITOR='nano'

# Source custom aliases if they exist
if [[ -f "$HOME/.oh-my-zsh/custom/custom_aliases.zsh" ]]; then
    source "$HOME/.oh-my-zsh/custom/custom_aliases.zsh"
fi

# uv — Python toolchain
export PATH="$HOME/.local/bin:$PATH"

# volta — Node.js version manager
export VOLTA_HOME="$HOME/.volta"
export PATH="$VOLTA_HOME/bin:$PATH"

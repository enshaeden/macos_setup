# Personal Aliases and Functions
# This file is meant to be placed in ~/.oh-my-zsh/custom/

# Theme and Plugins (if not already set in main .zshrc)
ZSH_THEME="duellj"
# plugins=(git python)

# Preferred editor
export EDITOR='nano'
export VISUAL='nano'

# Useful Aliases
alias ll='ls -FGlAhp'
alias which='type -a'
alias zshconfig="nano ~/.zshrc"
alias ohmyzsh="nano ~/.oh-my-zsh"

# Network & System
alias pingwtf='ping 8.8.8.8 -c' # Usage: pingwtf 10
alias restart='sudo shutdown -r now'
alias cleanup='python3 /usr/local/bin/file_cleanup.py'
alias netdiag='python3 ~/Diagnostic\ Tools/Network/network_troubleshooter.py'

# Information helper
ii () {
    echo -e "\nYou are logged on $HOST"
    echo -e "\nAdditionnal information: " ; uname -a
    echo -e "\nUsers logged on: " ; w -h
    echo -e "\nCurrent date : " ; date
    echo -e "\nMachine stats : " ; uptime
    echo -e "\nCurrent network location : " ; scselect
    echo
}

# Archive extraction
extract () {
    if [ -f "$1" ] ; then
      case "$1" in
        *.tar.bz2)   tar xjf "$1"     ;;
        *.tar.gz)    tar xzf "$1"     ;;
        *.bz2)       bunzip2 "$1"     ;;
        *.rar)       unrar e "$1"     ;;
        *.gz)        gunzip "$1"      ;;
        *.tar)       tar xf "$1"      ;;
        *.tbz2)      tar xjf "$1"     ;;
        *.tgz)       tar xzf "$1"     ;;
        *.zip)       unzip "$1"       ;;
        *.Z)         uncompress "$1"  ;;
        *.7z)        7z x "$1"        ;;
        *)           echo "'$1' cannot be extracted via extract()" ;;
      esac
    else
      echo "'$1' is not a valid file"
    fi
}

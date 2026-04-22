#!/bin/zsh
# State management for macOS Setup Suite

STATE_FILE="${HOME}/.mac-setup-state.json"

# Ensure state file exists
if [[ ! -f "${STATE_FILE}" ]]; then
  echo "{}" > "${STATE_FILE}"
fi

set_state() {
  local key="$1"
  local value="$2"
  
  if command -v jq >/dev/null 2>&1; then
    local tmp=$(mktemp)
    jq --arg key "${key}" --arg value "${value}" '.[$key] = $value' "${STATE_FILE}" > "${tmp}" && mv "${tmp}" "${STATE_FILE}"
  else
    # Fallback if jq not yet installed
    return 0
  fi
}

get_state() {
  local key="$1"
  
  if command -v jq >/dev/null 2>&1; then
    jq -r --arg key "${key}" '.[$key] // empty' "${STATE_FILE}"
  else
    return 1
  fi
}

is_completed() {
  local task="$1"
  local current_status=$(get_state "${task}")
  [[ "${current_status}" == "completed" ]]
}

mark_completed() {
  local task="$1"
  set_state "${task}" "completed"
}

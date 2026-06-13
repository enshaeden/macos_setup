#!/bin/zsh
# Extracted logic for setting up LaunchAgents
source "${SCRIPT_DIR}/scripts/lib/logger.sh"

USER_HOME="${HOME}"
LAUNCH_AGENTS_DIR="${USER_HOME}/Library/LaunchAgents"
mkdir -p "${LAUNCH_AGENTS_DIR}"

CLEANUP_SCRIPT_DEST="/usr/local/bin/file_cleanup.py"
CLEANUP_PLIST="${LAUNCH_AGENTS_DIR}/net.enshaeden.file_cleanup.plist"
MONITOR_PLIST="${LAUNCH_AGENTS_DIR}/net.enshaeden.net_monitor.plist"

sudo mkdir -p /usr/local/bin
sudo cp "${SCRIPT_DIR}/scripts/file_cleanup.py" "${CLEANUP_SCRIPT_DEST}"
sudo chmod +x "${CLEANUP_SCRIPT_DEST}"

uv_bin="${HOME}/.local/bin/uv"

# Cleanup Agent
cat > "${CLEANUP_PLIST}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>net.enshaeden.file_cleanup</string>
  <key>ProgramArguments</key>
  <array>
    <string>${uv_bin}</string>
    <string>run</string>
    <string>${CLEANUP_SCRIPT_DEST}</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>StartInterval</key>
  <integer>5760</integer>
  <key>StandardOutPath</key>
  <string>${USER_HOME}/Library/Logs/net.enshaeden.file_cleanup.log</string>
  <key>StandardErrorPath</key>
  <string>${USER_HOME}/Library/Logs/net.enshaeden.file_cleanup.err</string>
</dict>
</plist>
EOF

# Monitor Agent
cat > "${MONITOR_PLIST}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>net.enshaeden.net_monitor</string>
  <key>ProgramArguments</key>
  <array>
    <string>${uv_bin}</string>
    <string>run</string>
    <string>${SCRIPT_DIR}/scripts/net_monitor.py</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${USER_HOME}/Library/Logs/net.enshaeden.net_monitor.log</string>
  <key>StandardErrorPath</key>
  <string>${USER_HOME}/Library/Logs/net.enshaeden.net_monitor.err</string>
</dict>
</plist>
EOF

chmod 644 "${CLEANUP_PLIST}" "${MONITOR_PLIST}"
for plist in "${CLEANUP_PLIST}" "${MONITOR_PLIST}"; do
  launchctl bootout "gui/$(id -u)" "${plist}" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "${plist}"
done

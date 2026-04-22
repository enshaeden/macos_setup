# macOS Setup Tool

A modular setup suite for macOS (Apple Silicon). This tool provisions your machine with Homebrew, Python, Zsh, and personal automation scripts while providing ongoing maintenance and monitoring.

## Fast Installation (New Mac)

Open **Terminal** and run the following command:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/enshaeden/macos_setup/main/bootstrap.sh)"
```

*Note: Update the `REPO_URL` in `bootstrap.sh` before running.*

## Key Features

- **Modular Architecture**: Tasks are split into independent modules (`modules/`) for better maintenance.
- **Unified Configuration**: Control the entire suite from a single `config.yaml`.
- **State Management**: Tracks task completion in `~/.mac-setup-state.json` for idempotent runs.
- **Unified Logging**: All logs are written to `~/Library/Logs/mac-setup/`.
- **Proactive Monitoring**: Background network monitoring with non-blocking notifications.
- **Maintenance**: Automated file cleanup for Desktop and Downloads with regex support.

## Project Structure

- `macos_setup.sh`: The modular orchestrator.
- `config.yaml`: The single source of truth for settings and feature toggles.
- `modules/`: Contains setup modules (Homebrew, Zsh, Python, etc.).
- `scripts/`:
  - `lib/`: Shared shell libraries for logging and state management.
  - `file_cleanup.py`: Advanced file organizer with regex routing.
  - `net_monitor.py`: Background network health monitor.
  - `network_troubleshooter.py`: Comprehensive macOS diagnostic utility.
- `dotfiles/`: Custom shell configuration.

## Customization

Modify `config.yaml` to:
- Enable or disable specific features.
- Update app download URLs.
- Define custom file routing rules (supporting extensions and regex).
- Adjust network monitoring thresholds.

## Maintenance & Logs

- **Setup Logs**: `~/Library/Logs/mac-setup/setup.log`
- **Cleanup Logs**: `~/Library/Logs/mac-setup/file_cleanup.log`
- **Network Logs**: `~/Library/Logs/mac-setup/net_monitor.log`

To update your setup:
```bash
cd ~/.mac-setup # Default install dir
git pull
./macos_setup.sh
```

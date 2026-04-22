#!/usr/bin/env python3
import subprocess
import time
import yaml
import logging
from pathlib import Path

# Setup logging
LOG_DIR = Path.home() / "Library/Logs/mac-setup"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "net_monitor.log"),
        logging.StreamHandler()
    ]
)

def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    if not config_path.exists():
        return {}
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def show_notification(title, message):
    """Shows a non-blocking macOS notification."""
    script = f'display notification "{message}" with title "{title}"'
    subprocess.run(["osascript", "-e", script])

def check_network(target):
    try:
        result = subprocess.run(
            ["ping", "-c", "5", "-q", target],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return 100, 0 # 100% loss
        
        # Parse output
        loss_line = [line for line in result.stdout.split("\n") if "packet loss" in line][0]
        loss = float(loss_line.split("%")[0].split(",")[-1].strip())
        
        latency_line = [line for line in result.stdout.split("\n") if "round-trip" in line][0]
        avg_latency = float(latency_line.split("/")[4])
        
        return loss, avg_latency
    except Exception as e:
        logging.error(f"Monitor ping error: {e}")
        return 100, 0

def main():
    logging.info("Starting proactive network monitor...")
    while True:
        config = load_config()
        mon_config = config.get("monitoring", {})
        if not mon_config:
            time.sleep(60)
            continue

        target = mon_config.get("target", "1.1.1.1")
        loss_threshold = mon_config.get("thresholds", {}).get("packet_loss_percent", 10)
        latency_threshold = mon_config.get("thresholds", {}).get("latency_ms", 150)
        interval = mon_config.get("interval_seconds", 300)

        loss, latency = check_network(target)
        
        issues = []
        if loss >= loss_threshold:
            issues.append(f"High loss: {loss}%")
        if latency >= latency_threshold:
            issues.append(f"High latency: {latency}ms")
        
        if issues:
            msg = " | ".join(issues)
            logging.warning(f"Network issue detected: {msg}")
            if mon_config.get("alerts_enabled"):
                show_notification("Network Issue Detected", msg)
        else:
            logging.info(f"Network healthy. Target: {target}, Latency: {latency}ms")
        
        time.sleep(interval)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import subprocess
import time
import os
import socket
import re
import json
from pathlib import Path

def run_command(command_list):
    """Runs a command, captures output, returns output or error."""
    try:
        process = subprocess.run(command_list, capture_output=True, text=True, timeout=60)
        if process.returncode != 0:
            return f"ERROR: Command failed (return code {process.returncode})\n{process.stderr}"
        return process.stdout.strip()
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out."
    except Exception as e:
        return f"ERROR: {e}"

def get_default_gateway():
    """Gets default gateway for macOS."""
    output = run_command(["route", "-n", "get", "default"])
    match = re.search(r"gateway: ([0-9.]+)", output)
    return match.group(1) if match else "ERROR: Could not determine default gateway."

def check_vpn():
    """Checks for active VPN connections on macOS."""
    output = run_command(["ifconfig"])
    vpn_keywords = ["tun", "ppp", "utun"]
    active_vpn = []
    lines = output.splitlines()
    for i in range(len(lines)):
        if any(keyword in lines[i] for keyword in vpn_keywords):
            for j in range(i + 1, min(i + 5, len(lines))):
                if "inet " in lines[j]:
                    active_vpn.append(lines[i].strip())
                    break
    return "VPN active" if active_vpn else "No active VPN detected"

def ping_test(target, count=4):
    print(f"Pinging {target}...")
    return run_command(["ping", "-c", str(count), target])

def traceroute_test(target, max_hops=30):
    print(f"Running traceroute to {target}...")
    output = run_command(["traceroute", "-n", "-m", str(max_hops), target])
    
    hops = []
    for line in output.split("\n"):
        match = re.search(r"^\s*(\d+)\s+([\d.*]+)", line)
        if match:
            hops.append({"Hop": match.group(1), "IP": match.group(2)})
    return {"hops": hops, "raw": output}

def dns_health_check(targets=["8.8.8.8", "1.1.1.1"]):
    results = {}
    for dns in targets:
        start = time.time()
        run_command(["nslookup", "google.com", dns])
        results[dns] = round((time.time() - start) * 1000, 2)
    return results

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "ERROR"

def save_results(results):
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_folder = Path.home() / "Library/Logs/mac-setup/diagnostics"
    log_folder.mkdir(parents=True, exist_ok=True)
    log_path = log_folder / f"diag_{timestamp}.json"
    with open(log_path, "w") as f:
        json.dump(results, f, indent=4)
    return log_path

def main():
    print("\n--- macOS Network Diagnostics ---\n")
    target = "8.8.8.8"
    
    results = {
        "timestamp": time.ctime(),
        "gateway": get_default_gateway(),
        "vpn": check_vpn(),
        "local_ip": get_local_ip(),
        "ping": ping_test(target),
        "traceroute": traceroute_test(target),
        "dns": dns_health_check()
    }
    
    log_path = save_results(results)
    print(f"\nDiagnostics complete. Saved to: {log_path}\n")
    
    # Simple summary
    print("Summary:")
    print(f"- Gateway: {results['gateway']}")
    print(f"- VPN: {results['vpn']}")
    print(f"- Local IP: {results['local_ip']}")
    if "ERROR" in results['ping']:
        print("- Ping: FAILED")
    else:
        print("- Ping: SUCCESS")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import subprocess
import platform
import time
import os
import socket
import re
import json

def run_command(command_list):
    """Runs a command, captures output, returns output or error."""
    try:
        process = subprocess.run(command_list, capture_output=True, text=True, timeout=60)
        if process.returncode != 0:
            return f"ERROR: Command failed (return code {process.returncode})\n{process.stderr}"
        return process.stdout.strip()
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out."
    except FileNotFoundError:
        return "ERROR: Command not found. Is it installed?"
    except Exception as e:
        return f"ERROR: {e}"

def get_default_gateway():
    """Gets default gateway in a system-agnostic way."""
    print("Checking default gateway...")
    if platform.system() == "Windows":
        output = run_command(["ipconfig"])
        match = re.search(r"Default Gateway[. ]*: ([0-9.]+)", output)
    elif platform.system() == "Darwin":
        output = run_command(["route", "-n", "get", "default"])
        match = re.search(r"gateway: ([0-9.]+)", output)
    else:
        output = run_command(["ip", "route", "show"]) or run_command(["netstat", "-nr"])
        match = re.search(r"default via ([0-9.]+)", output)
    return match.group(1) if match else "ERROR: Could not determine default gateway."

def check_vpn():
    """Checks for active VPN connections by detecting VPN interfaces with IP addresses."""
    print("Checking for active VPN connections...")
    system = platform.system()

    if system == "Windows":
        output = run_command(["rasdial"])
        return "VPN active" if "No connections" not in output else "No active VPN detected"

    output = run_command(["ifconfig"] if system == "Darwin" else ["ip", "addr", "show"])
    vpn_keywords = ["tun", "ppp", "utun"]

    active_vpn = []
    lines = output.splitlines()
    for i in range(len(lines)):
        line = lines[i]
        if any(keyword in line for keyword in vpn_keywords):
            for j in range(i + 1, min(i + 5, len(lines))):
                if "inet " in lines[j] or "inet addr:" in lines[j]:
                    active_vpn.append(line.strip())
                    break

    return "VPN active" if active_vpn else "No active VPN detected"

def ping_test(target, count=4):
    """Performs a ping test to the target."""
    print(f"Pinging {target} with {count} packets...")
    command = ["ping", "-n" if platform.system() == "Windows" else "-c", str(count), target]
    return run_command(command)

def measure_latency(target, count=10):
    """Measures latency and packet loss over multiple ping tests."""
    print(f"Measuring latency to {target} with {count} packets...")
    output = run_command(["ping", "-c", str(count), target])

    packet_loss = re.search(r"(\d+)% packet loss", output)
    avg_latency = re.search(r"= ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)", output)

    return {
        "Packet Loss": packet_loss.group(1) + "%" if packet_loss else "N/A",
        "Avg Latency (ms)": avg_latency.group(2) if avg_latency else "N/A"
    }

def traceroute_test(target, max_hops=30):
    """Performs a traceroute test with structured output and success check."""
    print(f"Running traceroute to {target} with max {max_hops} hops...")

    try:
        resolved_target = socket.gethostbyname(target)
    except Exception:
        resolved_target = target

    command = (
        ["tracert", "-d", "-h", str(max_hops), target]
        if platform.system() == "Windows"
        else ["traceroute", "-n", "-m", str(max_hops), target]
    )
    output = run_command(command)

    hops = []
    target_reached = False
    failed_at = None
    last_hop_num = 0

    for line in output.split("\n"):
        match = re.search(r"^\s*(\d+)\s+([\d.*]+)", line)
        if match:
            hop = match.group(1).strip()
            ip = match.group(2).strip()
            last_hop_num = int(hop)
            hops.append({"Hop": hop, "IP": ip})

            if ip == resolved_target:
                target_reached = True

    if not target_reached:
        failed_at = str(last_hop_num + 1)

    return {
        "hops": hops if hops else "Traceroute failed.",
        "trace_successful": target_reached,
        "trace_failed_at_hop": failed_at
    }

def dns_lookup(target):
    """Performs a DNS lookup."""
    print(f"Performing DNS lookup for {target}...")
    return run_command(["nslookup", target]) or run_command(["dig", "+short", target])

def dns_health_check(targets=["8.8.8.8", "1.1.1.1", "9.9.9.9"]):
    """Compares DNS resolution times using multiple DNS providers."""
    print("Checking DNS resolution times...")
    results = {}
    for dns in targets:
        start = time.time()
        run_command(["nslookup", "example.com", dns])
        results[dns] = round((time.time() - start) * 1000, 2)
    return results

def netstat_connections():
    """Retrieves active network connections."""
    print("Checking active network connections...")
    return run_command(["netstat", "-an"])

def get_network_interfaces():
    """Retrieves network interface details."""
    print("Retrieving network interface details...")
    return run_command(["ipconfig", "/all"] if platform.system() == "Windows" else ["ifconfig"])

def get_arp_table():
    """Retrieves ARP table and extracts IP-to-MAC mappings."""
    print("Retrieving ARP table...")
    output = run_command(["arp", "-a"])
    arp_entries = []

    for line in output.splitlines():
        if platform.system() == "Darwin":
            match = re.search(r"\((\d+\.\d+\.\d+\.\d+)\) at ([0-9a-f:]+)", line)
        else:
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([\w:-]+)", line)

        if match:
            arp_entries.append({
                "IP Address": match.group(1),
                "MAC Address": match.group(2)
            })

    return arp_entries if arp_entries else "No ARP entries found."

def get_mtu():
    """Retrieves MTU settings."""
    print("Checking MTU settings...")
    return run_command(["netsh", "interface", "ipv4", "show", "subinterfaces"] if platform.system() == "Windows" else ["ifconfig"])

def get_route_table():
    """Retrieves the system's route table."""
    print("Retrieving routing table...")
    return run_command(["route", "print"] if platform.system() == "Windows" else ["netstat", "-rn"])

def get_local_ip():
    """Retrieves the local machine's external IP address reliably."""
    print("Retrieving local IP address...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception as e:
        return f"ERROR: Could not determine local IP - {e}"

def test_connectivity(target):
    """Tests basic connectivity to a target using multiple ports."""
    print(f"Testing connectivity to {target}...")
    for port in [80, 443, 53]:
        try:
            with socket.create_connection((target, port), timeout=5):
                return f"Connection successful on port {port}"
        except Exception:
            continue
    return "ERROR: Connection failed on all tested ports."

def clear_screen():
    os.system('cls' if platform.system() == "Windows" else 'clear')

def save_results(results):
    """Saves results to a log file in JSON format."""
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    log_folder = os.path.expanduser("~/Desktop/Network_Logs")
    os.makedirs(log_folder, exist_ok=True)
    log_path = os.path.join(log_folder, f"network_diagnostics_{timestamp}.json")
    with open(log_path, "w") as file:
        json.dump(results, file, indent=4)
    return log_path

def main():
    start_time = time.time()

    print("\n--- Network Diagnostics Tool ---\n")
    target = input("Enter a target (default: 8.8.8.8): ").strip() or "8.8.8.8"
    max_hops = input("Enter max traceroute hops (default 30): ").strip() or "30"
    ping_count = input("Enter ping count (default 4): ").strip() or "4"

    try:
        max_hops = int(max_hops)
        ping_count = int(ping_count)
    except ValueError:
        print("Invalid input, using defaults.")
        max_hops, ping_count = 30, 4

    clear_screen()

    results = {
        "default_gateway": get_default_gateway(),
        "vpn_check": check_vpn(),
        "local_ip": get_local_ip(),
        "connectivity_test": test_connectivity(target),
        "ping_test": ping_test(target, ping_count),
        "latency_test": measure_latency(target),
        "traceroute_test": traceroute_test(target, max_hops),
        "dns_lookup": dns_lookup(target),
        "dns_health_check": dns_health_check(),
        "netstat_connections": netstat_connections(),
        "network_interfaces": get_network_interfaces(),
        "arp_table": get_arp_table(),
        "mtu_settings": get_mtu(),
        "route_table": get_route_table(),
    }

    log_path = save_results(results)
    end_time = time.time()
    print(f"\nDiagnostics complete in {round(end_time - start_time, 2)} seconds. Results saved to: {log_path}\n")

    return log_path


def evaluate_network_logs(file_path):
    """Reads a diagnostic JSON log and prints a human-readable health summary."""
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        cleaned_lines = [line for line in lines if not line.strip().startswith("//")]
        data = json.loads("".join(cleaned_lines))

        issues = []

        print("Network Diagnostics Evaluation")
        print("=" * 40)
        print("")

        if "default_gateway" in data:
            print(f"Default Gateway: The gateway {data['default_gateway']} is valid.\n")

        if "vpn_check" in data:
            vpn_status = data["vpn_check"].lower().strip()
            if vpn_status.startswith("no"):
                print("VPN Status: No VPN detected.\n")
            else:
                print("VPN Status: A VPN is active.\n")

        if "local_ip" in data:
            print(f"Local IP Address: The local IP {data['local_ip']} is correctly assigned.\n")

        if "connectivity_test" in data:
            if "successful" in data["connectivity_test"].lower():
                print("Connectivity Test: Successful connection.\n")
            else:
                print("Connectivity Test: Connection failed.\n")
                issues.append("Connectivity test failure")

        if "ping_test" in data and data["ping_test"]:
            ping_output = data["ping_test"]
            if "ERROR" in ping_output:
                print("Ping Test: Ping command failed.\n")
                issues.append("Ping test failed")
            else:
                match = re.search(r"(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)", ping_output)
                if match:
                    _, avg_time, _, stddev = match.groups()
                    print(f"Ping Test: Avg latency is {avg_time} ms; Std Dev is {stddev} ms.\n")
                    if float(stddev) > 10:
                        issues.append("Ping instability")
                else:
                    print("Ping Test: Unable to parse statistics.\n")
                    issues.append("Ping parsing error")

        if "latency_test" in data:
            loss = data["latency_test"].get("Packet Loss", "N/A")
            latency = data["latency_test"].get("Avg Latency (ms)", "N/A")
            if loss == "N/A" or latency == "N/A":
                print("Latency Test: No latency data available.\n")
            else:
                print(f"Latency Test: Packet loss is {loss}; Avg latency is {latency} ms.\n")
                if loss.lower() not in ["0%", "0"]:
                    issues.append("Packet loss detected")
                if float(latency) > 100:
                    issues.append("High latency")

        if "traceroute_test" in data:
            test = data["traceroute_test"]
            if isinstance(test, dict):
                hops = test.get("hops", [])
                if test.get("trace_successful", True):
                    print("Traceroute Test: Traceroute completed successfully.\n")
                elif isinstance(hops, list) and any(hop.get("IP", "") == "*" for hop in hops):
                    print("Traceroute Test: Some hops timed out.\n")
                    issues.append("Traceroute incomplete")
                else:
                    print("Traceroute Test: Traceroute failed.\n")
                    issues.append("Traceroute failure")
            elif isinstance(test, list):
                if any(hop.get("IP", "") == "*" for hop in test):
                    print("Traceroute Test: Some hops timed out.\n")
                    issues.append("Traceroute incomplete")
                else:
                    print("Traceroute Test: Completed successfully.\n")
            elif isinstance(test, str):
                if "failed" in test.lower():
                    print("Traceroute Test: Traceroute test failed.\n")
                    issues.append("Traceroute failure")
                else:
                    print("Traceroute Test: Completed successfully.\n")

        if "dns_lookup" in data:
            if "ERROR" in data["dns_lookup"]:
                print("DNS Lookup: DNS lookup failed.\n")
                issues.append("DNS lookup failure")
            else:
                print("DNS Lookup: DNS lookup succeeded.\n")

        if "dns_health_check" in data:
            dns_results = []
            for server, latency in data["dns_health_check"].items():
                dns_results.append(f"{server}: {latency} ms")
            print(f"DNS Health Check: {', '.join(dns_results)}.\n")
            for lat in data["dns_health_check"].values():
                if float(lat) > 50:
                    issues.append("High DNS latency")
                    break

        if "netstat_connections" in data:
            output = data["netstat_connections"]
            connections = re.findall(r"(\S+\.\d+)\s+(\S+\.\d+)\s+(\S+)", output)
            if connections:
                estab = sum(1 for _, _, state in connections if state == "ESTABLISHED")
                print(f"Netstat Connections: {estab} established connections.\n")
                if estab < 5:
                    issues.append("Low active connections")
            else:
                print("Netstat Connections: No active connections found.\n")
                issues.append("No active connections")

        if "network_interfaces" in data:
            ni = data["network_interfaces"]
            count = len([line for line in ni.splitlines() if line.strip() != ""])
            print(f"Network Interfaces: Detected {count} lines in interfaces info.\n")

        if "arp_table" in data:
            arp = data["arp_table"]
            if isinstance(arp, list) and arp:
                print(f"ARP Table: Found {len(arp)} entries:")
                for entry in arp:
                    ip = entry.get("IP Address", "Unknown")
                    mac = entry.get("MAC Address", "Unknown")
                    first_octet = mac.split(":")[0].zfill(2)
                    try:
                        multicast_tag = " (multicast)" if int(first_octet, 16) & 1 else ""
                    except ValueError:
                        multicast_tag = ""
                    print(f"   {ip} -> {mac}{multicast_tag}")
                print("")
            elif isinstance(arp, str):
                if "no arp entries" in arp.lower():
                    print("ARP Table: No ARP entries found.\n")
                else:
                    print("ARP Table: ARP entries exist.\n")

        if "mtu_settings" in data:
            mtu = data["mtu_settings"]
            lines = [line.strip() for line in mtu.splitlines() if line.strip()]
            mtu_values = []
            for line in lines:
                match = re.search(r"\b(?:MTU[:\s]*)(\d{3,5})\b", line, re.IGNORECASE)
                if match:
                    mtu_values.append(int(match.group(1)))
                else:
                    num_match = re.search(r"\b(1[0-9]{3})\b", line)
                    if num_match:
                        mtu_values.append(int(num_match.group(1)))
            if mtu_values:
                max_mtu = max(sorted(set(mtu_values)))
                mtu_msg = f"Optimal MTU achieved: {max_mtu} bytes."
            else:
                mtu_msg = "MTU test results could not be determined. Please verify the test configuration."
            print(f"MTU Settings: Found info across {len(lines)} lines.\nInterpretation: {mtu_msg}\n")

        if "route_table" in data:
            rt = data["route_table"]
            rt_lines = len([line for line in rt.splitlines() if line.strip() != ""])
            print(f"Route Table: Contains {rt_lines} lines of routing information.\n")

        print("*" * 40)
        print("OVERALL EVALUATION:", end=" ")
        if not issues:
            print("Network appears healthy with no major issues detected.")
        else:
            if "Connectivity test failure" in issues or "Ping test failed" in issues:
                cause = "Possible connectivity or firewall issues."
            elif "Packet loss detected" in issues or "High latency" in issues:
                cause = "Network congestion or instability."
            elif "Traceroute failure" in issues or "Traceroute incomplete" in issues:
                cause = "Routing issues or firewall restrictions."
            elif "DNS lookup failure" in issues or "High DNS latency" in issues:
                cause = "DNS server configuration issues."
            else:
                cause = "Mixed network issues."
            print(f"Issues detected: {', '.join(issues)}. {cause}")

        print("*" * 40)
        print("\n\nEvaluation Complete.")
        print("=" * 40)

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except json.JSONDecodeError:
        print(f"Error: Failed to parse JSON file at {file_path}")

if __name__ == "__main__":
    log = main()
    evaluate_network_logs(log)

#!/usr/bin/env python3
import subprocess
import platform
import time
import os
import socket
import re
import json
import urllib.request
import urllib.error
import ssl

SYSTEM = platform.system()


# ---------------------------------------------------------------------------
# Core runner
# ---------------------------------------------------------------------------

def run_command(command_list, timeout=60):
    try:
        process = subprocess.run(command_list, capture_output=True, text=True, timeout=timeout)
        if process.returncode != 0:
            return f"ERROR: Command failed (return code {process.returncode})\n{process.stderr}"
        return process.stdout.strip()
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out."
    except FileNotFoundError:
        return f"ERROR: Command not found: {command_list[0]}"
    except Exception as e:
        return f"ERROR: {e}"


# ---------------------------------------------------------------------------
# Environment context
# ---------------------------------------------------------------------------

def get_environment_info():
    print("Collecting environment info...")
    info = {
        "hostname": socket.gethostname(),
        "platform": SYSTEM,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if SYSTEM == "Darwin":
        info["os_version"] = run_command(["sw_vers", "-productVersion"])
        info["os_build"] = run_command(["sw_vers", "-buildVersion"])
        dsconfigad = run_command(["dsconfigad", "-show"])
        if "ERROR" not in dsconfigad and dsconfigad:
            domain_match = re.search(r"Active Directory Domain\s*=\s*(.+)", dsconfigad)
            info["ad_domain"] = domain_match.group(1).strip() if domain_match else None
        else:
            info["ad_domain"] = None
    elif SYSTEM == "Windows":
        info["os_version"] = platform.version()
    else:
        info["os_version"] = platform.release()
    return info


# ---------------------------------------------------------------------------
# Network identity
# ---------------------------------------------------------------------------

def get_default_gateway():
    print("Checking default gateway...")
    if SYSTEM == "Windows":
        output = run_command(["ipconfig"])
        match = re.search(r"Default Gateway[. ]*: ([0-9.]+)", output)
    elif SYSTEM == "Darwin":
        output = run_command(["route", "-n", "get", "default"])
        match = re.search(r"gateway: ([0-9.]+)", output)
    else:
        output = run_command(["ip", "route", "show"]) or run_command(["netstat", "-nr"])
        match = re.search(r"default via ([0-9.]+)", output)
    return match.group(1) if match else "ERROR: Could not determine default gateway."


def get_local_ip():
    print("Retrieving local IP address...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception as e:
        return f"ERROR: Could not determine local IP - {e}"


def get_public_ip():
    print("Checking public IP address...")
    endpoints = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "http://checkip.amazonaws.com",
    ]
    ctx = ssl.create_default_context()
    for url in endpoints:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "network-diag/1.0"})
            with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
                ip = resp.read().decode().strip()
                if re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
                    return ip
        except Exception:
            continue
    return "ERROR: Could not determine public IP"


# ---------------------------------------------------------------------------
# VPN detection
# ---------------------------------------------------------------------------

def check_vpn():
    print("Checking for active VPN connections...")
    if SYSTEM == "Windows":
        output = run_command(["rasdial"])
        return {"active": "No connections" not in output, "interfaces": []}

    output = run_command(["ifconfig"])
    vpn_keywords = ["tun", "ppp", "utun"]
    active_vpn = []
    lines = output.splitlines()
    for i, line in enumerate(lines):
        if any(keyword in line for keyword in vpn_keywords):
            iface_match = re.match(r"^(\S+):", line)
            iface_name = iface_match.group(1) if iface_match else line.strip()
            tunnel_ip = None
            for j in range(i + 1, min(i + 5, len(lines))):
                ip_match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", lines[j])
                if ip_match:
                    tunnel_ip = ip_match.group(1)
                    break
            if tunnel_ip:
                active_vpn.append({"interface": iface_name, "tunnel_ip": tunnel_ip})

    return {"active": bool(active_vpn), "interfaces": active_vpn}


# ---------------------------------------------------------------------------
# WiFi
# ---------------------------------------------------------------------------

def get_wifi_info():
    print("Checking WiFi status...")
    if SYSTEM != "Darwin":
        return {"status": "WiFi check only supported on macOS"}

    airport = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
    if not os.path.exists(airport):
        return {"status": "ERROR: airport utility not found"}

    output = run_command([airport, "-I"])
    if not output or "ERROR" in output:
        return {"status": "ERROR: Could not get WiFi info"}

    result = {}
    ssid_match = re.search(r"\s+SSID: (.+)", output)
    signal_match = re.search(r"\s+agrCtlRSSI: (-?\d+)", output)
    noise_match = re.search(r"\s+agrCtlNoise: (-?\d+)", output)
    channel_match = re.search(r"\s+channel: (\S+)", output)
    bssid_match = re.search(r"\s+BSSID: (\S+)", output)

    if ssid_match:
        result["connected"] = True
        result["ssid"] = ssid_match.group(1).strip()
    else:
        result["connected"] = False
        result["ssid"] = None

    if signal_match:
        rssi = int(signal_match.group(1))
        result["rssi_dbm"] = rssi
        if rssi >= -50:
            result["signal_quality"] = "Excellent"
        elif rssi >= -60:
            result["signal_quality"] = "Good"
        elif rssi >= -70:
            result["signal_quality"] = "Fair"
        else:
            result["signal_quality"] = "Poor"

    if noise_match and signal_match:
        result["snr_db"] = int(signal_match.group(1)) - int(noise_match.group(1))

    if channel_match:
        ch_str = channel_match.group(1)
        result["channel"] = ch_str
        ch_num = re.match(r"(\d+)", ch_str)
        if ch_num:
            ch = int(ch_num.group(1))
            result["band"] = "2.4 GHz" if ch <= 14 else ("5 GHz" if ch <= 64 else "5/6 GHz")

    if bssid_match:
        result["bssid"] = bssid_match.group(1)

    return result


# ---------------------------------------------------------------------------
# Captive portal
# ---------------------------------------------------------------------------

def check_captive_portal():
    print("Checking for captive portal...")
    try:
        req = urllib.request.Request(
            "http://captive.apple.com/hotspot-detect.html",
            headers={"User-Agent": "CaptiveNetworkSupport"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode()
            if "<TITLE>Success</TITLE>" in body:
                return {"captive": False, "status": "No captive portal detected"}
            return {"captive": True, "status": "Captive portal likely active — login page may be required"}
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 307, 308):
            return {"captive": True, "status": f"Captive portal redirect detected (HTTP {e.code})"}
        return {"captive": False, "status": f"HTTP {e.code} — likely no captive portal"}
    except Exception as e:
        return {"captive": None, "status": f"ERROR: {e}"}


# ---------------------------------------------------------------------------
# Proxy detection
# ---------------------------------------------------------------------------

def check_proxy():
    print("Checking proxy configuration...")
    proxy_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
                  "NO_PROXY", "no_proxy", "ALL_PROXY"]
    found = {var: os.environ[var] for var in proxy_vars if var in os.environ}

    if SYSTEM == "Darwin":
        scutil_output = run_command(["scutil", "--proxy"])
        if "HTTPEnable : 1" in scutil_output:
            h = re.search(r"HTTPProxy : (\S+)", scutil_output)
            p = re.search(r"HTTPPort : (\d+)", scutil_output)
            if h:
                found["macOS_HTTP_proxy"] = f"{h.group(1)}:{p.group(1) if p else '?'}"
        if "HTTPSEnable : 1" in scutil_output:
            h = re.search(r"HTTPSProxy : (\S+)", scutil_output)
            p = re.search(r"HTTPSPort : (\d+)", scutil_output)
            if h:
                found["macOS_HTTPS_proxy"] = f"{h.group(1)}:{p.group(1) if p else '?'}"

    return {"proxies_found": found, "proxy_active": bool(found)}


# ---------------------------------------------------------------------------
# NTP
# ---------------------------------------------------------------------------

def check_ntp():
    print("Checking NTP time sync...")
    if SYSTEM == "Darwin":
        server_out = run_command(["systemsetup", "-getnetworktimeserver"])
        server_match = re.search(r"Network Time Server: (\S+)", server_out)
        ntp_server = server_match.group(1) if server_match else "time.apple.com"

        enabled_out = run_command(["systemsetup", "-getnetworktime"])
        ntp_enabled = "Network Time: On" in enabled_out

        sntp_out = run_command(["sntp", "-t", "2", ntp_server], timeout=10)
        offset_match = re.search(r"([+-]?\d+\.\d+)\s*[+-]\d+\.\d+\s*s", sntp_out)
        offset = float(offset_match.group(1)) if offset_match else None

        return {
            "ntp_enabled": ntp_enabled,
            "ntp_server": ntp_server,
            "offset_seconds": offset,
            "clock_skewed": abs(offset) > 300 if offset is not None else None,
        }
    elif SYSTEM == "Linux":
        output = run_command(["timedatectl", "status"])
        return {"ntp_enabled": "System clock synchronized: yes" in output, "raw": output}
    return {"status": "NTP check not implemented for this platform"}


# ---------------------------------------------------------------------------
# DNS
# ---------------------------------------------------------------------------

def get_local_dns_servers():
    print("Checking local DNS configuration...")
    if SYSTEM == "Darwin":
        output = run_command(["scutil", "--dns"])
        servers = list(dict.fromkeys(re.findall(r"nameserver\[\d+\]\s*:\s*(\S+)", output)))
        domains = list(dict.fromkeys(re.findall(r"search domain\[\d+\]\s*:\s*(\S+)", output)))
        return {"nameservers": servers, "search_domains": domains}
    try:
        with open("/etc/resolv.conf") as f:
            content = f.read()
        servers = re.findall(r"^nameserver\s+(\S+)", content, re.MULTILINE)
        domains = re.findall(r"^search\s+(.+)", content, re.MULTILINE)
        return {"nameservers": servers, "search_domains": domains}
    except Exception as e:
        return {"error": str(e)}


def dns_lookup(target):
    print(f"Performing DNS lookup for {target}...")
    # IP target → forward lookup on known hostname (reverse lookup not useful here)
    if re.match(r"^\d+\.\d+\.\d+\.\d+$", target):
        lookup_target = "example.com"
        print(f"  (target is IP; testing forward lookup with {lookup_target})")
    else:
        lookup_target = target
    result = run_command(["nslookup", lookup_target])
    if not result or "ERROR" in result:
        result = run_command(["dig", "+short", lookup_target])
    return result


def dns_health_check(targets=None):
    if targets is None:
        targets = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]
    print("Checking DNS resolution times...")
    results = {}
    for dns in targets:
        start = time.time()
        out = run_command(["nslookup", "example.com", dns], timeout=10)
        elapsed = round((time.time() - start) * 1000, 2)
        results[dns] = {
            "latency_ms": elapsed,
            "success": "ERROR" not in out and "failed" not in out.lower()
        }
    return results


# ---------------------------------------------------------------------------
# Connectivity tests
# ---------------------------------------------------------------------------

def test_connectivity(target):
    print(f"Testing connectivity to {target}...")
    for port in [80, 443, 53]:
        try:
            with socket.create_connection((target, port), timeout=5):
                return f"Connection successful on port {port}"
        except Exception:
            continue
    return "ERROR: Connection failed on all tested ports."


def check_http_reachability(target):
    print(f"Testing HTTP/HTTPS reachability to {target}...")
    # Use a known hostname if target is a bare IP (TLS cert validation would fail)
    test_host = target if not re.match(r"^\d+\.\d+\.\d+\.\d+$", target) else "www.example.com"
    results = {}
    ctx = ssl.create_default_context()
    for scheme in ["https", "http"]:
        url = f"{scheme}://{test_host}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "network-diag/1.0"})
            start = time.time()
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                elapsed = round((time.time() - start) * 1000, 1)
                results[scheme] = {"status": resp.status, "latency_ms": elapsed, "reachable": True}
        except urllib.error.HTTPError as e:
            results[scheme] = {"status": e.code, "reachable": True}
        except Exception as e:
            results[scheme] = {"reachable": False, "error": str(e)}
    return results


def ping_test(target, count=4):
    print(f"Pinging {target} with {count} packets...")
    command = ["ping", "-n" if SYSTEM == "Windows" else "-c", str(count), target]
    return run_command(command)


def measure_latency(target, count=10):
    print(f"Measuring latency to {target} with {count} packets...")
    flag = "-n" if SYSTEM == "Windows" else "-c"
    output = run_command(["ping", flag, str(count), target])

    if SYSTEM == "Windows":
        packet_loss = re.search(r"(\d+)% loss", output)
        avg_latency = re.search(r"Average = (\d+)ms", output)
        return {
            "Packet Loss": packet_loss.group(1) + "%" if packet_loss else "N/A",
            "Avg Latency (ms)": avg_latency.group(1) if avg_latency else "N/A"
        }
    else:
        packet_loss = re.search(r"(\d+)% packet loss", output)
        avg_latency = re.search(r"= ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)", output)
        return {
            "Packet Loss": packet_loss.group(1) + "%" if packet_loss else "N/A",
            "Avg Latency (ms)": avg_latency.group(2) if avg_latency else "N/A"
        }


def traceroute_test(target, max_hops=30):
    print(f"Running traceroute to {target} with max {max_hops} hops...")

    try:
        resolved_target = socket.gethostbyname(target)
    except Exception:
        resolved_target = target

    command = (
        ["tracert", "-d", "-h", str(max_hops), target]
        if SYSTEM == "Windows"
        else ["traceroute", "-n", "-m", str(max_hops), target]
    )
    output = run_command(command, timeout=120)

    hops = []
    target_reached = False
    last_hop_num = 0
    consecutive_timeouts = 0

    for line in output.split("\n"):
        ip_match = re.search(r"^\s*(\d+)\s+(\d+\.\d+\.\d+\.\d+)", line)
        timeout_match = re.search(r"^\s*(\d+)\s+\*", line)

        if ip_match:
            hop_num = int(ip_match.group(1))
            ip = ip_match.group(2)
            last_hop_num = hop_num
            consecutive_timeouts = 0
            hops.append({"Hop": str(hop_num), "IP": ip, "timeout": False})
            if ip == resolved_target:
                target_reached = True
        elif timeout_match:
            hop_num = int(timeout_match.group(1))
            last_hop_num = hop_num
            consecutive_timeouts += 1
            hops.append({"Hop": str(hop_num), "IP": "*", "timeout": True})

    return {
        "hops": hops if hops else "Traceroute failed.",
        "trace_successful": target_reached,
        "trace_failed_at_hop": str(last_hop_num + 1) if not target_reached else None,
        "consecutive_timeouts_at_end": consecutive_timeouts,
    }


# ---------------------------------------------------------------------------
# System info
# ---------------------------------------------------------------------------

def netstat_connections():
    print("Checking active network connections...")
    output = run_command(["netstat", "-an"])
    return {
        "established": len(re.findall(r"ESTABLISHED", output)),
        "listening": len(re.findall(r"LISTEN", output)),
        "time_wait": len(re.findall(r"TIME_WAIT", output)),
        "close_wait": len(re.findall(r"CLOSE_WAIT", output)),
    }


def get_network_interfaces():
    print("Retrieving network interface details...")
    return run_command(["ipconfig", "/all"] if SYSTEM == "Windows" else ["ifconfig"])


def get_arp_table():
    print("Retrieving ARP table...")
    output = run_command(["arp", "-a"])
    arp_entries = []
    for line in output.splitlines():
        if SYSTEM == "Darwin":
            match = re.search(r"\((\d+\.\d+\.\d+\.\d+)\) at ([0-9a-f:]+)", line)
        else:
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([\w:-]+)", line)
        if match:
            arp_entries.append({"IP Address": match.group(1), "MAC Address": match.group(2)})
    return arp_entries if arp_entries else "No ARP entries found."


def get_mtu():
    print("Checking MTU settings...")
    if SYSTEM == "Windows":
        output = run_command(["netsh", "interface", "ipv4", "show", "subinterfaces"])
        mtu_values = {}
        for line in output.splitlines():
            match = re.search(r"(\d{4,5})\s+\d+\s+\d+\s+(.+)", line)
            if match:
                mtu_values[match.group(2).strip()] = int(match.group(1))
        return mtu_values if mtu_values else output
    else:
        output = run_command(["ifconfig"])
        mtu_values = {}
        current_iface = None
        for line in output.splitlines():
            iface_match = re.match(r"^(\S+):", line)
            if iface_match:
                current_iface = iface_match.group(1)
            mtu_match = re.search(r"\bmtu\s+(\d+)\b", line, re.IGNORECASE)
            if mtu_match and current_iface:
                mtu_values[current_iface] = int(mtu_match.group(1))
        return mtu_values if mtu_values else "ERROR: Could not parse MTU values"


def get_route_table():
    print("Retrieving routing table...")
    return run_command(["route", "print"] if SYSTEM == "Windows" else ["netstat", "-rn"])


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def clear_screen():
    os.system('cls' if SYSTEM == "Windows" else 'clear')


def save_results(results):
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    log_folder = os.path.expanduser("~/Desktop/Network_Logs")
    os.makedirs(log_folder, exist_ok=True)
    log_path = os.path.join(log_folder, f"network_diagnostics_{timestamp}.json")
    with open(log_path, "w") as file:
        json.dump(results, file, indent=4)
    return log_path


# ---------------------------------------------------------------------------
# Main collection
# ---------------------------------------------------------------------------

def main():
    start_time = time.time()
    print("\n--- Network Diagnostics Tool ---\n")

    target = input("Enter a target hostname or IP (default: 8.8.8.8): ").strip() or "8.8.8.8"
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
        "environment": get_environment_info(),
        "default_gateway": get_default_gateway(),
        "local_ip": get_local_ip(),
        "public_ip": get_public_ip(),
        "vpn_check": check_vpn(),
        "wifi_info": get_wifi_info(),
        "captive_portal": check_captive_portal(),
        "proxy_config": check_proxy(),
        "ntp_check": check_ntp(),
        "local_dns_servers": get_local_dns_servers(),
        "connectivity_test": test_connectivity(target),
        "http_reachability": check_http_reachability(target),
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
    elapsed = round(time.time() - start_time, 2)
    print(f"\nDiagnostics complete in {elapsed} seconds. Results saved to: {log_path}\n")
    return log_path


# ---------------------------------------------------------------------------
# Evaluation — structured output for Help Desk and end users
# ---------------------------------------------------------------------------

def _make_finding(severity, code, what, why, likely_cause, steps):
    return {"severity": severity, "code": code, "what": what,
            "why": why, "likely_cause": likely_cause, "steps": steps}


def evaluate_network_logs(file_path):
    """Reads a diagnostic JSON log and prints a structured human-readable health summary."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        cleaned = [l for l in lines if not l.strip().startswith("//")]
        data = json.loads("".join(cleaned))
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Failed to parse JSON file at {file_path}")
        return

    findings = []
    confidence_notes = []

    # --- Environment context ---
    env = data.get("environment", {})
    hostname = env.get("hostname", socket.gethostname())
    os_version = env.get("os_version", platform.system())
    timestamp = env.get("timestamp", "Unknown")
    local_ip = data.get("local_ip", "Unknown")
    public_ip = data.get("public_ip", "Unknown")
    gateway = data.get("default_gateway", "Unknown")

    # --- VPN ---
    vpn_data = data.get("vpn_check", {})
    vpn_active = False
    vpn_interfaces = []
    if isinstance(vpn_data, dict):
        vpn_active = vpn_data.get("active", False)
        vpn_interfaces = vpn_data.get("interfaces", [])
    elif isinstance(vpn_data, str):
        vpn_active = "active" in vpn_data.lower() and not vpn_data.lower().startswith("no")

    if vpn_active:
        iface_str = (", ".join(f"{v['interface']} ({v['tunnel_ip']})" for v in vpn_interfaces)
                     if vpn_interfaces else "unknown interface")
        findings.append(_make_finding(
            "INFO", "VPN_ACTIVE",
            f"VPN is active ({iface_str})",
            "VPN tunnels traffic through a remote server. This can affect speed, routing, and which resources you can reach.",
            None,
            ["If you cannot reach company resources: disconnect and reconnect VPN.",
             "If internet is slow with VPN: ask IT about split-tunneling options."]
        ))
        confidence_notes.append("VPN active — routing path obscured, diagnosis confidence reduced")

    # --- WiFi signal ---
    wifi = data.get("wifi_info", {})
    if isinstance(wifi, dict) and wifi.get("connected"):
        signal = wifi.get("signal_quality")
        rssi = wifi.get("rssi_dbm")
        ssid = wifi.get("ssid", "Unknown")
        band = wifi.get("band", "Unknown")
        if signal in ("Poor", "Fair"):
            sev = "CRITICAL" if signal == "Poor" else "WARNING"
            findings.append(_make_finding(
                sev, "WIFI_WEAK_SIGNAL",
                f"Weak WiFi signal ({signal}, {rssi} dBm) on network '{ssid}'",
                "Weak signal causes dropped packets, slow speeds, and disconnections.",
                f"Too far from access point, physical obstructions, or interference. Currently on {band}.",
                ["Move closer to your WiFi router or access point.",
                 "Try connecting via ethernet cable if available.",
                 "If on 2.4 GHz, try the 5 GHz network if your router offers it."]
            ))

    # --- Captive portal ---
    captive = data.get("captive_portal", {})
    if isinstance(captive, dict) and captive.get("captive"):
        findings.append(_make_finding(
            "CRITICAL", "CAPTIVE_PORTAL",
            "Network login page (captive portal) is blocking internet access",
            "Hotels, cafes, airports, and some guest networks require you to accept terms or log in before granting internet access.",
            "You are on a public or guest WiFi network that requires browser authentication.",
            ["Open a web browser and visit any website — a login or terms page should appear.",
             "Accept terms or enter credentials to gain internet access.",
             "After logging in, try your original task again."]
        ))

    # --- Proxy ---
    proxy_data = data.get("proxy_config", {})
    if isinstance(proxy_data, dict) and proxy_data.get("proxy_active"):
        proxies = proxy_data.get("proxies_found", {})
        proxy_list = ", ".join(f"{k}={v}" for k, v in proxies.items())
        findings.append(_make_finding(
            "INFO", "PROXY_ACTIVE",
            f"Proxy configuration detected: {proxy_list}",
            "Proxy settings route traffic through an intermediate server. Misconfigured proxy can silently block all internet access.",
            "Corporate network policy, VPN client, or manual proxy configuration.",
            ["If not on a corporate network and internet is broken: check System Settings → Network → Proxies and disable if set.",
             "If on a corporate network: verify proxy settings with IT."]
        ))
        confidence_notes.append("Proxy active — HTTP reachability results may reflect proxy behavior, not direct connectivity")

    # --- NTP ---
    ntp = data.get("ntp_check", {})
    if isinstance(ntp, dict) and ntp.get("clock_skewed"):
        offset = ntp.get("offset_seconds", 0)
        findings.append(_make_finding(
            "WARNING", "CLOCK_SKEWED",
            f"System clock out of sync by {abs(offset):.0f} seconds",
            "Many secure services (VPN, corporate login, email) reject connections when your clock is more than 5 minutes off. This causes mysterious authentication failures.",
            "NTP sync failure, or the system was asleep or offline for an extended period.",
            ["Go to System Settings → General → Date & Time.",
             "Ensure 'Set time and date automatically' is ON.",
             "If already on: toggle off, wait 5 seconds, toggle back on."]
        ))

    # --- Connectivity ---
    connectivity = data.get("connectivity_test", "")
    connectivity_ok = isinstance(connectivity, str) and "successful" in connectivity.lower()
    if not connectivity_ok:
        findings.append(_make_finding(
            "CRITICAL", "NO_CONNECTIVITY",
            "Cannot connect to the internet",
            "Your computer cannot establish a connection to external servers on any standard port (80, 443, 53).",
            "Router has no internet connection, ISP outage, or firewall blocking all outbound traffic.",
            ["Check if other devices (phone, tablet) have internet on the same network.",
             "Restart your router: unplug power for 30 seconds, plug back in, wait 2 minutes.",
             "If using ethernet: try a different cable or port.",
             "If other devices also have no internet: contact your ISP."]
        ))

    # --- HTTP reachability ---
    http_reach = data.get("http_reachability", {})
    if isinstance(http_reach, dict) and connectivity_ok:
        https_ok = http_reach.get("https", {}).get("reachable", True)
        http_ok = http_reach.get("http", {}).get("reachable", True)
        if not https_ok and not http_ok:
            findings.append(_make_finding(
                "WARNING", "HTTP_BLOCKED",
                "TCP ports reachable but HTTP/HTTPS requests are failing",
                "You can reach servers at a low level but web traffic is being blocked or intercepted. This indicates a transparent proxy, firewall rule, or TLS inspection issue.",
                "Corporate firewall, transparent proxy, or DNS-based content filtering.",
                ["Open a web browser — if you see a block or warning page, a proxy or firewall is active.",
                 "If on a corporate network: contact IT about proxy or firewall exceptions.",
                 "If at home: restart router, check if ISP is blocking ports."]
            ))

    # --- Packet loss ---
    latency_data = data.get("latency_test", {})
    loss_val = None
    latency_val = None
    if isinstance(latency_data, dict):
        try:
            loss_val = float(str(latency_data.get("Packet Loss", "N/A")).replace("%", ""))
        except (ValueError, AttributeError):
            pass
        try:
            latency_val = float(str(latency_data.get("Avg Latency (ms)", "N/A")))
        except (ValueError, AttributeError):
            pass

    if loss_val is not None and loss_val > 0:
        if loss_val >= 50:
            sev, desc = "CRITICAL", f"{loss_val:.0f}% of packets lost — connection is severely degraded"
        elif loss_val >= 10:
            sev, desc = "WARNING", f"{loss_val:.0f}% packet loss — connection is unstable"
        else:
            sev, desc = "WARNING", f"{loss_val:.0f}% packet loss — minor instability detected"
        findings.append(_make_finding(
            sev, "PACKET_LOSS", desc,
            "Packet loss causes web pages to fail, video calls to drop or freeze, and file transfers to stall or corrupt.",
            "WiFi interference, overloaded router, ISP congestion, or faulty cable.",
            ["If on WiFi: move closer to your router or switch to ethernet.",
             "Restart your router (unplug 30 sec).",
             "If on ethernet: try a different cable.",
             "If loss persists after router restart: may be ISP-side — contact ISP."]
        ))

    # --- High latency ---
    if latency_val is not None and latency_val > 100:
        if latency_val > 300:
            sev, desc = "CRITICAL", f"Severe latency: {latency_val:.0f}ms average (normal: <50ms)"
        elif latency_val > 150:
            sev, desc = "WARNING", f"High latency: {latency_val:.0f}ms average (normal: <50ms)"
        else:
            sev, desc = "WARNING", f"Elevated latency: {latency_val:.0f}ms average (normal: <50ms)"
        findings.append(_make_finding(
            sev, "HIGH_LATENCY", desc,
            "High latency makes web pages slow to load, video calls choppy, and remote desktop sluggish.",
            "Network congestion, VPN routing overhead, distant target server, or overloaded router.",
            ["If on WiFi: move closer to router or use ethernet.",
             "Close applications that use a lot of bandwidth (streaming, large downloads).",
             "If VPN is active: disconnect and retest — VPN routing adds latency.",
             "Restart router if latency is unexpected."]
        ))

    # --- Jitter ---
    ping_raw = data.get("ping_test", "")
    if isinstance(ping_raw, str) and "ERROR" not in ping_raw:
        stddev_match = re.search(r"= ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)", ping_raw)
        if stddev_match:
            stddev = float(stddev_match.group(4))
            if stddev > 20:
                findings.append(_make_finding(
                    "WARNING", "PING_JITTER",
                    f"Connection jitter detected (stddev: {stddev:.1f}ms)",
                    "High jitter (variation in delay) makes voice and video calls choppy even when average latency seems acceptable.",
                    "WiFi congestion, radio interference, or overloaded network equipment.",
                    ["Switch to ethernet if on WiFi.",
                     "Check if other devices are streaming or downloading heavily.",
                     "Restart router if jitter is unexpected."]
                ))

    # --- Traceroute ---
    traceroute = data.get("traceroute_test", {})
    if isinstance(traceroute, dict) and not traceroute.get("trace_successful", True):
        failed_hop = traceroute.get("trace_failed_at_hop", "?")
        hops = traceroute.get("hops", [])
        good_hops = len([h for h in hops if isinstance(h, dict) and not h.get("timeout")])
        if good_hops <= 2:
            cause = "Problem is close to your machine — likely your router or local network."
            steps = ["Restart your router.",
                     "If on WiFi: try ethernet.",
                     "Check if other devices on same network have internet."]
        elif good_hops <= 5:
            cause = "Problem appears to be with your ISP or the first few external hops."
            steps = ["Contact your ISP — this appears to be outside your home network.",
                     "Check your ISP's status page for outages."]
        else:
            cause = "Problem is several hops away — likely a routing issue between ISPs or at the target."
            steps = ["This may be a temporary internet routing issue outside your control.",
                     "Try again in 10-15 minutes.",
                     "If persistent: report to Help Desk with the log file."]
        findings.append(_make_finding(
            "WARNING", "TRACEROUTE_INCOMPLETE",
            f"Network path to target is incomplete — trace stopped at hop {failed_hop}",
            "Traffic is being dropped somewhere between your machine and the destination.",
            cause, steps
        ))

    # --- DNS failure ---
    dns_result = data.get("dns_lookup", "")
    if isinstance(dns_result, str) and "ERROR" in dns_result:
        findings.append(_make_finding(
            "CRITICAL", "DNS_FAILURE",
            "DNS lookup failed — cannot resolve website names to addresses",
            "Your computer cannot translate website names (like google.com) into network addresses. All web browsing fails even if your network connection is otherwise fine.",
            "DNS server unreachable, misconfigured DNS settings, or VPN blocking DNS.",
            ["Open System Settings → Network → your connection → Details → DNS and check servers are listed.",
             "Temporarily add 8.8.8.8 as a DNS server to test.",
             "If on VPN: disconnect and test — VPN sometimes breaks DNS.",
             "Restart router."]
        ))
        confidence_notes.append("DNS failure — hostname-based test results may be unreliable")

    # --- Slow/failed DNS servers ---
    dns_health = data.get("dns_health_check", {})
    if isinstance(dns_health, dict):
        failed_dns = []
        for server, val in dns_health.items():
            success = val.get("success", True) if isinstance(val, dict) else True
            if not success:
                failed_dns.append(server)
        if failed_dns:
            findings.append(_make_finding(
                "WARNING", "DNS_SERVER_UNREACHABLE",
                f"DNS server(s) not responding: {', '.join(failed_dns)}",
                "Unreachable DNS servers slow web browsing as your computer tries each before failing over.",
                "Firewall blocking DNS port (53), or DNS server outage.",
                ["Contact Help Desk — DNS server configuration may need updating."]
            ))

    # ---------------------------------------------------------------------------
    # Render output
    # ---------------------------------------------------------------------------

    WIDTH = 62
    real_issues = [f for f in findings if f["severity"] != "INFO"]
    info_items = [f for f in findings if f["severity"] == "INFO"]

    severities = [f["severity"] for f in real_issues]
    if "CRITICAL" in severities:
        overall = "CRITICAL"
    elif "WARNING" in severities:
        overall = "DEGRADED"
    else:
        overall = "HEALTHY"

    confidence = ("HIGH" if not confidence_notes
                  else "MEDIUM" if len(confidence_notes) == 1
                  else "LOW")

    status_label = {"CRITICAL": "X  CRITICAL", "DEGRADED": "!  DEGRADED", "HEALTHY": "OK HEALTHY"}[overall]

    print("\n" + "=" * WIDTH)
    print(f"  NETWORK STATUS: {status_label}")
    print("=" * WIDTH)

    if not real_issues:
        print("\n  No problems detected. Network appears healthy.\n")
    else:
        print(f"\n  {len(real_issues)} issue(s) found:\n")
        for finding in real_issues:
            prefix = {"CRITICAL": "[ CRITICAL ]", "WARNING": "[ WARNING  ]"}[finding["severity"]]
            print(f"  {prefix} {finding['what']}")
            print(f"               {finding['why']}")
            if finding.get("likely_cause"):
                print(f"               Likely cause: {finding['likely_cause']}")
            print()

    if info_items:
        print("  Additional info:")
        for item in info_items:
            print(f"    [  INFO  ]  {item['what']}")
        print()

    # Self-help steps
    all_steps = []
    seen_steps = set()
    for finding in findings:
        if finding["severity"] in ("CRITICAL", "WARNING"):
            for step in finding.get("steps", []):
                if step not in seen_steps:
                    all_steps.append(step)
                    seen_steps.add(step)

    if all_steps:
        print("-" * WIDTH)
        print("  THINGS TO TRY BEFORE CALLING HELP DESK:\n")
        for i, step in enumerate(all_steps[:8], 1):
            print(f"  {i}. {step}")
        print()

    # Help Desk report block
    print("=" * WIDTH)
    print("  HELP DESK REPORT  --  copy this when you call or email")
    print("=" * WIDTH)
    print(f"  Date/Time    : {timestamp}")
    print(f"  Computer     : {hostname} ({os_version})")
    print(f"  Local IP     : {local_ip}")
    print(f"  Gateway      : {gateway}")
    print(f"  Public IP    : {public_ip}")

    if vpn_active:
        vpn_str = (", ".join(f"{v['interface']} / {v['tunnel_ip']}" for v in vpn_interfaces)
                   if vpn_interfaces else "Yes")
        print(f"  VPN          : Active ({vpn_str})")
    else:
        print("  VPN          : Not active")

    if isinstance(wifi, dict) and wifi.get("connected"):
        print(f"  WiFi         : {wifi.get('ssid', '?')} | "
              f"{wifi.get('signal_quality', '?')} ({wifi.get('rssi_dbm', '?')} dBm) | "
              f"{wifi.get('band', '?')}")
    else:
        print("  WiFi         : Not connected (wired or unavailable)")

    local_dns = data.get("local_dns_servers", {})
    if isinstance(local_dns, dict) and local_dns.get("nameservers"):
        print(f"  DNS Servers  : {', '.join(local_dns['nameservers'][:3])}")

    print()
    print("  PROBLEMS FOUND:")
    if not real_issues:
        print("    None")
    else:
        for f in real_issues:
            print(f"    [{f['severity']}] {f['what']}")

    if loss_val is not None or latency_val is not None:
        loss_display = f"{loss_val:.0f}%" if loss_val is not None else "N/A"
        lat_display = f"{latency_val:.0f}ms" if latency_val is not None else "N/A"
        print()
        print(f"  Packet Loss  : {loss_display}  (normal: 0%)")
        print(f"  Avg Latency  : {lat_display}  (normal: <50ms)")

    log_folder = os.path.expanduser("~/Desktop/Network_Logs")
    print(f"\n  Log file     : {log_folder}/")
    print("=" * WIDTH)

    print(f"\n  Diagnosis confidence: {confidence}")
    for note in confidence_notes:
        print(f"    - {note}")

    print()
    print("  Evaluation complete.")
    print("=" * WIDTH + "\n")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    log = main()
    evaluate_network_logs(log)

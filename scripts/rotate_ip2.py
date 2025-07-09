import os
import subprocess
import time
import random
import requests

# ----- Configuration -----
CONFIG_DIR = r"C:\Users\rahul.gupta\OpenVPN\config"  # Path to .ovpn files
OPENVPN_PATH = r"C:\Program Files\OpenVPN\bin\openvpn.exe"  # OpenVPN binary
WAIT_TIME = 60  # Max seconds to wait for VPN to connect
ROTATE_EVERY = 120  # Seconds between rotations
LOG_FILE = os.path.join(CONFIG_DIR, "vpn_log.txt")
# -------------------------

def disconnect_vpn():
    print("🛑 Disconnecting any running VPN...")
    subprocess.run("taskkill /F /IM openvpn.exe >nul 2>&1", shell=True)

def get_uk_ovpn_files():
    return [f for f in os.listdir(CONFIG_DIR) if f.startswith("uk") and f.endswith(".ovpn")]

def connect_vpn(config_file):
    config_path = os.path.join(CONFIG_DIR, config_file)
    print(f"🔌 Connecting to: {config_file}")

    with open(LOG_FILE, 'w') as log_file:
        process = subprocess.Popen(
            [OPENVPN_PATH, "--config", config_path],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )

    # Wait for VPN to connect
    print("⏳ Waiting for VPN to fully connect...")
    for i in range(WAIT_TIME):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                log = f.read()
                if "Initialization Sequence Completed" in log:
                    print("✅ VPN Connected Successfully.")
                    break
        time.sleep(1)
    else:
        print("❌ VPN may not have connected. Check vpn_log.txt.")

    return process

def get_public_ip():
    print("🌐 Fetching public IP addresses...")
    try:
        ip1 = requests.get("https://api.ipify.org", timeout=10).text
        ip2 = requests.get("https://ifconfig.me", timeout=10).text
        print(f"🌐 IP from api.ipify.org: {ip1}")
        print(f"🌍 IP from ifconfig.me: {ip2}")
        return ip1
    except Exception as e:
        print(f"⚠️ Could not fetch public IP. {e}")
        return None

def rotate_once():
    disconnect_vpn()
    time.sleep(5)

    uk_configs = get_uk_ovpn_files()
    if not uk_configs:
        print("❌ No UK .ovpn files found.")
        return None

    selected = random.choice(uk_configs)
    process = connect_vpn(selected)

    print("🔍 Verifying new IP...")
    time.sleep(5)
    get_public_ip()

    return process

# -------------------------
if __name__ == "__main__":
    try:
        while True:
            print("\n🔁 Rotating VPN IP...")
            vpn_process = rotate_once()
            print(f"🕒 Waiting {ROTATE_EVERY}s before next rotation...\n")
            time.sleep(ROTATE_EVERY)
    except KeyboardInterrupt:
        disconnect_vpn()
        print("🛑 Exited by user.")

import os
import subprocess
import time
import random
import requests
import tempfile

# ----- Configuration -----
CONFIG_DIR = r"C:\Users\rahul.gupta\OpenVPN\config"  # Path to .ovpn files
OPENVPN_PATH = r"C:\Program Files\OpenVPN\bin\openvpn.exe"  # OpenVPN binary
WAIT_TIME = 60  # Max seconds to wait for VPN to connect
ROTATE_EVERY = 120  # Seconds between rotations
LOG_FILE = os.path.join(CONFIG_DIR, "vpn_log.txt")

# ProtonVPN credentials - set these environment variables or modify here
PROTONVPN_USERNAME = os.getenv('PROTONVPN_USERNAME', 'UsQoNw8ds1RLCUeH')
PROTONVPN_PASSWORD = os.getenv('PROTONVPN_PASSWORD', '7L7MKzkLnMc84tiaNZJNvmkapyDJ7cco')
# -------------------------

def disconnect_vpn():
    print("🛑 Disconnecting any running VPN...")
    subprocess.run("taskkill /F /IM openvpn.exe >nul 2>&1", shell=True)

def get_uk_ovpn_files():
    return [f for f in os.listdir(CONFIG_DIR) if f.startswith("uk") and f.endswith(".ovpn")]

def create_temp_auth_file():
    """Create a temporary auth file with credentials"""
    temp_auth = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
    temp_auth.write(f"{PROTONVPN_USERNAME}\n{PROTONVPN_PASSWORD}")
    temp_auth.close()
    
    # Debug: Print temp file location and contents
    print(f"📁 Created temp auth file: {temp_auth.name}")
    with open(temp_auth.name, 'r') as f:
        contents = f.read()
        print(f"📄 Auth file contents (first 20 chars): {contents[:20]}...")
    
    return temp_auth.name

def connect_vpn(config_file):
    config_path = os.path.join(CONFIG_DIR, config_file)
    print(f"🔌 Connecting to: {config_file}")

    # Create temporary auth file
    temp_auth_file = create_temp_auth_file()
    
    try:
        with open(LOG_FILE, 'w') as log_file:
            # Run OpenVPN with elevated privileges and disable DCO
            process = subprocess.Popen(
                [OPENVPN_PATH, "--config", config_path, "--auth-user-pass", temp_auth_file, 
                 "--verb", "3", "--disable-dco"],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

        # Wait for VPN to connect
        print("⏳ Waiting for VPN to fully connect...")
        for i in range(WAIT_TIME):
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                    log = f.read()
                    if "Initialization Sequence Completed" in log:
                        print("✅ VPN Connected Successfully.")
                        break
                    elif "AUTH_FAILED" in log:
                        print("❌ Authentication failed. Check credentials.")
                        print("📋 Recent log entries:")
                        log_lines = log.split('\n')
                        for line in log_lines[-10:]:  # Show last 10 lines
                            if line.strip():
                                print(f"   {line}")
                        break
                    elif "RESOLVE" in log and "Cannot resolve host address" in log:
                        print("❌ DNS resolution failed. Check internet connection.")
                        break
                    elif "NETSH: command failed" in log or "ERROR: command failed" in log:
                        print("❌ Network configuration failed. Try running as administrator.")
                        break
            time.sleep(1)
        else:
            print("❌ VPN may not have connected. Check vpn_log.txt.")
            # Show some log content for debugging
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                    log = f.read()
                    print("📋 Log file contents:")
                    print(log[-500:])  # Show last 500 characters

        return process
    
    finally:
        # Clean up temporary auth file
        try:
            os.unlink(temp_auth_file)
        except:
            pass

def get_public_ip():
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
    time.sleep(10)
    get_public_ip()

    return process

# -------------------------
if __name__ == "__main__":
    try:
        print("🔍 Current IP before VPN:")
        get_public_ip()
        
        while True:
            print("\n🔁 Rotating VPN IP...")
            vpn_process = rotate_once()
            print(f"🕒 Waiting {ROTATE_EVERY}s before next rotation...\n")
            time.sleep(ROTATE_EVERY)
    except KeyboardInterrupt:
        disconnect_vpn()
        print("🛑 Exited by user.")
import os
import subprocess
import time
import random
import requests
import sys
import ctypes

# ----- Configuration -----
CONFIG_DIR = r"C:\Users\rahul.gupta\OpenVPN\config"  # Path to .ovpn files
OPENVPN_PATH = r"C:\Program Files\OpenVPN\bin\openvpn.exe"  # OpenVPN binary
WAIT_TIME = 60  # Max seconds to wait for VPN to connect
ROTATE_EVERY = 10  # Seconds between rotations
LOG_FILE = os.path.join(CONFIG_DIR, "vpn_log.txt")
# -------------------------

def is_admin():
    """Check if the script is running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Restart the script with administrator privileges"""
    if is_admin():
        return True
    else:
        print("Script requires administrator privileges to manage VPN connections.")
        print("Attempting to restart with administrator privileges...")
        try:
            # Re-run the script with admin privileges
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return False
        except Exception as e:
            print(f"Failed to restart with admin privileges: {e}")
            print("Please manually run this script as administrator.")
            return False

def disconnect_vpn():
    """Disconnect any running VPN connections"""
    print("Disconnecting any running VPN...")
    # Kill OpenVPN processes
    subprocess.run("taskkill /F /IM openvpn.exe >nul 2>&1", shell=True)
    time.sleep(2)
    
    # Also try to disconnect using OpenVPN's management interface if available
    try:
        subprocess.run("netsh interface set interface \"OpenVPN TAP-Windows6\" disable", 
                      shell=True, capture_output=True)
    except:
        pass

def get_uk_ovpn_files():
    """Get list of UK OpenVPN configuration files"""
    try:
        return [f for f in os.listdir(CONFIG_DIR) if f.startswith("uk") and f.endswith(".ovpn")]
    except FileNotFoundError:
        print(f"Configuration directory not found: {CONFIG_DIR}")
        return []

def connect_vpn(config_file):
    """Connect to VPN using specified configuration file"""
    config_path = os.path.join(CONFIG_DIR, config_file)
    
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}")
        return None
    
    print(f"Connecting to: {config_file}")
    
    try:
        # Clear previous log
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
        
        # Start OpenVPN with elevated privileges
        with open(LOG_FILE, 'w') as log_file:
            process = subprocess.Popen(
                [OPENVPN_PATH, "--config", config_path, "--log", LOG_FILE],
                stdout=log_file,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        
        # Wait for VPN to connect
        print("Waiting for VPN to fully connect...")
        connected = False
        
        for i in range(WAIT_TIME):
            if os.path.exists(LOG_FILE):
                try:
                    with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                        log = f.read()
                        if "Initialization Sequence Completed" in log:
                            print("VPN Connected Successfully.")
                            connected = True
                            break
                        elif "FATAL" in log or "fatal error" in log:
                            print("VPN connection failed with fatal error.")
                            break
                        elif "AUTH_FAILED" in log:
                            print("VPN authentication failed.")
                            break
                except Exception as e:
                    pass
            
            time.sleep(1)
            if i % 10 == 0 and i > 0:
                print(f"Still waiting... ({i}/{WAIT_TIME}s)")
        
        if not connected:
            print("VPN may not have connected. Check vpn_log.txt for details.")
            if os.path.exists(LOG_FILE):
                print("Last few lines of log:")
                try:
                    with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        for line in lines[-5:]:
                            print(f"   {line.strip()}")
                except:
                    pass
        
        return process
    
    except Exception as e:
        print(f"Error starting VPN: {e}")
        return None

def get_public_ip():
    """Fetch and display current public IP address"""
    print("Fetching public IP addresses...")
    try:
        # Try multiple IP services for reliability
        services = [
            "https://api.ipify.org",
            "https://ifconfig.me",
            "https://icanhazip.com",
            "https://ipinfo.io/ip"
        ]
        
        ips = []
        for service in services:
            try:
                response = requests.get(service, timeout=10)
                ip = response.text.strip()
                if ip:
                    ips.append((service, ip))
                    print(f"IP from {service}: {ip}")
            except Exception as e:
                print(f"Failed to get IP from {service}: {e}")

        if ips:
            return ips[0][1]  # Return first successful IP
        else:
            print("Could not fetch public IP from any service.")
            return None
            
    except Exception as e:
        print(f"Error fetching public IP: {e}")
        return None

def test_connection():
    """Test internet connectivity"""
    try:
        response = requests.get("https://www.google.com", timeout=10)
        if response.status_code == 200:
            print("Internet connection is working.")
            return True
    except:
        pass

    print("No internet connection detected.")
    return False

def rotate_once():
    """Perform one VPN rotation"""
    # Disconnect current VPN
    disconnect_vpn()
    time.sleep(5)
    
    # Get available UK configurations
    uk_configs = get_uk_ovpn_files()
    if not uk_configs:
        print("No UK .ovpn files found in the configuration directory.")
        print(f"Please check: {CONFIG_DIR}")
        return None

    print(f"Found {len(uk_configs)} UK configurations: {', '.join(uk_configs)}")

    # Select random configuration
    selected = random.choice(uk_configs)
    print(f"Selected configuration: {selected}")

    # Connect to VPN
    process = connect_vpn(selected)
    
    if process:
        print("Verifying new connection...")
        time.sleep(5)
        
        # Test connectivity
        if test_connection():
            get_public_ip()
        else:
            print("Connection established but no internet access.")

    return process

def main():
    """Main function"""
    print("VPN IP Rotation Script Starting...")
    print("=" * 50)
    
    # Check for administrator privileges
    if not run_as_admin():
        input("Press Enter to exit...")
        return
    
    print("Running with administrator privileges.")
    
    # Verify OpenVPN installation
    if not os.path.exists(OPENVPN_PATH):
        print(f"OpenVPN not found at: {OPENVPN_PATH}")
        print("Please install OpenVPN or update the OPENVPN_PATH variable.")
        input("Press Enter to exit...")
        return
    
    # Verify configuration directory
    if not os.path.exists(CONFIG_DIR):
        print(f"Configuration directory not found: {CONFIG_DIR}")
        print("Please update the CONFIG_DIR variable to point to your .ovpn files.")
        input("Press Enter to exit...")
        return
    
    print("Configuration verified. Starting rotation...")
    print(f"Config directory: {CONFIG_DIR}")
    print(f"Rotation interval: {ROTATE_EVERY} seconds")
    print(f"Log file: {LOG_FILE}")
    print("=" * 50)
    
    try:
            rotation_count = 0
        # while True:
            rotation_count += 1
            print(f"\n VPN Rotation #{rotation_count}")
            print("-" * 30)
            
            vpn_process = rotate_once()
            
            if vpn_process:
                print(f" Waiting {ROTATE_EVERY} seconds before next rotation...")
                print("   Press Ctrl+C to stop the script.")
                time.sleep(ROTATE_EVERY)
            else:
                print("Failed to establish VPN connection. Retrying in 30 seconds...")
                time.sleep(30)
                
    except KeyboardInterrupt:
        print("\nStopping VPN rotation...")
        disconnect_vpn()
        print("Script stopped by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        disconnect_vpn()
        print("Script terminated due to error.")
    finally:
        input("Press Enter to exit...")

# -------------------------
if __name__ == "__main__":
    main()
import subprocess
import sys
import os

def install_wireguard():
    try:
        subprocess.run(['apt', 'update'], check=True)
        subprocess.run(['apt', 'install', '-y', 'wireguard'], check=True)
        print("WireGuard installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing WireGuard: {e}")
        sys.exit(1)

def generate_wireguard_keys():
    try:
        private_key = subprocess.check_output(['wg', 'genkey']).strip().decode('utf-8')
        public_key = subprocess.check_output(['wg', 'pubkey'], input=private_key.encode()).strip().decode('utf-8')
        return private_key, public_key
    except subprocess.CalledProcessError as e:
        print(f"Error generating WireGuard keys: {e}")
        sys.exit(1)

def configure_wireguard():
    server_private_key, server_public_key = generate_wireguard_keys()
    client_private_key, client_public_key = generate_wireguard_keys()

    config_content = f"""
[Interface]
Address = 10.0.0.1/24
SaveConfig = true
ListenPort = 51820
PrivateKey = {server_private_key}

[Peer]
PublicKey = {client_public_key}
AllowedIPs = 10.0.0.2/32
"""
    try:
        with open('/etc/wireguard/wg0.conf', 'w') as f:
            f.write(config_content)
        subprocess.run(['systemctl', 'start', 'wg-quick@wg0'], check=True)
        subprocess.run(['systemctl', 'enable', 'wg-quick@wg0'], check=True)
        print("WireGuard configured and started successfully.")
        
        # Configure firewall rules
        subprocess.run(['iptables', '-A', 'INPUT', '-i', 'wg0', '-p', 'tcp', '--dport', '80', '-j', 'ACCEPT'], check=True)
        subprocess.run(['iptables', '-A', 'INPUT', '-i', 'wg0', '-p', 'tcp', '--dport', '443', '-j', 'ACCEPT'], check=True)
        subprocess.run(['iptables', '-A', 'INPUT', '-p', 'tcp', '--dport', '80', '-j', 'DROP'], check=True)
        subprocess.run(['iptables', '-A', 'INPUT', '-p', 'tcp', '--dport', '443', '-j', 'DROP'], check=True)
        subprocess.run(['sh', '-c', "iptables-save > /etc/iptables/rules.v4"], check=True)
        print("Firewall rules configured successfully.")
    except Exception as e:
        print(f"Error configuring WireGuard: {e}")
        sys.exit(1)

def get_client_config():
    try:
        with open('/etc/wireguard/wg0.conf', 'r') as f:
            config = f.read()
        print("WireGuard client configuration:\n")
        print(config)
    except FileNotFoundError:
        print("WireGuard configuration file not found.")
        sys.exit(1)

def uninstall_wireguard():
    try:
        subprocess.run(['systemctl', 'stop', 'wg-quick@wg0'], check=True)
        subprocess.run(['systemctl', 'disable', 'wg-quick@wg0'], check=True)
        subprocess.run(['apt', 'remove', '-y', 'wireguard'], check=True)
        subprocess.run(['apt', 'autoremove', '-y'], check=True)
        print("WireGuard uninstalled successfully.")
        
        # Restore firewall rules
        subprocess.run(['iptables', '-D', 'INPUT', '-i', 'wg0', '-p', 'tcp', '--dport', '80', '-j', 'ACCEPT'], check=True)
        subprocess.run(['iptables', '-D', 'INPUT', '-i', 'wg0', '-p', 'tcp', '--dport', '443', '-j', 'ACCEPT'], check=True)
        subprocess.run(['iptables', '-D', 'INPUT', '-p', 'tcp', '--dport', '80', '-j', 'DROP'], check=True)
        subprocess.run(['iptables', '-D', 'INPUT', '-p', 'tcp', '--dport', '443', '-j', 'DROP'], check=True)
        subprocess.run(['sh', '-c', "iptables-save > /etc/iptables/rules.v4"], check=True)
        print("Firewall rules restored successfully.")
    except Exception as e:
        print(f"Error uninstalling WireGuard: {e}")
        sys.exit(1)

def wireguard_menu():
    while True:
        print("WireGuard Configuration")
        print("1. Configure WireGuard")
        print("2. Get Client Configuration")
        print("3. Uninstall WireGuard")
        print("4. Back to main menu")

        choice = input("Enter your choice: ")

        if choice == '1':
            install_wireguard()
            configure_wireguard()
        elif choice == '2':
            get_client_config()
        elif choice == '3':
            uninstall_wireguard()
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Please run this script with sudo.")
        sys.exit(1)
    wireguard_menu()

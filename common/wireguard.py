import os
import subprocess
import sys
import socket

def get_server_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

def generate_keys():
    private_key = subprocess.run(['wg', 'genkey'], check=True, stdout=subprocess.PIPE).stdout.decode().strip()
    public_key = subprocess.run(['wg', 'pubkey'], input=private_key.encode(), check=True, stdout=subprocess.PIPE).stdout.decode().strip()
    return private_key, public_key

def install_wireguard():
    print("Installing WireGuard...")
    try:
        subprocess.run(['apt-get', 'update'], check=True)
        subprocess.run(['apt-get', 'install', '-y', 'wireguard'], check=True)
        print("WireGuard installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing WireGuard: {e}")
        sys.exit(1)

def uninstall_wireguard():
    print("Uninstalling WireGuard...")
    try:
        subprocess.run(['apt-get', 'remove', '-y', 'wireguard'], check=True)
        subprocess.run(['apt-get', 'autoremove', '-y'], check=True)
        print("WireGuard uninstalled successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error uninstalling WireGuard: {e}")
        sys.exit(1)

def get_configuration():
    ip_address = get_server_ip()
    private_key, public_key = generate_keys()
    config = f"""
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = {private_key}

[Peer]
PublicKey = {public_key}
AllowedIPs = 0.0.0.0/0
Endpoint = {ip_address}:51820
    """
    return config

def get_configuration_qr(config):
    try:
        qr_code = subprocess.run(['qrencode', '-t', 'ansiutf8', config], check=True, stdout=subprocess.PIPE).stdout.decode()
        return qr_code
    except subprocess.CalledProcessError as e:
        print(f"Error generating QR Code: {e}")
        sys.exit(1)

def save_configuration(config, filename='/etc/wireguard/wg0.conf'):
    try:
        with open(filename, 'w') as f:
            f.write(config)
        subprocess.run(['chmod', '600', filename], check=True)
    except Exception as e:
        print(f"Error saving configuration: {e}")
        sys.exit(1)

def wireguard_menu():
    while True:
        print("\nWireGuard Management")
        print("1. Install VPS Service")
        print("2. Uninstall VPS Service")
        print("3. Get Configuration")
        print("4. Get Configuration (QR Code)")
        print("0. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            install_wireguard()
        elif choice == '2':
            uninstall_wireguard()
        elif choice == '3':
            config = get_configuration()
            print(config)
            save_config = input("Do you want to save this configuration to /etc/wireguard/wg0.conf? [y/n]: ")
            if save_config.lower() == 'y':
                save_configuration(config)
        elif choice == '4':
            config = get_configuration()
            qr_code = get_configuration_qr(config)
            print("Scan the following QR Code with your WireGuard app:")
            print(qr_code)
            save_config = input("Do you want to save this configuration to /etc/wireguard/wg0.conf? [y/n]: ")
            if save_config.lower() == 'y':
                save_configuration(config)
        elif choice == '0':
            sys.exit()
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Please run this script with sudo.")
        sys.exit(1)
    wireguard_menu()

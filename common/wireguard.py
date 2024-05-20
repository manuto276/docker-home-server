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
        subprocess.run(['apt-get', 'install', '-y', 'wireguard', 'qrencode'], check=True)
        print("WireGuard installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing WireGuard: {e}")
        sys.exit(1)
    configure_wireguard()

def uninstall_wireguard():
    print("Uninstalling WireGuard...")
    try:
        subprocess.run(['apt-get', 'remove', '-y', 'wireguard'], check=True)
        subprocess.run(['apt-get', 'autoremove', '-y'], check=True)
        print("WireGuard uninstalled successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error uninstalling WireGuard: {e}")
        sys.exit(1)

def get_server_configuration():
    ip_address = get_server_ip()
    private_key, public_key = generate_keys()
    config = f"""
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = {private_key}

# Add peer configurations below
    """
    return config, private_key, public_key

def get_peer_configuration(server_public_key, server_ip, peer_ip, peer_num):
    private_key, public_key = generate_keys()
    config = f"""
[Peer]
PublicKey = {public_key}
AllowedIPs = {peer_ip}/32
PersistentKeepalive = 25
    """
    peer_config = f"""
[Interface]
Address = {peer_ip}/24
PrivateKey = {private_key}

[Peer]
PublicKey = {server_public_key}
AllowedIPs = 0.0.0.0/0
Endpoint = {server_ip}:51820
PersistentKeepalive = 25
    """
    return config, peer_config

def save_configuration(config, filename):
    try:
        with open(filename, 'w') as f:
            f.write(config)
        subprocess.run(['chmod', '600', filename], check=True)
    except Exception as e:
        print(f"Error saving configuration: {e}")
        sys.exit(1)

def configure_wireguard():
    server_config, server_private_key, server_public_key = get_server_configuration()
    num_peers = int(input("Enter the number of peers: "))

    for i in range(1, num_peers + 1):
        peer_ip = f"10.0.0.{i + 1}"
        peer_config, peer_config_full = get_peer_configuration(server_public_key, get_server_ip(), peer_ip, i)
        server_config += peer_config
        peer_filename = f"/etc/wireguard/peer{i}.conf"
        save_configuration(peer_config_full, peer_filename)
        print(f"Configuration for peer {i} saved to {peer_filename}")
        qr_code = subprocess.run(['qrencode', '-t', 'ansiutf8', peer_config_full], check=True, stdout=subprocess.PIPE).stdout.decode()
        print(f"QR Code for peer {i}:\n{qr_code}")

    save_configuration(server_config, '/etc/wireguard/wg0.conf')
    print("Server configuration saved to /etc/wireguard/wg0.conf")

def wireguard_menu():
    while True:
        print("\nWireGuard Management")
        print("1. Install VPS Service")
        print("2. Uninstall VPS Service")
        print("3. Get Server Configuration")
        print("4. Get Server Configuration (QR Code)")
        print("0. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            install_wireguard()
        elif choice == '2':
            uninstall_wireguard()
        elif choice == '3':
            with open('/etc/wireguard/wg0.conf', 'r') as f:
                print(f.read())
        elif choice == '4':
            with open('/etc/wireguard/wg0.conf', 'r') as f:
                server_config = f.read()
            qr_code = subprocess.run(['qrencode', '-t', 'ansiutf8', server_config], check=True, stdout=subprocess.PIPE).stdout.decode()
            print("Scan the following QR Code with your WireGuard app:")
            print(qr_code)
        elif choice == '0':
            sys.exit()
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Please run this script with sudo.")
        sys.exit(1)
    wireguard_menu()

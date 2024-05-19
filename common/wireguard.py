import subprocess
import sys

def generate_wireguard_config():
    # Generate WireGuard server and client keys
    server_private_key = subprocess.run(['wg', 'genkey'], stdout=subprocess.PIPE, check=True).stdout.decode().strip()
    server_public_key = subprocess.run(['echo', server_private_key, '|', 'wg', 'pubkey'], stdout=subprocess.PIPE, shell=True, check=True).stdout.decode().strip()

    client_private_key = subprocess.run(['wg', 'genkey'], stdout=subprocess.PIPE, check=True).stdout.decode().strip()
    client_public_key = subprocess.run(['echo', client_private_key, '|', 'wg', 'pubkey'], stdout=subprocess.PIPE, shell=True, check=True).stdout.decode().strip()

    # Generate a basic WireGuard configuration for the client
    config = f"""
[Interface]
PrivateKey = {client_private_key}
Address = 10.0.0.2/24
DNS = 8.8.8.8

[Peer]
PublicKey = {server_public_key}
Endpoint = YOUR_SERVER_IP:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 21
"""

    print(config)

    return config

def print_wireguard_qr(config):
    # Print QR code using qrencode
    subprocess.run(['qrencode', '-t', 'ANSIUTF8', config], check=True)

def wireguard_menu():
    while True:
        print("WireGuard Configuration")
        print("1. Generate WireGuard QR")
        print("2. Back to main menu")

        choice = input("Enter your choice: ")

        if choice == '1':
            config = generate_wireguard_config()
            print("WireGuard configuration:")
            print(config)
            print("Generating QR code...")
            print_wireguard_qr(config)
        elif choice == '2':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Please run this script with sudo.")
        sys.exit(1)
    wireguard_menu()

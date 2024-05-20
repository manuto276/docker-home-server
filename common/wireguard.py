import subprocess
import os
import sys

WG_CONFIG_PATH = "/etc/wireguard"
WG_SERVER_CONFIG = f"{WG_CONFIG_PATH}/wg0.conf"
WG_SERVER_PORT = 51820  # Porta classica di WireGuard
CLIENT_SUBNET = "10.0.0.2/32"

def check_sudo():
    if os.geteuid() != 0:
        print("This script must be run as root.")
        sys.exit(1)

def run_command(command):
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Command '{command}' failed with error: {e}")

def get_server_ip():
    ip_address = subprocess.run(['hostname', '-I'], stdout=subprocess.PIPE).stdout.decode().strip().split()[0]
    return ip_address

def install_wireguard():
    print("Installing WireGuard...")
    run_command('apt-get update')
    run_command('apt-get install -y wireguard wireguard-tools qrencode')
    print("WireGuard installed successfully.")

    # Configura WireGuard Server
    server_ip = get_server_ip()
    client_ip = CLIENT_SUBNET

    # Genera chiavi del server se non presenti
    if not os.path.exists(f"{WG_CONFIG_PATH}/server_private.key"):
        server_private_key = subprocess.check_output('wg genkey', shell=True).decode('utf-8').strip()
        server_public_key = subprocess.check_output(f'echo {server_private_key} | wg pubkey', shell=True).decode('utf-8').strip()
        with open(f"{WG_CONFIG_PATH}/server_private.key", 'w') as f:
            f.write(server_private_key)
        with open(f"{WG_CONFIG_PATH}/server_public.key", 'w') as f:
            f.write(server_public_key)
    else:
        with open(f"{WG_CONFIG_PATH}/server_private.key", 'r') as f:
            server_private_key = f.read().strip()
        with open(f"{WG_CONFIG_PATH}/server_public.key", 'r') as f:
            server_public_key = f.read().strip()

    # Genera chiavi client
    client_private_key, client_public_key = generate_keys()

    # Crea configurazione del server
    create_server_config(server_ip, WG_SERVER_PORT, server_private_key, client_public_key, client_ip)
    
    # Crea configurazione del client
    client_config = create_client_config(client_private_key, server_public_key, server_ip, WG_SERVER_PORT, client_ip)
    client_config_path = save_client_config(client_config)

    # Genera QR code
    generate_qr_code(client_config_path)

def uninstall_wireguard():
    print("Uninstalling WireGuard...")
    run_command('systemctl stop wg-quick@wg0')
    run_command('systemctl disable wg-quick@wg0')
    run_command('apt-get remove -y wireguard wireguard-tools')
    run_command('apt-get autoremove -y')
    print("WireGuard uninstalled successfully.")

def generate_keys():
    client_private_key = subprocess.check_output('wg genkey', shell=True).decode('utf-8').strip()
    client_public_key = subprocess.check_output(f'echo {client_private_key} | wg pubkey', shell=True).decode('utf-8').strip()
    with open(f"{WG_CONFIG_PATH}/client_private.key", 'w') as f:
        f.write(client_private_key)
    with open(f"{WG_CONFIG_PATH}/client_public.key", 'w') as f:
        f.write(client_public_key)
    return client_private_key, client_public_key

def create_server_config(server_ip, server_port, server_private_key, client_public_key, client_ip):
    server_config = f"""
[Interface]
Address = 10.0.0.1/24
ListenPort = {server_port}
PrivateKey = {server_private_key}
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE; iptables -A FORWARD -o %i -j ACCEPT; iptables -A INPUT -p udp --dport {server_port} -j ACCEPT
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE; iptables -D FORWARD -o %i -j ACCEPT; iptables -D INPUT -p udp --dport {server_port} -j ACCEPT

[Peer]
PublicKey = {client_public_key}
AllowedIPs = {client_ip}
"""
    with open(WG_SERVER_CONFIG, 'w') as f:
        f.write(server_config)
    run_command('systemctl enable wg-quick@wg0')
    run_command('systemctl start wg-quick@wg0')

def create_client_config(client_private_key, server_public_key, server_ip, server_port, client_ip):
    client_config = f"""
[Interface]
Address = {client_ip}
PrivateKey = {client_private_key}
DNS = 1.1.1.1

[Peer]
PublicKey = {server_public_key}
Endpoint = {server_ip}:{server_port}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
    return client_config

def save_client_config(config):
    client_config_path = f"{WG_CONFIG_PATH}/client.conf"
    with open(client_config_path, 'w') as f:
        f.write(config)
    return client_config_path

def generate_qr_code(client_config_path):
    qr_code_path = client_config_path + ".png"
    run_command(f"qrencode -t png -o {qr_code_path} < {client_config_path}")
    print(f"QR code generated and saved as {qr_code_path}.")

def main_menu():
    check_sudo()

    while True:
        print("\nVPN Management Menu")
        print("1. Install WireGuard")
        print("2. Uninstall WireGuard")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            install_wireguard()
        elif choice == '2':
            uninstall_wireguard()
        elif choice == '3':
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main_menu()

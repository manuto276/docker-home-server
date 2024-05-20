import subprocess
import sys

def get_wireguard_config_from_container(container_name):
    # Verifica l'installazione di qrencode, in caso contrario installalo
    try:
        subprocess.run(['qrencode', '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        print("qrencode is not installed.")
        try:
            subprocess.run(['apt', 'install', '-y', 'qrencode'], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error installing qrencode: {e}")
            sys.exit(1)

    # Copia il file di configurazione dal container Docker al sistema host
    config_path = "/config/peer1/peer1.conf"  # Percorso della configurazione WireGuard nel container
    local_config_path = "/tmp/peer1.conf"

    try:
        subprocess.run(['docker', 'cp', f'{container_name}:{config_path}', local_config_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error copying file from container: {e}")
        sys.exit(1)

    # Leggi il contenuto del file di configurazione
    try:
        with open(local_config_path, 'r') as file:
            config = file.read()
    except FileNotFoundError:
        print("Configuration file not found.")
        sys.exit(1)

    return config

def print_wireguard_qr(config):
    # Print QR code using qrencode
    subprocess.run(['qrencode', '-t', 'ANSIUTF8'], input=config.encode(), check=True)

def wireguard_menu():
    while True:
        print("WireGuard Configuration")
        print("1. Generate WireGuard QR")
        print("2. Back to main menu")

        choice = input("Enter your choice: ")

        if choice == '1':
            container_name = "wireguard"  # Nome del container Docker WireGuard
            config = get_wireguard_config_from_container(container_name)
            print("WireGuard configuration:")
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

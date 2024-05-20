import os
import sys
from common import install, uninstall, mysql, nextcloud, wireguard, dnsmasq

def main_menu():
    while True:
        print("Docker Home Server Setup")
        print("1. Install Docker Server")
        print("2. Uninstall Docker Server")
        print("3. Configure MySQL")
        print("4. Configure Nextcloud")
        print("5. WireGuard Configuration")
        print("6. dnsmasq Configuration")
        print("7. Exit")
        
        choice = input("Enter your choice: ")

        if choice == '1':
            install.install_server()
        elif choice == '2':
            uninstall.uninstall_server()
        elif choice == '3':
            mysql.configure_mysql()
        elif choice == '4':
            nextcloud.configure_nextcloud()
        elif choice == '5':
            wireguard.wireguard_menu()
        elif choice == '6':
            dnsmasq.dnsmasq_menu()
        elif choice == '7':
            sys.exit()
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Please run this script with sudo.")
        sys.exit(1)
    main_menu()

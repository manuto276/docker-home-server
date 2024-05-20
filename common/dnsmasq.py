import subprocess
import sys
import os

def install_dnsmasq():
    try:
        subprocess.run(['apt', 'update'], check=True)
        subprocess.run(['apt', 'install', '-y', 'dnsmasq'], check=True)
        print("dnsmasq installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dnsmasq: {e}")
        sys.exit(1)

def configure_dnsmasq():
    domain = input("Enter the domain (e.g., example.it): ").strip()
    dnsmasq_config = f"""
address=/{domain}/127.0.0.1
"""
    try:
        with open('/etc/dnsmasq.conf', 'a') as f:
            f.write(dnsmasq_config)
        subprocess.run(['systemctl', 'restart', 'dnsmasq'], check=True)
        subprocess.run(['systemctl', 'enable', 'dnsmasq'], check=True)
        print("dnsmasq configured and started successfully.")
    except Exception as e:
        print(f"Error configuring dnsmasq: {e}")
        sys.exit(1)

def uninstall_dnsmasq():
    try:
        subprocess.run(['systemctl', 'stop', 'dnsmasq'], check=True)
        subprocess.run(['systemctl', 'disable', 'dnsmasq'], check=True)
        subprocess.run(['apt', 'remove', '-y', 'dnsmasq'], check=True)
        subprocess.run(['apt', 'autoremove', '-y'], check=True)
        print("dnsmasq uninstalled successfully.")
    except Exception as e:
        print(f"Error uninstalling dnsmasq: {e}")
        sys.exit(1)

def dnsmasq_menu():
    while True:
        print("dnsmasq Configuration")
        print("1. Configure dnsmasq")
        print("2. Uninstall dnsmasq")
        print("3. Back to main menu")

        choice = input("Enter your choice: ")

        if choice == '1':
            install_dnsmasq()
            configure_dnsmasq()
        elif choice == '2':
            uninstall_dnsmasq()
        elif choice == '3':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Please run this script with sudo.")
        sys.exit(1)
    dnsmasq_menu()

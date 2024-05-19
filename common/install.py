import os
import shutil
import subprocess
import sys
from common import mysql

def load_default_config():
    config = {}
    with open(os.path.join(os.path.dirname(__file__), '../config/default.conf')) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                config[key] = value.strip('"')
    return config

def install_docker():
    # Controlla se Docker è già installato
    if shutil.which('docker') is None:
        # Installa Docker e Docker Compose dalle repository ufficiali
        subprocess.run(['apt', 'update'], check=True)
        subprocess.run(['apt', 'install', '-y', 'docker.io', 'docker-compose'], check=True)
        # Aggiunge l'utente corrente al gruppo docker
        subprocess.run(['usermod', '-aG', 'docker', os.getlogin()], check=True)
        # Avvia il servizio Docker
        subprocess.run(['systemctl', 'start', 'docker'], check=True)
        # Abilita il servizio Docker all'avvio
        subprocess.run(['systemctl', 'enable', 'docker'], check=True)

def create_directories(config):
    directories = [
        config['NGINX_CONF_DIR'], config['NGINX_CERTS_DIR'], config['NGINX_VHOST_DIR'],
        config['WIREGUARD_CONFIG_DIR'], config['GITLAB_CONFIG_DIR'], config['GITLAB_LOGS_DIR'],
        config['GITLAB_DATA_DIR'], config['MYSQL_DATA_DIR'], config['NEXTCLOUD_DATA_DIR']
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def replace_placeholders(config, src, dst):
    for subdir, _, files in os.walk(src):
        for file in files:
            file_path = os.path.join(subdir, file)
            with open(file_path) as f:
                content = f.read()
            for key, value in config.items():
                content = content.replace(f'__{key}__', value)
            dest_path = os.path.join(dst, os.path.relpath(file_path, src))
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, 'w') as f:
                f.write(content)

def build_docker_containers(temp_dir):
    subprocess.run(['docker-compose', 'up', '-d'], cwd=temp_dir, check=True)

def stop_docker_containers(temp_dir):
    subprocess.run(['docker-compose', 'down'], cwd=temp_dir, check=True)

def cleanup_docker_containers():
    # Prune Docker system
    subprocess.run(['docker', 'system', 'prune', '-f'], check=True)

    # Prune Docker images
    subprocess.run(['docker', 'image', 'prune', '-f'], check=True)

def save_config(config):
    # Save the configuration to /etc/docker-home-server/config

    # Check if the directory /etc/docker-home-server exists
    if not os.path.exists('/etc/docker-home-server'):
        os.makedirs('/etc/docker-home-server')

    # Write the configuration to /etc/docker-home-server/config
    with open('/etc/docker-home-server/config.conf', 'w') as f:
        for key, value in config.items():
            f.write(f'{key}={value}\n')
    
    # Change the owner of the configuration file to root
    subprocess.run(['chown', 'root:root', '/etc/docker-home-server/config.conf'], check=True)

    # Change the permissions of the configuration file to 600
    subprocess.run(['chmod', '600', '/etc/docker-home-server/config.conf'], check=True)

def load_config():
    # Load the configuration from /etc/docker-home-server/config

    # Check if the configuration file exists
    if not os.path.exists('/etc/docker-home-server/config.conf'):
        return None

    config = {}
    with open('/etc/docker-home-server/config.conf') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                config[key] = value.strip('"')
    return config

def generate_ssl_certificate(domain):
    # Generate an SSL certificate
    ssl_dir = '/etc/ssl/certs'
    if not os.path.exists(ssl_dir):
        os.makedirs(ssl_dir)
    
    # Check if the SSL certificate already exists
    if os.path.exists(f'{ssl_dir}/{domain}.crt') and os.path.exists(f'{ssl_dir}/{domain}.key'):
        recreate_certificate = input("The SSL certificate already exists. Do you want to recreate it? [y/n]: ")
        if recreate_certificate.lower() != 'y':
            return

    subprocess.run([
        'openssl', 'req', '-x509', '-nodes', '-days', '365', '-newkey', 'rsa:2048', 
        '-keyout', f'{ssl_dir}/{domain}.key', 
        '-out', f'{ssl_dir}/{domain}.crt', 
        '-subj', f'/CN={domain}'
    ], check=True)

def configure_ports():
    # Configure the ports to be used by the services
    # Enable the firewall and allow ports for SSH and VPN.
    # Close all other ports by default.
    subprocess.run(['ufw', 'default', 'deny'], check=True)

    subprocess.run(['ufw', 'allow', '22'], check=True)
    subprocess.run(['ufw', 'allow', '51820/udp'], check=True)
    subprocess.run(['ufw', 'enable'], check=True)

def install_server():
    # Load the default configuration and the previous configuration, then join them by giving priority to the previous configuration
    print("Loading default configuration...")
    config = load_default_config()
    previous_config = load_config()

    if previous_config is not None:
        config.update(previous_config)
    
    print("Installing Docker and Docker Compose...")
    install_docker()
    
    print("Creating necessary directories...")
    create_directories(config)
    
    # Asking the user for the configuration values
    # Get the IP address of the server (eg. 57.18.21.0)
    ip_address = subprocess.run(['hostname', '-I'], stdout=subprocess.PIPE).stdout.decode().strip().split()[0]
    config['SERVERIP'] = ip_address

    # Asking for the IP address (use the generated IP address if available)
    ip_address = input(f"Enter the server IP address [{ip_address}]: ")
    if ip_address:
        config['SERVERIP'] = ip_address

    # Asking for the domain name
    domain = input(f"Enter the domain name [{config['BASE_DOMAIN']}]: ")
    if domain:
        config['BASE_DOMAIN'] = domain
        config['GITLAB_DOMAIN'] = f"gitlab.{domain}"
        config['NEXTCLOUD_DOMAIN'] = f"cloud.{domain}"
        config['WIREGUARD_DOMAIN'] = f"vpn.{domain}"
        config['PHPMYADMIN_DOMAIN'] = f"phpmyadmin.{domain}"

    # Asking for the WireGuard server port
    wireguard_port = input(f"Enter the WireGuard server port [{config['SERVERPORT']}]: ")
    if wireguard_port:
        config['SERVERPORT'] = wireguard_port
        
    # Asking for email address
    email = input(f"Enter the email address [{config['EMAIL']}]: ")
    if email:
        config['EMAIL'] = email
    
    # Asking for the MySQL root password
    mysql_root_password = input(f"Enter the MySQL root password [{config['MYSQL_ROOT_PASSWORD']}]: ")
    if mysql_root_password:
        config['MYSQL_ROOT_PASSWORD'] = mysql_root_password

    # Asking if user wants to create a MySQL user
    create_mysql_user = input("Do you want to create a MySQL user? [y/n]: ")
    if create_mysql_user.lower() == 'y':
        # Asking for the MySQL user
        mysql_user = input(f"Enter the MySQL user [{config['MYSQL_USER']}]: ")
        if mysql_user:
            config['MYSQL_USER'] = mysql_user

        # Asking for the MySQL user password
        mysql_password = input(f"Enter the MySQL user password [{config['MYSQL_PASSWORD']}]: ")
        if mysql_password:
            config['MYSQL_PASSWORD'] = mysql_password

    # Asking if user wants to create a default MySQL database
    create_mysql_database = input("Do you want to create a default MySQL database? [y/n]: ")
    if create_mysql_database.lower() == 'y':
        # Asking for the MySQL database name
        mysql_database = input(f"Enter the MySQL database name [{config['MYSQL_DATABASE']}]: ")
        if mysql_database:
            config['MYSQL_DATABASE'] = mysql_database

    # Asking if user wants to create a Nextcloud user
    create_nextcloud_user = input("Do you want to create a Nextcloud user? [y/n]: ")
    if create_nextcloud_user.lower() == 'y':
        # Asking for the Nextcloud admin password
        nextcloud_password = input(f"Enter the Nextcloud admin password [{config['NEXTCLOUD_PASSWORD']}]: ")
        if nextcloud_password:
            config['NEXTCLOUD_PASSWORD'] = nextcloud_password

    # Generate SSL certificates
    print("Generating SSL certificates...")
    generate_ssl_certificate(config['BASE_DOMAIN'])
    generate_ssl_certificate(config['GITLAB_DOMAIN'])
    generate_ssl_certificate(config['NEXTCLOUD_DOMAIN'])
    generate_ssl_certificate(config['WIREGUARD_DOMAIN'])
    generate_ssl_certificate(config['PHPMYADMIN_DOMAIN'])
    
    temp_dir = '/tmp/docker-home-server'
    print(f"Copying src/ to {temp_dir}...")
    shutil.copytree('src', temp_dir, dirs_exist_ok=True)
    
    print("Replacing placeholders with configuration values...")
    replace_placeholders(config, temp_dir, temp_dir)

    print("Stopping Docker containers (if any)...")
    stop_docker_containers(temp_dir)

    print("Cleaning up Docker containers...")
    cleanup_docker_containers()
    
    print("Building Docker containers...")
    build_docker_containers(temp_dir)

    if create_mysql_database.lower() == 'y':
        print("Creating MySQL database...")
        mysql.create_mysql_database(config)

    if create_mysql_user.lower() == 'y':
        print("Creating MySQL user...")
        mysql.create_mysql_user(config)

    print("Configuring ports...")
    configure_ports()

    print("Cleaning up temporary files...")
    shutil.rmtree(temp_dir)

    print("Saving configuration...")
    save_config(config)
    
    print("Docker Home Server installation completed.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Please run this script with sudo.")
        sys.exit(1)
    install_server()

import os
import shutil
import subprocess
import sys

def load_default_config():
    config = {}
    with open('config/config.default') as f:
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

def generate_wireguard_keys():
    # Generate the WireGuard server keys
    server_private_key = subprocess.run(['wg', 'genkey'], stdout=subprocess.PIPE, check=True).stdout.decode().strip()
    server_public_key = subprocess.run(['echo', server_private_key, '|', 'wg', 'pubkey'], stdout=subprocess.PIPE, check=True).stdout.decode().strip()

    # Generate the WireGuard client keys
    client_private_key = subprocess.run(['wg', 'genkey'], stdout=subprocess.PIPE, check=True).stdout.decode().strip()
    client_public_key = subprocess.run(['echo', client_private_key, '|', 'wg', 'pubkey'], stdout=subprocess.PIPE, check=True).stdout.decode().strip()

    return server_private_key, server_public_key, client_private_key, client_public_key

def generate_ssl_certificate(domain):
    # Generate an SSL certificate
    ssl_dir = '/etc/ssl/certs'
    if not os.path.exists(ssl_dir):
        os.makedirs(ssl_dir)
    
    subprocess.run([
        'openssl', 'req', '-x509', '-nodes', '-days', '365', '-newkey', 'rsa:2048', 
        '-keyout', f'{ssl_dir}/{domain}.key', 
        '-out', f'{ssl_dir}/{domain}.crt', 
        '-subj', f'/CN={domain}'
    ], check=True)

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

    # Asking for the MySQL database name
    mysql_database = input(f"Enter the MySQL database name [{config['MYSQL_DATABASE']}]: ")
    if mysql_database:
        config['MYSQL_DATABASE'] = mysql_database

    # Asking for the MySQL user
    mysql_user = input(f"Enter the MySQL user [{config['MYSQL_USER']}]: ")
    if mysql_user:
        config['MYSQL_USER'] = mysql_user

    # Asking for the MySQL user password
    mysql_password = input(f"Enter the MySQL user password [{config['MYSQL_PASSWORD']}]: ")
    if mysql_password:
        config['MYSQL_PASSWORD'] = mysql_password

    # Asking for the Nextcloud admin password
    nextcloud_password = input(f"Enter the Nextcloud admin password [{config['NEXTCLOUD_PASSWORD']}]: ")
    if nextcloud_password:
        config['NEXTCLOUD_PASSWORD'] = nextcloud_password

    # Asking for the GitLab root password
    gitlab_root_password = input(f"Enter the GitLab root password [{config['GITLAB_PASSWORD']}]: ")
    if gitlab_root_password:
        config['GITLAB_PASSWORD'] = gitlab_root_password
    
    # Generate WireGuard keys
    print("Generating WireGuard keys...")
    server_private_key, server_public_key, client_private_key, client_public_key = generate_wireguard_keys()
    config['SERVER_PRIVATE_KEY'] = server_private_key
    config['SERVER_PUBLIC_KEY'] = server_public_key
    config['CLIENT_PRIVATE_KEY'] = client_private_key
    config['CLIENT_PUBLIC_KEY'] = client_public_key

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
    replace_placeholders(config, 'src', temp_dir)

    print("Stopping Docker containers (if any)...")
    stop_docker_containers(temp_dir)

    print("Cleaning up Docker containers...")
    cleanup_docker_containers()
    
    print("Building Docker containers...")
    build_docker_containers(temp_dir)
    
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

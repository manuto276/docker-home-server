import os
import shutil
import subprocess
import sys

# Carica il modulo MySQL (assicurati di avere questo modulo nella directory corretta)
from common import mysql

def load_default_config():
    """
    Carica la configurazione predefinita dal file 'default.conf'.
    """
    config = {}
    try:
        with open(os.path.join(os.path.dirname(__file__), '../config/default.conf')) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value.strip('"')
    except FileNotFoundError:
        print("File di configurazione predefinita non trovato.")
        sys.exit(1)
    return config

def install_docker():
    """
    Verifica se Docker è installato, altrimenti installa Docker e le sue dipendenze.
    """
    try:
        # Verifica se Docker è installato
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Docker è già installato.")
    except subprocess.CalledProcessError:
        print("Docker non è installato. Procedo con l'installazione.")
        try:
            # Aggiorna il sistema e installa le dipendenze
            subprocess.run(['apt', 'update'], check=True)
            subprocess.run(['apt', 'install', '-y', 'apt-transport-https', 'ca-certificates', 'curl', 'software-properties-common'], check=True)

            # Aggiungi la chiave GPG ufficiale di Docker
            subprocess.run("curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -", shell=True, check=True)

            # Aggiungi il repository Docker APT
            subprocess.run('sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"', shell=True, check=True)

            # Aggiorna l'indice dei pacchetti
            subprocess.run(['apt', 'update'], check=True)

            # Installa Docker
            subprocess.run(['apt', 'install', '-y', 'docker-ce', 'docker-compose'], check=True)

            # Aggiungi l'utente corrente al gruppo docker
            subprocess.run(['usermod', '-aG', 'docker', os.getlogin()], check=True)

            # Avvia il servizio Docker
            subprocess.run(['systemctl', 'start', 'docker'], check=True)

            # Abilita il servizio Docker all'avvio
            subprocess.run(['systemctl', 'enable', 'docker'], check=True)

            print("Docker è stato installato con successo.")
        except subprocess.CalledProcessError as e:
            print(f"C'è stato un problema nell'installazione di Docker: {e}")
            sys.exit(1)

def configure_firewall():
    """
    Configura il firewall per permettere il traffico necessario e bloccare il resto.
    """
    rules = [
        "sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT",
        "sudo iptables -A INPUT -p udp --dport 51820 -j ACCEPT",
        "sudo iptables -A INPUT -s 10.0.0.0/24 -j ACCEPT",
        "sudo iptables -A INPUT -i docker0 -j ACCEPT",
        "sudo iptables -A INPUT -i lo -j ACCEPT",
        "sudo iptables -A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT",
        "sudo iptables -P INPUT DROP",
        "sudo apt-get install -y iptables-persistent",
        "sudo sh -c \"iptables-save > /etc/iptables/rules.v4\""
    ]

    for rule in rules:
        try:
            subprocess.run(rule, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Errore nell'applicazione della regola firewall: {e}")

    print("Il firewall è stato configurato con successo.")

def create_directories(config):
    """
    Crea le directory necessarie specificate nella configurazione.
    """
    directories = [
        config['NGINX_CONF_DIR'], config['NGINX_CERTS_DIR'], config['NGINX_VHOST_DIR'],
        config['WIREGUARD_CONFIG_DIR'], config['GITLAB_CONFIG_DIR'], config['GITLAB_LOGS_DIR'],
        config['GITLAB_DATA_DIR'], config['MYSQL_DATA_DIR'], config['NEXTCLOUD_DATA_DIR']
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def replace_placeholders(config, src, dst):
    """
    Sostituisce i segnaposto nei file di configurazione con i valori specificati.
    """
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
    """
    Costruisce e avvia i container Docker.
    """
    try:
        subprocess.run(['docker-compose', 'up', '-d'], cwd=temp_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Errore durante la costruzione dei container Docker: {e}")
        sys.exit(1)

def stop_docker_containers(temp_dir):
    """
    Ferma i container Docker se sono in esecuzione.
    """
    try:
        subprocess.run(['docker-compose', 'down'], cwd=temp_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'arresto dei container Docker: {e}")

def cleanup_docker_containers():
    """
    Pulisce i container e le immagini Docker inutilizzate.
    """
    try:
        # Prune Docker system
        subprocess.run(['docker', 'system', 'prune', '-f'], check=True)

        # Prune Docker images
        subprocess.run(['docker', 'image', 'prune', '-f'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Errore durante la pulizia dei container Docker: {e}")

def save_config(config):
    """
    Salva la configurazione in '/etc/docker-home-server/config.conf'.
    """
    try:
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
    except Exception as e:
        print(f"Errore nel salvataggio della configurazione: {e}")
        sys.exit(1)

def load_config():
    """
    Carica la configurazione da '/etc/docker-home-server/config.conf'.
    """
    if not os.path.exists('/etc/docker-home-server/config.conf'):
        return None

    config = {}
    try:
        with open('/etc/docker-home-server/config.conf') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value.strip('"')
    except Exception as e:
        print(f"Errore nel caricamento della configurazione: {e}")
        return None

    return config

def generate_ssl_certificate(domain):
    """
    Genera un certificato SSL per il dominio specificato.
    """
    ssl_dir = '/etc/ssl/certs'
    try:
        if not os.path.exists(ssl_dir):
            os.makedirs(ssl_dir)

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
    except subprocess.CalledProcessError as e:
        print(f"Errore nella generazione del certificato SSL per {domain}: {e}")

def copy_nginx_config(temp_dir):
    """
    Copia i file di configurazione di Nginx dalla directory temporanea alla directory di configurazione di Nginx.
    """
    nginx_conf_dir = '/etc/nginx/conf.d'
    try:
        shutil.copytree(f'{temp_dir}/nginx/conf.d', nginx_conf_dir, dirs_exist_ok=True)
    except Exception as e:
        print(f"Errore nella copia della configurazione di Nginx: {e}")

def install_server():
    """
    Procedura di installazione del server Docker Home.
    """
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
    ip_address = subprocess.run(['hostname', '-I'], stdout=subprocess.PIPE).stdout.decode().strip().split()[0]
    config['SERVERIP'] = ip_address

    ip_address = input(f"Enter the server IP address [{ip_address}]: ")
    if ip_address:
        config['SERVERIP'] = ip_address

    domain = input(f"Enter the domain name [{config['BASE_DOMAIN']}]: ")
    if domain:
        config['BASE_DOMAIN'] = domain
        config['GITLAB_DOMAIN'] = f"gitlab.{domain}"
        config['NEXTCLOUD_DOMAIN'] = f"nextcloud.{domain}"
        config['PHPMYADMIN_DOMAIN'] = f"phpmyadmin.{domain}"

    wireguard_port = input(f"Enter the WireGuard server port [{config['SERVERPORT']}]: ")
    if wireguard_port:
        config['SERVERPORT'] = wireguard_port

    email = input(f"Enter the email address [{config['EMAIL']}]: ")
    if email:
        config['EMAIL'] = email

    mysql_root_password = input(f"Enter the MySQL root password [{config['MYSQL_ROOT_PASSWORD']}]: ")
    if mysql_root_password:
        config['MYSQL_ROOT_PASSWORD'] = mysql_root_password

    create_mysql_user = input("Do you want to create a MySQL user? [y/n]: ")
    if create_mysql_user.lower() == 'y':
        mysql_user = input(f"Enter the MySQL user [{config['MYSQL_USER']}]: ")
        if mysql_user:
            config['MYSQL_USER'] = mysql_user

        mysql_password = input(f"Enter the MySQL user password [{config['MYSQL_PASSWORD']}]: ")
        if mysql_password:
            config['MYSQL_PASSWORD'] = mysql_password

    create_mysql_database = input("Do you want to create a default MySQL database? [y/n]: ")
    if create_mysql_database.lower() == 'y':
        mysql_database = input(f"Enter the MySQL database name [{config['MYSQL_DATABASE']}]: ")
        if mysql_database:
            config['MYSQL_DATABASE'] = mysql_database

    create_nextcloud_user = input("Do you want to create a Nextcloud user? [y/n]: ")
    if create_nextcloud_user.lower() == 'y':
        nextcloud_password = input(f"Enter the Nextcloud admin password [{config['NEXTCLOUD_PASSWORD']}]: ")
        if nextcloud_password:
            config['NEXTCLOUD_PASSWORD'] = nextcloud_password

    print("Generating SSL certificates...")
    generate_ssl_certificate(config['BASE_DOMAIN'])
    generate_ssl_certificate(config['GITLAB_DOMAIN'])
    generate_ssl_certificate(config['NEXTCLOUD_DOMAIN'])
    generate_ssl_certificate(config['PHPMYADMIN_DOMAIN'])

    temp_dir = '/tmp/docker-home-server'
    print(f"Copying src/ to {temp_dir}...")
    shutil.copytree('src', temp_dir, dirs_exist_ok=True)

    print("Replacing placeholders with configuration values...")
    replace_placeholders(config, temp_dir, temp_dir)

    print("Copying Nginx configuration...")
    copy_nginx_config(temp_dir)

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

import os
import shutil
import subprocess
import sys
import time

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
                    config[key] = value.strip('\"')
    except FileNotFoundError:
        print("File di configurazione predefinita non trovato.")
        sys.exit(1)
    return config

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
                    config[key] = value.strip('\"')
    except Exception as e:
        print(f"Errore nel caricamento della configurazione: {e}")
        return None

    return config

def save_config(config):
    """
    Salva la configurazione in '/etc/docker-home-server/config.conf'.
    """
    try:
        if not os.path.exists('/etc/docker-home-server'):
            os.makedirs('/etc/docker-home-server')

        with open('/etc/docker-home-server/config.conf', 'w') as f:
            for key, value in config.items():
                f.write(f'{key}={value}\n')

        subprocess.run(['chown', 'root:root', '/etc/docker-home-server/config.conf'], check=True)
        subprocess.run(['chmod', '600', '/etc/docker-home-server/config.conf'], check=True)
    except Exception as e:
        print(f"Errore nel salvataggio della configurazione: {e}")
        sys.exit(1)

def install_docker():
    """
    Verifica se Docker è installato, altrimenti installa Docker e le sue dipendenze.
    """
    try:
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Docker è già installato.")
    except Exception:
        print("Docker non è installato. Procedo con l'installazione.")
        try:
            subprocess.run(['apt', 'update'], check=True)
            subprocess.run(['apt', 'install', '-y', 'apt-transport-https', 'ca-certificates', 'curl', 'software-properties-common'], check=True)
            subprocess.run("curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -", shell=True, check=True)
            subprocess.run('sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"', shell=True, check=True)
            subprocess.run(['apt', 'update'], check=True)
            subprocess.run(['apt', 'install', '-y', 'docker-ce', 'docker-compose'], check=True)
            subprocess.run(['usermod', '-aG', 'docker', os.getlogin()], check=True)
            subprocess.run(['systemctl', 'start', 'docker'], check=True)
            subprocess.run(['systemctl', 'enable', 'docker'], check=True)
            print("Docker è stato installato con successo.")
        except Exception as e:
            print(f"C'è stato un problema nell'installazione di Docker: {e}")
            sys.exit(1)

def create_directories(config):
    """
    Crea le directory necessarie specificate nella configurazione.
    """
    directories = [
        config['NGINX_CONF_DIR'], config['NGINX_CERTS_DIR'], config['NGINX_VHOST_DIR'],
        config['GITLAB_CONFIG_DIR'], config['GITLAB_LOGS_DIR'],
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

def obtain_ssl_certificate(domain, email, compose_dir):
    """
    Ottiene un certificato SSL per il dominio specificato utilizzando Certbot.
    """
    try:
        subprocess.run([
            'docker-compose', 'run', '--rm', 'certbot', 'certonly', '--webroot',
            '--webroot-path=/var/lib/letsencrypt', '-d', domain, '--email', email, '--agree-tos', '--non-interactive'
        ], check=True, cwd=compose_dir)
    except subprocess.CalledProcessError as e:
        print(f"Errore nell'ottenimento del certificato SSL per {domain}: {e}")

def copy_nginx_config(temp_dir):
    """
    Copia i file di configurazione di Nginx dalla directory temporanea alla directory di configurazione di Nginx.
    """
    nginx_conf_dir = '/etc/nginx/conf.d'
    try:
        shutil.copytree(f'{temp_dir}/nginx/conf.d', nginx_conf_dir, dirs_exist_ok=True)
    except Exception as e:
        print(f"Errore nella copia della configurazione di Nginx: {e}")

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
        subprocess.run(['docker', 'system', 'prune', '-f'], check=True)
        subprocess.run(['docker', 'image', 'prune', '-f'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Errore durante la pulizia dei container Docker: {e}")

def build_docker_containers(temp_dir):
    """
    Costruisce e avvia i container Docker.
    """
    try:
        subprocess.run(['docker-compose', 'up', '-d'], cwd=temp_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Errore durante la costruzione dei container Docker: {e}")
        sys.exit(1)

def initialize_nextcloud_database(config):
    # Aspetta che MySQL sia pronto
    time.sleep(10)
    
    # Comandi per creare database e utente Nextcloud su MySQL
    try:
        subprocess.run([
            'docker', 'exec', 'mysql', 'mysql', '-uroot', f'-p{config["MYSQL_ROOT_PASSWORD"]}',
            '-e', f'CREATE DATABASE IF NOT EXISTS {config["NEXTCLOUD_MYSQL_DATABASE"]};'
        ], check=True)
        
        subprocess.run([
            'docker', 'exec', 'mysql', 'mysql', '-uroot', f'-p{config["MYSQL_ROOT_PASSWORD"]}',
            '-e', f"CREATE USER IF NOT EXISTS '{config['NEXTCLOUD_MYSQL_USER']}'@'%' IDENTIFIED BY '{config['MYSQL_ROOT_PASSWORD']}';"
        ], check=True)
        
        subprocess.run([
            'docker', 'exec', 'mysql', 'mysql', '-uroot', f'-p{config["MYSQL_ROOT_PASSWORD"]}',
            '-e', f"GRANT ALL PRIVILEGES ON {config['NEXTCLOUD_MYSQL_DATABASE']}.* TO '{config['NEXTCLOUD_MYSQL_USER']}'@'%';"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'inizializzazione del database Nextcloud: {e}")
        sys.exit(1)

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

    print("Generating SSL certificates with Certbot...")
    obtain_ssl_certificate(config['BASE_DOMAIN'], config['EMAIL'], temp_dir)
    obtain_ssl_certificate(config['GITLAB_DOMAIN'], config['EMAIL'], temp_dir)
    obtain_ssl_certificate(config['NEXTCLOUD_DOMAIN'], config['EMAIL'], temp_dir)
    obtain_ssl_certificate(config['PHPMYADMIN_DOMAIN'], config['EMAIL'], temp_dir)

    print("Cleaning up temporary files...")
    shutil.rmtree(temp_dir)

    print("Saving configuration...")
    save_config(config)

    print("Initializing Nextcloud database...")
    initialize_nextcloud_database(config)

    print("Docker Home Server installation completed.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Please run this script with sudo.")
        sys.exit(1)
    install_server()
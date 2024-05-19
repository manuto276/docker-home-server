#!/bin/bash

# Funzione per controllare e installare i prerequisiti
check_prerequisites() {
    local required_cmds=("wg" "openssl" "docker" "docker-compose")
    for cmd in "${required_cmds[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            echo "$cmd non è installato. Installazione in corso..."
            install_$cmd
        fi
    done
}

install_wg() {
    apt-get update && apt-get install -y wireguard
}

install_openssl() {
    apt-get update && apt-get install -y openssl
}

install_docker() {
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
}

install_docker-compose() {
    apt-get update && apt-get install -y docker-compose
}

# Funzione per generare chiavi WireGuard
generate_wireguard_keys() {
    if [ -f /etc/docker-server/keys ]; then
        source /etc/docker-server/keys
        echo "Sono state trovate le chiavi WireGuard generate in precedenza"
    else
        echo "Generazione delle chiavi WireGuard in corso..."
        SERVER_PRIVATE_KEY=$(wg genkey)
        SERVER_PUBLIC_KEY=$(echo $SERVER_PRIVATE_KEY | wg pubkey)
        CLIENT_PRIVATE_KEY=$(wg genkey)
        CLIENT_PUBLIC_KEY=$(echo $CLIENT_PRIVATE_KEY | wg pubkey)
        mkdir -p /etc/docker-server
        cat <<EOL > /etc/docker-server/keys
SERVER_PRIVATE_KEY=$SERVER_PRIVATE_KEY
SERVER_PUBLIC_KEY=$SERVER_PUBLIC_KEY
CLIENT_PUBLIC_KEY=$CLIENT_PUBLIC_KEY
EOL
    fi
}

# Funzione per generare certificati SSL autofirmati
generate_ssl_certificates() {
    mkdir -p $NGINX_CERTS_DIR
    generate_certificate $BASE_DOMAIN
    generate_certificate $COLLABORA_DOMAIN
    generate_certificate $NEXTCLOUD_DOMAIN
    generate_certificate $PHPMYADMIN_DOMAIN
    generate_certificate $GITLAB_DOMAIN
}

generate_certificate() {
    local domain=$1
    if [ -f $NGINX_CERTS_DIR/$domain.crt ] && [ -f $NGINX_CERTS_DIR/$domain.key ]; then
        echo "Certificato SSL per $domain trovato"
    else
        echo "Generazione del certificato SSL per $domain in corso..."
        rm -f $NGINX_CERTS_DIR/$domain.crt
        rm -f $NGINX_CERTS_DIR/$domain.key
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout $NGINX_CERTS_DIR/$domain.key -out $NGINX_CERTS_DIR/$domain.crt -subj "/C=IT/ST=Italy/L=Italy/O=Global Security/OU=IT Department/CN=$domain"
    fi
}

# Funzione per preparare la configurazione
prepare_configuration() {
    TEMP_DIR=$(mktemp -d)
    cp -r "$(dirname "$0")/../src"/* $TEMP_DIR
    replace_placeholders
    copy_configuration_files
}

# Funzione per sostituire i placeholder
replace_placeholders() {
    find $TEMP_DIR -type f -exec sed -i "s|__PUID__|$PUID|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__PGID__|$PGID|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__TZ__|$TZ|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__SERVERURL__|$SERVERURL|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__SERVERPORT__|$SERVERPORT|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__PEERS__|$PEERS|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__PEERDNS__|$PEERDNS|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__INTERNAL_SUBNET__|$INTERNAL_SUBNET|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__WG_ADDRESS__|$WG_ADDRESS|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__SERVER_PRIVATE_KEY__|$SERVER_PRIVATE_KEY|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__SERVER_PUBLIC_KEY__|$SERVER_PUBLIC_KEY|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__CLIENT_PUBLIC_KEY__|$CLIENT_PUBLIC_KEY|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__CLIENT_ALLOWED_IPS__|10.0.0.2/32|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__MYSQL_ROOT_PASSWORD__|$MYSQL_ROOT_PASSWORD|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__MYSQL_DATABASE__|$MYSQL_DATABASE|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__GITLAB_DOMAIN__|$GITLAB_DOMAIN|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__COLLABORA_DOMAIN__|$COLLABORA_DOMAIN|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__COLLABORA_USERNAME__|$COLLABORA_USERNAME|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__COLLABORA_PASSWORD__|$COLLABORA_PASSWORD|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__NGINX_CONF_DIR__|$NGINX_CONF_DIR|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__NGINX_CERTS_DIR__|$NGINX_CERTS_DIR|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__NGINX_VHOST_DIR__|$NGINX_VHOST_DIR|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__WIREGUARD_CONFIG_DIR__|$WIREGUARD_CONFIG_DIR|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__GITLAB_CONFIG_DIR__|$GITLAB_CONFIG_DIR|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__GITLAB_LOGS_DIR__|$GITLAB_LOGS_DIR|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__GITLAB_DATA_DIR__|$GITLAB_DATA_DIR|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__MYSQL_DATA_DIR__|$MYSQL_DATA_DIR|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__NEXTCLOUD_DATA_DIR__|$NEXTCLOUD_DATA_DIR|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__BASE_DOMAIN__|$BASE_DOMAIN|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__NEXTCLOUD_DOMAIN__|$NEXTCLOUD_DOMAIN|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__PHPMYADMIN_DOMAIN__|$PHPMYADMIN_DOMAIN|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__PHPMYADMIN_DATA_DIR__|$PHPMYADMIN_DATA_DIR|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__EMAIL__|$EMAIL|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__NEXTCLOUD_USERNAME__|$NEXTCLOUD_USERNAME|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__NEXTCLOUD_PASSWORD__|$NEXTCLOUD_PASSWORD|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__NEXT_CLOUD_MYSQL_USER__|$NEXT_CLOUD_MYSQL_USER|g" {} \;
    find $TEMP_DIR -type f -exec sed -i "s|__NEXT_CLOUD_MYSQL_DATABASE__|$NEXT_CLOUD_MYSQL_DATABASE|g" {} \;
}

# Funzione per copiare i file di configurazione
copy_configuration_files() {
    mkdir -p $NGINX_CONF_DIR
    mkdir -p $NGINX_VHOST_DIR
    cp $TEMP_DIR/nginx.conf $NGINX_CONF_DIR/nginx.conf
    cp $TEMP_DIR/gitlab.conf $NGINX_VHOST_DIR/gitlab.conf
    cp $TEMP_DIR/collabora.conf $NGINX_VHOST_DIR/collabora.conf
    cp $TEMP_DIR/nextcloud.conf $NGINX_VHOST_DIR/nextcloud.conf
    cp $TEMP_DIR/phpmyadmin.conf $NGINX_VHOST_DIR/phpmyadmin.conf
    mkdir -p $WIREGUARD_CONFIG_DIR
    mkdir -p $GITLAB_CONFIG_DIR
    mkdir -p $GITLAB_LOGS_DIR
    mkdir -p $GITLAB_DATA_DIR
    mkdir -p $MYSQL_DATA_DIR
    mkdir -p $NEXTCLOUD_DATA_DIR
    mkdir -p $COLLABORA_DATA_DIR
    mkdir -p $PHPMYADMIN_DATA_DIR
}

# Funzione per avviare i container Docker
deploy_containers() {
    docker-compose -f $TEMP_DIR/docker-compose.yml up -d
}

# Funzione per eseguire lo script di setup MySQL
run_mysql_setup() {
    source "$(dirname "$0")/mysql.sh"
}

# Funzione per eseguire lo script di setup Nextcloud
run_nextcloud_setup() {
    source "$(dirname "$0")/nextcloud.sh"
}

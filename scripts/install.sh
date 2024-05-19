#!/bin/bash

# Include utility functions
source "$(dirname "$0")/utils.sh"
source "$(dirname "$0")/mysql.sh"
source "$(dirname "$0")/nextcloud.sh"
source "$(dirname "$0")/wireguard.sh"

# Verifica che lo script venga eseguito con sudo
if [ "$EUID" -ne 0 ]; then
    echo "Esegui lo script con sudo"
    exit 1
fi

# Funzione principale di installazione
main() {
    check_prerequisites
    load_config
    get_user_input
    generate_wireguard_keys
    generate_ssl_certificates
    prepare_configuration
    deploy_containers
    create_default_mysql_user
    create_default_nextcloud_user
}

# Funzione per caricare il file di configurazione
load_config() {
    if [ -f /etc/docker-server/config ]; then
        source /etc/docker-server/config
    else
        source "$(dirname "$0")/../config/config.default"
    fi
}

# Funzione per richiedere input all'utente
get_user_input() {
    read -p "Inserisci l'indirizzo IP del server [default: $(get_free_ip)]: " SERVERIP
    SERVERIP=${SERVERIP:-$(get_free_ip)}
    read -p "Inserisci il dominio di base (es. example.com): " BASE_DOMAIN
    read -p "Inserisci l'email per i certificati SSL: " EMAIL
    read -p "Vuoi creare un utente per Nextcloud? [s/n]: " input_create_nextcloud_user
    if [ "$input_create_nextcloud_user" == "s" ]; then
        read -p "Inserisci il nome utente di Nextcloud: " NEXTCLOUD_USERNAME
        read -p "Inserisci la password di Nextcloud: " NEXTCLOUD_PASSWORD
    fi
    read -p "Vuoi creare un utente per MySQL? [s/n]: " input_create_mysql_user
    if [ "$input_create_mysql_user" == "s" ]; then
        read -p "Inserisci il nome dell'utente MySQL: " MYSQL_USER
        read -p "Inserisci la password dell'utente MySQL: " MYSQL_PASSWORD
    fi
}

# Esecuzione della funzione principale
main

#!/bin/bash

# Include utility functions
source "$(dirname "$0")/utils.sh"

# Funzione principale di disinstallazione
main() {
    stop_containers
    remove_containers
    remove_images
    remove_volumes
    remove_networks
    remove_configuration
}

# Funzione per fermare i container
stop_containers() {
    docker stop $(docker ps -a -q)
}

# Funzione per rimuovere i container
remove_containers() {
    docker rm $(docker ps -a -q)
}

# Funzione per rimuovere le immagini Docker
remove_images() {
    docker image prune -a -f
}

# Funzione per rimuovere i volumi Docker
remove_volumes() {
    docker volume prune -f
}

# Funzione per rimuovere le reti Docker
remove_networks() {
    docker network prune -f
}

# Funzione per rimuovere i file di configurazione
remove_configuration() {
    rm -rf /etc/docker-server
}

# Esecuzione della funzione principale
main

#!/bin/bash

# Include utility functions
source "$(dirname "$0")/utils.sh"

# Verifica che lo script venga eseguito con sudo
if [ "$EUID" -ne 0 ]; then
    echo "Esegui lo script con sudo"
    exit 1
fi

# Funzione per fermare e rimuovere i container Docker
remove_containers() {
    docker-compose -f "$(dirname "$0")/../src/docker-compose.yml" down
    docker system prune -a -f
    docker network prune -f
}

# Funzione principale di disinstallazione
main() {
    remove_containers
}

# Esecuzione della funzione principale
main

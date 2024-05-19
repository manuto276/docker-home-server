#!/bin/bash

# Include utility functions
source "$(dirname "$0")/utils.sh"

# Funzione per creare un utente Nextcloud di default
create_default_nextcloud_user() {
    docker exec -it nextcloud occ user:add --display-name="$NEXTCLOUD_USERNAME" --password="$NEXTCLOUD_PASSWORD" "$NEXTCLOUD_USERNAME"
}

# Funzione per mostrare il menu
show_menu() {
    echo "1) Crea un nuovo utente Nextcloud"
    echo "2) Mostra utenti Nextcloud"
    echo "3) Cancella un utente Nextcloud"
    echo "4) Esci"
}

# Funzione per creare un nuovo utente Nextcloud
create_nextcloud_user() {
    read -p "Inserisci il nome del nuovo utente Nextcloud: " new_user
    read -p "Inserisci la password del nuovo utente Nextcloud: " new_password
    docker exec -it nextcloud occ user:add --display-name="$new_user" --password="$new_password" "$new_user"
}

# Funzione per mostrare gli utenti Nextcloud
show_nextcloud_users() {
    docker exec -it nextcloud occ user:list
}

# Funzione per cancellare un utente Nextcloud
delete_nextcloud_user() {
    read -p "Inserisci il nome dell'utente Nextcloud da cancellare: " del_user
    docker exec -it nextcloud occ user:delete "$del_user"
}

# Funzione per eseguire l'azione selezionata
execute_choice() {
    case $1 in
        1) create_nextcloud_user ;;
        2) show_nextcloud_users ;;
        3) delete_nextcloud_user ;;
        4) exit 0 ;;
        *) echo "Scelta non valida!" ;;
    esac
}

# Ciclo principale del menu
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    while true; do
        show_menu
        read -p "Seleziona un'opzione: " choice
        execute_choice $choice
    done
fi

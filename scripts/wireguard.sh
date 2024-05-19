#!/bin/bash

# Include utility functions
source "$(dirname "$0")/utils.sh"

# Funzione per generare QR Code per la configurazione di WireGuard
generate_wireguard_qr() {
    docker exec -it wireguard /app/show-peer 1 | qrencode -t ansiutf8
}

# Funzione per mostrare il menu
show_menu() {
    echo "1) Genera QR Code per la configurazione WireGuard"
    echo "2) Mostra peer WireGuard"
    echo "3) Aggiungi peer WireGuard"
    echo "4) Rimuovi peer WireGuard"
    echo "5) Esci"
}

# Funzione per mostrare i peer WireGuard
show_wireguard_peers() {
    docker exec -it wireguard /app/show-peer 1
}

# Funzione per aggiungere un peer WireGuard
add_wireguard_peer() {
    read -p "Inserisci il nome del peer: " peer_name
    docker exec -it wireguard /app/add-peer "$peer_name"
}

# Funzione per rimuovere un peer WireGuard
remove_wireguard_peer() {
    read -p "Inserisci il nome del peer da rimuovere: " peer_name
    docker exec -it wireguard /app/remove-peer "$peer_name"
}

# Funzione per eseguire l'azione selezionata
execute_choice() {
    case $1 in
        1) generate_wireguard_qr ;;
        2) show_wireguard_peers ;;
        3) add_wireguard_peer ;;
        4) remove_wireguard_peer ;;
        5) exit 0 ;;
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

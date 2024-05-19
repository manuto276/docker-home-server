#!/bin/bash

# Include utility functions
source "$(dirname "$0")/scripts/utils.sh"

# Funzione per mostrare il menu principale
show_main_menu() {
    echo "1) Installa il server"
    echo "2) Disinstalla il server"
    echo "3) Configura MySQL"
    echo "4) Configura Nextcloud"
    echo "5) Configura WireGuard"
    echo "6) Esci"
}

# Funzione per eseguire l'azione selezionata
execute_main_choice() {
    case $1 in
        1) sudo "$(dirname "$0")/scripts/install.sh" ;;
        2) sudo "$(dirname "$0")/scripts/uninstall.sh" ;;
        3) "$(dirname "$0")/scripts/mysql.sh" ;;
        4) "$(dirname "$0")/scripts/nextcloud.sh" ;;
        5) "$(dirname "$0")/scripts/wireguard.sh" ;;
        6) exit 0 ;;
        *) echo "Scelta non valida!" ;;
    esac
}

# Ciclo principale del menu
while true; do
    show_main_menu
    read -p "Seleziona un'opzione: " main_choice
    execute_main_choice $main_choice
done

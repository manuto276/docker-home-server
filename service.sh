#!/bin/bash

# Funzione per mostrare il menu
show_menu() {
    echo "1) Installa il server"
    echo "2) Disinstalla il server"
    echo "3) Configura MySQL"
    echo "4) Configura Nextcloud"
    echo "5) Esci"
}

# Funzione per eseguire l'azione selezionata
execute_choice() {
    case $1 in
        1)
            bash "$(dirname "$0")/scripts/install.sh"
            ;;
        2)
            bash "$(dirname "$0")/scripts/uninstall.sh"
            ;;
        3)
            bash "$(dirname "$0")/scripts/mysql.sh"
            ;;
        4)
            bash "$(dirname "$0")/scripts/nextcloud.sh"
            ;;
        5)
            exit 0
            ;;
        *)
            echo "Scelta non valida!"
            ;;
    esac
}

# Ciclo principale del menu
while true; do
    show_menu
    read -p "Seleziona un'opzione: " choice
    execute_choice $choice
done

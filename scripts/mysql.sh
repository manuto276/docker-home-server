#!/bin/bash

# Include utility functions
source "$(dirname "$0")/utils.sh"

# Funzione per creare un utente MySQL di default
create_default_mysql_user() {
    docker exec -it mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "CREATE USER IF NOT EXISTS '$MYSQL_USER'@'%' IDENTIFIED BY '$MYSQL_PASSWORD';"
    docker exec -it mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "GRANT ALL PRIVILEGES ON $MYSQL_DATABASE.* TO '$MYSQL_USER'@'%';"
    docker exec -it mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "FLUSH PRIVILEGES;"
}

# Funzione per mostrare il menu
show_menu() {
    echo "1) Mostra utenti MySQL"
    echo "2) Mostra database MySQL"
    echo "3) Crea un nuovo utente MySQL"
    echo "4) Cancella un utente MySQL"
    echo "5) Crea un nuovo database MySQL"
    echo "6) Cancella un database MySQL"
    echo "7) Esci"
}

# Funzione per mostrare gli utenti MySQL
show_mysql_users() {
    docker exec -it mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "SELECT User, Host FROM mysql.user;"
}

# Funzione per mostrare i database MySQL
show_mysql_databases() {
    docker exec -it mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "SHOW DATABASES;"
}

# Funzione per creare un nuovo utente MySQL
create_mysql_user() {
    read -p "Inserisci il nome del nuovo utente MySQL: " new_user
    read -p "Inserisci la password del nuovo utente MySQL: " new_password
    docker exec -it mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "CREATE USER '$new_user'@'%' IDENTIFIED BY '$new_password';"
    docker exec -it mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "GRANT ALL PRIVILEGES ON *.* TO '$new_user'@'%';"
    docker exec -it mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "FLUSH PRIVILEGES;"
}

# Funzione per cancellare un utente MySQL
delete_mysql_user() {
    read -p "Inserisci il nome dell'utente MySQL da cancellare: " del_user
    docker exec -it mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "DROP USER '$del_user'@'%';"
}

# Funzione per creare un nuovo database MySQL
create_mysql_database() {
    read -p "Inserisci il nome del nuovo database MySQL: " new_db
    docker exec -it mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "CREATE DATABASE $new_db;"
}

# Funzione per cancellare un database MySQL
delete_mysql_database() {
    read -p "Inserisci il nome del database MySQL da cancellare: " del_db
    docker exec -it mysql mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "DROP DATABASE $del_db;"
}

# Funzione per eseguire l'azione selezionata
execute_choice() {
    case $1 in
        1) show_mysql_users ;;
        2) show_mysql_databases ;;
        3) create_mysql_user ;;
        4) delete_mysql_user ;;
        5) create_mysql_database ;;
        6) delete_mysql_database ;;
        7) exit 0 ;;
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

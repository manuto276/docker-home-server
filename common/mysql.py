import subprocess
import configparser

def read_config():
    config = configparser.ConfigParser()
    config.read('/etc/docker-home-server/config.conf')
    return {
        'MYSQL_ROOT_USER': 'root',
        'MYSQL_ROOT_PASSWORD': config.get('DEFAULT', 'MYSQL_ROOT_PASSWORD')
    }

def create_mysql_database(config):
    db_name = input("Enter the name of the database to create: ")
    print("Creating MySQL database...")
    subprocess.run([
        "docker", "exec", "-i", "mysql", "mysql", 
        f"-u{config['MYSQL_ROOT_USER']}", 
        f"-p{config['MYSQL_ROOT_PASSWORD']}", 
        "-e", f"CREATE DATABASE IF NOT EXISTS {db_name};"
    ])
    print("MySQL database created.")

def list_mysql_databases(config):
    print("Listing MySQL databases...")
    subprocess.run([
        "docker", "exec", "-i", "mysql", "mysql", 
        f"-u{config['MYSQL_ROOT_USER']}", 
        f"-p{config['MYSQL_ROOT_PASSWORD']}", 
        "-e", "SHOW DATABASES;"
    ])
    print("MySQL databases listed.")

def delete_mysql_database(config):
    db_name = input("Enter the name of the database to delete: ")
    print("Deleting MySQL database...")
    subprocess.run([
        "docker", "exec", "-i", "mysql", "mysql", 
        f"-u{config['MYSQL_ROOT_USER']}", 
        f"-p{config['MYSQL_ROOT_PASSWORD']}", 
        "-e", f"DROP DATABASE IF EXISTS {db_name};"
    ])
    print("MySQL database deleted.")

def create_mysql_user(config):
    user_name = input("Enter the name of the user to create: ")
    user_password = input("Enter the password for the user: ")
    print("Creating MySQL user...")
    subprocess.run([
        "docker", "exec", "-i", "mysql", "mysql", 
        f"-u{config['MYSQL_ROOT_USER']}", 
        f"-p{config['MYSQL_ROOT_PASSWORD']}", 
        "-e", f"CREATE USER IF NOT EXISTS '{user_name}'@'%' IDENTIFIED BY '{user_password}';"
    ])
    print("MySQL user created.")

def list_mysql_users(config):
    print("Listing MySQL users...")
    subprocess.run([
        "docker", "exec", "-i", "mysql", "mysql", 
        f"-u{config['MYSQL_ROOT_USER']}", 
        f"-p{config['MYSQL_ROOT_PASSWORD']}", 
        "-e", "SELECT User FROM mysql.user;"
    ])
    print("MySQL users listed.")

def delete_mysql_user(config):
    user_name = input("Enter the name of the user to delete: ")
    print("Deleting MySQL user...")
    subprocess.run([
        "docker", "exec", "-i", "mysql", "mysql", 
        f"-u{config['MYSQL_ROOT_USER']}", 
        f"-p{config['MYSQL_ROOT_PASSWORD']}", 
        "-e", f"DROP USER IF EXISTS '{user_name}'@'%';"
    ])
    print("MySQL user deleted.")

def manage_mysql():
    config = read_config()
    
    while True:
        print("\nMySQL Management Menu:")
        print("1. Create Database")
        print("2. List Databases")
        print("3. Delete Database")
        print("4. Create User")
        print("5. List Users")
        print("6. Delete User")
        print("7. Exit")
        
        choice = input("Enter your choice: ")
        
        if choice == '1':
            create_mysql_database(config)
        elif choice == '2':
            list_mysql_databases(config)
        elif choice == '3':
            delete_mysql_database(config)
        elif choice == '4':
            create_mysql_user(config)
        elif choice == '5':
            list_mysql_users(config)
        elif choice == '6':
            delete_mysql_user(config)
        elif choice == '7':
            print("Exiting MySQL management.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    manage_mysql()

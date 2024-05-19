import subprocess

def configure_mysql():
    print("Configuring MySQL...")
    # Add MySQL configuration code here
    # Example: create database, create user, etc.
    # You can use subprocess to run mysql commands or use a MySQL library for Python
    print("MySQL configuration completed.")

def create_mysql_database(config):
    print("Creating MySQL database...")
    subprocess.run([
        "docker", "exec", "-i", "mysql", "mysql", 
        f"-u{config['MYSQL_ROOT_USER']}", 
        f"-p{config['MYSQL_ROOT_PASSWORD']}", 
        "-e", f"CREATE DATABASE IF NOT EXISTS {config['MYSQL_DATABASE']};"
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
    print("Deleting MySQL database...")
    subprocess.run([
        "docker", "exec", "-i", "mysql", "mysql", 
        f"-u{config['MYSQL_ROOT_USER']}", 
        f"-p{config['MYSQL_ROOT_PASSWORD']}", 
        "-e", f"DROP DATABASE IF EXISTS {config['MYSQL_DATABASE']};"
    ])
    print("MySQL database deleted.")

def create_mysql_user(config):
    print("Creating MySQL user...")
    subprocess.run([
        "docker", "exec", "-i", "mysql", "mysql", 
        f"-u{config['MYSQL_ROOT_USER']}", 
        f"-p{config['MYSQL_ROOT_PASSWORD']}", 
        "-e", f"CREATE USER IF NOT EXISTS '{config['MYSQL_USER']}'@'%' IDENTIFIED BY '{config['MYSQL_PASSWORD']}';"
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
    print("Deleting MySQL user...")
    subprocess.run([
        "docker", "exec", "-i", "mysql", "mysql", 
        f"-u{config['MYSQL_ROOT_USER']}", 
        f"-p{config['MYSQL_ROOT_PASSWORD']}", 
        "-e", f"DROP USER IF EXISTS '{config['MYSQL_USER']}'@'%';"
    ])
    print("MySQL user deleted.")
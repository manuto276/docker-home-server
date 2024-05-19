import subprocess
import sys
import os

def stop_containers():
    subprocess.run(['docker-compose', 'down'], check=True)

def remove_docker_images():
    subprocess.run(['docker', 'rmi', '-f', '$(docker images -q)'], shell=True, check=True)

def uninstall_docker():
    subprocess.run(['apt-get', 'remove', '-y', 'docker.io'], check=True)
    subprocess.run(['apt-get', 'remove', '-y', 'docker-compose'], check=True)
    subprocess.run(['apt-get', 'autoremove', '-y'], check=True)

def uninstall_server():
    print("Stopping Docker containers...")
    stop_containers()
    
    print("Removing Docker images...")
    remove_docker_images()
    
    print("Uninstalling Docker and Docker Compose...")
    uninstall_docker()
    
    print("Docker Home Server uninstalled.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Please run this script with sudo.")
        sys.exit(1)
    uninstall_server()

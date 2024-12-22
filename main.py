import os
import shutil
import zipfile
from pathlib import Path
import docker

# Initialize Docker client
client = docker.from_env()

def create_backup_directory(base_dir):
    backup_dir = Path(base_dir) / "docker_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir

def backup_bind_mount(source, backup_dir):
    if not os.path.exists(source):
        print(f"Source path does not exist: {source}")
        return

    destination = backup_dir / Path(source).name
    shutil.copytree(source, destination)
    print(f"Backed up bind mount from {source} to {destination}")

def backup_volume(volume_name, backup_dir):
    volume_data = f"/var/lib/docker/volumes/{volume_name}/_data"
    if not os.path.exists(volume_data):
        print(f"Volume data does not exist: {volume_data}")
        return

    destination = backup_dir / volume_name
    shutil.copytree(volume_data, destination)
    print(f"Backed up volume {volume_name} to {destination}")

def create_zip(backup_dir, output_zip):
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                file_path = Path(root) / file
                zipf.write(file_path, file_path.relative_to(backup_dir))

def backup_container_mounts(output_dir):
    containers = client.containers.list(all=True)
    backup_dir = create_backup_directory(output_dir)

    for container in containers:
        container_dir = backup_dir / container.name
        container_dir.mkdir(parents=True, exist_ok=True)

        details = client.api.inspect_container(container.id)
        for mount in details.get("Mounts", []):
            if mount["Type"] == "bind":
                backup_bind_mount(mount["Source"], container_dir)
            elif mount["Type"] == "volume":
                backup_volume(mount["Name"], container_dir)

        # Create a zip for each container
        zip_path = backup_dir / f"{container.name}.zip"
        create_zip(container_dir, zip_path)
        print(f"Created zip: {zip_path}")

        # Clean up extracted files (leave only the zip)
        shutil.rmtree(container_dir)

if __name__ == "__main__":
    # Directory to store the backup zips
    output_dir = "./backups"
    backup_container_mounts(output_dir)

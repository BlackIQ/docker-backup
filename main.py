import os
import shutil
import zipfile
from pathlib import Path
import docker

client = docker.from_env()

def create_backup_directory(base_dir):
    backup_dir = Path(base_dir) / "docker_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir

def backup_bind_mount(source, backup_dir):
    try:
        if not os.access(source, os.R_OK):
            print(f"Permission denied: Cannot read source path {source}")
            return

        destination = backup_dir / Path(source).name
        shutil.copytree(source, destination)
        print(f"Backed up bind mount from {source} to {destination}")
    except PermissionError as e:
        print(f"Permission error while copying {source}: {e}")
    except Exception as e:
        print(f"Error while backing up {source}: {e}")

def create_zip(backup_dir, output_zip):
    try:
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    file_path = Path(root) / file
                    zipf.write(file_path, file_path.relative_to(backup_dir))
        print(f"Created zip archive: {output_zip}")
    except PermissionError as e:
        print(f"Permission error while creating zip: {e}")
    except Exception as e:
        print(f"Error creating zip {output_zip}: {e}")

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

        zip_path = backup_dir / f"{container.name}.zip"
        create_zip(container_dir, zip_path)

        shutil.rmtree(container_dir)

if __name__ == "__main__":
    output_dir = "./backups"
    if not os.access(output_dir, os.W_OK):
        print(f"Permission denied: Cannot write to output directory {output_dir}")
    else:
        backup_container_mounts(output_dir)

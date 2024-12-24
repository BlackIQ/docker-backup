import docker

client = docker.from_env()

def list_volumes_and_mounts():
    containers = client.containers.list(all=True)
    result = []

    for container in containers:
        container_info = {
            "container_id": container.id,
            "name": container.name,
            "mounts": []
        }

        details = client.api.inspect_container(container.id)
        for mount in details.get("Mounts", []):
            container_info["mounts"].append({
                "type": mount["Type"],
                "source": mount["Source"],
                "destination": mount["Destination"]
            })

        result.append(container_info)

    return result

if __name__ == "__main__":
    mounts_info = list_volumes_and_mounts()

    for info in mounts_info:
        print(f"Container: {info['name']} (ID: {info['container_id']})")
        for mount in info['mounts']:
            print(f"  - Type: {mount['type']}, Source: {mount['source']}, Destination: {mount['destination']}")
        print()

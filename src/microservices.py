import requests


def microservice_add_model(service_host_name, group_id, texts):
    result = requests.post(f"http://{service_host_name}/add_group",
                           json={"group_id": group_id, "texts": texts})
    return result.json()


def microservice_generate(group_id, service_host_name, hint):
    result = requests.get(f"http://{service_host_name}/generate",
                          params={"group_id": group_id, "hint": hint})
    return result.json()

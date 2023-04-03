import requests


class MicroserviceException(Exception):
    pass


class MicroserviceManager:
    def __init__(self, microservices):
        self.services = microservices

    def add_group(self, group_id, texts):
        try:
            for service in self.services:
                response = requests.post(f"{service.url}:{service.port}/add_group",
                                         json={"group_id": group_id, "texts": texts}, timeout=15)
                result = response.json()["result"]
                if result == "ERROR":
                    raise MicroserviceException(
                        f"Internal microservice error (add_group): {service.docker_name}")
        except Exception as exc:
            raise MicroserviceException(
                f"Error in microservice {service.docker_name} add_group {exc}") from exc

    def generate(self, service_name, group_id, hint):
        try:
            service_ind = -1
            for i in range(len(self.services)):
                if self.services[i].docker_name == service_name:
                    service_ind = i
                    break

            if service_ind == -1:
                raise MicroserviceException(
                    f"Wrong microservice name - {service_name}")

            service = self.services[service_ind]

            response = requests.post(
                f"{service.url}:{service.port}/generate", json={"group_id": group_id, "hint": hint}, timeout=90)
            result = response.json()["result"]
            if result == "ERROR":
                raise MicroserviceException(
                    f"Internal microservice error (generate): {service.docker_name}")
            return result
        except Exception as exc:
            raise MicroserviceException(
                f"Error in microservice {service.docker_name} generate: {exc}") from exc

    def check_status(self, group_id):
        try:
            ready_count = 0
            total_count = len(self.services)
            for service in self.services:
                response = requests.get(
                    f"{service.url}:{service.port}/check_status", params={"group_id": group_id}, timeout=2)
                result = response.json()["result"]
                if result == "ERROR":
                    raise MicroserviceException(
                        f"Internal microservice error (check_status): {service.docker_name}")
                if result == "OK":
                    ready_count += 1
            if ready_count == total_count:
                return True
            return False
        except Exception as exc:
            raise MicroserviceException(
                f"Error in microservice {service.docker_name} check_status: {exc}") from exc

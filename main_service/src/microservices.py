import requests
import threading
import time


class MicroserviceException(Exception):
    pass


class MicroserviceManager:
    def __init__(self, microservices):
        self.services = microservices

    def add_group(self, group_id, texts):
        try:
            for service in self.services:
                def send_request():
                    requests.post(f"{service.url}:{service.port}/add_group", json={"group_id": group_id, "texts": texts}, timeout=1)

                threading.Thread(target=send_request).start()
                time.sleep(0.2)
                result = "RUN ASYNC"
                if result == "ERROR":
                    raise MicroserviceException(
                        "Internal microservice error (add_group)")
        except Exception as exc:
            raise MicroserviceException(f"Error in add_group {exc}") from exc

    def generate(self, service_name, group_id, hint):
        try:
            service_ind = 0
            for i in range(len(self.services)):
                if self.services[i].docker_name == service_name:
                    service_ind = i
                    break

            service = self.services[service_ind]

            response = requests.post(
                f"{service.url}:{service.port}/generate", json={"group_id": group_id, "hint": hint}, timeout=10)
            result = response.json()["result"]
            if result == "ERROR":
                raise MicroserviceException(
                    "Internal microservice error (generate)")
            return result
        except Exception as exc:
            raise MicroserviceException(f"Error in generate: {exc}") from exc

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
                        "Internal microservice error (check_status)")
                if result == "OK":
                    ready_count += 1
            if ready_count == total_count:
                return True
            return False
        except Exception as exc:
            raise MicroserviceException(
                f"Error in check_status: {exc}") from exc

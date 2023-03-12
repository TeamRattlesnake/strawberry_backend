import requests


class MicroserviceManager:
    def __init__(self, microservices):
        self.services = microservices

    def add_group(self, group_id, texts):
        for service in self.services:
            response = requests.post(f"{service.url}:{service.port}/add_group",
                                     json={"group_id": group_id, "texts": texts}, timeout=10)
            result = response.json()["result"]
            if result == "ERROR":
                raise Exception("Microserver Error")

    def generate(self, service_name, group_id, hint):
        service = self.services[service_name]
        response = requests.post(
            f"{service.url}:{service.port}/generate", json={"group_id": group_id, "hint": hint}, timeout=10)
        result = response.json()["result"]
        if result == "ERROR":
            raise Exception("Microserver Error")
        return result

    def check_status(self, group_id):
        ready_count = 0
        total_count = len(self.services)
        for service in self.services:
            response = requests.get(
                f"{service.url}:{service.port}/check_status", params={"group_id": group_id}, timeout=10)
            result = response.json()["result"]
            if result == "ERROR":
                raise Exception("Microserver Error")
            if result == "OK":
                ready_count += 1
        if ready_count == total_count:
            return True
        return False

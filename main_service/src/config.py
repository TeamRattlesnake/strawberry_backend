import json


class MicroserviceData:
    def __init__(self, data):
        name, dict_data = list(data.items())[0][0], list(data.items())[0][1]
        self.name = name,
        self.docker_name = dict_data["docker_name"]
        self.port = dict_data["port"]
        self.url = dict_data["url"]


class Config:

    def __init__(self, filename):
        with open(filename, "r", encoding="UTF-8") as file:
            self.raw_data = json.load(file)
            self.client_secret = self.raw_data["client_secret"]
            self.db_user = self.raw_data["db_user"]
            self.db_password = self.raw_data["db_password"]
            self.db_port = self.raw_data["db_port"]
            self.db_host = self.raw_data["db_host"]
            self.db_db = self.raw_data["db_db"]
            self.services = [MicroserviceData(data)
                             for data in self.raw_data["services"]]

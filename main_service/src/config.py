import os


class EnvironmentConfig:

    def __init__(self):
        self.MYSQL_USER = os.environ.get("MYSQL_USER")
        self.MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
        self.MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE")
        self.MYSQL_TCP_PORT = os.environ.get("MYSQL_TCP_PORT")
        self.CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
        self.MYSQL_HOST = os.environ.get("MYSQL_HOST")
        self.MICROSERVICES_HOST_NAMES = os.environ.get(
            "MICROSERVICES_HOST_NAMES").split(",")

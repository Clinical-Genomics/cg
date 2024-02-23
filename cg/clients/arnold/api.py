"""Module for the arnoldAPIClient."""


class ArnoldAPIClient:
    def __init__(self, config: dict):
        self.db_uri: str = config["uri"]
        self.host: str = config["host"]

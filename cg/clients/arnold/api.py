"""Module for the arnoldAPIClient."""


class ArnoldAPIClient:
    def __init__(self, config: dict):
        self.host: str = config["host"]

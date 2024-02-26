"""Module for the arnoldAPIClient."""


class ArnoldAPIClient:
    def __init__(self, config: dict):
        self.api_url: str = config["api_url"]

"""The JanusAPIClient."""
import requests
from requests import Request, Response

from cg.apps.janus.dto.collect_qc_request import CollectQCRequest
from cg.exc import JanusAPIError


class JanusAPIClient:
    def __init__(self, config: dict[str]):
        self.host = config["janus"]["host"]

    def get_qc_metrics(self, collect_qc_request: CollectQCRequest):
        endpoint: str = f"{self.host}/collect_qc_metrics"
        response = requests.post(endpoint, data=collect_qc_request)
        if response.status_code is not 200:
            self._handle_errors(response)
        return response.json()

    @staticmethod
    def _handle_errors(response: Response):
        if 400 <= response.status_code < 500:
            raise JanusAPIError(f"Client error: {response.status_code}")
        elif 500 <= response.status_code:
            raise JanusAPIError(f"Server error: {response.status_code}")

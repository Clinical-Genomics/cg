"""The JanusAPIClient."""

from http import HTTPStatus

import requests
from requests import Response

from cg.apps.janus.dto.create_collect_qc_request import CreateCollectQCRequest
from cg.exc import JanusAPIError


class JanusAPIClient:
    def __init__(self, config: dict[str]):
        self.host = config["janus"]["host"]

    def qc_metrics(self, collect_qc_request: CreateCollectQCRequest):
        endpoint: str = f"{self.host}/collect_qc_metrics"
        response = requests.post(endpoint, data=collect_qc_request.model_dump_json())
        if response.status_code == HTTPStatus.OK:
            return response.json()
        self._handle_errors(response)

    @staticmethod
    def _handle_errors(response: Response):
        if 400 <= response.status_code < 500:
            raise JanusAPIError(f"Client error: {response.status_code}")
        elif 500 <= response.status_code:
            raise JanusAPIError(f"Server error: {response.status_code}")

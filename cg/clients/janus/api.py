"""The JanusAPIClient."""

from http import HTTPStatus

import requests
from requests import Response

from cg.clients.janus.dto.create_qc_metrics_request import CreateQCMetricsRequest
from cg.clients.janus.exceptions import JanusClientError, JanusServerError


class JanusAPIClient:
    def __init__(self, config: dict[str]):
        self.host = config["janus"]["host"]

    def qc_metrics(self, collect_qc_request: CreateQCMetricsRequest) -> dict | None:
        endpoint: str = f"{self.host}/collect_qc_metrics"
        post_request_data: str = collect_qc_request.model_dump_json()
        response = requests.post(endpoint, data=post_request_data)
        if response.status_code == HTTPStatus.OK:
            return response.json()
        self._handle_errors(response)

    @staticmethod
    def _handle_errors(response: Response):
        if 400 <= response.status_code < 500:
            raise JanusClientError(f"Client error: {response.status_code}")
        elif 500 <= response.status_code:
            raise JanusServerError(f"Server error: {response.status_code}")

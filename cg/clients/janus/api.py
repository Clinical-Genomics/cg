"""The JanusAPIClient."""

import logging
from http import HTTPStatus

import requests
from requests import Response

from cg.clients.janus.dto.create_qc_metrics_request import CreateQCMetricsRequest
from cg.clients.janus.exceptions import JanusClientError, JanusServerError

LOG = logging.getLogger(__name__)


class JanusAPIClient:
    def __init__(self, config: dict[str]):
        self.host = config["janus"]["host"]

    def qc_metrics(self, collect_qc_request: CreateQCMetricsRequest) -> dict | None:
        endpoint: str = f"{self.host}/collect_qc"
        post_request_data: str = collect_qc_request.model_dump_json()
        response = requests.post(endpoint, data=post_request_data, verify=True)
        if response.status_code == HTTPStatus.OK:
            return response.json()
        self._handle_errors(response)

    @staticmethod
    def _handle_errors(response: Response):
        if HTTPStatus.BAD_REQUEST <= response.status_code < HTTPStatus.INTERNAL_SERVER_ERROR:
            LOG.error(f"Client error: {response.content}")
            raise JanusClientError
        elif HTTPStatus.INTERNAL_SERVER_ERROR <= response.status_code:
            LOG.error(f"Server error: {response.content}")
            raise JanusServerError

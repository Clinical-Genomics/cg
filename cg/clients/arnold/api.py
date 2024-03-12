"""Module for the arnoldAPIClient."""

import logging
from http import HTTPStatus

import requests
from requests import Response

from cg.clients.arnold.dto.create_case_request import CreateCaseRequest
from cg.clients.arnold.exceptions import ArnoldClientError, ArnoldServerError

LOG = logging.getLogger(__name__)


class ArnoldAPIClient:
    def __init__(self, config: dict):
        self.api_url: str = config["api_url"]

    def create_case(self, case: CreateCaseRequest) -> Response:
        endpoint: str = f"{self.api_url}/case/"
        post_request_data: CreateCaseRequest = case
        response: Response = requests.post(endpoint, data=post_request_data)
        if response.status_code == HTTPStatus.OK:
            LOG.info(f"Successfully created case for {case.case_id} in Arnold.")
            return response
        self._handle_errors(response)

    @staticmethod
    def _handle_errors(response: Response):
        if HTTPStatus.BAD_REQUEST <= response.status_code < HTTPStatus.INTERNAL_SERVER_ERROR:
            raise ArnoldClientError(
                f"Client error: {response.status_code}. Reason {response.content}"
            )
        elif HTTPStatus.INTERNAL_SERVER_ERROR <= response.status_code:
            raise ArnoldServerError(
                f"Server error: {response.status_code}. Reason {response.content}"
            )

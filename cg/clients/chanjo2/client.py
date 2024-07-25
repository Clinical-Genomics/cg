"""Coverage analysis API for human clinical sequencing data."""

import requests

from cg.clients.chanjo2.models import CoveragePostRequest, CoveragePostResponse
from cg.clients.chanjo2.utils import handle_client_errors


class Chanjo2APIClient:
    """
    Chanjo2 API to communicate with a d4tools software in order to return coverage
    over genomic intervals.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "accept": "application/json",
        }

    @handle_client_errors
    def get_coverage(self, coverage_post_request: CoveragePostRequest) -> CoveragePostResponse:
        """Send a POST request to the coverage endpoint to retrieve gene coverage summary data."""
        endpoint: str = f"{self.base_url}/coverage/d4/genes/summary"
        post_data: dict = coverage_post_request.model_dump()
        response: requests.Response = requests.post(
            url=endpoint, headers=self.headers, json=post_data
        )
        response.raise_for_status()
        response_json: dict = response.json()
        return CoveragePostResponse.model_validate(response_json)

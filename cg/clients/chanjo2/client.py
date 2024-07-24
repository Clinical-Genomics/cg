"""Coverage analysis API for human clinical sequencing data."""

import logging
from typing import Any

import requests

from cg.clients.chanjo2.models import CoverageData, CoverageRequest

LOG = logging.getLogger(__name__)


class Chanjo2APIClient:
    """
    Chanjo2 API to communicate with a d4tools software in order to return coverage
    over genomic intervals.
    """

    def __init__(self, config: dict[str, str]):
        self.headers = {
            "Content-Type": "application/json",
            "accept": "application/json",
        }
        self.host = config["chanjo2"]["host"]

    def get_coverage(self, coverage_request: CoverageRequest) -> CoverageData | None:
        """Send a POST request to the coverage endpoint to retrieve gene coverage summary data."""
        endpoint: str = f"{self.host}/coverage/d4/genes/summary"
        post_data: dict[str, Any] = coverage_request.model_dump()
        try:
            response: requests.Response = requests.post(
                url=endpoint, headers=self.headers, json=post_data
            )
            response.raise_for_status()
            response_content: dict[str, Any] = response.json().values()
            if not response_content:
                LOG.error("The POST get coverage response is empty")
                return None
            return CoverageData(**next(iter(response_content)))
        except (requests.RequestException, ValueError) as error:
            LOG.error(f"Error during coverage POST request: {error}")
            return None

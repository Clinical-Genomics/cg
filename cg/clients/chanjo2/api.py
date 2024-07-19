"""Coverage analysis API for human clinical sequencing data."""

import logging
from typing import Any

import requests
from pydantic import ValidationError

from cg.clients.chanjo2.models import CoverageData, CoverageRequest

LOG = logging.getLogger(__name__)


class Chanjo2APIClient:
    """
    Chanjo2 API to communicate with a d4tools software in order to return coverage
    over genomic intervals.
    """

    def __init__(self, config: dict[str, str]):
        self.headers = {"Content-Type": "application/json"}
        self.host = config["chanjo2"]["host"]

    def get_coverage(self, coverage_request: CoverageRequest) -> CoverageData | None:
        """Send a POST request to the coverage endpoint to retrieve gene coverage summary data."""
        endpoint: str = f"{self.host}/coverage/d4/genes/summary"
        post_data: dict[str, Any] = coverage_request.model_dump()
        try:
            response = requests.post(url=endpoint, headers=self.headers, data=post_data)
            response.raise_for_status()
            coverage_data = next(iter(response.json().values()))
            return CoverageData(**coverage_data)
        except (requests.RequestException, ValueError, ValidationError) as error:
            LOG.error(f"Error during coverage POST request: {error}")
            return None

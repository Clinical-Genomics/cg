"""Chanjo2 API model fixtures."""

import pytest

from cg.clients.chanjo2.models import (
    CoveragePostRequest,
    CoveragePostResponse,
    CoverageSample,
)
from cg.constants.constants import GenomeVersion


@pytest.fixture
def coverage_post_request(sample_id: str) -> CoveragePostRequest:
    return CoveragePostRequest(
        build=GenomeVersion.GRCh37,
        coverage_threshold=10,
        hgnc_gene_ids=[2861, 3791, 6481, 7436, 30521],
        interval_type="genes",
        samples=[
            CoverageSample(
                coverage_file_path=f"/path/to/coverage/{sample_id}.d4",
                name=sample_id,
            )
        ],
    )


@pytest.fixture
def coverage_post_response(coverage_post_response_json: dict) -> CoveragePostResponse:
    return CoveragePostResponse.model_validate(coverage_post_response_json)

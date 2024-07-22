"""Chanjo2 API model fixtures."""

import pytest

from cg.clients.chanjo2.models import CoverageData, CoverageRequest, CoverageSample
from cg.constants.constants import GenomeVersion


@pytest.fixture
def coverage_request(sample_id: str) -> CoverageRequest:
    return CoverageRequest(
        build=GenomeVersion.GRCh37,
        coverage_threshold=10,
        gene_ids=[2861, 3791, 6481, 7436, 30521],
        interval_type="genes",
        samples=[
            CoverageSample(
                coverage_path=f"/path/to/coverage/{sample_id}.d4",
                id=sample_id,
            )
        ],
    )


@pytest.fixture
def coverage_data() -> CoverageData:
    return CoverageData(
        mean_coverage=55.55,
        coverage_completeness_percent=33.33,
    )

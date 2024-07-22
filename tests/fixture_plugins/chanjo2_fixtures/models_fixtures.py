"""Chanjo2 API model fixtures."""

import pytest

from cg.clients.chanjo2.models import Chanjo2Sample, CoverageData, CoverageRequest
from cg.constants.gene_panel import ReferenceGenomeBuild


@pytest.fixture
def coverage_request(sample_id: str) -> CoverageRequest:
    return CoverageRequest(
        build=ReferenceGenomeBuild.GRCH37,
        coverage_threshold=10,
        gene_ids=[2861, 3791, 6481, 7436, 30521],
        interval_type="genes",
        samples=[
            Chanjo2Sample(
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

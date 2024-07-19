"""Chanjo2 API model fixtures."""

import pytest

from cg.clients.chanjo2.models import CoverageRequest, Sample
from cg.constants.gene_panel import ReferenceGenomeBuild


@pytest.fixture
def coverage_request(sample_id: str) -> CoverageRequest:
    return CoverageRequest(
        build=ReferenceGenomeBuild.GRCH37,
        coverage_threshold=10,
        gene_ids=[2861, 3791, 6481, 7436, 30521],
        interval_type="genes",
        samples=[
            Sample(
                coverage_path=f"/path/to/coverage/{sample_id}.d4",
                id=sample_id,
            )
        ],
    )

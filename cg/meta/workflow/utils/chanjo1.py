"""Chanjo1 coverage utilities for workflow analysis APIs."""

import logging

from cg.apps.coverage import ChanjoAPI
from cg.clients.chanjo2.models import CoverageMetricsChanjo1

LOG = logging.getLogger(__name__)


def get_sample_coverage(
    chanjo_api: ChanjoAPI, sample_id: str, gene_ids: list[int]
) -> CoverageMetricsChanjo1 | None:
    sample_coverage: dict = chanjo_api.sample_coverage(sample_id=sample_id, panel_genes=gene_ids)
    if sample_coverage:
        return CoverageMetricsChanjo1(
            coverage_completeness_percent=sample_coverage.get("mean_completeness"),
            mean_coverage=sample_coverage.get("mean_coverage"),
        )
    LOG.warning(f"Could not calculate sample coverage for: {sample_id}")
    return None

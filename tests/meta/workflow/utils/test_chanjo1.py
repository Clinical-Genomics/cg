from unittest.mock import Mock, create_autospec

from pytest_mock import MockerFixture

from cg.apps.coverage.chanjo_api import ChanjoAPI
from cg.clients.chanjo2.models import CoverageMetricsChanjo1
from cg.meta.workflow.utils import chanjo1
from cg.store.models import Sample


def test_get_sample_coverage(mocker: MockerFixture):
    # GIVEN a sample
    sample: Sample = create_autospec(Sample, internal_id="internal_id")

    # GIVEN a mocked chanjo API
    chanjo_api = create_autospec(ChanjoAPI)
    chanjo_api.sample_coverage = Mock(
        return_value={"mean_coverage": 28.9, "mean_completeness": 88.5}
    )

    # GIVEN some gene ids
    gene_ids: list[int] = [5, 8]

    # WHEN getting the chanjo coverage for the sample
    sample_coverage: CoverageMetricsChanjo1 | None = chanjo1.get_sample_coverage(
        chanjo_api=chanjo_api,
        sample_id=sample.internal_id,
        gene_ids=gene_ids,
    )

    assert sample_coverage == CoverageMetricsChanjo1(
        coverage_completeness_percent=88.5, mean_coverage=28.9
    )

    # THEN the sample coverage should have been called with the right information
    chanjo_api.sample_coverage.assert_called_once_with(
        sample_id="internal_id", panel_genes=gene_ids
    )

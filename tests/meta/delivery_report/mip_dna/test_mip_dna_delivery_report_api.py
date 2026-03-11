from unittest.mock import Mock, create_autospec

from pytest_mock import MockerFixture

from cg.apps.coverage import ChanjoAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims.api import LimsAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.constants.constants import GenomeBuild
from cg.meta.delivery.delivery import DeliveryAPI
from cg.meta.delivery_report import mip_dna as mip_dna_delivery_report
from cg.meta.delivery_report.mip_dna import MipDNADeliveryReportAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Sample
from cg.store.store import Store


def test_mip_dna_get_sample_coverage(mocker: MockerFixture):
    """Test that get_sample_coverage returns coverage data from chanjo."""

    # GIVEN a chanjo API returning coverage for the sample
    expected_coverage = {"mean_coverage": 30.0, "mean_completeness": 95.0}
    chanjo_api = create_autospec(ChanjoAPI)
    chanjo_api.sample_coverage.return_value = expected_coverage
    mock_chanjo_factory = mocker.patch.object(
        mip_dna_delivery_report, "chanjo_api_for_genome_build", return_value=chanjo_api
    )

    # GIVEN a scout API returning genes for a panel
    scout_api = create_autospec(ScoutAPI)
    scout_api.get_genes = Mock(return_value=[{"hgnc_id": 1}])

    # GIVEN a MIP-DNA delivery report API
    analysis_api = create_autospec(
        MipDNAAnalysisAPI,
        config=create_autospec(CGConfig),
        delivery_api=create_autospec(DeliveryAPI),
        housekeeper_api=create_autospec(HousekeeperAPI),
        lims_api=create_autospec(LimsAPI),
        scout_api=scout_api,
        status_db=create_autospec(Store),
    )
    delivery_report_api = MipDNADeliveryReportAPI(analysis_api=analysis_api)

    # GIVEN a case with panels and a sample
    case = create_autospec(Case, panels=["some_panel"])
    sample = create_autospec(Sample, internal_id="sample_id")

    # WHEN getting sample coverage
    result = delivery_report_api.get_sample_coverage(sample=sample, case=case)

    # THEN the expected coverage is returned
    assert result == expected_coverage

    # THEN chanjo was configured and called correctly
    mock_chanjo_factory.assert_called_once_with(
        config=analysis_api.config, genome_build=GenomeBuild.hg19
    )
    chanjo_api.sample_coverage.assert_called_once_with(sample_id="sample_id", panel_genes=[1])

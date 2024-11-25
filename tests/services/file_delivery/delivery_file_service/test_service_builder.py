from unittest.mock import MagicMock

import pytest
from _pytest.fixtures import FixtureRequest
from pydantic import BaseModel

from cg.constants import DataDelivery, Workflow
from cg.services.deliver_files.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.deliver_files.deliver_files_service.deliver_files_service_factory import (
    DeliveryServiceFactory,
)
from cg.services.deliver_files.file_fetcher.abstract import FetchDeliveryFilesService
from cg.services.deliver_files.file_fetcher.analysis_raw_data_service import (
    RawDataAndAnalysisDeliveryFileFetcher,
)
from cg.services.deliver_files.file_fetcher.analysis_service import AnalysisDeliveryFileFetcher
from cg.services.deliver_files.file_fetcher.raw_data_service import RawDataDeliveryFileFetcher
from cg.services.deliver_files.file_formatter.utils.sample_concatenation_service import (
    SampleFileConcatenationFormatter,
)
from cg.services.deliver_files.file_formatter.utils.sample_service import SampleFileFormatter
from cg.services.deliver_files.file_mover.service import DeliveryFilesMover
from cg.services.deliver_files.tag_fetcher.abstract import FetchDeliveryFileTagsService
from cg.services.deliver_files.tag_fetcher.sample_and_case_service import (
    SampleAndCaseDeliveryTagsFetcher,
)


class DeliveryServiceScenario(BaseModel):
    """Model holding the necessary parameters to build a specific delivery service."""

    app_tag: str
    data_analysis: Workflow
    delivery_type: DataDelivery
    expected_tag_fetcher: type[FetchDeliveryFileTagsService]
    expected_file_fetcher: type[FetchDeliveryFilesService]
    expected_file_mover: type[DeliveryFilesMover]
    expected_sample_file_formatter: type[SampleFileFormatter | SampleFileConcatenationFormatter]
    store_name: str


@pytest.mark.parametrize(
    "scenario",
    [
        DeliveryServiceScenario(
            app_tag="MWRNXTR003",
            data_analysis=Workflow.RAW_DATA,
            delivery_type=DataDelivery.FASTQ,
            expected_tag_fetcher=SampleAndCaseDeliveryTagsFetcher,
            expected_file_fetcher=RawDataDeliveryFileFetcher,
            expected_file_mover=DeliveryFilesMover,
            expected_sample_file_formatter=SampleFileConcatenationFormatter,
            store_name="microbial_store",
        ),
        DeliveryServiceScenario(
            app_tag="VWGDPTR001",
            data_analysis=Workflow.MUTANT,
            delivery_type=DataDelivery.ANALYSIS_FILES,
            expected_tag_fetcher=SampleAndCaseDeliveryTagsFetcher,
            expected_file_fetcher=AnalysisDeliveryFileFetcher,
            expected_file_mover=DeliveryFilesMover,
            expected_sample_file_formatter=SampleFileFormatter,
            store_name="mutant_store",
        ),
        DeliveryServiceScenario(
            app_tag="PANKTTR020",
            data_analysis=Workflow.BALSAMIC,
            delivery_type=DataDelivery.FASTQ_ANALYSIS,
            expected_tag_fetcher=SampleAndCaseDeliveryTagsFetcher,
            expected_file_fetcher=RawDataAndAnalysisDeliveryFileFetcher,
            expected_file_mover=DeliveryFilesMover,
            expected_sample_file_formatter=SampleFileFormatter,
            store_name="applications_store",
        ),
    ],
    ids=["microbial-fastq", "SARS-COV2", "Targeted"],
)
def test_build_delivery_service(scenario: DeliveryServiceScenario, request: FixtureRequest):
    # GIVEN a delivery service builder with mocked store and hk_api
    builder = DeliveryServiceFactory(
        store=request.getfixturevalue(scenario.store_name),
        hk_api=MagicMock(),
        rsync_service=MagicMock(),
        tb_service=MagicMock(),
        analysis_service=MagicMock(),
    )

    # GIVEN a case with mocked sample app tag
    case_mock = MagicMock()
    case_mock.data_delivery = scenario.delivery_type
    case_mock.data_analysis = scenario.data_analysis
    case_mock.samples = [
        MagicMock(application_version=MagicMock(application=MagicMock(tag=scenario.app_tag)))
    ]

    # WHEN building a delivery service
    delivery_service: DeliverFilesService = builder.build_delivery_service(case=case_mock)

    # THEN the correct file formatter and file fetcher services are used
    assert isinstance(delivery_service.file_manager.tags_fetcher, scenario.expected_tag_fetcher)
    assert isinstance(delivery_service.file_manager, scenario.expected_file_fetcher)
    assert isinstance(delivery_service.file_mover, scenario.expected_file_mover)
    assert isinstance(
        delivery_service.file_formatter.sample_file_formatter,
        scenario.expected_sample_file_formatter,
    )

from unittest.mock import MagicMock

import pytest
from _pytest.fixtures import FixtureRequest
from pydantic import BaseModel

from cg.constants import DataDelivery, Workflow
from cg.services.deliver_files.constants import DeliveryDestination, DeliveryStructure
from cg.services.deliver_files.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.deliver_files.factory import (
    DeliveryServiceFactory,
)
from cg.services.deliver_files.file_fetcher.abstract import FetchDeliveryFilesService
from cg.services.deliver_files.file_fetcher.analysis_raw_data_service import (
    RawDataAndAnalysisDeliveryFileFetcher,
)
from cg.services.deliver_files.file_fetcher.analysis_service import AnalysisDeliveryFileFetcher
from cg.services.deliver_files.file_fetcher.raw_data_service import RawDataDeliveryFileFetcher
from cg.services.deliver_files.file_formatter.files.mutant_service import (
    MutantFileFormatter,
)
from cg.services.deliver_files.file_formatter.files.concatenation_service import (
    SampleFileConcatenationFormatter,
)
from cg.services.deliver_files.file_formatter.files.sample_service import (
    SampleFileFormatter,
)
from cg.services.deliver_files.file_formatter.path_name.abstract import PathNameFormatter
from cg.services.deliver_files.file_formatter.path_name.flat_structure import (
    FlatStructurePathFormatter,
)
from cg.services.deliver_files.file_formatter.path_name.nested_structure import (
    NestedStructurePathFormatter,
)
from cg.services.deliver_files.file_mover.abstract import DestinationFilesMover
from cg.services.deliver_files.file_mover.base_service import BaseDestinationFilesMover
from cg.services.deliver_files.file_mover.customer_inbox_service import (
    CustomerInboxDestinationFilesMover,
)
from cg.services.deliver_files.tag_fetcher.abstract import FetchDeliveryFileTagsService
from cg.services.deliver_files.tag_fetcher.fohm_upload_service import FOHMUploadTagsFetcher
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
    expected_file_mover: type[DestinationFilesMover]
    expected_sample_file_formatter: type[
        SampleFileFormatter | SampleFileConcatenationFormatter | MutantFileFormatter
    ]
    expected_path_name_formatter: type[PathNameFormatter]
    store_name: str
    delivery_destination: DeliveryDestination
    delivery_structure: DeliveryStructure


@pytest.mark.parametrize(
    "scenario",
    [
        DeliveryServiceScenario(
            app_tag="MWRNXTR003",
            data_analysis=Workflow.RAW_DATA,
            delivery_type=DataDelivery.FASTQ,
            expected_tag_fetcher=SampleAndCaseDeliveryTagsFetcher,
            expected_file_fetcher=RawDataDeliveryFileFetcher,
            expected_file_mover=CustomerInboxDestinationFilesMover,
            expected_sample_file_formatter=SampleFileConcatenationFormatter,
            expected_path_name_formatter=NestedStructurePathFormatter,
            store_name="microbial_store",
            delivery_destination=DeliveryDestination.CUSTOMER,
            delivery_structure=DeliveryStructure.NESTED,
        ),
        DeliveryServiceScenario(
            app_tag="VWGDPTR001",
            data_analysis=Workflow.MUTANT,
            delivery_type=DataDelivery.ANALYSIS_FILES,
            expected_tag_fetcher=SampleAndCaseDeliveryTagsFetcher,
            expected_file_fetcher=AnalysisDeliveryFileFetcher,
            expected_file_mover=CustomerInboxDestinationFilesMover,
            expected_sample_file_formatter=MutantFileFormatter,
            expected_path_name_formatter=NestedStructurePathFormatter,
            store_name="mutant_store",
            delivery_destination=DeliveryDestination.CUSTOMER,
            delivery_structure=DeliveryStructure.NESTED,
        ),
        DeliveryServiceScenario(
            app_tag="PANKTTR020",
            data_analysis=Workflow.BALSAMIC,
            delivery_type=DataDelivery.FASTQ_ANALYSIS,
            expected_tag_fetcher=SampleAndCaseDeliveryTagsFetcher,
            expected_file_fetcher=RawDataAndAnalysisDeliveryFileFetcher,
            expected_file_mover=CustomerInboxDestinationFilesMover,
            expected_sample_file_formatter=SampleFileFormatter,
            expected_path_name_formatter=NestedStructurePathFormatter,
            store_name="applications_store",
            delivery_destination=DeliveryDestination.CUSTOMER,
            delivery_structure=DeliveryStructure.NESTED,
        ),
        DeliveryServiceScenario(
            app_tag="VWGDPTR001",
            data_analysis=Workflow.MUTANT,
            delivery_type=DataDelivery.ANALYSIS_FILES,
            expected_tag_fetcher=FOHMUploadTagsFetcher,
            expected_file_fetcher=AnalysisDeliveryFileFetcher,
            expected_file_mover=BaseDestinationFilesMover,
            expected_sample_file_formatter=MutantFileFormatter,
            expected_path_name_formatter=FlatStructurePathFormatter,
            store_name="mutant_store",
            delivery_destination=DeliveryDestination.FOHM,
            delivery_structure=DeliveryStructure.FLAT,
        ),
        DeliveryServiceScenario(
            app_tag="VWGDPTR001",
            data_analysis=Workflow.MUTANT,
            delivery_type=DataDelivery.ANALYSIS_FILES,
            expected_tag_fetcher=SampleAndCaseDeliveryTagsFetcher,
            expected_file_fetcher=AnalysisDeliveryFileFetcher,
            expected_file_mover=BaseDestinationFilesMover,
            expected_sample_file_formatter=MutantFileFormatter,
            expected_path_name_formatter=FlatStructurePathFormatter,
            store_name="mutant_store",
            delivery_destination=DeliveryDestination.BASE,
            delivery_structure=DeliveryStructure.FLAT,
        ),
    ],
    ids=["microbial-fastq", "SARS-COV2", "Targeted", "FOHM Upload", "base"],
)
def test_build_delivery_service(scenario: DeliveryServiceScenario, request: FixtureRequest):
    # GIVEN a delivery service builder with mocked store and hk_api
    builder = DeliveryServiceFactory(
        lims_api=MagicMock(),
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
    delivery_service: DeliverFilesService = builder.build_delivery_service(
        case=case_mock,
        delivery_destination=scenario.delivery_destination,
        delivery_structure=scenario.delivery_structure,
    )

    # THEN the correct file formatter and file fetcher services are used
    assert isinstance(delivery_service.file_manager.tags_fetcher, scenario.expected_tag_fetcher)
    assert isinstance(delivery_service.file_manager, scenario.expected_file_fetcher)
    assert isinstance(delivery_service.file_mover, scenario.expected_file_mover)
    assert isinstance(
        delivery_service.file_formatter.sample_file_formatter,
        scenario.expected_sample_file_formatter,
    )
    if not isinstance(delivery_service.file_formatter.sample_file_formatter, MutantFileFormatter):
        assert isinstance(
            delivery_service.file_formatter.sample_file_formatter.path_name_formatter,
            scenario.expected_path_name_formatter,
        )
        assert isinstance(
            delivery_service.file_formatter.case_file_formatter.path_name_formatter,
            scenario.expected_path_name_formatter,
        )

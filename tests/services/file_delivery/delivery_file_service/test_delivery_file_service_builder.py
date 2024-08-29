import pytest
from unittest.mock import MagicMock, patch

from cg.constants import Workflow, DataDelivery
from cg.services.file_delivery.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.file_delivery.deliver_files_service.deliver_files_service_factory import (
    DeliveryServiceFactory,
)
from cg.services.file_delivery.fetch_delivery_files_tags.fetch_sample_and_case_delivery_file_tags_service import (
    FetchSampleAndCaseDeliveryFileTagsService,
)
from cg.services.file_delivery.fetch_file_service.fetch_analysis_files_service import (
    FetchAnalysisDeliveryFilesService,
)
from cg.services.file_delivery.fetch_file_service.fetch_fastq_analysis_files_service import (
    FetchFastqAndAnalysisDeliveryFilesService,
)
from cg.services.file_delivery.fetch_file_service.fetch_fastq_files_service import (
    FetchFastqDeliveryFilesService,
)
from cg.services.file_delivery.file_formatter_service.utils.sample_file_concatenation_formatter import (
    SampleFileConcatenationFormatter,
)
from cg.services.file_delivery.file_formatter_service.utils.sample_file_formatter import (
    SampleFileFormatter,
)
from cg.services.file_delivery.move_files_service.move_delivery_files_service import (
    MoveDeliveryFilesService,
)


@pytest.mark.parametrize(
    "workflow,delivery_type,expected_tag_fetcher,expected_file_fetcher,expected_file_mover,expected_sample_file_formatter",
    [
        (
            Workflow.MICROSALT,
            DataDelivery.FASTQ,
            FetchSampleAndCaseDeliveryFileTagsService,
            FetchFastqDeliveryFilesService,
            MoveDeliveryFilesService,
            SampleFileConcatenationFormatter,
        ),
        (
            Workflow.MUTANT,
            DataDelivery.ANALYSIS_FILES,
            FetchSampleAndCaseDeliveryFileTagsService,
            FetchAnalysisDeliveryFilesService,
            MoveDeliveryFilesService,
            SampleFileConcatenationFormatter,
        ),
        (
            Workflow.BALSAMIC,
            DataDelivery.FASTQ_ANALYSIS,
            FetchSampleAndCaseDeliveryFileTagsService,
            FetchFastqAndAnalysisDeliveryFilesService,
            MoveDeliveryFilesService,
            SampleFileFormatter,
        ),
    ],
)
def test_build_delivery_service(
    workflow,
    delivery_type,
    expected_tag_fetcher,
    expected_file_fetcher,
    expected_file_mover,
    expected_sample_file_formatter,
):
    # GIVEN a delivery service builder with mocked store and hk_api
    store_mock = MagicMock()
    hk_api_mock = MagicMock()
    builder = DeliveryServiceFactory(store=store_mock, hk_api=hk_api_mock)

    # WHEN building a delivery service
    delivery_service: DeliverFilesService = builder.build_delivery_service(
        workflow=workflow, delivery_type=delivery_type
    )

    # THEN the correct file formatter and file fetcher services are used
    assert isinstance(delivery_service.file_manager.tags_fetcher, expected_tag_fetcher)
    assert isinstance(delivery_service.file_manager, expected_file_fetcher)
    assert isinstance(delivery_service.file_mover, expected_file_mover)
    assert isinstance(
        delivery_service.file_formatter.sample_file_formatter, expected_sample_file_formatter
    )

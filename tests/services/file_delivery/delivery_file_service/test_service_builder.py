import pytest
from unittest.mock import MagicMock

from cg.constants import Workflow, DataDelivery
from cg.services.deliver_files.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.deliver_files.deliver_files_service.deliver_files_service_factory import (
    DeliveryServiceFactory,
)
from cg.services.deliver_files.tag_fetcher.sample_and_case_service import (
    SampleAndCaseDeliveryTagsFetcher,
)
from cg.services.deliver_files.file_fetcher.analysis_service import (
    AnalysisDeliveryFileFetcher,
)
from cg.services.deliver_files.file_fetcher.analysis_raw_data_service import (
    RawDataAndAnalysisDeliveryFileFetcher,
)
from cg.services.deliver_files.file_fetcher.raw_data_service import (
    RawDataDeliveryFileFetcher,
)
from cg.services.deliver_files.file_formatter.utils.sample_concatenation_service import (
    SampleFileConcatenationFormatter,
)
from cg.services.deliver_files.file_formatter.utils.sample_service import (
    SampleFileFormatter,
)
from cg.services.deliver_files.file_mover.service import (
    DeliveryFilesMover,
)


@pytest.mark.parametrize(
    "workflow,delivery_type,expected_tag_fetcher,expected_file_fetcher,expected_file_mover,expected_sample_file_formatter",
    [
        (
            Workflow.MICROSALT,
            DataDelivery.FASTQ,
            SampleAndCaseDeliveryTagsFetcher,
            RawDataDeliveryFileFetcher,
            DeliveryFilesMover,
            SampleFileConcatenationFormatter,
        ),
        (
            Workflow.MUTANT,
            DataDelivery.ANALYSIS_FILES,
            SampleAndCaseDeliveryTagsFetcher,
            AnalysisDeliveryFileFetcher,
            DeliveryFilesMover,
            SampleFileFormatter,
        ),
        (
            Workflow.BALSAMIC,
            DataDelivery.FASTQ_ANALYSIS,
            SampleAndCaseDeliveryTagsFetcher,
            RawDataAndAnalysisDeliveryFileFetcher,
            DeliveryFilesMover,
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
    builder = DeliveryServiceFactory(
        store=MagicMock(),
        hk_api=MagicMock(),
        rsync_service=MagicMock(),
        tb_service=MagicMock(),
        analysis_service=MagicMock(),
    )

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

from pathlib import Path
from unittest import mock
from unittest.mock import Mock

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.services.deliver_files.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.deliver_files.deliver_files_service.deliver_files_service_factory import (
    DeliveryServiceFactory,
)
from cg.services.deliver_files.file_fetcher.exc import NoDeliveryFilesError
from cg.services.deliver_files.file_fetcher.models import DeliveryFiles
from cg.services.deliver_files.file_formatter.models import FormattedFile
from cg.store.models import Case
from cg.store.store import Store


def test_file_delivery_service_no_files(empty_delivery_files: DeliveryFiles):
    # GIVEN a delivery file service with no files to deliver
    file_delivery_service = DeliverFilesService(
        delivery_file_manager_service=Mock(),
        move_file_service=Mock(),
        file_filter=Mock(),
        file_formatter_service=Mock(),
        rsync_service=Mock(),
        tb_service=Mock(),
        analysis_service=Mock(),
        status_db=Mock(),
    )

    # WHEN getting the files to deliver that raises an NoDeliveryFilesError

    # THEN the service should return immediately without any errors
    with mock.patch.object(
        file_delivery_service.file_manager,
        "get_files_to_deliver",
        side_effect=NoDeliveryFilesError,
    ):
        file_delivery_service.deliver_files_for_case(case=Mock(), delivery_base_path=Mock())

    assert not file_delivery_service.file_mover.move_files.called
    assert not file_delivery_service.file_formatter.format_files.called
    assert not file_delivery_service.rsync_service.rsync_files.called
    assert not file_delivery_service.tb_service.add_rsync_job.called
    assert not file_delivery_service.analysis_service.update_status.called


def test_deliver_files_for_case(
    case_id: str,
    delivery_store_microsalt: Store,
    tmp_path: Path,
    expected_fastq_delivery_files: DeliveryFiles,
    expected_concatenated_fastq_formatted_files: list[FormattedFile],
):
    # GIVEN a case with samples that are present in Housekeeper and the Store
    case: Case = delivery_store_microsalt.get_case_by_internal_id(case_id)
    case.data_analysis = Workflow.RAW_DATA
    factory = DeliveryServiceFactory(
        lims_api=Mock(),
        store=delivery_store_microsalt,
        hk_api=Mock(),
        rsync_service=Mock(),
        tb_service=Mock(),
        analysis_service=Mock(),
    )
    delivery_service = factory.build_delivery_service(case=case)

    # GIVEN that the correct files are fetched
    with mock.patch.object(
        delivery_service.file_manager,
        "get_files_to_deliver",
        return_value=expected_fastq_delivery_files,
    ):
        # WHEN delivering files for the case
        delivery_service.deliver_files_for_case(case=case, delivery_base_path=tmp_path)

    # THEN assert that the files are moved and formatted
    for formatted_file in expected_concatenated_fastq_formatted_files:
        assert formatted_file.formatted_path.exists()

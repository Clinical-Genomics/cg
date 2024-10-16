from unittest import mock
from unittest.mock import Mock

from cg.services.deliver_files.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.deliver_files.file_fetcher.exc import NoDeliveryFilesError
from cg.services.deliver_files.file_fetcher.models import DeliveryFiles


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

"""Test the move delivery files service."""

import pytest

from cg.services.deliver_files.file_fetcher.models import DeliveryFiles
from cg.services.deliver_files.file_mover.delivery_files_mover import (
    DeliveryFilesMover,
)
from cg.services.deliver_files.file_mover.fohm_upload_files_mover import GenericFilesMover
from cg.services.deliver_files.utils import FileMover, FileManager


@pytest.mark.parametrize(
    "expected_moved_delivery_files,delivery_files,move_files_service",
    [
        (
            "expected_moved_fastq_delivery_files",
            "expected_fastq_delivery_files",
            DeliveryFilesMover(FileMover(FileManager())),
        ),
        (
            "expected_moved_analysis_delivery_files",
            "expected_analysis_delivery_files",
            DeliveryFilesMover(FileMover(FileManager())),
        ),
        (
            "expected_moved_upload_files",
            "expected_upload_files",
            GenericFilesMover(FileMover(FileManager())),
        ),
    ],
)
def test_move_files(
    expected_moved_delivery_files: DeliveryFiles,
    delivery_files: DeliveryFiles,
    move_files_service: DeliveryFilesMover,
    tmp_path,
    request,
):
    # GIVEN a delivery files to move
    expected_moved_delivery_files: DeliveryFiles = request.getfixturevalue(
        expected_moved_delivery_files
    )
    delivery_files: DeliveryFiles = request.getfixturevalue(delivery_files)

    # WHEN moving the delivery files
    moved_delivery_files: DeliveryFiles = move_files_service.move_files(
        delivery_files=delivery_files, delivery_base_path=tmp_path
    )

    # THEN assert that the delivery files are moved
    assert moved_delivery_files == expected_moved_delivery_files
    if case_files := moved_delivery_files.case_files:
        for case_file in case_files:
            assert case_file.file_path.exists()
    for sample_file in moved_delivery_files.sample_files:
        assert sample_file.file_path.exists()

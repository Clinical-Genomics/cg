from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest

from cg.constants.constants import FileFormat
from cg.constants.pacbio import PacBioDirsAndFiles
from cg.services.decompression_service.decompressor import Decompressor
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.run_devices.pacbio.run_file_manager.models import PacBioRunValidatorFiles
from cg.services.run_devices.pacbio.run_file_manager.run_file_manager import PacBioRunFileManager
from cg.services.run_devices.pacbio.run_validator.pacbio_run_validator import PacBioRunValidator
from cg.services.validate_file_transfer_service.validate_file_transfer_service import (
    ValidateFileTransferService,
)


@pytest.fixture
def run_validator() -> PacBioRunValidator:
    return PacBioRunValidator(
        decompressor=create_autospec(Decompressor),
        file_transfer_validator=create_autospec(ValidateFileTransferService),
        file_manager=Mock(),
    )


@pytest.fixture
def run_data(tmp_path: Path) -> PacBioRunData:
    return PacBioRunData(
        full_path=tmp_path,
        run_id="not_relevant",
        well_name="not_relevant",
        plate=1,
    )


def test_pacbio_run_validator(run_data: PacBioRunData, run_validator: PacBioRunValidator):
    """Test that the run validator flow works as expected."""
    # GIVEN PacBio run data and a PacBio run validator

    # GIVEN that the files that should be unzipped are not unzipped yet
    file_manager: PacBioRunFileManager = create_autospec(PacBioRunFileManager)
    file_manager.get_unzipped_files = Mock(return_value=[Path(run_data.full_path, "some_file.txt")])

    # GIVEN that the run has correct validator files
    manifest_file = Path("some_manifest.txt")
    decompression_target = Path("decompression_dir")
    decompression_destination = Path("decompression_dest_dir")
    file_manager.get_run_validation_files = Mock(
        return_value=PacBioRunValidatorFiles(
            manifest_file=manifest_file,
            decompression_target=decompression_target,
            decompression_destination=decompression_destination,
        )
    )
    run_validator.file_manager = file_manager

    # WHEN ensuring post-processing can start
    run_validator.ensure_post_processing_can_start(run_data)

    # THEN the run is validated
    run_validator.file_manager.get_run_validation_files.assert_called_once_with(run_data)
    run_validator.file_transfer_validator.validate_file_transfer.assert_called_once_with(
        manifest_file=manifest_file,
        source_dir=run_data.full_path,
        manifest_file_format=FileFormat.TXT,
    )
    run_validator.decompressor.decompress.assert_called_once_with(
        source_path=decompression_target, destination_path=decompression_destination
    )
    assert Path(run_data.full_path, PacBioDirsAndFiles.RUN_IS_VALID).exists()


def test_pacbio_run_validator_skip_if_validated(
    run_data: PacBioRunData, run_validator: PacBioRunValidator
):
    """Test that the run validator skips validation if the run is already validated."""
    # GIVEN run data and a run validator

    # GIVEN that the run is already validated
    run_validator._touch_is_validated(run_data.full_path)

    # WHEN ensuring post-processing can start
    run_validator.ensure_post_processing_can_start(run_data)

    # THEN the validation flow is skipped as the run is already validated
    assert Path(run_data.full_path, PacBioDirsAndFiles.RUN_IS_VALID).exists()
    run_validator.file_manager.get_run_validation_files.assert_not_called()
    run_validator.file_transfer_validator.validate_file_transfer.assert_not_called()
    run_validator.decompressor.decompress.assert_not_called()


def test_pacbio_run_validator_skip_decompression(
    run_data: PacBioRunData, run_validator: PacBioRunValidator
):
    # GIVEN that the files have already been decompressed
    file_manager: PacBioRunFileManager = create_autospec(PacBioRunFileManager)
    base_path = Path(
        run_data.full_path,
        PacBioDirsAndFiles.STATISTICS_DIR,
        PacBioDirsAndFiles.UNZIPPED_REPORTS_DIR,
    )
    base_path.mkdir(parents=True, exist_ok=True)
    decompressed_files: list[Path] = [
        Path(base_path, PacBioDirsAndFiles.BARCODES_REPORT),
        Path(base_path, PacBioDirsAndFiles.CONTROL_REPORT),
        Path(base_path, PacBioDirsAndFiles.LOADING_REPORT),
        Path(base_path, PacBioDirsAndFiles.RAW_DATA_REPORT),
        Path(base_path, PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT),
    ]
    for file in decompressed_files:
        file.touch()
    file_manager.get_files_to_parse = Mock(return_value=decompressed_files)
    run_validator.file_manager = file_manager

    # WHEN ensuring post-processing can start
    run_validator.ensure_post_processing_can_start(run_data)

    # THEN the decompression process is not performed
    run_validator.file_manager.get_run_validation_files.assert_called_once_with(run_data)
    run_validator.file_transfer_validator.validate_file_transfer.assert_called_once()
    run_validator.decompressor.decompress.assert_not_called()
    assert Path(run_data.full_path, PacBioDirsAndFiles.RUN_IS_VALID).exists()

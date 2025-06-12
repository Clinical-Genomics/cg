from pathlib import Path

from cg.constants.pacbio import PacBioDirsAndFiles
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.run_devices.pacbio.run_validator.pacbio_run_validator import PacBioRunValidator


def test_pacbio_run_validator(tmp_path: Path, mock_pacbio_run_validator: PacBioRunValidator):
    """Test that the run validator flow works as expected."""
    # GIVEN run data and a run validator
    run_data = PacBioRunData(
        full_path=tmp_path,
        sequencing_run_name="not_relevant",
        well_name="not_relevant",
        plate=1,
    )

    # WHEN ensuring post-processing can start
    mock_pacbio_run_validator.ensure_post_processing_can_start(run_data)

    # THEN the run is validated
    assert mock_pacbio_run_validator.file_manager.get_run_validation_files.call_count == 1
    assert mock_pacbio_run_validator.file_transfer_validator.validate_file_transfer.call_count == 1
    assert mock_pacbio_run_validator.decompressor.decompress.call_count == 1
    assert Path(run_data.full_path, PacBioDirsAndFiles.RUN_IS_VALID).exists()


def test_pacbio_run_validator_skip_if_validated(
    tmp_path: Path, mock_pacbio_run_validator: PacBioRunValidator
):
    """Test that the run validator skips validation if the run is already validated."""
    # GIVEN run data and a run validator
    run_data = PacBioRunData(
        full_path=tmp_path,
        sequencing_run_name="not_relevant",
        well_name="not_relevant",
        plate=1,
    )

    # GIVEN that the run is already validated
    mock_pacbio_run_validator._touch_is_validated(run_data.full_path)

    # WHEN ensuring post-processing can start
    mock_pacbio_run_validator.ensure_post_processing_can_start(run_data)

    # THEN the validation flow is skipped as the run is already validated
    assert Path(run_data.full_path, PacBioDirsAndFiles.RUN_IS_VALID).exists()
    assert mock_pacbio_run_validator.file_manager.get_run_validation_files.call_count == 0
    assert mock_pacbio_run_validator.file_transfer_validator.validate_file_transfer.call_count == 0
    assert mock_pacbio_run_validator.decompressor.decompress.call_count == 0

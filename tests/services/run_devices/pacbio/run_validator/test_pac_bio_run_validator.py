from pathlib import Path
from unittest.mock import Mock

from cg.constants.pacbio import PacBioDirsAndFiles
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.run_devices.pacbio.run_validator.pacbio_run_validator import PacBioRunValidator


def test_pac_bio_run_validator(tmp_path: Path):
    # GIVEN run data and a run validator
    run_data = PacBioRunData(
        full_path=Path(tmp_path),
        sequencing_run_name="not_relevant",
        well_name="not_relevant",
        plate=1,
    )
    run_validator = PacBioRunValidator(
        decompressor=Mock(),
        file_transfer_validator=Mock(),
        file_manager=Mock(),
    )

    # WHEN ensuring post processing can start
    run_validator.ensure_post_processing_can_start(run_data)

    # THEN the run is validated
    assert run_validator.file_manager.get_run_validation_files.call_count == 1
    assert run_validator.file_transfer_validator.validate_file_transfer.call_count == 1
    assert run_validator.decompressor.decompress.call_count == 1
    assert Path(run_data.full_path, PacBioDirsAndFiles.RUN_IS_VALID).exists()


def test_pac_bio_run_validator_skip_if_validated(tmp_path: Path):
    # GIVEN run data and a run validator
    run_data = PacBioRunData(
        full_path=Path(tmp_path),
        sequencing_run_name="not_relevant",
        well_name="not_relevant",
        plate=1,
    )
    run_validator = PacBioRunValidator(
        decompressor=Mock(),
        file_transfer_validator=Mock(),
        file_manager=Mock(),
    )
    run_validator._touch_is_validated(run_data.full_path)

    # WHEN ensuring post processing can start
    run_validator.ensure_post_processing_can_start(run_data)

    # THEN the run is validated
    assert Path(run_data.full_path, PacBioDirsAndFiles.RUN_IS_VALID).exists()
    assert run_validator.file_manager.get_run_validation_files.call_count == 0
    assert run_validator.file_transfer_validator.validate_file_transfer.call_count == 0
    assert run_validator.decompressor.decompress.call_count == 0

import logging
from pathlib import Path

from cg.constants.constants import FileFormat
from cg.constants.pacbio import PacBioDirsAndFiles
from cg.services.decompression_service.decompressor import Decompressor
from cg.services.run_devices.abstract_classes import RunValidator
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.run_devices.pacbio.run_file_manager.models import PacBioRunValidatorFiles
from cg.services.run_devices.pacbio.run_file_manager.run_file_manager import PacBioRunFileManager
from cg.services.validate_file_transfer_service.validate_file_transfer_service import (
    ValidateFileTransferService,
)

LOG = logging.getLogger(__name__)


class PacBioRunValidator(RunValidator):
    """
    PacBio run validator.
    Ensure that the post-processing of a pacbio run can start.
    """

    def __init__(
        self,
        decompressor: Decompressor,
        file_transfer_validator: ValidateFileTransferService,
        file_manager: PacBioRunFileManager,
    ):
        self.decompressor = decompressor
        self.file_transfer_validator = file_transfer_validator
        self.file_manager = file_manager

    def ensure_post_processing_can_start(self, run_data: PacBioRunData) -> None:
        """
        Ensure that a post-processing run can start.
        1. Check if all files are present listed in a manifest file.
        2. Decompresses the zipped reports.
        3. Touches a file to indicate that the run is validated
        4. Skips validation if the run is already validated
        """
        if self._is_validated(run_data.full_path):
            LOG.debug(f"Run for {run_data.full_path} is validated.")
            return
        paths_information: PacBioRunValidatorFiles = self.file_manager.get_run_validation_files(
            run_data
        )
        self.file_transfer_validator.validate_file_transfer(
            manifest_file=paths_information.manifest_file,
            source_dir=run_data.full_path,
            manifest_file_format=FileFormat.TXT,
        )
        self.decompressor.decompress(
            source_path=paths_information.decompression_target,
            destination_path=paths_information.decompression_destination,
        )
        self._touch_is_validated(run_data.full_path)
        LOG.debug(f"Run for {run_data.full_path} is validated.")

    @staticmethod
    def _is_validated(run_path: Path) -> bool:
        return Path(run_path, PacBioDirsAndFiles.RUN_IS_VALID).exists()

    @staticmethod
    def _touch_is_validated(run_path: Path) -> None:
        Path(run_path, PacBioDirsAndFiles.RUN_IS_VALID).touch()

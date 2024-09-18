from pathlib import Path

from cg.constants.constants import FileFormat
from cg.services.decompression_service.decompressor import Decompressor
from cg.services.run_devices.abstract_classes import RunValidator
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.run_devices.pacbio.run_file_manager.models import PacBioRunValidatorFiles
from cg.services.run_devices.pacbio.run_file_manager.run_file_manager import PacBioRunFileManager
from cg.services.validate_file_transfer_service.validate_file_transfer_service import (
    ValidateFileTransferService,
)


class PacBioRunValidator(RunValidator):
    """PacBio run validator.
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

    def ensure_post_processing_can_start(self, run_data: PacBioRunData):
        """Ensure that a post processing run can start."""
        paths_information: PacBioRunValidatorFiles = self.file_manager.get_run_validation_files(
            run_data
        )
        self.file_transfer_validator.validate_file_transfer(
            manifest_file=paths_information.manifest_file,
            source_dir=run_data.full_path,
            manifest_file_format=FileFormat.TXT,
        )
        if not self._is_decompressed_folder_present(paths_information):
            self.decompressor.decompress(
                source_path=paths_information.decompression_target,
                destination_path=paths_information.decompression_destination,
            )

    @staticmethod
    def _is_decompressed_folder_present(paths_information: PacBioRunValidatorFiles) -> bool:
        return paths_information.decompression_destination.exists()

from pathlib import Path
import logging

from cg.constants.file_transfer_service import PACBIO_MANIFEST_FILE_PATTERN, TRANSFER_VALIDATED_FILE
from cg.constants.constants import FileFormat
from cg.io.controller import WriteFile
from cg.models.cg_config import CGConfig
from cg.services.validate_file_transfer_service.validate_file_transfer_service import (
    ValidateFileTransferService,
)


LOG = logging.getLogger(__name__)


class ValidatePacbioFileTransferService(ValidateFileTransferService):

    def __init__(self, config: CGConfig):
        super().__init__()
        self.config: CGConfig = config
        self.data_dir: Path = Path(self.config.run_instruments.pacbio.data_dir)
        self.trigger_dir: Path = Path(self.config.run_instruments.pacbio.systemd_trigger_dir)

    @staticmethod
    def get_run_id(manifest_file_path: Path) -> str:
        return manifest_file_path.parent.parent.parent.name

    def get_flow_cell_id(self) -> str:
        return self.get_flow_cell_path.name

    @staticmethod
    def get_flow_cell_path(manifest_file_path: Path) -> Path:
        return manifest_file_path.parent.parent

    @staticmethod
    def transfer_validated_file_name(manifest_file_path: Path) -> str:
        return f"{manifest_file_path.parent}/{TRANSFER_VALIDATED_FILE}"

    def create_validated_transfer_file(self, manifest_file_path: Path) -> None:
        file_name: str = self.transfer_validated_file_name(manifest_file_path)
        writer = WriteFile()
        writer.write_file(file_name=file_name, content="")
        LOG.debug(f"Created validated transfer file {file_name}")

    def is_transfer_validated(self, manifest_file_path: Path) -> bool:
        return Path(self.transfer_validated_file_name(manifest_file_path)).exists()

    def create_systemd_trigger_file(self, manifest_file_path: Path) -> None:
        systemd_trigger_file_name = (
            f"{self.trigger_dir}/{self.get_run_id(manifest_file_path)}-{self.get_flow_cell_id()}"
        )
        writer = WriteFile()
        writer.write_file(file_name=systemd_trigger_file_name, content="")
        LOG.debug(f"Created systemd trigger file {systemd_trigger_file_name}")

    def validate_transfer_done(self, manifest_file_path: Path) -> bool:
        if not self.validate_by_manifest_file(
            manifest_file=manifest_file_path,
            source_dir=self.get_flow_cell_path(manifest_file_path),
            manifest_file_format=FileFormat.TXT,
        ):
            LOG.error(
                f"Transfer not done for run {self.get_run_id(manifest_file_path)} and flow cell {self.get_flow_cell_id()}"
            )
            return False
        self.create_validated_transfer_file(manifest_file_path)
        self.create_systemd_trigger_file(manifest_file_path)
        return True

    def validate_all_transfer_done(self) -> None:
        manifest_file_paths = self.get_manifest_file_paths(
            source_dir=self.data_dir, pattern=PACBIO_MANIFEST_FILE_PATTERN
        )
        for manifest_file_path in manifest_file_paths:
            if not self.is_transfer_validated(manifest_file_path):
                self.validate_transfer_done(manifest_file_path)

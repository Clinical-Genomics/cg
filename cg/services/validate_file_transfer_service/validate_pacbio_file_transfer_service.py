from pathlib import Path
import logging
from cg.constants.constants import FileFormat
from cg.models.cg_config import CGConfig
from cg.services.validate_file_transfer_service.validate_file_transfer_service import (
    ValidateFileTransferService,
)
from cg.utils.files import (
    get_directories_in_path,
    get_file_in_directory_with_pattern,
)

LOG = logging.getLogger(__name__)


class ValidatePacbioFileTransferService(ValidateFileTransferService):

    def __init__(self, config: CGConfig):
        super().__init__()
        self.config: CGConfig = config
        self.data_dir: str = self.config.pacbio_data_directory

    def get_run_path(self, run_id: str) -> Path:
        return Path(self.data_dir, run_id)

    def get_flow_cell_paths(self, run_id: str) -> list[Path]:
        run_path: Path = self.get_run_path(run_id)
        return get_directories_in_path(run_path)

    @staticmethod
    def get_manifest_file_path(flow_cell_path: Path) -> Path:
        return get_file_in_directory_with_pattern(directory=flow_cell_path, pattern="transferdone")

    def validate_transfer_done(self, run_id: str) -> bool:
        flow_cell_paths: list[Path] = self.get_flow_cell_paths(run_id)
        for flow_cell_path in flow_cell_paths:
            try:
                manifest_file: Path = self.get_manifest_file_path(flow_cell_path)
            except FileNotFoundError:
                LOG.error(
                    f"Manifest file not found for run {run_id} and flow cell {flow_cell_path.name}"
                )
                return False
            if not self.validate_by_manifest_file(
                manifest_file=manifest_file,
                source_dir=flow_cell_path,
                manifest_file_format=FileFormat.TXT,
            ):
                LOG.error(f"Transfer not done for run {run_id} and flow cell {flow_cell_path.name}")
                return False
        return True

    def get_run_ids(self) -> list[str]:
        run_ids: list[str] = []
        run_dirs: list[Path] = get_directories_in_path(Path(self.data_dir))
        for run_dir in run_dirs:
            if run_dir.name.startswith("r"):
                run_ids.append(run_dir.name)
        return run_ids

    def validate_all_transfer_done(self) -> bool:
        run_ids: list[str] = self.get_run_ids()
        for run_id in run_ids:
            return self.validate_transfer_done(run_id)

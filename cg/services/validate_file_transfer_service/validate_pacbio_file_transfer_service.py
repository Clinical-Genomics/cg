from pathlib import Path
import logging
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile, WriteFile
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
        self.trigger_file: str = self.config.pacbio_data_directory + "/validated_flow_cell_runs"

    def get_run_path(self, run_id: str) -> Path:
        return Path(self.data_dir, run_id)

    def get_flow_cell_paths(self, run_id: str) -> list[Path]:
        run_path: Path = self.get_run_path(run_id)
        return get_directories_in_path(run_path)

    @staticmethod
    def get_manifest_file_path(flow_cell_path: Path) -> Path:
        return get_file_in_directory_with_pattern(directory=flow_cell_path, pattern="transferdone")

    def validate_transfer_done(self, run_id: str, flow_cell_path: Path) -> bool:
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

    def ensure_trigger_file_exists(self):
        if not Path(self.trigger_file).exists():
            writer = WriteFile()
            writer.write_file_from_content(
                file_path=Path(self.trigger_file), file_format=FileFormat.TXT, content=[]
            )

    def write_flow_cell_path_to_trigger(self, flow_cell_path: Path):
        reader = ReadFile()
        self.ensure_trigger_file_exists()
        content: any = reader.get_content_from_file(
            file_path=Path(self.trigger_file), file_format=FileFormat.TXT
        )
        content.append(str(flow_cell_path) + "\n")
        writer = WriteFile()
        writer.write_file_from_content(
            file_path=Path(self.trigger_file), file_format=FileFormat.TXT, content=content
        )

    def validate_all_transfer_done(self) -> bool:
        run_ids: list[str] = self.get_run_ids()
        for run_id in run_ids:
            for flow_cell_path in self.get_flow_cell_paths(run_id):
                if self.validate_transfer_done(run_id=run_id, flow_cell_path=flow_cell_path):
                    LOG.info(f"Transfer done for run {run_id} and flow cell {flow_cell_path.name}")
                    self.write_flow_cell_path_to_trigger(flow_cell_path)

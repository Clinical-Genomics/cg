import logging
import shutil
from pathlib import Path

LOG = logging.getLogger(__name__)


class PipelineExtension:
    def configure(self, case_id: str, case_run_directory: Path) -> None:
        """Intended for pipeline specific configurations. If none is needed, this bare class
        can be used."""
        pass

    def do_required_files_exist(self, case_run_directory: Path) -> bool:
        return True

    @staticmethod
    def _copy_file_to_case_directory(source_file_path: Path, case_run_directory: Path) -> None:
        """Copy a file to the case run directory."""
        shutil.copy2(source_file_path, case_run_directory / source_file_path.name)
        LOG.debug(
            f"Copied {source_file_path.name} to case directory for case {case_run_directory.name}"
        )

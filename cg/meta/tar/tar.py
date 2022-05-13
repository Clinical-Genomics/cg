"""API for tar archiving and extraction on Hasta"""
import logging
from pathlib import Path
from typing import List

from cg.constants.extraction import FlowCellExtractionParameters
from cg.utils import Process

LOG = logging.getLogger(__name__)


class TarAPI:
    """Class that uses tar for various archiving and archive extraction functionality"""

    def __init__(self, binary_path: str, dry_run: bool = False):
        self.process: Process = Process(binary=binary_path)
        self.dry_run: bool = dry_run

    def run_tar_command(self, command: list) -> None:
        """Runs a Tar command"""
        LOG.info("Starting Tar command:")
        LOG.info(f"{self.process.binary} {' '.join(command)}")
        self.process.run_command(command, dry_run=self.dry_run)

    @staticmethod
    def get_extract_file_command(input_file: Path, output_dir: Path) -> List[str]:
        """Generates the Tar command for flow cel run directory extraction"""
        extraction_parameters: list = FlowCellExtractionParameters.EXTRACT_FILE.copy()
        extraction_parameters.append(str(input_file))
        exclude_files: list = FlowCellExtractionParameters.EXCLUDE_FILES.copy()
        extraction_parameters.extend(exclude_files)
        target_directory_parameters: list = FlowCellExtractionParameters.CHANGE_TO_DIR.copy()
        extraction_parameters.extend(target_directory_parameters)
        extraction_parameters.append(str(output_dir))
        return extraction_parameters

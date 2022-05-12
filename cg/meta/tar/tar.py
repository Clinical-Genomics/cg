"""API for tar archiving and extraction on Hasta"""
import logging
from pathlib import Path
from typing import List

from cg.constants.encryption import ExtractionParameters
from cg.utils import Process

LOG = logging.getLogger(__name__)


class TarAPI:
    """Class that uses tar for various archiving and archive extraction functionality"""

    def __init__(self, binary_path: str, dry_run: bool = False):
        self.process: Process = Process(binary=binary_path)
        self.dry_run: bool = dry_run

    def run_gpg_command(self, command: list) -> None:
        """Runs a GPG command"""
        LOG.info("Starting GPG command:")
        LOG.info(f"{self.process.binary} {' '.join(command)}")
        self.process.run_command(command, dry_run=self.dry_run)

    @staticmethod
    def get_extract_file_command(input_file: Path, output_dir: Path) -> List[str]:
        """Generates the gpg command for symmetric decryption"""
        extraction_parameters: list = ExtractionParameters.EXTRACT_FILE.copy()
        extraction_parameters.append(str(input_file))
        exclude_files: list = ExtractionParameters.EXCLUDE_FILES.copy()
        extraction_parameters.append(exclude_files)
        target_directory_parameters: list = ExtractionParameters.CHANGE_TO_DIR.copy()
        extraction_parameters.extend([target_directory_parameters, output_dir])
        return extraction_parameters

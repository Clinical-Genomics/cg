"""API for encryption."""
import logging
import subprocess
from io import TextIOWrapper
from pathlib import Path
from typing import List

from cg.constants.encryption import GPGParameters
from cg.utils import Process

LOG = logging.getLogger(__name__)


class EncryptionAPI:
    """Class that uses gpg for various encryption and decryption functionality"""

    def __init__(self, binary_path: str, dry_run: bool = False):
        self.binary_path: str = binary_path
        self.process: Process = Process(binary=binary_path)
        self.dry_run: bool = dry_run

    def run_gpg_command(self, command: list) -> None:
        """Runs a GPG command"""
        LOG.info("Starting GPG command:")
        LOG.info(f"{self.process.binary} {' '.join(command)}")
        self.process.run_command(command, dry_run=self.dry_run)

    def run_passhprase_process(
        self, quality_level: int, count: int, passphrase_file: TextIOWrapper
    ) -> None:
        with open(passphrase_file.name, "w") as f:
            process = subprocess.Popen(
                [
                    self.binary_path,
                    "--gen-random",
                    str(quality_level),
                    str(count),
                ],
                stdout=f,
            )
        process.wait()

    def get_asymmetric_decryption_command(self, input_file: Path, output_file: Path) -> List[str]:
        """Generates the gpg command for asymmetric decryption"""
        decryption_parameters: list = GPGParameters.ASYMMETRIC_DECRYPTION.copy()
        output_parameter: list = GPGParameters.OUTPUT_PARAMETER.copy()
        output_parameter.extend([str(output_file), str(input_file)])
        decryption_parameters.extend(output_parameter)
        return decryption_parameters

    def get_symmetric_decryption_command(
        self, input_file: Path, output_file: Path, encryption_key: Path
    ) -> List[str]:
        """Generates the gpg command for symmetric decryption"""
        decryption_parameters: list = GPGParameters.SYMMETRIC_DECRYPTION.copy()
        decryption_parameters.append(str(encryption_key))
        output_parameter: list = GPGParameters.OUTPUT_PARAMETER.copy()
        output_parameter.extend([str(output_file), str(input_file)])
        decryption_parameters.extend(output_parameter)
        return decryption_parameters

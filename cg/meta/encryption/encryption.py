"""API for encryption on Hasta"""

import logging
from pathlib import Path

from cg.constants import FileExtensions
from cg.constants.encryption import EncryptionUserID, GPGParameters
from cg.utils import Process

LOG = logging.getLogger(__name__)
LIMIT_PIGZ_TASK: int = 3


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

    def get_symmetric_passphrase_cmd(
        self, passphrase_file_path: Path, quality_level: int = 2, count: int = 256
    ) -> str:
        """Return command to generate a symmetrical passphrase file."""
        return " ".join(
            [
                self.binary_path,
                "--gen-random",
                str(quality_level),
                str(count),
                ">",
                passphrase_file_path.as_posix(),
            ]
        )

    def get_asymmetrically_encrypt_passphrase_cmd(self, passphrase_file_path: Path) -> str:
        """Return command to asymmetrically encrypt a symmetrical passphrase file."""
        return " ".join(
            [
                self.binary_path,
                "--encrypt",
                "--yes",
                "--recipient",
                EncryptionUserID.HASTA_USER_ID,
                "--output",
                passphrase_file_path.with_suffix(FileExtensions.GPG).as_posix(),
                passphrase_file_path.as_posix(),
            ]
        )

    def get_asymmetric_decryption_command(self, input_file: Path, output_file: Path) -> list[str]:
        """Generates the gpg command for asymmetric decryption"""
        decryption_parameters: list = GPGParameters.ASYMMETRIC_DECRYPTION.copy()
        output_parameter: list = GPGParameters.OUTPUT_PARAMETER.copy()
        output_parameter.extend([str(output_file), str(input_file)])
        decryption_parameters.extend(output_parameter)
        return decryption_parameters

    def get_symmetric_decryption_command(
        self, input_file: Path, output_file: Path, encryption_key: Path
    ) -> list[str]:
        """Generates the gpg command for symmetric decryption"""
        decryption_parameters: list = GPGParameters.SYMMETRIC_DECRYPTION.copy()
        decryption_parameters.append(str(encryption_key))
        output_parameter: list = GPGParameters.OUTPUT_PARAMETER.copy()
        output_parameter.extend([str(output_file), str(input_file)])
        decryption_parameters.extend(output_parameter)
        return decryption_parameters

    def create_pending_file(self, pending_path: Path) -> None:
        """Create a pending flag file."""
        LOG.info(f"Creating pending flag {pending_path}")
        if self.dry_run:
            return
        pending_path.touch(exist_ok=False)

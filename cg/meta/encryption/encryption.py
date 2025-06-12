"""API for encryption on Hasta"""

import logging
import subprocess
from io import TextIOWrapper
from pathlib import Path
from tempfile import NamedTemporaryFile

from cg.constants import FileExtensions
from cg.constants.encryption import EncryptionUserID, GPGParameters
from cg.exc import ChecksumFailedError
from cg.utils import Process
from cg.utils.checksum.checksum import sha512_checksum

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

    def generate_temporary_passphrase_file(self, quality_level: int = 2, count: int = 256) -> Path:
        """Generates a temporary file with random bytes. The default values are based on the
        encryption parameters as used on the NAS:es connected to the sequencers"""
        LOG.debug("Generate temporary passphrase file:")
        passphrase_file = NamedTemporaryFile(delete=False)
        self.run_passhprase_process(
            passphrase_file=passphrase_file, quality_level=quality_level, count=count
        )
        LOG.debug(f"Temporary passphrase file generated: {passphrase_file.name}")

        return Path(passphrase_file.name)

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

    def get_asymmetric_encryption_command(self, input_file: Path, output_file: Path) -> list[str]:
        """Generates the gpg command for asymmetric encryption"""
        encryption_parameters: list = GPGParameters.ASYMMETRIC_ENCRYPTION.copy()
        output_parameter: list = GPGParameters.OUTPUT_PARAMETER.copy()
        output_parameter.extend([str(output_file), str(input_file)])
        encryption_parameters.extend(output_parameter)
        return encryption_parameters

    def get_symmetric_encryption_command(self, input_file: Path, output_file: Path) -> list[str]:
        """Generates the gpg command for symmetric encryption of spring files"""
        encryption_parameters: list = GPGParameters.SYMMETRIC_ENCRYPTION.copy()
        encryption_parameters.append(str(self.temporary_passphrase))
        output_parameter: list = GPGParameters.OUTPUT_PARAMETER.copy()
        output_parameter.extend([str(output_file), str(input_file)])
        encryption_parameters.extend(output_parameter)
        return encryption_parameters

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


class SpringEncryptionAPI(EncryptionAPI):
    """Encryption functionality for spring files"""

    def __init__(
        self,
        binary_path: str,
        dry_run: bool = False,
    ):
        super().__init__(binary_path=binary_path, dry_run=dry_run)
        self._temporary_passphrase = None

    def spring_symmetric_encryption(self, spring_file_path: Path) -> None:
        """Symmetrically encrypts a spring file"""
        output_file = self.encrypted_spring_file_path(spring_file_path)
        LOG.debug("*** ENCRYPTING SPRING FILE ***")
        LOG.info(f"Encrypt spring file: {spring_file_path}")
        LOG.info(f"to output file     : {output_file}")
        encryption_command: list = self.get_symmetric_encryption_command(
            input_file=spring_file_path, output_file=output_file
        )
        self.run_gpg_command(encryption_command)

    def key_asymmetric_encryption(self, spring_file_path: Path) -> None:
        """Asymmetrically encrypts the key used for spring file encryption"""
        output_file = self.encrypted_key_path(spring_file_path)
        LOG.debug("*** ENCRYPTING KEY FILE ***")
        LOG.info(f"Encrypt key file: {self.temporary_passphrase}")
        LOG.info(f"to target file  : {output_file}")
        encryption_command: list = self.get_asymmetric_encryption_command(
            input_file=self.temporary_passphrase, output_file=output_file
        )
        self.run_gpg_command(encryption_command)

    def spring_symmetric_decryption(self, spring_file_path: Path, output_file: Path) -> None:
        """decrypt a spring file"""
        input_file = self.encrypted_spring_file_path(spring_file_path)
        LOG.debug("*** DECRYPTING SPRING FILE ***")
        LOG.info(f"Decrypt spring file: {input_file}")
        LOG.info(f"to target file     : {output_file}")
        decryption_command: list = self.get_symmetric_decryption_command(
            input_file=input_file,
            output_file=output_file,
            encryption_key=self.encryption_key(spring_file_path),
        )
        self.run_gpg_command(decryption_command)

    def key_asymmetric_decryption(self, spring_file_path: Path) -> None:
        """Asymmetrically decrypts the key used for spring file decryption"""
        input_file = self.encrypted_key_path(spring_file_path)
        output_file = self.encryption_key(spring_file_path)
        LOG.debug("*** DECRYPTING KEY FILE ***")
        LOG.info(f"Decrypt key file: {input_file}")
        LOG.info(f"to target file  : {output_file}")
        decryption_command: list = self.get_asymmetric_decryption_command(
            input_file=input_file, output_file=output_file
        )
        self.run_gpg_command(decryption_command)

    def cleanup(self, spring_file_path: Path) -> None:
        """Removes any existing encrypted key file, key file and encrypted spring file before
        attempting encryption or after an error has occurred"""
        LOG.debug("*** PRE OR POST ENCRYPTION CLEANUP ***")
        try:
            self.decrypted_spring_file_checksum(spring_file_path).unlink()
            LOG.info("Removed existing decrypted checksum spring file")
        except FileNotFoundError:
            LOG.info("No decrypted checksum spring file to clean up, continuing cleanup")
        try:
            self.encrypted_spring_file_path(spring_file_path).unlink()
            LOG.info("Removed existing encrypted spring file")
        except FileNotFoundError:
            LOG.info("No encrypted spring file to clean up, continuing cleanup")
        try:
            self.encrypted_key_path(spring_file_path).unlink()
            LOG.info("Removed existing encrypted key file")
        except FileNotFoundError:
            LOG.info("No encrypted key file to clean up, continuing cleanup")
        try:
            self.encryption_key(spring_file_path).unlink()
            LOG.info("Removed existing key file")
        except FileNotFoundError:
            LOG.info("No existing key file to clean up, cleanup process completed")

    def compare_spring_file_checksums(self, spring_file_path: Path) -> None:
        """Make sure the encrypted spring file is correct and can be decrypted"""
        LOG.debug("PERFORMING CHECKSUM COMPARISON")
        if self.dry_run:
            LOG.info("Dry run, skipping checksum!")
            return
        self.key_asymmetric_decryption(spring_file_path=spring_file_path)
        self.spring_symmetric_decryption(
            spring_file_path=spring_file_path,
            output_file=self.decrypted_spring_file_checksum(spring_file_path),
        )
        is_checksum_equal = sha512_checksum(spring_file_path) == sha512_checksum(
            self.decrypted_spring_file_checksum(spring_file_path)
        )
        if not is_checksum_equal:
            raise ChecksumFailedError("Checksum comparison failed!")
        LOG.info("Checksum comparison successful!")

    def encrypted_key_path(self, spring_file_path: Path) -> Path:
        """The name of the encrypted key file"""
        return Path(spring_file_path).with_suffix(FileExtensions.KEY + FileExtensions.GPG)

    def encryption_key(self, spring_file_path: Path) -> Path:
        """The name of the encryption key"""
        return Path(spring_file_path).with_suffix(FileExtensions.KEY)

    def encrypted_spring_file_path(self, spring_file_path: Path) -> Path:
        """The name of the encrypted spring file"""
        return spring_file_path.with_suffix(FileExtensions.SPRING + FileExtensions.GPG)

    def decrypted_spring_file_checksum(self, spring_file_path: Path) -> Path:
        """The name of the decrypted spring file used to perform the checksum check"""
        return spring_file_path.with_suffix(FileExtensions.SPRING + FileExtensions.TMP)

    @property
    def temporary_passphrase(self) -> Path:
        """The name of the temporary passphrase"""
        if self._temporary_passphrase is None:
            self._temporary_passphrase: Path = self.generate_temporary_passphrase_file()
        return self._temporary_passphrase

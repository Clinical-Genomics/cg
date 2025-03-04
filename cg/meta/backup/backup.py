""" Module for retrieving flow cells from backup."""

import logging
import subprocess
from pathlib import Path

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import ChecksumFailedError
from cg.meta.encryption.encryption import SpringEncryptionAPI
from cg.models.compression_data import CompressionData
from cg.services.pdc_service.pdc_service import PdcService

LOG = logging.getLogger(__name__)


class SpringBackupAPI:
    """Class for handling PDC backup and retrieval of spring compressed fastq files."""

    def __init__(
        self,
        encryption_api: SpringEncryptionAPI,
        pdc_service: PdcService,
        hk_api: HousekeeperAPI,
        dry_run: bool = False,
    ):
        self.encryption_api: SpringEncryptionAPI = encryption_api
        self.hk_api: HousekeeperAPI = hk_api
        self.pdc: PdcService = pdc_service
        self.dry_run = dry_run

    def encrypt_and_archive_spring_file(self, spring_file_path: Path) -> None:
        """Encrypts and archives a spring file and its decryption key."""
        LOG.debug(f"*** START BACKUP PROCESS OF SPRING FILE {spring_file_path} ***")
        if self.is_compression_ongoing(spring_file_path):
            LOG.info(
                f"Spring (de)compression ongoing, skipping archiving for spring file {spring_file_path}",
            )
            return
        self.encryption_api.cleanup(spring_file_path)
        if self.is_spring_file_archived(spring_file_path):
            LOG.info(
                "Spring file already archived! Spring file will be removed from disk, continuing "
                "to next spring file "
            )
            self.remove_archived_spring_file(spring_file_path)
            return
        try:
            self.encryption_api.spring_symmetric_encryption(spring_file_path)
            self.encryption_api.key_asymmetric_encryption(spring_file_path)
            self.encryption_api.compare_spring_file_checksums(spring_file_path)
            self.pdc.archive_file_to_pdc(
                file_path=str(self.encryption_api.encrypted_spring_file_path(spring_file_path))
            )
            self.pdc.archive_file_to_pdc(
                file_path=str(self.encryption_api.encrypted_key_path(spring_file_path))
            )
            self.mark_file_as_archived(spring_file_path)
            self.encryption_api.cleanup(spring_file_path)
            self.remove_archived_spring_file(spring_file_path)
            LOG.debug("*** ARCHIVING PROCESS COMPLETED SUCCESSFULLY ***")
        except subprocess.CalledProcessError as error:
            LOG.error(f"Encryption failed: {error.stderr}")
            LOG.debug("*** COMMAND PROCESS FAILED! ***")
            self.encryption_api.cleanup(spring_file_path)
        except ChecksumFailedError as error:
            LOG.error(error)
            self.encryption_api.cleanup(spring_file_path)
            LOG.debug("*** CHECKSUM PROCESS FAILED! ***")

    def retrieve_and_decrypt_spring_file(self, spring_file_path: Path) -> None:
        """Retrieves and decrypts a spring file and its decryption key."""
        LOG.info(f"*** START RETRIEVAL PROCESS OF SPRING FILE {spring_file_path} ***")
        try:
            self.pdc.retrieve_file_from_pdc(
                file_path=str(self.encryption_api.encrypted_spring_file_path(spring_file_path)),
            )
            self.pdc.retrieve_file_from_pdc(
                file_path=str(self.encryption_api.encrypted_key_path(spring_file_path)),
            )
            self.encryption_api.key_asymmetric_decryption(spring_file_path)
            self.encryption_api.spring_symmetric_decryption(
                spring_file_path, output_file=spring_file_path
            )
        except subprocess.CalledProcessError as error:
            LOG.error(f"Decryption failed: {error.stderr}")
            LOG.debug("*** RETRIEVAL PROCESS FAILED! ***")
        self.encryption_api.cleanup(spring_file_path)
        LOG.debug("*** RETRIEVAL PROCESS COMPLETED SUCCESSFULLY ***")

    def mark_file_as_archived(self, spring_file_path: Path) -> None:
        """Set the field 'to_archive' of the file in Housekeeper to mark that it has been
        archived to PDC."""
        if self.dry_run:
            LOG.info(f"Dry run, no changes made to {spring_file_path}")
            return
        hk_spring_file: File = self.hk_api.files(path=str(spring_file_path)).first()
        if hk_spring_file:
            LOG.info(f"Setting {spring_file_path} to archived in Housekeeper")
            self.hk_api.set_to_archive(file=hk_spring_file, value=True)
        else:
            LOG.warning(f"Could not find {spring_file_path} on disk")

    def remove_archived_spring_file(self, spring_file_path: Path) -> None:
        """Removes all files related to spring PDC archiving."""
        if not self.dry_run:
            LOG.info(f"Removing spring file {spring_file_path} from disk")
            spring_file_path.unlink()

    def is_to_be_retrieved_and_decrypted(self, spring_file_path: Path) -> bool:
        """Determines if a spring file is archived on PDC and needs to be retrieved and decrypted."""
        spring_file: File = self.hk_api.files(path=str(spring_file_path)).first()
        if spring_file and not spring_file_path.exists():
            return spring_file.to_archive
        return False

    def is_spring_file_archived(self, spring_file_path: Path) -> bool:
        """Checks if a spring file is marked as archived in Housekeeper."""
        spring_file: File = self.hk_api.files(path=str(spring_file_path)).first()
        if spring_file:
            return spring_file.to_archive
        return False

    @staticmethod
    def is_compression_ongoing(spring_file_path: Path) -> bool:
        """Determines if (de)compression of the spring file ongoing."""
        return CompressionData(spring_file_path).pending_exists()

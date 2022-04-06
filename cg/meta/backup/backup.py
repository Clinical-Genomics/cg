""" Module for retrieving FCs from backup """
import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

from housekeeper.store import models as hk_models

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import ChecksumFailedError
from cg.meta.backup.pdc import PdcAPI
from cg.meta.encryption.encryption import SpringEncryptionAPI
from cg.store import Store, models

LOG = logging.getLogger(__name__)


class BackupApi:
    """Class for retrieving FCs from backup"""

    def __init__(self, status: Store, pdc_api: PdcAPI, root_dir: dict):

        self.status: Store = status
        self.pdc: PdcAPI = pdc_api
        self.root_dir: dict = root_dir

    def check_processing(self, max_processing_flowcells: int = 1) -> bool:
        """Check if the processing queue for flow cells is not full."""
        processing_flowcells = self.status.flowcells(status="processing").count()
        LOG.debug("processing flow cells: %s", processing_flowcells)
        return processing_flowcells < max_processing_flowcells

    def pop_flowcell(self) -> Optional[models.Flowcell]:
        """Get the top flow cell from the requested queue"""
        flowcell_obj: Optional[models.Flowcell] = self.status.flowcells(status="requested").first()
        if not flowcell_obj:
            return None

        return flowcell_obj

    def fetch_flowcell(
        self, flowcell_obj: Optional[models.Flowcell] = None, dry_run: bool = False
    ) -> Optional[float]:
        """Start fetching a flow cell from backup if possible.

        1. The processing queue is not full
        2. The requested queue is not emtpy
        """
        if self.check_processing() is False:
            LOG.info("processing queue is full")
            return None

        if not flowcell_obj:
            flowcell_obj = self.pop_flowcell()

        if not flowcell_obj:
            LOG.info("no flow cells requested")
            return None

        flowcell_obj.status = "processing"
        if not dry_run:
            self.status.commit()
            LOG.info("%s: retrieving from PDC", flowcell_obj.name)

        start_time = time.time()

        try:
            self.pdc.retrieve_flowcell(
                flowcell_id=flowcell_obj.name,
                sequencer_type=flowcell_obj.sequencer_type,
                root_dir=self.root_dir,
                dry=dry_run,
            )
            if not dry_run:
                flowcell_obj.status = "retrieved"
                self.status.commit()
                LOG.info('Status for flow cell %s set to "retrieved"', flowcell_obj.name)
        except subprocess.CalledProcessError as error:
            LOG.error("%s: retrieval failed", flowcell_obj.name)
            if not dry_run:
                flowcell_obj.status = "requested"
                self.status.commit()
            raise error

        end_time = time.time()
        return end_time - start_time


class SpringBackupAPI:
    """Class for handling PDC backup and retrieval of spring compressed fastq files"""

    def __init__(
        self,
        encryption_api: SpringEncryptionAPI,
        pdc_api: PdcAPI,
        hk_api: HousekeeperAPI,
        dry_run: bool = False,
    ):
        self.encryption_api: SpringEncryptionAPI = encryption_api
        self.hk_api: HousekeeperAPI = hk_api
        self.pdc: PdcAPI = pdc_api
        self._dry_run = dry_run

    def encrypt_and_archive_spring_file(self, spring_file_path: Path) -> None:
        """Encrypts and archives a spring file and its decryption key"""
        LOG.debug(f"*** START BACKUP PROCESS OF SPRING FILE %s ***", spring_file_path)
        self.encryption_api.cleanup(spring_file_path)
        try:
            self.encryption_api.spring_symmetric_encryption(spring_file_path)
            self.encryption_api.key_asymmetric_encryption(spring_file_path)
            self.encryption_api.compare_file_checksums(spring_file_path)
            self.pdc.archive_file_to_pdc(
                file_path=str(self.encryption_api.encrypted_spring_file_path(spring_file_path)),
                dry_run=self.dry_run,
            )
            self.pdc.archive_file_to_pdc(
                file_path=str(self.encryption_api.encrypted_key_path(spring_file_path)),
                dry_run=self.dry_run,
            )
            self.mark_file_as_archived(spring_file_path)
            self.remove_archived_spring_files(spring_file_path)
            LOG.debug(f"*** ARCHIVING PROCESS COMPLETED SUCCESSFULLY ***")
        except subprocess.CalledProcessError as error:
            LOG.error("Encryption failed: %s", error.stderr)
            LOG.debug(f"*** COMMAND PROCESS FAILED! ***")
            self.encryption_api.cleanup(spring_file_path)
        except ChecksumFailedError as error:
            LOG.error(error.message)
            self.encryption_api.cleanup(spring_file_path)
            LOG.debug(f"*** CHECKSUM PROCESS FAILED! ***")

    def retrieve_and_decrypt_spring_file(self, spring_file_path: Path) -> None:
        """Retrieves and decrypts a spring file and its decryption key"""
        LOG.info(f"*** START RETRIEVAL PROCESS OF SPRING FILE %s ***", spring_file_path)
        try:
            self.pdc.retrieve_file_from_pdc(
                file_path=str(self.encryption_api.encrypted_spring_file_path(spring_file_path)),
                dry_run=self.dry_run,
            )
            self.pdc.retrieve_file_from_pdc(
                file_path=str(self.encryption_api.encrypted_key_path(spring_file_path)),
                dry_run=self.dry_run,
            )
            self.encryption_api.key_asymmetric_decryption(spring_file_path)
            self.encryption_api.spring_symmetric_decryption(
                spring_file_path, output_file=spring_file_path
            )
        except subprocess.CalledProcessError as error:
            LOG.error("Decryption failed: %s", error.stderr)
            self.encryption_api.cleanup(spring_file_path)
            LOG.debug(f"*** RETRIEVAL PROCESS FAILED! ***")
        LOG.debug(f"*** RETRIEVAL PROCESS COMPLETED SUCCESSFULLY ***")

    def mark_file_as_archived(self, spring_file_path: Path) -> None:
        """Set the field 'to_archive' of the file in Housekeeper to mark that it has been
        archived to PDC"""
        if self.dry_run:
            LOG.info("Dry run, no changes made to %s", spring_file_path)
            return
        hk_spring_file: hk_models.File = self.hk_api.files(path=spring_file_path).first()
        LOG.info("Setting %s to archived in Housekeeper", spring_file_path)
        self.hk_api.set_to_archive(file=hk_spring_file, value=True)

    def needs_to_be_retrieved_and_decrypted(self, spring_file_path: Path) -> bool:
        """Determines if a spring file is archived on PDC and needs to be retrieved and decrypted"""
        return (
            self.hk_api.files(path=spring_file_path).first().to_archive
            and not spring_file_path.exists()
        )

    def remove_archived_spring_files(self, spring_file_path: Path) -> None:
        """Removes all files related to spring PDC archiving"""
        self.encryption_api.cleanup(spring_file_path)
        if not self.dry_run:
            spring_file_path.unlink()

    @property
    def dry_run(self) -> bool:
        """Dry run property"""
        LOG.debug("Backup dry run property: %s", self._dry_run)
        return self._dry_run

    @dry_run.setter
    def dry_run(self, value: bool) -> None:
        """Set the dry run property"""
        LOG.debug(
            "Set backup dry run property to %s, and set the encryption dry run property to the "
            "same value",
            value,
        )
        self._dry_run = value
        self.encryption_api.dry_run = value
